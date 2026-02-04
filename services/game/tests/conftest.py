"""
Shared test fixtures for pokerlite tests.
"""
import pytest
from app.core.models import TableState, Player


@pytest.fixture
def empty_table():
    """Create an empty table state."""
    return TableState(table_id="test-table")


@pytest.fixture
def table_with_two_players():
    """Create a table with two connected players (heads-up)."""
    table = TableState(table_id="test-table")
    table.players = {
        "p1": Player(pid="p1", name="Alice", stack=1000, seat=1, connected=True),
        "p2": Player(pid="p2", name="Bob", stack=1000, seat=2, connected=True),
    }
    table.dealer_seat = 1
    return table


@pytest.fixture
def table_with_three_players():
    """Create a table with three connected players."""
    table = TableState(table_id="test-table")
    table.players = {
        "p1": Player(pid="p1", name="Alice", stack=1000, seat=1, connected=True),
        "p2": Player(pid="p2", name="Bob", stack=1000, seat=2, connected=True),
        "p3": Player(pid="p3", name="Charlie", stack=1000, seat=3, connected=True),
    }
    table.dealer_seat = 1
    return table


@pytest.fixture
def table_with_blinds_posted(table_with_two_players):
    """Create a table with blinds already posted (heads-up)."""
    from poker.card_utils import shuffle_deck

    table = table_with_two_players
    table.hand_in_progress = True
    table.street = "preflop"

    # In heads-up, dealer is SB
    # p1 (dealer, seat 1) is SB, p2 (seat 2) is BB
    table.players["p1"].stack = 995  # Posted SB of 5
    table.players["p2"].stack = 990  # Posted BB of 10
    table.pot = 15
    table.player_bets = {"p1": 5, "p2": 10}
    table.total_contributions = {"p1": 5, "p2": 10}
    table.current_bet = 10
    table.current_turn_pid = "p1"  # SB acts first preflop in heads-up
    table.deck = shuffle_deck()[:40]  # Partial deck for testing
    table.hole_cards = {"p1": ["Ah", "Kh"], "p2": ["Qs", "Qd"]}

    return table


@pytest.fixture
def table_mid_hand():
    """Create a table mid-hand with some action already taken."""
    from poker.card_utils import shuffle_deck

    table = TableState(table_id="test-table")
    table.players = {
        "p1": Player(pid="p1", name="Alice", stack=900, seat=1, connected=True),
        "p2": Player(pid="p2", name="Bob", stack=900, seat=2, connected=True),
    }
    table.hand_in_progress = True
    table.street = "flop"
    table.pot = 200
    table.board = ["Ah", "Kd", "7c"]
    table.current_bet = 0
    table.player_bets = {}
    table.folded_pids = set()
    table.players_acted = set()
    table.current_turn_pid = "p2"  # BB acts first post-flop
    table.dealer_seat = 1
    table.deck = shuffle_deck()[:40]  # Partial deck for testing
    table.hole_cards = {"p1": ["Th", "Ts"], "p2": ["Jh", "Js"]}

    return table
