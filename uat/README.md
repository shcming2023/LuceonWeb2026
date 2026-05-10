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
