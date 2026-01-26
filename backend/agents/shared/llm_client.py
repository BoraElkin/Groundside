"""
LLM client wrapper - Multi-provider support.

This module provides backward compatibility by re-exporting the default LLM client.
For new code, use LLMFactory.create() to get the configured provider.
"""
from .anthropic_llm_client import AnthropicLLMClient
from .base_llm_client import BaseLLMClient
from .llm_factory import LLMFactory

# Backward compatibility: LLMClient now points to the factory's default client
# This maintains compatibility with existing code while allowing provider switching
LLMClient = AnthropicLLMClient  # Default for backward compatibility

__all__ = [
    "LLMClient",
    "BaseLLMClient",
    "AnthropicLLMClient",
    "LLMFactory",
]
