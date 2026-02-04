"""
Comprehensive tests for poker hand evaluation and comparison logic.
"""
import pytest
from poker.poker_logic import (
    evaluate_hand,
    evaluate_hand_with_cards,
    compare_hands,
    hand_name,
    get_key_cards,
    _check_straight
)
from poker.constants import HAND_RANKS


class TestEvaluateHand:
    """Tests for evaluate_hand function."""

    # Royal Flush
    def test_royal_flush(self):
        cards = ["As", "Ks", "Qs", "Js", "Ts"]
        rank, tiebreakers = evaluate_hand(cards)
        assert rank == HAND_RANKS["royal_flush"]
        assert tiebreakers == [14]

    def test_royal_flush_hearts(self):
        cards = ["Ah", "Kh", "Qh", "Jh", "Th"]
        rank, _ = evaluate_hand(cards)
        assert rank == HAND_RANKS["royal_flush"]

    # Straight Flush
    def test_straight_flush(self):
        cards = ["9h", "8h", "7h", "6h", "5h"]
        rank, tiebreakers = evaluate_hand(cards)
        assert rank == HAND_RANKS["straight_flush"]
        assert tiebreakers == [9]

    def test_straight_flush_low(self):
        """Test A-2-3-4-5 suited (steel wheel)."""
        cards = ["Ac", "2c", "3c", "4c", "5c"]
        rank, tiebreakers = evaluate_hand(cards)
        assert rank == HAND_RANKS["straight_flush"]
        assert tiebreakers == [5]  # 5 is the high card in wheel

    # Four of a Kind
    def test_four_of_a_kind(self):
        cards = ["Kh", "Ks", "Kd", "Kc", "2h"]
        rank, tiebreakers = evaluate_hand(cards)
        assert rank == HAND_RANKS["four_of_a_kind"]
        assert tiebreakers[0] == 13  # Kings
        assert tiebreakers[1] == 2   # Kicker

    def test_four_of_a_kind_aces(self):
        cards = ["Ah", "As", "Ad", "Ac", "Ks"]
        rank, tiebreakers = evaluate_hand(cards)
        assert rank == HAND_RANKS["four_of_a_kind"]
        assert tiebreakers[0] == 14  # Aces

    # Full House
    def test_full_house(self):
        cards = ["Qh", "Qs", "Qd", "7c", "7h"]
        rank, tiebreakers = evaluate_hand(cards)
        assert rank == HAND_RANKS["full_house"]
        assert tiebreakers == [12, 7]  # Queens full of sevens

    def test_full_house_aces_over_kings(self):
        cards = ["Ah", "As", "Ad", "Kc", "Kh"]
        rank, tiebreakers = evaluate_hand(cards)
        assert rank == HAND_RANKS["full_house"]
        assert tiebreakers == [14, 13]

    # Flush
    def test_flush(self):
        cards = ["Kd", "Jd", "9d", "6d", "3d"]
        rank, tiebreakers = evaluate_hand(cards)
        assert rank == HAND_RANKS["flush"]
        assert tiebreakers == [13, 11, 9, 6, 3]

    def test_flush_ace_high(self):
        cards = ["Ad", "Qd", "Td", "7d", "2d"]
        rank, tiebreakers = evaluate_hand(cards)
        assert rank == HAND_RANKS["flush"]
        assert tiebreakers[0] == 14

    # Straight
    def test_straight(self):
        cards = ["Ts", "9h", "8d", "7c", "6s"]
        rank, tiebreakers = evaluate_hand(cards)
        assert rank == HAND_RANKS["straight"]
        assert tiebreakers == [10]

    def test_straight_ace_high(self):
        cards = ["As", "Kh", "Qd", "Jc", "Ts"]
        rank, tiebreakers = evaluate_hand(cards)
        assert rank == HAND_RANKS["straight"]
        assert tiebreakers == [14]

    def test_straight_wheel(self):
        """Test A-2-3-4-5 straight (wheel)."""
        cards = ["Ah", "2s", "3d", "4c", "5h"]
        rank, tiebreakers = evaluate_hand(cards)
        assert rank == HAND_RANKS["straight"]
        assert tiebreakers == [5]

    # Three of a Kind
    def test_three_of_a_kind(self):
        cards = ["8h", "8s", "8d", "Kc", "3h"]
        rank, tiebreakers = evaluate_hand(cards)
        assert rank == HAND_RANKS["three_of_a_kind"]
        assert tiebreakers[0] == 8
        assert 13 in tiebreakers  # King kicker

    # Two Pair
    def test_two_pair(self):
        cards = ["Jh", "Js", "5d", "5c", "Ah"]
        rank, tiebreakers = evaluate_hand(cards)
        assert rank == HAND_RANKS["two_pair"]
        assert tiebreakers == [11, 5, 14]  # Jacks, fives, ace kicker

    def test_two_pair_kings_and_queens(self):
        cards = ["Kh", "Ks", "Qd", "Qc", "2h"]
        rank, tiebreakers = evaluate_hand(cards)
        assert rank == HAND_RANKS["two_pair"]
        assert tiebreakers == [13, 12, 2]

    # Pair
    def test_pair(self):
        cards = ["9h", "9s", "Kd", "7c", "3h"]
        rank, tiebreakers = evaluate_hand(cards)
        assert rank == HAND_RANKS["pair"]
        assert tiebreakers[0] == 9

    def test_pair_aces(self):
        cards = ["Ah", "As", "Kd", "Qc", "Jh"]
        rank, tiebreakers = evaluate_hand(cards)
        assert rank == HAND_RANKS["pair"]
        assert tiebreakers == [14, 13, 12, 11]

    # High Card
    def test_high_card(self):
        cards = ["Ah", "Ks", "9d", "7c", "3h"]
        rank, tiebreakers = evaluate_hand(cards)
        assert rank == HAND_RANKS["high_card"]
        assert tiebreakers == [14, 13, 9, 7, 3]

    def test_high_card_king_high(self):
        cards = ["Kh", "Qs", "Td", "8c", "2h"]
        rank, tiebreakers = evaluate_hand(cards)
        assert rank == HAND_RANKS["high_card"]
        assert tiebreakers[0] == 13

    # Edge Cases
    def test_empty_hand(self):
        rank, tiebreakers = evaluate_hand([])
        assert rank == HAND_RANKS["high_card"]

    def test_two_cards(self):
        cards = ["Ah", "Ks"]  # Different suits - not a flush
        rank, _ = evaluate_hand(cards)
        assert rank == HAND_RANKS["high_card"]

    def test_seven_cards_finds_best(self):
        """With 7 cards, should find the best 5-card hand."""
        cards = ["Ah", "Kh", "Qh", "Jh", "Th", "2c", "3d"]
        rank, _ = evaluate_hand(cards)
        # Has a flush, not just high cards
        assert rank == HAND_RANKS["royal_flush"]


