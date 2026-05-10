from datetime import datetime, timezone
from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph

from agents.backend_agent import BackendAgent
from agents.base import BaseAgent
from agents.schemas import AgentInput
from agents.deployment_agent import DeploymentAgent
from agents.frontend_agent import FrontendAgent
from agents.tester_agent import TesterAgent
from backend.app.config import get_settings
from context.context_builder import ContextBuilder
from database.repository import AGENTS, Repository
from evaluation.scorer import EvaluationScorer
from llm_providers.factory import build_chat_provider
from memory.long_term_memory import LongTermMemory
from memory.short_term_memory import ShortTermMemory
from tools.file_writer import write_artifacts


class SoftwareTeamState(TypedDict, total=False):
    run_id: int
    requirement: str
    provider: str
    model: str
    artifacts: dict[str, str]
    messages: list[str]
    bug_report: str
    bugs_found: bool
    evaluation_passed: bool
    revision_count: int
    stopped: bool
    failed: bool


class SoftwareTeamWorkflow:
    """Coordinates agents through LangGraph and persists every step."""

    def __init__(self, repository: Repository | None = None) -> None:
        self.repository = repository or Repository()
        self.settings = get_settings()
        self.context_builder = ContextBuilder()
        self.short_term_memory = ShortTermMemory(repository=self.repository)
        self.long_term_memory = LongTermMemory(repository=self.repository)
        self.evaluator = EvaluationScorer()
        self.initial_graph = self._build_initial_graph().compile()
        self.deployment_graph = self._build_deployment_graph().compile()

    def run_until_approval(self, run_id: int) -> SoftwareTeamState | None:
        run = self.repository.get_run(run_id)
        if not run:
            return None

        self.repository.update_run(run_id, status="running", current_stage="backend", error=None)
        self.repository.set_many_agent_statuses(run_id, AGENTS, "idle")
        self.repository.add_log(
            run_id,
            "Human Manager",
            "Run started",
            "Requirement accepted. Backend Agent is taking the first pass.",
        )

        state: SoftwareTeamState = {
            "run_id": run.id,
            "requirement": run.requirement,
            "provider": run.provider,
            "model": run.model,
            "artifacts": {file.path: file.content for file in self.repository.list_files(run_id)},
            "messages": [],
            "bug_report": "",
            "bugs_found": False,
            "evaluation_passed": False,
            "revision_count": 0,
        }
        final_state = self.initial_graph.invoke(state)
        refreshed = self.repository.get_run(run_id)
        if refreshed and refreshed.status not in {"failed", "stopped"}:
            self.repository.update_run(run_id, status="waiting_approval", current_stage="deployment_approval")
            self.repository.add_log(
                run_id,
                "Human Manager",
                "Approval required",
                "Testing is complete. Review generated files, then approve deployment when ready.",
            )
        return final_state

    def run_deployment(self, run_id: int) -> SoftwareTeamState | None:
        run = self.repository.get_run(run_id)
        if not run:
            return None
        if not run.approved_for_deployment:
            self.repository.add_log(
                run_id,
                "Deployment Agent",
                "Blocked",
                "Deployment requires human manager approval before it can run.",
                status="warning",
            )
            return None

        self.repository.update_run(run_id, status="running", current_stage="deployment")
        state: SoftwareTeamState = {
            "run_id": run.id,
            "requirement": run.requirement,
            "provider": run.provider,
            "model": run.model,
            "artifacts": {file.path: file.content for file in self.repository.list_files(run_id)},
            "messages": [message.content for message in self.repository.list_messages(run_id)],
            "bug_report": "",
            "bugs_found": False,
            "evaluation_passed": False,
            "revision_count": 0,
        }
        final_state = self.deployment_graph.invoke(state)
        refreshed = self.repository.get_run(run_id)
        if refreshed and refreshed.status not in {"failed", "stopped"}:
            self.repository.update_run(
                run_id,
                status="completed",
                current_stage="completed",
                completed_at=datetime.now(timezone.utc),
            )
            self.repository.add_log(
                run_id,
                "Deployment Agent",
                "Deployment ready",
                "Docker and local deployment artifacts are ready in the generated run folder.",
            )
        return final_state

    def _build_initial_graph(self) -> StateGraph:
        graph = StateGraph(SoftwareTeamState)
        graph.add_node("backend", self._backend_node)
        graph.add_node("frontend", self._frontend_node)
        graph.add_node("tester", self._tester_node)
        graph.add_node("backend_revision", self._backend_revision_node)
        graph.add_node("frontend_revision", self._frontend_revision_node)

        graph.add_edge(START, "backend")
        graph.add_conditional_edges("backend", self._continue_or_end, {"continue": "frontend", "end": END})
        graph.add_conditional_edges("frontend", self._continue_or_end, {"continue": "tester", "end": END})
        graph.add_conditional_edges("tester", self._route_after_testing, {
            "revise": "backend_revision",
            "approval": END,
            "end": END,
        })
        graph.add_conditional_edges("backend_revision", self._continue_or_end, {
            "continue": "frontend_revision",
            "end": END,
        })
        graph.add_conditional_edges("frontend_revision", self._continue_or_end, {
            "continue": "tester",
            "end": END,
        })
        return graph

    def _build_deployment_graph(self) -> StateGraph:
        graph = StateGraph(SoftwareTeamState)
        graph.add_node("deployment", self._deployment_node)
        graph.add_edge(START, "deployment")
        graph.add_edge("deployment", END)
        return graph

    def _backend_node(self, state: SoftwareTeamState) -> SoftwareTeamState:
        return self._run_agent(state, BackendAgent(), "backend")

    def _frontend_node(self, state: SoftwareTeamState) -> SoftwareTeamState:
        return self._run_agent(state, FrontendAgent(), "frontend")

    def _tester_node(self, state: SoftwareTeamState) -> SoftwareTeamState:
        return self._run_agent(state, TesterAgent(), "testing", captures_bugs=True)

    def _backend_revision_node(self, state: SoftwareTeamState) -> SoftwareTeamState:
        next_state = dict(state)
        next_state["revision_count"] = int(state.get("revision_count", 0)) + 1
        return self._run_agent(next_state, BackendAgent(), "backend_revision", revision=True)

    def _frontend_revision_node(self, state: SoftwareTeamState) -> SoftwareTeamState:
        return self._run_agent(state, FrontendAgent(), "frontend_revision", revision=True)

    def _deployment_node(self, state: SoftwareTeamState) -> SoftwareTeamState:
        return self._run_agent(state, DeploymentAgent(), "deployment")

    def _run_agent(
        self,
        state: SoftwareTeamState,
        agent: BaseAgent,
        stage: str,
        captures_bugs: bool = False,
        revision: bool = False,
    ) -> SoftwareTeamState:
        run_id = int(state["run_id"])
        if self.repository.stop_requested(run_id):
            self.repository.update_run(run_id, status="stopped", current_stage=stage)
            self.repository.add_log(run_id, agent.name, "Stopped", "Run stopped by the human manager.", status="warning")
            return {**state, "stopped": True}

        self.repository.update_run(run_id, current_stage=stage)
        self.repository.set_agent_status(run_id, agent.name, "thinking")
        self.repository.add_log(run_id, agent.name, "Thinking", f"{agent.name} is planning the {stage} step.")

        try:
            chat_provider = build_chat_provider(state.get("provider"), state.get("model"))
            chat_provider.validate()
            self.repository.set_agent_status(run_id, agent.name, "working")
            retrieved_memory = self.long_term_memory.retrieve(state["requirement"], limit=3)
            focused_context = self.context_builder.build(
                user_requirement=state["requirement"],
                current_task=stage,
                agent_name=agent.name,
                agent_role=agent.role,
                artifacts=state.get("artifacts", {}),
                constraints="Use complete relative file paths. Do not store or output secrets.",
                errors_or_feedback=state.get("bug_report", ""),
                long_term_memory=retrieved_memory,
            )
            self.repository.add_context_snapshot(run_id, agent.name, focused_context)
            self.short_term_memory.remember(run_id, f"context:{agent.name}:{stage}", str(focused_context))
            agent_input = AgentInput(
                run_id=run_id,
                requirement=state["requirement"],
                focused_context=focused_context,
                artifacts=state.get("artifacts", {}),
                messages=state.get("messages", []),
                bug_report=state.get("bug_report", ""),
                revision=revision,
            )
            result = agent.invoke(agent_input, chat_provider.chat_model)
            artifacts = {**state.get("artifacts", {}), **result.artifacts}
            run_dir = self.settings.generated_root / f"run_{run_id}"
            write_artifacts(run_dir, result.artifacts)
            self.repository.upsert_generated_files(run_id, agent.name, result.artifacts)
            self.repository.add_message(run_id, agent.name, "assistant", result.summary)
            self.short_term_memory.remember(run_id, f"output:{agent.name}:{stage}", result.summary)
            self.repository.add_log(
                run_id,
                agent.name,
                "Completed",
                f"{result.summary} Artifacts: {len(result.artifacts)}.",
                status="success",
            )
            self.repository.set_agent_status(run_id, agent.name, "completed")

            updated: SoftwareTeamState = {
                **state,
                "artifacts": artifacts,
                "messages": [*state.get("messages", []), f"{agent.name}: {result.summary}"],
            }
            if captures_bugs:
                updated["bugs_found"] = bool(result.bugs)
                updated["bug_report"] = "\n".join(result.bugs)
                evaluation = self.evaluator.score(
                    artifacts,
                    result.bugs,
                    requirement=state["requirement"],
                    llm_judge=chat_provider.chat_model,
                )
                updated["evaluation_passed"] = evaluation.passed
                self.repository.add_evaluation(run_id, **evaluation.model_dump())
                self.short_term_memory.remember(run_id, "latest_evaluation", evaluation.model_dump_json())
                self.repository.add_log(
                    run_id,
                    "Evaluation",
                    "Scored artifacts",
                    evaluation.model_dump_json(),
                    status="success" if evaluation.passed else "warning",
                )
                if result.bugs:
                    self.repository.add_log(
                        run_id,
                        agent.name,
                        "Bugs found",
                        "\n".join(result.bugs),
                        status="warning",
                    )
            return updated
        except Exception as exc:
            self.repository.set_agent_status(run_id, agent.name, "failed")
            self.repository.update_run(run_id, status="failed", current_stage=stage, error=str(exc))
            self.repository.add_log(run_id, agent.name, "Failed", str(exc), status="error")
            return {**state, "failed": True}

    def _continue_or_end(self, state: SoftwareTeamState) -> Literal["continue", "end"]:
        if state.get("failed") or state.get("stopped"):
            return "end"
        return "continue"

    def _route_after_testing(self, state: SoftwareTeamState) -> Literal["revise", "approval", "end"]:
        if state.get("failed") or state.get("stopped"):
            return "end"
        needs_revision = state.get("bugs_found") or not state.get("evaluation_passed", False)
        if needs_revision and int(state.get("revision_count", 0)) < 1:
            run_id = int(state["run_id"])
            self.repository.add_log(
                run_id,
                "Tester Agent",
                "Feedback loop",
                "Testing or evaluation found issues. Sending feedback back to Backend and Frontend agents for one revision pass.",
                status="warning",
            )
            return "revise"
        if state.get("evaluation_passed"):
            self.long_term_memory.remember(
                "successful_solution",
                f"Requirement: {state['requirement']}\nArtifacts: {', '.join(sorted(state.get('artifacts', {})))}",
                source_run_id=int(state["run_id"]),
            )
        return "approval"
