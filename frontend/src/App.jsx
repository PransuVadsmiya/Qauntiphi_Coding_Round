import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import ContributionGraph from "./components/ContributionGraph";
import ProfileHeader from "./components/ProfileHeader";
import RepoGrid from "./components/RepoGrid";

const EMPTY_STREAKS = { current: 0, longest: 0, total: 0, active_days: 0 };

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
      localStorage.setItem("lastUser", user);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  // Open the last viewed user, or the backend's default user.
  useEffect(() => {
    (async () => {
      let start = "";
      try { start = localStorage.getItem("lastUser") || ""; } catch {}
      if (!start) {
        try { start = (await api.health()).default_user; } catch {}
      }
      if (start) {
        setInput(start);
        load(start);
      }
    })();
  }, [load]);

  const submit = (e) => {
    e.preventDefault();
    load(input.trim());
  };

  return (
    <div className="app">
      <nav className="topbar">
        <span className="brand">◆ DevFolio</span>
        <form onSubmit={submit} className="search">
          <input value={input} onChange={(e) => setInput(e.target.value)} placeholder="GitHub username" />
          <button disabled={loading || !input.trim()}>{loading ? "Loading…" : "Load"}</button>
        </form>
        {login && (
          <button className="ghost" onClick={() => load(login, true)} disabled={loading} title="Bypass the SQLite cache">
            ↻ Refresh from GitHub
          </button>
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
            <ProfileHeader profile={profile} streaks={contrib.streaks} />
            {contribError ? (
              <section className="card"><h2>Contribution activity</h2><p className="muted">{contribError}</p></section>
            ) : (
              <ContributionGraph days={contrib.days} streaks={contrib.streaks} />
            )}
            <RepoGrid repos={repos} />
          </>
        )}
      </main>

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
