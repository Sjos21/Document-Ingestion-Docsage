import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_live_returns_alive(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"


@pytest.mark.asyncio
async def test_ready_reports_dependency_statuses(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health/ready")
    assert response.status_code in (200, 503)
    body = response.json()
    assert "checks" in body
    assert set(body["checks"]) == {"postgres", "redis", "ollama"}