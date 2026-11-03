"""FastAPI entry point.

Run from the backend/ folder:
    uvicorn app.main:app --reload
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import init_db
from .routers import assistant, match, portfolio, settings as settings_router

@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="GitHub Developer Portfolio API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "github_token": bool(settings.github_token),
        "llm_enabled": settings.llm_enabled,
        "default_user": settings.default_user,
    }


app.include_router(portfolio.router)
app.include_router(settings_router.router)
app.include_router(match.router)
app.include_router(assistant.router)
