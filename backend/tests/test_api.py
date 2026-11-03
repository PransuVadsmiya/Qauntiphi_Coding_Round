from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_profile_endpoint(fake_github):
    r = client.get("/api/profile/octocat")
    assert r.status_code == 200
    body = r.json()
    assert body["stats"]["followers"] == 42
    assert body["stats"]["total_stars"] == 15
    assert body["top_languages"][0]["language"] == "Python"


def test_repos_endpoint_hides_forks_by_default(fake_github):
    names = [r["name"] for r in client.get("/api/repos/octocat").json()["repos"]]
    assert names == ["ml-lab", "web-app"]
    with_forks = client.get("/api/repos/octocat?include_forks=true").json()
    assert with_forks["count"] == 3


def test_contributions_endpoint(fake_github):
    body = client.get("/api/contributions/octocat").json()
    assert len(body["days"]) == 6
    assert body["streaks"]["longest"] == 3


def test_unknown_user_returns_404(fake_github):
    assert client.get("/api/profile/nobody-here").status_code == 404


def test_settings_roundtrip(fake_github):
    client.put("/api/settings/octocat", json={"theme": "dark", "pinned": ["ml-lab"]})
    assert client.get("/api/settings/octocat").json() == {"theme": "dark", "pinned": ["ml-lab"]}


def test_display_name_with_space_gives_clear_error(fake_github):
    r = client.get("/api/profile/Pransu Vadsmiya")
    assert r.status_code == 400
    assert "not a valid GitHub username" in r.json()["detail"]


def test_profile_repo_counts_split_forks(fake_github):
    stats = client.get("/api/profile/octocat").json()["stats"]
    assert stats["public_repos"] == 3      # GitHub's count includes forks
    assert stats["original_repos"] == 2    # what the cards show by default
    assert stats["forked_repos"] == 1


def test_match_reads_languages_from_sqlite_cache_not_github(fake_github):
    client.get("/api/profile/octocat")          # first load fills the cache
    calls = fake_github.calls
    r = client.post("/api/match", json={"login": "octocat", "job_description": "Python and React engineer"})
    assert r.json()["match_percent"] == 100
    assert fake_github.calls == calls           # scoring made zero GitHub calls
