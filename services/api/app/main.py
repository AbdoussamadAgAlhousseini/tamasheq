import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import capabilities, chat, dictionary, health


def create_app() -> FastAPI:
    settings = get_settings()
    logging.basicConfig(level=logging.INFO)
    app = FastAPI(title="TAMASHEQ API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Content-Type", "Authorization"],
    )
    app.include_router(health.router)
    app.include_router(capabilities.router)
    app.include_router(chat.router)
    app.include_router(dictionary.router)
    return app


app = create_app()
