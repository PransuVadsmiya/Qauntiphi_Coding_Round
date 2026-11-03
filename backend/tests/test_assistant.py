from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _chat(msg):
    r = client.post("/api/chat", json={"login": "octocat", "message": msg})
    assert r.status_code == 200
    return r.json()


def test_chat_rule_based_answers_without_llm(fake_github):
    assert _chat("What languages does this developer use?")["source"] == "rules"
    assert "Python" in _chat("What are their strongest skills?")["reply"]
    assert "ml-lab" in _chat("What is their most starred project?")["reply"]


def test_chat_answers_specific_technology(fake_github):
    reply = _chat("Has this developer used React or Rust?")["reply"]
    assert "React: yes" in reply and "web-app" in reply
    assert "Rust: no evidence" in reply


def test_gap_coach_fallback(fake_github):
    r = client.post("/api/gap-coach", json={"login": "octocat", "job_description": "Python, Docker and Go engineer"})
    assert r.status_code == 200
    body = r.json()
    assert body["source"] == "rules"
    gaps = [g["skill"] for g in body["advice"]["gaps"]]
    assert "Docker" in gaps and "Go" in gaps
    assert len(body["advice"]["project_ideas"]) == 2
    assert "Python" in body["advice"]["pitch"]
