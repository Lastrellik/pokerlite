"""
Tests for game flow and street progression logic.
"""
import pytest
import time
from app.core.game_flow import (
    start_new_hand,
    advance_turn,
    advance_street,
    run_showdown,
    check_turn_timeout,
    _advance_dealer,
    _get_first_postflop_actor,
    TURN_TIMEOUT_SECONDS
)
from app.core.models import TableState, Player


class TestStartNewHand:
    """Tests for start_new_hand function."""

    def test_starts_hand_with_two_players(self, table_with_two_players):
        table = table_with_two_players

        start_new_hand(table)

        assert table.hand_in_progress is True
        assert table.street == "preflop"
        assert len(table.board) == 0
        assert table.pot == 15  # SB + BB

    def test_deals_hole_cards(self, table_with_two_players):
        table = table_with_two_players

        start_new_hand(table)

        assert len(table.hole_cards) == 2
        assert len(table.hole_cards["p1"]) == 2
        assert len(table.hole_cards["p2"]) == 2

    def test_sets_current_turn(self, table_with_two_players):
        table = table_with_two_players

        start_new_hand(table)

        assert table.current_turn_pid is not None
        assert table.turn_deadline is not None

    def test_clears_previous_showdown(self, table_with_two_players):
        table = table_with_two_players
        table.showdown_data = {"some": "data"}

        start_new_hand(table)

        assert table.showdown_data is None

    def test_not_enough_players(self, empty_table):
        table = empty_table
        table.players["p1"] = Player(pid="p1", name="Alice", stack=1000, seat=1)

        start_new_hand(table)

        assert table.hand_in_progress is False

    def test_resets_folded_and_acted(self, table_with_two_players):
        table = table_with_two_players
        table.folded_pids = {"p1"}
        table.players_acted = {"p1", "p2"}

        start_new_hand(table)

        assert len(table.folded_pids) == 0
        assert len(table.players_acted) == 0


class TestAdvanceDealer:
    """Tests for _advance_dealer function."""

    def test_first_hand_uses_first_seat(self, table_with_two_players):
        table = table_with_two_players
        table.dealer_seat = 0  # No dealer yet
        players = list(table.players.values())

        _advance_dealer(table, players)

        assert table.dealer_seat == 1  # First seat

    def test_advances_to_next_player(self, table_with_two_players):
        table = table_with_two_players
        table.dealer_seat = 1
        players = list(table.players.values())

        _advance_dealer(table, players)

        assert table.dealer_seat == 2

    def test_wraps_around(self, table_with_two_players):
        table = table_with_two_players
        table.dealer_seat = 2
        players = list(table.players.values())

        _advance_dealer(table, players)

        assert table.dealer_seat == 1


class TestAdvanceTurn:
    """Tests for advance_turn function."""

    def test_advances_to_next_player(self, table_with_blinds_posted):
        table = table_with_blinds_posted
        table.current_turn_pid = "p1"

        advance_turn(table)

        assert table.current_turn_pid == "p2"

    def test_wraps_around(self, table_with_blinds_posted):
        table = table_with_blinds_posted
        table.current_turn_pid = "p2"

        advance_turn(table)

        assert table.current_turn_pid == "p1"

    def test_skips_folded_players(self, table_with_three_players):
        table = table_with_three_players
        table.hand_in_progress = True
        table.current_turn_pid = "p1"
        table.folded_pids = {"p2"}

        advance_turn(table)

        assert table.current_turn_pid == "p3"

    def test_sets_deadline(self, table_with_blinds_posted):
        table = table_with_blinds_posted

        advance_turn(table)

        assert table.turn_deadline is not None
        assert table.turn_deadline > time.time()


