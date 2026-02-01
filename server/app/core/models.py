from dataclasses import dataclass, field
from typing import Dict, List, Optional
import asyncio
from fastapi import WebSocket

@dataclass
class Player:
    pid: str
    name: str
    stack: int = 1000
    seat: int = 0
    connected: bool = True

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
    small_blind: int = 5
    big_blind: int = 10

    # Showdown data (populated after showdown, cleared on new hand)
    showdown_data: Optional[dict] = None

    # Last action taken (for UI animations)
    last_action: Optional[dict] = None  # {pid, action, amount}

    # Runout mode (all players all-in, dealing remaining streets with delays)
    runout_in_progress: bool = False


    def upsert_player(self, pid: str, name: str) -> Player:
        if pid not in self.players:
            used_seats = {p.seat for p in self.players.values()}
            seat = 1
            while seat in used_seats:
                seat += 1
            self.players[pid] = Player(pid=pid, name=name, seat=seat, connected=True)
        else:
            p = self.players[pid]
            p.connected = True
            p.name = name
        return self.players[pid]

    def mark_disconnected(self, pid: str) -> None:
        if pid in self.players:
            self.players[pid].connected = False