class TestEvaluateHandWithCards:
    """Tests for evaluate_hand_with_cards function."""

    def test_returns_best_five(self):
        cards = ["Ah", "Kh", "Qh", "Jh", "Th", "2c", "3d"]
        rank, tiebreakers, best_cards = evaluate_hand_with_cards(cards)
        assert rank == HAND_RANKS["royal_flush"]
        assert len(best_cards) == 5

    def test_five_cards_returns_same(self):
        cards = ["Ah", "Ks", "Qd", "Jc", "9h"]
        rank, tiebreakers, best_cards = evaluate_hand_with_cards(cards)
        assert best_cards == cards

    def test_finds_hidden_straight(self):
        """Should find straight among 7 cards."""
        cards = ["9h", "8s", "7d", "6c", "5h", "Ac", "Kd"]
        rank, _, best_cards = evaluate_hand_with_cards(cards)
        assert rank == HAND_RANKS["straight"]


class TestCheckStraight:
    """Tests for _check_straight helper function."""

    def test_normal_straight(self):
        is_straight, high = _check_straight([10, 9, 8, 7, 6])
        assert is_straight is True
        assert high == 10

    def test_wheel_straight(self):
        is_straight, high = _check_straight([14, 5, 4, 3, 2])
        assert is_straight is True
        assert high == 5

    def test_not_straight(self):
        is_straight, _ = _check_straight([14, 13, 11, 10, 9])
        assert is_straight is False

    def test_too_few_cards(self):
        is_straight, _ = _check_straight([14, 13, 12])
        assert is_straight is False


