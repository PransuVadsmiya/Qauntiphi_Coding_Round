import { useState } from "react";

const SAMPLE_JD = `We are hiring a Data Scientist / ML Engineer.
Requirements: strong Python, pandas, scikit-learn and PyTorch; SQL (PostgreSQL);
experience building REST APIs with FastAPI or Flask; Docker; familiarity with React is a plus.`;

export function badgeTone(pct) {
  if (pct >= 75) return "strong";
  if (pct >= 50) return "good";
  if (pct >= 25) return "partial";
  return "low";
}

/** Circular "Match %" badge shown at the top of the profile. */
export function MatchBadge({ result, loading, onClick }) {
  if (!result) {
    return (
      <button className="match-badge empty-badge" onClick={onClick} title="Paste a job description to score it">
        <svg width="64" height="64" viewBox="0 0 64 64" aria-hidden="true">
          <circle cx="32" cy="32" r="26" className="ring-bg" />
          <text x="32" y="37" textAnchor="middle">{loading ? "…" : "?"}</text>
        </svg>
        <span>
          <strong>{loading ? "Scoring…" : "Match %"}</strong>
          <small>Paste a job description</small>
        </span>
      </button>
    );
  }
  const pct = result.match_percent;
  const r = 26, c = 2 * Math.PI * r;
  return (
    <button className={`match-badge ${badgeTone(pct)}`} onClick={onClick} title="See the breakdown">
      <svg width="64" height="64" viewBox="0 0 64 64" aria-hidden="true">
        <circle cx="32" cy="32" r={r} className="ring-bg" />
        <circle
          cx="32" cy="32" r={r} className="ring"
          strokeDasharray={c} strokeDashoffset={c * (1 - pct / 100)}
          transform="rotate(-90 32 32)"
        />
        <text x="32" y="37" textAnchor="middle">{pct}%</text>
      </svg>
      <span>
        <strong>{result.label}</strong>
        <small>Tech Stack Compatibility</small>
      </span>
    </button>
  );
}

export default function MatchPanel({ jd, setJd, result, loading, error, onAnalyze, onCoach }) {
  const [open, setOpen] = useState(true);
  return (
    <section className="card" id="match-panel">
      <div className="section-head">
        <h2>🎯 Tech Stack Compatibility</h2>
        <button className="ghost" onClick={() => setOpen(!open)}>{open ? "Hide" : "Show"}</button>
      </div>
      {open && (
        <>
          <textarea
            rows={5}
            value={jd}
            onChange={(e) => setJd(e.target.value)}
            placeholder="Paste a job description here…"
          />
          <div className="row">
            <button onClick={onAnalyze} disabled={loading || jd.trim().length < 10}>
              {loading ? "Analyzing…" : "Calculate match"}
            </button>
            <button className="ghost" onClick={() => setJd(SAMPLE_JD)}>Use sample JD</button>
            {result && onCoach && (
              <button className="ghost" onClick={onCoach}>✨ Ask the Gap Coach</button>
            )}
          </div>
          {error && <p className="error-text">{error}</p>}

          {result && (
            <div className="breakdown">
              <div className="chips">
                {result.matched.map((t) => <span key={t} className="chip ok">✓ {t}</span>)}
                {result.partial.map((t) => <span key={t} className="chip mid">~ {t}</span>)}
                {result.missing.map((t) => <span key={t} className="chip bad">✗ {t}</span>)}
                {result.technologies.length === 0 && <span className="muted">No known technologies found in this text.</span>}
              </div>
              {result.technologies.length > 0 && (
                <table>
                  <thead>
                    <tr><th>Technology</th><th>Status</th><th>Why</th><th>Evidence</th></tr>
                  </thead>
                  <tbody>
                    {result.technologies.map((t) => (
                      <tr key={t.technology}>
                        <td>{t.technology}</td>
                        <td><span className={`chip ${t.status === "matched" ? "ok" : t.status === "partial" ? "mid" : "bad"}`}>{t.status}</span></td>
                        <td className="muted">{t.reason}</td>
                        <td className="muted">{t.repos.join(", ") || "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
              <p className="muted small">
                Score = average credit across the JD's technologies (full credit when a matching language is ≥5% of your code,
                partial when it's smaller or only mentioned in repo topics). Computed from the SQLite-cached repo languages.
              </p>
            </div>
          )}
        </>
      )}
    </section>
  );
}
