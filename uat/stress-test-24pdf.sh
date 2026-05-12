#!/bin/bash
# ============================================================
# Luceon2026 — 24-PDF 批量压力测试脚本
#
# 用途：验证系统在 24 个 PDF 批量提交下的稳定性和吞吐能力
# 依赖：curl、jq、python3
# 用法：
#   bash uat/stress-test-24pdf.sh
#   BASE_URL=http://192.168.31.33:8081 TEST_PDF_DIR=../testpdf bash uat/stress-test-24pdf.sh
#   CHECK_KEEPALIVE=true bash uat/stress-test-24pdf.sh
#
# 环境变量说明：
#   BASE_URL            - 目标服务地址（默认 http://127.0.0.1:8081）
#   TEST_PDF_DIR        - 样本 PDF 目录（默认 ../testpdf）
#   CONCURRENT_BATCH    - 每批并发数（默认 8）
#   BATCH_INTERVAL      - 批次间隔秒数（默认 10）
#   MAX_WAIT_MINUTES    - 最大等待分钟数（默认 60）
#   POLL_INTERVAL       - 状态轮询间隔秒（默认 15）
#   CHECK_KEEPALIVE     - 是否检查 Ollama keep-alive（默认 false）
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/test-utils.sh"

# 环境变量覆盖
BASE_URL="${BASE_URL:-http://127.0.0.1:8081}"
TEST_PDF_DIR="${TEST_PDF_DIR:-${SCRIPT_DIR}/../testpdf}"
CONCURRENT_BATCH="${CONCURRENT_BATCH:-8}"
BATCH_INTERVAL="${BATCH_INTERVAL:-10}"
MAX_WAIT_MINUTES="${MAX_WAIT_MINUTES:-60}"
POLL_INTERVAL="${POLL_INTERVAL:-15}"
CHECK_KEEPALIVE="${CHECK_KEEPALIVE:-false}"

TOTAL_PDFS=24
PASS=0
FAIL=0
TASK_IDS=()
TIMING_DATA=()

# ── 脚本头 ───────────────────────────────────────────────────

print_separator
echo -e "${CYAN}  Luceon2026 24-PDF 压力测试${RESET}"
echo -e "${CYAN}  目标地址：${BASE_URL}${RESET}"
echo -e "${CYAN}  样本目录：${TEST_PDF_DIR}${RESET}"
echo -e "${CYAN}  时间：$(date '+%Y-%m-%d %H:%M:%S')${RESET}"
if [[ "$CHECK_KEEPALIVE" == "true" ]]; then
  echo -e "${CYAN}  Ollama keep-alive 检查：已启用${RESET}"
fi
print_separator
echo ""

# ── 前置检查 ─────────────────────────────────────────────────

echo -e "${CYAN}【0】前置依赖检查${RESET}"

# jq
if ! command -v jq &>/dev/null; then
  color_fail "缺少 jq，请安装: brew install jq"
  exit 1
fi
color_pass "jq 可用"

# 样本目录
if [[ ! -d "$TEST_PDF_DIR" ]]; then
  color_fail "样本目录不存在: ${TEST_PDF_DIR}"
  exit 1
fi

# 统计 PDF 数量
PDF_COUNT=$(find "$TEST_PDF_DIR" -maxdepth 1 -name '*.pdf' -not -name '._*' 2>/dev/null | wc -l | tr -d ' ')
if [[ $PDF_COUNT -lt $TOTAL_PDFS ]]; then
  color_fail "PDF 样本不足 (需要 ${TOTAL_PDFS} 个，实际 ${PDF_COUNT} 个)"
  exit 1
fi
color_pass "PDF 样本充足 (${PDF_COUNT} 个)"
echo ""

# ── 1. 预检 ──────────────────────────────────────────────────

echo -e "${CYAN}【1】预检${RESET}"

# dependency-health
if check_dependency_health 60 3; then
  color_pass "dependency-health 全绿"
  PASS=$((PASS + 1))
else
  color_fail "dependency-health 未就绪"
  FAIL=$((FAIL + 1))
fi

# 准入电路（先于 submit-probe 检查，避免 probe 任务干扰电路状态）
if check_admission_circuit; then
  color_pass "准入电路已关闭"
  PASS=$((PASS + 1))
