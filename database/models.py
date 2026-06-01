from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.defaults import DEFAULT_MODEL, DEFAULT_PROVIDER
from database.session import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    requirement: Mapped[str] = mapped_column(Text)
    provider: Mapped[str] = mapped_column(String(40), default=DEFAULT_PROVIDER)
    model: Mapped[str] = mapped_column(String(120), default=DEFAULT_MODEL)
    status: Mapped[str] = mapped_column(String(40), default="created")
    current_stage: Mapped[str] = mapped_column(String(80), default="requirement")
    approved_for_deployment: Mapped[bool] = mapped_column(Boolean, default=False)
    stop_requested: Mapped[bool] = mapped_column(Boolean, default=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    logs: Mapped[list["AgentLog"]] = relationship(back_populates="run", cascade="all, delete-orphan")
    files: Mapped[list["GeneratedFile"]] = relationship(back_populates="run", cascade="all, delete-orphan")
    statuses: Mapped[list["AgentStatus"]] = relationship(back_populates="run", cascade="all, delete-orphan")
    messages: Mapped[list["AgentMessage"]] = relationship(back_populates="run", cascade="all, delete-orphan")
    contexts: Mapped[list["ContextSnapshot"]] = relationship(back_populates="run", cascade="all, delete-orphan")
    short_term_memory: Mapped[list["ShortTermMemoryItem"]] = relationship(back_populates="run", cascade="all, delete-orphan")
    evaluations: Mapped[list["EvaluationResult"]] = relationship(back_populates="run", cascade="all, delete-orphan")
    chat_messages: Mapped[list["RunChatMessage"]] = relationship(back_populates="run", cascade="all, delete-orphan")


class AgentStatus(Base):
    __tablename__ = "agent_statuses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"), index=True)
    agent_name: Mapped[str] = mapped_column(String(80), index=True)
    status: Mapped[str] = mapped_column(String(40), default="idle")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    run: Mapped[Run] = relationship(back_populates="statuses")


class AgentLog(Base):
    __tablename__ = "agent_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    agent_name: Mapped[str] = mapped_column(String(80), index=True)
    action: Mapped[str] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(40), default="info")
    output_summary: Mapped[str] = mapped_column(Text)

    run: Mapped[Run] = relationship(back_populates="logs")


class AgentMessage(Base):
    __tablename__ = "agent_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    agent_name: Mapped[str] = mapped_column(String(80), index=True)
    role: Mapped[str] = mapped_column(String(40), default="assistant")
    content: Mapped[str] = mapped_column(Text)

    run: Mapped[Run] = relationship(back_populates="messages")


class GeneratedFile(Base):
    __tablename__ = "generated_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"), index=True)
    path: Mapped[str] = mapped_column(String(300), index=True)
    content: Mapped[str] = mapped_column(Text)
    agent_name: Mapped[str] = mapped_column(String(80), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    run: Mapped[Run] = relationship(back_populates="files")


class ContextSnapshot(Base):
    __tablename__ = "context_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    agent_name: Mapped[str] = mapped_column(String(80), index=True)
    payload_json: Mapped[str] = mapped_column(Text)

    run: Mapped[Run] = relationship(back_populates="contexts")


class ShortTermMemoryItem(Base):
    __tablename__ = "short_term_memory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"), index=True)
    key: Mapped[str] = mapped_column(String(120), index=True)
    value: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    run: Mapped[Run] = relationship(back_populates="short_term_memory")


class LongTermMemoryItem(Base):
    __tablename__ = "long_term_memory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category: Mapped[str] = mapped_column(String(120), index=True)
    summary: Mapped[str] = mapped_column(Text)
    source_run_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    correctness: Mapped[int] = mapped_column(Integer)
    completeness: Mapped[int] = mapped_column(Integer)
    code_quality: Mapped[int] = mapped_column(Integer)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    summary: Mapped[str] = mapped_column(Text)

    run: Mapped[Run] = relationship(back_populates="evaluations")


class RunChatMessage(Base):
    __tablename__ = "run_chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"), index=True)
    role: Mapped[str] = mapped_column(String(40), index=True)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)

    run: Mapped[Run] = relationship(back_populates="chat_messages")
