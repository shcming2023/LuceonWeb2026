#!/bin/bash
# ============================================================
# Luceon2026 — 准入电路故障注入验证脚本
#
# 用途：验证 MinerU 准入电路在不同故障场景下的行为
# 依赖：curl、jq、docker
# 用法：
#   bash uat/fault-injection-admission.sh --mode mineru-down
#   bash uat/fault-injection-admission.sh --mode mineru-half-failure
#   bash uat/fault-injection-admission.sh --mode recovery
#
# 模式说明：
#   mineru-down          - 完全停止 MinerU，验证 503 和 Markdown 不受影响
#   mineru-half-failure  - 模拟半故障（/health OK, submit 500）
#   recovery             - 验证恢复流程（/health 恢复 → submit-probe 成功 → 电路关闭）
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/test-utils.sh"

BASE_URL="${BASE_URL:-http://127.0.0.1:8081}"
TEST_PDF_DIR="${TEST_PDF_DIR:-${SCRIPT_DIR}/../testpdf}"
TEST_MD_DIR="${TEST_MD_DIR:-${SCRIPT_DIR}/../testmd}"
MODE=""
PASS=0
FAIL=0

# ── 参数解析 ─────────────────────────────────────────────────

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      MODE="$2"
      shift 2
      ;;
    *)
      echo "未知参数: $1"
      echo "用法: $0 --mode [mineru-down|mineru-half-failure|recovery]"
      exit 1
      ;;
  esac
done

if [[ -z "$MODE" ]]; then
  echo -e "${RED}错误：必须指定 --mode 参数${RESET}"
  echo "用法: $0 --mode [mineru-down|mineru-half-failure|recovery]"
  exit 1
fi

if [[ "$MODE" != "mineru-down" && "$MODE" != "mineru-half-failure" && "$MODE" != "recovery" ]]; then
  echo -e "${RED}错误：无效的 mode: ${MODE}${RESET}"
  echo "可用 mode: mineru-down, mineru-half-failure, recovery"
  exit 1
fi

# ── 脚本头 ───────────────────────────────────────────────────

print_separator
echo -e "${CYAN}  Luceon2026 准入电路故障注入验证${RESET}"
echo -e "${CYAN}  模式：${MODE}${RESET}"
echo -e "${CYAN}  目标地址：${BASE_URL}${RESET}"
echo -e "${CYAN}  时间：$(date '+%Y-%m-%d %H:%M:%S')${RESET}"
print_separator
echo ""

# ── 前置检查 ─────────────────────────────────────────────────

echo -e "${CYAN}【0】前置检查${RESET}"
if ! command -v jq &>/dev/null; then
  color_fail "缺少 jq"
  exit 1
fi
color_pass "jq 可用"
echo ""

# ── 模式：mineru-down ────────────────────────────────────────

