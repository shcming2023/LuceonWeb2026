# EduAsset CMS — UAT 测试指南

**当前 UAT 默认目标环境：** `http://localhost:8081` 或局域网 `http://<HOST_IP>:8081`（可通过 `BASE_URL` 覆盖）
**MinIO 控制台：** `http://localhost:19001`（生产本地运行要求 local-only 绑定时以部署文档为准）

---

## 一、部署方式

### 方式 A：Docker 部署（推荐）

在宿主机上执行：

```bash
# 1. 进入项目目录
cd /path/to/Luceon2026

# 2. 确认 .env 已配置；当前本地 UAT 通常使用 CMS_PORT=8081
cat .env | grep CMS_PORT

# 3. 启动所有服务
docker compose up -d --build

# 4. 查看服务状态
docker compose ps

# 5. 验证部署
./uat/smoke-test.sh
```

**全新部署（清空所有数据）：**

```bash
docker compose down -v          # 停止并删除数据卷
docker compose up -d --build    # 重新构建并启动
```

### 方式 B：本地 Windows 二级验收环境 (Tier 2 UAT Baseline)

专门为 Windows 宿主机设计的隔离沙盒，不污染真实生产环境。

```powershell
# 1. 环境预检 (预先检查依赖与端口占用)
   npx pnpm@10.4.1 run local:check

# 2. 启动 Tier 2 环境 (包含本地 MinerU 与 Ollama)
docker compose -f docker-compose.yml -f docker-compose.local.yml -f docker-compose.override.yml up -d --build

# 3. 验证部署
bash uat/smoke-test.sh
```

> **提示：** 如果只想要验证 API 链路且不打算让电脑跑大模型，请追加 `-f docker-compose.tier2-lite.yml` 来启动轻量 Mock 档位。
>
> **提示：** 要使用当前第一阶段真实验证流程，请追加 `-f docker-compose.tier2-standard.yml`。启动 Standard 档前需确认本机 MinerU FastAPI 可通过 `LOCAL_MINERU_ENDPOINT` 访问，且本机 Ollama 存在 `qwen3.5:9b` 模型。

---

## 二、关键配置（`.env`）

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `CMS_PORT` | `8080` / UAT 常用 `8081` | 对外暴露端口；当前 UAT 脚本默认按 8081 验证 |
| `CMS_HOST` | `localhost` | 对外展示的主机名（启动信息中使用） |
| `MINIO_ENDPOINT` | `localhost` | MinIO 主机（容器内可达地址） |
| `MINIO_PUBLIC_ENDPOINT` | — | presigned URL 公开地址（如 `http://YOUR_HOST:8081/minio`） |
| `MINIO_ACCESS_KEY` | `minioadmin` | ⚠️ 生产环境请更换强密码 |
| `MINIO_SECRET_KEY` | `minioadmin` | ⚠️ 生产环境请更换强密码 |

---

## 三、冒烟测试（快速验证）

部署完成后运行：

```bash
./uat/smoke-test.sh

# 或指定目标地址
BASE_URL=http://YOUR_HOST:8081 ./uat/smoke-test.sh
```

**当前检查项：**

| # | 检查项 | 预期结果 |
|---|--------|---------|
| 1 | 根路径重定向 `/` | HTTP 302 → `/cms/` |
| 2 | CMS 主页 `/cms/` | HTTP 200，HTML 内容正常 |
| 3 | SPA 路由 `/cms/tasks` | HTTP 200 |
| 4 | SPA 路由 `/cms/tasks/dummy-id` | HTTP 200 |
| 5 | SPA 路由 `/cms/audit` | HTTP 200 |
| 6 | Legacy 路由 `/cms/source-materials` | HTTP 200 |
| 7 | `upload-server` 健康检查 | `{"ok":true}` |
| 8 | `db-server` 健康检查 | `{"ok":true}` |
| 9 | DB API `/materials` | HTTP 200，JSON 数组 |
| 10 | DB API `/settings` | HTTP 200 |
| 11 | MinIO 代理 `/minio/minio/health/live` | HTTP 200 |
| 12 | MinIO 控制台 | HTTP 可达则 PASS；不可达则 SKIP |

---

## 四、自动化 E2E 测试（Playwright）