else
  color_fail "准入电路已打开"
  FAIL=$((FAIL + 1))
fi

# MinerU submit-probe（T-S07 集成，仅 1 次避免 MinerU 任务积压）
if run_submit_probe_check 1; then
  color_pass "MinerU submit-probe 通过"
  PASS=$((PASS + 1))
else
  color_fail "MinerU submit-probe 失败"
  FAIL=$((FAIL + 1))
fi

echo ""

# 如有预检失败，立即退出
if [[ $FAIL -gt 0 ]]; then
  color_fail "预检失败，终止测试"
  exit 1
fi

# ── 2. 获取基线 ──────────────────────────────────────────────

BASELINE_COUNT=$(get_baseline_count)
echo -e "${CYAN}【2】基线任务数：${BASELINE_COUNT}${RESET}"
echo ""

# ── Ollama keep-alive 初始状态 ───────────────────────────────

if [[ "$CHECK_KEEPALIVE" == "true" ]]; then
  echo -e "${CYAN}【2a】Ollama 初始状态${RESET}"
  OLLAMA_INITIAL=$(check_ollama_status)
  echo "  ollama 状态: $(echo "$OLLAMA_INITIAL" | cut -d'|' -f1) / warm: $(echo "$OLLAMA_INITIAL" | cut -d'|' -f2)"
  echo ""
fi

# ── 3. 批量提交 ──────────────────────────────────────────────

echo -e "${CYAN}【3】批量提交 (${TOTAL_PDFS} 个 PDF)${RESET}"

# 收集 PDF 文件列表
PDF_FILES=()
while IFS= read -r line; do
  PDF_FILES+=("$line")
done < <(find "$TEST_PDF_DIR" -maxdepth 1 -name '*.pdf' -not -name '._*' | head -n "$TOTAL_PDFS")

BATCHES=$(( (TOTAL_PDFS + CONCURRENT_BATCH - 1) / CONCURRENT_BATCH ))
SUBMIT_OK=0
SUBMIT_FAIL=0

for ((b=1; b<=BATCHES; b++)); do
  START_IDX=$(( (b - 1) * CONCURRENT_BATCH ))
  END_IDX=$(( START_IDX + CONCURRENT_BATCH - 1 ))
  [[ $END_IDX -ge $TOTAL_PDFS ]] && END_IDX=$((TOTAL_PDFS - 1))

  BATCH_TASK_IDS=()
  for ((i=START_IDX; i<=END_IDX; i++)); do
    pdf_path="${PDF_FILES[$i]}"
    task_id=$(submit_pdf "$pdf_path" || true)
    if [[ -n "$task_id" && "$task_id" != "null" ]]; then
      BATCH_TASK_IDS+=("$task_id")
      SUBMIT_OK=$((SUBMIT_OK + 1))
    else
      SUBMIT_FAIL=$((SUBMIT_FAIL + 1))
    fi
  done

  TASK_IDS+=("${BATCH_TASK_IDS[@]}")
  echo "  批次 ${b}/${BATCHES}: 提交 $((END_IDX - START_IDX + 1)) 个... ${GREEN}✓${RESET} (${#BATCH_TASK_IDS[@]}/$((END_IDX - START_IDX + 1)) 创建成功)"

  # 批次间隔
  if [[ $b -lt $BATCHES ]]; then
    sleep "$BATCH_INTERVAL"
  fi
done

echo "  总计：${SUBMIT_OK}/${TOTAL_PDFS} 任务创建成功"
echo ""

# ── 3a. 验证任务已全部创建 ──────────────────────────────────

CURRENT_COUNT=$(get_baseline_count)
EXPECTED_COUNT=$((BASELINE_COUNT + SUBMIT_OK))
if [[ $CURRENT_COUNT -ge $EXPECTED_COUNT ]]; then
  color_pass "任务数验证: ${CURRENT_COUNT} >= ${EXPECTED_COUNT}"
  PASS=$((PASS + 1))
else
  color_fail "任务数验证: ${CURRENT_COUNT} < ${EXPECTED_COUNT}"
  FAIL=$((FAIL + 1))
fi

