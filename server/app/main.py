from fastapi import FastAPI
from .routes.http import router as http_router
from .routes.ws import router as ws_router

def create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(http_router)
    app.include_router(ws_router)
    return app

app = create_app()
