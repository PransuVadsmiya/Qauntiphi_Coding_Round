"""Application settings loaded from environment variables / .env file."""
import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")


class Settings:
    github_token: str = os.getenv("GITHUB_TOKEN", "").strip()
    default_user: str = "".join(os.getenv("DEFAULT_GITHUB_USER", "").split())

    llm_provider: str = os.getenv("LLM_PROVIDER", "none").strip().lower()
    llm_api_key: str = os.getenv("LLM_API_KEY", "").strip()
    llm_model: str = os.getenv("LLM_MODEL", "").strip()

    cache_ttl_seconds: int = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
    db_path: Path = BACKEND_DIR / os.getenv("DB_PATH", "portfolio_cache.db")

    @property
    def llm_enabled(self) -> bool:
        return self.llm_provider != "none" and bool(self.llm_api_key)


settings = Settings()
