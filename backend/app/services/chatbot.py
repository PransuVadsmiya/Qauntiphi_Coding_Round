"""Extra feature 1: "Ask my Portfolio" chatbot.

A recruiter (or the developer) asks questions in plain English; the answer is
grounded in the cached portfolio snapshot. Uses the LLM when configured and
falls back to a rule-based answerer otherwise.
"""
import re

from . import llm
from .match import extract_technologies
from .portfolio_context import as_text, snapshot

SYSTEM_PROMPT = """You are the portfolio assistant for a developer's GitHub profile page.
Answer questions from recruiters and visitors about this developer using ONLY the
portfolio data below. Be concise (2-5 sentences or a short bullet list), specific
(name repos, languages, numbers) and honest: if the data doesn't show something,
say so rather than guessing. Refer to the developer in the third person.

PORTFOLIO DATA
--------------
{context}"""

SUGGESTED_QUESTIONS = [
    "What are this developer's strongest skills?",
    "Which project best shows backend experience?",
    "Has this developer worked with machine learning?",
    "How active have they been recently?",
]


def answer(login: str, message: str, history: list[dict]) -> dict:
    snap = snapshot(login)
    if not snap["repos"]:
        return {"reply": "I don't have any cached repositories for this user yet. Load the profile first.", "source": "rules"}

    try:
        reply = llm.chat(
            SYSTEM_PROMPT.format(context=as_text(snap)),
            [*history[-8:], {"role": "user", "content": message}],
        )
        if reply:
            return {"reply": reply, "source": "llm"}
    except llm.LLMError:
        pass  # fall through to rules so the demo never breaks
    return {"reply": rule_based(snap, message), "source": "rules"}


def rule_based(snap: dict, message: str) -> str:
    q = message.lower()
    u, repos, langs, s = snap["user"], snap["repos"], snap["languages"], snap["streaks"]
    name = u.get("name") or u.get("login")

    techs = extract_technologies(message)
    if techs:
        parts = []
        for tech, tech_langs in techs.items():
            hits = [
                r["name"] for r in repos
                if r["language"] in tech_langs
                or tech.lower() in " ".join(r["topics"]).lower()
                or tech.lower() in (r["description"] or "").lower()
            ]
            parts.append(
                f"{tech}: yes, in {len(hits)} repo(s) such as {', '.join(hits[:4])}." if hits
                else f"{tech}: no evidence in the public repositories."
            )
        return " ".join(parts)

    if re.search(r"star|popular|best|top project|showcase", q):
        top = sorted(repos, key=lambda r: r["stars"], reverse=True)[:3]
        return f"{name}'s most starred projects: " + "; ".join(
            f"{r['name']} ({r['stars']}★, {r['language'] or 'n/a'})" for r in top
        ) + "."
    if re.search(r"language|skill|stack|strong", q):
        return f"By share of code, {name} mostly writes " + ", ".join(
            f"{l['language']} ({l['percent']}%)" for l in langs[:5]
        ) + "."
    if re.search(r"active|streak|contribut|commit|recent", q):
        recent = sorted(repos, key=lambda r: r["pushed_at"] or "", reverse=True)[:3]
        return (f"{name} made {s['total']} contributions in the last year, with a current streak of "
                f"{s['current']} days (longest {s['longest']}). Recently active repos: "
                + ", ".join(r["name"] for r in recent) + ".")
    if re.search(r"follower|who|about|bio", q):
        return (f"{name} has {u.get('followers', 0)} followers, {len(repos)} original public repos and "
                f"{snap['total_stars']} total stars. Bio: {u.get('bio') or 'not provided'}.")
    return ("I can answer questions about skills, languages, top projects, activity and specific technologies "
            "(e.g. \"Has this developer used React?\"). Set an LLM key for free-form answers.")
