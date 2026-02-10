"""Authentication utilities for game service."""
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from db import verify_token, get_db, User, PlayerStack


def validate_token_and_load_user(token: str) -> Optional[Tuple[User, int]]:
    """
    Validate JWT token and load user with their stack.

    Args:
        token: JWT token string

    Returns:
        Tuple of (User, stack) if valid, None if invalid

    Example:
        user_data = validate_token_and_load_user(token)
        if user_data:
            user, stack = user_data
            print(f"User {user.username} has {stack} chips")
    """
    # Verify token
    payload = verify_token(token)
    if payload is None:
        return None

    # Get username from token
    username = payload.get("sub")
    if username is None:
        return None

    # Get database session
    db = next(get_db())
    try:
        # Load user
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            return None

        # Load user's stack (or create default if doesn't exist)
        player_stack = db.query(PlayerStack).filter(PlayerStack.user_id == user.id).first()
        if player_stack is None:
            # Create default stack if user doesn't have one
            player_stack = PlayerStack(user_id=user.id, stack=1000)
            db.add(player_stack)
            db.commit()
            db.refresh(player_stack)

        return (user, player_stack.stack)
    finally:
        db.close()


def update_user_stack(user_id: int, new_stack: int) -> bool:
    """
    Update user's stack in the database.

    Args:
        user_id: User's database ID
        new_stack: New chip count

    Returns:
        True if successful, False otherwise
    """
    db = next(get_db())
    try:
        player_stack = db.query(PlayerStack).filter(PlayerStack.user_id == user_id).first()
        if player_stack:
            player_stack.stack = new_stack
            db.commit()
            return True
        return False
    except Exception as e:
        print(f"[AUTH] Error updating stack: {e}")
        db.rollback()
        return False
    finally:
        db.close()