class TestAdvanceStreet:
    """Tests for advance_street function."""

    def test_preflop_to_flop(self, table_with_blinds_posted):
        table = table_with_blinds_posted
        table.street = "preflop"

        result = advance_street(table)

        assert result is True
        assert table.street == "flop"
        assert len(table.board) == 3

    def test_flop_to_turn(self, table_mid_hand):
        table = table_mid_hand
        table.street = "flop"
        table.board = ["Ah", "Kd", "7c"]

        result = advance_street(table)

        assert result is True
        assert table.street == "turn"
        assert len(table.board) == 4

    def test_turn_to_river(self, table_mid_hand):
        table = table_mid_hand
        table.street = "turn"
        table.board = ["Ah", "Kd", "7c", "2s"]

        result = advance_street(table)

        assert result is True
        assert table.street == "river"
        assert len(table.board) == 5

    def test_river_ends_hand(self, table_mid_hand):
        table = table_mid_hand
        table.street = "river"
        table.board = ["Ah", "Kd", "7c", "2s", "Qh"]

        result = advance_street(table)

        assert result is False

    def test_resets_betting_state(self, table_mid_hand):
        table = table_mid_hand
        table.street = "preflop"
        table.current_bet = 20
        table.player_bets = {"p1": 20, "p2": 20}
        table.players_acted = {"p1", "p2"}

        advance_street(table)

        assert table.current_bet == 0
        assert table.player_bets == {}
        assert len(table.players_acted) == 0


class TestGetFirstPostflopActor:
    """Tests for _get_first_postflop_actor function."""

    def test_returns_first_after_dealer(self, table_mid_hand):
        table = table_mid_hand
        table.dealer_seat = 1  # p1 is dealer

        first = _get_first_postflop_actor(table)

        assert first == "p2"  # p2 is first after dealer

    def test_wraps_around(self, table_mid_hand):
        table = table_mid_hand
        table.dealer_seat = 2  # p2 is dealer

        first = _get_first_postflop_actor(table)

        assert first == "p1"  # Wraps to p1


class TestRunShowdown:
    """Tests for run_showdown function."""

    def test_single_player_wins(self, table_mid_hand):
        table = table_mid_hand
        table.folded_pids = {"p2"}
        table.pot = 100

        result = run_showdown(table)

        assert "Alice" in result
        assert "100" in result
        assert table.players["p1"].stack == 1000  # 900 + 100

    def test_awards_pot_to_winner(self, table_mid_hand):
        table = table_mid_hand
        initial_stack = table.players["p2"].stack
        table.pot = 200
        table.board = ["2h", "3d", "4c", "5s", "9h"]
        table.hole_cards = {
            "p1": ["7h", "Kc"],  # High card
            "p2": ["As", "Ad"],  # Pair of aces - wins
        }

        result = run_showdown(table)

        assert "Bob" in result
        assert table.players["p2"].stack == initial_stack + 200

    def test_split_pot_on_tie(self, table_mid_hand):
        table = table_mid_hand
        table.pot = 200
        table.board = ["2h", "3d", "4c", "5s", "6h"]  # Straight on board
        table.hole_cards = {
            "p1": ["7h", "8h"],  # Doesn't improve
            "p2": ["7s", "8s"],  # Same hand
        }

        result = run_showdown(table)

        assert "Split pot" in result or "tie" in result.lower()

    def test_creates_showdown_data(self, table_mid_hand):
        table = table_mid_hand
        table.pot = 100
        table.board = ["2h", "3d", "4c", "5s", "9h"]
        table.hole_cards = {
            "p1": ["Ah", "Kh"],
            "p2": ["As", "Ad"],
        }

        run_showdown(table)

        assert table.showdown_data is not None
        assert "winner_pids" in table.showdown_data
        assert "players" in table.showdown_data
        assert len(table.showdown_data["players"]) == 2

    def test_ends_hand(self, table_mid_hand):
        table = table_mid_hand
        table.pot = 100
        table.board = ["2h", "3d", "4c", "5s", "9h"]
        table.hole_cards = {
            "p1": ["Ah", "Kh"],
            "p2": ["As", "Ad"],
        }

        run_showdown(table)

        assert table.hand_in_progress is False
        assert table.pot == 0


