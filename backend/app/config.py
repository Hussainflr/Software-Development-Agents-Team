from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from config.defaults import DEFAULT_MODEL, DEFAULT_OLLAMA_BASE_URL, DEFAULT_PROVIDER


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Agentic Software Development Team"
    database_url: str = "sqlite:///./agent_team.db"
    generated_projects_dir: Path = Field(default=Path("generated_projects"))

    llm_provider: str = DEFAULT_PROVIDER
    llm_model: str = DEFAULT_MODEL
    ollama_base_url: str = DEFAULT_OLLAMA_BASE_URL

    openai_api_key: str | None = None
    anthropic_api_key: str | None = None

    @property
    def generated_root(self) -> Path:
        return self.generated_projects_dir.resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings()
