"""Core portfolio endpoints: profile header, repos, contributions, refresh."""
import re
import time

from fastapi import APIRouter, HTTPException, Query

from .. import cache
from ..github_client import GitHubError
from ..services import profile as stats
from ..services import sync

router = APIRouter(prefix="/api", tags=["portfolio"])


USERNAME_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$")


def _gh(fn, *args, **kwargs):
    """Translate GitHub errors into clean HTTP errors."""
    login = args[0] if args else ""
    if not USERNAME_RE.match(login):
        raise HTTPException(
            status_code=400,
            detail=f"'{login}' is not a valid GitHub username. Use the username from the profile URL "
                   "(e.g. PransuVadsmiya), not the display name.",
        )
    try:
        return fn(*args, **kwargs)
    except GitHubError as e:
        raise HTTPException(status_code=e.status if e.status in (400, 401, 403, 404) else 502, detail=e.message)


@router.get("/profile/{login}")
def get_profile(login: str, refresh: bool = Query(False)):
    """Profile header: user info, follower count, total stars, top languages."""
    user = _gh(sync.ensure_profile, login, force=refresh)
    repos = _gh(sync.ensure_repos, login, force=refresh)
    lang_bytes = sync.cached_language_bytes(login)
    return {
        "user": user,
        "stats": {
            "followers": user.get("followers", 0),
            "following": user.get("following", 0),
            "public_repos": user.get("public_repos", 0),
            "total_stars": stats.total_stars(repos),
            "total_forks": stats.total_forks(repos),
        },
        "top_languages": stats.top_languages(lang_bytes),
        "cache": _cache_info(login),
    }


@router.get("/repos/{login}")
def get_repos(
    login: str,
    refresh: bool = Query(False),
    include_forks: bool = Query(False),
    sort: str = Query("stars", pattern="^(stars|forks|updated|name)$"),
):
    repos = _gh(sync.ensure_repos, login, force=refresh)
    if not include_forks:
        repos = [r for r in repos if not r["is_fork"]]
    key = {
        "stars": lambda r: (-r["stars"], r["name"].lower()),
        "forks": lambda r: (-r["forks"], r["name"].lower()),
        "updated": lambda r: r["pushed_at"] or "",
        "name": lambda r: r["name"].lower(),
    }[sort]
    repos = sorted(repos, key=key, reverse=(sort == "updated"))
    return {"count": len(repos), "repos": repos}


@router.get("/contributions/{login}")
def get_contributions(login: str, refresh: bool = Query(False)):
    days = _gh(sync.ensure_contributions, login, force=refresh)
    return {"days": days, "streaks": stats.streaks(days)}


@router.post("/refresh/{login}")
def refresh(login: str):
    """Drop the cache for this user so the next load re-pulls from GitHub."""
    cache.invalidate(login)
    return {"ok": True}


@router.get("/cache/{login}")
def cache_status(login: str):
    return _cache_info(login)


def _cache_info(login: str) -> dict:
    gh = sync.client()
    now = time.time()
    return {
        "datasets": {k: round(now - v) for k, v in cache.last_refreshed(login).items()},  # age in seconds
        "ttl_seconds": cache.settings.cache_ttl_seconds,
        "rate_limit_remaining": gh.rate_limit_remaining,
        "network_calls": gh.network_calls,
        "not_modified_hits": gh.not_modified_hits,
    }
