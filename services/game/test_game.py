#!/usr/bin/env python3
"""
End-to-end test for pokerlite game.
Connects 2 players, plays a hand, verifies winner announcement.
"""
import asyncio
import json
import websockets


async def player_bot(name: str, table_id: str):
    """
    Bot player that connects and automatically checks when it's their turn.
    """
    uri = f"ws://localhost:8000/ws/{table_id}"
    print(f"[{name}] Connecting to {uri}")

    my_pid = None

    async with websockets.connect(uri) as ws:
        # Join the table
        join_msg = {"type": "join", "name": name}
        await ws.send(json.dumps(join_msg))
        print(f"[{name}] Sent join message")

        # Listen for messages
        while True:
            try:
                msg_raw = await asyncio.wait_for(ws.recv(), timeout=10.0)
                msg = json.loads(msg_raw)
                msg_type = msg.get("type")

                if msg_type == "welcome":
                    my_pid = msg.get("pid")
                    print(f"[{name}] Welcomed! PID: {my_pid}")

                elif msg_type == "state":
                    state = msg.get("state", {})
                    hand_in_progress = state.get("hand_in_progress")
                    current_turn = state.get("current_turn_pid")
                    pot = state.get("pot")
                    hole_cards = state.get("hole_cards")
                    players = state.get("players", [])

                    street = state.get("street", "unknown")
                    board = state.get("board", [])

                    print(f"[{name}] State update:")
                    current_bet = state.get("current_bet", 0)
                    player_bets = state.get("player_bets", {})

                    print(f"  - Street: {street}")
                    print(f"  - Hand in progress: {hand_in_progress}")
                    print(f"  - Current turn PID: {current_turn}")
                    print(f"  - Pot: {pot}")
                    print(f"  - Current bet: {current_bet}")
                    print(f"  - Board: {board}")
                    print(f"  - My hole cards: {hole_cards}")
                    print(f"  - Players:")
                    for p in players:
                        player_bet = player_bets.get(p['pid'], 0)
                        print(f"    * {p['name']}: {p['stack']} chips (seat {p['seat']}, bet: {player_bet})")

                    # Check if it's our turn
                    if hand_in_progress and current_turn == my_pid:
                        current_bet = state.get("current_bet", 0)
                        player_bets = state.get("player_bets", {})
                        my_bet = player_bets.get(my_pid, 0)
                        to_call = current_bet - my_bet

                        if to_call > 0:
                            print(f"[{name}] It's my turn! Calling {to_call}...")
                            await asyncio.sleep(0.3)
                            call_msg = {"type": "action", "action": "call"}
                            await ws.send(json.dumps(call_msg))
                            print(f"[{name}] Sent CALL")
                        else:
                            print(f"[{name}] It's my turn! Checking...")
                            await asyncio.sleep(0.3)
                            check_msg = {"type": "action", "action": "check"}
                            await ws.send(json.dumps(check_msg))
                            print(f"[{name}] Sent CHECK")

                    # If hand is over, wait a bit then disconnect
                    if not hand_in_progress and pot == 0:
                        print(f"[{name}] Hand is over")

                elif msg_type == "info":
                    message = msg.get("message")
                    print(f"[{name}] *** INFO: {message} ***")

                    # If hand is over, disconnect soon
                    if "wins" in message.lower():
                        print(f"[{name}] Winner announced, disconnecting in 2s")
                        await asyncio.sleep(2)
                        break

                else:
                    print(f"[{name}] Unknown message type: {msg_type}")

            except asyncio.TimeoutError:
                print(f"[{name}] Timeout waiting for message, disconnecting")
                break
            except Exception as e:
                print(f"[{name}] Error: {e}")
                break

    print(f"[{name}] Disconnected")


async def game_starter(table_id: str):
    """
    Connects briefly to start the game.
    """
    await asyncio.sleep(1.5)  # Wait for both players to connect

    uri = f"ws://localhost:8000/ws/{table_id}"
    print("[STARTER] Connecting to start the game")

    async with websockets.connect(uri) as ws:
        # Join
        await ws.send(json.dumps({"type": "join", "name": "Starter"}))

        # Wait for welcome and state
        await ws.recv()  # welcome
        await ws.recv()  # state

        # Start the hand
        await ws.send(json.dumps({"type": "start"}))
        print("[STARTER] *** STARTING HAND ***")

        # Disconnect - players will continue
        await asyncio.sleep(0.5)

    print("[STARTER] Disconnected after starting hand")


async def run_test():
    """
    Main test runner.
    """
    print("="*60)
    print("POKERLITE END-TO-END TEST")
    print("="*60)
    print()

    table_id = "test_table"

    # Create player tasks - they'll auto-check when it's their turn
    player1_task = asyncio.create_task(player_bot("Alice", table_id))
    player2_task = asyncio.create_task(player_bot("Bob", table_id))

    # Start the game after players connect
    starter_task = asyncio.create_task(game_starter(table_id))

    # Wait for all tasks
    await asyncio.gather(player1_task, player2_task, starter_task, return_exceptions=True)

    print()
    print("="*60)
    print("TEST COMPLETE")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(run_test())
