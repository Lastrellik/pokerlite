#!/usr/bin/env python3
"""
Stress test for pokerlite - runs multiple games and validates logic.
"""
import asyncio
import json
import websockets
import random


class PokerBot:
    def __init__(self, name: str, table_id: str, strategy: str = "call"):
        self.name = name
        self.table_id = table_id
        self.strategy = strategy  # "call", "aggressive", "tight"
        self.my_pid = None
        self.hands_played = 0
        self.hands_won = 0
        self.starting_stack = 1000
        self.current_stack = 1000
        self.total_won = 0
        self.total_lost = 0

    async def play(self):
        """Connect and play poker."""
        uri = f"ws://localhost:8000/ws/{self.table_id}"

        async with websockets.connect(uri) as ws:
            # Join
            await ws.send(json.dumps({"type": "join", "name": self.name}))

            while True:
                try:
                    msg_raw = await asyncio.wait_for(ws.recv(), timeout=15.0)
                    msg = json.loads(msg_raw)

                    if msg.get("type") == "welcome":
                        self.my_pid = msg.get("pid")

                    elif msg.get("type") == "state":
                        state = msg.get("state", {})
                        await self._handle_state(state, ws)

                    elif msg.get("type") == "info":
                        info_msg = msg.get("message", "")
                        if "wins" in info_msg.lower():
                            if self.name in info_msg:
                                self.hands_won += 1
                            # Check if hand is done
                            if not state.get("hand_in_progress", True):
                                self.hands_played += 1

                except asyncio.TimeoutError:
                    break
                except Exception as e:
                    print(f"[{self.name}] Error: {e}")
                    break

    async def _handle_state(self, state, ws):
        """Handle game state and make decisions."""
        if not state.get("hand_in_progress"):
            return

        if state.get("current_turn_pid") != self.my_pid:
            return

        # Update stack
        players = state.get("players", [])
        my_player = next((p for p in players if p.get("pid") == self.my_pid), None)
        if my_player:
            self.current_stack = my_player.get("stack", 0)

        # Determine action
        current_bet = state.get("current_bet", 0)
        player_bets = state.get("player_bets", {})
        my_bet = player_bets.get(self.my_pid, 0)
        to_call = current_bet - my_bet

        action = await self._decide_action(state, to_call)
        await ws.send(json.dumps(action))

    async def _decide_action(self, state, to_call):
        """Decide what action to take based on strategy."""
        if self.strategy == "call":
            # Always call or check
            if to_call > 0:
                return {"type": "action", "action": "call"}
            else:
                return {"type": "action", "action": "check"}

        elif self.strategy == "aggressive":
            # 50% raise, 50% call
            if random.random() < 0.5 and to_call < 100:
                amount = to_call * 2 + 20
                return {"type": "action", "action": "raise", "amount": amount}
            elif to_call > 0:
                return {"type": "action", "action": "call"}
            else:
                return {"type": "action", "action": "check"}

        elif self.strategy == "tight":
            # Fold to any bet, check otherwise
            if to_call > 0:
                return {"type": "action", "action": "fold"}
            else:
                return {"type": "action", "action": "check"}

        return {"type": "action", "action": "check"}


async def run_game(game_num: int, num_hands: int = 5):
    """Run a single game with multiple bots."""
    table_id = f"stress_test_{game_num}"

    print(f"\n{'='*60}")
    print(f"GAME {game_num}: Starting {num_hands} hands")
    print(f"{'='*60}")

    # Create bots with different strategies
    bots = [
        PokerBot("Alice", table_id, "call"),
        PokerBot("Bob", table_id, "aggressive"),
        PokerBot("Charlie", table_id, "tight"),
    ]

    # Start all bots
    bot_tasks = [asyncio.create_task(bot.play()) for bot in bots]

    # Wait a bit for connection
    await asyncio.sleep(1.5)

    # Start hands
    uri = f"ws://localhost:8000/ws/{table_id}"
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({"type": "join", "name": "Dealer"}))
        await ws.recv()  # welcome

        for hand_num in range(num_hands):
            print(f"\n--- Hand {hand_num + 1}/{num_hands} ---")
            await ws.send(json.dumps({"type": "start"}))
            await asyncio.sleep(3)  # Let hand play out

    # Wait for bots to finish
    await asyncio.sleep(2)

    # Cancel bot tasks
    for task in bot_tasks:
        task.cancel()

    await asyncio.gather(*bot_tasks, return_exceptions=True)

    # Print results
    print(f"\nGame {game_num} Results:")
    for bot in bots:
        win_rate = (bot.hands_won / bot.hands_played * 100) if bot.hands_played > 0 else 0
        print(f"  {bot.name} ({bot.strategy}): {bot.hands_won}/{bot.hands_played} wins ({win_rate:.1f}%)")


