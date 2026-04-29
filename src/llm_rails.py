from dataclasses import dataclass

@dataclass
class JudgeResult:
    allowed: bool
    score: int
    reason: str
    mechanism: str = "llm_judge"

def avaliar_qualidade_resposta(pergunta: str, resposta: str) -> JudgeResult:
    # Exemplo determinístico para CI.
    # Em ambiente real, pode chamar um LLM judge.
    score = 5 if len(resposta.strip()) > 30 else 3
    return JudgeResult(
        allowed=score >= 4,
        score=score,
        reason="Resposta avaliada por critério simplificado para CI.",
    )
