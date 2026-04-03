#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"
FRONTEND_DIR="${ROOT_DIR}/frontend"

cleanup() {
  if [[ -n "${BACKEND_PID:-}" ]]; then
    kill "${BACKEND_PID}" >/dev/null 2>&1 || true
  fi
  if [[ -n "${FRONTEND_PID:-}" ]]; then
    kill "${FRONTEND_PID}" >/dev/null 2>&1 || true
  fi
}

trap cleanup EXIT

echo "Starting backend API on http://127.0.0.1:8000"
(
  cd "${BACKEND_DIR}"
  .venv/bin/python -m uvicorn recsys_prd.api.app:create_app --factory --host 127.0.0.1 --port 8000
) &
BACKEND_PID=$!

echo "Starting frontend Vite server on http://127.0.0.1:5173"
(
  cd "${FRONTEND_DIR}"
  npm run dev -- --host 127.0.0.1 --port 5173
) &
FRONTEND_PID=$!

echo "Backend PID: ${BACKEND_PID}"
echo "Frontend PID: ${FRONTEND_PID}"
echo "Use Ctrl+C to stop both processes."

wait "${BACKEND_PID}" "${FRONTEND_PID}"
