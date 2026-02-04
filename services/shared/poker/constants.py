"""
Game constants for poker.
"""

# Card constants
RANKS = "23456789TJQKA"
SUITS = "shdc"  # spades, hearts, diamonds, clubs

# Valid actions
VALID_ACTIONS = {"fold", "check", "call", "raise", "all_in"}

# Hand rankings (lower number = better hand)
HAND_RANKS = {
    "royal_flush": 1,
    "straight_flush": 2,
    "four_of_a_kind": 3,
    "full_house": 4,
    "flush": 5,
    "straight": 6,
    "three_of_a_kind": 7,
    "two_pair": 8,
    "pair": 9,
    "high_card": 10,
}

# Betting constants
DEFAULT_SMALL_BLIND = 5
DEFAULT_BIG_BLIND = 10
DEFAULT_STARTING_STACK = 1000

# Table limits
MAX_PLAYERS = 8
TURN_TIMEOUT_SECONDS = 30
