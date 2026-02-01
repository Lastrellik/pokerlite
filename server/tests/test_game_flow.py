"""
Tests for game flow and street progression logic.
"""
import pytest
import time
from app.core.game_flow import (
    start_new_hand,
    advance_turn,
    advance_street,
    run_showdown,
    check_turn_timeout,
    _advance_dealer,
    _get_first_postflop_actor,
    TURN_TIMEOUT_SECONDS
)
from app.core.models import TableState, Player


class TestStartNewHand:
    """Tests for start_new_hand function."""

    def test_starts_hand_with_two_players(self, table_with_two_players):
        table = table_with_two_players

        start_new_hand(table)

        assert table.hand_in_progress is True
        assert table.street == "preflop"
        assert len(table.board) == 0
        assert table.pot == 15  # SB + BB

    def test_deals_hole_cards(self, table_with_two_players):
        table = table_with_two_players

        start_new_hand(table)

        assert len(table.hole_cards) == 2
        assert len(table.hole_cards["p1"]) == 2
        assert len(table.hole_cards["p2"]) == 2

    def test_sets_current_turn(self, table_with_two_players):
        table = table_with_two_players

        start_new_hand(table)

        assert table.current_turn_pid is not None
        assert table.turn_deadline is not None

    def test_clears_previous_showdown(self, table_with_two_players):
        table = table_with_two_players
        table.showdown_data = {"some": "data"}

        start_new_hand(table)

        assert table.showdown_data is None

    def test_not_enough_players(self, empty_table):
        table = empty_table
        table.players["p1"] = Player(pid="p1", name="Alice", stack=1000, seat=1)

        start_new_hand(table)

        assert table.hand_in_progress is False

    def test_resets_folded_and_acted(self, table_with_two_players):
        table = table_with_two_players
        table.folded_pids = {"p1"}
        table.players_acted = {"p1", "p2"}

        start_new_hand(table)

        assert len(table.folded_pids) == 0
        assert len(table.players_acted) == 0


class TestAdvanceDealer:
    """Tests for _advance_dealer function."""

    def test_first_hand_uses_first_seat(self, table_with_two_players):
        table = table_with_two_players
        table.dealer_seat = 0  # No dealer yet
        players = list(table.players.values())

        _advance_dealer(table, players)

        assert table.dealer_seat == 1  # First seat

    def test_advances_to_next_player(self, table_with_two_players):
        table = table_with_two_players
        table.dealer_seat = 1
        players = list(table.players.values())

        _advance_dealer(table, players)

        assert table.dealer_seat == 2

    def test_wraps_around(self, table_with_two_players):
        table = table_with_two_players
        table.dealer_seat = 2
        players = list(table.players.values())

        _advance_dealer(table, players)

        assert table.dealer_seat == 1


class TestAdvanceTurn:
    """Tests for advance_turn function."""

    def test_advances_to_next_player(self, table_with_blinds_posted):
        table = table_with_blinds_posted
        table.current_turn_pid = "p1"

        advance_turn(table)

        assert table.current_turn_pid == "p2"

    def test_wraps_around(self, table_with_blinds_posted):
        table = table_with_blinds_posted
        table.current_turn_pid = "p2"

        advance_turn(table)

        assert table.current_turn_pid == "p1"

    def test_skips_folded_players(self, table_with_three_players):
        table = table_with_three_players
        table.hand_in_progress = True
        table.current_turn_pid = "p1"
        table.folded_pids = {"p2"}

        advance_turn(table)

        assert table.current_turn_pid == "p3"

    def test_sets_deadline(self, table_with_blinds_posted):
        table = table_with_blinds_posted

        advance_turn(table)

        assert table.turn_deadline is not None
        assert table.turn_deadline > time.time()


class TestAdvanceStreet:
    """Tests for advance_street function."""

    def test_preflop_to_flop(self, table_with_blinds_posted):
        table = table_with_blinds_posted
        table.street = "preflop"

        result = advance_street(table)

        assert result is True
        assert table.street == "flop"
        assert len(table.board) == 3

    def test_flop_to_turn(self, table_mid_hand):
        table = table_mid_hand
        table.street = "flop"
        table.board = ["Ah", "Kd", "7c"]

        result = advance_street(table)

        assert result is True
        assert table.street == "turn"
        assert len(table.board) == 4

    def test_turn_to_river(self, table_mid_hand):
        table = table_mid_hand
        table.street = "turn"
        table.board = ["Ah", "Kd", "7c", "2s"]

        result = advance_street(table)

        assert result is True
        assert table.street == "river"
        assert len(table.board) == 5

    def test_river_ends_hand(self, table_mid_hand):
        table = table_mid_hand
        table.street = "river"
        table.board = ["Ah", "Kd", "7c", "2s", "Qh"]

        result = advance_street(table)

        assert result is False

    def test_resets_betting_state(self, table_mid_hand):
        table = table_mid_hand
        table.street = "preflop"
        table.current_bet = 20
        table.player_bets = {"p1": 20, "p2": 20}
        table.players_acted = {"p1", "p2"}

        advance_street(table)

        assert table.current_bet == 0
        assert table.player_bets == {}
        assert len(table.players_acted) == 0


