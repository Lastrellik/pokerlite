import json
from typing import Optional
from .models import TableState, PlayerRole
from .player_utils import eligible_players
from .waitlist import get_waitlist_position

def public_state(table: TableState, viewer_pid: Optional[str] = None) -> dict:
    # Get viewer's role
    viewer = table.players.get(viewer_pid) if viewer_pid else None
    viewer_role = viewer.role.value if viewer else None

    # Only show hole cards to seated players who are in the hand
    hole = None
    if viewer_pid and viewer_pid in table.hole_cards:
        if viewer and viewer.role == PlayerRole.SEATED:
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

    # Get waitlist position for viewer
    waitlist_position = get_waitlist_position(table, viewer_pid) if viewer_pid else 0

    # Build spectator list (names only)
    spectators = [
        {"pid": p.pid, "name": p.name}
        for p in table.players.values()
        if p.role == PlayerRole.SPECTATOR and p.connected
    ]

    # Build waitlist with positions
    waitlist = [
        {"pid": pid, "name": table.players[pid].name, "position": i + 1}
        for i, pid in enumerate(table.waitlist)
        if pid in table.players and table.players[pid].connected
    ]

    return {
        "table_id": table.table_id,

        # Only include seated players in main players list
        "players": [
            {
                "pid": p.pid,
                "name": p.name,
                "stack": p.stack,
                "seat": p.seat,
                "connected": p.connected,
                "folded": p.pid in table.folded_pids,
            }
            for p in sorted(table.players.values(), key=lambda x: x.seat)
            if p.connected and p.role == PlayerRole.SEATED
        ],

        "hand_in_progress": table.hand_in_progress,
        "dealer_seat": table.dealer_seat,
        "sb_pid": sb_pid,
        "bb_pid": bb_pid,
        "current_turn_pid": table.current_turn_pid,
        "turn_deadline": table.turn_deadline,
        "turn_timeout_seconds": table.turn_timeout_seconds,
        "pot": table.pot,
        "board": table.board,
        "street": table.street,
        "current_bet": table.current_bet,
        "player_bets": table.player_bets,

        # private view
        "hole_cards": hole,

        # showdown data (only present after showdown, before next hand)
        "showdown": table.showdown_data,

        # last action for UI animations
        "last_action": table.last_action,

        # Player role and management info
        "my_role": viewer_role,
        "waitlist_position": waitlist_position,
        "spectators": spectators,
        "waitlist": waitlist,
    }


async def broadcast_state(table: TableState) -> None:
    # Per-connection view (so later we can customize what each pid sees)
    for pid, ws in list(table.connections.items()):
        try:
            await ws.send_text(json.dumps({"type": "state", "state": public_state(table, pid)}))
        except Exception:
            # Ignore send errors; disconnect handler will clean up
            pass
