from __future__ import annotations

import json

from langchain_core.messages import HumanMessage, SystemMessage

from database.repository import Repository
from llm_providers.factory import build_chat_provider


class RunChatService:
    """Read-only, run-scoped assistant for explaining workflow state.

    The service is intentionally isolated from workflow mutation. It can answer
    questions using persisted run data, but it cannot stop, resume, approve, or
    modify a run. That keeps the feature easy to remove or promote later.
    """

    def __init__(self, repository: Repository | None = None) -> None:
        self.repository = repository or Repository()

    def answer(self, run_id: int, user_message: str) -> tuple[object, object]:
        run = self.repository.get_run(run_id)
        if not run:
            raise ValueError("Run not found")

        user_row = self.repository.add_chat_message(run_id, "user", user_message.strip())
        answer = self._generate_answer(run_id, user_message.strip())
        assistant_row = self.repository.add_chat_message(run_id, "assistant", answer)
        return user_row, assistant_row

    def _generate_answer(self, run_id: int, user_message: str) -> str:
        run = self.repository.get_run(run_id)
        if not run:
            return "I could not find this run."

        digest = self._build_run_digest(run_id)
        system = (
            "You are Mission Control Chat, a read-only assistant for one software-agent run. "
            "Answer using only the provided run digest. Be concise, practical, and clear. "
            "If the user asks you to mutate the run, explain that chat is read-only and point them to dashboard controls."
        )
        try:
            provider = build_chat_provider(run.provider, run.model)
            provider.validate()
            response = provider.chat_model.invoke(
                [
                    SystemMessage(content=system),
                    HumanMessage(content=f"Run digest:\n{json.dumps(digest, indent=2)}\n\nUser question:\n{user_message}"),
                ]
            )
            return str(getattr(response, "content", response)).strip()
        except Exception as exc:
            return self._fallback_answer(digest, exc)

    def _build_run_digest(self, run_id: int) -> dict[str, object]:
        run = self.repository.get_run(run_id)
        evaluations = self.repository.list_evaluations(run_id)
        files = self.repository.list_files(run_id)
        logs = self.repository.list_logs(run_id)
        messages = self.repository.list_messages(run_id)
        return {
            "run_id": run_id,
            "requirement": run.requirement if run else "",
            "status": run.status if run else "unknown",
            "current_stage": run.current_stage if run else "unknown",
            "revision_count": self.repository.revision_count(run_id),
            "latest_evaluation": evaluations[-1].summary if evaluations else "No evaluation yet.",
            "evaluation_passed": evaluations[-1].passed if evaluations else None,
            "generated_files": [file.path for file in files[:80]],
            "recent_logs": [
                {
                    "agent": log.agent_name,
                    "action": log.action,
                    "status": log.status,
                    "summary": self._log_summary(log.output_summary),
                }
                for log in logs[-12:]
            ],
            "agent_summaries": [
                {"agent": message.agent_name, "summary": message.content}
                for message in messages[-10:]
            ],
        }

    def _fallback_answer(self, digest: dict[str, object], exc: Exception) -> str:
        files = digest.get("generated_files") or []
        file_count = len(files) if isinstance(files, list) else 0
        latest_evaluation = digest.get("latest_evaluation") or "No evaluation yet."
        return (
            "I could not reach the LLM for chat, so here is a local status summary.\n\n"
            f"Run {digest.get('run_id')} is `{digest.get('status')}` at `{digest.get('current_stage')}`.\n"
            f"Revision count: {digest.get('revision_count')}.\n"
            f"Generated files: {file_count}.\n"
            f"Latest evaluation: {latest_evaluation}\n\n"
            f"Chat provider error: {exc}"
        )

    @staticmethod
    def _log_summary(value: str) -> str:
        try:
            payload = json.loads(value)
            return str(payload.get("summary") or value)
        except json.JSONDecodeError:
            return value
