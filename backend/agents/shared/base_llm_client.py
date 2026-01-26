"""
Base LLM client interface for multi-provider support.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import json


class BaseLLMClient(ABC):
    """
    Abstract base class for LLM clients.

    All LLM providers (Anthropic, OpenAI, etc.) must implement this interface.
    """

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        response_format: str = "text",  # "text" or "json"
        retry_attempts: int = 3,
        timeout: int = 60,
    ) -> Dict[str, Any]:
        """
        Generate completion from LLM.

        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation (0.0 to 1.0)
            response_format: Expected format ("text" or "json")
            retry_attempts: Number of retry attempts on failure
            timeout: Timeout in seconds

        Returns:
            Dict with:
                - content: Generated text
                - parsed_json: Parsed JSON (if response_format="json")
                - usage: Token usage statistics
                - model: Model used
                - provider: Provider name ("anthropic", "openai", etc.)
        """
        pass

    @abstractmethod
    async def generate_with_images(
        self,
        prompt: str,
        image_data: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Generate completion with image inputs.

        Args:
            prompt: User prompt
            image_data: List of image data dictionaries
            system_prompt: System prompt (optional)
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation

        Returns:
            Dict with generated content and metadata
        """
        pass

    @staticmethod
    def extract_json(text: str) -> Dict[str, Any]:
        """
        Extract JSON from LLM response.

        Handles cases where JSON is wrapped in markdown code blocks or has extra text.
        """
        # Try direct parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to find JSON in markdown code block
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            json_text = text[start:end].strip()
            return json.loads(json_text)

        # Try to find JSON between curly braces
        if "{" in text and "}" in text:
            start = text.find("{")
            end = text.rfind("}") + 1
            json_text = text[start:end]
            return json.loads(json_text)

        raise ValueError("No valid JSON found in response")

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name (e.g., 'anthropic', 'openai')."""
        pass
