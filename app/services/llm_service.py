"""
Unified LLM service supporting Groq (OpenAI-compatible) and Ollama.

Usage:
    from app.services.llm_service import LLMService
    service = LLMService()
    response = await service.complete(
        system_prompt="...",
        user_prompt="...",
        temperature=0.3,
        use_fast_model=False
    )
"""

import httpx
import asyncio
from app.config import get_settings


class LLMError(Exception):
    pass


class LLMService:

    def __init__(self):
        self.settings = get_settings()

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        use_fast_model: bool = False,
        max_tokens: int = 4096,
    ) -> str:
        """
        Returns the raw text content of the LLM response.
        Raises LLMError on failure.
        """
        if self.settings.llm_backend == "groq":
            return await self._groq_complete(
                system_prompt, user_prompt, temperature, use_fast_model, max_tokens
            )
        elif self.settings.llm_backend == "ollama":
            return await self._ollama_complete(
                system_prompt, user_prompt, temperature, use_fast_model, max_tokens
            )
        else:
            raise ValueError(f"Unknown LLM_BACKEND: {self.settings.llm_backend}")

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
        """Retry wrapper with exponential backoff."""
        last_error = None
        for attempt in range(retries):
            try:
                return await self.complete(
                    system_prompt, user_prompt, temperature, use_fast_model, max_tokens
                )
            except Exception as e:
                last_error = e
                if attempt < retries - 1:
                    await asyncio.sleep(delay * (2**attempt))
        raise LLMError(f"All {retries} attempts failed: {last_error}")

    async def _groq_complete(
        self, system: str, user: str, temperature: float, fast: bool, max_tokens: int
    ) -> str:
        model = (
            self.settings.groq_fast_model if fast else self.settings.groq_primary_model
        )
        headers = {
            "Authorization": f"Bearer {self.settings.groq_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{self.settings.groq_base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def _ollama_complete(
        self, system: str, user: str, temperature: float, fast: bool, max_tokens: int
    ) -> str:
        model = (
            self.settings.ollama_fast_model if fast else self.settings.ollama_primary_model
        )
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        async with httpx.AsyncClient(timeout=300.0) as client:
            resp = await client.post(
                f"{self.settings.ollama_base_url}/api/chat",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["message"]["content"]
