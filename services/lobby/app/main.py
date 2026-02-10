"""Main FastAPI application for lobby service."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path

from .routes.tables import router as tables_router
from .routes.auth import router as auth_router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="PokerLite Lobby",
        description="Lobby service for managing poker tables",
        version="1.0.0"
    )

    # CORS configuration
    cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(auth_router)
    app.include_router(tables_router)

    # Mount static files for avatars
    static_dir = Path(__file__).parent.parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/api/health")
    def health():
        """Health check endpoint."""
        return {"ok": True, "service": "lobby"}

    @app.get("/api/avatars")
    def list_avatars():
        """List available avatar IDs."""
        # Predefined avatar list (actual images to be added later)
        return {
            "avatars": [
                {"id": "chips", "name": "Poker Chips", "url": "/static/avatars/chips.png"},
                {"id": "spades", "name": "Spades", "url": "/static/avatars/spades.png"},
                {"id": "hearts", "name": "Hearts", "url": "/static/avatars/hearts.png"},
                {"id": "diamonds", "name": "Diamonds", "url": "/static/avatars/diamonds.png"},
                {"id": "clubs", "name": "Clubs", "url": "/static/avatars/clubs.png"},
                {"id": "ace", "name": "Ace", "url": "/static/avatars/ace.png"},
                {"id": "king", "name": "King", "url": "/static/avatars/king.png"},
                {"id": "queen", "name": "Queen", "url": "/static/avatars/queen.png"},
                {"id": "jack", "name": "Jack", "url": "/static/avatars/jack.png"},
                {"id": "dealer", "name": "Dealer Button", "url": "/static/avatars/dealer.png"},
            ]
        }

    return app


app = create_app()
