"""
Player action handlers.
"""
from typing import Dict, Any, Optional
from .models import TableState
from .player_utils import active_pids
from .betting import process_call, process_raise, is_betting_complete
from .game_flow import advance_turn, advance_street, run_showdown, start_new_hand, check_turn_timeout
from .constants import VALID_ACTIONS


async def handle_message(table: TableState, pid: str, msg: Dict[str, Any]) -> Optional[str]:
    """
    Handle incoming player messages.
    Returns optional info message to broadcast.
    """
    mtype = msg.get("type")

    if mtype == "start":
        start_new_hand(table)
        return None

    if mtype == "action":
        return await _handle_action(table, pid, msg)

    return None


async def _handle_action(table: TableState, pid: str, msg: Dict[str, Any]) -> Optional[str]:
    """Handle player action (fold, check, call, raise)."""
    # Check for timeout first
    timed_out, auto_action = check_turn_timeout(table)
    if timed_out:
        # Player timed out before their action, process timeout
        current_pid = table.current_turn_pid
        player_name = table.players[current_pid].name if current_pid else "Player"

        # Continue game flow after timeout
        active = active_pids(table)
        if len(active) == 1:
            return run_showdown(table)

        if is_betting_complete(table, active):
            can_continue = advance_street(table)
            if not can_continue:
                return run_showdown(table)
        else:
            advance_turn(table)

        return f"{player_name} timed out - auto {auto_action}"

    action = msg.get("action")
    amount = msg.get("amount", 0)

    if action not in VALID_ACTIONS:
        return None

    # Must be your turn
    if table.current_turn_pid != pid:
        return None

    player = table.players[pid]
    player_current_bet = table.player_bets.get(pid, 0)

    # Mark player as having acted
    table.players_acted.add(pid)

    # Record last action for UI animations
    table.last_action = {"pid": pid, "action": action, "amount": amount}

    # Handle fold
    if action == "fold":
        table.folded_pids.add(pid)

        # Check if only one player remains
        active = active_pids(table)
        if len(active) == 1:
            return run_showdown(table)

    # Handle check
    elif action == "check":
        # Can only check if no bet to call
        if table.current_bet > player_current_bet:
            return None  # Invalid action

    # Handle call
    elif action == "call":
        process_call(table, pid)

    # Handle raise
    elif action == "raise":
        process_raise(table, pid, amount)

    # Handle all-in
    elif action == "all_in":
        # All-in is a raise with the player's entire stack
        all_in_amount = player.stack + player_current_bet
        process_raise(table, pid, all_in_amount)

    # Check if betting round is complete
    active = active_pids(table)
    if is_betting_complete(table, active):
        # Check if we need to run out the board (at most one player can still bet)
        players_with_chips = [apid for apid in active if table.players[apid].stack > 0]

        if len(players_with_chips) <= 1 and len(active) > 1:
            # At most one player has chips - no more betting possible, run out the board
            table.runout_in_progress = True
            table.current_turn_pid = None  # No one to act

            # Reveal all hole cards for the runout (standard poker rules)
            table.showdown_data = {
                "players": {
                    pid: {"hole_cards": table.hole_cards.get(pid, [])}
                    for pid in active
                },
                "winner_pids": [],  # No winner yet
                "runout": True,  # Flag to indicate this is a runout reveal, not final showdown
            }
            return None  # Runout task will handle the rest
        # Try to advance to next street
        can_continue = advance_street(table)
        if not can_continue:
            # After river, go to showdown
            return run_showdown(table)
        return None

    advance_turn(table)
    return None


def handle_disconnect(table: TableState, pid: str) -> Optional[str]:
    """
    Handles a player disconnect. Auto-folds them if hand is in progress.
    Returns info message if applicable.
    """
    if not table.hand_in_progress:
        return None

    # Fold the disconnected player
    if pid not in table.folded_pids:
        table.folded_pids.add(pid)

        # Check if only one player remains
        active = active_pids(table)
        if len(active) == 1:
            return run_showdown(table)
        elif len(active) == 0:
            # No one left, end hand
            from .game_flow import _end_hand
            _end_hand(table)
            return "Hand ended - all players disconnected"

        # If it was their turn, advance
        if table.current_turn_pid == pid:
            advance_turn(table)

    # Also check if we have enough eligible players to continue
    from .player_utils import eligible_players
    eligible = eligible_players(table)
    if len(eligible) < 2 and table.hand_in_progress:
        from .game_flow import _end_hand
        _end_hand(table)
        return "Hand ended - not enough players"

    return None
