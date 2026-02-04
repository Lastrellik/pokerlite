"""Tests for table management endpoints."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    """Test health check endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"ok": True, "service": "lobby"}


@pytest.mark.asyncio
async def test_create_table():
    """Test creating a new table."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/tables", json={
            "name": "Test Table",
            "small_blind": 5,
            "big_blind": 10,
            "max_players": 6,
            "turn_timeout_seconds": 30,
        })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Table"
        assert data["small_blind"] == 5
        assert data["big_blind"] == 10
        assert data["max_players"] == 6
        assert "table_id" in data
        assert "game_ws_url" in data
        assert data["game_ws_url"].startswith("ws://")


@pytest.mark.asyncio
async def test_create_table_with_defaults():
    """Test creating a table with default values."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/tables", json={"name": "Default Table"})
        assert response.status_code == 201
        data = response.json()
        assert data["small_blind"] == 5
        assert data["big_blind"] == 10
        assert data["max_players"] == 8
        assert data["turn_timeout_seconds"] == 30


@pytest.mark.asyncio
async def test_list_tables():
    """Test listing tables."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create a table first
        await client.post("/api/tables", json={"name": "Table 1"})
        await client.post("/api/tables", json={"name": "Table 2"})

        # List tables
        response = await client.get("/api/tables")
        assert response.status_code == 200
        tables = response.json()
        assert len(tables) >= 2
        table_names = [t["name"] for t in tables]
        assert "Table 1" in table_names
        assert "Table 2" in table_names


@pytest.mark.asyncio
async def test_get_table():
    """Test getting a specific table."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create a table
        create_resp = await client.post("/api/tables", json={"name": "My Table"})
        table_id = create_resp.json()["table_id"]

        # Get the table
        response = await client.get(f"/api/tables/{table_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "My Table"
        assert response.json()["table_id"] == table_id


@pytest.mark.asyncio
async def test_get_nonexistent_table():
    """Test getting a table that doesn't exist."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/tables/nonexistent")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_table():
    """Test deleting a table."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create a table
        create_resp = await client.post("/api/tables", json={"name": "Temp Table"})
        table_id = create_resp.json()["table_id"]

        # Delete the table
        response = await client.delete(f"/api/tables/{table_id}")
        assert response.status_code == 204

        # Verify it's gone
        get_resp = await client.get(f"/api/tables/{table_id}")
        assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_nonexistent_table():
    """Test deleting a table that doesn't exist."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.delete("/api/tables/nonexistent")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_table_validation():
    """Test validation on table creation."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Empty name should fail
        response = await client.post("/api/tables", json={"name": ""})
        assert response.status_code == 422

        # Invalid small blind should fail
        response = await client.post("/api/tables", json={"name": "Test", "small_blind": 0})
        assert response.status_code == 422

        # Too many players should fail
        response = await client.post("/api/tables", json={"name": "Test", "max_players": 10})
        assert response.status_code == 422
