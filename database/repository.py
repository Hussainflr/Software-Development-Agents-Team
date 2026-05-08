from collections.abc import Iterable
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import AgentLog, AgentMessage, AgentStatus, GeneratedFile, Run
from database.session import SessionLocal


AGENTS = ["Backend Agent", "Frontend Agent", "Tester Agent", "Deployment Agent"]


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
            log = AgentLog(
                run_id=run_id,
                agent_name=agent_name,
                action=action,
                status=status,
                output_summary=output_summary,
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

    def stop_requested(self, run_id: int) -> bool:
        run = self.get_run(run_id)
        return bool(run and run.stop_requested)

    def set_many_agent_statuses(self, run_id: int, agent_names: Iterable[str], status: str) -> None:
        for agent_name in agent_names:
            self.set_agent_status(run_id, agent_name, status)

