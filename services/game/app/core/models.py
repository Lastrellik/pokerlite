from dataclasses import dataclass, field
from typing import Dict, List, Optional
import asyncio
from fastapi import WebSocket

# Import from shared module
from models.player import Player, PlayerRole

@dataclass
class TableState:
    table_id: str
    players: Dict[str, Player] = field(default_factory=dict)
    connections: Dict[str, WebSocket] = field(default_factory=dict)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    # Minimal game fields (placeholder engine)
    hand_in_progress: bool = False
    dealer_seat: int = 0
    current_turn_pid: Optional[str] = None
    turn_deadline: Optional[float] = None  # Unix timestamp when turn expires
    pot: int = 0
    board: List[str] = field(default_factory=list)

    # Private per-hand state
    deck: list[str] = field(default_factory=list)
    hole_cards: dict[str, list[str]] = field(default_factory=dict)
    folded_pids: set[str] = field(default_factory=set)
    players_acted: set[str] = field(default_factory=set)  # Track who has acted this round
    street: str = "preflop"  # preflop, flop, turn, river

    # Betting state
    current_bet: int = 0  # Amount needed to call
    player_bets: dict[str, int] = field(default_factory=dict)  # Bets in current round
    total_contributions: dict[str, int] = field(default_factory=dict)  # Total bets throughout entire hand
    small_blind: int = 5
    big_blind: int = 10

    # Table configuration
    max_players: int = 8
    turn_timeout_seconds: int = 30

    # Showdown data (populated after showdown, cleared on new hand)
    showdown_data: Optional[dict] = None

    # Last action taken (for UI animations)
    last_action: Optional[dict] = None  # {pid, action, amount}

    # Runout mode (all players all-in, dealing remaining streets with delays)
    runout_in_progress: bool = False

    # Testing/determinism support
    deck_seed: Optional[int] = None  # If set, use seeded shuffling
    use_deterministic_deck: bool = False  # Enable for testing

    # Player management
    waitlist: list[str] = field(default_factory=list)  # PIDs in FIFO order
    spectator_pids: set[str] = field(default_factory=set)  # PIDs of spectators


    def upsert_player(self, pid: str, name: str, force_spectator: bool = False) -> Player:
        from poker.constants import DEFAULT_STARTING_STACK

        if pid in self.players:
            # Reconnecting player - keep their role
            p = self.players[pid]
            p.connected = True
            p.name = name
            return p

        # New player - determine role
        seated_count = sum(
            1 for p in self.players.values()
            if p.role == PlayerRole.SEATED and p.connected
        )

        if force_spectator or seated_count >= self.max_players or self.hand_in_progress:
            # Add as spectator
            player = Player(
                pid=pid, name=name, seat=0, stack=0,
                role=PlayerRole.SPECTATOR, connected=True
            )
            self.spectator_pids.add(pid)
        else:
            # Seat the player - only count connected players' seats
            used_seats = {p.seat for p in self.players.values() if p.role == PlayerRole.SEATED and p.connected}
            seat = 1
            while seat in used_seats:
                seat += 1
            player = Player(
                pid=pid, name=name, seat=seat, stack=DEFAULT_STARTING_STACK,
                role=PlayerRole.SEATED, connected=True
            )

        self.players[pid] = player
        return player

    def mark_disconnected(self, pid: str) -> None:
        if pid in self.players:
            self.players[pid].connected = False
            # Remove from waitlist if they were waiting
            if pid in self.waitlist:
                self.waitlist.remove(pid)

    def remove_player(self, pid: str) -> None:
        """Completely remove a player from the table."""
        if pid in self.players:
            # Remove from all tracking structures
            self.players.pop(pid, None)
            self.spectator_pids.discard(pid)
            if pid in self.waitlist:
                self.waitlist.remove(pid)

    def is_empty(self) -> bool:
        """Check if table has no players at all."""
        return len(self.players) == 0
