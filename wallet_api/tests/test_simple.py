import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.fixture
async def simple_client():
    """Fixture for a simple test client without database dependency"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_simple(simple_client):
    """Simple test to check client fixture"""
    response = await simple_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    print(f"Response: {data}")