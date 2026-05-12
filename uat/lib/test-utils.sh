#!/bin/bash
# ============================================================
# Luceon2026 — 测试公共工具函数
#
# 用途：为压力测试和故障注入脚本提供公共函数
# 依赖：curl、jq
# 用法：在脚本中 source uat/lib/test-utils.sh
# ============================================================

# 颜色代码（与 smoke-test.sh 一致）
GREEN="\033[32m"
RED="\033[31m"
YELLOW="\033[33m"
CYAN="\033[36m"
RESET="\033[0m"

# 默认环境变量
BASE_URL="${BASE_URL:-http://127.0.0.1:8081}"
DEFAULT_POLL_INTERVAL="${POLL_INTERVAL:-15}"
DEFAULT_MAX_WAIT_MINUTES="${MAX_WAIT_MINUTES:-60}"

# ── 输出辅助 ─────────────────────────────────────────────────

print_separator() {
  echo -e "${CYAN}============================================================${RESET}"
}

color_pass() {
  echo -e "${GREEN}✓ $*${RESET}"
}

color_fail() {
  echo -e "${RED}✗ $*${RESET}"
}

color_warn() {
  echo -e "${YELLOW}⚠ $*${RESET}"
}

color_info() {
  echo -e "${CYAN}$*${RESET}"
}

# ── 依赖检查 ─────────────────────────────────────────────────

check_dependency_health() {
  local max_attempts="${1:-30}"
  local interval="${2:-2}"
  local attempt=0

  while [[ $attempt -lt $max_attempts ]]; do
    local resp
    resp=$(curl -s --max-time 10 --connect-timeout 5 "${BASE_URL}/__proxy/upload/ops/dependency-health" 2>/dev/null || echo '{}')
    local ok
    ok=$(echo "$resp" | jq -r '.ok // false' 2>/dev/null)
    local blocking
    blocking=$(echo "$resp" | jq -r 'if .blocking == null then true else .blocking end' 2>/dev/null)

    if [[ "$ok" == "true" && "$blocking" == "false" ]]; then
      return 0
    fi

    sleep "$interval"
    attempt=$((attempt + 1))
  done

  return 1
}

check_admission_circuit() {
  local resp
  resp=$(curl -s --max-time 10 --connect-timeout 5 "${BASE_URL}/__proxy/upload/ops/mineru/admission-circuit" 2>/dev/null || echo '{}')
  local open
  open=$(echo "$resp" | jq -r 'if .open == null then true else .open end' 2>/dev/null)

  if [[ "$open" == "false" ]]; then
    return 0
  else
    return 1
  fi
}

# ── 任务操作 ─────────────────────────────────────────────────

submit_pdf() {
  local pdf_path="$1"
  local resp
  resp=$(curl -s --max-time 30 --connect-timeout 10 \
    -F "file=@${pdf_path}" \
    "${BASE_URL}/__proxy/upload/tasks" 2>/dev/null || echo '{}')

  local task_id
  task_id=$(echo "$resp" | jq -r '.taskId // .id // ""' 2>/dev/null)

  if [[ -z "$task_id" || "$task_id" == "null" ]]; then
    echo ""
    return 1
  fi

  echo "$task_id"
  return 0
}

submit_markdown() {
  local md_path="$1"
  local resp
  resp=$(curl -s --max-time 30 --connect-timeout 10 \
    -F "file=@${md_path}" \
    "${BASE_URL}/__proxy/upload/tasks" 2>/dev/null || echo '{}')

  local task_id
  task_id=$(echo "$resp" | jq -r '.taskId // .id // ""' 2>/dev/null)

  if [[ -z "$task_id" || "$task_id" == "null" ]]; then
    echo ""
    return 1
  fi

  echo "$task_id"
  return 0
}

get_all_tasks() {
  curl -s --max-time 10 --connect-timeout 5 "${BASE_URL}/__proxy/db/tasks" 2>/dev/null || echo '[]'
}

get_task_by_id() {
  local task_id="$1"
  curl -s --max-time 10 --connect-timeout 5 "${BASE_URL}/__proxy/db/tasks/${task_id}" 2>/dev/null || echo '{}'
}

get_task_events() {
  local task_id="$1"
  curl -s --max-time 10 --connect-timeout 5 "${BASE_URL}/__proxy/db/task-events?taskId=${task_id}" 2>/dev/null || echo '[]'
}

# ── 状态轮询 ─────────────────────────────────────────────────

