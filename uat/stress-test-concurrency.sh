#!/bin/bash
# ============================================================
# Luceon2026 — 5+ 并发阶段排队验证脚本
#
# 用途：验证高速并发提交下的阶段排队机制
# 依赖：curl、jq、python3
# 用法：
#   bash uat/stress-test-concurrency.sh
#   BASE_URL=http://192.168.31.33:8081 bash uat/stress-test-concurrency.sh
#
# 环境变量：
#   BASE_URL            - 目标服务地址（默认 http://127.0.0.1:8081）
#   TEST_PDF_DIR        - 样本 PDF 目录（默认 ../testpdf）
#   TEST_MD_DIR         - 样本 Markdown 目录（默认 ../testmd）
#   MAX_WAIT_MINUTES    - 最大等待分钟数（默认 10）
#   POLL_INTERVAL       - 状态轮询间隔秒（默认 10）
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/test-utils.sh"

BASE_URL="${BASE_URL:-http://127.0.0.1:8081}"
TEST_PDF_DIR="${TEST_PDF_DIR:-${SCRIPT_DIR}/../testpdf}"
TEST_MD_DIR="${TEST_MD_DIR:-${SCRIPT_DIR}/../testmd}"
MAX_WAIT_MINUTES="${MAX_WAIT_MINUTES:-10}"
POLL_INTERVAL="${POLL_INTERVAL:-10}"

PASS=0
FAIL=0
MD_TASK_IDS=()
PDF_TASK_IDS=()
ALL_TASK_IDS=()

# ── 脚本头 ───────────────────────────────────────────────────

print_separator
echo -e "${CYAN}  Luceon2026 5+ 并发阶段排队验证脚本${RESET}"
echo -e "${CYAN}  目标地址：${BASE_URL}${RESET}"
echo -e "${CYAN}  时间：$(date '+%Y-%m-%d %H:%M:%S')${RESET}"
print_separator
echo ""

# ── 前置检查 ─────────────────────────────────────────────────

echo -e "${CYAN}【0】前置依赖检查${RESET}"
if ! command -v jq &>/dev/null; then
  color_fail "缺少 jq"
  exit 1
fi
color_pass "jq 可用"

if [[ ! -d "$TEST_PDF_DIR" ]]; then
  color_fail "PDF 样本目录不存在: ${TEST_PDF_DIR}"
  exit 1
fi
PDF_COUNT=$(find "$TEST_PDF_DIR" -maxdepth 1 -name '*.pdf' -not -name '._*' 2>/dev/null | wc -l | tr -d ' ')
if [[ $PDF_COUNT -lt 5 ]]; then
  color_fail "需要至少 5 个 PDF 样本（实际 ${PDF_COUNT}）"
  exit 1
fi

# Markdown 样本目录（可选，不存在时跳过）
HAVE_MD=true
if [[ ! -d "$TEST_MD_DIR" ]]; then
  color_warn "Markdown 样本目录不存在，Markdown 并发验证跳过"
  HAVE_MD=false
else
  MD_COUNT=$(find "$TEST_MD_DIR" -maxdepth 1 -name '*.md' -not -name '._*' 2>/dev/null | wc -l | tr -d ' ')
  if [[ $MD_COUNT -lt 5 ]]; then
    color_warn "Markdown 样本不足 5 个（实际 ${MD_COUNT}），Markdown 并发验证跳过"
    HAVE_MD=false
  fi
fi
echo ""

# ── 1. 预检 ──────────────────────────────────────────────────

echo -e "${CYAN}【1】预检${RESET}"

if check_dependency_health 30 3; then
  color_pass "dependency-health 全绿"
  PASS=$((PASS + 1))
else
  color_fail "dependency-health 未就绪"
  FAIL=$((FAIL + 1))
fi

if check_admission_circuit; then
  color_pass "准入电路已关闭"
  PASS=$((PASS + 1))
else
  color_fail "准入电路已打开"
  FAIL=$((FAIL + 1))
fi

echo ""
if [[ $FAIL -gt 0 ]]; then
  color_fail "预检失败，终止测试"
  exit 1
fi

# ── 2. 获取基线 ──────────────────────────────────────────────

BASELINE_COUNT=$(get_baseline_count)
echo -e "${CYAN}【2】基线任务数：${BASELINE_COUNT}${RESET}"
echo ""

# ── 3. 并发提交 ──────────────────────────────────────────────

echo -e "${CYAN}【3】快速连续提交（并发模式）${RESET}"

SUBMIT_COUNT=0
SUBMIT_OK=0
SUBMIT_FAIL=0

