import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { langColor } from "../api";

function Stat({ label, value, hint }) {
  return (
    <div className="stat" title={hint}>
      <span className="stat-value">{value?.toLocaleString?.() ?? value}</span>
      <span className="stat-label">{label}</span>
    </div>
  );
}

export default function ProfileHeader({ profile, streaks, badge }) {
  const { user, stats, top_languages: langs } = profile;
  const forks = stats.forked_repos ?? 0;
  return (
    <section className="card header">
      {badge && <div className="header-badge">{badge}</div>}
      <div className="identity">
        <img className="avatar" src={user.avatar_url} alt={`${user.login} avatar`} />
        <div>
          <h1>{user.name || user.login}</h1>
          <a className="handle" href={user.html_url} target="_blank" rel="noreferrer">
            @{user.login}
          </a>
          {user.bio && <p className="bio">{user.bio}</p>}
          <div className="meta">
            {user.location && <span>📍 {user.location}</span>}
            {user.blog && (
              <a href={user.blog.startsWith("http") ? user.blog : `https://${user.blog}`} target="_blank" rel="noreferrer">
                🔗 {user.blog}
              </a>
            )}
          </div>
        </div>
      </div>

      <div className="stats">
        <Stat label="Followers" value={stats.followers} />
        <Stat label="Total stars" value={stats.total_stars} hint="Sum of stars across original repositories" />
        <Stat
          label={forks > 0 ? `Repos (+${forks} fork${forks === 1 ? "" : "s"})` : "Repos"}
          value={stats.original_repos ?? stats.public_repos}
          hint="Original repositories; forks are counted separately and excluded from stars and languages"
        />
        <Stat label="Current streak" value={`${streaks?.current ?? 0}d`} />
        <Stat label="Longest streak" value={`${streaks?.longest ?? 0}d`} />
      </div>

      <div className="languages">
        <h3>Top languages</h3>
        {langs.length === 0 ? (
          <p className="muted">No language data yet.</p>
        ) : (
          <div className="lang-body">
            <div className="pie">
              <ResponsiveContainer width="100%" height={170}>
                <PieChart>
                  <Pie data={langs} dataKey="bytes" nameKey="language" innerRadius={45} outerRadius={78} paddingAngle={2} stroke="none">
                    {langs.map((l) => (
                      <Cell key={l.language} fill={langColor(l.language)} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(_, name, item) => [`${item.payload.percent}%`, name]}
                    contentStyle={{ background: "var(--panel-2)", border: "1px solid var(--border)", borderRadius: 8, color: "var(--text)" }}
                    itemStyle={{ color: "var(--text)" }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <ul className="legend">
              {langs.map((l) => (
                <li key={l.language}>
                  <span className="dot" style={{ background: langColor(l.language) }} />
                  {l.language}
                  <span className="muted">{l.percent}%</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </section>
  );
}
