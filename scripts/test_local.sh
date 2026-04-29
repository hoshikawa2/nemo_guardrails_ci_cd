#!/usr/bin/env bash
set -euo pipefail
export OPENAI_API_KEY=${OPENAI_API_KEY:-sk-fake}
pytest -v
