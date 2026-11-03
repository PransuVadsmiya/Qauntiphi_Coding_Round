# DevFolio: GitHub Developer Portfolio

A personal-branding dashboard that visualizes a developer's GitHub activity, repository stats and coding streaks, scores how well their tech stack matches a job description, and lets recruiters chat with the portfolio.

Built for the Quantiphi Analytics vibe coding round.

## Features

### Core
| Requirement | Implementation |
|---|---|
| **Contribution graph** | GitHub-style heatmap of the last year (53 × 7 grid), coloured by intensity level 0–4, with hover details, current streak, longest streak and active days |
| **Repository cards** | Stars, forks, language tag (GitHub colours), description, topics and last push; searchable, filterable by language, sortable |
| **Profile header** | Avatar, bio, followers, **total stars** (summed over original repos, forks excluded), repo count, streaks, and a **Top Languages** donut chart weighted by bytes of code |
| **API integration** | GitHub **REST** (profile, repos, per-repo languages) + **GraphQL** (contribution calendar) |
| **Caching engine** | **SQLite** caches profile, repo metadata, languages, contributions and user settings (see below) |
| **Tech Stack Compatibility** | Paste a job description → backend extracts tech keywords and compares them with the languages in the **cached** repos → circular **Match %** badge at the top of the profile plus a per-technology breakdown |

### Extra features (chatbot-powered)
1. **💬 Ask my Portfolio**: a floating chatbot where a recruiter can ask *"Has this developer worked with ML?"* or *"Which project shows backend skills?"*. Answers are grounded only in the cached portfolio data (a small RAG over SQLite), so they're accurate and cost no GitHub API calls.
2. **✨ JD Gap Coach**: after scoring a JD, the coach summarises the fit, lists strengths and gaps, suggests 2–3 projects to close the gaps, and drafts a tailored pitch to send the recruiter.

Both work with **Gemini, Groq or OpenAI**. With no LLM key they fall back to rule-based answers, so the app never breaks.

## How the caching engine works

```
request ──► is dataset fresh in SQLite? (cache_meta, TTL = 1h default)
              │ yes ──► serve from SQLite (0 GitHub calls)
              │ no
              ▼
          GitHub request with If-None-Match: <stored ETag>
              │ 304 Not Modified ──► reuse cached body (free: doesn't count against the rate limit)
              │ 200 OK ──► store new ETag + body, update tables
              │ 403 rate-limited ──► serve stale cache instead of failing
```

| Table | Purpose |
|---|---|
| `users` | profile per username |
| `repos` | repository metadata |
| `repo_languages` | bytes of code per language per repo (pie chart + match score) |
| `contributions` | one row per day of the contribution calendar |
| `settings` | per-user settings (e.g. last job description and score) |
| `api_cache` | raw HTTP responses + ETags |
| `cache_meta` | when each dataset was last refreshed |

The footer shows load time, GitHub calls, 304 hits and remaining rate limit, so the cache's effect is visible. **↻ Refresh from GitHub** bypasses the cache.

## How the Match % is calculated

1. A dictionary of ~35 technologies with aliases (e.g. `react, react.js, next.js` → React) maps each tech to the GitHub languages that evidence it. Frameworks map to their language, so *Django* is satisfied by Python code and *React* by JavaScript/TypeScript.
2. Each technology found in the JD gets a credit:
   - **1.0 matched**: a mapped language is ≥ 5% of the user's code
   - **0.6 partial**: the language is present but small, or the tech appears in repo topics/descriptions
   - **0 missing**
3. **Match % = average credit × 100**. Labels: Strong ≥ 75, Good ≥ 50, Partial ≥ 25, Low below that.

Forked repos are excluded so the score reflects the developer's own code.

## Tech stack

| Layer | Tools |
|---|---|
| Backend | Python, FastAPI, httpx, SQLite |
| Frontend | React 18 (Vite), Recharts |
| Data | GitHub REST + GraphQL APIs |
| LLM (optional) | Gemini / Groq / OpenAI |
| Tests | pytest with a mocked GitHub API |

## Setup

### 1. Backend
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # Windows: copy .env.example .env
```
Edit `backend/.env`:
- `GITHUB_TOKEN`: a classic personal access token with the `read:user` scope (GitHub → Settings → Developer settings → Personal access tokens). Required for the contribution graph and higher rate limits.
- `DEFAULT_GITHUB_USER`: the profile to open by default.
- `LLM_PROVIDER` (`gemini` / `groq` / `openai` / `none`) and `LLM_API_KEY`: optional, for the AI features.

Run it:
```bash
uvicorn app.main:app --reload --port 8000
```
API docs: http://localhost:8000/docs

### 2. Frontend
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173. The dev server proxies `/api` to the backend.

### 3. Tests
```bash
cd backend
pytest
```

## API

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/profile/{login}` | Header data: user, stats, top languages, cache info |
| GET | `/api/repos/{login}` | Repo cards (`sort`, `include_forks`) |
| GET | `/api/contributions/{login}` | Daily contributions + streaks |
| POST | `/api/match` | `{login, job_description}` → Match % and breakdown |
| POST | `/api/chat` | `{login, message, history}` → portfolio chatbot reply |
| POST | `/api/gap-coach` | `{login, job_description}` → gap analysis, project ideas, pitch |
| GET/PUT | `/api/settings/{login}` | User settings stored in SQLite |
| POST | `/api/refresh/{login}` | Invalidate the cache for a user |
| GET | `/api/cache/{login}` | Cache age, API calls, 304 hits, rate limit |

All `GET` data endpoints accept `?refresh=true` to bypass the cache.

## Project structure

```
backend/
  app/
    main.py                FastAPI app and routers
    config.py              environment settings
    db.py                  SQLite schema
    cache.py               TTL + ETag cache and settings storage
    github_client.py       REST + GraphQL client
    services/
      sync.py              get-or-fetch: SQLite first, GitHub when stale
      profile.py           total stars, top languages, streaks
      tech_dict.py         tech keyword → language dictionary
      match.py             Tech Stack Compatibility score
      llm.py               Gemini / Groq / OpenAI client
      portfolio_context.py cached portfolio snapshot for the LLM
      chatbot.py           Ask my Portfolio
      gap_coach.py         JD Gap Coach
    routers/               portfolio, match, assistant, settings
  tests/                   pytest suite with a mocked GitHub API
frontend/
  src/
    App.jsx
    api.js
    components/            ProfileHeader, ContributionGraph, RepoGrid,
                           MatchPanel (+ MatchBadge), ChatPanel, GapCoach
```
