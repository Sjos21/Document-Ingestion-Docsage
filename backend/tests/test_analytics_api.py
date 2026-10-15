import pytest
from httpx import AsyncClient

AUTH = "/api/v1/auth"
ANALYTICS = "/api/v1/analytics"


async def _register(client: AsyncClient, email: str) -> dict:
    r = await client.post(AUTH + "/register", json={"email": email, "password": "password123"})
    assert r.status_code == 201
    return r.json()


def _auth(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.mark.asyncio
async def test_analytics_requires_auth(client: AsyncClient) -> None:
    assert (await client.get(f"{ANALYTICS}/uploads/daily")).status_code == 401


@pytest.mark.asyncio
async def test_analytics_endpoints_return_empty_lists_when_no_data(client: AsyncClient) -> None:
    tokens = await _register(client, "analytics@example.com")
    for path in ["uploads/daily", "searches/daily", "chats/daily", "top-uploaders", "failures", "zero-result-queries"]:
        r = await client.get(f"{ANALYTICS}/{path}", headers=_auth(tokens))
        assert r.status_code == 200
        assert r.json() == []