run_mineru_down() {
  echo -e "${CYAN}【1】确认 MinerU 就绪${RESET}"

  if check_dependency_health 15 3; then
    local dep_health
    dep_health=$(curl -s --max-time 10 "${BASE_URL}/__proxy/upload/ops/dependency-health" 2>/dev/null || echo '{}')
    local mineru_ok
    mineru_ok=$(echo "$dep_health" | jq -r '.dependencies.mineru // "unknown"' 2>/dev/null)
    color_pass "dependency-health 全绿 (MinerU: ${mineru_ok})"
    PASS=$((PASS + 1))
  else
    color_warn "dependency-health 未全绿"
  fi

  if check_admission_circuit; then
    color_pass "准入电路已关闭"
    PASS=$((PASS + 1))
  else
    color_warn "准入电路已打开（可能已有故障）"
  fi

  # submit-probe 验证
  if run_submit_probe_check 1; then
    color_pass "MinerU submit-probe 通过"
  else
    color_warn "MinerU submit-probe 未通过"
  fi

  echo ""

  # ── 停止 MinerU ─────────────────────

  echo -e "${YELLOW}【2】请手动停止 MinerU FastAPI 服务${RESET}"
  echo ""
  echo "  方式 1 (Docker): docker stop <mineru-container-name>"
  echo "  方式 2 (本地进程): kill <mineru-pid>"
  echo "  方式 3: 关闭运行 MinerU 的终端"
  echo ""

  read -p "停止 MinerU 后按 Enter 继续..." _unused
  echo ""

  # 等待系统检测到 MinerU 不可用
  echo "  等待系统检测 MinerU 不可用 (15s)..."
  sleep 15

  # ── 验证 503 ────────────────────────

  echo -e "${CYAN}【3】验证 PDF 上传返回 503${RESET}"

  PDF_FILES=$(find "$TEST_PDF_DIR" -maxdepth 1 -name '*.pdf' -not -name '._*' 2>/dev/null | head -1)
  if [[ -n "$PDF_FILES" ]]; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
      --max-time 15 \
      -F "file=@${PDF_FILES}" \
      "${BASE_URL}/__proxy/upload/tasks" 2>/dev/null || echo "000")

    if [[ "$HTTP_CODE" == "503" ]]; then
      color_pass "PDF 上传返回 503 MINERU_ADMISSION_CIRCUIT_OPEN"
      PASS=$((PASS + 1))
    else
      color_fail "PDF 上传返回 HTTP ${HTTP_CODE}（期望 503）"
      FAIL=$((FAIL + 1))
    fi
  else
    color_fail "无 PDF 样本，无法验证 503 熔断隔离"
    FAIL=$((FAIL + 1))
  fi

  echo ""

  # ── 验证 Markdown 不受影响 ────────

  echo -e "${CYAN}【4】验证 Markdown 上传不受影响${RESET}"

  MD_FILES=$(find "$TEST_MD_DIR" -maxdepth 1 -name '*.md' -not -name '._*' 2>/dev/null | head -1 || echo "")
  if [[ -n "$MD_FILES" ]]; then
    TASK_ID=$(submit_markdown "$MD_FILES" || true)
    if [[ -n "$TASK_ID" && "$TASK_ID" != "null" ]]; then
      color_pass "Markdown 上传成功 (taskId=${TASK_ID})"
      PASS=$((PASS + 1))
    else
      color_fail "Markdown 上传失败"
      FAIL=$((FAIL + 1))
    fi
  else
    color_fail "无 Markdown 样本，无法验证 Markdown 旁路不受影响"
    FAIL=$((FAIL + 1))
  fi

  echo ""

  # ── 提示恢复 ────────────────────────

  echo -e "${YELLOW}【5】请手动恢复 MinerU 服务${RESET}"
  echo "  方式 1 (Docker): docker start <mineru-container-name>"
  echo "  方式 2 (本地进程): 重新启动 MinerU FastAPI"
  echo ""

  read -p "恢复 MinerU 后按 Enter 继续..." _unused
  echo ""

  echo -e "${CYAN}【6】验证恢复后的 submit-probe${RESET}"
  sleep 10
  if run_submit_probe_check 3; then
    color_pass "submit-probe 全部通过"
  else
    color_warn "submit-probe 部分失败（可能需等待冷却期）"
  fi

  echo ""
}

# ── 模式：mineru-half-failure ────────────────────────────────

run_mineru_half_failure() {
  echo -e "${CYAN}【1】确认 MinerU 就绪${RESET}"

  if check_dependency_health 15 3; then
    color_pass "dependency-health 全绿"
    PASS=$((PASS + 1))
  else
    color_warn "dependency-health 未全绿"
  fi

  if check_admission_circuit; then
    color_pass "准入电路关闭"
    PASS=$((PASS + 1))
  else
    color_warn "准入电路已打开"
  fi

  echo ""

  echo -e "${YELLOW}【2】半故障模拟说明${RESET}"
  echo "  半故障场景：MinerU /health 正常但 submit 返回 500"
  echo "  当前默认不自动模拟，需手动导致此状态"
  echo ""

  # submit-probe 检查
  echo -e "${CYAN}【3】预故障 submit-probe 验证${RESET}"
  if run_submit_probe_check 1; then
    color_pass "submit-probe 通过"
  else
    color_warn "submit-probe 未通过"
  fi

  echo ""

  echo -e "${YELLOW}【4】请手动制造 MinerU 半故障状态（/health OK, submit 500）${RESET}"
  echo "  例如：修改 MinerU 的 POST /tasks 端点返回 500"
  echo ""

  read -p "制造半故障状态后按 Enter 继续..." _unused
  echo ""

  sleep 10

  echo -e "${CYAN}【5】故障后 submit-probe 验证${RESET}"
  if run_submit_probe_check 3; then
    color_warn "submit-probe 仍然通过（半故障未生效？）"
  else
    color_pass "submit-probe 部分/全部失败（半故障已生效）"
    PASS=$((PASS + 1))
  fi

  # 检查电路是否打开
  echo ""
  if check_admission_circuit; then
    color_warn "准入电路仍未打开（可能需更多故障累积）"
  else
    color_pass "准入电路已打开"
    PASS=$((PASS + 1))
  fi

  echo ""
  echo -e "${YELLOW}请手动恢复 MinerU 正常状态后重新测试${RESET}"
}

