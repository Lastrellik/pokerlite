"""
Card utility functions for poker.
"""
import random
from typing import List
from poker.constants import RANKS, SUITS


def new_deck() -> List[str]:
    """Create a new deck of 52 cards."""
    return [r + s for r in RANKS for s in SUITS]


def shuffle_deck() -> List[str]:
    """Create and shuffle a new deck."""
    deck = new_deck()
    random.shuffle(deck)
    return deck


def rank_value(rank: str) -> int:
    """Convert rank character to numeric value (2=2, T=10, A=14)."""
    return RANKS.index(rank) + 2


def parse_card(card: str) -> tuple[str, str]:
    """Parse a card into (rank, suit)."""
    return card[0], card[1]