```bash
npx pnpm@10.4.1 install
npx pnpm@10.4.1 --dir uat exec playwright install chromium

# 运行所有测试（默认 localhost:8081）
npx pnpm@10.4.1 --dir uat exec playwright test

# 指定目标地址和公网主机名
BASE_URL=http://YOUR_HOST:8081 PUBLIC_HOST=YOUR_HOST npx pnpm@10.4.1 --dir uat exec playwright test

# 有头模式（可见浏览器）
npx pnpm@10.4.1 --dir uat exec playwright test --headed

# 只运行特定测试组
npx pnpm@10.4.1 --dir uat exec playwright test --grep "MinIO"

# 查看 HTML 报告
npx pnpm@10.4.1 --dir uat exec playwright show-report playwright-report
```

**环境变量说明：**

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `BASE_URL` | `http://localhost:8081` | 测试目标地址 |
| `PUBLIC_HOST` | — | presigned URL 应包含的公网主机名（如 `192.168.31.33`），未设置时跳过主机名匹配 |

### 上传队列可靠性回归（本地样本目录）

```bash
cd uat
TEST_PDF_DIR="$(pwd)/../testpdf" \
BASE_URL=http://127.0.0.1:8081 \
npx pnpm@10.4.1 --dir uat exec playwright test tests/upload-queue-reliability.spec.ts
```

- `testpdf` 是本地验收样本目录，不随 Git 同步，不要提交大 PDF
- 复验前请确认目录存在且至少包含 10 个 PDF（会自动过滤 `.DS_Store`、`._*` 与非 PDF 文件）

**测试套件覆盖范围：**

| 测试组 | 测试内容 |
|--------|---------|
| 【1】页面加载与 SPA 路由 | 根路径重定向、各页面可访问性 |
| 【2】后端服务健康检查 | `upload-server`、`db-server` 健康端点 |
| 【3】DB API 基础功能 | 素材列表、设置读写（含自动清理） |
| 【4】MinIO Nginx 代理 | `/minio/` 可达性、presigned URL 地址验证 |
| 【5】文件上传流程 | 文件上传、presigned URL 局域网可访问性 |
| 【6】页面导航交互 | 核心路由 SPA 切换无错误 |
| 【7】处理链路与状态一致性 | PDF 与 Markdown 完整链路（MinerU + AI）状态收敛验证 |

---

## 六、维护与清理

### 1. 一致性审计
系统提供了自动化的数据一致性审计工具，可识别孤儿任务、丢失文件及冗余对象。

- **扫描入口：** `GET /__proxy/upload/audit/consistency`
- **导出报告：** 支持在 `/cms/audit` 页面直接导出 JSON/Markdown 审计报告。
- **系统健康：** 访问 `/cms/ops/health` 查看全链路实时状态。
- **历史诊断手册：** 参见 [reviews archive](../archive/phase1-governance-2026-05-06/docs-reviews/)。
- **当前治理摘要：** [PHASE1_ACCEPTANCE_SUMMARY.md](../docs/reviews/PHASE1_ACCEPTANCE_SUMMARY.md)

### 2. 测试产物管理
Playwright 运行产生的临时文件（`test-results/`、`playwright-report/`）已被 `.gitignore` 排除，无需手动提交。

---

## 五、手动验证清单

- [ ] 浏览器打开 `http://YOUR_HOST:8081`，自动跳转到 `/cms/tasks`
- [ ] 页面正常渲染，侧边栏导航可切换
- [ ] 在「任务管理」页面上传一个 PDF/Markdown 文件
- [ ] 上传成功后文件可在列表中显示，预览可正常加载
- [ ] 检查文件 URL 格式为 `http://YOUR_HOST:8081/minio/...`（非 `minio:9000`）
- [ ] 添加/修改数据后刷新页面，数据保持不变
- [ ] 访问「系统设置」→「测试 MinIO 连接」显示成功
- [ ] 访问 `http://YOUR_HOST:19001` 可登录 MinIO 控制台

---

## 六、常见问题排查

### Docker 部署模式

```bash
docker compose ps                              # 查看容器状态
docker compose logs -f upload-server           # 实时日志
docker compose restart upload-server           # 重启单个服务
```

### Node.js 直接部署模式

