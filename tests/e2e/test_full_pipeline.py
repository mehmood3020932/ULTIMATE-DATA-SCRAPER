# tests/e2e/test_full_pipeline.py
# End-to-end full pipeline test

import asyncio
import pytest
import httpx
import websockets

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:3000/events"


@pytest.mark.asyncio
async def test_full_scraping_pipeline():
    """Test complete scraping flow from job creation to completion."""
    async with httpx.AsyncClient() as client:
        # 1. Login
        login_response = await client.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": "test@example.com", "password": "testpass"},
        )
        token = login_response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Create job
        job_response = await client.post(
            f"{BASE_URL}/api/v1/scraping/jobs",
            headers=headers,
            json={
                "instructions": {
                    "target_url": "https://quotes.toscrape.com",
                    "instructions": "Extract all quotes with authors",
                    "config": {"max_pages": 1},
                },
            },
        )
        job_id = job_response.json()["id"]
        assert job_id is not None
        
        # 3. Connect to WebSocket for realtime updates
        async with websockets.connect(
            WS_URL,
            extra_headers={"Authorization": f"Bearer {token}"},
        ) as ws:
            # Subscribe to job updates
            await ws.send(f'{{"action": "subscribe_job", "job_id": "{job_id}"}}')
            
            # Wait for completion (with timeout)
            try:
                while True:
                    msg = await asyncio.wait_for(ws.recv(), timeout=60)
                    data = json.loads(msg)
                    if data.get("status") in ["completed", "failed"]:
                        break
            except asyncio.TimeoutError:
                pytest.fail("Job timed out")
        
        # 4. Verify job result
        result_response = await client.get(
            f"{BASE_URL}/api/v1/jobs/{job_id}",
            headers=headers,
        )
        job_data = result_response.json()
        assert job_data["status"] == "completed"
        assert job_data["items_extracted"] > 0