"""
Production-ready configuration management for the agentic application.

Follows 12-factor app principles and provides environment-based configuration
with proper validation and defaults.
"""

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings


class LLMConfig(BaseSettings):
    """LLM provider configuration."""

    provider: Literal["openai", "anthropic", "ollama", "litellm"] = "litellm"
    model: str = "gpt-4-turbo"
    temperature: float = 0.2
    max_tokens: int = 2000
    timeout_seconds: int = 60
    retry_count: int = 3


class DatabaseConfig(BaseSettings):
    """Database configuration."""

    url: str = "sqlite:///./agent_team.db"
    echo: bool = False
    pool_size: int = 10
    max_overflow: int = 20


class LoggingConfig(BaseSettings):
    """Logging configuration."""

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    format: str = "json"  # json or text
    include_timestamps: bool = True


class AppConfig(BaseSettings):
    """Root application configuration."""

    app_name: str = "Software Development Agents Team"
    version: str = "2.0.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False

    # Sub-configs
    llm: LLMConfig = LLMConfig()
    database: DatabaseConfig = DatabaseConfig()
    logging: LoggingConfig = LoggingConfig()

    # Paths
    project_root: Path = Path(__file__).parent
    generated_root: Path = project_root / "generated_projects"
    artifacts_root: Path = project_root / "artifacts"

    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"
        case_sensitive = False

    def __init__(self, **data):
        super().__init__(**data)
        # Create necessary directories
        self.generated_root.mkdir(exist_ok=True)
        self.artifacts_root.mkdir(exist_ok=True)


# Global config instance
_config: AppConfig | None = None


def get_config() -> AppConfig:
    """Get or create the global application configuration."""
    global _config
    if _config is None:
        _config = AppConfig()
    return _config


def set_config(config: AppConfig) -> None:
    """Set the global application configuration (useful for testing)."""
    global _config
    _config = config
