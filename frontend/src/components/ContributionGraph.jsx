import { useMemo, useState } from "react";

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** GitHub-style heatmap: 53 week columns x 7 day rows, coloured by intensity level 0-4. */
export default function ContributionGraph({ days, streaks }) {
  const [hover, setHover] = useState(null);

  const { weeks, monthLabels } = useMemo(() => {
    if (!days.length) return { weeks: [], monthLabels: [] };
    // Pad the start so the first column begins on Sunday.
    const first = new Date(days[0].date + "T00:00:00");
    const padded = [...Array(first.getDay()).fill(null), ...days];
    const weeks = [];
    for (let i = 0; i < padded.length; i += 7) weeks.push(padded.slice(i, i + 7));

    const monthLabels = [];
    let lastMonth = -1;
    weeks.forEach((w, i) => {
      const day = w.find(Boolean);
      if (!day) return;
      const m = new Date(day.date + "T00:00:00").getMonth();
      if (m !== lastMonth) {
        monthLabels.push({ index: i, label: MONTHS[m] });
        lastMonth = m;
      }
    });
    return { weeks, monthLabels };
  }, [days]);

  if (!days.length) {
    return (
      <section className="card">
        <h2>Contribution activity</h2>
        <p className="muted">No contribution data. Add a GITHUB_TOKEN to the backend .env to enable the heatmap.</p>
      </section>
    );
  }

  return (
    <section className="card">
      <div className="section-head">
        <h2>{streaks.total.toLocaleString()} contributions in the last year</h2>
        <div className="streak-pills">
          <span className="pill">🔥 Current streak: {streaks.current}d</span>
          <span className="pill">🏆 Longest: {streaks.longest}d</span>
          <span className="pill">📅 Active days: {streaks.active_days}</span>
        </div>
      </div>

      <div className="heatmap-scroll">
        <div className="heatmap">
          <div className="months" style={{ gridTemplateColumns: `repeat(${weeks.length}, 16px)` }}>
            {monthLabels.map((m) => (
              <span key={m.index} style={{ gridColumn: m.index + 1 }}>{m.label}</span>
            ))}
          </div>
          <div className="grid-wrap">
            <div className="weekdays">
              <span /> <span>Mon</span> <span /> <span>Wed</span> <span /> <span>Fri</span> <span />
            </div>
            <div className="grid">
              {weeks.map((w, wi) => (
                <div className="week" key={wi}>
                  {Array.from({ length: 7 }).map((_, di) => {
                    const d = w[di];
                    return d ? (
                      <div
                        key={di}
                        className={`cell l${d.level}`}
                        onMouseEnter={() => setHover(d)}
                        onMouseLeave={() => setHover(null)}
                        title={`${d.count} contributions on ${d.date}`}
                      />
                    ) : (
                      <div key={di} className="cell empty" />
                    );
                  })}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="heatmap-foot">
        <span className="muted">
          {hover ? `${hover.count} contribution${hover.count === 1 ? "" : "s"} on ${new Date(hover.date + "T00:00:00").toDateString()}` : "Hover a day for details"}
        </span>
        <span className="scale">
          Less {[0, 1, 2, 3, 4].map((l) => <span key={l} className={`cell l${l}`} />)} More
        </span>
      </div>
    </section>
  );
}
