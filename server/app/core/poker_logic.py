"""
Poker hand evaluation and comparison logic.
"""
from typing import List
from collections import Counter
from .constants import HAND_RANKS
from .card_utils import rank_value


def evaluate_hand(cards: List[str]) -> tuple:
    """
    Evaluates a poker hand and returns (hand_rank, tiebreakers).
    Works with 2-7 cards, finds best 5-card hand.
    Returns tuple of (hand_rank_number, [tiebreaker_values]) where lower is better.
    """
    if not cards:
        return (HAND_RANKS["high_card"], [0])

    # Parse cards
    ranks = [c[0] for c in cards]
    suits = [c[1] for c in cards]
    rank_values = sorted([rank_value(r) for r in ranks], reverse=True)

    # Count rank frequencies
    rank_counts = Counter(rank_values)
    counts = sorted(rank_counts.values(), reverse=True)
    unique_ranks = sorted(rank_counts.keys(), reverse=True)

    # Check for flush
    suit_counts = Counter(suits)
    is_flush = max(suit_counts.values()) >= 5 if len(cards) >= 5 else len(set(suits)) == 1

    # Check for straight
    is_straight, straight_high = _check_straight(unique_ranks)

    # Determine hand ranking
    if is_straight and is_flush:
        if straight_high == 14:
            return (HAND_RANKS["royal_flush"], [14])
        return (HAND_RANKS["straight_flush"], [straight_high])

    if counts[0] == 4:
        four_kind = [k for k, v in rank_counts.items() if v == 4][0]
        kicker = [k for k in unique_ranks if k != four_kind][0] if len(unique_ranks) > 1 else 0
        return (HAND_RANKS["four_of_a_kind"], [four_kind, kicker])

    if counts[0] == 3 and (len(counts) > 1 and counts[1] >= 2):
        trips = [k for k, v in rank_counts.items() if v == 3][0]
        pair = [k for k, v in rank_counts.items() if v >= 2 and k != trips][0]
        return (HAND_RANKS["full_house"], [trips, pair])

    if is_flush:
        return (HAND_RANKS["flush"], rank_values[:5])

    if is_straight:
        return (HAND_RANKS["straight"], [straight_high])

    if counts[0] == 3:
        trips = [k for k, v in rank_counts.items() if v == 3][0]
        kickers = sorted([k for k in unique_ranks if k != trips], reverse=True)[:2]
        return (HAND_RANKS["three_of_a_kind"], [trips] + kickers)

    if counts[0] == 2 and (len(counts) > 1 and counts[1] == 2):
        pairs = sorted([k for k, v in rank_counts.items() if v == 2], reverse=True)[:2]
        kickers = [k for k in unique_ranks if k not in pairs]
        kicker = kickers[0] if kickers else 0
        return (HAND_RANKS["two_pair"], pairs + [kicker])

    if counts[0] == 2:
        pair = [k for k, v in rank_counts.items() if v == 2][0]
        kickers = sorted([k for k in unique_ranks if k != pair], reverse=True)[:3]
        return (HAND_RANKS["pair"], [pair] + kickers)

    # High card
    return (HAND_RANKS["high_card"], rank_values[:5])


def _check_straight(unique_ranks: List[int]) -> tuple[bool, int]:
    """Check if ranks form a straight. Returns (is_straight, high_card)."""
    if len(unique_ranks) < 5:
        return False, 0

    # Check for normal straights
    for i in range(len(unique_ranks) - 4):
        if unique_ranks[i] - unique_ranks[i+4] == 4:
            return True, unique_ranks[i]

    # Check for A-2-3-4-5 (wheel)
    if 14 in unique_ranks and set([2,3,4,5]).issubset(unique_ranks):
        return True, 5  # In wheel, 5 is high card

    return False, 0


def compare_hands(hand1: tuple, hand2: tuple) -> int:
    """
    Compares two hand evaluations.
    Returns: -1 if hand1 wins, 1 if hand2 wins, 0 if tie.
    """
    rank1, tiebreakers1 = hand1
    rank2, tiebreakers2 = hand2

    if rank1 < rank2:
        return -1
    if rank1 > rank2:
        return 1

    # Same rank, compare tiebreakers
    for t1, t2 in zip(tiebreakers1, tiebreakers2):
        if t1 > t2:
            return -1
        if t1 < t2:
            return 1

    return 0  # Exact tie


def hand_name(hand_eval: tuple) -> str:
    """Returns human-readable name for a hand evaluation."""
    rank_num, tiebreakers = hand_eval
    rank_names = {v: k for k, v in HAND_RANKS.items()}
    name = rank_names.get(rank_num, "unknown")
    return name.replace("_", " ").title()
