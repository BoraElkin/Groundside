"""
Factory for creating LLM clients based on provider.
"""
from typing import Optional
import structlog

from config import settings
from .base_llm_client import BaseLLMClient
from .anthropic_llm_client import AnthropicLLMClient
from .openai_llm_client import OpenAILLMClient, OPENAI_AVAILABLE

logger = structlog.get_logger()


class LLMFactory:
    """
    Factory for creating LLM clients.

    Supports multiple providers: Anthropic Claude, OpenAI GPT, etc.
    """

    @staticmethod
    def create(
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ) -> BaseLLMClient:
        """
        Create an LLM client for the specified provider.

        Args:
            provider: Provider name ("anthropic", "openai"). Defaults to settings.llm_provider
            api_key: API key for the provider. Defaults to settings
            model: Model name. Defaults to settings

        Returns:
            LLM client instance

        Raises:
            ValueError: If provider is unknown or not available
        """
        # Default to settings if not specified
        provider = provider or settings.llm_provider or "anthropic"
        provider = provider.lower()

        logger.info("creating_llm_client", provider=provider, model=model)

        if provider == "anthropic":
            return AnthropicLLMClient(api_key=api_key, model=model)

        elif provider == "openai":
            if not OPENAI_AVAILABLE:
                raise ValueError(
                    "OpenAI provider selected but openai package is not installed. "
                    "Install with: pip install openai"
                )
            return OpenAILLMClient(api_key=api_key, model=model)

        else:
            raise ValueError(
                f"Unknown LLM provider: {provider}. "
                f"Supported providers: anthropic, openai"
            )

    @staticmethod
    def get_available_providers() -> list:
        """
        Get list of available providers.

        Returns:
            List of provider names
        """
        providers = ["anthropic"]

        if OPENAI_AVAILABLE:
            providers.append("openai")

        return providers

    @staticmethod
    def create_default() -> BaseLLMClient:
        """
        Create LLM client using default settings.

        Returns:
            LLM client instance with default configuration
        """
        return LLMFactory.create()
