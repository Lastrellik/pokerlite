"""Tests for action handling."""
import pytest
from app.core.actions import handle_message
from app.core.game_flow import start_new_hand
from app.core.models import TableState, Player, PlayerRole


@pytest.fixture
def table_with_three_players():
    """Create a table with three players for testing."""
    table = TableState(table_id="test-table")
    table.players = {
        "p1": Player(pid="p1", name="Alice", stack=1000, seat=1, connected=True, role=PlayerRole.SEATED),
        "p2": Player(pid="p2", name="Bob", stack=1000, seat=2, connected=True, role=PlayerRole.SEATED),
        "p3": Player(pid="p3", name="Charlie", stack=1000, seat=3, connected=True, role=PlayerRole.SEATED),
    }
    return table


class TestActionHandling:
    """Tests for handle_message action processing."""

    @pytest.mark.asyncio
    async def test_handle_fold_action(self, table_with_three_players):
        """Test folding reduces active players."""
        table = table_with_three_players
        start_new_hand(table)
        current_pid = table.current_turn_pid

        result = await handle_message(table, current_pid, {"type": "action", "action": "fold"})

        assert "folds" in result
        assert current_pid in table.folded_pids

    @pytest.mark.asyncio
    async def test_handle_check_action(self, table_with_three_players):
        """Test checking when no bet to call."""
        table = table_with_three_players
        start_new_hand(table)

        # Get to a state where checking is valid (BB can check if everyone limps)
        while table.current_bet > table.player_bets.get(table.current_turn_pid, 0):
            pid = table.current_turn_pid
            await handle_message(table, pid, {"type": "action", "action": "call"})

        current_pid = table.current_turn_pid
        result = await handle_message(table, current_pid, {"type": "action", "action": "check"})

        # Check completes betting and advances to flop
        assert "Dealing Flop" in result or "checks" in result

    @pytest.mark.asyncio
    async def test_handle_call_action(self, table_with_three_players):
        """Test calling matches the current bet."""
        table = table_with_three_players
        start_new_hand(table)
        current_pid = table.current_turn_pid
        initial_bet = table.player_bets.get(current_pid, 0)

        result = await handle_message(table, current_pid, {"type": "action", "action": "call"})

        assert "calls" in result or "all-in" in result
        assert table.player_bets[current_pid] >= initial_bet

    @pytest.mark.asyncio
    async def test_handle_raise_action(self, table_with_three_players):
        """Test raising increases the current bet."""
        table = table_with_three_players
        start_new_hand(table)
        current_pid = table.current_turn_pid
        old_bet = table.current_bet

        result = await handle_message(table, current_pid, {"type": "action", "action": "raise", "amount": 50})

        assert "raises" in result
        assert table.current_bet > old_bet
        assert table.player_bets[current_pid] == 50

    @pytest.mark.asyncio
    async def test_handle_all_in_action(self, table_with_three_players):
        """Test going all-in."""
        table = table_with_three_players
        start_new_hand(table)
        current_pid = table.current_turn_pid
        initial_stack = table.players[current_pid].stack

        result = await handle_message(table, current_pid, {"type": "action", "action": "all_in"})

        assert "all-in" in result
        assert table.players[current_pid].stack == 0
        assert table.player_bets[current_pid] == initial_stack

    @pytest.mark.asyncio
    async def test_invalid_action_returns_none(self, table_with_three_players):
        """Test that invalid actions return None."""
        table = table_with_three_players
        start_new_hand(table)

        result = await handle_message(table, "p1", {"type": "action", "action": "invalid"})

        assert result is None

    @pytest.mark.asyncio
    async def test_action_not_your_turn_returns_none(self, table_with_three_players):
        """Test that acting out of turn returns None."""
        table = table_with_three_players
        start_new_hand(table)
        
        # Find a player who is NOT current
        not_current = [pid for pid in table.players if pid != table.current_turn_pid][0]

        result = await handle_message(table, not_current, {"type": "action", "action": "check"})

        assert result is None

    @pytest.mark.asyncio
    async def test_betting_complete_advances_street(self, table_with_three_players):
        """Test that completing betting round advances to next street."""
        table = table_with_three_players
        start_new_hand(table)
        
        # Everyone calls to complete preflop
        while table.street == "preflop":
            pid = table.current_turn_pid
            result = await handle_message(table, pid, {"type": "action", "action": "call"})
            if "Dealing Flop" in result:
                break

        assert table.street == "flop"
        assert len(table.board) == 3

    @pytest.mark.asyncio
    async def test_all_in_call_message_format(self, table_with_three_players):
        """Test that all-in calls show correct message format."""
        table = table_with_three_players
        start_new_hand(table)
        
        # First player raises big
        pid1 = table.current_turn_pid
        await handle_message(table, pid1, {"type": "action", "action": "raise", "amount": 500})
        
        # Next player with smaller stack calls all-in
        pid2 = table.current_turn_pid
        table.players[pid2].stack = 300  # Set stack smaller than bet
        table.player_bets[pid2] = 10  # Already has BB in
        
        result = await handle_message(table, pid2, {"type": "action", "action": "call"})
        
        assert "goes all-in for" in result
        assert table.players[pid2].stack == 0

    @pytest.mark.asyncio
    async def test_everyone_folds_triggers_showdown(self, table_with_three_players):
        """Test that when everyone folds, one player wins."""
        table = table_with_three_players
        start_new_hand(table)
        
        # Get all players except one to fold
        pids = list(table.players.keys())
        for _ in range(len(pids) - 1):
            pid = table.current_turn_pid
            result = await handle_message(table, pid, {"type": "action", "action": "fold"})
            if "wins" in result:
                break
        
        assert table.hand_in_progress is False

    @pytest.mark.asyncio
    async def test_complete_hand_to_showdown(self, table_with_three_players):
        """Test a complete hand from start to showdown."""
        table = table_with_three_players
        start_new_hand(table)
        
        # Play through all streets
        while table.hand_in_progress:
            pid = table.current_turn_pid
            if not pid:
                break
            result = await handle_message(table, pid, {"type": "action", "action": "call"})
            if result and "wins" in result:
                break
        
        assert table.hand_in_progress is False
        assert table.showdown_data is not None

    @pytest.mark.asyncio
    async def test_runout_clears_turn_state(self, table_with_three_players):
        """Test that turn state is cleared when entering runout mode."""
        table = table_with_three_players
        start_new_hand(table)

        # Get everyone to call on preflop
        while table.street == "preflop" and table.current_turn_pid:
            pid = table.current_turn_pid
            await handle_message(table, pid, {"type": "action", "action": "call"})
            # Stop if we advanced to flop
            if table.street != "preflop":
                break

        # Now simulate everyone going all-in on flop
        # Set them all to have same small stack so they all go all-in together
        for p in table.players.values():
            p.stack = 50

        # First player goes all-in
        pid = table.current_turn_pid
        await handle_message(table, pid, {"type": "action", "action": "all_in"})

        # Second player calls all-in
        pid = table.current_turn_pid
        await handle_message(table, pid, {"type": "action", "action": "call"})

        # Third player calls all-in - this completes betting with everyone all-in
        pid = table.current_turn_pid
        result = await handle_message(table, pid, {"type": "action", "action": "call"})

        # Should now be in runout mode with turn cleared
        assert table.runout_in_progress is True
        assert table.current_turn_pid is None
