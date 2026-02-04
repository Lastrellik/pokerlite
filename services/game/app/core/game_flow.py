"""
Game flow and street progression logic.
"""
import time
from .models import TableState
from .player_utils import connected_players, active_pids, eligible_players
from poker.card_utils import shuffle_deck
from .betting import post_blinds
from poker.poker_logic import evaluate_hand, evaluate_hand_with_cards, compare_hands, hand_name, get_key_cards

# Turn timer constant (30 seconds)
TURN_TIMEOUT_SECONDS = 30


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
    from .models import PlayerRole
    from .waitlist import promote_from_waitlist

    # Convert busted players (stack=0) to spectators BEFORE starting new hand
    # This way they remain visible during showdown of previous hand
    for player in list(table.players.values()):
        if player.role == PlayerRole.SEATED and player.stack == 0:
            player.role = PlayerRole.SPECTATOR
            player.seat = 0
            table.spectator_pids.add(player.pid)

    # Promote from waitlist if seats available
    promoted_pid = promote_from_waitlist(table)
    while promoted_pid:
        promoted_pid = promote_from_waitlist(table)

    players = eligible_players(table)

    if len(players) < 2:
        return

    # Clear previous showdown data and last action
    table.showdown_data = None
    table.last_action = None
    table.runout_in_progress = False

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
    table.total_contributions = {}

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
        # In heads up, dealer/SB acts first preflop; otherwise UTG (dealer+3) acts first
        if len(players) == 2:
            # Dealer is SB in heads-up, SB acts first preflop
            first_idx = dealer_idx
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
    table.last_action = None  # Clear last action when advancing streets

    # Reset betting for new street
    table.current_bet = 0
    table.player_bets = {}

    # Deal community cards
    _deal_community_cards(table, next_street)

    # Reset turn to first active player after dealer (post-flop order)
    table.current_turn_pid = _get_first_postflop_actor(table)
    _set_turn_deadline(table)

    return True


