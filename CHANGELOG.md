# Changelog

## [v6.9.1] - 2026-05-16

### Milestone 6.9.1: Mainline Through And Governance Reset

- Preserves the current working mainline as a rollback anchor: upload -> MinIO -> local MinerU -> parsed artifacts -> Ollama `qwen3.5:9b` -> AI metadata -> operator review.
- Records Task 205 pressure-window evidence as sufficient for the 6.9.1 milestone boundary: 24/24 MinerU parses completed, 23/24 tasks reached review-pending/reviewing, and one AI-stage residual remains visible and manual-retry eligible.
- Retires the former role-dispatch workflow and archives its role contracts, task template, team contract, and workflow prompt material under `archive/team-model-retired-2026-05-16/`.
- Keeps `TaskAndReport/` as the historical evidence registry instead of an active role-dispatch surface.
- Adds `docs/codex/MILESTONE_6.9.1.md` as the milestone boundary and rollback note.

## [milestone-prd-v0.4-wave1] - 2026-04-22

### ✨ PRD v0.4 一期修订：任务流水线工程契约落地

#### 状态机与联动（PRD v0.4 §6 / §7）
- `AiMetadataWorker`：进入 Provider 调用前将关联 ParseTask 置为 `ai-running`，AI Job 终态字面量统一为 `confirmed / review-pending / failed`。
- `upload-server` `onComplete`：修正 ParseTask 终态映射（`confirmed → completed`、`review-pending → review-pending`、`failed → failed`），不再依赖旧字面量。
- `ParseTaskWorker`：启动时扫描失活的 `running / result-store / ai-pending` 任务，超时则置为 `failed` 并写事件。

#### 任务动作 API 与 SSE（PRD v0.4 §8 / §10）
- 新增：`POST /tasks/:id/retry | /reparse | /re-ai | /cancel | /review`、`POST /tasks/batch/retry`、`GET /tasks/stream`。
- 新增进程内任务事件总线 `server/lib/task-events-bus.mjs`，Worker / 动作 API 统一广播 `task-update`，SSE 探针心跳保活 25s。

#### 数据库与一致性扫描（PRD v0.4 §9 / §13）
- `db-server` 启动时自动将遗留状态归一化：ParseTask `success → completed`，AiMetadataJob `succeeded → confirmed`，幂等并支持回滚。
- `/materials` 列表排序改为 `updateTime DESC → createTime DESC → id 字典序 DESC`，不再假设 id 为数字。
- `consistency-routes` 重写为字符串 ID 全匹配；新增 `GET /audit/consistency`、`POST /audit/consistency/apply`，覆盖 Canonical 状态、孤儿任务 / Job、悬挂 aiJobId、`ai-running` 无活跃 Job、对象存储前缀等不变量。

#### 前端页面（PRD v0.4 §6.3 / §10.3）
- `TaskManagementPage`：按 Canonical 展示桶（queued / processing / reviewing / completed / failed / canceled）重写过滤与状态标签；新增 Retry / Reparse / Re-AI / Cancel / 审核 / 批量重试 / 新建任务 按钮；接入 SSE 实时增量刷新。
- `TaskDetailPage`：状态样式覆盖 Canonical；顶部新增动作按钮组；按 taskId 订阅 SSE 自动刷新。
- `Layout`：左侧导航首项改为「新建任务」，图标 `PlusCircle`。

#### 验证
- `node --check` 所有改动的后端文件全部通过。
- `tsc -p tsconfig.json --noEmit` 、 `pnpm build` 均通过，产物 `dist/assets/index-*.js ~599KB`。

---

## [milestone-6.6] - 2026-04-16

### 🧩 Docker 刷新后预览修复（PDF/Markdown）

#### 修复内容
- **Markdown 预览刷新恢复**：`/presign` 支持按 objectName 自动选择 parsedBucket，并返回同源 `proxy-file` URL，避免刷新后 `markdownObjectName` 指向错误 bucket 导致预览空白。
- **PDF 预览不再触发下载**：`/proxy-file` 在 MinIO 元数据为 `octet-stream` 时按扩展名兜底 `Content-Type`（PDF → `application/pdf`），避免被 Nginx `X-Content-Type-Options: nosniff` 影响而触发下载。
- **PDF Viewer 兼容性增强**：`/proxy-file` 支持 Range（字节范围）读取（`206 Partial Content`），提升 Chrome/Edge iframe 内嵌预览稳定性。

#### 影响范围
- Docker 部署环境下的资产详情页 PDF iframe 预览
- Docker 部署环境下的 Markdown 预览（刷新后）

---

## [v0.7.0] - 2026-04-14

