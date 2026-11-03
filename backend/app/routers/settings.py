"""User settings stored in SQLite (theme, pinned repos, saved job description...)."""
from typing import Any

from fastapi import APIRouter

from .. import cache

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/{login}")
def read_settings(login: str):
    return cache.get_settings(login)


@router.put("/{login}")
def update_settings(login: str, values: dict[str, Any]):
    return cache.save_settings(login, values)
