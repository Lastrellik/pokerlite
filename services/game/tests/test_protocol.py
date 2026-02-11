"""
Tests for protocol (public state serialization).
"""
import pytest
from app.core.models import TableState, PlayerRole
from app.core.protocol import public_state


@pytest.fixture
def table():
    return TableState(table_id="test")


class TestPublicState:
    def test_spectator_gets_my_stack(self, table):
        """Spectators should have their stack available in my_stack field."""
        # Add a spectator with chips
        table.upsert_player("spectator1", "Spectator", force_spectator=True, stack=1500)

        state = public_state(table, "spectator1")

        assert state["my_stack"] == 1500
        assert state["my_role"] == "spectator"

    def test_spectator_with_zero_chips_gets_my_stack(self, table):
        """Spectators with 0 chips should have my_stack = 0."""
        # Add a spectator with 0 chips
        table.upsert_player("broke", "Broke Player", force_spectator=True, stack=0)

        state = public_state(table, "broke")

        assert state["my_stack"] == 0
        assert state["my_role"] == "spectator"

    def test_waitlist_player_gets_my_stack(self, table):
        """Waitlist players should have their stack available."""
        from app.core.waitlist import join_waitlist

        # Add spectator with chips
        table.upsert_player("waiter", "Waiter", force_spectator=True, stack=2000)
        join_waitlist(table, "waiter")

        state = public_state(table, "waiter")

        assert state["my_stack"] == 2000
        assert state["my_role"] == "waitlist"
        assert state["waitlist_position"] == 1

    def test_seated_player_gets_my_stack(self, table):
        """Seated players should have their stack available."""
        table.upsert_player("player1", "Player 1", stack=3000)

        state = public_state(table, "player1")

        assert state["my_stack"] == 3000
        assert state["my_role"] == "seated"

    def test_no_viewer_has_zero_my_stack(self, table):
        """When there's no viewer, my_stack should be 0."""
        table.upsert_player("player1", "Player 1")

        state = public_state(table, None)

        assert state["my_stack"] == 0
        assert state["my_role"] is None

    def test_spectators_not_in_players_list(self, table):
        """Spectators should not appear in the main players list."""
        table.upsert_player("seated1", "Seated Player", stack=1000)
        table.upsert_player("spectator1", "Spectator", force_spectator=True, stack=500)

        state = public_state(table, "spectator1")

        # Players list should only have seated players
        assert len(state["players"]) == 1
        assert state["players"][0]["pid"] == "seated1"

        # Spectator should be in spectators list
        assert len(state["spectators"]) == 1
        assert state["spectators"][0]["pid"] == "spectator1"

        # But spectator can still see their stack via my_stack
        assert state["my_stack"] == 500
