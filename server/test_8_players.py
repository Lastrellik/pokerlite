#!/usr/bin/env python3
"""
Test poker game with 8 players.
"""
import asyncio
import json
import websockets


async def player_bot(name: str, table_id: str, seat_num: int):
    """Bot player that auto-calls."""
    uri = f"ws://localhost:8000/ws/{table_id}"
    my_pid = None

    async with websockets.connect(uri) as ws:
        # Join
        await ws.send(json.dumps({"type": "join", "name": name}))
        print(f"[{name}] Joined table")

        while True:
            try:
                msg_raw = await asyncio.wait_for(ws.recv(), timeout=20.0)
                msg = json.loads(msg_raw)

                if msg.get("type") == "welcome":
                    my_pid = msg.get("pid")
                    print(f"[{name}] Got PID: {my_pid}")

                elif msg.get("type") == "state":
                    state = msg.get("state", {})
                    hand_in_progress = state.get("hand_in_progress")
                    current_turn = state.get("current_turn_pid")
                    street = state.get("street")
                    pot = state.get("pot")
                    board = state.get("board", [])
                    players = state.get("players", [])

                    # Log interesting state changes
                    if hand_in_progress and current_turn == my_pid:
                        current_bet = state.get("current_bet", 0)
                        player_bets = state.get("player_bets", {})
                        my_bet = player_bets.get(my_pid, 0)
                        to_call = current_bet - my_bet

                        print(f"[{name}] My turn on {street}, pot={pot}, board={board}, to_call={to_call}")

                        # Auto-call or check
                        await asyncio.sleep(0.2)
                        if to_call > 0:
                            await ws.send(json.dumps({"type": "action", "action": "call"}))
                            print(f"[{name}] Called {to_call}")
                        else:
                            await ws.send(json.dumps({"type": "action", "action": "check"}))
                            print(f"[{name}] Checked")

                    elif not hand_in_progress and pot == 0 and len(players) == 8:
                        # Show final player count when hand ends
                        pass

                elif msg.get("type") == "info":
                    info_msg = msg.get("message", "")
                    print(f"[{name}] INFO: {info_msg}")
                    if "wins" in info_msg.lower():
                        await asyncio.sleep(1)
                        break

            except asyncio.TimeoutError:
                print(f"[{name}] Timeout")
                break
            except Exception as e:
                print(f"[{name}] Error: {e}")
                break

    print(f"[{name}] Disconnected")


async def game_starter(table_id: str, num_players: int):
    """Wait for players then start the game."""
    await asyncio.sleep(2)  # Wait for all players to connect

    uri = f"ws://localhost:8000/ws/{table_id}"
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({"type": "join", "name": "Dealer"}))
        await ws.recv()  # welcome

        # Wait a bit more
        await asyncio.sleep(1)

        # Check state
        msg = await ws.recv()
        state = json.loads(msg).get("state", {})
        players = state.get("players", [])

        print(f"\n{'='*60}")
        print(f"GAME STARTING WITH {len(players)} PLAYERS")
        print(f"{'='*60}")
        for p in players:
            print(f"  Seat {p['seat']}: {p['name']} ({p['stack']} chips)")
        print(f"{'='*60}\n")

        # Start the hand
        await ws.send(json.dumps({"type": "start"}))
        print("[DEALER] Hand started!\n")

        # Wait for hand to complete
        await asyncio.sleep(15)


async def main():
    """Run 8-player game."""
    table_id = "test_8_players"

    print("="*60)
    print("8-PLAYER POKER TEST")
    print("="*60)
    print()

    player_names = [
        "Alice", "Bob", "Charlie", "Diana",
        "Eve", "Frank", "Grace", "Henry"
    ]

    # Create all player bots
    player_tasks = [
        asyncio.create_task(player_bot(name, table_id, i+1))
        for i, name in enumerate(player_names)
    ]

    # Start game after players connect
    starter_task = asyncio.create_task(game_starter(table_id, len(player_names)))

    # Wait for all to finish
    await asyncio.gather(*player_tasks, starter_task, return_exceptions=True)

    print("\n" + "="*60)
    print("8-PLAYER TEST COMPLETE")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