class TestCheckTurnTimeout:
    """Tests for check_turn_timeout function."""

    def test_no_timeout_when_not_expired(self, table_with_blinds_posted):
        table = table_with_blinds_posted
        table.turn_deadline = time.time() + 100  # Far in future

        timed_out, action = check_turn_timeout(table)

        assert timed_out is False
        assert action == ""

    def test_timeout_folds_when_facing_bet(self, table_with_blinds_posted):
        table = table_with_blinds_posted
        table.turn_deadline = time.time() - 1  # Expired
        table.current_turn_pid = "p1"
        table.current_bet = 10
        table.player_bets = {"p1": 5}

        timed_out, action = check_turn_timeout(table)

        assert timed_out is True
        assert action == "fold"
        assert "p1" in table.folded_pids

    def test_timeout_checks_when_no_bet(self, table_with_blinds_posted):
        table = table_with_blinds_posted
        table.turn_deadline = time.time() - 1
        table.current_turn_pid = "p1"
        table.current_bet = 5
        table.player_bets = {"p1": 5}  # Already matched

        timed_out, action = check_turn_timeout(table)

        assert timed_out is True
        assert action == "check"

    def test_no_timeout_when_no_hand(self, empty_table):
        table = empty_table
        table.hand_in_progress = False

        timed_out, action = check_turn_timeout(table)

        assert timed_out is False


class TestTurnOrderBugFix:
    """Tests for turn order bug fix - ensuring turn advances correctly when current player folds."""

    def test_turn_advances_when_current_player_folds(self):
        """Test that turn advances to next player when current player folds (not back to pids[0])."""
        from app.core.models import PlayerRole

        table = TableState(table_id="test-table")
        # Create 4 players in seats 1, 2, 3, 4
        table.players = {
            "p1": Player(pid="p1", name="Alice", stack=1000, seat=1, connected=True, role=PlayerRole.SEATED),
            "p2": Player(pid="p2", name="Bob", stack=1000, seat=2, connected=True, role=PlayerRole.SEATED),
            "p3": Player(pid="p3", name="Charlie", stack=1000, seat=3, connected=True, role=PlayerRole.SEATED),
            "p4": Player(pid="p4", name="David", stack=1000, seat=4, connected=True, role=PlayerRole.SEATED),
        }
        table.hand_in_progress = True
        table.dealer_seat = 1

        # Turn is on p2 (seat 2)
        table.current_turn_pid = "p2"

        # p2 folds
        table.folded_pids.add("p2")

        # Advance turn
        advance_turn(table)

        # Turn should advance to p3 (seat 3), NOT back to p1 (seat 1, which is pids[0])
        assert table.current_turn_pid == "p3"

    def test_turn_advances_correctly_after_raise_then_fold(self):
        """Test specific bug scenario: Player A raises, turn advances to Player B, Player B folds."""
        from app.core.models import PlayerRole

        table = TableState(table_id="test-table")
        # Create 4 players
        table.players = {
            "p1": Player(pid="p1", name="Alice", stack=1000, seat=1, connected=True, role=PlayerRole.SEATED),
            "p2": Player(pid="p2", name="Bob", stack=900, seat=2, connected=True, role=PlayerRole.SEATED),
            "p3": Player(pid="p3", name="Charlie", stack=1000, seat=3, connected=True, role=PlayerRole.SEATED),
            "p4": Player(pid="p4", name="David", stack=1000, seat=4, connected=True, role=PlayerRole.SEATED),
        }
        table.hand_in_progress = True
        table.dealer_seat = 1
        table.current_bet = 100  # p2 raised to 100
        table.player_bets = {"p2": 100}
        table.players_acted = {"p2"}  # Only p2 has acted (after raise)

        # Turn is on p3 after p2's raise
        table.current_turn_pid = "p3"

        # p3 folds
        table.folded_pids.add("p3")

        # Advance turn
        advance_turn(table)

        # Turn should advance to p4 (seat 4), not wrap back to p1
        assert table.current_turn_pid == "p4"

    def test_turn_wraps_correctly_when_last_player_folds(self):
        """Test that turn wraps around correctly when last player (by seat) folds."""
        from app.core.models import PlayerRole

        table = TableState(table_id="test-table")
        table.players = {
            "p1": Player(pid="p1", name="Alice", stack=1000, seat=1, connected=True, role=PlayerRole.SEATED),
            "p2": Player(pid="p2", name="Bob", stack=1000, seat=2, connected=True, role=PlayerRole.SEATED),
            "p4": Player(pid="p4", name="David", stack=1000, seat=4, connected=True, role=PlayerRole.SEATED),
        }
        table.hand_in_progress = True
        table.dealer_seat = 1

        # Turn is on p4 (highest seat)
        table.current_turn_pid = "p4"

        # p4 folds
        table.folded_pids.add("p4")

        # Advance turn
        advance_turn(table)

        # Turn should wrap to p1 (lowest seat)
        assert table.current_turn_pid == "p1"

    def test_turn_advances_when_disconnected_player_on_turn(self):
        """Test that turn advances correctly when current player disconnects."""
        from app.core.models import PlayerRole

        table = TableState(table_id="test-table")
        table.players = {
            "p1": Player(pid="p1", name="Alice", stack=1000, seat=1, connected=True, role=PlayerRole.SEATED),
            "p2": Player(pid="p2", name="Bob", stack=1000, seat=2, connected=False, role=PlayerRole.SEATED),
            "p3": Player(pid="p3", name="Charlie", stack=1000, seat=3, connected=True, role=PlayerRole.SEATED),
        }
        table.hand_in_progress = True
        table.dealer_seat = 1

        # Turn is on p2 who just disconnected
        table.current_turn_pid = "p2"

        # Advance turn (p2 not in active list because disconnected)
        advance_turn(table)

        # Turn should advance to p3, not back to p1
        assert table.current_turn_pid == "p3"


