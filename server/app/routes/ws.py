from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import secrets

from ..core.tables import get_table
from ..core.protocol import broadcast_state
from ..core.game import handle_message, handle_disconnect

router = APIRouter()

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