### 🎉 Docker 部署首次验证通过 (Milestone)

这是项目第一个在生产级 Docker 环境下完成端到端功能验证的里程碑版本。

#### 核心变更
- **Docker 部署验证通过**：在 Mac Mini 局域网环境（`192.168.31.33:8081`）下，使用 Docker Compose 部署的完整系统成功通过测试。
- **MinerU 云端解析验证**：单个 PDF 文件（`FastTest01.pdf`）的 MinerU 解析流程在 Docker 环境下完整运行成功，从上传到获取解析结果全程无误。
- **Nginx 代理路由确认**：`/__proxy/mineru/` 路由正确代理到 `mineru.net`，请求头 `Authorization: Bearer <apiKey>` 正确转发。
- **MinerU API Key 配置说明更新**：文档中补充了 MinerU API Key 的正确配置方式（系统设置页面配置，不带 `Bearer ` 前缀）。

#### 文档更新
- **docs/deploy/DEPLOY.md**：新增 MinerU API Key 配置注意事项，明确配置方式与常见错误排查。
- **docs/codex/PROJECT_HISTORY.md**：阶段十新增"部署验证里程碑"记录，标记 Docker 部署首次测试通过。

#### 验证环境
- 宿主机：Mac Mini（`192.168.31.33`）
- 部署方式：Docker Compose（`docker-compose up -d --build`）
- 前端端口：`8081`（`CMS_PORT=8081`）
- MinerU 引擎：云端 API（`mineru.net`）
- 测试文件：`FastTest01.pdf`（16.73 KB）

#### 关键发现
- Docker 网络与 Nginx 代理层配置正确，问题根因为 MinerU API Key 配置不当（填写错误或带 `Bearer ` 前缀导致鉴权失败）。
- 系统在配置正确后，Docker 环境下的完整流水线（上传 → MinerU 解析 → 结果转存 → 展示）与开发环境行为一致。

---

## [v0.6.1] - 2026-04-11

### 🚀 稳定性与健壮性提升 (Stability & Robustness)

本次更新基于深度代码评审，重点修复了系统在极端情况下的稳定性隐患，优化了内存使用，并清理了冗余依赖。

#### 服务端 (Server)
- **优雅停机 (Graceful Shutdown)**: `db-server` 和 `upload-server` 新增了对 `SIGTERM` 和 `SIGINT` 信号的处理。在容器重启或意外退出时，`db-server` 会强制同步内存中的防抖数据到磁盘，避免数据丢失；`upload-server` 会等待进行中的请求完成。
- **内存优化 (OOM Prevention)**: `upload-server` 的 `multer` 存储引擎从 `memoryStorage` 迁移至 `diskStorage`。大文件上传时不再将完整内容驻留内存，而是使用临时文件缓冲，并在处理完成后自动清理，彻底解决了并发上传大文件时的 OOM 风险。
- **输入验证 (Input Validation)**: `db-server` 新增了基础的请求体验证中间件，拦截非对象请求体和原型链污染攻击，防止脏数据破坏内存缓存。

#### 前端 (Frontend)
- **静默失败提示 (Error Notification)**: 优化了 `appContext.tsx` 中的 `db-server` 同步逻辑。当后端服务不可用时，不再完全静默失败，而是在连续失败 3 次后通过 `sonner` 弹窗提示用户，并在服务恢复后自动通知。
- **全局错误恢复 (Error Boundary)**: 增强了 `ErrorBoundary` 组件，新增了错误堆栈展示和"重试"按钮，允许用户在不刷新页面的情况下尝试恢复组件状态。

#### 配置与依赖 (Config & Dependencies)
- **依赖清理 (Dependency Cleanup)**: 移除了 `package.json` 中未使用的 `@mui/material`、`@emotion/react` 和 `better-sqlite3` 依赖，减小了项目体积和构建时间。
- **Nginx 缓存修复 (Nginx Cache)**: 修复了 `docker/nginx.conf` 中静态资源长期缓存的 `alias` 路径映射问题，改用 `root` 指令确保带 hash 的 JS/CSS 文件能被正确缓存。
- **安全加固 (Security)**:
  - 移除了 `vite.config.ts` 中已废弃的 `X-Frame-Options`，简化了 `allowedHosts` 配置。
  - 更新了 `.env.example` 和 `docker-compose.yml`，强制要求用户在生产环境中修改 MinIO 的默认密钥 (`minioadmin`)。
- **类型修复 (TypeScript)**: 修复了 `types.ts` 和 `appContext.tsx` 中遗留的 TypeScript 类型报错，为配置接口添加了索引签名。