class TestSidePots:
    """Tests for side pot handling when players have different stack sizes."""

    def test_side_pot_short_stack_wins(self):
        """Test side pot when player with fewer chips wins."""
        from app.core.models import PlayerRole

        table = TableState(table_id="test-table")
        # Player A: 1000 chips, Player B: 500 chips
        table.players = {
            "pA": Player(pid="pA", name="Alice", stack=0, seat=1, connected=True, role=PlayerRole.SEATED),
            "pB": Player(pid="pB", name="Bob", stack=0, seat=2, connected=True, role=PlayerRole.SEATED),
        }
        table.hand_in_progress = True
        table.pot = 1500  # 1000 from A + 500 from B
        table.board = ["2h", "3d", "4c", "5s", "9h"]
        table.hole_cards = {
            "pA": ["7h", "Kc"],  # High card K
            "pB": ["As", "Ad"],  # Pair of aces - WINS
        }
        table.player_bets = {
            "pA": 1000,
            "pB": 500,
        }

        run_showdown(table)

        # Bob should win only 1000 (500 from himself + 500 matched from Alice)
        # Alice gets back her unmatched 500
        assert table.players["pB"].stack == 1000
        assert table.players["pA"].stack == 500

    def test_side_pot_large_stack_wins(self):
        """Test side pot when player with more chips wins."""
        from app.core.models import PlayerRole

        table = TableState(table_id="test-table")
        table.players = {
            "pA": Player(pid="pA", name="Alice", stack=0, seat=1, connected=True, role=PlayerRole.SEATED),
            "pB": Player(pid="pB", name="Bob", stack=0, seat=2, connected=True, role=PlayerRole.SEATED),
        }
        table.hand_in_progress = True
        table.pot = 1500
        table.board = ["2h", "3d", "4c", "5s", "9h"]
        table.hole_cards = {
            "pA": ["As", "Ad"],  # Pair of aces - WINS
            "pB": ["7h", "Kc"],  # High card K
        }
        table.player_bets = {
            "pA": 1000,
            "pB": 500,
        }

        run_showdown(table)

        # Alice should win everything (1500)
        assert table.players["pA"].stack == 1500
        assert table.players["pB"].stack == 0

    def test_side_pot_three_players(self):
        """Test multiple side pots with three players of different stacks."""
        from app.core.models import PlayerRole

        table = TableState(table_id="test-table")
        # Player A: 1000, Player B: 500, Player C: 300
        table.players = {
            "pA": Player(pid="pA", name="Alice", stack=0, seat=1, connected=True, role=PlayerRole.SEATED),
            "pB": Player(pid="pB", name="Bob", stack=0, seat=2, connected=True, role=PlayerRole.SEATED),
            "pC": Player(pid="pC", name="Charlie", stack=0, seat=3, connected=True, role=PlayerRole.SEATED),
        }
        table.hand_in_progress = True
        table.pot = 1800  # 1000 + 500 + 300
        table.board = ["Kh", "Qd", "Jc", "2s", "3h"]
        table.hole_cards = {
            "pA": ["7h", "8c"],  # High card K
            "pB": ["Th", "Tc"],  # Pair of tens - BEST HAND
            "pC": ["9h", "9s"],  # Pair of nines - second best
        }
        table.player_bets = {
            "pA": 1000,
            "pB": 500,
            "pC": 300,
        }

        run_showdown(table)

        # Side pot structure:
        # Pot 1 (main): 300 * 3 = 900 (A, B, C eligible) - Bob wins (best hand)
        # Pot 2: 200 * 2 = 400 (A, B eligible) - Bob wins (best hand)
        # Pot 3: 500 * 1 = 500 (A only) - Alice gets back her excess
        assert table.players["pB"].stack == 1300  # Wins pots 1 and 2
        assert table.players["pA"].stack == 500   # Gets back unmatched chips
        assert table.players["pC"].stack == 0     # Lost

    def test_side_pot_short_stack_wins_only_eligible_pot(self):
        """Test that short stack winner only gets the pot they're eligible for."""
        from app.core.models import PlayerRole

        table = TableState(table_id="test-table")
        table.players = {
            "pA": Player(pid="pA", name="Alice", stack=0, seat=1, connected=True, role=PlayerRole.SEATED),
            "pB": Player(pid="pB", name="Bob", stack=0, seat=2, connected=True, role=PlayerRole.SEATED),
            "pC": Player(pid="pC", name="Charlie", stack=0, seat=3, connected=True, role=PlayerRole.SEATED),
        }
        table.hand_in_progress = True
        table.pot = 1800
        table.board = ["Ah", "Qd", "Jc", "9s", "2h"]
        table.hole_cards = {
            "pA": ["7h", "8c"],  # High card A
            "pB": ["Kh", "Kc"],  # Pair of kings - BEST HAND but short stack
            "pC": ["Th", "Ts"],  # Pair of tens - SECOND BEST
        }
        table.player_bets = {
            "pA": 1000,
            "pB": 300,   # Short stack with best hand
            "pC": 500,
        }

        run_showdown(table)

        # Pot 1 (main): 300 * 3 = 900 - Bob wins (best hand)
        # Pot 2: 200 * 2 = 400 (A, C eligible) - Charlie wins (second best hand among A, C)
        # Pot 3: 500 * 1 = 500 (A only) - Alice gets back
        assert table.players["pB"].stack == 900   # Wins only main pot
        assert table.players["pC"].stack == 400   # Wins side pot
        assert table.players["pA"].stack == 500   # Gets back unmatched