# ── 模式：recovery ────────────────────────────────────────────

run_recovery() {
  echo -e "${CYAN}【1】确认当前状态${RESET}"

  echo "  当前 MinerU 部分恢复（仅 /health OK）"

  if check_admission_circuit; then
    color_warn "准入电路已关闭（无需恢复）"
  else
    color_info "准入电路保持打开"
  fi

  echo ""

  # ── 验证电路保持打开 ───────────────

  echo -e "${CYAN}【2】验证仅 /health 恢复时电路保持打开${RESET}"

  # 首先确认 MinerU /health OK
  local dep_health
  dep_health=$(curl -s --max-time 10 "${BASE_URL}/__proxy/upload/ops/dependency-health" 2>/dev/null || echo '{}')
  local mineru_ok
  mineru_ok=$(echo "$dep_health" | jq -r '.dependencies.mineru // "unknown"' 2>/dev/null)

  echo "  MinerU /health: ${mineru_ok}"

  # 检查电路
  local circuit_resp
  circuit_resp=$(curl -s --max-time 10 "${BASE_URL}/__proxy/upload/ops/mineru/admission-circuit" 2>/dev/null || echo '{}')
  local circuit_open
  circuit_open=$(echo "$circuit_resp" | jq -r 'if .open == null then true else .open end' 2>/dev/null)
  echo "  准入电路 open: ${circuit_open}"

  if [[ "$circuit_open" == "true" && "$mineru_ok" == "ok" ]]; then
    color_pass "仅 /health 恢复时电路保持打开"
    PASS=$((PASS + 1))
  else
    color_warn "电路状态异常（open=${circuit_open}, mineru=${mineru_ok}）"
  fi

  echo ""

  # ── submit-probe 验证 ──────────────

  echo -e "${CYAN}【3】执行 submit-probe 并验证电路关闭${RESET}"

  echo "  确保 MinerU 完全恢复（submit 端点正常）..."
  sleep 5

  if run_submit_probe_check 3; then
    color_pass "submit-probe 全部通过"
    PASS=$((PASS + 1))
  else
    color_warn "submit-probe 未全部通过"
    FAIL=$((FAIL + 1))
  fi

  echo ""

  # 等待冷却期
  echo "  等待冷却期（5s）..."
  sleep 5

  # 再次检查电路
  if check_admission_circuit; then
    color_pass "准入电路在冷却期后关闭"
    PASS=$((PASS + 1))
  else
    color_warn "准入电路仍未关闭（可能冷却期未到或探头次数不足）"
  fi

  echo ""

  # ── 验证 PDF 上传恢复 ─────────────

  echo -e "${CYAN}【4】验证 PDF 上传恢复正常${RESET}"

  PDF_FILES=$(find "$TEST_PDF_DIR" -maxdepth 1 -name '*.pdf' -not -name '._*' 2>/dev/null | head -1)
  if [[ -n "$PDF_FILES" ]]; then
    TASK_ID=$(submit_pdf "$PDF_FILES" || true)
    if [[ -n "$TASK_ID" && "$TASK_ID" != "null" ]]; then
      color_pass "PDF 上传成功 (taskId=${TASK_ID})"
      PASS=$((PASS + 1))
    else
      color_fail "PDF 上传失败"
      FAIL=$((FAIL + 1))
    fi
  else
    color_warn "无 PDF 样本，跳过验证"
  fi

  echo ""
}

# ── 执行选定模式 ─────────────────────────────────────────────

case "$MODE" in
  mineru-down)          run_mineru_down ;;
  mineru-half-failure)  run_mineru_half_failure ;;
  recovery)             run_recovery ;;
esac

# ── 最终判定 ─────────────────────────────────────────────────

print_separator

if [[ $FAIL -eq 0 ]]; then
  echo -e "  结果：${GREEN}✓ PASS${RESET}（准入电路故障注入验证通过）"
  print_separator
  echo ""
  exit 0
else
  echo -e "  结果：${RED}✗ FAIL${RESET}（${FAIL} 项检查未通过）"
  print_separator
  echo ""
  exit 1
fi