# 提交 5 个 Markdown
if [[ "$HAVE_MD" == "true" ]]; then
  echo "  提交 5 个 Markdown..."
  MD_FILES=()
  while IFS= read -r line; do
    MD_FILES+=("$line")
  done < <(find "$TEST_MD_DIR" -maxdepth 1 -name '*.md' -not -name '._*' | head -n 5)

  MD_START_TS=$(date +%s)
  for ((i=0; i<5; i++)); do
    md_path="${MD_FILES[$i]}"
    task_id=$(submit_markdown "$md_path" || true)
    if [[ -n "$task_id" && "$task_id" != "null" ]]; then
      MD_TASK_IDS+=("$task_id")
      ALL_TASK_IDS+=("$task_id")
      SUBMIT_OK=$((SUBMIT_OK + 1))
      echo "    [${SUBMIT_COUNT}] Markdown: ${task_id}"
    else
      SUBMIT_FAIL=$((SUBMIT_FAIL + 1))
      echo "    [${SUBMIT_COUNT}] Markdown: FAIL"
    fi
    SUBMIT_COUNT=$((SUBMIT_COUNT + 1))
  done
  MD_END_TS=$(date +%s)
  MD_DURATION=$((MD_END_TS - MD_START_TS))
  echo "  Markdown 提交耗时: ${MD_DURATION}s"

  # 验证：上传间隔 < 5s
  MD_AVG=$(echo "scale=1; ${MD_DURATION} / 5" | bc 2>/dev/null || echo 999)
  if echo "$MD_AVG < 5" | bc -l 2>/dev/null | grep -q 1; then
    color_pass "Markdown 上传间隔平均 ${MD_AVG}s < 5s"
    PASS=$((PASS + 1))
  else
    color_fail "Markdown 上传间隔平均 ${MD_AVG}s >= 5s"
    FAIL=$((FAIL + 1))
  fi
else
  echo "  跳过 Markdown 并发提交"
fi

# 提交 5 个 PDF
echo "  提交 5 个 PDF..."
PDF_FILES=()
while IFS= read -r line; do
  PDF_FILES+=("$line")
done < <(find "$TEST_PDF_DIR" -maxdepth 1 -name '*.pdf' -not -name '._*' | head -n 5)

PDF_START_TS=$(date +%s)
for ((i=0; i<5; i++)); do
  pdf_path="${PDF_FILES[$i]}"
  task_id=$(submit_pdf "$pdf_path" || true)
  if [[ -n "$task_id" && "$task_id" != "null" ]]; then
    PDF_TASK_IDS+=("$task_id")
    ALL_TASK_IDS+=("$task_id")
    SUBMIT_OK=$((SUBMIT_OK + 1))
    echo "    [${SUBMIT_COUNT}] PDF: ${task_id}"
  else
    SUBMIT_FAIL=$((SUBMIT_FAIL + 1))
    echo "    [${SUBMIT_COUNT}] PDF: FAIL"
  fi
  SUBMIT_COUNT=$((SUBMIT_COUNT + 1))
done
PDF_END_TS=$(date +%s)
PDF_DURATION=$((PDF_END_TS - PDF_START_TS))
echo "  PDF 提交耗时: ${PDF_DURATION}s"

# 验证：上传间隔 < 5s
PDF_AVG=$(echo "scale=1; ${PDF_DURATION} / 5" | bc 2>/dev/null || echo 999)
if echo "$PDF_AVG < 5" | bc -l 2>/dev/null | grep -q 1; then
  color_pass "PDF 上传间隔平均 ${PDF_AVG}s < 5s"
  PASS=$((PASS + 1))
else
  color_fail "PDF 上传间隔平均 ${PDF_AVG}s >= 5s"
  FAIL=$((FAIL + 1))
fi

echo "  总计：${SUBMIT_OK}/${SUBMIT_COUNT} 任务创建成功"
echo ""

# ── 4. 阶段排队验证 ─────────────────────────────────────────

echo -e "${CYAN}【4】阶段排队验证${RESET}"

MAX_SECONDS=$((MAX_WAIT_MINUTES * 60))
ELAPSED=0
MINERU_VIOLATION=0
AI_VIOLATION=0

