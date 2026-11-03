// Thin wrapper around the FastAPI backend.
async function request(path, options = {}) {
  const res = await fetch(`/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail || detail;
    } catch {}
    throw new Error(detail);
  }
  return res.json();
}

export const api = {
  health: () => request("/health"),
  profile: (login, refresh = false) => request(`/profile/${login}?refresh=${refresh}`),
  repos: (login) => request(`/repos/${login}?include_forks=true`),
  contributions: (login, refresh = false) => request(`/contributions/${login}?refresh=${refresh}`),
  refresh: (login) => request(`/refresh/${login}`, { method: "POST" }),
  cache: (login) => request(`/cache/${login}`),
  getSettings: (login) => request(`/settings/${login}`),
  saveSettings: (login, values) =>
    request(`/settings/${login}`, { method: "PUT", body: JSON.stringify(values) }),
  match: (login, jobDescription) =>
    request(`/match`, { method: "POST", body: JSON.stringify({ login, job_description: jobDescription }) }),
  chat: (login, message, history = []) =>
    request(`/chat`, { method: "POST", body: JSON.stringify({ login, message, history }) }),
  gapCoach: (login, jobDescription) =>
    request(`/gap-coach`, { method: "POST", body: JSON.stringify({ login, job_description: jobDescription }) }),
};

// GitHub's official-ish language colours for tags and the pie chart.
export const LANGUAGE_COLORS = {
  Python: "#3572A5", JavaScript: "#f1e05a", TypeScript: "#3178c6", Java: "#b07219",
  "C++": "#f34b7d", C: "#555555", "C#": "#178600", Go: "#00ADD8", Rust: "#dea584",
  Ruby: "#701516", PHP: "#4F5D95", Swift: "#F05138", Kotlin: "#A97BFF", Dart: "#00B4AB",
  HTML: "#e34c26", CSS: "#563d7c", SCSS: "#c6538c", Shell: "#89e051",
  "Jupyter Notebook": "#DA5B0B", R: "#198CE7", MATLAB: "#e16737", Scala: "#c22d40",
  Vue: "#41b883", Svelte: "#ff3e00", Dockerfile: "#384d54", SQL: "#e38c00",
  Other: "#8b949e",
};

export const langColor = (lang) => LANGUAGE_COLORS[lang] || "#8b949e";