class TestBustedPlayerVisibility:
    """Tests for busted player visibility bug fix - players with stack=0 should stay until next hand."""

    def test_busted_players_remain_after_showdown(self):
        """Test that players with stack=0 remain at table after showdown ends."""
        from app.core.models import PlayerRole

        table = TableState(table_id="test-table")
        table.players = {
            "p1": Player(pid="p1", name="Alice", stack=1000, seat=1, connected=True, role=PlayerRole.SEATED),
            "p2": Player(pid="p2", name="Bob", stack=0, seat=2, connected=True, role=PlayerRole.SEATED),
        }
        table.hand_in_progress = True
        table.pot = 100
        table.board = ["2h", "3d", "4c", "5s", "9h"]
        table.hole_cards = {
            "p1": ["Ah", "Kh"],
            "p2": ["7s", "8s"],
        }

        # Run showdown (p1 wins)
        run_showdown(table)

        # p2 should still be SEATED with stack=0 after showdown
        assert table.players["p2"].role == PlayerRole.SEATED
        assert table.players["p2"].seat == 2
        assert table.players["p2"].stack == 0

    def test_busted_players_converted_on_next_hand_start(self):
        """Test that busted players are converted to spectators when next hand starts."""
        from app.core.models import PlayerRole

        table = TableState(table_id="test-table")
        table.players = {
            "p1": Player(pid="p1", name="Alice", stack=1000, seat=1, connected=True, role=PlayerRole.SEATED),
            "p2": Player(pid="p2", name="Bob", stack=0, seat=2, connected=True, role=PlayerRole.SEATED),
            "p3": Player(pid="p3", name="Charlie", stack=500, seat=3, connected=True, role=PlayerRole.SEATED),
        }
        table.hand_in_progress = False

        # Start a new hand
        start_new_hand(table)

        # p2 should now be a spectator (busted)
        assert table.players["p2"].role == PlayerRole.SPECTATOR
        assert table.players["p2"].seat == 0
        assert "p2" in table.spectator_pids

        # p1 and p3 should still be seated
        assert table.players["p1"].role == PlayerRole.SEATED
        assert table.players["p3"].role == PlayerRole.SEATED

    def test_multiple_busted_players_converted_together(self):
        """Test that multiple busted players are all converted when next hand starts."""
        from app.core.models import PlayerRole

        table = TableState(table_id="test-table")
        table.players = {
            "p1": Player(pid="p1", name="Alice", stack=2000, seat=1, connected=True, role=PlayerRole.SEATED),
            "p2": Player(pid="p2", name="Bob", stack=0, seat=2, connected=True, role=PlayerRole.SEATED),
            "p3": Player(pid="p3", name="Charlie", stack=0, seat=3, connected=True, role=PlayerRole.SEATED),
            "p4": Player(pid="p4", name="David", stack=500, seat=4, connected=True, role=PlayerRole.SEATED),
        }
        table.hand_in_progress = False

        # Start a new hand
        start_new_hand(table)

        # p2 and p3 should be spectators
        assert table.players["p2"].role == PlayerRole.SPECTATOR
        assert table.players["p3"].role == PlayerRole.SPECTATOR
        assert "p2" in table.spectator_pids
        assert "p3" in table.spectator_pids

        # p1 and p4 should still be seated
        assert table.players["p1"].role == PlayerRole.SEATED
        assert table.players["p4"].role == PlayerRole.SEATED

    def test_showdown_data_includes_busted_player_cards(self):
        """Test that showdown data includes cards from players who busted."""
        from app.core.models import PlayerRole

        table = TableState(table_id="test-table")
        table.players = {
            "p1": Player(pid="p1", name="Alice", stack=1000, seat=1, connected=True, role=PlayerRole.SEATED),
            "p2": Player(pid="p2", name="Bob", stack=0, seat=2, connected=True, role=PlayerRole.SEATED),
        }
        table.hand_in_progress = True
        table.pot = 100
        table.board = ["2h", "3d", "4c", "5s", "9h"]
        table.hole_cards = {
            "p1": ["Ah", "Kh"],
            "p2": ["7s", "8s"],
        }

        # Run showdown
        run_showdown(table)

        # Showdown data should include both players
        assert table.showdown_data is not None
        assert "p1" in table.showdown_data["players"]
        assert "p2" in table.showdown_data["players"]
        assert table.showdown_data["players"]["p2"]["hole_cards"] == ["7s", "8s"]


