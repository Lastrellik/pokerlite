"""Database models for users and player stacks."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from .base import Base


class User(Base):
    """User account model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=False)
    avatar_id = Column(String(50), default="chips", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)

    # Relationship to player stacks
    stacks = relationship("PlayerStack", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"


class PlayerStack(Base):
    """Player chip stack persistence."""

    __tablename__ = "player_stacks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    stack = Column(Integer, default=1000, nullable=False)  # Default starting stack
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship to user
    user = relationship("User", back_populates="stacks")

    # Index for faster lookups
    __table_args__ = (
        Index("ix_player_stacks_user_id", "user_id"),
    )

    def __repr__(self):
        return f"<PlayerStack(user_id={self.user_id}, stack={self.stack})>"