def _get_first_postflop_actor(table: TableState) -> str | None:
    """Get the first player to act post-flop (first active player after dealer)."""
    from .player_utils import active_players

    active = active_players(table)
    if not active:
        return None

    if len(active) == 1:
        return active[0].pid

    # Sort by seat
    seats = sorted([p.seat for p in active])

    # Find first seat after dealer
    dealer_seat = table.dealer_seat

    # Find the first seat that comes after the dealer in clockwise order
    for seat in seats:
        if seat > dealer_seat:
            player = next(p for p in active if p.seat == seat)
            return player.pid

    # Wrap around - dealer is at or after all active seats
    player = next(p for p in active if p.seat == seats[0])
    return player.pid


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
    from .player_utils import active_players

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
        # Find the next active player after the current player's seat
        current_seat = table.players[table.current_turn_pid].seat
        active = active_players(table)
        active_seats = sorted([p.seat for p in active])

        # Find first seat after current_seat in circular order
        next_seat = None
        for seat in active_seats:
            if seat > current_seat:
                next_seat = seat
                break

        # Wrap around if needed
        if next_seat is None and active_seats:
            next_seat = active_seats[0]

        # Find player with that seat
        if next_seat is not None:
            next_player = next(p for p in active if p.seat == next_seat)
            table.current_turn_pid = next_player.pid
        else:
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

        # Set showdown data for fold win (so frontend can show winner highlight)
        table.showdown_data = {
            "winner_pids": [winner.pid],
            "pot_won": pot_won,
            "fold_win": True,
            "players": {},  # No cards shown for fold win
        }

        _end_hand(table)
        return f"{winner.name} wins {pot_won} chips (others folded)"

    # Evaluate all hands with best 5 cards
    hand_evals = {}
    for pid in active:
        cards = table.hole_cards.get(pid, []) + table.board
        hand_evals[pid] = evaluate_hand_with_cards(cards)

    # Create side pots based on total contributions throughout the hand
    # Sort players by their total bet amounts
    player_bets_list = [(pid, table.total_contributions.get(pid, 0)) for pid in active]

    # Check if all bets are equal or zero (no side pots needed)
    bet_amounts = [bet for _, bet in player_bets_list]
    all_equal_bets = len(set(bet_amounts)) <= 1

    if all_equal_bets:
        # Simple case: everyone contributed equally, single pot for all
        side_pots = [{
            'amount': table.pot,
            'eligible_players': set(active)
        }]
    else:
        # Complex case: different bet amounts, need side pots
        player_bets_list.sort(key=lambda x: x[1])

        # Build side pots
        side_pots = []
        remaining_players = set(active)
        prev_bet_level = 0

        for i, (pid, bet_amount) in enumerate(player_bets_list):
            if bet_amount > prev_bet_level and remaining_players:
                # Create a pot for this bet level
                pot_amount = (bet_amount - prev_bet_level) * len(remaining_players)
                side_pots.append({
                    'amount': pot_amount,
                    'eligible_players': remaining_players.copy()
                })
                prev_bet_level = bet_amount

            # Remove this player from remaining (they're all-in at this level)
            remaining_players.discard(pid)

    # Award each side pot to the best hand among eligible players
    total_pot = table.pot
    total_awarded = 0
    pot_winners = {}  # Track total won per player
    pot_winner_details = []  # Track which players won which pots

    for pot_idx, pot in enumerate(side_pots):
        eligible = list(pot['eligible_players'])

        # Find best hand among eligible players
        best_hand = None
        pot_winners_list = []

        for pid in eligible:
            hand = hand_evals[pid][:2]
            if best_hand is None:
                best_hand = hand
                pot_winners_list = [pid]
            else:
                result = compare_hands(hand, best_hand)
                if result == -1:
                    best_hand = hand
                    pot_winners_list = [pid]
                elif result == 0:
                    pot_winners_list.append(pid)

        # Split pot among winners
        pot_share = pot['amount'] // len(pot_winners_list)
        remainder = pot['amount'] % len(pot_winners_list)

        for i, pid in enumerate(pot_winners_list):
            award = pot_share
            if i == 0:
                award += remainder
            table.players[pid].stack += award
            total_awarded += award
            pot_winners[pid] = pot_winners.get(pid, 0) + award

        # Record pot details for display
        pot_winner_details.append({
            'pot_idx': pot_idx,
            'amount': pot['amount'],
            'winners': pot_winners_list
        })

    # Determine overall winners (for display) and find the winning hand
    winners = list(pot_winners.keys())

    # Find the best hand among all winners for display
    winning_hand = None
    winning_hand_name = ""
    for pid in winners:
        hand = hand_evals[pid][:2]
        if winning_hand is None or compare_hands(hand, winning_hand) <= 0:
            winning_hand = hand
            winning_hand_name = hand_name(hand)

    # Build showdown data before ending hand
    showdown_players = {}
    for pid in active:
        rank, tiebreakers, best_5 = hand_evals[pid]
        key_cards = get_key_cards(best_5, rank)
        showdown_players[pid] = {
            "hole_cards": table.hole_cards.get(pid, []),
            "best_5_cards": best_5,
            "highlight_cards": key_cards,
            "hand_name": hand_name((rank, tiebreakers)),
        }

    # Build side pot breakdown for display
    side_pot_breakdown = []
    if len(side_pots) > 1:
        # Multiple pots - show breakdown
        for pot_detail in pot_winner_details:
            idx = pot_detail['pot_idx']
            pot_type = "Main Pot" if idx == 0 else f"Side Pot {idx}"
            pot_winner_names = [table.players[pid].name for pid in pot_detail['winners']]
            side_pot_breakdown.append({
                "type": pot_type,
                "amount": pot_detail['amount'],
                "winners": pot_winner_names
            })

    table.showdown_data = {
        "players": showdown_players,
        "winner_pids": winners,
        "winning_hand_name": winning_hand_name,
        "pot_won": total_pot,
        "board": table.board.copy(),
        "side_pots": side_pot_breakdown if side_pot_breakdown else None,
    }

    _end_hand(table)

    # Generate result message
    if len(winners) == 1:
        winner = table.players[winners[0]]
        won_amount = pot_winners[winners[0]]
        # Calculate net gain (subtract their total contribution to the pot)
        original_bet = table.total_contributions.get(winners[0], 0)
        net_gain = won_amount - original_bet

        if len(side_pots) > 1:
            # Multiple side pots - explain the breakdown
            result_msg = f"{winner.name} wins ${won_amount} (${net_gain} profit) with {winning_hand_name}"
            # Add side pot details
            for idx, pot_info in enumerate(side_pot_breakdown):
                pot_type = pot_info['type']
                pot_amt = pot_info['amount']
                pot_winner_names = ', '.join(pot_info['winners'])
                result_msg += f"\n  • {pot_type}: ${pot_amt} → {pot_winner_names}"
            return result_msg
        else:
            # Single pot
            return f"{winner.name} wins ${total_pot} (${net_gain} profit) with {winning_hand_name}"
    else:
        # Multiple winners (split pot scenario)
        winner_details = []
        for pid in winners:
            won_amt = pot_winners[pid]
            original_bet = table.total_contributions.get(pid, 0)
            profit = won_amt - original_bet
            winner_details.append(f"{table.players[pid].name} (${won_amt}, +${profit})")

        result = f"Split pot: {', '.join(winner_details)} with {winning_hand_name}"
        # Add side pot breakdown if applicable
        if len(side_pots) > 1 and side_pot_breakdown:
            for pot_info in side_pot_breakdown:
                pot_type = pot_info['type']
                pot_amt = pot_info['amount']
                pot_winner_names = ', '.join(pot_info['winners'])
                result += f"\n  • {pot_type}: ${pot_amt} → {pot_winner_names}"
        return result


def _end_hand(table: TableState) -> None:
    """Clean up hand state and handle player transitions."""
    table.hand_in_progress = False
    table.current_turn_pid = None
    table.pot = 0
    table.board = []

    # Note: Busted players (stack=0) are NOT converted to spectators here
    # They remain visible until the next hand starts (see start_new_hand)
    # This allows players to see the showdown results before busted players disappear
