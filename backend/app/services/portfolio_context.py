"""Builds a compact text snapshot of a developer's portfolio from the SQLite cache.

This is the "retrieval" step for both chatbot features: the LLM only sees
facts from the cache, which keeps answers grounded and costs no GitHub calls.
"""
from ..db import db
from . import profile as stats
from . import sync


def snapshot(login: str) -> dict:
    with db() as conn:
        user = conn.execute("SELECT * FROM users WHERE login=?", (login.lower(),)).fetchone()
        days = conn.execute(
            "SELECT date, count, level FROM contributions WHERE login=? ORDER BY date", (login.lower(),)
        ).fetchall()
    repos = [r for r in sync.cached_repos(login) if not r["is_fork"]]
    langs = stats.top_languages(sync.cached_language_bytes(login), top_n=10)
    return {
        "user": dict(user) if user else {"login": login},
        "repos": repos,
        "languages": langs,
        "streaks": stats.streaks([dict(d) for d in days]),
        "total_stars": stats.total_stars(repos),
    }


def as_text(snap: dict, max_repos: int = 40) -> str:
    u = snap["user"]
    lines = [
        f"Developer: {u.get('name') or u.get('login')} (@{u.get('login')})",
        f"Bio: {u.get('bio') or 'n/a'} | Location: {u.get('location') or 'n/a'}",
        f"Followers: {u.get('followers', 0)} | Public repos: {u.get('public_repos', 0)} | Total stars: {snap['total_stars']}",
        f"Contributions last year: {snap['streaks']['total']} | Current streak: {snap['streaks']['current']} days | "
        f"Longest streak: {snap['streaks']['longest']} days",
        "Languages by share of code: " + ", ".join(f"{l['language']} {l['percent']}%" for l in snap["languages"]),
        "",
        "Repositories (name | language | stars | forks | topics | description):",
    ]
    for r in snap["repos"][:max_repos]:
        lines.append(
            f"- {r['name']} | {r['language'] or 'n/a'} | {r['stars']}★ | {r['forks']} forks | "
            f"{', '.join(r['topics']) or '-'} | {r['description'] or '-'}"
        )
    return "\n".join(lines)