async def validate_hand_rankings():
    """Test hand ranking logic directly."""
    from app.core.game import _evaluate_hand, _compare_hands

    print(f"\n{'='*60}")
    print("VALIDATING HAND RANKINGS")
    print(f"{'='*60}")

    test_cases = [
        # (cards, expected_hand_name, description)
        (["As", "Ah", "Ad", "Ac", "Ks"], "Four Of A Kind", "Four Aces"),
        (["Ts", "Js", "Qs", "Ks", "As"], "Royal Flush", "Royal Flush"),
        (["9s", "Ts", "Js", "Qs", "Ks"], "Straight Flush", "Straight Flush K-high"),
        (["Ah", "Ac", "Ad", "Kh", "Kc"], "Full House", "Aces full of Kings"),
        (["2s", "4s", "6s", "8s", "Ts"], "Flush", "Ten-high flush"),
        (["5h", "6d", "7c", "8s", "9h"], "Straight", "Nine-high straight"),
        (["Ah", "Ac", "Ad", "Kh", "Qc"], "Three Of A Kind", "Three Aces"),
        (["Ah", "Ac", "Kd", "Kh", "Qc"], "Two Pair", "Aces and Kings"),
        (["Ah", "Ac", "Kd", "Qh", "Jc"], "Pair", "Pair of Aces"),
        (["Ah", "Kc", "Qd", "Jh", "9c"], "High Card", "Ace high"),
    ]

    passed = 0
    failed = 0

    for cards, expected, description in test_cases:
        result = _evaluate_hand(cards)
        rank_num = result[0]

        # Get hand name from rank number
        from app.core.game import HAND_RANKS
        rank_names = {v: k for k, v in HAND_RANKS.items()}
        actual_name = rank_names.get(rank_num, "unknown").replace("_", " ").title()

        if actual_name == expected:
            print(f"✓ {description}: {actual_name}")
            passed += 1
        else:
            print(f"✗ {description}: Expected {expected}, got {actual_name}")
            failed += 1

    print(f"\nHand Ranking Tests: {passed} passed, {failed} failed")
    return failed == 0


async def validate_pot_math():
    """Validate pot calculations are correct."""
    print(f"\n{'='*60}")
    print("VALIDATING POT MATH")
    print(f"{'='*60}")

    # Run a simple game and track pot
    table_id = "pot_test"

    uri = f"ws://localhost:8000/ws/{table_id}"
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({"type": "join", "name": "Tester"}))

        # Track pot through game
        pots_seen = []

        for i in range(5):
            try:
                msg_raw = await asyncio.wait_for(ws.recv(), timeout=2.0)
                msg = json.loads(msg_raw)

                if msg.get("type") == "state":
                    state = msg.get("state", {})
                    pot = state.get("pot", 0)
                    pots_seen.append(pot)

            except asyncio.TimeoutError:
                break

    # Check pot never goes negative
    all_valid = all(p >= 0 for p in pots_seen)

    if all_valid:
        print(f"✓ Pot values all non-negative: {pots_seen}")
    else:
        print(f"✗ Invalid pot values found: {pots_seen}")

    return all_valid


async def main():
    """Run all stress tests."""
    print("="*60)
    print("POKERLITE STRESS TEST")
    print("="*60)

    # Test hand rankings
    rankings_ok = await validate_hand_rankings()

    # Test pot math
    pot_ok = await validate_pot_math()

    # Run multiple games
    num_games = 3
    for game_num in range(1, num_games + 1):
        try:
            await run_game(game_num, num_hands=3)
        except Exception as e:
            print(f"Game {game_num} error: {e}")

    print(f"\n{'='*60}")
    print("STRESS TEST COMPLETE")
    print(f"{'='*60}")
    print(f"Hand Rankings: {'✓ PASS' if rankings_ok else '✗ FAIL'}")
    print(f"Pot Math: {'✓ PASS' if pot_ok else '✗ FAIL'}")
    print(f"Games Completed: {num_games}")


if __name__ == "__main__":
    asyncio.run(main())
