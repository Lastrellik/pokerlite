"""Tests for table cleanup and player removal."""
import pytest
from app.core.models import TableState
from models.player import PlayerRole


class TestPlayerRemoval:
    """Test remove_player functionality."""

    def test_remove_player_removes_from_all_structures(self):
        """Player should be completely removed from table."""
        table = TableState(table_id="test")
        table.upsert_player("p1", "Alice")
        table.upsert_player("p2", "Bob")

        # Verify player exists
        assert "p1" in table.players
        assert len(table.players) == 2

        # Remove player
        table.remove_player("p1")

        # Verify removed
        assert "p1" not in table.players
        assert len(table.players) == 1
        assert "p2" in table.players

    def test_remove_seated_player_frees_seat(self):
        """Removing a seated player should free their seat."""
        table = TableState(table_id="test")
        p1 = table.upsert_player("p1", "Alice")
        seat1 = p1.seat

        # Remove player
        table.remove_player("p1")

        # New player should be able to take that seat
        p2 = table.upsert_player("p2", "Bob")
        assert p2.seat == seat1

    def test_remove_spectator(self):
        """Removing a spectator should clean up spectator tracking."""
        table = TableState(table_id="test")
        # Force spectator
        p1 = table.upsert_player("p1", "Alice", force_spectator=True)
        assert p1.role == PlayerRole.SPECTATOR
        assert "p1" in table.spectator_pids

        # Remove
        table.remove_player("p1")

        # Verify cleaned up
        assert "p1" not in table.players
        assert "p1" not in table.spectator_pids

    def test_remove_from_waitlist(self):
        """Removing a player should remove them from waitlist."""
        table = TableState(table_id="test")
        table.upsert_player("p1", "Alice", force_spectator=True)
        table.waitlist.append("p1")

        # Remove
        table.remove_player("p1")

        # Verify removed from waitlist
        assert "p1" not in table.waitlist

    def test_remove_nonexistent_player(self):
        """Removing non-existent player should not error."""
        table = TableState(table_id="test")
        # Should not raise
        table.remove_player("nonexistent")


class TestIsEmpty:
    """Test is_empty functionality."""

    def test_empty_table(self):
        """New table should be empty."""
        table = TableState(table_id="test")
        assert table.is_empty()

    def test_table_with_players_not_empty(self):
        """Table with players should not be empty."""
        table = TableState(table_id="test")
        table.upsert_player("p1", "Alice")
        assert not table.is_empty()

    def test_table_empty_after_removing_all_players(self):
        """Table should be empty after all players leave."""
        table = TableState(table_id="test")
        table.upsert_player("p1", "Alice")
        table.upsert_player("p2", "Bob")

        assert not table.is_empty()

        table.remove_player("p1")
        assert not table.is_empty()

        table.remove_player("p2")
        assert table.is_empty()

    def test_spectators_count_as_players(self):
        """Spectators should count toward table being non-empty."""
        table = TableState(table_id="test")
        table.upsert_player("p1", "Alice", force_spectator=True)
        assert not table.is_empty()
