# DevFolio: GitHub Developer Portfolio

A personal-branding dashboard that visualizes a developer's GitHub activity, repository stats and coding streaks, scores how well their tech stack matches a job description, and lets recruiters chat with the portfolio.

Built for the Quantiphi Analytics vibe coding round.

## Requirements checklist

| Requirement from the problem statement | Status | Where it lives |
|---|---|---|
| **Contribution graph**: heatmap of daily coding activity, coloured by intensity | ✅ | `ContributionGraph.jsx`. 53 × 7 grid, 5 intensity levels from GitHub's quartiles, hover details, current/longest streak, active days |
| **Repository cards**: star count, fork count, language tag, short description | ✅ | `RepoGrid.jsx`. Also topics and last push; search, language filter, sort, show/hide forks |
| **Profile header**: follower count, total stars, "Top Languages" pie chart | ✅ | `ProfileHeader.jsx`. Total stars summed over original repos; donut chart weighted by bytes of code |
| **API integration**: GitHub REST/GraphQL | ✅ | `github_client.py`. REST for profile, repos, per-repo languages; GraphQL for the contribution calendar |
| **Caching engine**: SQLite caches repo metadata and user settings | ✅ | `db.py`, `cache.py`, `services/sync.py`. TTL + ETag cache; settings table stores repo view preferences and the last job description per user |
| **Vibe Check**: user inputs a job description | ✅ | `MatchPanel.jsx` |
| Backend compares JD keywords against the languages of the user's **cached** repositories | ✅ | `services/match.py` reads `repo_languages` from SQLite, with no GitHub call (covered by a test) |
| Generates a **"Match Percentage" badge at the top of the profile** | ✅ | `MatchBadge`, top-right of the profile header; shows a placeholder until a JD is scored |
| **Two extra chatbot-based features**, suggested and included | ✅ | Ask my Portfolio + JD Gap Coach (see below) |

## Core features

| Feature | Implementation |
|---|---|
| **Contribution graph** | GitHub-style heatmap of the last year, coloured by intensity level 0–4, with hover details, current streak, longest streak and active days |
| **Repository cards** | Stars, forks, language tag (GitHub colours), description, topics and last push; searchable, filterable by language, sortable, with a "Show forks" toggle. Your view preferences are saved in SQLite |
| **Profile header** | Avatar, bio, followers, **total stars** (summed over original repos, forks excluded), repo count (originals + forks shown separately), streaks, and a **Top Languages** donut chart weighted by bytes of code |
| **API integration** | GitHub **REST** + **GraphQL** |
| **Caching engine** | **SQLite** caches profile, repo metadata, languages, contributions and user settings (see below) |
| **Tech Stack Compatibility** | Paste a job description → backend extracts tech keywords and compares them with the languages in the **cached** repos → circular **Match %** badge at the top of the profile plus a per-technology breakdown. Matching repo cards are highlighted |

### "View profile" vs "Sync from GitHub"
- **View profile** loads the username in the search box. If that user was synced within the cache TTL (1 hour by default) everything is served from SQLite: instant, zero GitHub API calls.
- **↻ Sync from GitHub** ignores the cache and re-downloads the latest profile, repos, languages and contributions right now, then updates SQLite. Use it after pushing new code. "Last synced …" under the button shows how fresh the cached data is.

## Suggested extra features (chatbot capabilities)

The problem statement asks us to suggest and include two features beyond the spec. Both build on what chatbots are good at: answering free-form questions about a body of data, and turning analysis into tailored advice and writing.

### 1. 💬 Ask my Portfolio: a recruiter Q&A chatbot
**What it does:** A floating chat on the profile page. A recruiter can ask *"Has this developer worked with machine learning?"*, *"Which project best shows backend experience?"* or *"How active have they been recently?"* and get a short, specific answer naming repos, languages and numbers.

**Why we suggested it:** Recruiters skim. A portfolio page that answers their exact question turns a static page into a conversation, which is the core capability of a chatbot.

**How it works:** A small retrieval-augmented setup over our own cache. `portfolio_context.py` builds a compact snapshot (profile, language shares, streaks, every repo's language, stars, topics and description) from SQLite. That snapshot becomes the LLM's only context, with instructions to answer strictly from it and admit when the data doesn't show something, so answers stay grounded and cost zero GitHub API calls. Conversation history is kept so follow-up questions work. Each reply is tagged *AI* or *rule-based*.

### 2. ✨ JD Gap Coach: career advice from the match score
**What it does:** After a job description is scored, one click produces a fit summary, the developer's **strengths** for this role (with the repos that prove them), the **gaps** and why they matter, **2–3 concrete project ideas** to close them (ideally extending an existing repo), and a **tailored pitch** to send the recruiter, with a copy button.

**Why we suggested it:** The Match % says *how well* someone fits; the coach answers *what to do about it*. It turns a number into an action plan and a ready-to-send message: reasoning plus writing, which is what LLMs do best.

**How it works:** `gap_coach.py` sends the portfolio snapshot and the structured match breakdown to the LLM and asks for strict JSON (summary, strengths, gaps, project_ideas, pitch), which the UI renders as cards.

### Works with or without an LLM
Both features support **Gemini, Groq or OpenAI** (`LLM_PROVIDER` + `LLM_API_KEY` in `.env`). With no key, or if the LLM call fails, they fall back to rule-based logic: keyword/intent matching for the chatbot and templated advice and project ideas for the coach. The demo never breaks.

### Other ideas considered
- **AI README / bio writer** that drafts a profile README from the cached repos.
- **Repo-level "explain this project"** summaries for non-technical recruiters.
- **Weekly activity digest** summarising what changed since the last sync.

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
| Deployment | Docker, docker compose, nginx (reverse proxy for `/api`) |

## Setup

### Option A: Docker (one command)

The app is containerized as two services:

| Service | Image | What it does |
|---|---|---|
| `backend` | `python:3.12-slim` | FastAPI on port 8000, runs as a non-root user, with a health check on `/api/health`. The SQLite cache lives on the named volume `sqlite-cache`, so it survives restarts and rebuilds |
| `frontend` | multi-stage: `node:20-alpine` builds the React app → `nginx:1.27-alpine` serves it | nginx serves the static build and proxies `/api/*` to the backend container, so the browser talks to one origin (no CORS). Starts only after the backend is healthy |

```bash
cp backend/.env.example backend/.env      # Windows: copy backend\.env.example backend\.env
# put your GITHUB_TOKEN (and optionally LLM_API_KEY) in backend/.env
docker compose up --build
```
Open **http://localhost:8080**. API docs are at http://localhost:8000/docs.

Useful commands:
```bash
docker compose up -d --build     # run in the background
docker compose logs -f backend   # follow backend logs
docker compose down              # stop (cache volume is kept)
docker compose down -v           # stop and wipe the SQLite cache
```

`backend/.env` is optional for Docker: without it the app still starts, but the contribution graph needs `GITHUB_TOKEN` and the chatbot features fall back to rule-based answers.

### Option B: Run locally without Docker

#### 1. Backend
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

#### 2. Frontend
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173. The dev server proxies `/api` to the backend.

#### 3. Tests
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
docker-compose.yml       runs backend + frontend containers
backend/
  Dockerfile             python:3.12-slim, non-root, health check
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
  Dockerfile             node build stage → nginx serve stage
  nginx.conf             static files + /api proxy to the backend
  src/
    App.jsx
    api.js
    components/            ProfileHeader, ContributionGraph, RepoGrid,
                           MatchPanel (+ MatchBadge), ChatPanel, GapCoach
```