while [[ $ELAPSED -lt $MAX_SECONDS ]]; do
  sleep "$POLL_INTERVAL"
  ELAPSED=$((ELAPSED + POLL_INTERVAL))

  ALL_TASKS=$(get_all_tasks)

  # 统计活跃任务
  ACTIVE=0
  TERMINAL=0
  RUNNING=0
  for tid in "${ALL_TASK_IDS[@]}"; do
    STATE=$(echo "$ALL_TASKS" | jq -r ".[] | select(.id == \"${tid}\") | .state // \"unknown\"" 2>/dev/null)
    if [[ -z "$STATE" || "$STATE" == "null" ]]; then
      STATE="unknown"
    fi

    case "$STATE" in
      completed|review-pending|failed|canceled|skipped-canceled) TERMINAL=$((TERMINAL + 1)) ;;
      running) RUNNING=$((RUNNING + 1)); ACTIVE=$((ACTIVE + 1)) ;;
      *) ACTIVE=$((ACTIVE + 1)) ;;
    esac
  done

  # 检查 MinerU heavy-stage active count
  MINERU_ACTIVE=$(echo "$ALL_TASKS" | jq '[.[] | select(.stage == "mineru-processing" or .stage == "mineru-queued" or .stage == "result-fetching")] | length' 2>/dev/null || echo 0)
  if [[ $MINERU_ACTIVE -gt 1 ]]; then
    MINERU_VIOLATION=$((MINERU_VIOLATION + 1))
  fi

  # 检查 AI Worker active count
  AI_ACTIVE=$(echo "$ALL_TASKS" | jq '[.[] | select(.state == "ai-running" or .stage == "ai")] | length' 2>/dev/null || echo 0)
  if [[ $AI_ACTIVE -gt 1 ]]; then
    AI_VIOLATION=$((AI_VIOLATION + 1))
  fi

  echo -e "  [${ELAPSED}s] 终态: ${TERMINAL}/${#ALL_TASK_IDS[@]}, 活跃: ${ACTIVE}, MinerU active: ${MINERU_ACTIVE}, AI active: ${AI_ACTIVE}"

  # 全终态退出
  if [[ $TERMINAL -eq ${#ALL_TASK_IDS[@]} ]]; then
    break
  fi
done

echo ""

# 验证 MinerU heavy-stage 排队
if [[ $MINERU_VIOLATION -eq 0 ]]; then
  color_pass "MinerU heavy-stage active count ≤ 1 (违规次数: 0)"
  PASS=$((PASS + 1))
else
  color_fail "MinerU heavy-stage 排队违规 ${MINERU_VIOLATION} 次"
  FAIL=$((FAIL + 1))
fi

# 验证 AI Worker 排队
if [[ $AI_VIOLATION -eq 0 ]]; then
  color_pass "AI Worker active count ≤ 1 (违规次数: 0)"
  PASS=$((PASS + 1))
else
  color_fail "AI Worker 排队违规 ${AI_VIOLATION} 次"
  FAIL=$((FAIL + 1))
fi

# ── 5. 终态验证 ──────────────────────────────────────────────

echo ""
echo -e "${CYAN}【5】终态验证${RESET}"

ALL_TASKS=$(get_all_tasks)
TERMINAL=0
COMPLETED=0
REVIEW_PENDING=0
TASK_FAILED=0
CANCELED=0
NOT_TERMINAL=0

for tid in "${ALL_TASK_IDS[@]}"; do
  STATE=$(echo "$ALL_TASKS" | jq -r ".[] | select(.id == \"${tid}\") | .state // \"unknown\"" 2>/dev/null)
  if [[ -z "$STATE" || "$STATE" == "null" ]]; then
    STATE="unknown"
  fi

  case "$STATE" in
    completed)       COMPLETED=$((COMPLETED + 1)); TERMINAL=$((TERMINAL + 1)) ;;
    review-pending)  REVIEW_PENDING=$((REVIEW_PENDING + 1)); TERMINAL=$((TERMINAL + 1)) ;;
    failed)          TASK_FAILED=$((TASK_FAILED + 1)); TERMINAL=$((TERMINAL + 1)) ;;
    canceled|skipped-canceled) CANCELED=$((CANCELED + 1)); TERMINAL=$((TERMINAL + 1)) ;;
    *)               NOT_TERMINAL=$((NOT_TERMINAL + 1)) ;;
  esac
done

echo "  终态分布:"
echo "    completed:       ${COMPLETED}"
echo "    review-pending:  ${REVIEW_PENDING}"
echo "    failed:          ${TASK_FAILED}"
echo "    canceled:        ${CANCELED}"
echo "  未终态:           ${NOT_TERMINAL}"

if [[ $TERMINAL -eq ${#ALL_TASK_IDS[@]} ]]; then
  color_pass "所有 ${#ALL_TASK_IDS[@]} 个任务已到达终态"
  PASS=$((PASS + 1))
elif [[ $ELAPSED -ge $MAX_SECONDS ]]; then
  color_fail "超时 ${MAX_WAIT_MINUTES}min，尚有 ${NOT_TERMINAL} 个任务未终态"
  FAIL=$((FAIL + 1))
else
  color_pass "所有 ${#ALL_TASK_IDS[@]} 个任务已到达终态"
  PASS=$((PASS + 1))
fi

echo ""

# ── 最终判定 ─────────────────────────────────────────────────

print_separator

if [[ $FAIL -eq 0 ]]; then
  echo -e "  结果：${GREEN}✓ PASS${RESET}（并发阶段排队验证通过）"
  echo -e "  所有检查项通过：MinerU 排队、AI Worker 排队、终态收敛"
  print_separator
  echo ""
  exit 0
else
  echo -e "  结果：${RED}✗ FAIL${RESET}（${FAIL} 项检查未通过）"
  print_separator
  echo ""
  exit 1
fi