```bash
cat /tmp/cms-upload-server.log                 # upload-server 日志
cat /tmp/cms-db-server.log                     # db-server 日志
./start-uat.sh stop && ./start-uat.sh --build  # 重启所有服务
```

### MinIO 文件无法打开（presigned URL 报 403）

```bash
grep MINIO_PUBLIC_ENDPOINT .env   # 确认配置正确
grep MINIO_ENDPOINT .env          # 确认 MinIO 主机地址可达
curl http://YOUR_MINIO_HOST:9000/minio/health/live  # 验证 MinIO 可达
```

---

## 七、架构说明

```
局域网浏览器
    │
    ▼ http://YOUR_HOST:8081
┌─────────────────────────────────────────┐
│  Nginx (Docker) / proxy-server.mjs (Node)│
│  /cms/                → 静态文件 dist/   │
│  /__proxy/upload/*    → upload-server    │
│  /__proxy/db/*        → db-server        │
│  /minio/*             → MinIO:9000       │
│  /__proxy/mineru-local → :8083           │
│  /__proxy/tmpfiles    → tmpfiles.org（legacy）│
└─────────────────────────────────────────┘
         │                     │
    ┌────┘                     └────┐
    ▼                               ▼
upload-server (8788)          db-server (8789)
    │                               │
    ▼                               ▼
MinIO (MINIO_HOST:9000)       db-data.json
```

**MinIO presigned URL 修复原理：**

```
上传文件
  → upload-server 调用 MinIO SDK
  → SDK 生成: http://minio:9000/eduassets/originals/xxx.pdf?X-Amz-...
  → rewritePresignedUrl() 替换为:
             http://YOUR_HOST:8081/minio/eduassets/originals/xxx.pdf?X-Amz-...
  → 浏览器 GET http://YOUR_HOST:8081/minio/...
  → 代理转发到 MinIO:9000
  → 文件正常加载 ✓
```

---

## 八、阶段四基线复验流程 (Phase 4 Baseline Re-verification)

为了确保每一批小任务不破坏系统主链路，请在每一轮开发完成后执行以下标准复验流程：

### 1. 环境启动与冒烟测试
```bash
# 启动环境（确保后端代码最新）
docker compose up -d --build

# 执行后端 Worker 冒烟测试
node server/tests/worker-smoke.mjs

# 执行基础链路 Bash 冒烟
BASE_URL=http://127.0.0.1:8081 bash uat/smoke-test.sh
```

### 2. E2E 链路与一致性复验
```bash
# 执行完整 Pipeline 一致性 E2E（Playwright）
BASE_URL=http://127.0.0.1:8081 npx pnpm@10.4.1 --dir uat exec playwright test tests/pipeline-consistency.spec.ts

# 执行页面可用性回归（防止 React 运行时崩溃）
BASE_URL=http://127.0.0.1:8081 npx pnpm@10.4.1 --dir uat exec playwright test tests/pages-smoke.spec.ts

# 查看数据一致性审计结果 (Dry-run)
curl -sS http://127.0.0.1:8081/__proxy/upload/audit/consistency
```

### 3. 复验报告模板
复验完成后，请填写以下模板以供验收：

| 检查项 | 结果 / 状态 | 备注 |
| :--- | :--- | :--- |
| **Git Commit** | `{hash}` | 当前代码基准 |
| **Docker Health** | `Healthy` | `docker ps` 确认所有容器存活 |
| **MinerU / Ollama** | `Available` | 后端 logs 确认模型就绪 |
| **Smoke Test** | `Pass` | `smoke-test.sh` 无 Error |
| **Pipeline UAT** | `Pass` | Playwright `pipeline-consistency` 通过 |
| **Consistency Findings**| `Total: {n}` | 审计页面确认无新增 Unexpected Findings |
| **Flaky / Retry** | `None` | 测试过程中是否存在超时重试 |
| **Artifacts Hygiene** | `Clean` | `git status` 确认无产生 `package-lock.json` 等未忽略产物 |

---

## 九、Windows 与不同环境执行路径说明

### 1. 明确的命令兼容性
- **Windows 宿主机**：请使用 `npx.cmd pnpm@10.4.1` 代替 `npx pnpm@10.4.1`。
- **macOS / Linux / WSL / Bash**：请继续使用 `npx pnpm@10.4.1`。

