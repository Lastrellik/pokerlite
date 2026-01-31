from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from pathlib import Path

from .routes.http import router as http_router
from .routes.ws import router as ws_router

def create_app() -> FastAPI:
    app = FastAPI(title="PokerLite", version="1.0.0")

    # CORS configuration for development
    # In production, these should be set via environment variables
    cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(http_router)
    app.include_router(ws_router)

    # Serve static files (built React app) if they exist
    static_dir = Path(__file__).parent.parent / "static"
    if static_dir.exists():
        # Mount static assets (js, css, images, etc.)
        app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="assets")

        # Serve index.html for all other routes (SPA fallback)
        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            # Don't interfere with API or WebSocket routes
            if full_path.startswith("api/") or full_path.startswith("ws/"):
                return {"error": "Not found"}

            index_file = static_dir / "index.html"
            if index_file.exists():
                return FileResponse(index_file)
            return {"error": "Frontend not built"}

    return app

app = create_app()
