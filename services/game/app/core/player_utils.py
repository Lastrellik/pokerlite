"""
Player utility functions for poker.
"""
from typing import List
from .models import TableState, Player, PlayerRole


def connected_players(table: TableState) -> List[Player]:
    """Get all connected SEATED players sorted by seat."""
    return [
        p for p in sorted(table.players.values(), key=lambda x: x.seat)
        if p.connected and p.role == PlayerRole.SEATED
    ]


def eligible_players(table: TableState) -> List[Player]:
    """Get connected seated players with chips to play (stack > 0)."""
    return [
        p for p in connected_players(table)
        if p.stack > 0
    ]


def connected_pids(table: TableState) -> List[str]:
    """Get PIDs of connected seated players."""
    return [p.pid for p in connected_players(table)]


def active_players(table: TableState) -> List[Player]:
    """Get connected seated players who haven't folded."""
    return [
        p for p in connected_players(table)
        if p.pid not in table.folded_pids
    ]


def active_pids(table: TableState) -> List[str]:
    """Get PIDs of active (connected, seated, not folded) players."""
    return [p.pid for p in active_players(table)]


def get_player_seat(table: TableState, pid: str) -> int:
    """Get the seat number for a player."""
    player = table.players.get(pid)
    return player.seat if player else 0


def find_next_seat(seats: List[int], current_seat: int) -> int:
    """Find the next seat in circular order."""
    if not seats:
        return 0
    try:
        idx = seats.index(current_seat)
        return seats[(idx + 1) % len(seats)]
    except ValueError:
        return seats[0]
