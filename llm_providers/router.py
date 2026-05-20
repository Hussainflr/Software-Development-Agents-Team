from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any

from llm_providers.factory import build_chat_provider, suggested_provider_model


@dataclass(frozen=True)
class ModelRoute:
    provider: str
    model: str
    fallback_provider: str | None = None
    fallback_model: str | None = None


@dataclass(frozen=True)
class ModelInvocationMetrics:
    provider: str
    model: str
    latency_ms: int
    input_tokens_estimate: int
    output_tokens_estimate: int
    estimated_cost_usd: float


class ModelRouter:
    """LiteLLM-style router facade for future fallback, metrics, and streaming."""

    def route(self, provider: str | None, model: str | None) -> ModelRoute:
        if provider and model:
            fallback_provider, fallback_model = suggested_provider_model(
                {"detected_model": None, "ollama_running": False, "ollama_models": []}
            )
            return ModelRoute(provider=provider, model=model, fallback_provider=fallback_provider, fallback_model=fallback_model)
        selected_provider, selected_model = suggested_provider_model(
            {"detected_model": None, "ollama_running": False, "ollama_models": []}
        )
        return ModelRoute(provider=selected_provider, model=selected_model)

    def build_chat_model(self, provider: str | None, model: str | None) -> Any:
        route = self.route(provider, model)
        return build_chat_provider(route.provider, route.model).chat_model

    def measure(self, provider: str, model: str, prompt: str, output: str, started_at: float) -> ModelInvocationMetrics:
        latency_ms = int((perf_counter() - started_at) * 1000)
        input_tokens = self._estimate_tokens(prompt)
        output_tokens = self._estimate_tokens(output)
        return ModelInvocationMetrics(
            provider=provider,
            model=model,
            latency_ms=latency_ms,
            input_tokens_estimate=input_tokens,
            output_tokens_estimate=output_tokens,
            estimated_cost_usd=self._estimate_cost(provider, input_tokens, output_tokens),
        )

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        return max(1, round(len(text) / 4))

    @staticmethod
    def _estimate_cost(provider: str, input_tokens: int, output_tokens: int) -> float:
        if provider == "ollama":
            return 0.0
        # Conservative placeholder table until provider-specific pricing is configured.
        return round(((input_tokens * 0.0000005) + (output_tokens * 0.0000015)), 6)
