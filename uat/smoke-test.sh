#!/usr/bin/env bash
# ============================================================
# EduAsset CMS — 冒烟测试脚本
#
# 用途：部署后快速验证所有服务链路是否正常
# 依赖：curl（通常系统自带）
# 用法：
#   chmod +x uat/smoke-test.sh
#   ./uat/smoke-test.sh                         # 使用默认目标地址
#   BASE_URL=http://localhost:8081 ./uat/smoke-test.sh
# ============================================================

set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8081}"
PASS=0
FAIL=0
SKIP=0
SMOKE_BODY_FILE="${SMOKE_BODY_FILE:-/tmp/luceon-smoke-body.$$}"

GREEN="\033[32m"
RED="\033[31m"
YELLOW="\033[33m"
CYAN="\033[36m"
RESET="\033[0m"

cleanup() {
  rm -f "$SMOKE_BODY_FILE"
}
trap cleanup EXIT

echo -e "${CYAN}============================================================${RESET}"
echo -e "${CYAN}  EduAsset CMS 冒烟测试${RESET}"
echo -e "${CYAN}  目标地址：${BASE_URL}${RESET}"
echo -e "${CYAN}  时间：$(date '+%Y-%m-%d %H:%M:%S')${RESET}"
echo -e "${CYAN}============================================================${RESET}"
echo ""

# ── 测试函数 ─────────────────────────────────────────────────

check() {
  local name="$1"
  local url="$2"
  local expected_status="${3:-200}"
  local expected_body="${4:-}"

  printf "  %-52s" "[$name]"

  local http_code
  local body
  rm -f "$SMOKE_BODY_FILE"
  body=$(curl -s -o "$SMOKE_BODY_FILE" -w "%{http_code}" \
    --max-time 10 \
    --connect-timeout 5 \
    "$url" 2>/dev/null) || { http_code="000"; }
  http_code="${body:-000}"
  local resp_body
  resp_body=$(cat "$SMOKE_BODY_FILE" 2>/dev/null || echo "")

  if [[ "$http_code" == "$expected_status" ]]; then
    if [[ -n "$expected_body" ]] && ! echo "$resp_body" | grep -qi "$expected_body"; then
      echo -e "${RED}✗ FAIL${RESET} (HTTP $http_code, body 不含 '$expected_body')"
      echo "    响应内容: $(echo "$resp_body" | head -c 200)"
      FAIL=$((FAIL + 1))
    else
      echo -e "${GREEN}✓ PASS${RESET} (HTTP $http_code)"
      PASS=$((PASS + 1))
    fi
  else
    echo -e "${RED}✗ FAIL${RESET} (期望 HTTP $expected_status, 实际 $http_code)"
    if [[ -n "$resp_body" ]]; then
      echo "    响应内容: $(echo "$resp_body" | head -c 200)"
    fi
    FAIL=$((FAIL + 1))
  fi
}

