"""Shared Player model used by both lobby and game services."""
from dataclasses import dataclass
from enum import Enum


class PlayerRole(str, Enum):
    """Player role in the game."""
    SEATED = "seated"
    SPECTATOR = "spectator"
    WAITLIST = "waitlist"


@dataclass
class Player:
    """Player model - shared between lobby and game services."""
    pid: str
    name: str
    stack: int = 1000
    seat: int = 0
    connected: bool = True
    role: PlayerRole = PlayerRole.SEATED
