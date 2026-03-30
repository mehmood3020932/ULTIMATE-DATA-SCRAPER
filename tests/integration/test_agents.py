# tests/integration/test_agents.py
# Agent service integration tests

import pytest
import httpx

BASE_URL = "http://localhost:8001"


@pytest.mark.asyncio
async def test_agent_service_health():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_list_agents():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/agents")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert len(data["agents"]) >= 12  # All 12+ agents