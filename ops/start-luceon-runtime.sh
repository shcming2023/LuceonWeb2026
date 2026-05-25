#!/bin/bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CMS_BASE_URL="${CMS_BASE_URL:-http://127.0.0.1:${CMS_PORT:-8081}}"
UPLOAD_BASE_URL="${UPLOAD_BASE_URL:-$CMS_BASE_URL/__proxy/upload}"
MINERU_HEALTH_URL="${MINERU_HEALTH_URL:-http://127.0.0.1:8083/health}"
MINERU_START_TIMEOUT_SEC="${MINERU_START_TIMEOUT_SEC:-120}"
DOCKER_START_TIMEOUT_SEC="${DOCKER_START_TIMEOUT_SEC:-90}"
DEPENDENCY_HEALTH_TIMEOUT_SEC="${DEPENDENCY_HEALTH_TIMEOUT_SEC:-60}"
HTTP_WAIT_INTERVAL_SEC="${HTTP_WAIT_INTERVAL_SEC:-2}"
ALLOW_DEGRADED_START="${ALLOW_DEGRADED_START:-0}"

echo "=== Luceon Runtime Startup ==="
echo "CMS base: $CMS_BASE_URL"
echo "MinerU health: $MINERU_HEALTH_URL"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Error: required command not found: $1" >&2
    exit 1
  fi
}

http_ok() {
  curl -fsS --max-time 5 "$1" >/dev/null 2>&1
}

wait_for_http() {
  local name="$1"
  local url="$2"
  local timeout_sec="$3"
  local started_at
  started_at="$(date +%s)"

  while true; do
    if http_ok "$url"; then
      echo "OK: $name is reachable ($url)"
      return 0
    fi

    if [ "$(( $(date +%s) - started_at ))" -ge "$timeout_sec" ]; then
      echo "Error: timed out waiting for $name ($url)" >&2
      return 1
    fi

    sleep "$HTTP_WAIT_INTERVAL_SEC"
  done
}

tmux_has_session() {
  tmux has-session -t "$1" >/dev/null 2>&1
}

restart_tmux_session() {
  local session="$1"
  local command="$2"

  tmux kill-session -t "$session" 2>/dev/null || true
  tmux new-session -d -s "$session" "$command"
}

ensure_mineru() {
  if http_ok "$MINERU_HEALTH_URL"; then
    if tmux_has_session luceon-mineru; then
      echo "OK: MinerU is already healthy and managed by tmux session luceon-mineru"
    else
      echo "OK: MinerU is already healthy; leaving existing process untouched"
    fi
    return 0
  fi

  if tmux_has_session luceon-mineru; then
    echo "MinerU health is down while luceon-mineru session exists; restarting managed session..."
  else
    echo "MinerU health is down; starting managed tmux session luceon-mineru..."
  fi

  restart_tmux_session luceon-mineru "cd '$REPO_ROOT' && bash ops/start-mineru-api.sh"
  wait_for_http "MinerU API" "$MINERU_HEALTH_URL" "$MINERU_START_TIMEOUT_SEC"
}

ensure_sidecar() {
  echo "Starting MinerU Log Observer in tmux session luceon-sidecar..."
  restart_tmux_session luceon-sidecar "cd '$REPO_ROOT' && UPLOAD_SERVER_URL='$UPLOAD_BASE_URL' MINERU_LOG_SOURCE_CONTEXT=host-filesystem MINERU_ERR_LOG_PATH=/Users/concm/ops/logs/mineru-api.err.log MINERU_LOG_PATH=/Users/concm/ops/logs/mineru-api.log node ops/mineru-log-observer.mjs"
}

ensure_supervisor() {
  echo "Starting Dependency Supervisor in tmux session luceon-supervisor..."
  restart_tmux_session luceon-supervisor "cd '$REPO_ROOT' && node ops/luceon-dependency-supervisor.mjs"
}

dependency_health_summary() {
  node -e '
let input = "";
process.stdin.on("data", chunk => input += chunk);
process.stdin.on("end", () => {
  const data = JSON.parse(input);
  const deps = data.dependencies || {};
  const summary = {
    ok: data.ok === true,
    blocking: data.blocking === true,
    minio: deps.minio?.ok === true,
    mineru: deps.mineru?.ok === true,
    ollama: deps.ollama?.ok === true,
  };
  console.log(JSON.stringify(summary));
  process.exit(summary.ok && !summary.blocking ? 0 : 1);
});
'
}

wait_for_dependency_health() {
  local health_url="$UPLOAD_BASE_URL/ops/dependency-health"
  local timeout_sec="$1"
  local started_at
  local body
  started_at="$(date +%s)"

  while true; do
    body="$(curl -fsS --max-time 15 "$health_url" 2>/dev/null || true)"
    if [ -n "$body" ]; then
      if printf '%s' "$body" | dependency_health_summary; then
        echo "OK: dependency-health is non-blocking ($health_url)"
        return 0
      fi
    fi

    if [ "$(( $(date +%s) - started_at ))" -ge "$timeout_sec" ]; then
      echo "Error: dependency-health remains blocking after startup ($health_url)" >&2
      if [ "$ALLOW_DEGRADED_START" = "1" ]; then
        echo "ALLOW_DEGRADED_START=1 set; continuing despite blocking dependency-health." >&2
        return 0
      fi
      return 1
    fi

    sleep "$HTTP_WAIT_INTERVAL_SEC"
  done
}

require_cmd curl
require_cmd docker
require_cmd tmux
require_cmd node

echo "[1/5] Starting Docker services (MinIO, DB, Upload Server, Frontend)..."
cd "$REPO_ROOT"
docker compose up -d
wait_for_http "CMS frontend/upload proxy" "$UPLOAD_BASE_URL/ops/dependency-health" "$DOCKER_START_TIMEOUT_SEC"

echo "[2/5] Detecting and starting MinerU API when needed..."
ensure_mineru

echo "[3/5] Starting support observers..."
ensure_sidecar
ensure_supervisor

echo "[4/5] Verifying dependency health without submit probe..."
wait_for_dependency_health "$DEPENDENCY_HEALTH_TIMEOUT_SEC"

echo "[5/5] Runtime dependency startup complete."
echo "=== All required startup dependencies are reachable. ==="
echo "Dependency health: $UPLOAD_BASE_URL/ops/dependency-health"