class TestCompareHands:
    """Tests for compare_hands function."""

    def test_higher_rank_wins(self):
        flush = (HAND_RANKS["flush"], [13, 11, 9, 6, 3])
        straight = (HAND_RANKS["straight"], [10])
        assert compare_hands(flush, straight) == -1

    def test_lower_rank_loses(self):
        pair = (HAND_RANKS["pair"], [9, 13, 7, 3])
        two_pair = (HAND_RANKS["two_pair"], [11, 5, 14])
        assert compare_hands(pair, two_pair) == 1

    def test_same_rank_higher_tiebreaker_wins(self):
        pair_kings = (HAND_RANKS["pair"], [13, 10, 8, 5])
        pair_queens = (HAND_RANKS["pair"], [12, 10, 8, 5])
        assert compare_hands(pair_kings, pair_queens) == -1

    def test_same_rank_lower_tiebreaker_loses(self):
        pair_queens = (HAND_RANKS["pair"], [12, 10, 8, 5])
        pair_kings = (HAND_RANKS["pair"], [13, 10, 8, 5])
        assert compare_hands(pair_queens, pair_kings) == 1

    def test_exact_tie(self):
        hand1 = (HAND_RANKS["pair"], [9, 13, 7, 3])
        hand2 = (HAND_RANKS["pair"], [9, 13, 7, 3])
        assert compare_hands(hand1, hand2) == 0

    def test_kicker_matters(self):
        pair_with_ace = (HAND_RANKS["pair"], [9, 14, 7, 3])
        pair_with_king = (HAND_RANKS["pair"], [9, 13, 7, 3])
        assert compare_hands(pair_with_ace, pair_with_king) == -1


class TestHandName:
    """Tests for hand_name function."""

    def test_royal_flush_name(self):
        assert hand_name((HAND_RANKS["royal_flush"], [14])) == "Royal Flush"

    def test_straight_flush_name(self):
        assert hand_name((HAND_RANKS["straight_flush"], [9])) == "Straight Flush"

    def test_four_of_a_kind_name(self):
        assert hand_name((HAND_RANKS["four_of_a_kind"], [13, 2])) == "Four Of A Kind"

    def test_full_house_name(self):
        assert hand_name((HAND_RANKS["full_house"], [12, 7])) == "Full House"

    def test_flush_name(self):
        assert hand_name((HAND_RANKS["flush"], [13, 11, 9, 6, 3])) == "Flush"

    def test_straight_name(self):
        assert hand_name((HAND_RANKS["straight"], [10])) == "Straight"

    def test_three_of_a_kind_name(self):
        assert hand_name((HAND_RANKS["three_of_a_kind"], [8, 13, 3])) == "Three Of A Kind"

    def test_two_pair_name(self):
        assert hand_name((HAND_RANKS["two_pair"], [11, 5, 14])) == "Two Pair"

    def test_pair_name(self):
        assert hand_name((HAND_RANKS["pair"], [9, 13, 7, 3])) == "Pair"

    def test_high_card_name(self):
        assert hand_name((HAND_RANKS["high_card"], [14, 13, 9, 7, 3])) == "High Card"


