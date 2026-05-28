#!/usr/bin/env bash
set -euo pipefail

uvicorn app.main:app --reload &
API_PID=$!

cleanup() {
  kill "$API_PID" >/dev/null 2>&1 || true
}
trap cleanup EXIT

cd frontend
npm run dev
