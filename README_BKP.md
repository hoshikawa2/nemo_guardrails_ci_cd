# CI/CD NeMo Guardrails no Azure DevOps com Deploy em OCI OKE

## Objetivo

Esta documentação tem por objetivo mostrar como implantar a estratégia de guardrails via Nemo Guardrails.
A idéia principal é que o projeto está baseado nesta especificação:

[Tutorial: NeMo Guardrails com Python, Proxy OpenAI-Compatible e Tracing](https://github.com/hoshikawa2/nemo_guardrails_configuration)

A arquitetura desta solução visa se integrar com soluções de agentes de IA com os guardrails do Nemo Guardrails.


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

Os detalhes da arquitetura podem ser vistas no material citado acima.

As aplicações agentes devem ser integradas a esta estrutura do projeto:

```text
ai_agent_project
├── src/
│   ...
nemo_guardrails_tracing_project/
├── config/
│   ├── config.yml : Arquivo de configuração para o Nemo Guardrail (Modelos, definições de rails de input e output)
│   ├── config.py : Registro das ações para os guardrails
│   ├── guardrails.yaml : Arquivo de mapeamento dos rails conforme definição da Planilha inicial (não utilizado pelo código)
│   ├── rails/
│   ├─────input.co : configuração de entrada dos fluxos Nemo 
│   ├─────output.co : configuração de saída dos fluxos Nemo 
│   └── guardrails_catalog.json
├── src/
│   ├── app.py : demo para consumir rails sem uso de Nemo Guardrails
│   ├── app_nemo.py : demo para consumir rails com uso de Nemo Guardrails
│   ├── actions.py : Arquivo de Actions expondo deterministic_rails e llm_rails
│   ├── deterministic_rails.py : rails deterministicos para serem utilizados como modelo na estrutura
│   ├── judges.py : estrutura demo para ilustrar judge
│   ├── llm_client.py : mockup para demo llm
│   ├── llm_rails.py : rails llm para serem utilizados como modelo na estrutura
│   ├── models.py : classe do modelo de resposta dos rails
│   ├── registry.py : modelo de registry do guardrail
│   └── prompts/ : pasta com os prompts para rails que utilizam llm
├── tests/
│   └── test_guardrails.py : código utilizado para pytest
├── scripts/
│   └── run_tests.sh : bash script para testar os rails individualmente via pytest
├── requirements.txt : bibliotecas necessárias para o projeto
├── .env.example : variáveis de ambiente para configuração
└── README.md
```

Portanto, trataremos aqui neste material a implantação da estrutura de **nemo_guardrails_tracing_project** juntamente com o projeto de **Agente de IA**.

Conceitualmente, teríamos este pipeline de deployment:

```text
Pipeline do Agente de IA
↓
aciona/consome
↓
Pipeline do projeto NeMo Guardrails
↓
publica pacote/artefato aprovado
↓
Pipeline do Agente usa somente o resultado
```

O pipeline do agente não vê nem controla os steps internos do NeMo. Ele só consome um artefato versionado/aprovado.

## Modelo recomendado

### 1. Pipeline separado do NeMo

No repositório nemo_guardrails_configuration, você cria um pipeline próprio que:

```text
checkout nemo
↓
instala dependências
↓
roda testes de guardrails
↓
gera pacote/artefato
↓
publica artifact ou package
```

- O NeMo NÃO publica uma imagem final para produção
- Ele publica um artefato reutilizável

Exemplo conceitual:

O alvo do deployment é um container dentro de um cluster Kubernetes. Portanto, a idéia é:

```text
Pod
 └── container único
        ├── código do agente
        ├── library do NeMo
        └── configs de guardrails
```

No modelo de library, teremos o seguinte:

```text
Pipeline NeMo
   ↓
gera artifact (ou package)
   ↓
-----------------------------------
Pipeline Agente
   ↓
baixa artifact do NeMo
   ↓
EMBUTE no build
   ↓
gera imagem FINAL
   ↓
deploy no OKE
```

**azure-pipelines-nemo.yml**
```yaml
trigger:
- main

pool:
vmImage: ubuntu-latest

steps:
- checkout: self

- task: UsePythonVersion@0
  inputs:
  versionSpec: '3.11'

- script: |
  python -m pip install --upgrade pip
  pip install -r requirements.txt
  pytest -v
  displayName: Test NeMo Guardrails

- script: |
  mkdir -p dist/nemo_guardrails_configuration
  cp -r config dist/nemo_guardrails_configuration/
  cp -r src dist/nemo_guardrails_configuration/
  cp requirements.txt dist/nemo_guardrails_configuration/
  displayName: Package NeMo artifacts

- publish: dist/nemo_guardrails_configuration
  artifact: nemo-guardrails-package
  displayName: Publish NeMo package
```
Esse pipeline é controlado pelo time responsável pelo NeMo.


A arquitetura foi pensada para um projeto de guardrails que não é uma aplicação final isolada, mas uma camada reutilizável consumida por várias soluções, agentes, bots, APIs e motores conversacionais.

---

## Arquitetura

```text
Azure DevOps
   |
   |-- checkout do repositório
   |-- instala Python 3.11
   |-- instala dependências
   |-- executa pytest
   |-- build Docker
   |-- push para OCIR
   |-- kubectl apply no OKE
   |
OCI OKE
   |
   |-- Deployment guardrails-api
   |-- Service guardrails-service
   |
Aplicações consumidoras
   |
   |-- HTTP POST /chat
```

---

## Estrutura de arquivos

```text
.
├── app/
│   ├── __init__.py
│   └── main.py
├── config/
│   ├── config.yml
│   ├── input.co
│   └── output.co
├── src/
│   ├── __init__.py
│   ├── actions.py
│   ├── deterministic_rails.py
│   └── llm_rails.py
├── tests/
│   ├── conftest.py
│   ├── test_api_contract.py
│   ├── test_e2e.py
│   └── test_structural.py
├── k8s/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── kustomization.yaml
├── scripts/
│   ├── build_local.sh
│   ├── deploy_local.sh
│   └── test_local.sh
├── azure-pipelines.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## O que é o `./config` no CI/CD?

No código NeMo Guardrails normalmente existe:

```python
from nemoguardrails import LLMRails, RailsConfig

config = RailsConfig.from_path("./config")
rails = LLMRails(config)
```

No Azure DevOps, o `./config` é o diretório `config/` versionado no repositório.

Quando o pipeline executa:

```yaml
- checkout: self
```

o repositório é baixado no agente do Azure DevOps. A partir daí, o diretório `config/` passa a existir no workspace do pipeline.

Para evitar problemas com diretório corrente, este projeto usa path absoluto relativo ao arquivo Python:

```python
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config"
```

Assim, funciona localmente, no pytest, no Docker e no OKE.

---

## Artefatos principais

### `config/config.yml`

Define o modelo principal usado pelo NeMo Guardrails.

Neste exemplo usamos `engine: openai` porque muitos frameworks esperam a interface OpenAI. Em ambientes reais, esse endpoint pode apontar para um proxy OpenAI-compatible, inclusive um proxy para OCI Generative AI.

### `config/input.co`

Define rails de entrada. Em um projeto real, aqui entram fluxos de validação de entrada, por exemplo:

- toxicidade
- prompt injection
- dados sensíveis
- fora de escopo

### `config/output.co`

Define rails de saída. Em um projeto real, aqui entram validações como:

- resposta segura
- resposta aderente ao contexto
- resposta sem vazamento de dados
- resposta sem alucinação

### `src/deterministic_rails.py`

Contém regras determinísticas. Exemplos:

- máscara de CPF
- validação de alçada
- checagem de protocolo
- normalização de texto

### `src/llm_rails.py`

Contém validações que podem depender de LLM ou judge. Exemplos:

- qualidade de resposta
- groundedness
- classificação semântica
- verificação de tom

### `src/actions.py`

Local para registrar actions usadas pelo NeMo Guardrails.

### `app/main.py`

Expõe a solução como uma API HTTP:

```text
GET  /health
POST /chat
```

Isso permite que várias soluções consumam a arquitetura central de guardrails.

---

## Execução local

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY=sk-fake
pytest -v
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

Teste:

```bash
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"quero cancelar plano"}]}'
```

---

## Docker local

```bash
docker build -t guardrails-api:local .
docker run --rm -p 8080:8080 -e OPENAI_API_KEY=sk-fake guardrails-api:local
```

---

## Variáveis necessárias no Azure DevOps

Configure estas variáveis no Pipeline ou em Variable Group:

| Variável | Exemplo | Observação |
|---|---|---|
| `OCIR_REGION_KEY` | `gru` ou `sa-saopaulo-1` | usado para montar registry |
| `OCIR_REGISTRY` | `gru.ocir.io` | endpoint OCIR |
| `OCI_NAMESPACE` | `meunamespace` | namespace Object Storage/OCIR |
| `OCIR_REPOSITORY` | `guardrails/guardrails-api` | repositório da imagem |
| `OCIR_USER` | `tenancy/user` | usuário OCIR |
| `OCIR_PASSWORD` | `***` | auth token OCI |
| `OKE_KUBECONFIG_B64` | `***` | kubeconfig em base64 |
| `OPENAI_API_KEY` | `sk-fake` | pode ser fake quando usar proxy |

---

## Como gerar o kubeconfig base64

Na sua máquina:

```bash
oci ce cluster create-kubeconfig \
  --cluster-id <OCID_DO_CLUSTER> \
  --file kubeconfig \
  --region sa-saopaulo-1 \
  --token-version 2.0.0

