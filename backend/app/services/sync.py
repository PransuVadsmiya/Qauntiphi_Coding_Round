"""Get-or-fetch layer: serve from SQLite when fresh, otherwise refresh from GitHub.

Each dataset (profile, repos, contributions) has its own freshness entry in
cache_meta, so one stale dataset doesn't force a refetch of the others.
"""
import json
from typing import Optional

from .. import cache
from ..db import db
from ..github_client import GitHubClient

_client: Optional[GitHubClient] = None


def client() -> GitHubClient:
    global _client
    if _client is None:
        _client = GitHubClient()
    return _client


def set_client(c: GitHubClient) -> None:
    """Used by tests to inject a mocked client."""
    global _client
    _client = c


# ---------- profile ----------

def ensure_profile(login: str, force: bool = False) -> dict:
    login_l = login.lower()
    if force or not cache.is_fresh(login_l, "profile"):
        u = client().get_user(login)
        with db() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO users
                   (login, name, avatar_url, bio, location, blog, html_url,
                    followers, following, public_repos, created_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    login_l, u.get("name"), u.get("avatar_url"), u.get("bio"),
                    u.get("location"), u.get("blog"), u.get("html_url"),
                    u.get("followers", 0), u.get("following", 0),
                    u.get("public_repos", 0), u.get("created_at"),
                ),
            )
        cache.mark_refreshed(login_l, "profile")

    with db() as conn:
        row = conn.execute("SELECT * FROM users WHERE login=?", (login_l,)).fetchone()
    return dict(row) if row else {}


# ---------- repos + languages ----------

def ensure_repos(login: str, force: bool = False) -> list[dict]:
    login_l = login.lower()
    if force or not cache.is_fresh(login_l, "repos"):
        gh = client()
        repos = gh.get_repos(login)
        with db() as conn:
            conn.execute("DELETE FROM repos WHERE owner=?", (login_l,))
            conn.execute("DELETE FROM repo_languages WHERE owner=?", (login_l,))
            for r in repos:
                conn.execute(
                    """INSERT OR REPLACE INTO repos
                       (id, owner, name, description, html_url, language, stars,
                        forks, topics, is_fork, pushed_at, updated_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        r["id"], login_l, r["name"], r.get("description"),
                        r.get("html_url"), r.get("language"),
                        r.get("stargazers_count", 0), r.get("forks_count", 0),
                        json.dumps(r.get("topics", [])), int(bool(r.get("fork"))),
                        r.get("pushed_at"), r.get("updated_at"),
                    ),
                )
        # Language byte counts only for original (non-fork) repos: forks would
        # inflate the user's languages with someone else's code.
        for r in repos:
            if r.get("fork"):
                continue
            langs = gh.get_repo_languages(r["owner"]["login"], r["name"])
            with db() as conn:
                for lang, nbytes in langs.items():
                    conn.execute(
                        "INSERT OR REPLACE INTO repo_languages(repo_id, owner, language, bytes) VALUES (?,?,?,?)",
                        (r["id"], login_l, lang, nbytes),
                    )
        cache.mark_refreshed(login_l, "repos")

    return cached_repos(login_l)


def cached_repos(login: str) -> list[dict]:
    with db() as conn:
        rows = conn.execute(
            "SELECT * FROM repos WHERE owner=? ORDER BY stars DESC, pushed_at DESC",
            (login.lower(),),
        ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["topics"] = json.loads(d["topics"] or "[]")
        d["is_fork"] = bool(d["is_fork"])
        out.append(d)
    return out


def cached_language_bytes(login: str) -> dict[str, int]:
    """Total bytes per language across the user's cached original repos."""
    with db() as conn:
        rows = conn.execute(
            "SELECT language, SUM(bytes) AS total FROM repo_languages WHERE owner=? GROUP BY language ORDER BY total DESC",
            (login.lower(),),
        ).fetchall()
    return {r["language"]: r["total"] for r in rows}


# ---------- contributions ----------

def ensure_contributions(login: str, force: bool = False) -> list[dict]:
    login_l = login.lower()
    if force or not cache.is_fresh(login_l, "contributions"):
        days = client().get_contributions(login)
        with db() as conn:
            conn.execute("DELETE FROM contributions WHERE login=?", (login_l,))
            conn.executemany(
                "INSERT INTO contributions(login, date, count, level) VALUES (?,?,?,?)",
                [(login_l, d["date"], d["count"], d["level"]) for d in days],
            )
        cache.mark_refreshed(login_l, "contributions")

    with db() as conn:
        rows = conn.execute(
            "SELECT date, count, level FROM contributions WHERE login=? ORDER BY date",
            (login_l,),
        ).fetchall()
    return [dict(r) for r in rows]
