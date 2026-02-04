from typing import Dict
import httpx
import os
from .models import TableState

_tables: Dict[str, TableState] = {}

LOBBY_URL = os.getenv("LOBBY_URL", "http://localhost:8000")

def get_table(table_id: str) -> TableState:
    if table_id not in _tables:
        # Fetch table config from lobby service
        try:
            response = httpx.get(f"{LOBBY_URL}/api/tables/{table_id}", timeout=5.0)
            if response.status_code == 200:
                config = response.json()
                _tables[table_id] = TableState(
                    table_id=table_id,
                    small_blind=config.get("small_blind", 5),
                    big_blind=config.get("big_blind", 10),
                    max_players=config.get("max_players", 8),
                    turn_timeout_seconds=config.get("turn_timeout_seconds", 30),
                )
            else:
                # Table not found in lobby, use defaults
                _tables[table_id] = TableState(table_id=table_id)
        except Exception as e:
            print(f"Failed to fetch table config from lobby: {e}")
            # Fall back to defaults
            _tables[table_id] = TableState(table_id=table_id)

    return _tables[table_id]