poll_until_terminal() {
  local task_ids=("$@")
  local max_seconds=$((DEFAULT_MAX_WAIT_MINUTES * 60))
  local poll_interval="${DEFAULT_POLL_INTERVAL}"
  local elapsed=0

  if [[ ${#task_ids[@]} -eq 0 ]]; then
    echo "[]"
    return 1
  fi

  local terminal_states='completed|review-pending|failed|canceled|skipped-canceled'

  while [[ $elapsed -lt $max_seconds ]]; do
    sleep "$poll_interval"
    elapsed=$((elapsed + poll_interval))

    local all_tasks
    all_tasks=$(get_all_tasks)

    # 统计这些 taskIds 中不在终态的数量
    local active_count=0
    local terminal_results='[]'

    for tid in "${task_ids[@]}"; do
      local state
      state=$(echo "$all_tasks" | jq -r ".[] | select(.id == \"${tid}\") | .state // \"unknown\"" 2>/dev/null)
      if [[ -z "$state" || "$state" == "null" ]]; then
        state="unknown"
      fi

      if ! echo "$state" | grep -qE "^(${terminal_states})$"; then
        active_count=$((active_count + 1))
      fi
    done

    # 检查停止条件
    # 1. 准入电路打开
    if ! check_admission_circuit 2>/dev/null; then
      echo "CIRCUIT_OPEN"
      return 2
    fi

    # 2. 全部终态
    if [[ $active_count -eq 0 ]]; then
      echo "$all_tasks"
      return 0
    fi

    # 3. 超时
    if [[ $elapsed -ge $max_seconds ]]; then
      echo "TIMEOUT"
      return 3
    fi

    # 进度提示
    local completed
    completed=$(echo "$all_tasks" | jq '[.[] | select(.state == "completed" or .state == "review-pending")] | length' 2>/dev/null || echo 0)
    local total_tracked=${#task_ids[@]}
    echo -e "${CYAN}  [${elapsed}s] 活跃: ${active_count}/${total_tracked}, 完成: ${completed}${RESET}" >&2
  done

  echo "TIMEOUT"
  return 3
}

# ── 基线任务数 ───────────────────────────────────────────────

get_baseline_count() {
  local all_tasks
  all_tasks=$(get_all_tasks)
  echo "$all_tasks" | jq 'length' 2>/dev/null || echo 0
}

# ── 一致性审计 ───────────────────────────────────────────────

run_consistency_audit() {
  curl -s --max-time 10 --connect-timeout 5 "${BASE_URL}/__proxy/upload/audit/consistency" 2>/dev/null || echo '{"ok":false,"findings":["audit_failed"]}'
}

# ── MinerU submit-probe 连续验证 ─────────────────────────────

run_submit_probe_check() {
  local count="${1:-3}"
  local passed=0
  local failed=0
  local probe_times=()

  echo -e "${CYAN}  MinerU submit-probe 连续验证 (${count} 次):${RESET}" >&2

  for ((i=1; i<=count; i++)); do
    local start_time
    start_time=$(python3 -c 'import time; print(int(time.time()*1000))' 2>/dev/null || echo 0)

    local resp
    resp=$(curl -s --max-time 20 --connect-timeout 10 \
      "${BASE_URL}/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true" 2>/dev/null || echo '{}')

    local end_time
    end_time=$(python3 -c 'import time; print(int(time.time()*1000))' 2>/dev/null || echo 0)
    local duration_ms=$((end_time - start_time))
    probe_times+=("${duration_ms}ms")

    local ok
    ok=$(echo "$resp" | jq -r '.dependencies.mineru.submitProbe.ok // false' 2>/dev/null)

    if [[ "$ok" == "true" ]]; then
      printf "    %-40s ${GREEN}PASS${RESET} (%dms)\n" "第 ${i}/${count} 次 probe" "$duration_ms" >&2
      passed=$((passed + 1))
    else
      printf "    %-40s ${RED}FAIL${RESET} (%dms)\n" "第 ${i}/${count} 次 probe" "$duration_ms" >&2
      failed=$((failed + 1))
    fi
  done

  echo -e "${CYAN}  结果: ${GREEN}${passed} 通过${RESET} / ${RED}${failed} 失败${RESET} (共 ${count} 次)${RESET}" >&2
  echo ""

  if [[ $failed -gt 0 ]]; then
    return 1
  fi
  return 0
}

# ── Ollama keep-alive 检查 ───────────────────────────────────

check_ollama_status() {
  local resp
  resp=$(curl -s --max-time 10 --connect-timeout 5 "${BASE_URL}/__proxy/upload/ops/dependency-health" 2>/dev/null || echo '{}')

  local ollama_healthy
  ollama_healthy=$(echo "$resp" | jq -r '.dependencies.ollama // "unknown"' 2>/dev/null)
  local ollama_warm
  ollama_warm=$(echo "$resp" | jq -r '.dependencies.ollama_warm // false' 2>/dev/null)

  echo "${ollama_healthy}|${ollama_warm}"
}

# ── 耗时统计 ─────────────────────────────────────────────────

compute_percentiles() {
  local times=("$@")
  local sorted
  IFS=$'\n' sorted=($(printf '%s\n' "${times[@]}" | sort -n))
  unset IFS

  local count=${#sorted[@]}
  if [[ $count -eq 0 ]]; then
    echo "0|0|0"
    return
  fi

  local p50_idx=$((count * 50 / 100))
  local p95_idx=$((count * 95 / 100))
  [[ $p50_idx -ge $count ]] && p50_idx=$((count - 1))
  [[ $p95_idx -ge $count ]] && p95_idx=$((count - 1))
  [[ $p50_idx -lt 0 ]] && p50_idx=0
  [[ $p95_idx -lt 0 ]] && p95_idx=0

  echo "${sorted[$p50_idx]}|${sorted[$p95_idx]}|${sorted[$((count - 1))]}"
}
