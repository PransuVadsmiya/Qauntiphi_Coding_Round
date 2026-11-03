import { useMemo, useState } from "react";
import { langColor } from "../api";

function timeAgo(iso) {
  if (!iso) return "";
  const days = Math.floor((Date.now() - new Date(iso)) / 86400000);
  if (days < 1) return "today";
  if (days < 30) return `${days}d ago`;
  if (days < 365) return `${Math.floor(days / 30)}mo ago`;
  return `${Math.floor(days / 365)}y ago`;
}

export function RepoCard({ repo, highlighted }) {
  return (
    <a className={`card repo ${highlighted ? "highlight" : ""}`} href={repo.html_url} target="_blank" rel="noreferrer">
      <div className="repo-title">
        <span className="repo-name">{repo.name}</span>
        {repo.is_fork && <span className="pill">fork</span>}
      </div>
      <p className="repo-desc">{repo.description || <span className="muted">No description provided.</span>}</p>
      {repo.topics?.length > 0 && (
        <div className="topics">
          {repo.topics.slice(0, 4).map((t) => (
            <span key={t} className="topic">{t}</span>
          ))}
        </div>
      )}
      <div className="repo-meta">
        {repo.language && (
          <span className="lang-tag">
            <span className="dot" style={{ background: langColor(repo.language) }} />
            {repo.language}
          </span>
        )}
        <span title="Stars">★ {repo.stars}</span>
        <span title="Forks">⑂ {repo.forks}</span>
        <span className="muted">{timeAgo(repo.pushed_at)}</span>
      </div>
    </a>
  );
}

export default function RepoGrid({ repos, highlightLanguages = [] }) {
  const [sort, setSort] = useState("stars");
  const [query, setQuery] = useState("");
  const [lang, setLang] = useState("All");

  const languages = useMemo(
    () => ["All", ...new Set(repos.map((r) => r.language).filter(Boolean))],
    [repos]
  );

  const shown = useMemo(() => {
    const q = query.toLowerCase();
    const list = repos.filter(
      (r) =>
        (lang === "All" || r.language === lang) &&
        (!q || r.name.toLowerCase().includes(q) || (r.description || "").toLowerCase().includes(q))
    );
    const sorters = {
      stars: (a, b) => b.stars - a.stars,
      forks: (a, b) => b.forks - a.forks,
      updated: (a, b) => (b.pushed_at || "").localeCompare(a.pushed_at || ""),
      name: (a, b) => a.name.localeCompare(b.name),
    };
    return [...list].sort(sorters[sort]);
  }, [repos, sort, query, lang]);

  return (
    <section>
      <div className="section-head">
        <h2>Repositories <span className="muted">({shown.length})</span></h2>
        <div className="controls">
          <input placeholder="Search repos…" value={query} onChange={(e) => setQuery(e.target.value)} />
          <select value={lang} onChange={(e) => setLang(e.target.value)}>
            {languages.map((l) => <option key={l}>{l}</option>)}
          </select>
          <select value={sort} onChange={(e) => setSort(e.target.value)}>
            <option value="stars">Most stars</option>
            <option value="forks">Most forks</option>
            <option value="updated">Recently updated</option>
            <option value="name">Name</option>
          </select>
        </div>
      </div>
      <div className="repo-grid">
        {shown.map((r) => (
          <RepoCard key={r.id} repo={r} highlighted={highlightLanguages.includes(r.language)} />
        ))}
        {shown.length === 0 && <p className="muted">No repositories match.</p>}
      </div>
    </section>
  );
}
