from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_chat_allowed_contract():
    r = client.post("/chat", json={
        "messages": [{"role": "user", "content": "quero cancelar plano"}]
    })
    assert r.status_code == 200
    body = r.json()
    assert "blocked" in body
    assert "output" in body
    assert "rails" in body
