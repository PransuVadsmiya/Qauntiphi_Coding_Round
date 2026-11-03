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
