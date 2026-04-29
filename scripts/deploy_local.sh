#!/usr/bin/env bash
set -euo pipefail
kubectl apply -k k8s
kubectl rollout status deployment/guardrails-api -n guardrails
