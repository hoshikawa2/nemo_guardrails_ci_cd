import os
from pathlib import Path
from fastapi import FastAPI
from pydantic import BaseModel
from nemoguardrails import LLMRails, RailsConfig

from src.deterministic_rails import mask_pii, detectar_toxicidade, detectar_out_of_scope

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config"

os.environ.setdefault("OPENAI_API_KEY", "sk-fake")

config = RailsConfig.from_path(str(CONFIG_PATH))
rails = LLMRails(config)

app = FastAPI(title="Guardrails API", version="1.0.0")

class ChatRequest(BaseModel):
    messages: list[dict]

@app.get("/health")
def health():
    return {"status": "ok", "config_path": str(CONFIG_PATH)}

@app.post("/chat")
def chat(payload: ChatRequest):
    user_text = ""
    for msg in reversed(payload.messages):
        if msg.get("role") == "user":
            user_text = msg.get("content", "")
            break

    pii = mask_pii(user_text)
    tox = detectar_toxicidade(user_text)
    scope = detectar_out_of_scope(user_text)

    blocked = not tox.allowed
    if blocked:
        return {
            "blocked": True,
            "reason": tox.reason,
            "rails": [pii.__dict__, tox.__dict__, scope.__dict__],
            "output": "Mensagem bloqueada por política de segurança."
        }

    # Para demo CI/CD, evitamos depender de chamada real ao LLM.
    # Em produção, troque para rails.generate(...).
    output = f"Solicitação recebida e validada: {pii.sanitized_text}"

    return {
        "blocked": False,
        "reason": "Allowed",
        "rails": [pii.__dict__, tox.__dict__, scope.__dict__],
        "output": output
    }
