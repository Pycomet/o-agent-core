import os
from typing import Optional
from .client import LLMClient
from .trigger_vercel_client import TriggerVercelClient


class LLMClientFactory:
    """
    Factory for creating LLM client instances based on configuration.

    Supports Vercel AI SDK v5 (via Trigger.dev) and future Sovereign AI CEO.
    Clean, single-path architecture with no redundant clients.
    """

    @staticmethod
    def create_client(
        provider: Optional[str] = None, model: Optional[str] = None, **kwargs
    ) -> LLMClient:
        """
        Create an LLM client based on provider type.

        Args:
            provider: Provider name ('vercel', 'sovereign')
                     Defaults to LLMCLIENT_PROVIDER env var or 'vercel'
            model: Model name (provider-specific)
            **kwargs: Additional provider-specific arguments

        Returns:
            LLMClient instance

        Raises:
            ValueError: If provider is not supported
        """
        provider = provider or os.getenv("LLMCLIENT_PROVIDER", "vercel")

        if provider == "vercel":
            # Uses Vercel AI SDK v5 via Trigger.dev Node.js jobs
            return TriggerVercelClient(
                model=model or os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                api_key=kwargs.get("api_key") or os.getenv("TRIGGER_API_KEY"),
            )
        elif provider == "sovereign":
            raise NotImplementedError("Sovereign AI CEO client not yet implemented")
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")


# Convenience function for default client
def get_default_llm_client() -> LLMClient:
    """Get the default LLM client based on environment configuration"""
    return LLMClientFactory.create_client()
