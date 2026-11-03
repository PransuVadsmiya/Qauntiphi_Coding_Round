"""Derived stats for the dashboard: total stars, top languages, streaks."""
from datetime import date, timedelta


def total_stars(repos: list[dict]) -> int:
    return sum(r["stars"] for r in repos if not r["is_fork"])


def total_forks(repos: list[dict]) -> int:
    return sum(r["forks"] for r in repos if not r["is_fork"])


def top_languages(lang_bytes: dict[str, int], top_n: int = 6) -> list[dict]:
    """Share of code per language; everything past top_n is grouped as 'Other'."""
    total = sum(lang_bytes.values())
    if total == 0:
        return []
    items = sorted(lang_bytes.items(), key=lambda kv: kv[1], reverse=True)
    top, rest = items[:top_n], items[top_n:]
    result = [
        {"language": lang, "bytes": b, "percent": round(100 * b / total, 1)}
        for lang, b in top
    ]
    if rest:
        other = sum(b for _, b in rest)
        result.append({"language": "Other", "bytes": other, "percent": round(100 * other / total, 1)})
    return result


def streaks(days: list[dict], today: date | None = None) -> dict:
    """Current and longest streak of consecutive days with >= 1 contribution.

    The current streak is still alive if today has no contributions yet but
    yesterday did (the day isn't over).
    """
    if not days:
        return {"current": 0, "longest": 0, "total": 0, "active_days": 0}

    active = {d["date"] for d in days if d["count"] > 0}
    total = sum(d["count"] for d in days)

    longest = run = 0
    for d in sorted(days, key=lambda x: x["date"]):
        run = run + 1 if d["count"] > 0 else 0
        longest = max(longest, run)

    today = today or date.fromisoformat(max(d["date"] for d in days))
    cursor = today if today.isoformat() in active else today - timedelta(days=1)
    current = 0
    while cursor.isoformat() in active:
        current += 1
        cursor -= timedelta(days=1)

    return {"current": current, "longest": longest, "total": total, "active_days": len(active)}
