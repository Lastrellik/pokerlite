"""Shared TableConfig model for table metadata and settings."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class TableConfig:
    """Table metadata and settings (NOT runtime game state)."""
    table_id: str
    name: str
    small_blind: int = 5
    big_blind: int = 10
    max_players: int = 8
    turn_timeout_seconds: int = 30
    created_at: Optional[str] = None  # ISO timestamp

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "table_id": self.table_id,
            "name": self.name,
            "small_blind": self.small_blind,
            "big_blind": self.big_blind,
            "max_players": self.max_players,
            "turn_timeout_seconds": self.turn_timeout_seconds,
            "created_at": self.created_at,
        }
