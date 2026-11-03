import { useState } from "react";

/** Extra feature 2: JD Gap Coach results. */
export default function GapCoach({ data, loading, error, onClose }) {
  const [copied, setCopied] = useState(false);
  if (!data && !loading && !error) return null;

  const advice = data?.advice;
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(advice.pitch);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {}
  };

  return (
    <section className="card coach">
      <div className="section-head">
        <h2>✨ JD Gap Coach</h2>
        <div className="row tight">
          {data && <span className="pill">{data.source === "llm" ? "AI generated" : "rule-based"}</span>}
          <button className="ghost" onClick={onClose}>Close</button>
        </div>
      </div>
      {loading && <p className="muted">Analysing the gap between this role and the portfolio…</p>}
      {error && <p className="error-text">{error}</p>}
      {advice && (
        <div className="coach-grid">
          <p className="coach-summary">{advice.summary}</p>

          <div>
            <h3>Strengths</h3>
            <ul>{(advice.strengths || []).map((s, i) => <li key={i}>{s}</li>)}</ul>
            {!advice.strengths?.length && <p className="muted">No strong overlaps found.</p>}
          </div>

          <div>
            <h3>Gaps</h3>
            <ul>
              {(advice.gaps || []).map((g, i) => (
                <li key={i}><strong>{g.skill}</strong>: <span className="muted">{g.why_it_matters}</span></li>
              ))}
            </ul>
            {!advice.gaps?.length && <p className="muted">No gaps. This portfolio covers the role.</p>}
          </div>

          <div className="full">
            <h3>Projects to close the gap</h3>
            <div className="ideas">
              {(advice.project_ideas || []).map((p, i) => (
                <div key={i} className="idea">
                  <strong>{p.title}</strong>
                  <p>{p.description}</p>
                  <div className="chips">{(p.skills || []).map((s) => <span key={s} className="chip mid">{s}</span>)}</div>
                </div>
              ))}
            </div>
          </div>

          {advice.pitch && (
            <div className="full">
              <h3>Tailored pitch</h3>
              <blockquote>{advice.pitch}</blockquote>
              <button className="ghost" onClick={copy}>{copied ? "Copied ✓" : "Copy pitch"}</button>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
