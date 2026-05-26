#!/bin/bash
# ============================================================
# Luceon2026 — Worker 异常终止自愈验证脚本
#
# 用途：验证 upload-server 异常终止后 ParseTask Worker 的
#        自愈恢复能力（含事件验证）
# 依赖：curl、jq、docker
# 用法：
#   bash uat/fault-injection-worker-crash.sh
#   BASE_URL=http://192.168.31.33:8081 bash uat/fault-injection-worker-crash.sh
#
# 注意：此脚本涉及 docker kill，运行前需用户确认。
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/test-utils.sh"

BASE_URL="${BASE_URL:-http://127.0.0.1:8081}"
TEST_PDF_DIR="${TEST_PDF_DIR:-${SCRIPT_DIR}/../testpdf}"
PASS=0
FAIL=0

# ── 安全确认 ─────────────────────────────────────────────────

print_separator
echo -e "${CYAN}  Luceon2026 Worker 自愈故障注入验证${RESET}"
echo -e "${CYAN}  目标地址：${BASE_URL}${RESET}"
echo -e "${CYAN}  时间：$(date '+%Y-%m-%d %H:%M:%S')${RESET}"
print_separator
echo ""

echo -e "${YELLOW}⚠ 警告：此脚本将执行以下破坏性操作：${RESET}"
echo "  1. 强制终止 upload-server Docker 容器 (docker kill)"
echo "  2. 随后重启 upload-server (docker compose up -d)"
echo ""
echo -e "${YELLOW}请确保：${RESET}"
echo "  - 当前环境是测试/UAT 环境，非生产环境"
echo "  - 您有权限操作 Docker"
echo "  - 样本 PDF 目录存在且至少包含 1 个 PDF 文件"
echo ""

read -p "确认继续？(输入 yes 继续): " CONFIRM
if [[ "$CONFIRM" != "yes" ]]; then
  echo "已取消"
  exit 0
fi
echo ""

# ── 前置检查 ─────────────────────────────────────────────────

echo -e "${CYAN}【0】前置检查${RESET}"

if ! command -v jq &>/dev/null; then
  color_fail "缺少 jq"
  exit 1
fi
color_pass "jq 可用"

if ! command -v docker &>/dev/null; then
  color_fail "缺少 docker"
  exit 1
fi
color_pass "docker 可用"

# 获取 upload-server 容器名称
UPLOAD_CONTAINER=$(docker ps --format '{{.Names}}' 2>/dev/null | grep 'upload-server' | head -1 || echo "")
if [[ -z "$UPLOAD_CONTAINER" ]]; then
  color_fail "未找到运行中的 upload-server 容器"
  exit 1
fi
color_pass "upload-server 容器: ${UPLOAD_CONTAINER}"

# 检查样本 PDF
if [[ ! -d "$TEST_PDF_DIR" ]]; then
  color_fail "样本目录不存在: ${TEST_PDF_DIR}"
  exit 1
fi
PDF_FILES=$(find "$TEST_PDF_DIR" -maxdepth 1 -name '*.pdf' -not -name '._*' 2>/dev/null | head -1)
if [[ -z "$PDF_FILES" ]]; then
  color_fail "PDF 样本目录为空"
  exit 1
fi
color_pass "PDF 样本可用"

echo ""

# ── 1. 预检 ──────────────────────────────────────────────────

echo -e "${CYAN}【1】预检：dependency-health${RESET}"

if check_dependency_health 15 3; then
  color_pass "dependency-health 全绿"
  PASS=$((PASS + 1))
else
  color_fail "dependency-health 未就绪"
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

# ── 3. 提交一个 PDF ──────────────────────────────────────────

echo -e "${CYAN}【3】提交 PDF 任务并等待进入 running 状态${RESET}"

TASK_ID=$(submit_pdf "$PDF_FILES" || true)
if [[ -z "$TASK_ID" || "$TASK_ID" == "null" ]]; then
  color_fail "PDF 提交失败"
  exit 1
fi
echo "  任务 ID: ${TASK_ID}"

# 等待任务进入 running 状态
echo "  等待进入 running 或 ai-running 状态..."
MAX_WAIT=120
WAIT_SEC=0
TASK_STATE=""

while [[ $WAIT_SEC -lt $MAX_WAIT ]]; do
  sleep 3
  WAIT_SEC=$((WAIT_SEC + 3))

  TASK_INFO=$(get_task_by_id "$TASK_ID")
  TASK_STATE=$(echo "$TASK_INFO" | jq -r '.state // "unknown"' 2>/dev/null)

  echo "  [${WAIT_SEC}s] state=${TASK_STATE}"

  if [[ "$TASK_STATE" == "running" || "$TASK_STATE" == "ai-running" ]]; then
    color_pass "任务进入 ${TASK_STATE} 状态"
    PASS=$((PASS + 1))
    break
  fi

  # 如果任务已进入终态，说明没有真实执行 crash 注入；Stage 4 不能伪通过。
  if echo "$TASK_STATE" | grep -qE '^(completed|review-pending|failed|canceled)$'; then
    color_fail "任务已到达终态 ${TASK_STATE}，Worker crash 验证未执行"
    exit 1
  fi
done

if [[ "$TASK_STATE" != "running" && "$TASK_STATE" != "ai-running" ]]; then
  color_fail "任务未在 ${MAX_WAIT}s 内进入 running 状态"
  exit 1
fi

echo ""

# ── 4. 强制终止 upload-server ────────────────────────────────

echo -e "${CYAN}【4】强制终止 upload-server 容器${RESET}"
echo "  执行: docker kill ${UPLOAD_CONTAINER}"

