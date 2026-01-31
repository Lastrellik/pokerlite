import json
from typing import Optional
from .models import TableState

def public_state(table: TableState, viewer_pid: Optional[str] = None) -> dict:

    hole = None
    if viewer_pid and viewer_pid in table.hole_cards:
        hole = table.hole_cards.get(viewer_pid)

    return {
        "table_id": table.table_id,

        "players": [
            {
                "pid": p.pid,
                "name": p.name,
                "stack": p.stack,
                "seat": p.seat,
                "connected": p.connected,
            }
            for p in sorted(table.players.values(), key=lambda x: x.seat)
            if p.connected  # Only show connected players
        ],

        "hand_in_progress": table.hand_in_progress,
        "current_turn_pid": table.current_turn_pid,
        "turn_deadline": table.turn_deadline,
        "pot": table.pot,
        "board": table.board,
        "street": table.street,
        "current_bet": table.current_bet,
        "player_bets": table.player_bets,

        # private view
        "hole_cards": hole,
    }


async def broadcast_state(table: TableState) -> None:
    # Per-connection view (so later we can customize what each pid sees)
    for pid, ws in list(table.connections.items()):
        try:
            await ws.send_text(json.dumps({"type": "state", "state": public_state(table, pid)}))
        except Exception:
            # Ignore send errors; disconnect handler will clean up
            pass
