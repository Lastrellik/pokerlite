"""
Tests for data models.
"""
import pytest
from app.core.models import TableState, Player


class TestPlayer:
    """Tests for Player dataclass."""

    def test_default_values(self):
        player = Player(pid="test", name="Test Player")

        assert player.stack == 1000
        assert player.seat == 0
        assert player.connected is True

    def test_custom_values(self):
        player = Player(
            pid="p1",
            name="Alice",
            stack=500,
            seat=3,
            connected=False
        )

        assert player.pid == "p1"
        assert player.name == "Alice"
        assert player.stack == 500
        assert player.seat == 3
        assert player.connected is False


class TestTableState:
    """Tests for TableState dataclass."""

    def test_default_values(self):
        table = TableState(table_id="test-table")

        assert table.table_id == "test-table"
        assert table.hand_in_progress is False
        assert table.dealer_seat == 0
        assert table.pot == 0
        assert table.board == []
        assert table.street == "preflop"
        assert table.small_blind == 5
        assert table.big_blind == 10

    def test_upsert_player_new(self):
        table = TableState(table_id="test-table")

        player = table.upsert_player("p1", "Alice")

        assert player.pid == "p1"
        assert player.name == "Alice"
        assert player.seat == 1
        assert player.connected is True
        assert "p1" in table.players

    def test_upsert_player_existing(self):
        table = TableState(table_id="test-table")
        table.upsert_player("p1", "Alice")
        table.players["p1"].connected = False

        player = table.upsert_player("p1", "Alice Updated")

        assert player.name == "Alice Updated"
        assert player.connected is True

    def test_upsert_player_seat_assignment(self):
        table = TableState(table_id="test-table")

        table.upsert_player("p1", "Alice")
        table.upsert_player("p2", "Bob")
        table.upsert_player("p3", "Charlie")

        assert table.players["p1"].seat == 1
        assert table.players["p2"].seat == 2
        assert table.players["p3"].seat == 3

    def test_upsert_player_fills_gaps(self):
        table = TableState(table_id="test-table")
        table.upsert_player("p1", "Alice")  # seat 1
        table.upsert_player("p2", "Bob")    # seat 2
        del table.players["p1"]             # Remove seat 1

        table.upsert_player("p3", "Charlie")

        assert table.players["p3"].seat == 1  # Fills the gap

    def test_mark_disconnected(self):
        table = TableState(table_id="test-table")
        table.upsert_player("p1", "Alice")

        table.mark_disconnected("p1")

        assert table.players["p1"].connected is False

    def test_mark_disconnected_nonexistent(self):
        table = TableState(table_id="test-table")

        # Should not raise
        table.mark_disconnected("nonexistent")
