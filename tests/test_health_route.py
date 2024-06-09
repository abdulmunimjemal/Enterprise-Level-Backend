import pytest
from httpx import Response, AsyncClient

from src.apps.health.schemas import APIStatus


@pytest.mark.anyio
async def test_health(client: AsyncClient):
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data
    assert "uptime" in data
