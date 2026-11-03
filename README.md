# GitHub Developer Portfolio

A personal-branding dashboard that visualizes a developer's GitHub activity, repository stats and coding streaks, and scores how well their tech stack matches a job description.

Built for the Quantiphi Analytics vibe coding round.

## Features

**Core**
- **Profile header**: avatar, bio, follower count, total stars across repos, and a "Top Languages" pie chart
- **Contribution graph**: a GitHub-style heatmap of daily activity colored by intensity, with current and longest streaks
- **Repository cards**: stars, forks, primary language tag and description for each repo
- **Caching engine**: SQLite caches repo metadata, languages, contributions and user settings with a TTL and ETag-based conditional requests, so repeat loads are fast and barely touch the GitHub rate limit
- **Tech Stack Compatibility**: paste a job description and get a *Match %* badge at the top of the profile, computed from the languages in the cached repositories

**Extra (chatbot-powered)**
- **Ask my Portfolio**: a chatbot that answers questions about the developer using the cached repo data as context
- **JD Gap Coach**: explains the gap between a job description and the portfolio, and suggests projects to close it

## Tech stack

| Layer | Tools |
|---|---|
| Backend | FastAPI, httpx, SQLite |
| Frontend | React (Vite), Recharts |
| Data | GitHub REST + GraphQL APIs |
| LLM | Gemini / Groq / OpenAI (optional, with rule-based fallback) |

## Project structure

```
backend/
  app/
    main.py            FastAPI app and routers
    config.py          environment settings
    db.py              SQLite schema and connection
    github_client.py   REST + GraphQL client with ETag support
    cache.py           get-or-fetch cache with TTL
    services/          profile, match, tech dictionary, chatbot, gap coach
    routers/           HTTP endpoints
  tests/
frontend/
  src/components/      ProfileHeader, MatchBadge, ContributionGraph, RepoCard, ChatPanel, GapCoach
```

## Setup

_Setup instructions will be added as the backend and frontend are built._
