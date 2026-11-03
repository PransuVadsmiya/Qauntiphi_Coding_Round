"""Shared test fixtures: a temp SQLite DB and a mocked GitHub API."""
import json

import httpx
import pytest

from app import config
from app.db import init_db
from app.github_client import GitHubClient
from app.services import sync

USER = {
    "login": "octocat", "name": "The Octocat", "avatar_url": "https://x/a.png",
    "bio": "Hello", "location": "SF", "blog": "", "html_url": "https://github.com/octocat",
    "followers": 42, "following": 3, "public_repos": 3, "created_at": "2011-01-25T18:44:36Z",
}

REPOS = [
    {"id": 1, "name": "ml-lab", "description": "ML experiments", "html_url": "u1",
     "language": "Python", "stargazers_count": 10, "forks_count": 2, "topics": ["ml"],
     "fork": False, "pushed_at": "2026-10-01", "updated_at": "2026-10-01",
     "owner": {"login": "octocat"}},
    {"id": 2, "name": "web-app", "description": "React app", "html_url": "u2",
     "language": "TypeScript", "stargazers_count": 5, "forks_count": 1, "topics": [],
     "fork": False, "pushed_at": "2026-09-01", "updated_at": "2026-09-01",
     "owner": {"login": "octocat"}},
    {"id": 3, "name": "forked", "description": "someone else's", "html_url": "u3",
     "language": "Go", "stargazers_count": 999, "forks_count": 50, "topics": [],
     "fork": True, "pushed_at": "2026-08-01", "updated_at": "2026-08-01",
     "owner": {"login": "octocat"}},
]

LANGS = {
    "ml-lab": {"Python": 9000, "Jupyter Notebook": 1000},
    "web-app": {"TypeScript": 6000, "CSS": 1000, "HTML": 500},
}

CONTRIB = {
    "data": {"user": {"contributionsCollection": {"contributionCalendar": {
        "totalContributions": 7,
        "weeks": [{"contributionDays": [
            {"date": "2026-10-28", "contributionCount": 0, "contributionLevel": "NONE"},
            {"date": "2026-10-29", "contributionCount": 2, "contributionLevel": "FIRST_QUARTILE"},
            {"date": "2026-10-30", "contributionCount": 3, "contributionLevel": "SECOND_QUARTILE"},
            {"date": "2026-10-31", "contributionCount": 1, "contributionLevel": "FIRST_QUARTILE"},
            {"date": "2026-11-01", "contributionCount": 0, "contributionLevel": "NONE"},
            {"date": "2026-11-02", "contributionCount": 1, "contributionLevel": "FIRST_QUARTILE"},
        ]}],
    }}}}
}


class FakeGitHub:
    """Mock transport. Returns ETags and honours If-None-Match with a 304."""

    def __init__(self):
        self.calls = 0

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.calls += 1
        path = request.url.path
        if request.method == "POST":
            return httpx.Response(200, json=CONTRIB)
        if path == "/users/octocat":
            body = USER
        elif path == "/users/octocat/repos":
            body = REPOS
        elif path.startswith("/repos/octocat/") and path.endswith("/languages"):
            body = LANGS.get(path.split("/")[3], {})
        else:
            return httpx.Response(404, json={"message": "Not Found"})
        etag = f'"{abs(hash(json.dumps(body, sort_keys=True)))}"'
        if request.headers.get("if-none-match") == etag:
            return httpx.Response(304, headers={"etag": etag, "x-ratelimit-remaining": "4999"})
        return httpx.Response(200, json=body, headers={"etag": etag, "x-ratelimit-remaining": "4999"})


@pytest.fixture
def fake_github(tmp_path, monkeypatch):
    monkeypatch.setattr(config.settings, "db_path", tmp_path / "test.db")
    monkeypatch.setattr(config.Settings, "github_token", "test-token")
    init_db()
    fake = FakeGitHub()
    sync.set_client(GitHubClient(transport=httpx.MockTransport(fake.handler)))
    yield fake
    sync.set_client(None)
