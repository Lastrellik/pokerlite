"""
Waitlist management for poker tables.
"""
from .models import TableState, Player, PlayerRole
from .constants import MAX_PLAYERS, DEFAULT_STARTING_STACK


def join_waitlist(table: TableState, pid: str) -> bool:
    """
    Add a spectator to the waitlist.
    Returns True if added, False if already on waitlist or seated.
    """
    if pid in table.waitlist:
        return False

    player = table.players.get(pid)
    if not player:
        return False

    if player.role == PlayerRole.SEATED:
        return False

    table.waitlist.append(pid)
    player.role = PlayerRole.WAITLIST
    table.spectator_pids.discard(pid)
    return True


def leave_waitlist(table: TableState, pid: str) -> bool:
    """
    Remove a player from the waitlist, return them to spectator.
    Returns True if removed, False if not on waitlist.
    """
    if pid not in table.waitlist:
        return False

    table.waitlist.remove(pid)
    player = table.players.get(pid)
    if player:
        player.role = PlayerRole.SPECTATOR
        table.spectator_pids.add(pid)
    return True


def promote_from_waitlist(table: TableState) -> str | None:
    """
    Promote the first waitlisted player to a seat.
    Only call between hands when seats are available.
    Returns the promoted player's PID or None.
    """
    if table.hand_in_progress:
        return None

    seated_count = sum(
        1 for p in table.players.values()
        if p.role == PlayerRole.SEATED and p.connected
    )

    if seated_count >= MAX_PLAYERS:
        return None

    while table.waitlist:
        pid = table.waitlist.pop(0)
        player = table.players.get(pid)

        if not player or not player.connected:
            continue

        # Assign seat
        used_seats = {p.seat for p in table.players.values() if p.role == PlayerRole.SEATED}
        seat = 1
        while seat in used_seats:
            seat += 1

        player.seat = seat
        player.role = PlayerRole.SEATED
        player.stack = DEFAULT_STARTING_STACK
        return pid

    return None


def get_waitlist_position(table: TableState, pid: str) -> int:
    """
    Get a player's position in the waitlist (1-indexed).
    Returns 0 if not on waitlist.
    """
    try:
        return table.waitlist.index(pid) + 1
    except ValueError:
        return 0
