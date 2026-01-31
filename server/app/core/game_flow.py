"""
Game flow and street progression logic.
"""
import time
from .models import TableState
from .player_utils import connected_players, active_pids, eligible_players
from .card_utils import shuffle_deck
from .betting import post_blinds
from .poker_logic import evaluate_hand, compare_hands, hand_name

# Turn timer constant (20 seconds)
TURN_TIMEOUT_SECONDS = 20


def _set_turn_deadline(table: TableState) -> None:
    """Set turn deadline to current time + timeout."""
    if table.current_turn_pid:
        table.turn_deadline = time.time() + TURN_TIMEOUT_SECONDS
    else:
        table.turn_deadline = None


def check_turn_timeout(table: TableState) -> tuple[bool, str]:
    """
    Check if current turn has timed out.
    Returns (timed_out, action_taken) where action_taken is 'fold' or 'check'.
    """
    if not table.hand_in_progress or not table.current_turn_pid or not table.turn_deadline:
        return False, ""

    if time.time() < table.turn_deadline:
        return False, ""

    # Timeout occurred - auto fold or check
    pid = table.current_turn_pid
    player = table.players.get(pid)
    if not player:
        return False, ""

    player_current_bet = table.player_bets.get(pid, 0)

    # If there's a bet to call, fold. Otherwise check.
    if table.current_bet > player_current_bet:
        table.folded_pids.add(pid)
        action_taken = "fold"
    else:
        action_taken = "check"

    # Mark as acted
    table.players_acted.add(pid)

    return True, action_taken


def start_new_hand(table: TableState) -> None:
    """Initialize a new hand."""
    players = eligible_players(table)

    if len(players) < 2:
        return

    # Move dealer button
    _advance_dealer(table, players)

    # Reset hand state
    table.hand_in_progress = True
    table.pot = 0
    table.board = []
    table.folded_pids = set()
    table.players_acted = set()
    table.street = "preflop"
    table.current_bet = 0
    table.player_bets = {}

    # Create and shuffle deck
    table.deck = shuffle_deck()

    # Deal hole cards
    _deal_hole_cards(table, players)

    # Post blinds
    post_blinds(table)

    # Set first to act (after big blind)
    _set_first_to_act(table, players)


def _advance_dealer(table: TableState, players: list) -> None:
    """Move dealer button to next player."""
    if table.dealer_seat == 0:
        # First hand, dealer is first seat
        table.dealer_seat = players[0].seat
    else:
        # Find next seat after current dealer
        seats = sorted([p.seat for p in players])
        try:
            dealer_idx = seats.index(table.dealer_seat)
            next_idx = (dealer_idx + 1) % len(seats)
            table.dealer_seat = seats[next_idx]
        except ValueError:
            # Current dealer not found, use first seat
            table.dealer_seat = seats[0]


def _deal_hole_cards(table: TableState, players: list) -> None:
    """Deal 2 cards to each player."""
    table.hole_cards = {}
    for p in players:
        table.hole_cards[p.pid] = [table.deck.pop(), table.deck.pop()]


def _set_first_to_act(table: TableState, players: list) -> None:
    """Set first player to act preflop (after big blind)."""
    seats = sorted([p.seat for p in players])
    try:
        dealer_idx = seats.index(table.dealer_seat)
        # In heads up, SB acts first preflop; otherwise UTG (dealer+3) acts first
        if len(players) == 2:
            first_idx = (dealer_idx + 1) % len(seats)
        else:
            first_idx = (dealer_idx + 3) % len(seats)
        first_seat = seats[first_idx]
        first_player = [p for p in players if p.seat == first_seat][0]
        table.current_turn_pid = first_player.pid
    except (ValueError, IndexError):
        # Fallback to first active player
        pids = active_pids(table)
        table.current_turn_pid = pids[0] if pids else None

    _set_turn_deadline(table)


def advance_street(table: TableState) -> bool:
    """
    Advances to the next betting street and deals community cards.
    Returns True if advanced, False if hand should end (after river).
    """
    street_order = {
        "preflop": "flop",
        "flop": "turn",
        "turn": "river",
        "river": None
    }

    next_street = street_order.get(table.street)

    if next_street is None:
        # After river, hand is over
        return False

    # Advance to next street
    table.street = next_street
    table.players_acted = set()

    # Reset betting for new street
    table.current_bet = 0
    table.player_bets = {}

    # Deal community cards
    _deal_community_cards(table, next_street)

    # Reset turn to first active player
    pids = active_pids(table)
    table.current_turn_pid = pids[0] if pids else None
    _set_turn_deadline(table)

    return True


def _deal_community_cards(table: TableState, street: str) -> None:
    """Deal community cards for the given street."""
    if street == "flop":
        # Burn one, deal 3
        table.deck.pop()
        table.board = [table.deck.pop(), table.deck.pop(), table.deck.pop()]
    elif street == "turn":
        # Burn one, deal 1
        table.deck.pop()
        table.board.append(table.deck.pop())
    elif street == "river":
        # Burn one, deal 1
        table.deck.pop()
        table.board.append(table.deck.pop())


def advance_turn(table: TableState) -> None:
    """Advances turn to next active (not folded, connected) player."""
    pids = active_pids(table)

    if not pids:
        table.current_turn_pid = None
        _set_turn_deadline(table)
        return

    if table.current_turn_pid is None:
        table.current_turn_pid = pids[0]
        _set_turn_deadline(table)
        return

    try:
        i = pids.index(table.current_turn_pid)
        table.current_turn_pid = pids[(i + 1) % len(pids)]
    except ValueError:
        # Current player not in active list (disconnected or folded)
        table.current_turn_pid = pids[0] if pids else None

    _set_turn_deadline(table)


def run_showdown(table: TableState) -> str:
    """
    Evaluates all active players' hands, determines winner(s), and awards pot.
    Returns a message describing the result.
    """
    active = active_pids(table)

    if not active:
        _end_hand(table)
        return "Hand ended with no active players"

    if len(active) == 1:
        winner = table.players[active[0]]
        pot_won = table.pot
        winner.stack += table.pot
        _end_hand(table)
        return f"{winner.name} wins {pot_won} chips (others folded)"

    # Evaluate all hands
    hand_evals = {}
    for pid in active:
        cards = table.hole_cards.get(pid, []) + table.board
        hand_evals[pid] = evaluate_hand(cards)

    # Find winner(s)
    best_hand = None
    winners = []

    for pid in active:
        hand = hand_evals[pid]
        if best_hand is None:
            best_hand = hand
            winners = [pid]
        else:
            result = compare_hands(hand, best_hand)
            if result == -1:
                best_hand = hand
                winners = [pid]
            elif result == 0:
                winners.append(pid)

    # Award pot
    total_pot = table.pot
    pot_share = total_pot // len(winners)
    remainder = total_pot % len(winners)

    for i, pid in enumerate(winners):
        award = pot_share
        if i == 0:
            award += remainder
        table.players[pid].stack += award

    _end_hand(table)

    # Generate result message
    hand_description = hand_name(best_hand)
    if len(winners) == 1:
        winner = table.players[winners[0]]
        return f"{winner.name} wins {total_pot} chips with {hand_description}"
    else:
        winner_names = [table.players[pid].name for pid in winners]
        return f"Split pot: {', '.join(winner_names)} tie with {hand_description} ({pot_share} chips each)"


def _end_hand(table: TableState) -> None:
    """Clean up hand state."""
    table.hand_in_progress = False
    table.current_turn_pid = None
    table.pot = 0
    table.board = []
