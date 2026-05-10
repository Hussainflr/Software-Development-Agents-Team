from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from config.defaults import DEFAULT_MODEL, DEFAULT_PROVIDER


class RunCreate(BaseModel):
    requirement: str = Field(min_length=5)
    provider: str = DEFAULT_PROVIDER
    model: str = DEFAULT_MODEL


class RunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    requirement: str
    provider: str
    model: str
    status: str
    current_stage: str
    approved_for_deployment: bool
    stop_requested: bool
    error: str | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None


class AgentStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    agent_name: str
    status: str
    updated_at: datetime


class AgentLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime
    agent_name: str
    action: str
    status: str
    output_summary: str


class GeneratedFileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    path: str
    content: str
    agent_name: str
    created_at: datetime


class AgentMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime
    agent_name: str
    role: str
    content: str


class ContextSnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime
    agent_name: str
    payload_json: str


class ShortTermMemoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    value: str
    updated_at: datetime


class LongTermMemoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: str
    summary: str
    source_run_id: int | None
    created_at: datetime


class EvaluationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime
    correctness: int
    completeness: int
    code_quality: int
    passed: bool
    summary: str


class RunDetailResponse(RunResponse):
    statuses: list[AgentStatusResponse]
    logs: list[AgentLogResponse]
    files: list[GeneratedFileResponse]
    messages: list[AgentMessageResponse]
    contexts: list[ContextSnapshotResponse]
    short_term_memory: list[ShortTermMemoryResponse]
    long_term_memory: list[LongTermMemoryResponse]
    evaluations: list[EvaluationResponse]


class ProviderOptionResponse(BaseModel):
    id: str
    label: str
    default_model: str
    requires_api_key: bool


class ProvidersResponse(BaseModel):
    default_provider: str
    default_model: str
    options: list[ProviderOptionResponse]


class ActionResponse(BaseModel):
    message: str
    run: RunResponse | None = None
