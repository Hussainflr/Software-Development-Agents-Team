import json
from collections.abc import Iterable
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import (
    AgentLog,
    AgentMessage,
    AgentStatus,
    ContextSnapshot,
    EvaluationResult,
    GeneratedFile,
    LongTermMemoryItem,
    Run,
    ShortTermMemoryItem,
)
from database.session import SessionLocal


AGENTS = [
    "Planner Agent",
    "Backend Agent",
    "Frontend Agent",
    "Reviewer Agent",
    "Security Agent",
    "Tester Agent",
    "Evaluator Agent",
    "Deployment Agent",
]

ACTIVE_RUN_STATUSES = ("running", "waiting_approval", "deployment")


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class Repository:
    """Small persistence facade so agents and APIs do not share ORM details."""

    def __init__(self, session_factory=SessionLocal):
        self.session_factory = session_factory

    def create_run(self, requirement: str, provider: str, model: str) -> Run:
        with self.session_factory() as session:
            run = Run(
                requirement=requirement,
                provider=provider,
                model=model,
                status="running",
                current_stage="requirement",
            )
            session.add(run)
            session.flush()
            for agent_name in AGENTS:
                session.add(AgentStatus(run_id=run.id, agent_name=agent_name, status="idle"))
            session.commit()
            return run

    def get_run(self, run_id: int) -> Run | None:
        with self.session_factory() as session:
            return session.get(Run, run_id)

    def list_runs(self, limit: int = 20) -> list[Run]:
        with self.session_factory() as session:
            statement = select(Run).order_by(Run.created_at.desc()).limit(limit)
            return list(session.scalars(statement))

    def count_active_runs(self) -> int:
        with self.session_factory() as session:
            statement = select(Run).where(Run.status.in_(ACTIVE_RUN_STATUSES))
            return len(list(session.scalars(statement)))

    def interrupt_active_runs(self) -> int:
        """Mark runs left active by a previous API process as interrupted.

        Background agent threads are process-local, so a server restart cannot
        safely resume an old ``running`` row without launching duplicate work.
        """
        with self.session_factory() as session:
            runs = list(session.scalars(select(Run).where(Run.status == "running")))
            for run in runs:
                run.status = "interrupted"
                run.stop_requested = True
                run.error = "Run was interrupted because Mission Control restarted. Use Resume Run to continue from this stage."
                run.updated_at = now_utc()
                session.add(
                    AgentLog(
                        run_id=run.id,
                        agent_name="Mission Control",
                        action="Run interrupted",
                        status="warning",
                        output_summary=json.dumps(
                            {
                                "agent": "Mission Control",
                                "action": "Run interrupted",
                                "status": "warning",
                                "summary": run.error,
                            }
                        ),
                    )
                )

            if runs:
                active_statuses = list(
                    session.scalars(
                        select(AgentStatus).where(
                            AgentStatus.run_id.in_([run.id for run in runs]),
                            AgentStatus.status.in_(("thinking", "working")),
                        )
                    )
                )
                for status_row in active_statuses:
                    status_row.status = "interrupted"
                    status_row.updated_at = now_utc()

            session.commit()
            return len(runs)

    def update_run(self, run_id: int, **fields) -> Run | None:
        with self.session_factory() as session:
            run = session.get(Run, run_id)
            if not run:
                return None
            for key, value in fields.items():
                setattr(run, key, value)
            run.updated_at = now_utc()
            session.commit()
            return run

    def add_log(
        self,
        run_id: int,
        agent_name: str,
        action: str,
        output_summary: str,
        status: str = "info",
    ) -> AgentLog:
        with self.session_factory() as session:
            payload = {
                "agent": agent_name,
                "action": action,
                "status": status,
                "summary": output_summary,
            }
            log = AgentLog(
                run_id=run_id,
                agent_name=agent_name,
                action=action,
                status=status,
                output_summary=json.dumps(payload),
            )
            session.add(log)
            session.commit()
            return log

    def list_logs(self, run_id: int) -> list[AgentLog]:
        with self.session_factory() as session:
            statement = select(AgentLog).where(AgentLog.run_id == run_id).order_by(AgentLog.timestamp.asc())
            return list(session.scalars(statement))

    def set_agent_status(self, run_id: int, agent_name: str, status: str) -> None:
        with self.session_factory() as session:
            statement = select(AgentStatus).where(
                AgentStatus.run_id == run_id,
                AgentStatus.agent_name == agent_name,
            )
            row = session.scalar(statement)
            if row is None:
                row = AgentStatus(run_id=run_id, agent_name=agent_name, status=status)
                session.add(row)
            else:
                row.status = status
                row.updated_at = now_utc()
            session.commit()

    def list_agent_statuses(self, run_id: int) -> list[AgentStatus]:
        with self.session_factory() as session:
            statement = select(AgentStatus).where(AgentStatus.run_id == run_id).order_by(AgentStatus.agent_name.asc())
            return list(session.scalars(statement))

    def add_message(self, run_id: int, agent_name: str, role: str, content: str) -> AgentMessage:
        with self.session_factory() as session:
            message = AgentMessage(run_id=run_id, agent_name=agent_name, role=role, content=content)
            session.add(message)
            session.commit()
            return message

    def list_messages(self, run_id: int) -> list[AgentMessage]:
        with self.session_factory() as session:
            statement = select(AgentMessage).where(AgentMessage.run_id == run_id).order_by(AgentMessage.timestamp.asc())
            return list(session.scalars(statement))

    def upsert_generated_files(self, run_id: int, agent_name: str, artifacts: dict[str, str]) -> None:
        with self.session_factory() as session:
            for path, content in artifacts.items():
                statement = select(GeneratedFile).where(
                    GeneratedFile.run_id == run_id,
                    GeneratedFile.path == path,
                )
                existing = session.scalar(statement)
                if existing:
                    existing.content = content
                    existing.agent_name = agent_name
                    existing.created_at = now_utc()
                else:
                    session.add(
                        GeneratedFile(
                            run_id=run_id,
                            path=path,
                            content=content,
                            agent_name=agent_name,
                        )
                    )
            session.commit()

    def list_files(self, run_id: int) -> list[GeneratedFile]:
        with self.session_factory() as session:
            statement = select(GeneratedFile).where(GeneratedFile.run_id == run_id).order_by(GeneratedFile.path.asc())
            return list(session.scalars(statement))

    def add_context_snapshot(self, run_id: int, agent_name: str, payload: dict[str, str]) -> ContextSnapshot:
        with self.session_factory() as session:
            row = ContextSnapshot(run_id=run_id, agent_name=agent_name, payload_json=json.dumps(payload, indent=2))
            session.add(row)
            session.commit()
            return row

    def list_context_snapshots(self, run_id: int) -> list[ContextSnapshot]:
        with self.session_factory() as session:
            statement = (
                select(ContextSnapshot)
                .where(ContextSnapshot.run_id == run_id)
                .order_by(ContextSnapshot.timestamp.asc())
            )
            return list(session.scalars(statement))

    def upsert_short_term_memory(self, run_id: int, key: str, value: str) -> None:
        with self.session_factory() as session:
            statement = select(ShortTermMemoryItem).where(
                ShortTermMemoryItem.run_id == run_id,
                ShortTermMemoryItem.key == key,
            )
            row = session.scalar(statement)
            if row:
                row.value = value
                row.updated_at = now_utc()
            else:
                session.add(ShortTermMemoryItem(run_id=run_id, key=key, value=value))
            session.commit()

    def list_short_term_memory(self, run_id: int) -> list[ShortTermMemoryItem]:
        with self.session_factory() as session:
            statement = (
                select(ShortTermMemoryItem)
                .where(ShortTermMemoryItem.run_id == run_id)
                .order_by(ShortTermMemoryItem.updated_at.asc())
            )
            return list(session.scalars(statement))

    def revision_count(self, run_id: int) -> int:
        """Return the latest known refinement pass count for a run."""
        rows = self.list_short_term_memory(run_id)
        for row in reversed(rows):
            if row.key == "revision_count":
                try:
                    return max(0, int(row.value))
                except ValueError:
                    return 0

        # Backward-compatible fallback for runs created before revision_count
        # was persisted. Backend revision snapshots are created once per pass.
        count = 0
        for snapshot in self.list_context_snapshots(run_id):
            if snapshot.agent_name != "Backend Agent":
                continue
            try:
                payload = json.loads(snapshot.payload_json)
            except json.JSONDecodeError:
                continue
            if payload.get("current_task") == "backend_revision":
                count += 1
        return count

    def add_long_term_memory(
        self,
        category: str,
        summary: str,
        source_run_id: int | None = None,
    ) -> LongTermMemoryItem:
        with self.session_factory() as session:
            row = LongTermMemoryItem(category=category, summary=summary, source_run_id=source_run_id)
            session.add(row)
            session.commit()
            return row

    def search_long_term_memory(self, query: str, limit: int = 5) -> list[LongTermMemoryItem]:
        with self.session_factory() as session:
            terms = [term.lower() for term in query.split() if len(term) > 3]
            rows = list(session.scalars(select(LongTermMemoryItem).order_by(LongTermMemoryItem.created_at.desc())))
            if not terms:
                return rows[:limit]
            scored = [
                row
                for row in rows
                if any(term in f"{row.category} {row.summary}".lower() for term in terms)
            ]
            return scored[:limit]

    def list_long_term_memory(self, limit: int = 20) -> list[LongTermMemoryItem]:
        with self.session_factory() as session:
            statement = select(LongTermMemoryItem).order_by(LongTermMemoryItem.created_at.desc()).limit(limit)
            return list(session.scalars(statement))

    def add_evaluation(
        self,
        run_id: int,
        correctness: int,
        completeness: int,
        code_quality: int,
        passed: bool,
        summary: str,
    ) -> EvaluationResult:
        with self.session_factory() as session:
            row = EvaluationResult(
                run_id=run_id,
                correctness=correctness,
                completeness=completeness,
                code_quality=code_quality,
                passed=passed,
                summary=summary,
            )
            session.add(row)
            session.commit()
            return row

    def list_evaluations(self, run_id: int) -> list[EvaluationResult]:
        with self.session_factory() as session:
            statement = (
                select(EvaluationResult)
                .where(EvaluationResult.run_id == run_id)
                .order_by(EvaluationResult.timestamp.asc())
            )
            return list(session.scalars(statement))

    def stop_requested(self, run_id: int) -> bool:
        run = self.get_run(run_id)
        return bool(run and run.stop_requested)

    def set_many_agent_statuses(self, run_id: int, agent_names: Iterable[str], status: str) -> None:
        for agent_name in agent_names:
            self.set_agent_status(run_id, agent_name, status)
