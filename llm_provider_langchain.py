"""
Production-ready LLM provider with LangChain integration and error handling.

Supports multiple providers through LiteLLM with automatic retries and monitoring.
"""

from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import BaseOutputParser
from langchain_core.runnables import Runnable, RunnableConfig
from tenacity import retry, stop_after_attempt, wait_exponential

from config import get_config
from logging_config import get_logger

logger = get_logger(__name__)


class ChatLLMAdapter(BaseChatModel):
    """
    Adapts LiteLLM to LangChain's ChatModel interface.
    Provides retry logic, error handling, and monitoring.
    """

    provider: str
    model: str
    temperature: float = 0.2
    max_tokens: int = 2000
    timeout_seconds: int = 60

    class Config:
        """LangChain model config."""
        arbitrary_types_allowed = True

    @property
    def _llm_type(self) -> str:
        """Return the type of LLM."""
        return f"litellm-{self.provider}"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def _call(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> str:
        """Call LiteLLM with retry logic."""
        import litellm

        # Convert LangChain messages to LiteLLM format
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                formatted_messages.append({"role": "system", "content": msg.content})
            elif isinstance(msg, HumanMessage):
                formatted_messages.append({"role": "user", "content": msg.content})
            else:
                formatted_messages.append({"role": "assistant", "content": msg.content})

        logger.info(
            "calling_llm",
            model=self.model,
            provider=self.provider,
            message_count=len(messages),
        )

        try:
            response = litellm.completion(
                model=f"{self.provider}/{self.model}",
                messages=formatted_messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout=self.timeout_seconds,
                stop=stop,
            )
            
            content = response.choices[0].message.content
            logger.info(
                "llm_response_success",
                model=self.model,
                response_length=len(content),
            )
            return content
        except Exception as e:
            logger.error(
                "llm_call_failed",
                model=self.model,
                provider=self.provider,
                error=str(e),
            )
            raise

    async def _acall(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> str:
        """Async call (currently blocking, can be improved with async litellm)."""
        return self._call(messages, stop, run_manager, **kwargs)


def get_llm(config: "AppConfig | None" = None) -> ChatLLMAdapter:
    """Factory function to get configured LLM instance."""
    if config is None:
        config = get_config()

    return ChatLLMAdapter(
        provider=config.llm.provider,
        model=config.llm.model,
        temperature=config.llm.temperature,
        max_tokens=config.llm.max_tokens,
        timeout_seconds=config.llm.timeout_seconds,
    )


def get_runnable_llm(config: "AppConfig | None" = None) -> Runnable:
    """Get LLM as a LangChain Runnable for LCEL pipelines."""
    return get_llm(config)
