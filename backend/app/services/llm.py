"""Ollama chat-completion client. Local, CPU-only, zero-cost inference.

Requires `ollama serve` running locally and the configured model pulled
(`ollama pull <model>`) -- see Settings.ollama_model. Not covered by the
SQLite-backed unit test suite; see scripts/smoke_test_chat.py for a live
end-to-end check.
"""
from __future__ import annotations

import json
from collections.abc import AsyncIterator

import httpx

from app.config import get_settings


def _payload(settings, messages: list[dict[str, str]], stream: bool) -> dict:
    return {
        "model": settings.ollama_model,
        "messages": messages,
        "stream": stream,
        "keep_alive": "5m",
        "options": {"num_thread": 0},
    }


async def generate_chat_response(messages: list[dict[str, str]]) -> str:
    settings = get_settings()
    async with httpx.AsyncClient(
        base_url=settings.ollama_base_url, timeout=settings.ollama_timeout_seconds
    ) as client:
        response = await client.post("/api/chat", json=_payload(settings, messages, False))
        response.raise_for_status()
        return response.json()["message"]["content"]


async def stream_chat_response(messages: list[dict[str, str]]) -> AsyncIterator[str]:
    settings = get_settings()
    async with httpx.AsyncClient(
        base_url=settings.ollama_base_url, timeout=settings.ollama_timeout_seconds
    ) as client:
        async with client.stream(
            "POST", "/api/chat", json=_payload(settings, messages, True)
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line:
                    continue
                chunk = json.loads(line)
                token = chunk.get("message", {}).get("content", "")
                if token:
                    yield token
                if chunk.get("done"):
                    break
