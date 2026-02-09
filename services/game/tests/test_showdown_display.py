"""Tests for showdown display bug fixes."""
import pytest
from app.core.models import TableState, Player, PlayerRole
from app.core.game_flow import run_showdown, start_new_hand
from app.core.protocol import public_state


class TestShowdownDataPersistence:
    """Test that showdown data persists for display after hand ends."""

    def test_board_persists_after_showdown(self):
        """Board should remain visible after showdown for display."""
        table = TableState(table_id="test-table")
        table.hand_in_progress = True
        table.board = ["As", "Kh", "Qd", "Jc", "Ts"]
        table.pot = 100
        table.players = {
            "p1": Player(pid="p1", name="Alice", stack=50, seat=1, connected=True, role=PlayerRole.SEATED),
            "p2": Player(pid="p2", name="Bob", stack=0, seat=2, connected=True, role=PlayerRole.SEATED),
        }
        table.hole_cards = {
            "p1": ["Ah", "Kh"],
            "p2": ["7s", "8s"],
        }
        table.total_contributions = {"p1": 50, "p2": 50}

        # Run showdown
        run_showdown(table)

        # Board should still be visible after showdown (not cleared)
        # This allows frontend to display showdown properly
        assert table.board == ["As", "Kh", "Qd", "Jc", "Ts"]

    def test_hole_cards_persist_after_showdown(self):
        """Hole cards should remain visible after showdown for display."""
        table = TableState(table_id="test-table")
        table.hand_in_progress = True
        table.board = ["As", "Kh", "Qd", "Jc", "Ts"]
        table.pot = 100
        table.players = {
            "p1": Player(pid="p1", name="Alice", stack=50, seat=1, connected=True, role=PlayerRole.SEATED),
            "p2": Player(pid="p2", name="Bob", stack=0, seat=2, connected=True, role=PlayerRole.SEATED),
        }
        table.hole_cards = {
            "p1": ["Ah", "Kh"],
            "p2": ["7s", "8s"],
        }
        table.total_contributions = {"p1": 50, "p2": 50}

        # Run showdown
        run_showdown(table)

        # Hole cards should still exist (not cleared)
        assert "p1" in table.hole_cards
        assert "p2" in table.hole_cards
        assert table.hole_cards["p1"] == ["Ah", "Kh"]
        assert table.hole_cards["p2"] == ["7s", "8s"]

    def test_busted_player_stays_seated_after_showdown(self):
        """Busted players should stay SEATED after showdown (converted at next hand start)."""
        table = TableState(table_id="test-table")
        table.hand_in_progress = True
        table.board = ["2h", "3d", "4c", "5s", "9h"]
        table.pot = 100
        table.players = {
            "p1": Player(pid="p1", name="Alice", stack=1000, seat=1, connected=True, role=PlayerRole.SEATED),
            "p2": Player(pid="p2", name="Bob", stack=0, seat=2, connected=True, role=PlayerRole.SEATED),
        }
        table.hole_cards = {
            "p1": ["Ah", "Kh"],
            "p2": ["7s", "8s"],
        }
        table.total_contributions = {"p1": 50, "p2": 50}

        # Run showdown (p1 wins, p2 remains busted)
        run_showdown(table)

        # p2 should still be SEATED (not converted to SPECTATOR yet)
        # This allows showdown data to be displayed properly
        assert table.players["p2"].role == PlayerRole.SEATED
        assert table.players["p2"].stack == 0
        assert "p2" not in table.spectator_pids

    def test_board_cleared_at_next_hand_start(self):
        """Board should be cleared when next hand starts."""
        table = TableState(table_id="test-table")
        table.board = ["As", "Kh", "Qd", "Jc", "Ts"]  # Old board
        table.hole_cards = {"p1": ["Ah", "Kh"]}  # Old hole cards
        table.players = {
            "p1": Player(pid="p1", name="Alice", stack=100, seat=1, connected=True, role=PlayerRole.SEATED),
            "p2": Player(pid="p2", name="Bob", stack=100, seat=2, connected=True, role=PlayerRole.SEATED),
        }

        # Start new hand
        start_new_hand(table)

        # Board should be cleared (new hand)
        assert len(table.board) == 0
        # New hole cards dealt (2 cards per player)
        assert len(table.hole_cards["p1"]) == 2
        assert len(table.hole_cards["p2"]) == 2


class TestRunoutFlag:
    """Test that runout_in_progress flag is included in protocol."""

    def test_runout_flag_in_state(self):
        """runout_in_progress should be included in public state."""
        table = TableState(table_id="test-table")
        table.hand_in_progress = True
        table.runout_in_progress = True
        table.players = {
            "p1": Player(pid="p1", name="Alice", stack=0, seat=1, connected=True, role=PlayerRole.SEATED),
        }

        state = public_state(table, "p1")

        assert "runout_in_progress" in state
        assert state["runout_in_progress"] is True

    def test_runout_flag_false_by_default(self):
        """runout_in_progress should be False by default."""
        table = TableState(table_id="test-table")
        table.hand_in_progress = True
        table.players = {
            "p1": Player(pid="p1", name="Alice", stack=100, seat=1, connected=True, role=PlayerRole.SEATED),
        }

        state = public_state(table, "p1")

        assert state["runout_in_progress"] is False
