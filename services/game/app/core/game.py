"""
Main game module - exports all game functionality.
Refactored for clean separation of concerns.
"""

# Re-export all public functions for backward compatibility
from poker.constants import *
from poker.card_utils import *
from .player_utils import *
from poker.poker_logic import (
    evaluate_hand as _evaluate_hand,
    compare_hands as _compare_hands,
    hand_name as _hand_name,
)
from .betting import *
from .game_flow import *
from .actions import handle_message, handle_disconnect

# Expose with private naming for test compatibility
__all__ = [
    'handle_message',
    'handle_disconnect',
    '_evaluate_hand',
    '_compare_hands',
    '_hand_name',
]
