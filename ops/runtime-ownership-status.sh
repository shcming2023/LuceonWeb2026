#!/bin/bash
set -u

ROOT="$(pwd)"
RUN_MINERU_SUBMIT_PROBE="${RUN_MINERU_SUBMIT_PROBE:-0}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --submit-probe)
      RUN_MINERU_SUBMIT_PROBE=1
      shift
      ;;
    --no-submit-probe)
      RUN_MINERU_SUBMIT_PROBE=0
      shift
      ;;
    --help|-h)
      cat <<'USAGE'
Usage: bash ops/runtime-ownership-status.sh [ROOT] [--submit-probe|--no-submit-probe]

Default behavior is read-only/no-submit. The MinerU submit-probe creates a
bounded synthetic MinerU task and may update the durable admission circuit; run
it only with explicit task/user authorization:

  RUN_MINERU_SUBMIT_PROBE=1 bash ops/runtime-ownership-status.sh
  bash ops/runtime-ownership-status.sh --submit-probe
USAGE
      exit 0
      ;;
    *)
      ROOT="$1"
      shift
      ;;
  esac
done

UPLOAD_BASE="${UPLOAD_BASE:-http://localhost:8081/__proxy/upload}"
MINERU_HEALTH_URL="${MINERU_HEALTH_URL:-http://127.0.0.1:8083/health}"
OLLAMA_BASE="${OLLAMA_BASE:-http://127.0.0.1:11434}"

echo "== Luceon production runtime ownership status =="
echo "timestamp=$(date '+%Y-%m-%dT%H:%M:%S%z')"
echo "cwd=$ROOT"

echo
echo "== git =="
git -C "$ROOT" status --short --branch 2>/dev/null || true
git -C "$ROOT" log -1 --oneline 2>/dev/null || true

echo
echo "== tmux sessions =="
tmux list-sessions 2>/dev/null || true
for session in mineru_api luceon-mineru luceon-sidecar luceon-supervisor; do
  if tmux has-session -t "$session" 2>/dev/null; then
    echo "$session=present"
  else
    echo "$session=absent"
  fi
done

echo
echo "== listeners =="
lsof -nP -iTCP:8081 -iTCP:8083 -iTCP:11434 -iTCP:19001 -sTCP:LISTEN 2>/dev/null || true

echo
echo "== docker compose services =="
(cd "$ROOT" && docker compose ps) 2>/dev/null || true

echo
echo "== upload-server env truth =="
docker inspect cms-upload-server --format '{{range .Config.Env}}{{println .}}{{end}}' 2>/dev/null \
  | grep -E '^(LOCAL_MINERU_ENDPOINT|OLLAMA_API_URL|OLLAMA_TIER2_MODEL|DISABLE_AI_SKELETON_FALLBACK|ALLOW_AI_SKELETON_FALLBACK|MINERU_LOG_PATH|MINERU_ERR_LOG_PATH)=' \
  || true

echo
echo "== upload health =="
curl -fsS --max-time 5 "$UPLOAD_BASE/health" 2>/dev/null || true
echo

echo
echo "== dependency health without MinerU submit probe (read-only) =="
curl -sS --max-time 15 "$UPLOAD_BASE/ops/dependency-health" 2>/dev/null || true
echo

echo
if [[ "$RUN_MINERU_SUBMIT_PROBE" == "1" || "$RUN_MINERU_SUBMIT_PROBE" == "true" || "$RUN_MINERU_SUBMIT_PROBE" == "yes" ]]; then
  echo "== MinerU submit probe (SIDE EFFECT: creates synthetic MinerU task and may update admission circuit) =="
  curl -sS --max-time 15 "$UPLOAD_BASE/ops/dependency-health?mineruSubmitProbe=true" 2>/dev/null || true
else
  echo "== MinerU submit probe skipped =="
  echo "RUN_MINERU_SUBMIT_PROBE=0; no synthetic MinerU task was created by this helper."
  echo "To run the side-effecting probe, use RUN_MINERU_SUBMIT_PROBE=1 or --submit-probe only when explicitly authorized."
fi
echo

echo
echo "== active task diagnostics =="
curl -sS --max-time 15 "$UPLOAD_BASE/ops/mineru/active-task" 2>/dev/null || true
echo

echo
echo "== MinerU log-channel ownership diagnostics =="
curl -sS --max-time 15 "$UPLOAD_BASE/ops/mineru/log-channel-ownership" 2>/dev/null || true
echo

echo
echo "== MinerU health =="
curl -sS --max-time 10 "$MINERU_HEALTH_URL" 2>/dev/null || true
echo

echo
echo "== Ollama version =="
curl -sS --max-time 10 "$OLLAMA_BASE/api/version" 2>/dev/null || true
echo

echo
echo "== Ollama loaded models =="
curl -sS --max-time 10 "$OLLAMA_BASE/api/ps" 2>/dev/null || true
echo
