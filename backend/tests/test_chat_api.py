import pytest
from httpx import AsyncClient

from app.services import chat as chat_service

AUTH = "/api/v1/auth"
CHAT = "/api/v1/chat"


async def _register(client: AsyncClient, email: str, password: str = "password123") -> dict:
    response = await client.post(AUTH + "/register", json={"email": email, "password": password})
    assert response.status_code == 201
    return response.json()


def _auth_header(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.mark.asyncio
async def test_chat_requires_authentication(client: AsyncClient) -> None:
    response = await client.post(CHAT, json={"message": "hi"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_chat_refuses_without_context(client: AsyncClient, monkeypatch) -> None:
    async def fake_search_chunks_traced(**kwargs):
        from app.services.retrieval import SearchTrace
        return [], SearchTrace(0, 0, 0, 0, 0, 0, 0)

    monkeypatch.setattr(chat_service, "search_chunks_traced", fake_search_chunks_traced)

    tokens = await _register(client, "chatnoctx@example.com")
    response = await client.post(CHAT, headers=_auth_header(tokens), json={"message": "anything"})

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == chat_service.NO_CONTEXT_ANSWER
    assert body["sources"] == []


@pytest.mark.asyncio
async def test_chat_session_history_is_user_scoped(client: AsyncClient, monkeypatch) -> None:
    async def fake_search_chunks_traced(**kwargs):
        from app.services.retrieval import SearchTrace
        return [], SearchTrace(0, 0, 0, 0, 0, 0, 0)

    monkeypatch.setattr(chat_service, "search_chunks_traced", fake_search_chunks_traced)

    tokens_a = await _register(client, "chata@example.com")
    tokens_b = await _register(client, "chatb@example.com")

    response = await client.post(CHAT, headers=_auth_header(tokens_a), json={"message": "hello"})
    session_id = response.json()["session_id"]

    own = await client.get(f"{CHAT}/sessions/{session_id}/messages", headers=_auth_header(tokens_a))
    other = await client.get(f"{CHAT}/sessions/{session_id}/messages", headers=_auth_header(tokens_b))

    assert own.status_code == 200
    assert len(own.json()) == 2
    assert other.status_code == 404