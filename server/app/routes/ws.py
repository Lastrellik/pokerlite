from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import secrets
import asyncio

from ..core.tables import get_table
from ..core.protocol import broadcast_state
from ..core.game import handle_message, handle_disconnect
from ..core.game_flow import check_turn_timeout
from ..core.player_utils import active_pids
from ..core.betting import is_betting_complete
from ..core.game_flow import advance_turn, advance_street, run_showdown

router = APIRouter()

# Track active timeout checkers per table
_timeout_tasks: dict[str, asyncio.Task] = {}


async def _timeout_checker(table_id: str):
    """Background task that checks for turn timeouts and handles runouts."""
    table = get_table(table_id)

    while True:
        await asyncio.sleep(1)  # Check every second

        # Stop if no connections
        if not table.connections:
            break

        info_msg = None

        async with table.lock:
            if not table.hand_in_progress:
                continue

            # Handle runout mode (all players all-in)
            if table.runout_in_progress:
                print(f"[RUNOUT] Processing runout on {table.street}")
                if table.street == "river":
                    # Runout complete, go to showdown
                    table.runout_in_progress = False
                    info_msg = run_showdown(table)
                    print(f"[RUNOUT] Showdown complete: {info_msg}")
                else:
                    # Deal next street
                    advance_street(table)
                    street_names = {"flop": "Flop", "turn": "Turn", "river": "River"}
                    street_name = street_names.get(table.street, table.street)
                    info_msg = f"📋 Dealing {street_name}: {' '.join(table.board)}"
                    print(f"[RUNOUT] Advanced to {table.street}: {' '.join(table.board)}")

                # Broadcast info message
                if info_msg:
                    for conn_pid, conn_ws in list(table.connections.items()):
                        try:
                            await conn_ws.send_text(json.dumps({"type": "info", "message": info_msg}))
                        except Exception:
                            pass

                # Broadcast state for this street
                await broadcast_state(table)

                if table.runout_in_progress:
                    # Wait 2 seconds before next street for animation
                    await asyncio.sleep(2)
                continue

            timed_out, auto_action = check_turn_timeout(table)
            if not timed_out:
                continue

            # Process the timeout
            current_pid = table.current_turn_pid
            player_name = table.players[current_pid].name if current_pid else "Player"

            # Set last_action for UI animation
            table.last_action = {"pid": current_pid, "action": "fold" if auto_action == "fold" else "check", "amount": 0}

            # Continue game flow after timeout
            active = active_pids(table)
            if len(active) == 1:
                info_msg = run_showdown(table)
            elif is_betting_complete(table, active):
                can_continue = advance_street(table)
                if not can_continue:
                    info_msg = run_showdown(table)
                else:
                    info_msg = f"{player_name} timed out - auto {auto_action}"
            else:
                advance_turn(table)
                info_msg = f"{player_name} timed out - auto {auto_action}"

        # Broadcast info message
        if info_msg:
            for conn_pid, conn_ws in list(table.connections.items()):
                try:
                    await conn_ws.send_text(json.dumps({"type": "info", "message": info_msg}))
                except Exception:
                    pass

        await broadcast_state(table)

    # Clean up task reference
    _timeout_tasks.pop(table_id, None)

@router.websocket("/ws/{table_id}")
async def ws_endpoint(ws: WebSocket, table_id: str):
    await ws.accept()
    table = get_table(table_id)

    # First message must be join
    try:
        first = await ws.receive_text()
        hello = json.loads(first)
    except Exception:
        await ws.close()
        return

    if hello.get("type") != "join":
        await ws.send_text(json.dumps({"type": "info", "message": "first message must be type=join"}))
        await ws.close()
        return

    name = (hello.get("name") or "player")[:24]
    pid = hello.get("pid") or secrets.token_hex(8)

    async with table.lock:
        table.upsert_player(pid=pid, name=name)
        table.connections[pid] = ws

    # Start timeout checker if not running
    if table_id not in _timeout_tasks or _timeout_tasks[table_id].done():
        _timeout_tasks[table_id] = asyncio.create_task(_timeout_checker(table_id))

    await ws.send_text(json.dumps({"type": "welcome", "pid": pid}))
    await broadcast_state(table)

    try:
        while True:
            raw = await ws.receive_text()
            msg = json.loads(raw)

            async with table.lock:
                info_msg = await handle_message(table, pid, msg)

            # Broadcast info message if there is one
            if info_msg:
                for conn_pid, conn_ws in table.connections.items():
                    try:
                        await conn_ws.send_text(json.dumps({"type": "info", "message": info_msg}))
                    except Exception:
                        pass

            await broadcast_state(table)

    except WebSocketDisconnect:
        async with table.lock:
            table.mark_disconnected(pid)
            table.connections.pop(pid, None)
            info_msg = handle_disconnect(table, pid)

        # Broadcast disconnect info if applicable
        if info_msg:
            for conn_pid, conn_ws in table.connections.items():
                try:
                    await conn_ws.send_text(json.dumps({"type": "info", "message": info_msg}))
                except Exception:
                    pass

        await broadcast_state(table)
