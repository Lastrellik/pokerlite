"""Main FastAPI application for lobby service."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from .routes.tables import router as tables_router


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
    app.include_router(tables_router)

    @app.get("/api/health")
    def health():
        """Health check endpoint."""
        return {"ok": True, "service": "lobby"}

    return app


app = create_app()
