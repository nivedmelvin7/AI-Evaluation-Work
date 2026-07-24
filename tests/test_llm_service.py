"""
Tests for LLMService (OpenRouter is the sole LLM provider).

These mock the HTTP layer so they run offline and don't burn real API
quota — they check the retry/error wiring, not live model behaviour.
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.llm_service import LLMService, LLMError


def _make_service(api_key: str = "fake-key") -> LLMService:
    service = LLMService.__new__(LLMService)  # bypass __init__ (no real network client)
    service.settings = MagicMock()
    service.settings.openrouter_model = "qwen/qwen3.7-plus"
    service.settings.openrouter_api_key = api_key
    service._http = AsyncMock()
    return service


def _mock_response(content: Any) -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = {"choices": [{"message": {"content": content}}]}
    return resp


@pytest.mark.asyncio
async def test_successful_call_returns_content_and_correct_request_shape():
    service = _make_service()
    service._http.post = AsyncMock(return_value=_mock_response("<verification>ok</verification>"))

    result = await service.complete_with_retry("sys", "user", retries=3, delay=0)

    assert result == "<verification>ok</verification>"
    service._http.post.assert_awaited_once()
    call_kwargs = service._http.post.call_args.kwargs
    assert call_kwargs["json"]["model"] == "qwen/qwen3.7-plus"
    assert call_kwargs["headers"]["Authorization"] == "Bearer fake-key"
    assert call_kwargs["json"]["messages"][0] == {"role": "system", "content": "sys"}
    assert call_kwargs["json"]["messages"][1] == {"role": "user", "content": "user"}
    assert call_kwargs["json"]["reasoning"] == {"enabled": False}


@pytest.mark.asyncio
async def test_null_content_is_rejected_as_a_retryable_llm_error():
    service = _make_service()
    service._http.post = AsyncMock(return_value=_mock_response(None))

    with pytest.raises(LLMError, match="returned no final text"):
        await service.complete_with_retry("sys", "user", retries=1, delay=0)

    assert service._http.post.await_count == 1


@pytest.mark.asyncio
async def test_retries_on_transient_failure_then_succeeds():
    service = _make_service()
    service._http.post = AsyncMock(
        side_effect=[RuntimeError("transient hiccup"), _mock_response("result after retry")]
    )

    result = await service.complete_with_retry("sys", "user", retries=3, delay=0)

    assert result == "result after retry"
    assert service._http.post.await_count == 2


@pytest.mark.asyncio
async def test_all_retries_exhausted_raises_llm_error():
    service = _make_service()
    service._http.post = AsyncMock(side_effect=RuntimeError("persistent failure"))

    with pytest.raises(LLMError, match="All 3 attempts failed.*persistent failure"):
        await service.complete_with_retry("sys", "user", retries=3, delay=0)

    assert service._http.post.await_count == 3


@pytest.mark.asyncio
async def test_missing_api_key_raises_without_any_network_call():
    service = _make_service(api_key="")

    with pytest.raises(LLMError, match="OpenRouter API key not configured"):
        await service.complete_with_retry("sys", "user", retries=3, delay=0)

    service._http.post.assert_not_called()


@pytest.mark.asyncio
async def test_malformed_response_shape_raises_llm_error():
    service = _make_service()
    bad_response = MagicMock()
    bad_response.raise_for_status = MagicMock()
    bad_response.json.return_value = {"unexpected": "shape"}
    service._http.post = AsyncMock(return_value=bad_response)

    with pytest.raises(LLMError, match="All 3 attempts failed"):
        await service.complete_with_retry("sys", "user", retries=3, delay=0)


def test_init_does_not_raise_without_api_key(monkeypatch):
    """The app must still boot even with no OpenRouter key configured —
    the error should surface per-call, not at construction/import time."""
    from app import config as config_module
    from app.services import llm_service as llm_service_module

    settings = config_module.Settings(openrouter_api_key="")
    # llm_service.py did `from app.config import get_settings`, so it holds
    # its own binding — patching app.config.get_settings alone wouldn't
    # affect what llm_service actually calls.
    monkeypatch.setattr(llm_service_module, "get_settings", lambda: settings)

    service = LLMService()

    assert service.settings.openrouter_api_key == ""
