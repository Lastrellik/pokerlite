"""Admin routes for managing users and chip balances."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import List, Optional

from db import get_db, User, PlayerStack
from ..dependencies import get_current_admin

router = APIRouter(prefix="/api/admin", tags=["admin"])


class UserAdminResponse(BaseModel):
    """User info for admin listing."""
    id: int
    username: str
    email: Optional[str]
    is_admin: bool
    stack: Optional[int]

    class Config:
        from_attributes = True


class SetStackRequest(BaseModel):
    """Request to set a user's chip stack."""
    stack: int = Field(..., ge=0, le=10_000_000)


@router.get("/users", response_model=List[UserAdminResponse])
def list_users(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """List all users with their current chip stacks."""
    users = db.query(User).order_by(User.username).all()
    result = []
    for user in users:
        stack_row = db.query(PlayerStack).filter(PlayerStack.user_id == user.id).first()
        result.append(UserAdminResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            is_admin=user.is_admin,
            stack=stack_row.stack if stack_row else None,
        ))
    return result


@router.patch("/users/{user_id}/stack")
def set_stack(
    user_id: int,
    body: SetStackRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Set a user's chip stack (upsert)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    stack_row = db.query(PlayerStack).filter(PlayerStack.user_id == user_id).first()
    if stack_row:
        stack_row.stack = body.stack
    else:
        stack_row = PlayerStack(user_id=user_id, stack=body.stack)
        db.add(stack_row)

    db.commit()
    return {"user_id": user_id, "stack": body.stack}


@router.patch("/users/{user_id}/promote")
def promote_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Promote a user to admin."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.is_admin = True
    db.commit()
    return {"user_id": user_id, "is_admin": True}


@router.patch("/users/{user_id}/demote")
def demote_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Demote a user from admin. Cannot demote yourself."""
    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot demote yourself"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.is_admin = False
    db.commit()
    return {"user_id": user_id, "is_admin": False}
