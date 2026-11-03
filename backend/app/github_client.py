"""GitHub API client (REST + GraphQL) with ETag conditional requests.

Every REST GET goes through `_get_json`, which:
  * sends the stored ETag as If-None-Match,
  * on 304 Not Modified returns the cached body (does NOT count against rate limit),
  * on 200 stores the new ETag + body in SQLite.
"""
from typing import Any, Optional

import httpx

from . import cache
from .config import settings

REST_BASE = "https://api.github.com"
GRAPHQL_URL = "https://api.github.com/graphql"


class GitHubError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


def _headers(extra: Optional[dict] = None) -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "github-portfolio-dashboard",
    }
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    if extra:
        headers.update(extra)
    return headers


class GitHubClient:
    def __init__(self, transport: Optional[httpx.BaseTransport] = None):
        # `transport` lets tests inject a mock transport.
        self.http = httpx.Client(timeout=20.0, transport=transport)
        self.rate_limit_remaining: Optional[int] = None
        self.not_modified_hits = 0
        self.network_calls = 0

    # ---------- REST ----------

    def _get_json(self, path: str, params: Optional[dict] = None) -> Any:
        url = f"{REST_BASE}{path}"
        if params:
            url += "?" + "&".join(f"{k}={v}" for k, v in params.items())

        cached = cache.get_http_cache(url)
        extra = {"If-None-Match": cached["etag"]} if cached and cached["etag"] else None

        resp = self.http.get(url, headers=_headers(extra))
        self.network_calls += 1
        remaining = resp.headers.get("x-ratelimit-remaining")
        if remaining is not None:
            self.rate_limit_remaining = int(remaining)

        if resp.status_code == 304 and cached:
            self.not_modified_hits += 1
            return cached["body"]

        if resp.status_code == 404:
            raise GitHubError(404, f"GitHub user or resource not found: {path}")
        if resp.status_code in (401, 403):
            # Rate-limited or bad token: fall back to stale cache if we have it.
            if cached:
                return cached["body"]
            msg = resp.json().get("message", "Forbidden") if resp.content else "Forbidden"
            raise GitHubError(resp.status_code, msg)
        resp.raise_for_status()

        body = resp.json()
        cache.set_http_cache(url, resp.headers.get("etag"), body)
        return body

    def get_user(self, login: str) -> dict:
        return self._get_json(f"/users/{login}")

    def get_repos(self, login: str, max_pages: int = 5) -> list[dict]:
        repos: list[dict] = []
        for page in range(1, max_pages + 1):
            batch = self._get_json(
                f"/users/{login}/repos",
                {"per_page": 100, "page": page, "sort": "pushed"},
            )
            repos.extend(batch)
            if len(batch) < 100:
                break
        return repos

    def get_repo_languages(self, owner: str, repo: str) -> dict[str, int]:
        return self._get_json(f"/repos/{owner}/{repo}/languages")

    # ---------- GraphQL ----------

    CONTRIB_QUERY = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays { date contributionCount contributionLevel }
            }
          }
        }
      }
    }
    """

    LEVELS = {
        "NONE": 0,
        "FIRST_QUARTILE": 1,
        "SECOND_QUARTILE": 2,
        "THIRD_QUARTILE": 3,
        "FOURTH_QUARTILE": 4,
    }

    def get_contributions(self, login: str) -> list[dict]:
        """Daily contributions for the last year. GraphQL requires a token."""
        if not settings.github_token:
            raise GitHubError(401, "GITHUB_TOKEN is required for the contribution graph (GraphQL).")
        resp = self.http.post(
            GRAPHQL_URL,
            headers=_headers(),
            json={"query": self.CONTRIB_QUERY, "variables": {"login": login}},
        )
        self.network_calls += 1
        if resp.status_code != 200:
            raise GitHubError(resp.status_code, "GraphQL request failed")
        data = resp.json()
        if data.get("errors"):
            raise GitHubError(400, data["errors"][0].get("message", "GraphQL error"))
        user = (data.get("data") or {}).get("user")
        if not user:
            raise GitHubError(404, f"GitHub user not found: {login}")

        weeks = user["contributionsCollection"]["contributionCalendar"]["weeks"]
        return [
            {
                "date": d["date"],
                "count": d["contributionCount"],
                "level": self.LEVELS.get(d["contributionLevel"], 0),
            }
            for w in weeks
            for d in w["contributionDays"]
        ]
