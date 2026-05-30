#!/usr/bin/env bash
set -euo pipefail

uvicorn app.main:app \
  --reload \
  --reload-dir agents \
  --reload-dir app \
  --reload-dir backend \
  --reload-dir config \
  --reload-dir context \
  --reload-dir database \
  --reload-dir evaluation \
  --reload-dir guardrails \
  --reload-dir llm_providers \
  --reload-dir memory \
  --reload-dir observability \
  --reload-dir prompts \
  --reload-dir skills \
  --reload-dir tools \
  --reload-dir workflows \
  --reload-exclude 'generated_projects/*' \
  --reload-exclude 'frontend/*' \
  --reload-exclude '.venv/*' &
API_PID=$!

cleanup() {
  kill "$API_PID" >/dev/null 2>&1 || true
}
trap cleanup EXIT

cd frontend
npm run dev