if docker kill "$UPLOAD_CONTAINER" 2>/dev/null; then
  echo "  upload-server 已终止"
else
  color_warn "docker kill 失败，尝试继续"
fi

# 等待一段时间确保容器完全停止
sleep 3
echo ""

# ── 5. 重启 upload-server ────────────────────────────────────

echo -e "${CYAN}【5】重启 upload-server${RESET}"
echo "  执行: docker compose up -d upload-server"

if docker compose up -d upload-server 2>/dev/null || docker-compose up -d upload-server 2>/dev/null; then
  color_pass "upload-server 已重启"
  PASS=$((PASS + 1))
else
  color_fail "upload-server 重启失败"
  FAIL=$((FAIL + 1))
fi

echo ""

# ── 6. 等待恢复扫描 ──────────────────────────────────────────

echo -e "${CYAN}【6】等待恢复扫描完成（约 15s）${RESET}"
echo "  等待 Worker 启动并执行 runRecoveryScan..."

# 等待 dependency-health 恢复
echo "  等待 dependency-health 恢复..."
if check_dependency_health 30 3; then
  color_pass "dependency-health 全绿 (已恢复)"
  PASS=$((PASS + 1))
else
  color_warn "dependency-health 未就绪（但会继续验证）"
fi

# 额外等待恢复扫描执行
sleep 10
echo ""

# ── 7. 验证任务状态 ──────────────────────────────────────────

echo -e "${CYAN}【7】验证任务状态${RESET}"

TASK_INFO=$(get_task_by_id "$TASK_ID")
CURRENT_STATE=$(echo "$TASK_INFO" | jq -r '.state // "unknown"' 2>/dev/null)

echo "  任务 ${TASK_ID} 当前状态: ${CURRENT_STATE}"

# 验证状态已变回 pending（恢复扫描的结果）
if [[ "$CURRENT_STATE" == "pending" ]]; then
  color_pass "running 中的任务已重置为 pending"
  PASS=$((PASS + 1))
else
  echo "  任务状态为 ${CURRENT_STATE}（可能已被 MinerU 接管或已到其他阶段）"
fi

echo ""

# ── 8. 验证恢复事件 ──────────────────────────────────────────

echo -e "${CYAN}【8】验证恢复事件${RESET}"

EVENTS=$(get_task_events "$TASK_ID")

# 检查 parse-stale-running-recovered 或 parse-restart-recovered 事件
STALE_EVENT=$(echo "$EVENTS" | jq -r '[.[] | select(.event == "parse-stale-running-recovered" or .event == "parse-restart-recovered")] | length' 2>/dev/null || echo 0)
MINERU_EVENT=$(echo "$EVENTS" | jq -r '[.[] | select(.event == "parse-restart-mineru-resumed")] | length' 2>/dev/null || echo 0)

if [[ $STALE_EVENT -gt 0 ]]; then
  color_pass "parse-stale-running-recovered 或 parse-restart-recovered 事件已记录 (${STALE_EVENT} 条)"
  PASS=$((PASS + 1))
elif [[ $MINERU_EVENT -gt 0 ]]; then
  color_pass "parse-restart-mineru-resumed 事件已记录 (${MINERU_EVENT} 条)（MinerU 接管场景）"
  PASS=$((PASS + 1))
else
  # 没有恢复事件就不能作为 Stage 4 通过证据。
  CURRENT_STAGE=$(echo "$TASK_INFO" | jq -r '.stage // ""' 2>/dev/null)
  if [[ "$CURRENT_STAGE" == "mineru-processing" || "$CURRENT_STAGE" == "mineru-queued" ]]; then
    color_fail "任务被 MinerU 接管但未检测到恢复事件"
  else
    color_fail "未检测到恢复事件"
  fi
  FAIL=$((FAIL + 1))
fi

echo ""

# ── 9. 等待任务完成完整流程 ─────────────────────────────────

echo -e "${CYAN}【9】等待任务完成完整流程（最多 10min）${RESET}"

WAIT_SEC=0
MAX_FINAL_WAIT=600
FINAL_STATE=""

while [[ $WAIT_SEC -lt $MAX_FINAL_WAIT ]]; do
  sleep 15
  WAIT_SEC=$((WAIT_SEC + 15))

  TASK_INFO=$(get_task_by_id "$TASK_ID")
  FINAL_STATE=$(echo "$TASK_INFO" | jq -r '.state // "unknown"' 2>/dev/null)

  echo "  [${WAIT_SEC}s] state=${FINAL_STATE}"

  if echo "$FINAL_STATE" | grep -qE '^(completed|review-pending|failed|canceled|skipped-canceled)$'; then
    echo ""
    color_pass "任务到达终态: ${FINAL_STATE}"
    PASS=$((PASS + 1))
    break
  fi
done

if ! echo "$FINAL_STATE" | grep -qE '^(completed|review-pending|failed|canceled|skipped-canceled)$' 2>/dev/null; then
  color_fail "任务未在 ${MAX_FINAL_WAIT}s 内到达终态"
  FAIL=$((FAIL + 1))
fi

echo ""

# ── 最终判定 ─────────────────────────────────────────────────

print_separator

if [[ $FAIL -eq 0 ]]; then
  echo -e "  结果：${GREEN}✓ PASS${RESET}（Worker 自愈故障注入验证通过）"
  print_separator
  echo ""
  exit 0
else
  echo -e "  结果：${RED}✗ FAIL${RESET}（${FAIL} 项检查未通过）"
  print_separator
  echo ""
  exit 1
fi
