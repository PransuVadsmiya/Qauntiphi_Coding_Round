"""POST /api/match - Tech Stack Compatibility score against a job description."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .. import cache
from ..github_client import GitHubError
from ..services import sync
from ..services.match import compute_match

router = APIRouter(prefix="/api", tags=["match"])


class MatchRequest(BaseModel):
    login: str
    job_description: str = Field(min_length=10, max_length=20000)


@router.post("/match")
def match(req: MatchRequest):
    # Make sure the repo/language cache exists (served from SQLite if fresh).
    try:
        sync.ensure_repos(req.login)
    except GitHubError as e:
        raise HTTPException(status_code=e.status if e.status in (401, 403, 404) else 502, detail=e.message)
    result = compute_match(req.login, req.job_description)
    # Remember the last JD + score in user settings so the badge survives reloads.
    cache.save_settings(req.login, {
        "last_job_description": req.job_description,
        "last_match_percent": result["match_percent"],
    })
    return result