# ── Ollama keep-alive 中期检查 ───────────────────────────────

if [[ "$CHECK_KEEPALIVE" == "true" ]]; then
  echo -e "${CYAN}【3a】Ollama 提交后状态${RESET}"
  OLLAMA_MID=$(check_ollama_status)
  echo "  ollama 状态: $(echo "$OLLAMA_MID" | cut -d'|' -f1) / warm: $(echo "$OLLAMA_MID" | cut -d'|' -f2)"
  echo ""
fi

# ── 4. 终态等待 ──────────────────────────────────────────────

echo -e "${CYAN}【4】终态等待 (最大 ${MAX_WAIT_MINUTES}min)${RESET}"

TERMINAL_STATES='completed|review-pending|failed|canceled|skipped-canceled'
MAX_SECONDS=$((MAX_WAIT_MINUTES * 60))
ELAPSED=0
STOP_REASON="all_terminal"
NO_PROGRESS_COUNT=0
PREVIOUS_TERMINAL=0

while [[ $ELAPSED -lt $MAX_SECONDS ]]; do
  sleep "$POLL_INTERVAL"
  ELAPSED=$((ELAPSED + POLL_INTERVAL))

  ALL_TASKS=$(get_all_tasks)

  ACTIVE=0
  COMPLETED=0
  REVIEW_PENDING=0
  TASK_FAILED=0
  CANCELED=0
  PROCESSING=0

  for tid in "${TASK_IDS[@]}"; do
    STATE=$(echo "$ALL_TASKS" | jq -r ".[] | select(.id == \"${tid}\") | .state // \"unknown\"" 2>/dev/null)
    if [[ -z "$STATE" || "$STATE" == "null" ]]; then
      STATE="unknown"
    fi

    case "$STATE" in
      completed)       COMPLETED=$((COMPLETED + 1)) ;;
      review-pending)  REVIEW_PENDING=$((REVIEW_PENDING + 1)) ;;
      failed)          TASK_FAILED=$((TASK_FAILED + 1)) ;;
      canceled|skipped-canceled) CANCELED=$((CANCELED + 1)) ;;
      *)               ACTIVE=$((ACTIVE + 1))
                       if [[ "$STATE" == "running" || "$STATE" == "ai-running" ]]; then
                         PROCESSING=$((PROCESSING + 1))
                       fi ;;
    esac
  done

  CURRENT_TERMINAL=$((COMPLETED + REVIEW_PENDING + TASK_FAILED + CANCELED))

  # 进度输出
  echo -e "  [${ELAPSED}s] ${ACTIVE} 个活跃: completed=${COMPLETED}, review-pending=${REVIEW_PENDING}, processing=${PROCESSING}, failed=${TASK_FAILED}, canceled=${CANCELED}"

  # Ollama keep-alive 周期性检查
  if [[ "$CHECK_KEEPALIVE" == "true" ]]; then
    OLLAMA_CYCLE=$(check_ollama_status)
    echo "           ollama: $(echo "$OLLAMA_CYCLE" | cut -d'|' -f1) / warm: $(echo "$OLLAMA_CYCLE" | cut -d'|' -f2)"
  fi

  # 停止条件 1: 全部终态
  if [[ $ACTIVE -eq 0 ]]; then
    STOP_REASON="all_terminal"
    break
  fi

  # 停止条件 2: 准入电路打开
  if ! check_admission_circuit 2>/dev/null; then
    STOP_REASON="circuit_open"
    echo -e "  ${RED}准入电路已打开，终止轮询${RESET}"
    break
  fi

  # 停止条件 3: dependency blocked
  DEP_RESP=$(curl -s --max-time 10 "${BASE_URL}/__proxy/upload/ops/dependency-health" 2>/dev/null || echo '{}')
  DEP_BLOCKING=$(echo "$DEP_RESP" | jq -r '.blocking // false' 2>/dev/null)
  if [[ "$DEP_BLOCKING" == "true" ]]; then
    BLOCKED=$(echo "$DEP_RESP" | jq -r '.dependencies | to_entries | map(select(.value != "ok")) | from_entries | keys | join(", ")' 2>/dev/null)
    echo -e "  ${RED}依赖阻塞: ${BLOCKED}${RESET}"
    STOP_REASON="dependency_blocked"
    break
  fi

  # 停止条件 4: 连续 3 轮无终态推进（且无活跃处理中的任务）
  if [[ $CURRENT_TERMINAL -le $PREVIOUS_TERMINAL ]]; then
    NO_PROGRESS_COUNT=$((NO_PROGRESS_COUNT + 1))
  else
    NO_PROGRESS_COUNT=0
  fi
  PREVIOUS_TERMINAL=$CURRENT_TERMINAL

  if [[ $NO_PROGRESS_COUNT -ge 12 && $PROCESSING -eq 0 ]]; then
    STOP_REASON="no_progress"
    echo -e "  ${YELLOW}连续 ${NO_PROGRESS_COUNT} 轮无终态推进且无活跃处理任务${RESET}"
    break
  fi
