"""Admin routes for managing users and chip balances."""
import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import or_
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


class UserListResponse(BaseModel):
    """Paginated user list response."""
    users: List[UserAdminResponse]
    total: int
    page: int
    page_size: int
    pages: int


class SetStackRequest(BaseModel):
    """Request to set a user's chip stack."""
    stack: int = Field(..., ge=0, le=10_000_000)


@router.get("/users", response_model=UserListResponse)
def list_users(
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """List users with optional search and pagination."""
    query = db.query(User)
    if search:
        pattern = f"%{search}%"
        query = query.filter(or_(
            User.username.ilike(pattern),
            User.email.ilike(pattern),
        ))
    total = query.count()
    users_page = query.order_by(User.username).offset((page - 1) * page_size).limit(page_size).all()

    result = []
    for user in users_page:
        stack_row = db.query(PlayerStack).filter(PlayerStack.user_id == user.id).first()
        result.append(UserAdminResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            is_admin=user.is_admin,
            stack=stack_row.stack if stack_row else None,
        ))

    pages = math.ceil(total / page_size) if total > 0 else 1
    return UserListResponse(users=result, total=total, page=page, page_size=page_size, pages=pages)


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


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Delete a user. Cannot delete yourself."""
    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    db.delete(user)
    db.commit()