check_dependency_health_json() {
  local name="$1"
  local url="$2"

  printf "  %-52s" "[$name]"

  local body
  body=$(curl -fsS --max-time 20 --connect-timeout 5 "$url" 2>/dev/null || true)
  if [[ -z "$body" ]]; then
    echo -e "${RED}✗ FAIL${RESET} (dependency-health 不可达)"
    FAIL=$((FAIL + 1))
    return
  fi

  local summary
  local status
  set +e
  summary=$(printf '%s' "$body" | node -e '
let input = "";
process.stdin.on("data", chunk => input += chunk);
process.stdin.on("end", () => {
  try {
    const data = JSON.parse(input);
    const deps = data.dependencies || {};
    const submitProbeEnabled = deps.mineru?.submitProbe?.enabled === true;
    const ok = data.ok === true &&
      data.blocking === false &&
      deps.minio?.ok === true &&
      deps.mineru?.ok === true &&
      deps.ollama?.ok === true &&
      submitProbeEnabled === false;
    console.log(`ok=${data.ok === true} blocking=${data.blocking === true} minio=${deps.minio?.ok === true} mineru=${deps.mineru?.ok === true} ollama=${deps.ollama?.ok === true} submitProbe=${submitProbeEnabled}`);
    process.exit(ok ? 0 : 1);
  } catch (err) {
    console.log(`invalid-json ${err.message}`);
    process.exit(1);
  }
});
')
  status=$?
  set -e

  if [[ $status -eq 0 ]]; then
    echo -e "${GREEN}✓ PASS${RESET} (${summary})"
    PASS=$((PASS + 1))
  else
    echo -e "${RED}✗ FAIL${RESET} (${summary})"
    FAIL=$((FAIL + 1))
  fi
}

check_redirect() {
  local name="$1"
  local url="$2"

  printf "  %-52s" "[$name]"

  local http_code
  http_code=$(curl -s -o /dev/null -w "%{http_code}" \
    --max-time 10 \
    --connect-timeout 5 \
    "$url" 2>/dev/null) || http_code="000"

  if [[ "$http_code" == "301" || "$http_code" == "302" || "$http_code" == "200" ]]; then
    echo -e "${GREEN}✓ PASS${RESET} (HTTP $http_code)"
    PASS=$((PASS + 1))
  else
    echo -e "${RED}✗ FAIL${RESET} (期望 3xx/200, 实际 $http_code)"
    FAIL=$((FAIL + 1))
  fi
}

# ── 1. 前端访问 ───────────────────────────────────────────────
echo -e "${CYAN}【1】前端页面可达性${RESET}"
check_redirect "根路径重定向 /" "${BASE_URL}/"
check "CMS 主页 /cms/" "${BASE_URL}/cms/" "200" "<!doctype html"
check "SPA 路由 /cms/tasks" "${BASE_URL}/cms/tasks" "200" "<!doctype html"
check "SPA 路由 /cms/tasks/dummy-id" "${BASE_URL}/cms/tasks/dummy-id" "200" "<!doctype html"
check "SPA 路由 /cms/audit" "${BASE_URL}/cms/audit" "200" "<!doctype html"
check "Legacy 路由 /cms/source-materials" "${BASE_URL}/cms/source-materials" "200" "<!doctype html"
echo ""

# ── 2. 后端健康检查 ──────────────────────────────────────────
echo -e "${CYAN}【2】后端服务健康检查（通过 Nginx 代理）${RESET}"
check "upload-server /health" \
  "${BASE_URL}/__proxy/upload/health" "200" '"ok":true'
check "db-server /health" \
  "${BASE_URL}/__proxy/db/health" "200" '"ok":true'
echo ""

# ── 3. 主线依赖健康 ──────────────────────────────────────────
echo -e "${CYAN}【3】主线依赖健康（无 submit-probe）${RESET}"
check_dependency_health_json "dependency-health no-submit" \
  "${BASE_URL}/__proxy/upload/ops/dependency-health"
echo ""

# ── 4. DB API 基础功能 ────────────────────────────────────────
echo -e "${CYAN}【4】db-server REST API${RESET}"
check "获取素材列表 GET /materials" \
  "${BASE_URL}/__proxy/db/materials" "200"
check "获取设置 GET /settings" \
  "${BASE_URL}/__proxy/db/settings" "200"
echo ""

# ── 5. MinIO 代理可达性 ──────────────────────────────────────
echo -e "${CYAN}【5】MinIO 反向代理（/minio/）${RESET}"
# MinIO health 端点通过 Nginx /minio/ 代理访问
check "MinIO health via Nginx" \
  "${BASE_URL}/minio/minio/health/live" "200"
echo ""

# ── 6. MinIO 控制台（直接端口，仅 UAT 环境）─────────────────
echo -e "${CYAN}【6】MinIO 控制台（UAT 环境，可通过 MINIO_CONSOLE_URL 覆盖）${RESET}"
MINIO_CONSOLE_URL="${MINIO_CONSOLE_URL:-http://localhost:19001}"
printf "  %-52s" "[MinIO 控制台 $MINIO_CONSOLE_URL]"
http_code=$(curl -s -o /dev/null -w "%{http_code}" \
  --max-time 5 \
  --connect-timeout 3 \
  "$MINIO_CONSOLE_URL" 2>/dev/null) || http_code="000"
if [[ "$http_code" != "000" ]]; then
  echo -e "${GREEN}✓ PASS${RESET} (HTTP $http_code)"
  PASS=$((PASS + 1))
else
  echo -e "${YELLOW}⚠ SKIP${RESET} (控制台端口不可达，可忽略)"
  SKIP=$((SKIP + 1))
fi
echo ""

# ── 汇总 ─────────────────────────────────────────────────────
echo -e "${CYAN}============================================================${RESET}"
TOTAL=$((PASS + FAIL + SKIP))
echo -e "  结果汇总：${GREEN}通过 $PASS${RESET} / ${RED}失败 $FAIL${RESET} / ${YELLOW}跳过 $SKIP${RESET} (共 $TOTAL 项)"
echo -e "${CYAN}============================================================${RESET}"
echo "SMOKE_RESULT PASS=${PASS} FAIL=${FAIL} SKIP=${SKIP} TOTAL=${TOTAL}"
echo ""

if [[ $FAIL -gt 0 ]]; then
  echo -e "${RED}❌ 冒烟测试未通过，请检查上方失败项${RESET}"
  echo ""
  echo "  常见排查步骤："
  echo "  1. 确认服务已启动：./start-uat.sh --build（或先 pnpm build 再 ./start-uat.sh）"
  echo "  2. 查看 upload-server 日志：cat /tmp/cms-upload-server.log"
  echo "  3. 查看 db-server 日志：cat /tmp/cms-db-server.log"
  echo "  4. 确认 .env 中 CMS_PORT=8081 和 MINIO_PUBLIC_ENDPOINT 已正确配置"
  echo "  5. 确认 MinIO 在 \$MINIO_ENDPOINT:9000 可访问"
  exit 1
else
  echo -e "${GREEN}✅ 所有冒烟测试通过，系统运行正常${RESET}"
fi
