"""
Anthropic LLM client wrapper.
"""
import asyncio
from typing import Optional, Dict, Any, List
import anthropic
import structlog

from config import settings
from .base_llm_client import BaseLLMClient

logger = structlog.get_logger()


class AnthropicLLMClient(BaseLLMClient):
    """
    Wrapper for Anthropic Claude API with retry logic and error handling.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize Anthropic client.

        Args:
            api_key: Anthropic API key (defaults to settings)
            model: Model to use (defaults to settings)
        """
        self.api_key = api_key or settings.anthropic_api_key
        self.model = model or settings.llm_model
        self.client = anthropic.Anthropic(api_key=self.api_key)

    @property
    def provider_name(self) -> str:
        return "anthropic"

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
        Generate completion from Claude.

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
                - provider: Provider name
        """
        messages = [{"role": "user", "content": prompt}]

        for attempt in range(retry_attempts):
            try:
                logger.info(
                    "llm_generate_start",
                    provider="anthropic",
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    attempt=attempt + 1,
                )

                # Make API call
                response = await asyncio.to_thread(
                    self._sync_generate,
                    messages=messages,
                    system_prompt=system_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    timeout=timeout,
                )

                content = response.content[0].text

                logger.info(
                    "llm_generate_success",
                    provider="anthropic",
                    model=self.model,
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                )

                result = {
                    "content": content,
                    "usage": {
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens,
                    },
                    "model": response.model,
                    "provider": "anthropic",
                }

                # Parse JSON if requested
                if response_format == "json":
                    try:
                        parsed = self.extract_json(content)
                        result["parsed_json"] = parsed
                    except Exception as e:
                        logger.warning("json_parse_failed", error=str(e), content=content[:500])
                        result["parsed_json"] = None

                return result

            except anthropic.RateLimitError as e:
                logger.warning("llm_rate_limit", attempt=attempt + 1, error=str(e))
                if attempt < retry_attempts - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise

            except anthropic.APIError as e:
                logger.error("llm_api_error", attempt=attempt + 1, error=str(e))
                if attempt < retry_attempts - 1:
                    await asyncio.sleep(1)
                else:
                    raise

            except Exception as e:
                logger.error("llm_unexpected_error", attempt=attempt + 1, error=str(e))
                raise

        raise Exception("LLM generation failed after all retry attempts")

    def _sync_generate(
        self,
        messages: List[Dict],
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
        timeout: int,
    ):
        """Synchronous generation (to be called in thread)."""
        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
            "timeout": timeout,
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        return self.client.messages.create(**kwargs)

    async def generate_with_images(
        self,
        prompt: str,
        image_data: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Generate completion with image inputs (for document parsing).

        Args:
            prompt: User prompt
            image_data: List of image data dictionaries
            system_prompt: System prompt (optional)
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation

        Returns:
            Dict with generated content and metadata
        """
        messages = [
            {
                "role": "user",
                "content": [
                    *image_data,
                    {"type": "text", "text": prompt},
                ],
            }
        ]

        logger.info("llm_generate_with_images", provider="anthropic", num_images=len(image_data))

        response = await asyncio.to_thread(
            self._sync_generate,
            messages=messages,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=90,  # Longer timeout for image processing
        )

        content = response.content[0].text

        return {
            "content": content,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            "model": response.model,
            "provider": "anthropic",
        }
