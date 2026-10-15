"""HTTP-level tests for /search: auth, validation, empty-index behavior.

Uses the standard SQLite test client -- these tests only exercise request
validation and auth wiring, not actual similarity ranking (see
test_retrieval.py for that, which requires real Postgres).
"""
import pytest
from httpx import AsyncClient

AUTH = "/api/v1/auth"
SEARCH = "/api/v1/search"


async def _register(client: AsyncClient, email: str, password: str = "password123") -> dict:
    response = await client.post(AUTH + "/register", json={"email": email, "password": password})
    assert response.status_code == 201
    return response.json()


def _auth_header(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.mark.asyncio
async def test_search_requires_authentication(client: AsyncClient) -> None:
    response = await client.post(SEARCH, json={"query": "test"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_search_rejects_blank_query(client: AsyncClient) -> None:
    tokens = await _register(client, "blank@example.com")
    response = await client.post(SEARCH, headers=_auth_header(tokens), json={"query": "   "})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_search_rejects_top_k_out_of_range(client: AsyncClient) -> None:
    tokens = await _register(client, "topk@example.com")
    response = await client.post(SEARCH, headers=_auth_header(tokens), json={"query": "test", "top_k": 100})
    assert response.status_code == 422


