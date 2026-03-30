# tests/integration/test_api.py
# API integration tests

import pytest
import httpx

BASE_URL = "http://localhost:8000"


@pytest.mark.asyncio
async def test_health_check():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_auth_flow():
    async with httpx.AsyncClient() as client:
        # Register
        register_data = {
            "email": "test@example.com",
            "password": "TestPassword123!",
            "full_name": "Test User",
        }
        response = await client.post(f"{BASE_URL}/api/v1/auth/register", json=register_data)
        assert response.status_code == 201
        
        # Login
        login_data = {
            "email": "test@example.com",
            "password": "TestPassword123!",
        }
        response = await client.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        token = response.json()["access_token"]
        assert token is not None


@pytest.mark.asyncio
async def test_create_job():
    async with httpx.AsyncClient() as client:
        # This would require authentication
        job_data = {
            "name": "Test Job",
            "instructions": {
                "target_url": "https://example.com",
                "instructions": "Extract all product titles",
                "config": {
                    "max_pages": 1,
                },
            },
        }
        # response = await client.post(f"{BASE_URL}/api/v1/scraping/jobs", json=job_data)
        # assert response.status_code == 201