class TestGetKeyCards:
    """Tests for get_key_cards function."""

    def test_pair_returns_two_cards(self):
        cards = ["9h", "9s", "Kd", "7c", "3h"]
        key = get_key_cards(cards, HAND_RANKS["pair"])
        assert len(key) == 2
        assert all("9" in c for c in key)

    def test_two_pair_returns_four_cards(self):
        cards = ["Jh", "Js", "5d", "5c", "Ah"]
        key = get_key_cards(cards, HAND_RANKS["two_pair"])
        assert len(key) == 4

    def test_three_of_a_kind_returns_three_cards(self):
        cards = ["8h", "8s", "8d", "Kc", "3h"]
        key = get_key_cards(cards, HAND_RANKS["three_of_a_kind"])
        assert len(key) == 3
        assert all("8" in c for c in key)

    def test_four_of_a_kind_returns_four_cards(self):
        cards = ["Kh", "Ks", "Kd", "Kc", "2h"]
        key = get_key_cards(cards, HAND_RANKS["four_of_a_kind"])
        assert len(key) == 4
        assert all("K" in c for c in key)

    def test_flush_returns_all_five(self):
        cards = ["Kd", "Jd", "9d", "6d", "3d"]
        key = get_key_cards(cards, HAND_RANKS["flush"])
        assert len(key) == 5
        assert key == cards

    def test_straight_returns_all_five(self):
        cards = ["Ts", "9h", "8d", "7c", "6s"]
        key = get_key_cards(cards, HAND_RANKS["straight"])
        assert len(key) == 5

    def test_full_house_returns_all_five(self):
        cards = ["Qh", "Qs", "Qd", "7c", "7h"]
        key = get_key_cards(cards, HAND_RANKS["full_house"])
        assert len(key) == 5

    def test_high_card_returns_one(self):
        cards = ["Ah", "Ks", "9d", "7c", "3h"]
        key = get_key_cards(cards, HAND_RANKS["high_card"])
        assert len(key) == 1
        assert "A" in key[0]

    def test_single_card(self):
        cards = ["Ah"]
        key = get_key_cards(cards, HAND_RANKS["high_card"])
        assert key == cards


class TestHandRankings:
    """Integration tests verifying correct hand ranking order."""

    def test_royal_flush_beats_straight_flush(self):
        royal = evaluate_hand(["As", "Ks", "Qs", "Js", "Ts"])
        straight_flush = evaluate_hand(["Kh", "Qh", "Jh", "Th", "9h"])
        assert compare_hands(royal, straight_flush) == -1

    def test_straight_flush_beats_four_of_a_kind(self):
        sf = evaluate_hand(["9h", "8h", "7h", "6h", "5h"])
        quads = evaluate_hand(["Ah", "As", "Ad", "Ac", "Ks"])
        assert compare_hands(sf, quads) == -1

    def test_four_of_a_kind_beats_full_house(self):
        quads = evaluate_hand(["Kh", "Ks", "Kd", "Kc", "2h"])
        full = evaluate_hand(["Ah", "As", "Ad", "Qc", "Qh"])
        assert compare_hands(quads, full) == -1

    def test_full_house_beats_flush(self):
        full = evaluate_hand(["Qh", "Qs", "Qd", "7c", "7h"])
        flush = evaluate_hand(["Ad", "Kd", "Qd", "Jd", "9d"])
        assert compare_hands(full, flush) == -1

    def test_flush_beats_straight(self):
        flush = evaluate_hand(["Kd", "Jd", "9d", "6d", "3d"])
        straight = evaluate_hand(["As", "Kh", "Qd", "Jc", "Ts"])
        assert compare_hands(flush, straight) == -1

    def test_straight_beats_three_of_a_kind(self):
        straight = evaluate_hand(["Ts", "9h", "8d", "7c", "6s"])
        trips = evaluate_hand(["Ah", "As", "Ad", "Kc", "Qh"])
        assert compare_hands(straight, trips) == -1

    def test_three_of_a_kind_beats_two_pair(self):
        trips = evaluate_hand(["8h", "8s", "8d", "Kc", "3h"])
        two_pair = evaluate_hand(["Ah", "As", "Kd", "Kc", "Qh"])
        assert compare_hands(trips, two_pair) == -1

    def test_two_pair_beats_pair(self):
        two_pair = evaluate_hand(["Jh", "Js", "5d", "5c", "Ah"])
        pair = evaluate_hand(["Ah", "As", "Kd", "Qc", "Jh"])
        assert compare_hands(two_pair, pair) == -1

    def test_pair_beats_high_card(self):
        pair = evaluate_hand(["2h", "2s", "3d", "4c", "5h"])
        high = evaluate_hand(["Ah", "Ks", "Qd", "Jc", "9h"])
        assert compare_hands(pair, high) == -1
