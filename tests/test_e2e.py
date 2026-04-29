from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_e2e_toxicidade_bloqueada():
    r = client.post("/chat", json={
        "messages": [{"role": "user", "content": "vai se ferrar"}]
    })
    assert r.status_code == 200
    body = r.json()
    assert body["blocked"] is True

def test_e2e_pii_mascarado():
    r = client.post("/chat", json={
        "messages": [{"role": "user", "content": "Meu CPF é 169.323.728-86 e quero cancelar plano"}]
    })
    assert r.status_code == 200
    body = r.json()
    assert body["blocked"] is False
    assert "169.323.728-86" not in body["output"]