base64 -i kubeconfig | pbcopy
```

Cole o valor em `OKE_KUBECONFIG_B64` no Azure DevOps.

---

## Pipeline Azure DevOps

O arquivo `azure-pipelines.yml` faz:

1. Checkout.
2. Setup Python 3.11.
3. Instala dependências.
4. Executa testes.
5. Build da imagem Docker.
6. Login no OCIR.
7. Push da imagem.
8. Aplica manifests Kubernetes no OKE.
9. Aguarda rollout.

---

## Deploy no OKE

Os manifests estão em `k8s/`.

O pipeline substitui a imagem no deployment usando:

```bash
kubectl set image deployment/guardrails-api guardrails-api=$IMAGE_URI -n guardrails
```

---

## Testes

Os testes são versionados no repositório. O CI/CD não cria os testes; ele apenas executa.

Este pacote inclui:

- teste estrutural: valida carregamento do `RailsConfig`.
- teste de contrato da API: valida formato da requisição/resposta.
- teste E2E: simula entrada passando por API e rails.

---

## Considerações de produção

Para produção, recomenda-se evoluir:

- Secrets via Kubernetes Secret ou OCI Vault.
- Ingress Controller em vez de LoadBalancer direto.
- HPA para autoscaling.
- Logs estruturados.
- Tracing com OpenTelemetry.
- Separação de testes determinísticos e testes com LLM.
- Política de versionamento de imagem por commit SHA.
