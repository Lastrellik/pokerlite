"""
Tests for player utility functions.
"""
import pytest
from app.core.player_utils import (
    connected_players,
    eligible_players,
    connected_pids,
    active_players,
    active_pids,
    get_player_seat,
    find_next_seat
)
from app.core.models import TableState, Player


class TestConnectedPlayers:
    """Tests for connected_players function."""

    def test_returns_connected_only(self, table_with_two_players):
        table = table_with_two_players
        table.players["p2"].connected = False

        result = connected_players(table)

        assert len(result) == 1
        assert result[0].pid == "p1"

    def test_sorted_by_seat(self, table_with_three_players):
        table = table_with_three_players
        # Swap seats to test sorting
        table.players["p3"].seat = 1
        table.players["p1"].seat = 3

        result = connected_players(table)

        assert result[0].pid == "p3"  # seat 1
        assert result[1].pid == "p2"  # seat 2
        assert result[2].pid == "p1"  # seat 3

    def test_empty_table(self, empty_table):
        result = connected_players(empty_table)
        assert result == []


class TestEligiblePlayers:
    """Tests for eligible_players function."""

    def test_excludes_zero_stack(self, table_with_two_players):
        table = table_with_two_players
        table.players["p2"].stack = 0

        result = eligible_players(table)

        assert len(result) == 1
        assert result[0].pid == "p1"

    def test_excludes_disconnected(self, table_with_two_players):
        table = table_with_two_players
        table.players["p2"].connected = False

        result = eligible_players(table)

        assert len(result) == 1

    def test_both_filters(self, table_with_three_players):
        table = table_with_three_players
        table.players["p2"].stack = 0
        table.players["p3"].connected = False

        result = eligible_players(table)

        assert len(result) == 1
        assert result[0].pid == "p1"


class TestConnectedPids:
    """Tests for connected_pids function."""

    def test_returns_pids(self, table_with_two_players):
        result = connected_pids(table_with_two_players)

        assert "p1" in result
        assert "p2" in result

    def test_excludes_disconnected(self, table_with_two_players):
        table = table_with_two_players
        table.players["p2"].connected = False

        result = connected_pids(table)

        assert result == ["p1"]


class TestActivePlayers:
    """Tests for active_players function."""

    def test_excludes_folded(self, table_with_two_players):
        table = table_with_two_players
        table.folded_pids = {"p2"}

        result = active_players(table)

        assert len(result) == 1
        assert result[0].pid == "p1"

    def test_all_active(self, table_with_two_players):
        result = active_players(table_with_two_players)
        assert len(result) == 2


class TestActivePids:
    """Tests for active_pids function."""

    def test_returns_pids(self, table_with_two_players):
        result = active_pids(table_with_two_players)

        assert "p1" in result
        assert "p2" in result

    def test_excludes_folded(self, table_with_two_players):
        table = table_with_two_players
        table.folded_pids = {"p1"}

        result = active_pids(table)

        assert result == ["p2"]


class TestGetPlayerSeat:
    """Tests for get_player_seat function."""

    def test_returns_seat(self, table_with_two_players):
        table = table_with_two_players

        assert get_player_seat(table, "p1") == 1
        assert get_player_seat(table, "p2") == 2

    def test_nonexistent_player(self, table_with_two_players):
        result = get_player_seat(table_with_two_players, "nonexistent")
        assert result == 0


class TestFindNextSeat:
    """Tests for find_next_seat function."""

    def test_next_seat(self):
        seats = [1, 2, 3]
        assert find_next_seat(seats, 1) == 2
        assert find_next_seat(seats, 2) == 3

    def test_wraps_around(self):
        seats = [1, 2, 3]
        assert find_next_seat(seats, 3) == 1

    def test_empty_seats(self):
        assert find_next_seat([], 1) == 0

    def test_seat_not_found(self):
        seats = [1, 2, 3]
        assert find_next_seat(seats, 5) == 1  # Falls back to first
