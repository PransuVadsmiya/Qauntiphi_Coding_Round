"""Extra feature 2: JD Gap Coach.

Takes the compatibility result for a job description and explains the gap:
what's missing, concrete projects that would close it (built on top of the
developer's existing repos where possible) and a short tailored pitch.
"""
import json

from . import llm
from .match import compute_match
from .portfolio_context import as_text, snapshot

SYSTEM_PROMPT = """You are a career coach for software developers. Using the portfolio data and
the job-match analysis, return STRICT JSON with this shape and nothing else:
{{
  "summary": "2 sentences on overall fit",
  "strengths": ["up to 4 short bullets naming repos/languages that fit the JD"],
  "gaps": [{{"skill": "...", "why_it_matters": "one sentence"}}],
  "project_ideas": [{{"title": "...", "skills": ["..."], "description": "2 sentences, ideally extending an existing repo"}}],
  "pitch": "3-4 sentence first-person pitch the developer could send to the recruiter"
}}
Give 2-3 project ideas. Only claim skills the data supports.

PORTFOLIO DATA
--------------
{context}

MATCH ANALYSIS
--------------
{analysis}"""

# Fallback project ideas when no LLM is configured.
IDEAS = {
    "Docker": "Containerize your top project with a Dockerfile and docker-compose, and document one-command setup.",
    "React": "Build a React dashboard front end for one of your existing APIs or datasets.",
    "Node.js": "Write a small Express.js REST API with auth and tests, then deploy it.",
    "SQL": "Add a PostgreSQL/SQLite persistence layer with migrations to an existing project.",
    "Machine Learning": "Train and evaluate a scikit-learn model on a public dataset, with a clear README of results.",
    "Deep Learning": "Fine-tune a small PyTorch model and expose it through a FastAPI inference endpoint.",
    "Java": "Rebuild a small service in Spring Boot with JUnit tests.",
    "Spring": "Create a Spring Boot CRUD service with JPA and a Postman collection.",
    "TypeScript": "Port one JavaScript project to TypeScript with strict mode on.",
    "Go": "Write a concurrent CLI tool in Go (e.g. a parallel URL health checker).",
    "Rust": "Build a fast CLI utility in Rust and publish it as a crate.",
    "Terraform": "Provision your app's cloud infrastructure with Terraform and add it to the repo.",
}


def coach(login: str, job_description: str) -> dict:
    result = compute_match(login, job_description)
    snap = snapshot(login)

    try:
        raw = llm.chat(
            SYSTEM_PROMPT.format(context=as_text(snap), analysis=json.dumps(result, indent=1)),
            [{"role": "user", "content": f"Job description:\n{job_description}"}],
            temperature=0.5, max_tokens=1200,
        )
        if raw:
            cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            return {"match": result, "advice": json.loads(cleaned), "source": "llm"}
    except (llm.LLMError, json.JSONDecodeError):
        pass
    return {"match": result, "advice": rule_based(snap, result), "source": "rules"}


def rule_based(snap: dict, result: dict) -> dict:
    name = snap["user"].get("name") or snap["user"].get("login")
    strong = [t for t in result["technologies"] if t["status"] == "matched"]
    weak = [t for t in result["technologies"] if t["status"] != "matched"]

    strengths = [f"{t['technology']}: {t['reason']}" + (f" (e.g. {', '.join(t['repos'][:2])})" if t["repos"] else "")
                 for t in strong[:4]]
    gaps = [{"skill": t["technology"],
             "why_it_matters": f"The JD asks for {t['technology']} but there is {t['reason']}."}
            for t in weak]
    ideas = [{"title": f"{t['technology']} showcase project", "skills": [t["technology"]],
              "description": IDEAS.get(t["technology"], f"Build a small public project that uses {t['technology']} end to end.")}
             for t in weak[:3]]
    top_repo = max(snap["repos"], key=lambda r: r["stars"], default=None)
    pitch = (f"Hi, I'm {name}. My GitHub shows hands-on work with "
             f"{', '.join(t['technology'] for t in strong[:3]) or 'several technologies'}"
             + (f", including {top_repo['name']}" if top_repo else "")
             + f". My stack matches about {result['match_percent']}% of this role, and I'm actively building "
             f"{', '.join(g['skill'] for g in gaps[:2]) or 'new skills'} projects to close the rest.")
    return {
        "summary": f"{result['label']} ({result['match_percent']}%): {len(strong)} of "
                   f"{len(result['technologies'])} required technologies are well covered.",
        "strengths": strengths,
        "gaps": gaps,
        "project_ideas": ideas,
        "pitch": pitch,
    }
