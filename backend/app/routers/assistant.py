"""Chatbot-powered extra features: Ask my Portfolio + JD Gap Coach."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..github_client import GitHubError
from ..services import chatbot, gap_coach, sync

router = APIRouter(prefix="/api", tags=["assistant"])


class ChatTurn(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str


class ChatRequest(BaseModel):
    login: str
    message: str = Field(min_length=1, max_length=2000)
    history: list[ChatTurn] = []


class CoachRequest(BaseModel):
    login: str
    job_description: str = Field(min_length=10, max_length=20000)


def _ensure(login: str):
    try:
        sync.ensure_profile(login)
        sync.ensure_repos(login)
    except GitHubError as e:
        raise HTTPException(status_code=e.status if e.status in (401, 403, 404) else 502, detail=e.message)


@router.post("/chat")
def chat(req: ChatRequest):
    _ensure(req.login)
    return chatbot.answer(req.login, req.message, [t.model_dump() for t in req.history])


@router.get("/chat/suggestions")
def suggestions():
    return chatbot.SUGGESTED_QUESTIONS


@router.post("/gap-coach")
def coach(req: CoachRequest):
    _ensure(req.login)
    return gap_coach.coach(req.login, req.job_description)
