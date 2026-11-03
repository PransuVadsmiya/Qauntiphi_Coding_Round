import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import ChatPanel from "./components/ChatPanel";
import ContributionGraph from "./components/ContributionGraph";
import ErrorBoundary from "./components/ErrorBoundary";
import GapCoach from "./components/GapCoach";
import MatchPanel, { MatchBadge } from "./components/MatchPanel";
import ProfileHeader from "./components/ProfileHeader";
import RepoGrid from "./components/RepoGrid";

const EMPTY_STREAKS = { current: 0, longest: 0, total: 0, active_days: 0 };
const NO_COACH = { data: null, loading: false, error: "" };

function ago(seconds) {
  if (seconds == null) return "never";
  if (seconds < 60) return "just now";
  if (seconds < 3600) return `${Math.floor(seconds / 60)} min ago`;
  return `${Math.floor(seconds / 3600)} h ago`;
}

function cleanUsername(raw) {
  // Accept "PransuVadsmiya", "@PransuVadsmiya", "Pransu Vadsmiya" or a full profile URL.
  return (raw || "")
    .trim()
    .replace(/^https?:\/\/(www\.)?github\.com\//i, "")
    .replace(/^@/, "")
    .split(/[/?#]/)[0]
    .replace(/\s+/g, "");
}

export default function App() {
  const [login, setLogin] = useState("");
  const [input, setInput] = useState("");
  const [profile, setProfile] = useState(null);
  const [repos, setRepos] = useState([]);
  const [contrib, setContrib] = useState({ days: [], streaks: EMPTY_STREAKS });
  const [contribError, setContribError] = useState("");
  const [cacheInfo, setCacheInfo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [loadMs, setLoadMs] = useState(null);
  const [repoPrefs, setRepoPrefs] = useState({});

  const [jd, setJd] = useState("");
  const [match, setMatch] = useState(null);
  const [matchLoading, setMatchLoading] = useState(false);
  const [matchError, setMatchError] = useState("");
  const [coach, setCoach] = useState(NO_COACH);

  const runMatch = useCallback(async (user, text) => {
    setMatchLoading(true);
    setMatchError("");
    try {
      setMatch(await api.match(user, text));
    } catch (e) {
      setMatchError(e.message);
    } finally {
      setMatchLoading(false);
    }
  }, []);

  const runCoach = async () => {
    setCoach({ ...NO_COACH, loading: true });
    try {
      setCoach({ ...NO_COACH, data: await api.gapCoach(login, jd) });
    } catch (e) {
      setCoach({ ...NO_COACH, error: e.message });
    }
  };

  /**
   * View profile (refresh=false): served from the SQLite cache when it is
   * younger than the TTL, so it is instant and costs no GitHub calls.
   * Sync from GitHub (refresh=true): ignores the cache and re-downloads now.
   */
  const load = useCallback(async (user, refresh = false) => {
    if (!user) return;
    setLoading(true);
    setError("");
    setContribError("");
    const t0 = performance.now();
    try {
      const p = await api.profile(user, refresh);
      const r = await api.repos(user);
      setProfile(p);
      setRepos(r.repos);
      try {
        setContrib(await api.contributions(user, refresh));
      } catch (e) {
        setContrib({ days: [], streaks: EMPTY_STREAKS });
        setContribError(e.message);
      }
      setCacheInfo(await api.cache(user));
      setLogin(user);
      setLoadMs(Math.round(performance.now() - t0));
      try { localStorage.setItem("lastUser", user); } catch {}

      // Restore this user's settings from SQLite: repo view prefs + last job description.
      setMatch(null);
      setCoach(NO_COACH);
      const saved = await api.getSettings(user).catch(() => ({}));
      setRepoPrefs(saved.repo_prefs || {});
      if (saved.last_job_description) {
        setJd(saved.last_job_description);
        runMatch(user, saved.last_job_description);
      } else {
        setJd("");
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [runMatch]);

  // Open the last viewed user, or the backend's default user.
  useEffect(() => {
    (async () => {
      let start = "";
      try { start = localStorage.getItem("lastUser") || ""; } catch {}
      if (!start) {
        try { start = (await api.health()).default_user; } catch {}
      }
      start = cleanUsername(start);
      if (start) {
        setInput(start);
        load(start);
      }
    })();
  }, [load]);

  const submit = (e) => {
    e.preventDefault();
    const user = cleanUsername(input);
    setInput(user);
    load(user);
  };

  const updateRepoPrefs = (prefs) => {
    setRepoPrefs(prefs);
    api.saveSettings(login, { repo_prefs: prefs }).catch(() => {});
  };

  const scrollToMatch = () =>
    document.getElementById("match-panel")?.scrollIntoView({ behavior: "smooth", block: "start" });

  const syncedAgo = cacheInfo ? ago(cacheInfo.datasets?.repos) : null;

  return (
    <div className="app">
      <nav className="topbar">
        <span className="brand">◆ DevFolio</span>
        <form onSubmit={submit} className="search">
          <input value={input} onChange={(e) => setInput(e.target.value)} placeholder="GitHub username" />
          <button
            disabled={loading || !input.trim()}
            title="Show this user's portfolio. Uses the SQLite cache if it was synced within the last hour."
          >
            {loading ? "Loading…" : "View profile"}
          </button>
        </form>
        {login && (
          <div className="sync">
            <button
              className="ghost"
              onClick={() => load(login, true)}
              disabled={loading}
              title="Ignore the cache and download the latest data from GitHub now"
            >
              ↻ Sync from GitHub
            </button>
            <span className="muted small">Last synced {syncedAgo}</span>
          </div>
        )}
      </nav>

      <main>
        {error && <div className="alert">{error}</div>}
        {!profile && !loading && !error && (
          <div className="empty card">
            <h2>Build your developer portfolio</h2>
            <p className="muted">Enter a GitHub username above to load profile stats, repositories and contribution activity.</p>
          </div>
        )}

        {profile && (
          <>
            <ErrorBoundary name="Profile header">
              <ProfileHeader
                profile={profile}
                streaks={contrib.streaks}
                badge={<MatchBadge result={match} loading={matchLoading} onClick={scrollToMatch} />}
              />
            </ErrorBoundary>

            <ErrorBoundary name="Tech Stack Compatibility">
              <MatchPanel
                jd={jd}
                setJd={setJd}
                result={match}
                loading={matchLoading}
                error={matchError}
                onAnalyze={() => runMatch(login, jd)}
                onCoach={runCoach}
              />
            </ErrorBoundary>

            <ErrorBoundary name="Gap Coach">
              <GapCoach
                data={coach.data}
                loading={coach.loading}
                error={coach.error}
                onClose={() => setCoach(NO_COACH)}
              />
            </ErrorBoundary>

            <ErrorBoundary name="Contribution graph">
              {contribError ? (
                <section className="card"><h2>Contribution activity</h2><p className="muted">{contribError}</p></section>
              ) : (
                <ContributionGraph days={contrib.days} streaks={contrib.streaks} />
              )}
            </ErrorBoundary>

            <ErrorBoundary name="Repositories">
              <RepoGrid
                repos={repos}
                prefs={repoPrefs}
                onPrefsChange={updateRepoPrefs}
                highlightLanguages={
                  match ? match.technologies.filter((t) => t.status !== "missing").flatMap((t) => t.languages) : []
                }
              />
            </ErrorBoundary>
          </>
        )}
      </main>

      {profile && (
        <ErrorBoundary name="Portfolio chat">
          <ChatPanel login={login} />
        </ErrorBoundary>
      )}

      {cacheInfo && (
        <footer className="cache-bar">
          <span>⚡ Loaded in {loadMs} ms</span>
          <span>SQLite cache TTL {Math.round(cacheInfo.ttl_seconds / 60)} min</span>
          <span>GitHub calls this session: {cacheInfo.network_calls}</span>
          <span>304 Not Modified hits: {cacheInfo.not_modified_hits}</span>
          {cacheInfo.rate_limit_remaining != null && <span>Rate limit left: {cacheInfo.rate_limit_remaining}</span>}
        </footer>
      )}
    </div>
  );
}
