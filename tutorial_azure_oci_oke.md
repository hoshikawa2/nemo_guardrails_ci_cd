# 🔐 Tutorial Completo — Configuração de Credenciais OCI no Azure DevOps (CI/CD com OKE)

## 📌 Introdução

Este documento descreve como configurar credenciais para integração entre:

- Azure DevOps (CI/CD)
- Oracle Cloud Infrastructure (OCI)
- OCI Registry (OCIR)
- Oracle Kubernetes Engine (OKE)
- OCI Vault

---

## 🧱 Arquitetura

Azure DevOps → Docker → OCIR → OKE → Aplicação

---

## ⚙️ ETAPA 1 — Variáveis no Azure DevOps

Pipeline → Variables ou Library → Variable Groups

Variáveis:

- OCIR_USER (secret)
- OCIR_PASSWORD (secret)
- OCIR_REGISTRY
- OCI_NAMESPACE
- OCIR_REPOSITORY
- OPENAI_API_KEY (secret)
- OKE_KUBECONFIG_B64 (secret)

---

## ☸️ ETAPA 2 — Kubernetes (OKE)

### Gerar kubeconfig

oci ce cluster create-kubeconfig \
  --cluster-id <OCID_CLUSTER> \
  --file kubeconfig \
  --region sa-saopaulo-1 \
  --token-version 2.0.0

### Converter para base64

base64 kubeconfig

Salvar em OKE_KUBECONFIG_B64

### Uso no pipeline

echo "$(OKE_KUBECONFIG_B64)" | base64 -d > ~/.kube/config

---

## 🐳 ETAPA 3 — OCIR

Gerar Auth Token no OCI

User → Auth Tokens

Pipeline:

echo "$(OCIR_PASSWORD)" | docker login "$(OCIR_REGISTRY)" \
  -u "$(OCIR_USER)" --password-stdin

---

## 🔐 ETAPA 4 — OCI Vault

Criar secret no OCI Vault

Security → Vault → Secrets

Criar Dynamic Group:

ALL {{resource.type = 'instance'}}

Criar Policy:

Allow dynamic-group <group> to read secret-bundles in compartment <compartment>

Buscar secret:

oci secrets secret-bundle get \
  --secret-id <OCID_SECRET> \
  --query "data.\"secret-bundle-content\".content" \
  --raw-output | base64 --decode

---

## 🔄 Pipeline exemplo

pip install -r requirements.txt
pytest -v
docker build
docker push
kubectl apply

---

## ⚠️ Boas práticas

- Não commitar secrets
- Usar variáveis secret
- Usar Vault para produção

---

## 🚀 Conclusão

Pipeline seguro com Azure DevOps + OCI + OKE.
