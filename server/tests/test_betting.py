"""
Tests for betting and pot management logic.
"""
import pytest
from app.core.betting import post_blinds, process_call, process_raise, is_betting_complete
from app.core.models import TableState, Player


class TestPostBlinds:
    """Tests for post_blinds function."""

    def test_heads_up_dealer_is_sb(self, table_with_two_players):
        """In heads-up, dealer posts small blind."""
        table = table_with_two_players
        table.dealer_seat = 1  # p1 is dealer

        post_blinds(table)

        # p1 (dealer) should be SB
        assert table.players["p1"].stack == 995  # 1000 - 5
        assert table.player_bets["p1"] == 5

        # p2 should be BB
        assert table.players["p2"].stack == 990  # 1000 - 10
        assert table.player_bets["p2"] == 10

    def test_heads_up_pot_correct(self, table_with_two_players):
        """Pot should equal SB + BB."""
        table = table_with_two_players
        post_blinds(table)

        assert table.pot == 15  # 5 + 10
        assert table.current_bet == 10  # BB amount

    def test_three_players_dealer_plus_one_is_sb(self, table_with_three_players):
        """With 3+ players, SB is dealer+1, BB is dealer+2."""
        table = table_with_three_players
        table.dealer_seat = 1  # p1 is dealer

        post_blinds(table)

        # p1 (dealer) unchanged
        assert table.players["p1"].stack == 1000

        # p2 (dealer+1) is SB
        assert table.players["p2"].stack == 995
        assert table.player_bets["p2"] == 5

        # p3 (dealer+2) is BB
        assert table.players["p3"].stack == 990
        assert table.player_bets["p3"] == 10

    def test_three_players_wrap_around(self, table_with_three_players):
        """Blinds wrap around the table correctly."""
        table = table_with_three_players
        table.dealer_seat = 3  # p3 is dealer

        post_blinds(table)

        # p1 should be SB (wraps around)
        assert table.players["p1"].stack == 995

        # p2 should be BB
        assert table.players["p2"].stack == 990

    def test_all_in_small_blind(self, table_with_two_players):
        """Player with less than SB goes all-in."""
        table = table_with_two_players
        table.players["p1"].stack = 3  # Less than SB of 5

        post_blinds(table)

        assert table.players["p1"].stack == 0
        assert table.player_bets["p1"] == 3
        assert table.pot == 13  # 3 + 10

    def test_all_in_big_blind(self, table_with_two_players):
        """Player with less than BB goes all-in."""
        table = table_with_two_players
        table.players["p2"].stack = 7  # Less than BB of 10

        post_blinds(table)

        assert table.players["p2"].stack == 0
        assert table.player_bets["p2"] == 7
        assert table.current_bet == 7

    def test_not_enough_players(self, empty_table):
        """No blinds posted with less than 2 players."""
        table = empty_table
        table.players["p1"] = Player(pid="p1", name="Alice", stack=1000, seat=1)

        post_blinds(table)

        assert table.pot == 0
        assert table.player_bets == {}


class TestProcessCall:
    """Tests for process_call function."""

    def test_basic_call(self, table_with_blinds_posted):
        """Player calls the current bet."""
        table = table_with_blinds_posted
        # p1 (SB) has bet 5, needs to call 5 more to match BB of 10

        process_call(table, "p1")

        assert table.players["p1"].stack == 990  # 995 - 5
        assert table.player_bets["p1"] == 10
        assert table.pot == 20  # 15 + 5

    def test_call_when_already_matched(self, table_mid_hand):
        """Call when bet is 0 does nothing."""
        table = table_mid_hand
        table.current_bet = 0
        initial_stack = table.players["p1"].stack

        process_call(table, "p1")

        assert table.players["p1"].stack == initial_stack
        assert table.pot == 200

    def test_all_in_call(self, table_with_blinds_posted):
        """Player goes all-in when can't afford full call."""
        table = table_with_blinds_posted
        table.players["p1"].stack = 3  # Can't afford full 5 to call
        table.current_bet = 100  # Raise happened

        process_call(table, "p1")

        assert table.players["p1"].stack == 0
        assert table.player_bets["p1"] == 8  # 5 original + 3 more
        assert table.pot == 18  # 15 + 3