done

echo ""

# ── Ollama keep-alive 最终状态 ───────────────────────────────

if [[ "$CHECK_KEEPALIVE" == "true" ]]; then
  echo -e "${CYAN}【4a】Ollama keep-alive 最终报告${RESET}"
  OLLAMA_FINAL=$(check_ollama_status)
  OLLAMA_FINAL_HEALTHY=$(echo "$OLLAMA_FINAL" | cut -d'|' -f1)
  OLLAMA_FINAL_WARM=$(echo "$OLLAMA_FINAL" | cut -d'|' -f2)
  echo "  ollama 状态: ${OLLAMA_FINAL_HEALTHY}"
  echo "  warm 状态: ${OLLAMA_FINAL_WARM}"
  echo "  测试持续: ${ELAPSED}s ($((ELAPSED / 60))min)"
  if [[ "$OLLAMA_FINAL_HEALTHY" == "ok" ]]; then
    color_pass "Ollama keep-alive 状态正常"
  else
    color_warn "Ollama keep-alive 状态异常"
  fi
  echo ""
fi

# ── 5. 结果统计 ──────────────────────────────────────────────

echo -e "${CYAN}【5】结果统计${RESET}"

ALL_TASKS=$(get_all_tasks)
COMPLETED=0
REVIEW_PENDING=0
TASK_FAILED=0
CANCELED=0
ACTIVE=0
TASK_TIMES=()

for tid in "${TASK_IDS[@]}"; do
  TASK_INFO=$(echo "$ALL_TASKS" | jq ".[] | select(.id == \"${tid}\")" 2>/dev/null)

  if [[ -z "$TASK_INFO" ]]; then
    TASK_FAILED=$((TASK_FAILED + 1))
    continue
  fi

  STATE=$(echo "$TASK_INFO" | jq -r '.state // "unknown"')

  # 计算耗时
  CREATED=$(echo "$TASK_INFO" | jq -r '.createdAt // ""')
  COMPLETED_AT=$(echo "$TASK_INFO" | jq -r '.completedAt // .updatedAt // ""')
  if [[ -n "$CREATED" && -n "$COMPLETED_AT" && "$CREATED" != "null" && "$COMPLETED_AT" != "null" ]]; then
    CREATED_TS=$(date -j -f "%Y-%m-%dT%H:%M:%S" "${CREATED:0:19}" "+%s" 2>/dev/null || echo 0)
    COMPLETED_TS=$(date -j -f "%Y-%m-%dT%H:%M:%S" "${COMPLETED_AT:0:19}" "+%s" 2>/dev/null || echo 0)
    if [[ $CREATED_TS -gt 0 && $COMPLETED_TS -gt 0 ]]; then
      DURATION=$((COMPLETED_TS - CREATED_TS))
      TASK_TIMES+=("$DURATION")
    fi
  fi

  case "$STATE" in
    completed)       COMPLETED=$((COMPLETED + 1)) ;;
    review-pending)  REVIEW_PENDING=$((REVIEW_PENDING + 1)) ;;
    failed)          TASK_FAILED=$((TASK_FAILED + 1)) ;;
    canceled|skipped-canceled) CANCELED=$((CANCELED + 1)) ;;
    *)               ACTIVE=$((ACTIVE + 1)) ;;
  esac
done