class TestGetFirstPostflopActor:
    """Tests for _get_first_postflop_actor function."""

    def test_returns_first_after_dealer(self, table_mid_hand):
        table = table_mid_hand
        table.dealer_seat = 1  # p1 is dealer

        first = _get_first_postflop_actor(table)

        assert first == "p2"  # p2 is first after dealer

    def test_wraps_around(self, table_mid_hand):
        table = table_mid_hand
        table.dealer_seat = 2  # p2 is dealer

        first = _get_first_postflop_actor(table)

        assert first == "p1"  # Wraps to p1


class TestRunShowdown:
    """Tests for run_showdown function."""

    def test_single_player_wins(self, table_mid_hand):
        table = table_mid_hand
        table.folded_pids = {"p2"}
        table.pot = 100

        result = run_showdown(table)

        assert "Alice" in result
        assert "100" in result
        assert table.players["p1"].stack == 1000  # 900 + 100

    def test_awards_pot_to_winner(self, table_mid_hand):
        table = table_mid_hand
        initial_stack = table.players["p2"].stack
        table.pot = 200
        table.board = ["2h", "3d", "4c", "5s", "9h"]
        table.hole_cards = {
            "p1": ["7h", "Kc"],  # High card
            "p2": ["As", "Ad"],  # Pair of aces - wins
        }

        result = run_showdown(table)

        assert "Bob" in result
        assert table.players["p2"].stack == initial_stack + 200

    def test_split_pot_on_tie(self, table_mid_hand):
        table = table_mid_hand
        table.pot = 200
        table.board = ["2h", "3d", "4c", "5s", "6h"]  # Straight on board
        table.hole_cards = {
            "p1": ["7h", "8h"],  # Doesn't improve
            "p2": ["7s", "8s"],  # Same hand
        }

        result = run_showdown(table)

        assert "Split pot" in result or "tie" in result.lower()

    def test_creates_showdown_data(self, table_mid_hand):
        table = table_mid_hand
        table.pot = 100
        table.board = ["2h", "3d", "4c", "5s", "9h"]
        table.hole_cards = {
            "p1": ["Ah", "Kh"],
            "p2": ["As", "Ad"],
        }

        run_showdown(table)

        assert table.showdown_data is not None
        assert "winner_pids" in table.showdown_data
        assert "players" in table.showdown_data
        assert len(table.showdown_data["players"]) == 2

    def test_ends_hand(self, table_mid_hand):
        table = table_mid_hand
        table.pot = 100
        table.board = ["2h", "3d", "4c", "5s", "9h"]
        table.hole_cards = {
            "p1": ["Ah", "Kh"],
            "p2": ["As", "Ad"],
        }

        run_showdown(table)

        assert table.hand_in_progress is False
        assert table.pot == 0


class TestCheckTurnTimeout:
    """Tests for check_turn_timeout function."""

    def test_no_timeout_when_not_expired(self, table_with_blinds_posted):
        table = table_with_blinds_posted
        table.turn_deadline = time.time() + 100  # Far in future

        timed_out, action = check_turn_timeout(table)

        assert timed_out is False
        assert action == ""

    def test_timeout_folds_when_facing_bet(self, table_with_blinds_posted):
        table = table_with_blinds_posted
        table.turn_deadline = time.time() - 1  # Expired
        table.current_turn_pid = "p1"
        table.current_bet = 10
        table.player_bets = {"p1": 5}

        timed_out, action = check_turn_timeout(table)

        assert timed_out is True
        assert action == "fold"
        assert "p1" in table.folded_pids

    def test_timeout_checks_when_no_bet(self, table_with_blinds_posted):
        table = table_with_blinds_posted
        table.turn_deadline = time.time() - 1
        table.current_turn_pid = "p1"
        table.current_bet = 5
        table.player_bets = {"p1": 5}  # Already matched

        timed_out, action = check_turn_timeout(table)

        assert timed_out is True
        assert action == "check"

    def test_no_timeout_when_no_hand(self, empty_table):
        table = empty_table
        table.hand_in_progress = False

        timed_out, action = check_turn_timeout(table)

        assert timed_out is False
