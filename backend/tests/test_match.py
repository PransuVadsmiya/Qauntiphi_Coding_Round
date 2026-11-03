from fastapi.testclient import TestClient

from app.main import app
from app.services.match import compute_match, extract_technologies
from app.services import sync

client = TestClient(app)


def test_extract_handles_aliases_and_symbols():
    jd = "We need Python, Django, React.js, C++ and C# (.NET) with PostgreSQL. Spring Boot is a plus."
    techs = extract_technologies(jd)
    for t in ["Python", "Django", "React", "C++", "C#", "SQL", "Spring"]:
        assert t in techs, t


def test_no_false_positives_on_common_words():
    techs = extract_technologies("You will go to meetings and review our roadmap regularly.")
    assert "Go" not in techs and "R" not in techs


def test_match_scoring(fake_github):
    sync.ensure_repos("octocat")   # Python + TypeScript code cached
    res = compute_match("octocat", "Looking for Python, Django, React and Rust developers.")
    status = {t["technology"]: t["status"] for t in res["technologies"]}
    assert status["Python"] == "matched"
    assert status["Django"] == "matched"     # Django -> Python
    assert status["React"] == "matched"      # React -> TypeScript
    assert status["Rust"] == "missing"
    assert res["match_percent"] == 75
    assert res["label"] == "Strong match"


def test_partial_credit_for_small_language_share(fake_github):
    sync.ensure_repos("octocat")   # HTML is 500 of 17500 bytes ~2.9%
    res = compute_match("octocat", "Strong HTML and CSS skills needed")
    assert res["technologies"][0]["status"] in ("matched", "partial")


def test_match_endpoint_saves_last_score(fake_github):
    r = client.post("/api/match", json={"login": "octocat", "job_description": "Python and Go backend engineer"})
    assert r.status_code == 200
    assert r.json()["match_percent"] == 50
    saved = client.get("/api/settings/octocat").json()
    assert saved["last_match_percent"] == 50
