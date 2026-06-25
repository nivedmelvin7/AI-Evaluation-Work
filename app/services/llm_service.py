import asyncio
import logging
import time

from google import genai
from google.genai import types

from app.config import get_settings

logger = logging.getLogger(__name__)


class LLMError(Exception):
    pass


class LLMService:

    def __init__(self):
        self.settings = get_settings()
        self.client = genai.Client(api_key=self.settings.gemini_api_key)

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        use_fast_model: bool = False,
        max_tokens: int = 4096,
    ) -> str:
        model_name = self.settings.gemini_model
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        logger.debug(
            "LLM call — model=%s  temp=%.1f  max_tokens=%d  "
            "system_prompt_len=%d  user_prompt_len=%d",
            model_name,
            temperature,
            max_tokens,
            len(system_prompt),
            len(user_prompt),
        )

        t0 = time.perf_counter()
        response = await self.client.aio.models.generate_content(
            model=model_name,
            contents=user_prompt,
            config=config,
        )
        elapsed = time.perf_counter() - t0
        content = response.text
        logger.debug(
            "LLM response received — model=%s  elapsed=%.2fs  response_len=%d chars",
            model_name,
            elapsed,
            len(content),
        )
        return content

    async def complete_with_retry(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        use_fast_model: bool = False,
        max_tokens: int = 4096,
        retries: int = 3,
        delay: float = 2.0,
    ) -> str:
        model_name = self.settings.gemini_model
        last_error: Exception | None = None

        for attempt in range(retries):
            try:
                if attempt > 0:
                    wait = delay * (2 ** (attempt - 1))
                    logger.warning(
                        "LLM retry %d/%d for model=%s — waiting %.1fs after error: %s",
                        attempt + 1,
                        retries,
                        model_name,
                        wait,
                        last_error,
                    )
                    await asyncio.sleep(wait)

                return await self.complete(
                    system_prompt, user_prompt, temperature, use_fast_model, max_tokens
                )
            except Exception as exc:
                last_error = exc
                logger.error(
                    "LLM attempt %d/%d failed — model=%s  error=%s",
                    attempt + 1,
                    retries,
                    model_name,
                    exc,
                    exc_info=True,
                )

        raise LLMError(f"All {retries} attempts failed: {last_error}")
