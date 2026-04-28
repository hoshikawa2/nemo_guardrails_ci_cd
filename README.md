# CI/CD para Artefatos de Configuração no NeMo Guardrails

## Introdução

Em projetos que utilizam **NeMo Guardrails**, os principais artefatos não são apenas código, mas sim **configurações declarativas** que controlam o comportamento do LLM.

Isso muda completamente a abordagem de CI/CD.

---

## Tipos de Artefatos no NeMo

### 1. Configurações principais
- `config.yml` / `rails.yaml`
- `guardrails.yaml`
- `prompts/`
- `flows.co`
- `input.co`
- `output.co`

### 2. Código complementar
- Actions Python (`actions.py`)
- Integrações externas (APIs, tools)

---

## Problema Principal

Diferente de código tradicional:

- Pequenas mudanças em `.co` ou `.yaml` podem quebrar o comportamento
- Não há erro de compilação
- Falhas são **semânticas**, não sintáticas

---

## Pipeline CI/CD Recomendado

### Etapa 1: Validação Sintática

Validar YAML e estrutura:

```bash
yamllint .
```

Validar carregamento:

```python
from nemoguardrails import LLMRails, RailsConfig

config = RailsConfig.from_path("./config")
rails = LLMRails(config)
```

---

### Etapa 2: Testes de Guardrails (Unitários)

Criar cenários:

```python
tests = [
    {"input": "xingar atendente", "expected_blocked": True},
    {"input": "cancelar plano", "expected_blocked": False}
]
```

Executar:

```python
for t in tests:
    response = rails.generate(messages=[{"role": "user", "content": t["input"]}])
```

---

### Etapa 3: Testes de Regressão

Garantir que mudanças não quebram comportamento anterior.

- Snapshot de respostas
- Comparação antes/depois

---

### Etapa 4: Testes de Segurança (Guardrails)

Validar:

- Prompt injection
- Toxicidade
- Out-of-scope

---

### Etapa 5: Testes de Fluxo Completo (E2E)

Simular jornada real:

- Input → Guardrails → LLM → Tools → Output

---

## Estratégia de Versionamento

### Versionar separadamente:

- Código
- Configuração de guardrails

Exemplo:

```
/app
/config
/tests
```

---

## Deploy

### Opção 1: Embutido no container

```Dockerfile
COPY config/ /app/config/
```

### Opção 2: Config externo

- S3 / OCI Object Storage
- Volume mount

---

## Observabilidade no CI/CD

Integrar com:

- Logs estruturados
- Tracing (OpenTelemetry)
- Métricas de bloqueio

---

## Estratégia Avançada

### Feature Flags de Guardrails

Permitir ativar/desativar regras sem deploy.

---

## Anti-patterns

Evitar:

- Deploy direto sem testes
- Misturar lógica de negócio com guardrails
- Não versionar `.co`

---

## Conclusão

No NeMo Guardrails:

> CI/CD não é só sobre código, é sobre comportamento do agente.

É essencial tratar configurações como **artefatos críticos de software**.

## Referências

- [Tutorial: NeMo Guardrails com Python, Proxy OpenAI-Compatible e Tracing](https://github.com/hoshikawa2/nemo_guardrails_configuration)

## Acknowledgments

- **Author** - Cristiano Hoshikawa (Oracle LAD A-Team Solution Engineer)