### 2. 当前端口基线
- CMS Frontend / local UAT proxy：`8081`
- MinerU API：`8083`
- Ollama：`11434`
- MinIO Console：`19001`
- MinIO API：`9000` (仅限内部访问，外部通过 Nginx/minio 代理访问)

### 3. 三层验收路径
1. **轻量预检 (Tier 2 Lite)**：不强制拉取大体积模型和镜像。
   - 运行：`npx pnpm@10.4.1 run local:check`（Windows 可用 `npx.cmd pnpm@10.4.1 run local:check`）
   - 配置检查：`npx pnpm@10.4.1 run uat:docker:config`（Windows 可用 `npx.cmd pnpm@10.4.1 run uat:docker:config`）
   - **特性说明**：
     - **MinIO 自动建桶**：首次启动时 `cms-minio-init` 服务会自动创建并配置 `eduassets` 与 `eduassets-parsed` 桶，重复启动幂等。
     - **MinerU Mock**：内置轻量 Python 服务，提供 `/health` (HTTP 200) 健康检查支持，以满足依赖就绪前置条件。
2. **完整 Docker UAT**：本地或远端的完整测试沙盒，执行全部流程。
   - 运行：`docker compose up -d` 然后执行冒烟测试。
3. **手工浏览器验收**：在本地浏览器中通过 8081 端口和 19001 端口进行业务数据手工验收。

---

## 十、压力测试脚本

系统提供了独立的 Shell 压力测试脚本，用于验证批量上传和并发排队的稳定性。脚本风格与 `smoke-test.sh` 一致，不依赖 Playwright/Node.js 运行时。

### 前置依赖

| 工具 | 安装方式 | 说明 |
|------|---------|------|
| `curl` | 系统自带 | HTTP 请求 |
| `jq` | `brew install jq` (macOS) | JSON 解析 |
| `docker` | Docker Desktop | Worker 自愈验证需要 |
| `python3` | 系统自带 | 毫秒计时 |
| 样本 PDF | 手动准备 | 压力测试需要 `testpdf/` 目录 |

### 环境变量说明

| 变量 | 默认值 | 适用脚本 | 说明 |
|------|--------|---------|------|
| `BASE_URL` | `http://127.0.0.1:8081` | 全部 | 目标服务地址 |
| `TEST_PDF_DIR` | `../testpdf` | 24pdf, concurrency, worker-crash | 样本 PDF 目录 |
| `TEST_MD_DIR` | `../testmd` | concurrency | 样本 Markdown 目录 |
| `CONCURRENT_BATCH` | `8` | 24pdf | 每批并发提交数 |
| `BATCH_INTERVAL` | `10` | 24pdf | 批次间隔秒数 |
| `MAX_WAIT_MINUTES` | `60` (24pdf) / `10` (concurrency) | 全部 | 最大等待分钟数 |
| `POLL_INTERVAL` | `15` (24pdf) / `10` (concurrency) | 全部 | 状态轮询间隔秒 |
| `CHECK_KEEPALIVE` | `false` | 24pdf | 启用 Ollama keep-alive 检查 |

---

### stress-test-24pdf.sh — 24-PDF 批量压力测试

**用途**：验证系统在 24 个 PDF 批量提交下的稳定性和吞吐能力。

**执行**：

```bash
# 基本执行
bash uat/stress-test-24pdf.sh

# 自定义参数
BASE_URL=http://192.168.31.33:8081 TEST_PDF_DIR=../testpdf bash uat/stress-test-24pdf.sh

# 启用 Ollama keep-alive 检查
CHECK_KEEPALIVE=true bash uat/stress-test-24pdf.sh
```

**验证流程**：
1. 预检：dependency-health 全绿 + MinerU submit-probe 通过 + 准入电路关闭
2. 分 3 批提交 24 个 PDF（每批 8 个，间隔 10s）
3. 轮询终态直到全部完成或超时（最大 60min）
4. 输出报告：终态分布、耗时分布（P50/P95/Max）、一致性审计

**停止条件**：
- 全部到达终态 → 正常退出
- 超时 → FAIL
- 准入电路打开 → FAIL
- dependency blocked → FAIL
- 连续 3 轮无终态推进 → FAIL

