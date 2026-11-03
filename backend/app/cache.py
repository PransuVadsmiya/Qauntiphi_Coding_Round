"""Caching engine helpers.

Two levels of caching:
1. Dataset freshness (cache_meta): has this user's profile/repos/contributions
   been refreshed within CACHE_TTL_SECONDS? If yes, serve straight from SQLite
   with zero API calls.
2. HTTP cache (api_cache): when a dataset is stale we re-fetch, but send the
   stored ETag. GitHub answers 304 Not Modified for unchanged data, and 304s do
   not count against the rate limit.
"""
import json
import time
from typing import Any, Optional

from .config import settings
from .db import db


# ---------- dataset freshness ----------

def is_fresh(login: str, dataset: str, ttl: Optional[int] = None) -> bool:
    ttl = settings.cache_ttl_seconds if ttl is None else ttl
    with db() as conn:
        row = conn.execute(
            "SELECT refreshed_at FROM cache_meta WHERE login=? AND dataset=?",
            (login.lower(), dataset),
        ).fetchone()
    return bool(row) and (time.time() - row["refreshed_at"]) < ttl


def mark_refreshed(login: str, dataset: str) -> None:
    with db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO cache_meta(login, dataset, refreshed_at) VALUES (?,?,?)",
            (login.lower(), dataset, time.time()),
        )


def last_refreshed(login: str) -> dict[str, float]:
    with db() as conn:
        rows = conn.execute(
            "SELECT dataset, refreshed_at FROM cache_meta WHERE login=?",
            (login.lower(),),
        ).fetchall()
    return {r["dataset"]: r["refreshed_at"] for r in rows}


def invalidate(login: str) -> None:
    """Force the next request for this user to go back to GitHub."""
    with db() as conn:
        conn.execute("DELETE FROM cache_meta WHERE login=?", (login.lower(),))


# ---------- HTTP (ETag) cache ----------

def get_http_cache(url: str) -> Optional[dict]:
    with db() as conn:
        row = conn.execute(
            "SELECT etag, body, fetched_at FROM api_cache WHERE url=?", (url,)
        ).fetchone()
    if not row:
        return None
    return {"etag": row["etag"], "body": json.loads(row["body"]), "fetched_at": row["fetched_at"]}


def set_http_cache(url: str, etag: Optional[str], body: Any) -> None:
    with db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO api_cache(url, etag, body, fetched_at) VALUES (?,?,?,?)",
            (url, etag, json.dumps(body), time.time()),
        )


# ---------- user settings ----------

def get_settings(login: str) -> dict[str, Any]:
    with db() as conn:
        rows = conn.execute(
            "SELECT key, value FROM settings WHERE login=?", (login.lower(),)
        ).fetchall()
    return {r["key"]: json.loads(r["value"]) for r in rows}


def save_settings(login: str, values: dict[str, Any]) -> dict[str, Any]:
    with db() as conn:
        for key, value in values.items():
            conn.execute(
                "INSERT OR REPLACE INTO settings(login, key, value) VALUES (?,?,?)",
                (login.lower(), key, json.dumps(value)),
            )
    return get_settings(login)
