"""Tech Stack Compatibility score.

Compares technology keywords in a job description against the languages in
the user's CACHED repositories (repo_languages table, no live API call).

Scoring per JD technology (all weighted equally):
  1.0  strong match   - a mapped language makes up >= STRONG_SHARE of the user's code
  0.6  partial match  - a mapped language is present but small, OR the tech
                        appears in a repo's topics / name / description
  0.0  missing
Match % = sum(credits) / number of JD technologies * 100
"""
import re

from . import sync
from .tech_dict import build_patterns

STRONG_SHARE = 0.05   # 5% of total code bytes
PARTIAL_CREDIT = 0.6
_PATTERNS = build_patterns()


def _alias_regex(alias: str) -> re.Pattern:
    # Word boundaries that still work for aliases like "c++", "c#", ".net", "node.js".
    return re.compile(r"(?<![\w+#.])" + re.escape(alias) + r"(?![\w+#])", re.IGNORECASE)


_COMPILED = [(canon, _alias_regex(alias), langs) for canon, alias, langs in _PATTERNS]
# Single letters / very short aliases need exact case to avoid false hits ("ml" is fine, "R" is not).
_CASE_SENSITIVE = {"go": re.compile(r"\bGo\b"), "r": re.compile(r"\bR\b")}


def extract_technologies(text: str) -> dict[str, list[str]]:
    """Return {canonical tech: mapped languages} found in the text."""
    found: dict[str, list[str]] = {}
    for canon, rx, langs in _COMPILED:
        if canon not in found and rx.search(text):
            found[canon] = langs
    if "Go" not in found and _CASE_SENSITIVE["go"].search(text):
        found["Go"] = ["Go"]
    if "R" not in found and _CASE_SENSITIVE["r"].search(text):
        found["R"] = ["R"]
    return found


def _label(pct: int) -> str:
    if pct >= 75:
        return "Strong match"
    if pct >= 50:
        return "Good match"
    if pct >= 25:
        return "Partial match"
    return "Low match"


def compute_match(login: str, job_description: str) -> dict:
    lang_bytes = sync.cached_language_bytes(login)
    repos = [r for r in sync.cached_repos(login) if not r["is_fork"]]
    total = sum(lang_bytes.values()) or 1
    share = {lang: b / total for lang, b in lang_bytes.items()}

    techs = extract_technologies(job_description)
    if not techs:
        return {
            "match_percent": 0, "label": "No tech keywords found", "technologies": [],
            "matched": [], "partial": [], "missing": [], "user_languages": list(lang_bytes),
        }

    breakdown, credit_sum = [], 0.0
    for tech, langs in techs.items():
        best_lang = max(langs, key=lambda l: share.get(l, 0))
        lang_share = share.get(best_lang, 0)
        tech_l = tech.lower()
        evidence_repos = [
            r["name"] for r in repos
            if r["language"] in langs
            or tech_l in [t.lower() for t in r["topics"]]
            or tech_l in r["name"].lower()
            or tech_l in (r["description"] or "").lower()
        ][:5]

        if lang_share >= STRONG_SHARE:
            status, credit = "matched", 1.0
            reason = f"{best_lang} is {lang_share:.0%} of your code"
        elif lang_share > 0 or evidence_repos:
            status, credit = "partial", PARTIAL_CREDIT
            reason = (f"{best_lang} is only {lang_share:.1%} of your code" if lang_share > 0
                      else "mentioned in your repo topics or descriptions")
        else:
            status, credit = "missing", 0.0
            reason = "no evidence in your repositories"

        credit_sum += credit
        breakdown.append({
            "technology": tech, "status": status, "credit": credit,
            "languages": langs, "reason": reason, "repos": evidence_repos,
        })

    pct = round(100 * credit_sum / len(techs))
    order = {"matched": 0, "partial": 1, "missing": 2}
    breakdown.sort(key=lambda b: (order[b["status"]], b["technology"]))
    return {
        "match_percent": pct,
        "label": _label(pct),
        "technologies": breakdown,
        "matched": [b["technology"] for b in breakdown if b["status"] == "matched"],
        "partial": [b["technology"] for b in breakdown if b["status"] == "partial"],
        "missing": [b["technology"] for b in breakdown if b["status"] == "missing"],
        "user_languages": list(lang_bytes),
    }
