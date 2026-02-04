"""API routes for table management."""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
import secrets
from datetime import datetime, timezone
import os

from ..storage.base import TableStorage
from ..storage.memory import InMemoryTableStorage
from ..models import CreateTableRequest, TableResponse
from models.table_config import TableConfig

router = APIRouter(prefix="/api/tables", tags=["tables"])

# Global storage instance (in-memory for MVP)
_storage = InMemoryTableStorage()


def get_storage() -> TableStorage:
    """Dependency injection for storage."""
    return _storage


def get_game_ws_base() -> str:
    """Get the game service WebSocket base URL from env."""
    return os.getenv("GAME_WS_URL", "ws://localhost:8001")


@router.post("", response_model=TableResponse, status_code=201)
async def create_table(
    request: CreateTableRequest,
    storage: TableStorage = Depends(get_storage)
):
    """Create a new poker table."""
    table_id = secrets.token_urlsafe(8)
    config = TableConfig(
        table_id=table_id,
        name=request.name,
        small_blind=request.small_blind,
        big_blind=request.big_blind,
        max_players=request.max_players,
        turn_timeout_seconds=request.turn_timeout_seconds,
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    await storage.create_table(config)

    game_ws_base = get_game_ws_base()
    return TableResponse(
        **config.to_dict(),
        game_ws_url=f"{game_ws_base}/ws/{table_id}"
    )


@router.get("", response_model=List[TableResponse])
async def list_tables(storage: TableStorage = Depends(get_storage)):
    """List all active tables."""
    tables = await storage.list_tables()
    game_ws_base = get_game_ws_base()

    return [
        TableResponse(
            **t.to_dict(),
            game_ws_url=f"{game_ws_base}/ws/{t.table_id}"
        )
        for t in tables
    ]


@router.get("/{table_id}", response_model=TableResponse)
async def get_table(
    table_id: str,
    storage: TableStorage = Depends(get_storage)
):
    """Get table details by ID."""
    table = await storage.get_table(table_id)
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")

    game_ws_base = get_game_ws_base()
    return TableResponse(
        **table.to_dict(),
        game_ws_url=f"{game_ws_base}/ws/{table.table_id}"
    )


@router.delete("/{table_id}", status_code=204)
async def delete_table(
    table_id: str,
    storage: TableStorage = Depends(get_storage)
):
    """Delete a table."""
    success = await storage.delete_table(table_id)
    if not success:
        raise HTTPException(status_code=404, detail="Table not found")
