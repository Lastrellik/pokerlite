"""Tests for real-time side pot calculation."""
import pytest
from app.core.models import TableState
from app.core.game_flow import calculate_side_pots


class TestCalculateSidePots:
    """Test calculate_side_pots function."""

    def test_equal_contributions_single_pot(self):
        """When all players contribute equally, should return single pot."""
        table = TableState(table_id="test")
        table.pot = 100
        table.total_contributions = {"p1": 50, "p2": 50}

        pots = calculate_side_pots(table, ["p1", "p2"])

        assert len(pots) == 1
        assert pots[0]['amount'] == 100
        assert pots[0]['eligible_players'] == {"p1", "p2"}

    def test_different_contributions_multiple_pots(self):
        """When players contribute different amounts, should create side pots."""
        table = TableState(table_id="test")
        table.pot = 150
        table.total_contributions = {
            "p1": 50,   # All-in for 50
            "p2": 100,  # Calls 100
        }

        pots = calculate_side_pots(table, ["p1", "p2"])

        assert len(pots) == 2
        # Main pot: 50 * 2 = 100, eligible: both
        assert pots[0]['amount'] == 100
        assert pots[0]['eligible_players'] == {"p1", "p2"}
        # Side pot: 50 * 1 = 50, eligible: p2 only
        assert pots[1]['amount'] == 50
        assert pots[1]['eligible_players'] == {"p2"}

    def test_three_players_different_stacks(self):
        """Three players with different all-in amounts."""
        table = TableState(table_id="test")
        table.pot = 450
        table.total_contributions = {
            "p1": 50,   # Short stack all-in
            "p2": 100,  # Medium stack all-in
            "p3": 300,  # Large stack
        }

        pots = calculate_side_pots(table, ["p1", "p2", "p3"])

        assert len(pots) == 3
        # Main pot: 50 * 3 = 150
        assert pots[0]['amount'] == 150
        assert pots[0]['eligible_players'] == {"p1", "p2", "p3"}
        # Side pot 1: (100-50) * 2 = 100
        assert pots[1]['amount'] == 100
        assert pots[1]['eligible_players'] == {"p2", "p3"}
        # Side pot 2: (300-100) * 1 = 200
        assert pots[2]['amount'] == 200
        assert pots[2]['eligible_players'] == {"p3"}

    def test_empty_player_list(self):
        """Empty player list should return empty pot list."""
        table = TableState(table_id="test")
        table.pot = 100

        pots = calculate_side_pots(table, [])

        assert pots == []

    def test_single_player(self):
        """Single player should get entire pot."""
        table = TableState(table_id="test")
        table.pot = 100
        table.total_contributions = {"p1": 100}

        pots = calculate_side_pots(table, ["p1"])

        assert len(pots) == 1
        assert pots[0]['amount'] == 100
        assert pots[0]['eligible_players'] == {"p1"}

    def test_zero_contributions(self):
        """Players with zero contributions (preflop, all check)."""
        table = TableState(table_id="test")
        table.pot = 0
        table.total_contributions = {}

        pots = calculate_side_pots(table, ["p1", "p2"])

        assert len(pots) == 1
        assert pots[0]['amount'] == 0
        assert pots[0]['eligible_players'] == {"p1", "p2"}
