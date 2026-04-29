# CI/CD para Agentes de IA com NeMo Guardrails como Package Python no Azure DevOps e Deploy em OCI OKE

## 1. Introdução

Este documento apresenta uma estratégia de CI/CD para projetos de **Agentes de IA** que consomem uma arquitetura compartilhada de **guardrails baseada em NeMo Guardrails**.

A referência técnica e conceitual deste material é o projeto:

> [Tutorial: NeMo Guardrails com Python, Proxy OpenAI-Compatible e Tracing
](https://github.com/hoshikawa2/nemo_guardrails_configuration)

A decisão arquitetural considerada neste documento é:

> O projeto NeMo Guardrails **não será implantado como um serviço/server separado**.  
> Ele será empacotado como uma **biblioteca Python versionada**, publicada por um pipeline próprio, e instalada pelos projetos de Agente de IA durante o build da imagem Docker.

Essa decisão reduz a complexidade operacional, preserva a cadência de desenvolvimento dos times de agentes e mantém a governança dos artefatos de guardrails por meio de versionamento, testes e controle de publicação no pipeline do projeto NeMo.

---

## 2. Visão geral da arquitetura

### 2.1 Fluxo funcional dos guardrails

```text
User Input
  ↓
Input Rails
  ├─ Regex: PII Masking
  ├─ LLM: Toxicidade
  └─ LLM: Out-of-Scope
  ↓
LLM principal via NeMo Guardrails
  ↓
Output Rails
  ├─ Compliance Anatel
  ├─ Verbalização Prematura
  └─ Groundedness
  ↓
Python Rules
  ├─ Alçada de Ajuste
  └─ Consistência Histórica
  ↓
Execução de API / Backend
  ↓
Supervisor VAS Avulso
  ↓
Curadoria / Métricas
  ├─ TCR
  ├─ Fallback
  ├─ Tokens
  ├─ Tamanho de mensagem
  └─ Eficiência RAG
  ↓
Resposta final
```

Esse fluxo representa a função do projeto NeMo dentro da arquitetura: ele atua como uma **camada de segurança, validação, controle de resposta, curadoria e métricas** para agentes de IA.

---

## 3. Decisão arquitetural: NeMo como package, não como serviço

### 3.1 Modelo descartado: NeMo como serviço central

Uma alternativa seria implantar o projeto NeMo como um serviço separado:

```text
Agente de IA
  ↓ HTTP
Serviço NeMo Guardrails
  ↓
LLM / Tools / Backend
```

Esse modelo centralizaria o runtime dos guardrails, mas traria custos e impactos:

- necessidade de manter um serviço adicional;
- aumento de latência;
- criação de dependência runtime entre agente e serviço de guardrails;
- maior complexidade de deploy;
- possível gargalo de aprovação e governança;
- risco de interromper a cadência dos times de desenvolvimento.

### 3.2 Modelo adotado: NeMo como biblioteca versionada

```text
Pipeline NeMo
  ↓
gera package Python versionado
  ↓
publica em um feed privado
  ↓
Pipeline Agente
  ↓
pip install company-nemo-guardrails==x.y.z
  ↓
build da imagem final do agente
  ↓
deploy no OCI OKE
```

No runtime, o Pod terá **um único container**, contendo:

```text
Pod Kubernetes
 └── Container do Agente
       ├── código do agente de IA
       ├── package NeMo Guardrails instalado
       ├── configs de guardrails
       ├── actions
       ├── deterministic rails
       └── llm rails
```

Portanto, o deploy no OKE é sempre da **imagem final do agente**, e não de uma imagem separada do NeMo.

---

## 4. Separação de responsabilidades

### 4.1 Projeto NeMo Guardrails

O projeto NeMo é responsável por:

- manter os artefatos de guardrails;
- implementar rails determinísticos;
- implementar rails baseados em LLM;
- registrar actions;
- manter prompts;
- manter catálogo de regras;
- executar testes unitários e de regressão;
- gerar package Python versionado;
- publicar o package em um feed privado.

### 4.2 Projeto Agente de IA

Cada projeto de Agente de IA é responsável por:

- implementar sua lógica conversacional;
- implementar integrações com APIs, backend, ferramentas e RAG;
- declarar a dependência do package NeMo;
- executar testes de integração com os guardrails;
- construir a imagem Docker final;
- publicar a imagem no OCIR;
- fazer deploy no OKE.

### 4.3 Azure DevOps

O Azure DevOps é responsável por orquestrar:

- pipeline do NeMo;
- pipeline dos agentes;
- publicação do package;
- build Docker;
- push para OCIR;
- deploy no OKE;
- controle de variáveis e secrets;
- permissões entre repositórios, feeds e pipelines.

---

## 5. Artefatos envolvidos no projeto NeMo

O projeto `nemo_guardrails_configuration` contém artefatos que devem ser tratados como componentes de uma biblioteca compartilhada.

Estrutura esperada:

```text
nemo_guardrails_tracing_project/
├── config/
│   ├── config.yml
│   ├── config.py
│   ├── guardrails.yaml
│   ├── guardrails_catalog.json
│   └── rails/
│       ├── input.co
│       └── output.co
├── src/
│   ├── app.py
│   ├── app_nemo.py
│   ├── actions.py
│   ├── deterministic_rails.py
│   ├── judges.py
│   ├── llm_client.py
│   ├── llm_rails.py
│   ├── models.py
│   ├── registry.py
│   └── prompts/
├── tests/
│   └── test_guardrails.py
├── scripts/
│   └── run_tests.sh
├── requirements.txt
├── pyproject.toml
├── .env.example
└── README.md
```

### 5.1 `config/config.yml`

Arquivo principal de configuração do NeMo Guardrails. Define modelos, engine, parâmetros, input rails, output rails e fluxos habilitados.

Em ambientes corporativos, o `engine: openai` pode apontar para um proxy OpenAI-compatible, inclusive um proxy interno para OCI Generative AI.

### 5.2 `config/rails/input.co`

Define fluxos de entrada, como PII, toxicidade, prompt injection, out-of-scope, bloqueio de intenção e normalização de input.

### 5.3 `config/rails/output.co`

Define fluxos de saída, como resposta segura, groundedness, ausência de vazamento de dados, aderência ao tom, compliance e prevenção de verbalização prematura.

### 5.4 `src/actions.py`

Arquivo de registro das actions expostas ao NeMo. Ele conecta os fluxos `.co` com funções Python.

### 5.5 `src/deterministic_rails.py`

Contém rails determinísticos, como máscara de CPF, validação de alçada, validação de protocolo, consistência entre valores e regras de negócio com retorno previsível.

### 5.6 `src/llm_rails.py`

Contém rails que dependem de LLM ou judge, como toxicidade, out-of-scope, groundedness, qualidade de resposta, tom de voz e avaliação semântica.

### 5.7 `src/judges.py`

Contém avaliadores usados para medir qualidade ou segurança das respostas.

### 5.8 `src/models.py`

Contém classes de retorno padronizadas, por exemplo:

```python
class RailResult:
    allowed: bool
    reason: str
    sanitized_text: str | None
    code: str
    mechanism: str
    data: dict
```

### 5.9 `src/registry.py`

Contém o registry dos guardrails, mapeando código da regra, nome, tipo, mecanismo, severidade e comportamento esperado.

### 5.10 `src/prompts/`

Contém prompts usados por rails baseados em LLM. Esses prompts devem ser tratados como artefatos sensíveis.

### 5.11 `tests/test_guardrails.py`

Contém a suíte de testes do projeto NeMo. O pipeline apenas executa os testes versionados no repositório.

### 5.12 `pyproject.toml`

Arquivo necessário para transformar o projeto NeMo em package Python instalável.

---

## 6. Segurança e governança dos artefatos NeMo

Como o projeto NeMo contém artefatos de segurança, ele deve ter governança própria.

### 6.1 O time do agente não deve ter acesso aos steps internos do pipeline NeMo

O time do agente deve consumir apenas o resultado aprovado:

```text
company-nemo-guardrails==1.2.0
```

Ele não precisa acessar YAML do pipeline NeMo, steps de teste, lógica de aprovação, scripts internos ou secrets do pipeline NeMo.

### 6.2 Permissões recomendadas no Azure DevOps

| Recurso | Time NeMo | Time Agente |
|---|---:|---:|
| Repo NeMo | Leitura/escrita | Sem acesso ou leitura restrita |
| Pipeline NeMo | Administração | Sem acesso |
| Feed do package | Publicação | Leitura |
| Repo Agente | Sem acesso ou leitura | Leitura/escrita |
| Pipeline Agente | Sem acesso ou leitura | Administração |
| Service Connection OCI/OKE | Uso controlado | Uso conforme necessidade |

### 6.3 Segurança por contrato

O contrato entre NeMo e Agente é o package.

```text
Package Python versionado = contrato técnico e de segurança
```

---

## 7. Fluxo de CI/CD completo

### 7.1 Pipeline do NeMo

```text
Commit no repo NeMo
  ↓
Pipeline NeMo
  ↓
instala dependências
  ↓
executa testes
  ↓
gera package Python
  ↓
publica no Azure Artifacts
```

### 7.2 Pipeline do Agente

```text
Commit no repo Agente
  ↓
Pipeline Agente
  ↓
instala dependências
  ↓
instala package NeMo
  ↓
executa testes do agente
  ↓
build Docker
  ↓
push OCIR
  ↓
deploy OKE
```

### 7.3 Quem chama quem?

Nenhum pipeline precisa chamar o outro diretamente. O acoplamento ocorre via package:

```text
Pipeline NeMo publica package
Pipeline Agente instala package
```

---

## 8. Criando o package Python do projeto NeMo

### 8.1 Estrutura sugerida

```text
nemo_guardrails_configuration/
├── company_nemo_guardrails/
│   ├── __init__.py
│   ├── config/
│   │   ├── config.yml
│   │   └── rails/
│   │       ├── input.co
│   │       └── output.co
│   ├── actions.py
│   ├── deterministic_rails.py
│   ├── llm_rails.py
│   ├── judges.py
│   ├── models.py
│   ├── registry.py
│   └── prompts/
├── tests/
├── pyproject.toml
└── README.md
```

### 8.2 Exemplo de `pyproject.toml`

```toml
[build-system]
requires = ["setuptools>=68", "wheel", "build"]
build-backend = "setuptools.build_meta"

[project]
name = "company-nemo-guardrails"
version = "1.0.0"
description = "Biblioteca corporativa de guardrails baseada em NeMo Guardrails"
requires-python = ">=3.11"
dependencies = [
  "nemoguardrails[openai]",
  "pydantic>=2",
  "httpx"
]

[tool.setuptools.packages.find]
where = ["."]

[tool.setuptools.package-data]
company_nemo_guardrails = [
  "config/*.yml",
  "config/**/*.co",
  "prompts/*.txt",
  "prompts/*.md",
  "*.json"
]
```

### 8.3 Função utilitária para carregar config do package

```python
from importlib.resources import files
from nemoguardrails import RailsConfig, LLMRails

def create_rails():
    config_path = files("company_nemo_guardrails").joinpath("config")
    config = RailsConfig.from_path(str(config_path))
    return LLMRails(config)
```

Uso no agente:

```python
from company_nemo_guardrails import create_rails

rails = create_rails()
```

---

## 9. Pipeline Azure DevOps do NeMo para publicar package

```yaml
trigger:
- main

pool:
  vmImage: 'ubuntu-latest'

variables:
  PYTHON_VERSION: '3.11'

steps:
- checkout: self

- task: UsePythonVersion@0
  inputs:
    versionSpec: '$(PYTHON_VERSION)'
  displayName: 'Use Python $(PYTHON_VERSION)'

- script: |
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    pip install build twine pytest
  displayName: 'Install dependencies'

- script: |
    export OPENAI_API_KEY="${OPENAI_API_KEY:-sk-fake}"
    pytest -v --junitxml=test-results.xml
  displayName: 'Run NeMo Guardrails tests'

- task: PublishTestResults@2
  inputs:
    testResultsFormat: 'JUnit'
    testResultsFiles: 'test-results.xml'
    failTaskOnFailedTests: true
  condition: succeededOrFailed()
  displayName: 'Publish test results'

- script: |
    python -m build
    ls -la dist
  displayName: 'Build Python package'

- task: TwineAuthenticate@1
  inputs:
    artifactFeed: 'company-python-feed'
  displayName: 'Authenticate Azure Artifacts feed'

- script: |
    python -m twine upload       --repository company-python-feed       --config-file $(PYPIRC_PATH)       dist/*
  displayName: 'Publish package to Azure Artifacts'
```

---

## 10. Projeto Agente consumindo o package NeMo

### 10.1 Estrutura do projeto Agente

```text
ai_agent_project/
├── app/
│   ├── main.py
│   └── agent.py
├── tests/
│   ├── test_agent.py
│   └── test_guardrails_integration.py
├── k8s/
│   ├── deployment.yaml
│   └── service.yaml
├── Dockerfile
├── requirements.txt
├── azure-pipelines.yml
└── README.md
```

### 10.2 `requirements.txt` do Agente

```txt
fastapi
uvicorn[standard]
company-nemo-guardrails==1.0.0
```

### 10.3 Uso no código do Agente

```python
from company_nemo_guardrails import create_rails

rails = create_rails()

def process_message(message: str):
    response = rails.generate(
        messages=[{"role": "user", "content": message}],
        options={"log": {"activated_rails": True}}
    )
    return response.output_text
```

---

## 11. Pipeline Azure DevOps do Agente

```yaml
trigger:
- main

pool:
  vmImage: 'ubuntu-latest'

variables:
  PYTHON_VERSION: '3.11'
  IMAGE_NAME: 'ai-agent'
  IMAGE_TAG: '$(Build.SourceVersion)'
  K8S_NAMESPACE: 'ai-agent'

steps:
- checkout: self

- task: UsePythonVersion@0
  inputs:
    versionSpec: '$(PYTHON_VERSION)'
  displayName: 'Use Python $(PYTHON_VERSION)'

- task: PipAuthenticate@1
  inputs:
    artifactFeeds: 'company-python-feed'
  displayName: 'Authenticate Python feed'

- script: |
    python -m pip install --upgrade pip
    pip install -r requirements.txt
  displayName: 'Install agent dependencies with NeMo package'

- script: |
    export OPENAI_API_KEY="${OPENAI_API_KEY:-sk-fake}"
    pytest -v --junitxml=test-results.xml
  displayName: 'Run agent tests'

- task: PublishTestResults@2
  inputs:
    testResultsFormat: 'JUnit'
    testResultsFiles: 'test-results.xml'
    failTaskOnFailedTests: true
  condition: succeededOrFailed()
  displayName: 'Publish test results'

- script: |
    IMAGE_URI="$(OCIR_REGISTRY)/$(OCI_NAMESPACE)/$(OCIR_REPOSITORY):$(IMAGE_TAG)"
    echo "##vso[task.setvariable variable=IMAGE_URI]$IMAGE_URI"
    docker build -t "$IMAGE_URI" .
  displayName: 'Build Docker image'

- script: |
    echo "$(OCIR_PASSWORD)" | docker login "$(OCIR_REGISTRY)"       -u "$(OCIR_USER)"       --password-stdin
    docker push "$(IMAGE_URI)"
  displayName: 'Push image to OCIR'

- script: |
    mkdir -p ~/.kube
    echo "$(OKE_KUBECONFIG_B64)" | base64 -d > ~/.kube/config
    chmod 600 ~/.kube/config

    kubectl apply -f k8s/namespace.yaml
    sed "s|REPLACE_IMAGE_URI|$(IMAGE_URI)|g" k8s/deployment.yaml | kubectl apply -f -
    kubectl apply -f k8s/service.yaml

    kubectl rollout status deployment/ai-agent -n $(K8S_NAMESPACE) --timeout=180s
  displayName: 'Deploy to OCI OKE'
```

---

## 12. Dockerfile do Agente

```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip     && pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

---

## 13. Variáveis e secrets no Azure DevOps

### 13.1 Variáveis do pipeline do Agente

| Variável | Exemplo | Tipo |
|---|---|---|
| `OCIR_REGISTRY` | `gru.ocir.io` | normal |
| `OCI_NAMESPACE` | `meunamespace` | normal |
| `OCIR_REPOSITORY` | `agents/ai-agent` | normal |
| `OCIR_USER` | `tenancy/user` | secret |
| `OCIR_PASSWORD` | auth token OCI | secret |
| `OKE_KUBECONFIG_B64` | kubeconfig em base64 | secret |
| `OPENAI_API_KEY` | chave ou fake/proxy | secret |

### 13.2 Variáveis do pipeline NeMo

| Variável | Exemplo | Tipo |
|---|---|---|
| `OPENAI_API_KEY` | `sk-fake` | secret |
| Feed credentials | gerenciado pelo Azure Artifacts | service/task |

---

## 14. OCI Vault

### 14.1 Papel do OCI Vault

O OCI Vault deve ser usado para proteger secrets em runtime:

- chaves de LLM;
- credenciais de API;
- tokens de backend;
- senhas de integração.

### 14.2 Estratégia simples

```text
Azure DevOps secret → Kubernetes Secret → Pod
```

### 14.3 Estratégia recomendada

```text
OCI Vault → External Secrets Operator / CSI Driver → Kubernetes Secret → Pod
```

Esse modelo evita manter secrets de runtime no Azure DevOps.

---

## 15. Segurança: impedindo acesso indevido ao pipeline NeMo

### 15.1 Separação de repositórios

```text
Repo NeMo        → time plataforma/guardrails
Repo Agente      → time aplicação/agente
```

### 15.2 Separação de pipelines

```text
Pipeline NeMo    → administrado pelo time NeMo
Pipeline Agente  → administrado pelo time Agente
```

### 15.3 Compartilhamento apenas do package

O time do agente recebe permissão de leitura no feed:

```text
company-python-feed
```

Ele não precisa acessar repo NeMo, pipeline NeMo, steps de teste, scripts internos ou secrets do NeMo.

---

## 16. Testes no modelo com package

### 16.1 Testes do NeMo

Executados no pipeline NeMo:

- testes determinísticos;
- testes de segurança;
- testes de regressão;
- testes de catálogo;
- testes de actions;
- testes de judge.

### 16.2 Testes do Agente

Executados no pipeline do agente:

- testes do código do agente;
- teste de carregamento do package NeMo;
- teste de integração mínima;
- teste E2E do fluxo conversacional;
- teste de contrato de API.

### 16.3 Exemplo

```python
def test_agent_uses_guardrails():
    from company_nemo_guardrails import create_rails

    rails = create_rails()
    assert rails is not None
```

---

## 17. Versionamento

Recomenda-se versionamento semântico:

```text
MAJOR.MINOR.PATCH
```

Exemplos:

```text
1.0.0
1.1.0
1.1.1
2.0.0
```

| Tipo de mudança | Versão |
|---|---|
| Correção sem mudança de comportamento esperado | PATCH |
| Nova regra compatível | MINOR |
| Mudança que pode bloquear novos casos | MINOR ou MAJOR |
| Mudança incompatível | MAJOR |

No agente:

```txt
company-nemo-guardrails==1.2.0
```

Ou aceitando patches:

```txt
company-nemo-guardrails~=1.2.0
```

---

## 18. Conclusão

A estratégia recomendada para este cenário é:

```text
NeMo Guardrails = package Python versionado
Agente de IA = aplicação final
Pipeline NeMo = publica package aprovado
Pipeline Agente = instala package, gera imagem e faz deploy
Runtime = um container com agente + guardrails
```

Esse modelo equilibra segurança, governança, velocidade, simplicidade operacional, reutilização entre múltiplos agentes e deploy único no OCI OKE.

A governança deixa de depender de um serviço central em runtime e passa a acontecer no ciclo de CI/CD, por meio de testes, versionamento, publicação controlada e permissões no feed de packages.
