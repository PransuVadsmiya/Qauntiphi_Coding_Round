"""SQLite connection and schema.

Tables
------
users          cached GitHub profile per username
repos          cached repository metadata (stars, forks, language, description...)
repo_languages bytes of code per language per repo (used for Top Languages + Match %)
contributions  one row per day of the contribution calendar
settings       user-level settings (key/value per username)
api_cache      raw HTTP cache keyed by URL: ETag + body, for conditional requests
cache_meta     when each dataset (profile/repos/contributions) was last refreshed
"""
import sqlite3
from contextlib import contextmanager

from .config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    login        TEXT PRIMARY KEY,
    name         TEXT,
    avatar_url   TEXT,
    bio          TEXT,
    location     TEXT,
    blog         TEXT,
    html_url     TEXT,
    followers    INTEGER DEFAULT 0,
    following    INTEGER DEFAULT 0,
    public_repos INTEGER DEFAULT 0,
    created_at   TEXT
);

CREATE TABLE IF NOT EXISTS repos (
    id           INTEGER PRIMARY KEY,
    owner        TEXT NOT NULL,
    name         TEXT NOT NULL,
    description  TEXT,
    html_url     TEXT,
    language     TEXT,
    stars        INTEGER DEFAULT 0,
    forks        INTEGER DEFAULT 0,
    topics       TEXT,            -- JSON array
    is_fork      INTEGER DEFAULT 0,
    pushed_at    TEXT,
    updated_at   TEXT
);
CREATE INDEX IF NOT EXISTS idx_repos_owner ON repos(owner);

CREATE TABLE IF NOT EXISTS repo_languages (
    repo_id   INTEGER NOT NULL,
    owner     TEXT NOT NULL,
    language  TEXT NOT NULL,
    bytes     INTEGER NOT NULL,
    PRIMARY KEY (repo_id, language)
);
CREATE INDEX IF NOT EXISTS idx_lang_owner ON repo_languages(owner);

CREATE TABLE IF NOT EXISTS contributions (
    login  TEXT NOT NULL,
    date   TEXT NOT NULL,
    count  INTEGER NOT NULL,
    level  INTEGER NOT NULL,      -- 0..4 intensity bucket
    PRIMARY KEY (login, date)
);

CREATE TABLE IF NOT EXISTS settings (
    login  TEXT NOT NULL,
    key    TEXT NOT NULL,
    value  TEXT,
    PRIMARY KEY (login, key)
);

CREATE TABLE IF NOT EXISTS api_cache (
    url         TEXT PRIMARY KEY,
    etag        TEXT,
    body        TEXT NOT NULL,
    fetched_at  REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS cache_meta (
    login       TEXT NOT NULL,
    dataset     TEXT NOT NULL,
    refreshed_at REAL NOT NULL,
    PRIMARY KEY (login, dataset)
);
"""


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


@contextmanager
def db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with db() as conn:
        conn.executescript(SCHEMA)
