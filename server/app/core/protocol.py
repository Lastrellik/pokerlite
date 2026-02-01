import json
from typing import Optional
from .models import TableState
from .player_utils import eligible_players

def public_state(table: TableState, viewer_pid: Optional[str] = None) -> dict:

    hole = None
    if viewer_pid and viewer_pid in table.hole_cards:
        hole = table.hole_cards.get(viewer_pid)

    # Calculate SB/BB positions
    sb_pid = None
    bb_pid = None
    if table.hand_in_progress:
        players = eligible_players(table)
        if len(players) >= 2:
            seats = sorted([p.seat for p in players])
            try:
                dealer_idx = seats.index(table.dealer_seat)
            except ValueError:
                dealer_idx = 0
            # In heads-up: dealer is SB, other player is BB
            # In 3+ players: SB is dealer+1, BB is dealer+2
            if len(players) == 2:
                sb_seat = seats[dealer_idx]
                bb_seat = seats[(dealer_idx + 1) % len(seats)]
            else:
                sb_seat = seats[(dealer_idx + 1) % len(seats)]
                bb_seat = seats[(dealer_idx + 2) % len(seats)]
            sb_pid = next((p.pid for p in players if p.seat == sb_seat), None)
            bb_pid = next((p.pid for p in players if p.seat == bb_seat), None)

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
        "dealer_seat": table.dealer_seat,
        "sb_pid": sb_pid,
        "bb_pid": bb_pid,
        "current_turn_pid": table.current_turn_pid,
        "turn_deadline": table.turn_deadline,
        "pot": table.pot,
        "board": table.board,
        "street": table.street,
        "current_bet": table.current_bet,
        "player_bets": table.player_bets,

        # private view
        "hole_cards": hole,

        # showdown data (only present after showdown, before next hand)
        "showdown": table.showdown_data,
    }


async def broadcast_state(table: TableState) -> None:
    # Per-connection view (so later we can customize what each pid sees)
    for pid, ws in list(table.connections.items()):
        try:
            await ws.send_text(json.dumps({"type": "state", "state": public_state(table, pid)}))
        except Exception:
            # Ignore send errors; disconnect handler will clean up
            pass
