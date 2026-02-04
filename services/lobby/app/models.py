"""Pydantic models for API requests and responses."""
from pydantic import BaseModel, Field


class CreateTableRequest(BaseModel):
    """Request model for creating a table."""
    name: str = Field(..., min_length=1, max_length=50, description="Table name")
    small_blind: int = Field(default=5, ge=1, description="Small blind amount")
    big_blind: int = Field(default=10, ge=2, description="Big blind amount")
    max_players: int = Field(default=8, ge=2, le=8, description="Maximum players")
    turn_timeout_seconds: int = Field(default=30, ge=10, le=120, description="Turn timeout in seconds")


class TableResponse(BaseModel):
    """Response model for table data."""
    table_id: str
    name: str
    small_blind: int
    big_blind: int
    max_players: int
    turn_timeout_seconds: int
    created_at: str
    game_ws_url: str  # WebSocket URL to connect to game service