TERMINAL_TOTAL=$((COMPLETED + REVIEW_PENDING + TASK_FAILED + CANCELED))
echo "  创建任务: ${SUBMIT_OK}"
if [[ $SUBMIT_OK -gt 0 ]]; then
  TERMINAL_RATE=$(echo "scale=1; ${TERMINAL_TOTAL} * 100 / ${SUBMIT_OK}" | bc 2>/dev/null || echo 0)
  echo "  到达终态: ${TERMINAL_TOTAL} (${TERMINAL_RATE}%)"
else
  TERMINAL_RATE=0
  echo "  到达终态: 0"
fi
echo "  ────────────────────────"
echo "  终态分布:"
echo "    completed:        ${COMPLETED} (${COMPLETED}%)"
echo "    review-pending:   ${REVIEW_PENDING}"
echo "    failed:           ${TASK_FAILED}"
echo "    canceled:         ${CANCELED}"
echo "  处理中:             ${ACTIVE}"
echo ""

# ── 6. 耗时分布 ──────────────────────────────────────────────

echo -e "${CYAN}【6】耗时分布${RESET}"

if [[ ${#TASK_TIMES[@]} -gt 0 ]]; then
  PERCENTILES=$(compute_percentiles "${TASK_TIMES[@]}")
  P50=$(echo "$PERCENTILES" | cut -d'|' -f1)
  P95=$(echo "$PERCENTILES" | cut -d'|' -f2)
  MAX_TIME=$(echo "$PERCENTILES" | cut -d'|' -f3)

  echo "  P50: ${P50}s  P95: ${P95}s  Max: ${MAX_TIME}s"
else
  echo "  无耗时数据（所有任务未到达终态）"
fi
echo ""

# ── 7. 一致性审计 ────────────────────────────────────────────

echo -e "${CYAN}【7】一致性审计${RESET}"
AUDIT_RESULT=$(run_consistency_audit)
AUDIT_OK=$(echo "$AUDIT_RESULT" | jq -r '.ok // false' 2>/dev/null)
FINDINGS_COUNT=$(echo "$AUDIT_RESULT" | jq -r '.findings | length // 0' 2>/dev/null)

if [[ "$AUDIT_OK" == "true" ]]; then
  color_pass "一致性审计通过, findings=${FINDINGS_COUNT}"
else
  color_warn "一致性审计异常, findings=${FINDINGS_COUNT}"
fi
echo ""

# ── 最终判定 ─────────────────────────────────────────────────

print_separator

# 通道判定：>= 80% 到达终态
PASS_THRESHOLD=80

ACTUAL_RATE=$(echo "$TERMINAL_RATE" | cut -d'.' -f1 2>/dev/null || echo 0)
ACTUAL_RATE=${ACTUAL_RATE:-0}

if [[ "$STOP_REASON" == "circuit_open" ]]; then
  echo -e "  停止原因：准入电路打开 → ${RED}FAIL${RESET}"
  TEST_RESULT="FAIL"
elif [[ "$STOP_REASON" == "dependency_blocked" ]]; then
  echo -e "  停止原因：依赖阻塞 → ${RED}FAIL${RESET}"
  TEST_RESULT="FAIL"
elif [[ $ACTUAL_RATE -ge $PASS_THRESHOLD ]]; then
  echo -e "  结果：${GREEN}✓ PASS${RESET}（到达终态 ${TERMINAL_RATE}% ≥ ${PASS_THRESHOLD}%）"
  echo -e "  通过条件：${TERMINAL_TOTAL}/${SUBMIT_OK} ≈ ${TERMINAL_RATE}% ≥ ${PASS_THRESHOLD}%"
  TEST_RESULT="PASS"
else
  echo -e "  结果：${RED}✗ FAIL${RESET}（到达终态 ${TERMINAL_RATE}% < ${PASS_THRESHOLD}%）"
  echo -e "  通过条件：${TERMINAL_TOTAL}/${SUBMIT_OK} ≈ ${TERMINAL_RATE}% < ${PASS_THRESHOLD}%"
  TEST_RESULT="FAIL"
fi

print_separator
echo ""

if [[ "$TEST_RESULT" == "PASS" ]]; then
  exit 0
else
  exit 1
fi
