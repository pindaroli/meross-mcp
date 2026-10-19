"""Integration tests for FastAPI REST API endpoints."""

import httpx
import pytest
from httpx import ASGITransport

from meross_mcp.app import create_app
from meross_mcp.client import MerossClientManager


@pytest.fixture
def app(mock_client_manager: MerossClientManager):
    return create_app(mock_client_manager.settings)


@pytest.mark.asyncio
async def test_healthz_endpoint(app) -> None:
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "meross-mcp"}


@pytest.mark.asyncio
async def test_rest_list_devices(app) -> None:
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/devices")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Smart Plug Studio"
    assert data[0]["has_electricity_meter"] is True


@pytest.mark.asyncio
async def test_rest_get_device_detail(app) -> None:
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/devices/uuid-plug-mss310")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Smart Plug Studio"
    assert data["online"] is True


@pytest.mark.asyncio
async def test_rest_turn_on_unauthorized_without_key(app) -> None:
    # When api_key is configured, missing header should fail with 401
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/devices/uuid-plug-mss310/on")
    assert response.status_code == 401
    assert "Invalid or missing X-API-Key" in response.json()["detail"]


@pytest.mark.asyncio
async def test_rest_turn_on_and_off_with_key(app) -> None:
    headers = {"X-API-Key": "test-api-key"}
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Turn ON
        res_on = await ac.post("/api/v1/devices/uuid-plug-mss310/on?channel=0", headers=headers)
        assert res_on.status_code == 200
        assert res_on.json()["channels"][0]["is_on"] is True

        # Turn OFF
        res_off = await ac.post("/api/v1/devices/uuid-plug-mss310/off?channel=0", headers=headers)
        assert res_off.status_code == 200
        assert res_off.json()["channels"][0]["is_on"] is False


@pytest.mark.asyncio
async def test_rest_toggle(app) -> None:
    headers = {"X-API-Key": "test-api-key"}
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/devices/uuid-plug-mss310/toggle?channel=0", headers=headers)
    assert res.status_code == 200
    assert res.json()["channels"][0]["is_on"] is True


@pytest.mark.asyncio
async def test_rest_power_telemetry(app) -> None:
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/devices/uuid-plug-mss310/power?channel=0")
    assert response.status_code == 200
    data = response.json()
    assert data["power_w"] == 45.5
    assert data["voltage_v"] == 230.2
    assert data["current_a"] == 0.198


@pytest.mark.asyncio
async def test_rest_device_not_found(app) -> None:
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/devices/unknown-device-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_mcp_mount_endpoint(app) -> None:
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Verify /mcp routes to FastMCP sub-app rather than returning 404
        response = await ac.get("/mcp")
    assert response.status_code != 404
