#!/usr/bin/env bash
# Start AegisRAG on macOS with one command:   ./start-aegisrag.sh
#
# 1. gets the latest code from GitHub (never overwrites your local edits)
# 2. builds the Python environment (.venv, Python 3.12) if it is missing or broken
# 3. starts Qdrant in Docker if it is not already running
# 4. starts the backend on http://localhost:8000 (log: backend.log)
# 5. starts the frontend on http://localhost:3000   (Ctrl+C stops both)
set -euo pipefail
cd "$(dirname "$0")"
say() { printf "\n\033[1;36m==> %s\033[0m\n" "$1"; }

say "Getting the latest code"
git pull --ff-only || echo "(could not fast-forward; continuing with the code you have)"
git log --oneline -1

say "Python environment"
if ! .venv/bin/python -c "import fastapi, uvicorn, nltk, wordfreq" 2>/dev/null; then
  PY=$(command -v python3.12 || true)
  if [ -z "$PY" ]; then
    echo "Python 3.12 is needed. Install it with:  brew install python@3.12   then run this script again."
    exit 1
  fi
  echo "Rebuilding .venv with $PY (takes a few minutes the first time)"
  rm -rf .venv
  "$PY" -m venv .venv
  .venv/bin/python -m pip install --upgrade pip
  .venv/bin/python -m pip install -e ".[dev]"
fi
.venv/bin/python -c "from nltk.corpus import wordnet; wordnet.synsets('server')" 2>/dev/null || {
  .venv/bin/python -m pip install -q certifi
  SSL_CERT_FILE=$(.venv/bin/python -m certifi) .venv/bin/python -m nltk.downloader wordnet
}
echo "Python environment ready"

say "Qdrant (vector database)"
if curl -sf http://localhost:6333/collections >/dev/null; then
  echo "Qdrant is already running"
else
  docker start aegisrag-qdrant >/dev/null 2>&1 || \
    docker run -d --name aegisrag-qdrant -p 6333:6333 -v "$PWD/backend/qdrant_storage:/qdrant/storage" qdrant/qdrant >/dev/null
  for _ in $(seq 1 30); do curl -sf http://localhost:6333/collections >/dev/null && break; sleep 1; done
  curl -sf http://localhost:6333/collections >/dev/null || { echo "Qdrant did not start. Is Docker Desktop open?"; exit 1; }
  echo "Qdrant started"
fi

say "Backend (http://localhost:8000)"
OLD=$(lsof -ti tcp:8000 || true)
if [ -n "$OLD" ]; then echo "Stopping the old backend on port 8000"; kill $OLD || true; sleep 2; fi
(cd backend && ../.venv/bin/uvicorn app.main:app --port 8000 > ../backend.log 2>&1) &
BACKEND=$!
trap 'kill $BACKEND 2>/dev/null || true' EXIT
for _ in $(seq 1 60); do curl -sf http://localhost:8000/health >/dev/null && break; sleep 1; done
curl -sf http://localhost:8000/health >/dev/null || { echo "Backend did not start; see backend.log"; tail -20 backend.log; exit 1; }
echo "Backend running (log: backend.log)"

say "Frontend (http://localhost:3000)"
cd frontend-next
[ -d node_modules ] || npm ci
rm -rf .next
echo "Open http://localhost:3000 when it says Ready. Ctrl+C stops everything."
npm run dev
