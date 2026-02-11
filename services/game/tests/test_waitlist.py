"""
Tests for waitlist management functionality.
"""
import pytest
from app.core.models import TableState, Player, PlayerRole
from app.core.waitlist import (
    join_waitlist,
    leave_waitlist,
    promote_from_waitlist,
    get_waitlist_position,
)
from poker.constants import MAX_PLAYERS, DEFAULT_STARTING_STACK


@pytest.fixture
def table():
    return TableState(table_id="test")


@pytest.fixture
def table_with_spectator(table):
    """Table with one seated player and one spectator."""
    table.upsert_player("seated1", "Seated Player")
    table.upsert_player("spectator1", "Spectator", force_spectator=True, stack=1000)
    return table


@pytest.fixture
def full_table(table):
    """Table with MAX_PLAYERS seated."""
    for i in range(MAX_PLAYERS):
        table.upsert_player(f"player{i}", f"Player {i}")
    return table


class TestJoinWaitlist:
    def test_spectator_can_join(self, table_with_spectator):
        result = join_waitlist(table_with_spectator, "spectator1")
        assert result is True
        assert "spectator1" in table_with_spectator.waitlist
        assert table_with_spectator.players["spectator1"].role == PlayerRole.WAITLIST

    def test_seated_cannot_join(self, table_with_spectator):
        result = join_waitlist(table_with_spectator, "seated1")
        assert result is False
        assert "seated1" not in table_with_spectator.waitlist

    def test_duplicate_join_prevented(self, table_with_spectator):
        join_waitlist(table_with_spectator, "spectator1")
        result = join_waitlist(table_with_spectator, "spectator1")
        assert result is False
        assert table_with_spectator.waitlist.count("spectator1") == 1

    def test_nonexistent_player_cannot_join(self, table):
        result = join_waitlist(table, "nobody")
        assert result is False

    def test_spectator_with_zero_chips_cannot_join(self, table):
        # Add spectator with 0 chips
        table.upsert_player("broke_player", "Broke Player", stack=0)

        result = join_waitlist(table, "broke_player")

        assert result is False
        assert "broke_player" not in table.waitlist
        assert table.players["broke_player"].role == PlayerRole.SPECTATOR


class TestLeaveWaitlist:
    def test_can_leave_waitlist(self, table_with_spectator):
        join_waitlist(table_with_spectator, "spectator1")
        result = leave_waitlist(table_with_spectator, "spectator1")
        assert result is True
        assert "spectator1" not in table_with_spectator.waitlist
        assert table_with_spectator.players["spectator1"].role == PlayerRole.SPECTATOR

    def test_not_on_waitlist_returns_false(self, table_with_spectator):
        result = leave_waitlist(table_with_spectator, "spectator1")
        assert result is False


class TestPromoteFromWaitlist:
    def test_promotes_first_in_queue(self, table):
        # Add two spectators with chips
        table.upsert_player("p1", "Player 1")
        table.upsert_player("p2", "Player 2", force_spectator=True, stack=1000)
        table.upsert_player("p3", "Player 3", force_spectator=True, stack=1500)

        # Add to waitlist
        join_waitlist(table, "p2")
        join_waitlist(table, "p3")

        # Promote
        promoted = promote_from_waitlist(table)
        assert promoted == "p2"
        assert table.players["p2"].role == PlayerRole.SEATED
        assert table.players["p2"].stack == 1000  # Keeps their existing stack
        assert table.players["p2"].seat > 0

    def test_no_promotion_during_hand(self, table_with_spectator):
        join_waitlist(table_with_spectator, "spectator1")
        table_with_spectator.hand_in_progress = True
        promoted = promote_from_waitlist(table_with_spectator)
        assert promoted is None
        assert "spectator1" in table_with_spectator.waitlist

    def test_no_promotion_when_full(self, full_table):
        # Add spectator to full table
        full_table.upsert_player("spectator", "Spectator", force_spectator=True, stack=1000)
        join_waitlist(full_table, "spectator")

        promoted = promote_from_waitlist(full_table)
        assert promoted is None

    def test_skips_disconnected_players(self, table):
        table.upsert_player("p1", "Player 1")
        table.upsert_player("p2", "Player 2", force_spectator=True, stack=1000)
        table.upsert_player("p3", "Player 3", force_spectator=True, stack=1000)

        join_waitlist(table, "p2")
        join_waitlist(table, "p3")

        # Disconnect p2
        table.players["p2"].connected = False

        promoted = promote_from_waitlist(table)
        assert promoted == "p3"

    def test_skips_players_with_zero_chips(self, table):
        """Players with 0 chips should be skipped during promotion."""
        table.upsert_player("p1", "Player 1")
        table.upsert_player("broke", "Broke Player", force_spectator=True, stack=1000)
        table.upsert_player("rich", "Rich Player", force_spectator=True, stack=2000)

        # Manually add broke player to waitlist (normally wouldn't be allowed)
        table.waitlist.append("broke")
        table.players["broke"].role = PlayerRole.WAITLIST
        # Then set their chips to 0
        table.players["broke"].stack = 0

        # Add rich player normally
        join_waitlist(table, "rich")

        # Should skip broke player and promote rich player
        promoted = promote_from_waitlist(table)
        assert promoted == "rich"
        assert table.players["rich"].role == PlayerRole.SEATED


class TestGetWaitlistPosition:
    def test_returns_position(self, table_with_spectator):
        table_with_spectator.upsert_player("spec2", "Spectator 2", force_spectator=True, stack=1000)
        join_waitlist(table_with_spectator, "spectator1")
        join_waitlist(table_with_spectator, "spec2")

        assert get_waitlist_position(table_with_spectator, "spectator1") == 1
        assert get_waitlist_position(table_with_spectator, "spec2") == 2

    def test_not_on_waitlist_returns_zero(self, table_with_spectator):
        assert get_waitlist_position(table_with_spectator, "spectator1") == 0
        assert get_waitlist_position(table_with_spectator, "seated1") == 0


class TestPlayerCap:
    def test_max_players_enforced(self, table):
        """New players beyond MAX_PLAYERS become spectators."""
        # Fill the table
        for i in range(MAX_PLAYERS):
            table.upsert_player(f"player{i}", f"Player {i}")

        # Try to add one more
        player = table.upsert_player("extra", "Extra Player")
        assert player.role == PlayerRole.SPECTATOR
        assert player.stack == DEFAULT_STARTING_STACK  # Spectators keep their chips for waitlist

    def test_new_player_during_hand_is_spectator(self, table):
        """New players joining during a hand become spectators."""
        table.upsert_player("p1", "Player 1")
        table.hand_in_progress = True

        player = table.upsert_player("p2", "Player 2")
        assert player.role == PlayerRole.SPECTATOR

    def test_reconnecting_player_keeps_role(self, table):
        """Reconnecting players keep their existing role."""
        table.upsert_player("p1", "Player 1")
        table.players["p1"].connected = False
        table.hand_in_progress = True

        player = table.upsert_player("p1", "Player 1")
        assert player.role == PlayerRole.SEATED
        assert player.connected is True
