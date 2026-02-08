from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import os

from ..core.tables import get_table

router = APIRouter()


class TestConfig(BaseModel):
    """Configuration for test mode."""
    deck_seed: Optional[int] = None
    use_deterministic_deck: bool = False


@router.get("/api/health")
def health():
    return {"ok": True, "service": "pokerlite"}


@router.post("/api/test/tables/{table_id}/config")
async def set_test_config(table_id: str, config: TestConfig):
    """Set test configuration for a table (test mode only).

    Allows setting a deterministic deck seed for reproducible testing.
    Only available when not in production mode.
    """
    env = os.getenv("ENV", "development")
    if env == "production":
        raise HTTPException(status_code=403, detail="Not available in production")

    table = get_table(table_id)
    async with table.lock:
        table.deck_seed = config.deck_seed
        table.use_deterministic_deck = config.use_deterministic_deck

    return {
        "ok": True,
        "table_id": table_id,
        "config": {
            "deck_seed": config.deck_seed,
            "use_deterministic_deck": config.use_deterministic_deck,
        }
    }


@router.get("/api/test/tables/{table_id}/state")
async def get_test_state(table_id: str):
    """Get internal table state for test verification (test mode only).

    Returns internal state including deck, hole cards, and board for verification.
    Only available when not in production mode.
    """
    env = os.getenv("ENV", "development")
    if env == "production":
        raise HTTPException(status_code=403, detail="Not available in production")

    table = get_table(table_id)
    return {
        "table_id": table_id,
        "deck": table.deck[:10] if table.deck else [],  # First 10 cards only for safety
        "remaining_cards": len(table.deck) if table.deck else 0,
        "hole_cards": table.hole_cards,
        "board": table.board,
        "street": table.street,
        "pot": table.pot,
        "deck_seed": table.deck_seed,
        "use_deterministic_deck": table.use_deterministic_deck,
        "hand_in_progress": table.hand_in_progress,
        "players": {
            pid: {
                "name": p.name,
                "seat": p.seat,
                "stack": p.stack,
                "connected": p.connected,
                "role": p.role.value,
            }
            for pid, p in table.players.items()
        },
    }