class TestProcessRaise:
    """Tests for process_raise function."""

    def test_basic_raise(self, table_with_blinds_posted):
        """Player makes a standard raise."""
        table = table_with_blinds_posted

        process_raise(table, "p1", 30)

        assert table.players["p1"].stack == 970  # 995 - 25 (30 total - 5 already bet)
        assert table.player_bets["p1"] == 30
        assert table.current_bet == 30
        assert table.pot == 40  # 15 + 25

    def test_raise_clears_players_acted(self, table_with_blinds_posted):
        """Raise should reset players_acted to only the raiser."""
        table = table_with_blinds_posted
        table.players_acted = {"p1", "p2"}

        process_raise(table, "p1", 30)

        assert table.players_acted == {"p1"}

    def test_minimum_raise(self, table_with_blinds_posted):
        """Raise with 0 amount uses minimum raise."""
        table = table_with_blinds_posted

        process_raise(table, "p1", 0)

        # Min raise calculation: current_bet * 2 - player_current_bet
        # = 10 * 2 - 5 = 15
        # If that's less than big_blind (10), use big_blind
        # So min_raise = 15, current_bet becomes 15
        assert table.current_bet == 15

    def test_all_in_raise(self, table_with_blinds_posted):
        """Player goes all-in on raise."""
        table = table_with_blinds_posted
        table.players["p1"].stack = 15  # Only 15 chips left (plus 5 already bet = 20 total)

        process_raise(table, "p1", 100)  # Wants to raise to 100 but can't

        assert table.players["p1"].stack == 0
        assert table.player_bets["p1"] == 20  # 5 + 15 = 20 (all-in)
        assert table.current_bet == 20


class TestIsBettingComplete:
    """Tests for is_betting_complete function."""

    def test_no_active_players(self, empty_table):
        """Betting complete with no active players."""
        assert is_betting_complete(empty_table, []) is True

    def test_not_all_acted(self, table_with_blinds_posted):
        """Betting not complete when not all players have acted."""
        table = table_with_blinds_posted
        table.players_acted = {"p1"}  # Only p1 has acted

        assert is_betting_complete(table, ["p1", "p2"]) is False

    def test_all_acted_but_not_matched(self, table_with_blinds_posted):
        """Betting not complete when bets don't match."""
        table = table_with_blinds_posted
        table.players_acted = {"p1", "p2"}
        # p1 bet 5, p2 bet 10, bets don't match

        assert is_betting_complete(table, ["p1", "p2"]) is False

    def test_all_acted_and_matched(self, table_with_blinds_posted):
        """Betting complete when all acted and matched."""
        table = table_with_blinds_posted
        table.players_acted = {"p1", "p2"}
        table.player_bets = {"p1": 10, "p2": 10}

        assert is_betting_complete(table, ["p1", "p2"]) is True

    def test_all_in_player_doesnt_need_to_match(self, table_with_blinds_posted):
        """All-in player doesn't need to match current bet."""
        table = table_with_blinds_posted
        table.players["p1"].stack = 0  # p1 is all-in
        table.player_bets = {"p1": 5, "p2": 10}  # p1 bet less but all-in
        table.players_acted = {"p1", "p2"}

        assert is_betting_complete(table, ["p1", "p2"]) is True

    def test_check_round(self, table_mid_hand):
        """Betting complete when everyone checks."""
        table = table_mid_hand
        table.current_bet = 0
        table.player_bets = {}
        table.players_acted = {"p1", "p2"}

        assert is_betting_complete(table, ["p1", "p2"]) is True
