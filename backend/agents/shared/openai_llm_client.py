"""
OpenAI LLM client wrapper.
"""
import asyncio
from typing import Optional, Dict, Any, List
import structlog
import base64

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from config import settings
from .base_llm_client import BaseLLMClient

logger = structlog.get_logger()


class OpenAILLMClient(BaseLLMClient):
    """
    Wrapper for OpenAI API with retry logic and error handling.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize OpenAI client.

        Args:
            api_key: OpenAI API key (defaults to settings)
            model: Model to use (defaults to settings)
        """
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "OpenAI package not installed. Install with: pip install openai"
            )

        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.openai_model or "gpt-4-turbo-preview"
        self.client = AsyncOpenAI(api_key=self.api_key)

    @property
    def provider_name(self) -> str:
        return "openai"

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
        Generate completion from OpenAI.

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
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        for attempt in range(retry_attempts):
            try:
                logger.info(
                    "llm_generate_start",
                    provider="openai",
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    attempt=attempt + 1,
                )

                # Prepare kwargs
                kwargs = {
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "timeout": timeout,
                }

                # Add JSON mode if requested
                if response_format == "json":
                    kwargs["response_format"] = {"type": "json_object"}

                # Make API call
                response = await self.client.chat.completions.create(**kwargs)

                content = response.choices[0].message.content

                logger.info(
                    "llm_generate_success",
                    provider="openai",
                    model=self.model,
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                )

                result = {
                    "content": content,
                    "usage": {
                        "input_tokens": response.usage.prompt_tokens,
                        "output_tokens": response.usage.completion_tokens,
                    },
                    "model": response.model,
                    "provider": "openai",
                }

                # Parse JSON if requested
                if response_format == "json":
                    try:
                        parsed = self.extract_json(content)
                        result["parsed_json"] = parsed
                    except Exception as e:
                        logger.warning(
                            "json_parse_failed", error=str(e), content=content[:500]
                        )
                        result["parsed_json"] = None

                return result

            except Exception as e:
                error_type = type(e).__name__
                logger.error(
                    "llm_error",
                    provider="openai",
                    attempt=attempt + 1,
                    error_type=error_type,
                    error=str(e),
                )

                if "rate_limit" in str(e).lower():
                    if attempt < retry_attempts - 1:
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    else:
                        raise
                elif attempt < retry_attempts - 1:
                    await asyncio.sleep(1)
                else:
                    raise

        raise Exception("LLM generation failed after all retry attempts")

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
            image_data: List of image data dictionaries (Anthropic format)
            system_prompt: System prompt (optional)
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation

        Returns:
            Dict with generated content and metadata
        """
        # Convert Anthropic image format to OpenAI format
        content = []

        for img in image_data:
            if img.get("type") == "image":
                source = img.get("source", {})
                if source.get("type") == "base64":
                    # OpenAI expects: data:image/jpeg;base64,{base64_data}
                    media_type = source.get("media_type", "image/jpeg")
                    data = source.get("data", "")
                    url = f"data:{media_type};base64,{data}"
                    content.append({"type": "image_url", "image_url": {"url": url}})

        content.append({"type": "text", "text": prompt})

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": content})

        logger.info("llm_generate_with_images", provider="openai", num_images=len(image_data))

        # Use vision-capable model
        vision_model = "gpt-4-vision-preview" if "gpt-4" in self.model else self.model

        response = await self.client.chat.completions.create(
            model=vision_model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=90,  # Longer timeout for image processing
        )

        content_text = response.choices[0].message.content

        return {
            "content": content_text,
            "usage": {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
            },
            "model": response.model,
            "provider": "openai",
        }
