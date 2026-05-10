from pydantic import BaseModel, Field


class AgentInput(BaseModel):
    run_id: int
    requirement: str
    focused_context: dict[str, str]
    artifacts: dict[str, str] = Field(default_factory=dict)
    messages: list[str] = Field(default_factory=list)
    bug_report: str = ""
    revision: bool = False


class AgentOutput(BaseModel):
    summary: str = Field(default="Agent completed its task.")
    artifacts: dict[str, str] = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list)
    bugs: list[str] = Field(default_factory=list)
    raw_response: str = ""
