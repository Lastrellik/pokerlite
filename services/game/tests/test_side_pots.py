"""
Tests for side pot handling and total contributions tracking.
"""
import pytest
from app.core.betting import post_blinds, process_call, process_raise
from app.core.game_flow import run_showdown, start_new_hand
from app.core.models import TableState, Player, PlayerRole


@pytest.fixture
def table_four_players():
    """Table with four players for side pot testing."""
    table = TableState(table_id="test")
    table.players = {
        "p1": Player(pid="p1", name="Alice", stack=1590, seat=1, role=PlayerRole.SEATED, connected=True),
        "p2": Player(pid="p2", name="Bob", stack=830, seat=2, role=PlayerRole.SEATED, connected=True),
        "p3": Player(pid="p3", name="Charlie", stack=830, seat=3, role=PlayerRole.SEATED, connected=True),
        "p4": Player(pid="p4", name="Dave", stack=790, seat=4, role=PlayerRole.SEATED, connected=True),
    }
    table.dealer_seat = 1
    table.hand_in_progress = True
    return table


class TestTotalContributions:
    """Tests for total_contributions tracking."""

    def test_blinds_update_total_contributions(self, table_four_players):
        """Posting blinds should update total_contributions."""
        table = table_four_players
        start_new_hand(table)

        # Check that total_contributions matches player_bets after blinds
        assert table.total_contributions.get("p2", 0) == table.player_bets.get("p2", 0)
        assert table.total_contributions.get("p3", 0) == table.player_bets.get("p3", 0)

    def test_call_accumulates_total_contributions(self, table_four_players):
        """Calling should accumulate total_contributions."""
        table = table_four_players
        table.current_bet = 100
        table.player_bets = {"p1": 10}
        table.total_contributions = {"p1": 10}

        process_call(table, "p1")

        # Should add 90 to existing 10
        assert table.total_contributions["p1"] == 100
        assert table.player_bets["p1"] == 100

    def test_raise_accumulates_total_contributions(self, table_four_players):
        """Raising should accumulate total_contributions."""
        table = table_four_players
        table.current_bet = 50
        table.player_bets = {"p1": 10}
        table.total_contributions = {"p1": 10}

        process_raise(table, "p1", 200)

        # Added 190 to existing 10
        assert table.total_contributions["p1"] == 200
        assert table.player_bets["p1"] == 200

    def test_total_contributions_persists_across_streets(self, table_four_players):
        """total_contributions should persist when player_bets is reset."""
        table = table_four_players
        table.player_bets = {"p1": 100, "p2": 100}
        table.total_contributions = {"p1": 100, "p2": 100}

        # Simulate street change (player_bets gets reset in advance_street)
        table.player_bets = {}
        table.current_bet = 0

        # New betting round
        table.current_bet = 50
        process_call(table, "p1")

        # total_contributions should accumulate, not replace
        assert table.total_contributions["p1"] == 150  # 100 + 50
        assert table.player_bets["p1"] == 50  # Only current street


class TestSidePotCalculation:
    """Tests for side pot calculation using total_contributions."""

    def test_unequal_all_ins_create_side_pots(self, table_four_players):
        """Different all-in amounts should create proper side pots."""
        table = table_four_players
        table.board = ["Ah", "Kh", "Qh", "Jh", "2d"]  # Not a royal flush board

        # Simulate everyone all-in with different amounts, set stacks to 0
        table.players["p1"].stack = 0
        table.players["p2"].stack = 0
        table.players["p3"].stack = 0
        table.players["p4"].stack = 0

        table.total_contributions = {
            "p1": 1590,  # Biggest stack
            "p2": 830,   # Medium
            "p3": 830,   # Medium (same as p2)
            "p4": 790,   # Smallest
        }
        table.pot = 4040  # 1590 + 830 + 830 + 790

        # Give p1 the best hand (Ace-high flush)
        table.hole_cards = {
            "p1": ["Ad", "Kd"],  # Flush with A-K
            "p2": ["2c", "3c"],  # Nothing
            "p3": ["4d", "5d"],  # Nothing
            "p4": ["6s", "7s"],  # Nothing
        }

        result = run_showdown(table)

        # p1 should win everything: 4040 total, minus their 1590 contribution = 2450 profit
        assert table.players["p1"].stack == 4040
        assert "2450 profit" in result or "2,450 profit" in result

    def test_short_all_in_creates_correct_side_pot(self, table_four_players):
        """Player all-in for less should only be eligible for their portion."""
        table = table_four_players
        table.board = ["2c", "3c", "4c", "5c", "6c"]

        # Set all stacks to 0 (after all-in)
        table.players["p1"].stack = 0
        table.players["p2"].stack = 0
        table.players["p3"].stack = 0
        table.players["p4"].stack = 0

        # p1 all-in 790, p2 all-in 830, p3 calls 830, p4 all-in 790
        table.total_contributions = {
            "p1": 790,
            "p2": 830,
            "p3": 830,
            "p4": 790,
        }
        table.pot = 3240

        # p1 wins with straight flush
        table.hole_cards = {
            "p1": ["7c", "8c"],  # Straight flush 2-3-4-5-6-7-8
            "p2": ["9h", "Th"],  # Just the board flush
            "p3": ["Jh", "Qh"],  # Just the board flush
            "p4": ["Kh", "Ah"],  # Just the board flush
        }

        result = run_showdown(table)

        # p1 should only win the main pot (790 * 4 = 3160)
        # The side pot of $80 (40 from p2, 40 from p3) goes to best of {p2, p3, p4}
        assert table.players["p1"].stack == 3160
        # Check profit is correct: 3160 - 790 = 2370 (or +$2370 format)
        assert "+$2370" in result or "2370 profit" in result or "2,370 profit" in result

        # One of p2/p3/p4 should have won the side pot of $80
        side_pot_winner_stack = max(
            table.players["p2"].stack,
            table.players["p3"].stack,
            table.players["p4"].stack
        )
        assert side_pot_winner_stack == 40  # Split between 2 players


class TestAllInBehavior:
    """Tests for all-in action handling."""

    def test_all_in_below_current_bet_is_call(self, table_four_players):
        """All-in for less than current bet should be treated as call, not raise."""
        table = table_four_players
        table.current_bet = 1590
        table.player_bets = {"p1": 1590}
        table.total_contributions = {"p1": 1590}
        table.players_acted = {"p1"}

        # p4 has only 790, tries to go all-in (which is less than 1590)
        from app.core.actions import _handle_action

        msg = {"type": "action", "action": "all_in"}
        table.current_turn_pid = "p4"

        # Before fix: would call process_raise and reset players_acted to {"p4"}
        # After fix: should call process_call and keep p1 in players_acted
        import asyncio
        asyncio.run(_handle_action(table, "p4", msg))

        # p1 should still be in players_acted (not reset)
        assert "p1" in table.players_acted
        assert "p4" in table.players_acted
        # Should be treated as call, so total contributions is 790 (all their chips)
        assert table.total_contributions["p4"] == 790
        assert table.players["p4"].stack == 0
