"""
Player action handlers.
"""
from typing import Dict, Any, Optional
from .models import TableState, PlayerRole
from .player_utils import active_pids
from .betting import process_call, process_raise, is_betting_complete
from .game_flow import advance_turn, advance_street, run_showdown, start_new_hand, check_turn_timeout
from poker.constants import VALID_ACTIONS
from .waitlist import join_waitlist, leave_waitlist


async def handle_message(table: TableState, pid: str, msg: Dict[str, Any]) -> Optional[str]:
    """
    Handle incoming player messages.
    Returns optional info message to broadcast.
    """
    mtype = msg.get("type")
    player = table.players.get(pid)

    if mtype == "join_waitlist":
        if join_waitlist(table, pid):
            return f"{player.name} joined the waitlist"
        return None

    if mtype == "leave_waitlist":
        if leave_waitlist(table, pid):
            return f"{player.name} left the waitlist"
        return None

    # Only seated players can start hands or take actions
    if player and player.role != PlayerRole.SEATED:
        return None

    if mtype == "start":
        start_new_hand(table)
        return "New hand started"

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

    # Build action message for logging
    action_msg = None

    # Handle fold
    if action == "fold":
        table.folded_pids.add(pid)
        action_msg = f"{player.name} folds"

        # Check if only one player remains
        active = active_pids(table)
        if len(active) == 1:
            return run_showdown(table)

    # Handle check
    elif action == "check":
        # Can only check if no bet to call
        if table.current_bet > player_current_bet:
            return None  # Invalid action
        action_msg = f"{player.name} checks"

    # Handle call
    elif action == "call":
        call_amount = min(table.current_bet - player_current_bet, player.stack)
        is_all_in = call_amount >= player.stack
        process_call(table, pid)
        if is_all_in:
            total_bet = player_current_bet + call_amount
            action_msg = f"{player.name} goes all-in for ${total_bet}"
        else:
            action_msg = f"{player.name} calls ${call_amount}"

    # Handle raise
    elif action == "raise":
        # Validate amount is positive
        if amount is None or amount <= 0:
            return None  # Invalid raise amount
        process_raise(table, pid, amount)
        action_msg = f"{player.name} raises to ${amount}"

    # Handle all-in
    elif action == "all_in":
        # All-in is a raise with the player's entire stack
        all_in_amount = player.stack + player_current_bet

        # If all-in amount doesn't meet current bet, it's a call, not a raise
        if all_in_amount < table.current_bet:
            process_call(table, pid)
            action_msg = f"{player.name} goes all-in for ${all_in_amount}"
        else:
            process_raise(table, pid, all_in_amount)
            action_msg = f"{player.name} goes all-in for ${all_in_amount}"

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

            # Log for debugging
            print(f"[RUNOUT] Starting runout with {len(active)} players, {len(players_with_chips)} with chips")

            return action_msg  # Return the action message
        # Try to advance to next street
        can_continue = advance_street(table)
        if not can_continue:
            # After river, go to showdown
            return run_showdown(table)

        # Return street change message
        street_names = {"flop": "Flop", "turn": "Turn", "river": "River"}
        street_name = street_names.get(table.street, table.street)
        return f"📋 Dealing {street_name}: {' '.join(table.board)}"

    advance_turn(table)
    return action_msg


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