**通过标准**：>= 80% 任务到达终态（completed 或 review-pending）

**预期输出示例**：

```
============================================================
  Luceon2026 24-PDF 压力测试
  目标地址：http://127.0.0.1:8081
  样本目录：../testpdf
  时间：2026-05-11 15:30:00
============================================================

【1】预检
  ✓ dependency-health 全绿
  ✓ MinerU submit-probe 通过
  ✓ 准入电路已关闭

【2】批量提交 (24 个 PDF)
  批次 1/3: 提交 8 个... ✓ (8/8 创建成功)
  批次 2/3: 提交 8 个... ✓ (8/8 创建成功)
  批次 3/3: 提交 8 个... ✓ (8/8 创建成功)
  总计：24/24 任务创建成功

【3】终态等待 (最大 60min)
  [15s] 24 个活跃: completed=0, review-pending=0, processing=24
  ...
  [6min] 0 个活跃: completed=20, review-pending=2, failed=2

【4】结果统计
  创建任务: 24
  到达终态: 22 (91.7%)
  ────────────────────────
  终态分布:
    completed:        20
    review-pending:    2
    failed:            2
    canceled:          0
  处理中:             0

【5】耗时分布
  P50: 245s  P95: 312s  Max: 340s

【6】一致性审计
  GET /audit/consistency: ok=true, findings=0

============================================================
  结果：✓ PASS（到达终态 ≥ 80%）
============================================================
```

---

### stress-test-concurrency.sh — 5+ 并发阶段排队验证

**用途**：验证高速并发提交下的阶段排队机制和串行处理保证。

**执行**：

```bash
bash uat/stress-test-concurrency.sh
BASE_URL=http://192.168.31.33:8081 bash uat/stress-test-concurrency.sh
```

**验证点**：
1. upload/storage 持久化后任务创建间隔 < 5s
2. MinerU heavy-stage active count ≤ 1（同一时刻仅 1 个任务处理）
3. AI Worker active count ≤ 1（同一时刻仅 1 个任务运行 AI）
4. 所有 5+5 个任务在 10 分钟内到达终态

---

## 十一、故障注入脚本

### fault-injection-admission.sh — 准入电路故障注入验证

**用途**：验证 MinerU 准入电路在不同故障场景下的行为（503 返回、Markdown 不受影响、恢复流程）。

**执行**：

```bash
# 测试 1：完全停止 MinerU
bash uat/fault-injection-admission.sh --mode mineru-down

# 测试 2：半故障（需手动模拟 /health OK, submit 500）
bash uat/fault-injection-admission.sh --mode mineru-half-failure

# 测试 3：恢复验证
bash uat/fault-injection-admission.sh --mode recovery
```

**模式说明**：

| 模式 | 说明 | 验证点 |
|------|------|--------|
| `mineru-down` | 完全停止 MinerU | POST /tasks 返回 503，Markdown 上传不受影响 |
| `mineru-half-failure` | 半故障（/health OK, submit 500） | submit-probe 失败，电路正确打开 |
| `recovery` | 恢复验证 | 仅 /health 恢复时电路保持打开，submit-probe 成功 → 冷却期 → 电路关闭 → PDF 恢复 |

**注意**：`mineru-down` 和 `mineru-half-failure` 模式执行过程中会提示用户手动操作 MinerU 服务。

---

### fault-injection-worker-crash.sh — Worker 异常终止自愈验证

**用途**：验证 upload-server 异常终止后 ParseTask Worker 的自愈恢复能力。

**执行**：

```bash
bash uat/fault-injection-worker-crash.sh
BASE_URL=http://192.168.31.33:8081 bash uat/fault-injection-worker-crash.sh
```

**注意**：此脚本涉及 `docker kill` 操作，启动时会提示用户确认。

**验证流程**：
1. 预检：dependency-health 全绿
2. 提交一个 PDF，等待进入 running 状态
3. 强制终止 upload-server 容器 (`docker kill`)
4. 重启 upload-server (`docker compose up -d upload-server`)
5. 等待恢复扫描完成
6. 验证 running 中的任务被重置为 pending
7. 验证 `parse-stale-running-recovered` 或 `parse-restart-recovered` 事件被记录
8. 等待任务完成完整流程（到达 review-pending/completed）
