import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_portfolio_returns_200(async_client: AsyncClient, auth_headers: dict):
    """Test that the portfolio endpoint returns a 200 OK."""
    response = await async_client.get("/v1/portfolio", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "portfolio" in data
    assert isinstance(data["portfolio"], list)

@pytest.mark.asyncio
async def test_get_portfolio_filters(async_client: AsyncClient, auth_headers: dict):
    """Test that the portfolio endpoint accepts status filters."""
    response = await async_client.get("/v1/portfolio?status=active", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    for item in data["portfolio"]:
        assert item["status"] == "active"
