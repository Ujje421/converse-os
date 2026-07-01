"""Unit tests for API Gateway."""

import pytest
from httpx import AsyncClient, ASGITransport

from api_gateway.main import app
from api_gateway.config.settings import settings


@pytest.mark.asyncio
async def test_gateway_health():
    """Test gateway internal endpoints."""
    # Using mock redis for testing in a real scenario
    
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/health/live")
        assert response.status_code == 200
        assert response.json() == {"status": "alive"}


@pytest.mark.asyncio
async def test_proxy_route_not_found():
    """Test proxy routes that don't match the route map."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/v1/unknown")
        assert response.status_code == 404
