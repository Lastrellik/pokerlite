"""
Betting and pot management logic.
"""
from .models import TableState
from .player_utils import eligible_players, find_next_seat


def post_blinds(table: TableState) -> None:
    """Posts small blind and big blind at start of hand."""
    players = eligible_players(table)
    if len(players) < 2:
        return

    seats = sorted([p.seat for p in players])

    try:
        dealer_idx = seats.index(table.dealer_seat)
    except ValueError:
        dealer_idx = 0

    # Small blind = dealer + 1
    sb_idx = (dealer_idx + 1) % len(seats)
    sb_seat = seats[sb_idx]
    sb_player = [p for p in players if p.seat == sb_seat][0]

    # Big blind = dealer + 2
    bb_idx = (dealer_idx + 2) % len(seats)
    bb_seat = seats[bb_idx]
    bb_player = [p for p in players if p.seat == bb_seat][0]

    # Post small blind
    sb_amount = min(table.small_blind, sb_player.stack)
    sb_player.stack -= sb_amount
    table.pot += sb_amount
    table.player_bets[sb_player.pid] = sb_amount

    # Post big blind
    bb_amount = min(table.big_blind, bb_player.stack)
    bb_player.stack -= bb_amount
    table.pot += bb_amount
    table.player_bets[bb_player.pid] = bb_amount

    # Set current bet to big blind
    table.current_bet = bb_amount


def process_call(table: TableState, pid: str) -> None:
    """Process a call action."""
    player = table.players[pid]
    player_current_bet = table.player_bets.get(pid, 0)

    call_amount = table.current_bet - player_current_bet
    # All-in if not enough chips
    call_amount = min(call_amount, player.stack)

    player.stack -= call_amount
    table.pot += call_amount
    table.player_bets[pid] = player_current_bet + call_amount


def process_raise(table: TableState, pid: str, amount: int) -> None:
    """Process a raise action."""
    player = table.players[pid]
    player_current_bet = table.player_bets.get(pid, 0)

    # Determine minimum raise
    min_raise = table.current_bet * 2 - player_current_bet
    if min_raise < table.big_blind:
        min_raise = table.big_blind

    # Use provided amount or minimum
    raise_amount = max(amount, min_raise) if amount > 0 else min_raise

    # All-in if not enough chips
    raise_amount = min(raise_amount, player.stack + player_current_bet)

    # Deduct from stack
    to_pay = raise_amount - player_current_bet
    player.stack -= to_pay
    table.pot += to_pay
    table.player_bets[pid] = raise_amount

    # Update current bet
    table.current_bet = raise_amount

    # Everyone needs to act again (except this player)
    table.players_acted = {pid}


def is_betting_complete(table: TableState, active_pids: list[str]) -> bool:
    """Check if betting round is complete."""
    if not active_pids:
        return True

    # All players have acted
    if not all(pid in table.players_acted for pid in active_pids):
        return False

    # All players have matched current bet (or are all-in)
    for apid in active_pids:
        player_bet = table.player_bets.get(apid, 0)
        player = table.players[apid]
        if player_bet < table.current_bet and player.stack > 0:
            return False

    return True
