from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import secrets
import asyncio
import httpx
import os

from ..core.tables import get_table, delete_table
from ..core.protocol import broadcast_state
from ..core.game import handle_message, handle_disconnect
from ..core.game_flow import check_turn_timeout
from ..core.player_utils import active_pids
from ..core.betting import is_betting_complete
from ..core.game_flow import advance_turn, advance_street, run_showdown
from ..core.auth import validate_token_and_load_user

router = APIRouter()

# Track active timeout checkers per table
_timeout_tasks: dict[str, asyncio.Task] = {}

LOBBY_URL = os.getenv("LOBBY_URL", "http://localhost:8000")


async def cleanup_empty_table(table_id: str) -> None:
    """Delete table from both game and lobby services if all players disconnected."""
    table = get_table(table_id)

    # Debug: show connected players
    connected_players = [p.name for p in table.players.values() if p.connected]
    print(f"[CLEANUP] Table {table_id} has {len(connected_players)} connected players: {connected_players}")

    if table.has_no_connected_players():
        print(f"[CLEANUP] Table {table_id} is empty, deleting...")

        # Delete from game service
        delete_table(table_id)

        # Delete from lobby service
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(f"{LOBBY_URL}/api/tables/{table_id}", timeout=5.0)
                if response.status_code == 204:
                    print(f"[CLEANUP] Table {table_id} deleted from lobby")
                else:
                    print(f"[CLEANUP] Failed to delete table {table_id} from lobby: {response.status_code}")
        except Exception as e:
            print(f"[CLEANUP] Error deleting table {table_id} from lobby: {e}")

        # Stop timeout checker task
        task = _timeout_tasks.pop(table_id, None)
        if task and not task.done():
            task.cancel()


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
                    # Clear turn state during runout (no one to act)
                    table.current_turn_pid = None
                    table.turn_deadline = None
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

    # Check for authentication token
    token = hello.get("token")
    user_id = None
    initial_stack = 1000  # Default for unauthenticated players

    if token:
        # Validate token and load user
        user_data = validate_token_and_load_user(token)
        if user_data:
            user, stack = user_data
            name = user.username
            pid = f"user_{user.id}"  # Use consistent PID based on user ID
            user_id = user.id
            initial_stack = stack
            print(f"[AUTH] Authenticated user {name} (ID: {user_id}) with stack: {stack}")
        else:
            await ws.send_text(json.dumps({"type": "error", "message": "Invalid authentication token"}))
            await ws.close()
            return
    else:
        # Guest player (no auth)
        name = (hello.get("name") or "guest")[:24]
        pid = hello.get("pid") or secrets.token_hex(8)
        print(f"[WS] Guest player {name} connecting (no auth)")

    async with table.lock:
        # Check if player is already connected
        if pid in table.connections:
            print(f"[WS] WARNING: Player {pid} ({name}) reconnecting - closing old connection")
            try:
                old_ws = table.connections[pid]
                await old_ws.close()
            except Exception as e:
                print(f"[WS] Error closing old connection: {e}")

        table.upsert_player(pid=pid, name=name, stack=initial_stack)
        table.connections[pid] = ws

        # Store user_id in player metadata for later stack updates
        if user_id:
            if not hasattr(table, 'user_ids'):
                table.user_ids = {}
            table.user_ids[pid] = user_id

        print(f"[WS] Player {pid} ({name}) connected to table {table_id} with {initial_stack} chips")

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
        print(f"[WS] Player {pid} ({name}) disconnected from table {table_id}")
        async with table.lock:
            table.connections.pop(pid, None)

            # Handle in-game disconnect (fold player out if needed)
            info_msg = handle_disconnect(table, pid)
            if info_msg:
                print(f"[WS] Disconnect handled: {info_msg}")

            # Mark player as disconnected (preserves their stack and data)
            table.mark_disconnected(pid)

        # Broadcast disconnect info if applicable
        if info_msg:
            for conn_pid, conn_ws in table.connections.items():
                try:
                    await conn_ws.send_text(json.dumps({"type": "info", "message": info_msg}))
                except Exception:
                    pass

        await broadcast_state(table)

        # Check if all players are disconnected and clean up if so
        await cleanup_empty_table(table_id)
