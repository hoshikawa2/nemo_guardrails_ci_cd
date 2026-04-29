import re
from dataclasses import dataclass

@dataclass
class RailResult:
    allowed: bool
    reason: str = ""
    sanitized_text: str | None = None
    code: str | None = None
    mechanism: str = "deterministic"
    data: dict | None = None

def mask_pii(text: str) -> RailResult:
    cpf_pattern = r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b"
    sanitized = re.sub(cpf_pattern, "[CPF_MASCARADO]", text)
    return RailResult(
        allowed=True,
        reason="PII masked when present.",
        sanitized_text=sanitized,
        code="MSK",
        data={"pii_found": sanitized != text},
    )

def detectar_toxicidade(text: str) -> RailResult:
    toxic_terms = ["vai se ferrar", "idiota", "porcaria"]
    is_toxic = any(t in text.lower() for t in toxic_terms)
    return RailResult(
        allowed=not is_toxic,
        reason="Toxic content detected." if is_toxic else "No toxic content detected.",
        sanitized_text=text,
        code="TOX",
        data={"toxic": is_toxic},
    )

def detectar_out_of_scope(text: str) -> RailResult:
    allowed_terms = ["plano", "cancelar", "fatura", "serviço", "atendimento", "protocolo"]
    is_allowed = any(t in text.lower() for t in allowed_terms)
    return RailResult(
        allowed=is_allowed,
        reason="Out of scope." if not is_allowed else "In scope.",
        sanitized_text=text,
        code="OOS",
        data={"in_scope": is_allowed},
    )
