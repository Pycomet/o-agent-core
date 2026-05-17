import os
from typing import Optional

from .client import LLMClient
from .openai_client import OpenAIClient


class LLMClientFactory:
    """Factory for creating LLM client instances based on configuration."""

    @staticmethod
    def create_client(
        provider: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs,
    ) -> LLMClient:
        provider = provider or os.getenv("LLMCLIENT_PROVIDER", "openai")

        if provider == "openai":
            return OpenAIClient(
                model=model or os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                api_key=kwargs.get("api_key") or os.getenv("OPENAI_API_KEY"),
            )

        raise ValueError(f"Unsupported LLM provider: {provider}")


def get_default_llm_client() -> LLMClient:
    """Get the default LLM client based on environment configuration."""
    return LLMClientFactory.create_client()
