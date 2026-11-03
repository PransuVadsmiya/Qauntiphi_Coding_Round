from datetime import date

from app import cache
from app.services import profile, sync


def test_first_load_fetches_then_serves_from_cache(fake_github):
    sync.ensure_profile("octocat")
    repos = sync.ensure_repos("octocat")
    calls_after_first_load = fake_github.calls

    # Second load within TTL: zero network calls.
    sync.ensure_profile("octocat")
    assert sync.ensure_repos("octocat") == repos
    assert fake_github.calls == calls_after_first_load


def test_stale_cache_uses_etag_and_gets_304(fake_github):
    sync.ensure_repos("octocat")
    cache.invalidate("octocat")  # simulate TTL expiry
    sync.ensure_repos("octocat")
    # Every refetch was answered with 304 Not Modified (free on rate limit).
    assert sync.client().not_modified_hits >= 3


def test_forks_excluded_from_stars_and_languages(fake_github):
    repos = sync.ensure_repos("octocat")
    assert profile.total_stars(repos) == 15          # fork's 999 stars ignored
    langs = sync.cached_language_bytes("octocat")
    assert "Go" not in langs
    assert langs["Python"] == 9000


def test_top_languages_percentages(fake_github):
    sync.ensure_repos("octocat")
    top = profile.top_languages(sync.cached_language_bytes("octocat"), top_n=2)
    assert [t["language"] for t in top] == ["Python", "TypeScript", "Other"]
    assert round(sum(t["percent"] for t in top)) == 100


def test_contributions_and_streaks(fake_github):
    days = sync.ensure_contributions("octocat")
    assert len(days) == 6 and days[2]["level"] == 2
    s = profile.streaks(days, today=date(2026, 11, 2))
    assert s == {"current": 1, "longest": 3, "total": 7, "active_days": 4}
    # Today has no commits yet but yesterday did -> streak still alive
    s2 = profile.streaks(days, today=date(2026, 11, 3))
    assert s2["current"] == 1