class TestSidePotMessaging:
    """Tests for side pot result messages and display."""

    def test_single_winner_message_shows_profit(self):
        """Test that single winner message shows total won and profit."""
        from app.core.models import PlayerRole

        table = TableState(table_id="test")
        table.players = {
            "p1": Player(pid="p1", name="Alice", stack=0, seat=1, connected=True, role=PlayerRole.SEATED),
            "p2": Player(pid="p2", name="Bob", stack=0, seat=2, connected=True, role=PlayerRole.SEATED),
        }
        table.hand_in_progress = True
        table.pot = 2000
        table.board = ["Kh", "Qd", "Jc", "2s", "3h"]
        table.hole_cards = {
            "p1": ["7h", "8c"],  # High card - loses
            "p2": ["Th", "Tc"],  # Pair - wins
        }
        table.player_bets = {"p1": 1000, "p2": 1000}

        result = run_showdown(table)

        # Message should show total won and profit
        assert "Bob wins $2000" in result
        assert "$1000 profit" in result
        assert table.players["p2"].stack == 2000

    def test_three_player_side_pot_message(self):
        """Test message formatting with 3 players and side pots."""
        from app.core.models import PlayerRole

        table = TableState(table_id="test")
        table.players = {
            "p1": Player(pid="p1", name="Alice", stack=0, seat=1, connected=True, role=PlayerRole.SEATED),
            "p2": Player(pid="p2", name="Bob", stack=0, seat=2, connected=True, role=PlayerRole.SEATED),
            "p3": Player(pid="p3", name="Charlie", stack=0, seat=3, connected=True, role=PlayerRole.SEATED),
        }
        table.hand_in_progress = True
        table.pot = 3020
        table.board = ["Kh", "Qd", "Jc", "2s", "3h"]
        table.hole_cards = {
            "p1": ["7h", "8c"],  # High card
            "p2": ["Th", "Tc"],  # Pair of tens - WINS
            "p3": ["9h", "9s"],  # Pair of nines
        }
        table.player_bets = {"p1": 980, "p2": 1060, "p3": 980}

        result = run_showdown(table)

        # Should show side pot breakdown
        assert "Bob wins" in result
        assert "Main Pot:" in result
        assert "Side Pot" in result
        assert "$2940" in result  # Main pot amount
        assert "$80" in result    # Side pot amount

        # Verify actual payouts
        assert table.players["p2"].stack == 3020  # Bob wins all
        assert table.players["p1"].stack == 0
        assert table.players["p3"].stack == 0

    def test_split_pot_message_shows_profit(self):
        """Test split pot message shows winnings and profit for each winner."""
        from app.core.models import PlayerRole

        table = TableState(table_id="test")
        table.players = {
            "p1": Player(pid="p1", name="Alice", stack=0, seat=1, connected=True, role=PlayerRole.SEATED),
            "p2": Player(pid="p2", name="Bob", stack=0, seat=2, connected=True, role=PlayerRole.SEATED),
        }
        table.hand_in_progress = True
        table.pot = 2000
        table.board = ["Kh", "Qd", "Jc", "2s", "3h"]
        table.hole_cards = {
            "p1": ["Th", "Tc"],  # Pair of tens
            "p2": ["Td", "Ts"],  # Pair of tens - TIE
        }
        table.player_bets = {"p1": 1000, "p2": 1000}

        result = run_showdown(table)

        # Should show split pot with profits
        assert "Split pot:" in result
        assert "Alice" in result
        assert "Bob" in result
        # Each gets 1000, profit is 0
        assert "+$0" in result

    def test_side_pot_breakdown_in_showdown_data(self):
        """Test that side pot breakdown is included in showdown_data."""
        from app.core.models import PlayerRole

        table = TableState(table_id="test")
        table.players = {
            "p1": Player(pid="p1", name="Alice", stack=0, seat=1, connected=True, role=PlayerRole.SEATED),
            "p2": Player(pid="p2", name="Bob", stack=0, seat=2, connected=True, role=PlayerRole.SEATED),
            "p3": Player(pid="p3", name="Charlie", stack=0, seat=3, connected=True, role=PlayerRole.SEATED),
        }
        table.hand_in_progress = True
        table.pot = 1800
        table.board = ["Kh", "Qd", "Jc", "2s", "3h"]
        table.hole_cards = {
            "p1": ["7h", "8c"],
            "p2": ["Th", "Tc"],
            "p3": ["9h", "9s"],
        }
        table.player_bets = {"p1": 1000, "p2": 500, "p3": 300}

        run_showdown(table)

        # Check showdown_data contains side pot info
        assert table.showdown_data is not None
        assert "side_pots" in table.showdown_data
        side_pots = table.showdown_data["side_pots"]
        assert side_pots is not None
        assert len(side_pots) == 3  # Main pot + 2 side pots

        # Verify pot structure
        assert side_pots[0]["type"] == "Main Pot"
        assert side_pots[0]["amount"] == 900
        assert side_pots[1]["type"] == "Side Pot 1"
        assert side_pots[1]["amount"] == 400
        assert side_pots[2]["type"] == "Side Pot 2"
        assert side_pots[2]["amount"] == 500


