from datetime import datetime, timezone
from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph

from agents.backend_agent import BackendAgent
from agents.base import BaseAgent
from agents.schemas import AgentInput
from agents.deployment_agent import DeploymentAgent
from agents.frontend_agent import FrontendAgent
from agents.tester_agent import TesterAgent
from app.core.control_loop import ControlLoopPolicy, ControlLoopState, ControlPhase
from backend.app.config import get_settings
from context.context_builder import ContextBuilder
from database.repository import AGENTS, Repository
from evaluation.scorer import EvaluationScorer
from llm_providers.factory import build_chat_provider
from memory.long_term_memory import LongTermMemory
from memory.short_term_memory import ShortTermMemory
from observability.tracing import TraceEvent, TraceRecorder
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
    control_loop: dict[str, object]


class SoftwareTeamWorkflow:
    """Coordinates agents through LangGraph and persists every step."""

    def __init__(self, repository: Repository | None = None) -> None:
        self.repository = repository or Repository()
        self.settings = get_settings()
        self.context_builder = ContextBuilder()
        self.short_term_memory = ShortTermMemory(repository=self.repository)
        self.long_term_memory = LongTermMemory(repository=self.repository)
        self.evaluator = EvaluationScorer()
        self.control_policy = ControlLoopPolicy(max_refinements=1)
        self.trace_recorder = TraceRecorder(repository=self.repository)
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
            "control_loop": self._control_snapshot(
                ControlLoopState(run_id=run.id, goal=run.requirement, phase=ControlPhase.SENSE)
            ),
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
            "control_loop": self._control_snapshot(
                ControlLoopState(run_id=run.id, goal=run.requirement, phase=ControlPhase.SENSE)
            ),
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
        control_state = self._control_from_state(state)
        if self.repository.stop_requested(run_id):
            self.repository.update_run(run_id, status="stopped", current_stage=stage)
            self.repository.add_log(run_id, agent.name, "Stopped", "Run stopped by the human manager.", status="warning")
            control_state.transition(ControlPhase.CANCELLED, agent.name, stage=stage)
            self._record_trace(control_state, "workflow.cancelled", "Run stopped by the human manager.", "warning")
            return {**state, "stopped": True, "control_loop": self._control_snapshot(control_state)}

        self.repository.update_run(run_id, current_stage=stage)
        self.repository.set_agent_status(run_id, agent.name, "thinking")
        self.repository.add_log(run_id, agent.name, "Thinking", f"{agent.name} is planning the {stage} step.")
        control_state.transition(ControlPhase.PLAN, agent.name, stage=stage)
        self._record_trace(control_state, "control.plan", f"{agent.name} is planning {stage}.")

        try:
            chat_provider = build_chat_provider(state.get("provider"), state.get("model"))
            chat_provider.validate()
            self.repository.set_agent_status(run_id, agent.name, "working")
            control_state.transition(ControlPhase.ACT, agent.name, stage=stage, provider=state.get("provider"), model=state.get("model"))
            self._record_trace(control_state, "control.act", f"{agent.name} is executing {stage}.")
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
                "control_loop": self._control_snapshot(control_state),
            }
            if captures_bugs:
                control_state.transition(ControlPhase.EVALUATE, "Evaluator Agent", stage=stage)
                self._record_trace(control_state, "control.evaluate", "Evaluator is scoring generated artifacts.")
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
                updated["control_loop"] = self._control_snapshot(control_state)
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
            control_state.transition(ControlPhase.FAILED, agent.name, stage=stage, error=str(exc))
            self._record_trace(control_state, "control.failed", str(exc), "error")
            return {**state, "failed": True, "control_loop": self._control_snapshot(control_state)}

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
            control_state = self._control_from_state(state)
            control_state.mark_refinement()
            self._record_trace(control_state, "control.refine", "Evaluation requested one refinement pass.", "warning")
            self.repository.add_log(
                run_id,
                "Tester Agent",
                "Feedback loop",
                "Testing or evaluation found issues. Sending feedback back to Backend and Frontend agents for one revision pass.",
                status="warning",
            )
            state["control_loop"] = self._control_snapshot(control_state)
            return "revise"
        if needs_revision:
            run_id = int(state["run_id"])
            message = "Evaluation failed after the available revision pass. Deployment approval is blocked."
            self.repository.update_run(run_id, status="failed", current_stage="testing", error=message)
            self.repository.add_log(
                run_id,
                "Evaluation",
                "Deployment blocked",
                message,
                status="error",
            )
            return "end"
        if state.get("evaluation_passed"):
            control_state = self._control_from_state(state)
            control_state.transition(ControlPhase.FINALIZE, "Evaluator Agent", stage="deployment_approval")
            self._record_trace(control_state, "control.finalize", "Build phase passed and is ready for human approval.", "success")
            self.long_term_memory.remember(
                "successful_solution",
                f"Requirement: {state['requirement']}\nArtifacts: {', '.join(sorted(state.get('artifacts', {})))}",
                source_run_id=int(state["run_id"]),
            )
        return "approval"

    def _control_from_state(self, state: SoftwareTeamState) -> ControlLoopState:
        raw = state.get("control_loop") or {}
        control_state = ControlLoopState(
            run_id=int(state["run_id"]),
            goal=state["requirement"],
            phase=ControlPhase(raw.get("phase", ControlPhase.SENSE.value)),
            current_agent=raw.get("current_agent") if isinstance(raw.get("current_agent"), str) else None,
            refinements=int(raw.get("refinements", 0)),
            retries=dict(raw.get("retries", {})) if isinstance(raw.get("retries"), dict) else {},
            cancelled=bool(raw.get("cancelled", False)),
            metadata=dict(raw.get("metadata", {})) if isinstance(raw.get("metadata"), dict) else {},
        )
        return control_state

    def _control_snapshot(self, control_state: ControlLoopState) -> dict[str, object]:
        return {
            "phase": control_state.phase.value,
            "current_agent": control_state.current_agent,
            "refinements": control_state.refinements,
            "retries": control_state.retries,
            "cancelled": control_state.cancelled,
            "metadata": control_state.metadata,
        }

    def _record_trace(
        self,
        control_state: ControlLoopState,
        event_type: str,
        message: str,
        status: str = "info",
    ) -> None:
        self.trace_recorder.record(
            TraceEvent(
                run_id=control_state.run_id,
                component=control_state.current_agent or "Agentic OS",
                event_type=event_type,
                message=message,
                status=status,
                metadata={
                    "phase": control_state.phase.value,
                    "refinements": control_state.refinements,
                    **control_state.metadata,
                },
            )
        )
