import asyncio
import logging
import time

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

_OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class LLMError(Exception):
    pass


class LLMService:
    """OpenRouter-backed LLM client used by every pipeline stage."""

    def __init__(self):
        self.settings = get_settings()
        if not self.settings.openrouter_api_key:
            logger.warning(
                "OPENROUTER_API_KEY not set — every LLM call will fail until it is configured."
            )
        # Reused across calls for connection pooling — LLMService is a
        # long-lived singleton (constructed once by PipelineOrchestrator).
        self._http = httpx.AsyncClient(timeout=120.0)

    async def _complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        if not self.settings.openrouter_api_key:
            raise LLMError("OpenRouter API key not configured (OPENROUTER_API_KEY is unset)")

        model_name = self.settings.openrouter_model
        t0 = time.perf_counter()

        resp = await self._http.post(
            _OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {self.settings.openrouter_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
                # The pipeline needs a final JSON/XML response.  GPT-OSS can
                # spend its completion budget on visible reasoning and return
                # content=null, which leaves no structured result to parse.
                "reasoning": {"enabled": False},
            },
        )
        resp.raise_for_status()
        data = resp.json()

        try:
            choice = data["choices"][0]
            message = choice["message"]
            content = message["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError(f"OpenRouter response missing expected content: {data}") from exc

        # A successful HTTP response is not necessarily a usable completion.
        # Treat null, whitespace-only, and non-text content as a retryable LLM
        # failure so every pipeline stage reaches its existing fallback logic.
        if not isinstance(content, str) or not content.strip():
            finish_reason = choice.get("finish_reason", "unknown")
            reasoning = message.get("reasoning") or message.get("reasoning_content") or ""
            logger.warning(
                "OpenRouter returned no final text — model=%s finish_reason=%s reasoning_len=%d",
                model_name,
                finish_reason,
                len(reasoning) if isinstance(reasoning, str) else 0,
            )
            raise LLMError(
                "OpenRouter returned no final text "
                f"(model={model_name}, finish_reason={finish_reason})"
            )

        elapsed = time.perf_counter() - t0
        logger.debug(
            "LLM response received — model=%s  elapsed=%.2fs  response_len=%d chars",
            model_name,
            elapsed,
            len(content or ""),
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
        model_name = self.settings.openrouter_model
        last_error: Exception | None = None

        for attempt in range(retries):
            try:
                if attempt > 0:
                    wait = delay * (2 ** (attempt - 1))
                    logger.warning(
                        "LLM retry %d/%d for model=%s — waiting %.1fs after error: %s",
                        attempt + 1, retries, model_name, wait, last_error,
                    )
                    await asyncio.sleep(wait)
                return await self._complete(system_prompt, user_prompt, temperature, max_tokens)
            except Exception as exc:
                last_error = exc
                logger.error(
                    "LLM attempt %d/%d failed — model=%s  error=%s",
                    attempt + 1, retries, model_name, exc, exc_info=True,
                )

        raise LLMError(f"All {retries} attempts failed: {last_error}")