class TestAllInCallHandling:
    """Tests for all-in call scenarios."""

    def test_short_stack_call_creates_correct_side_pots(self):
        """Test that calling with insufficient stack creates proper side pots."""
        from app.core.models import PlayerRole

        table = TableState(table_id="test")
        table.players = {
            "p1": Player(pid="p1", name="Alice", stack=0, seat=1, connected=True, role=PlayerRole.SEATED),
            "p2": Player(pid="p2", name="Bob", stack=0, seat=2, connected=True, role=PlayerRole.SEATED),
        }
        table.hand_in_progress = True
        table.pot = 1500
        table.board = ["Kh", "Qd", "Jc", "2s", "3h"]
        table.hole_cards = {
            "p1": ["As", "Ah"],  # Pair of aces - WINS
            "p2": ["7h", "8c"],
        }
        # Alice bet 1000, Bob could only match 500
        table.player_bets = {"p1": 1000, "p2": 500}

        result = run_showdown(table)

        # Alice should win 1000 (main pot) and get 500 back
        assert table.players["p1"].stack == 1500
        assert table.players["p2"].stack == 0

        # Message should show breakdown
        assert "Alice wins" in result
        assert "$500 profit" in result

    def test_multiple_short_stacks_all_in(self):
        """Test complex scenario with multiple short stacks."""
        from app.core.models import PlayerRole

        table = TableState(table_id="test")
        table.players = {
            "p1": Player(pid="p1", name="Alice", stack=0, seat=1, connected=True, role=PlayerRole.SEATED),
            "p2": Player(pid="p2", name="Bob", stack=0, seat=2, connected=True, role=PlayerRole.SEATED),
            "p3": Player(pid="p3", name="Charlie", stack=0, seat=3, connected=True, role=PlayerRole.SEATED),
            "p4": Player(pid="p4", name="Dana", stack=0, seat=4, connected=True, role=PlayerRole.SEATED),
        }
        table.hand_in_progress = True
        table.pot = 2500
        table.board = ["Kh", "Qd", "Jc", "2s", "3h"]
        table.hole_cards = {
            "p1": ["7h", "8c"],  # High card
            "p2": ["9h", "9s"],  # Pair of 9s - second best
            "p3": ["Th", "Tc"],  # Pair of tens - BEST
            "p4": ["6h", "6s"],  # Pair of 6s
        }
        # Different stack sizes: 1000, 800, 500, 200
        table.player_bets = {"p1": 1000, "p2": 800, "p3": 500, "p4": 200}

        run_showdown(table)

        # Charlie (p3) should win from everyone they were eligible against
        # Main pot (200*4=800): Charlie wins (best hand)
        # Side pot 1 (300*3=900): Charlie wins (best hand)
        # Side pot 2 (300*2=600): Bob wins (Charlie not eligible! Bob beats Alice)
        # Side pot 3 (200*1=200): Alice gets back (only eligible)
        assert table.players["p3"].stack == 1700  # 800+900 (wins pots 1&2)
        assert table.players["p2"].stack == 600   # Wins pot 3
        assert table.players["p1"].stack == 200   # Gets back uncalled
        assert table.players["p4"].stack == 0
