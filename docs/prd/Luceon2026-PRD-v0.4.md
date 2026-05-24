# Luceon2026 PRD v0.4 —— 任务式文档解析与元数据审核工作台

- 文档版本：v0.4（综合修订版）
- 发布日期：2026-04-22
- 作者：Manus AI（基于多方评审意见、代码事实基线交叉核查后产出）
- 适用范围：Luceon2026 仓库（`shcming2023/Luceon2026`）下一阶段开发与联调
- 文档定位：**工程契约型 PRD**。本版本是一份独立自包含文档，替代 v0.2 与 v0.3，不需要与历史版本合并阅读即可完整理解需求与约束。
- 维护机制：6.9.1 里程碑后采用 Luceon/Lucode 双角色流程；Lucode 可提出产品/需求修订，Luceon 负责架构/验收边界审查和最终文档落账。历史 Lucia 维护规程已归档至 `archive/team-model-retired-2026-05-16/docs-prd/lucia-prd-maintenance.md`。

## 目录
1. 产品背景与本版修订动机
2. 产品目标与非目标
3. 官方原型对标：MinerU Extractor
4. 当前基线事实（Baseline Facts）
5. 用户角色与主流程
6. 统一状态机（Canonical State Machine）
7. 数据模型与对象命名约定
8. API 契约清单（已实现 / 待补齐 / 待废弃）
9. 一致性不变量与修复动作（Invariants & Repair Actions）
10. 下一阶段开发任务（Scope of v0.4）
11. 明确不做的事项（Out of Scope）
12. 验收标准（UAT）与度量指标
13. 风险、回退与发布策略
14. 对独立评审意见的核查结论
15. 术语表
16. 变更记录

---

## 1. 产品背景与本版修订动机

Luceon2026 起源于一个面向本地教育资源（以 PDF、Markdown 为主）的资料库管理工具。在过去数个迭代中，项目经历了两次关键转向：

- **第一次转向（v0.1 → v0.2）**：从"文件列表 + 元数据编辑"的资料库工具，转向"带解析管线与 AI 元数据识别的内容加工系统"。引入 MinerU（本地 FastAPI / 云端 API）作为解析引擎，引入 Ollama / OpenAI 兼容 Provider 作为元数据识别后端。
- **第二次转向（v0.2 → v0.4，本版）**：从以 `Material`（资料）为核心的"对象视图"，转向以 `ParseTask`（解析任务）为核心的"任务视图"，对齐官方 MinerU Extractor 的任务式交互范式。
- **第三次演进（v0.4 资产链迭代，Director 最新确认方向）**：正式确立 `PDF -> Raw Material -> Clean Material` 的可追溯资产链条。确立 Raw Material 为耐久的底层不变事实（包含 MinerU 解析产物与 AI 元数据）；Mineru2Table 为第一个 Clean Material 前置准备服务（负责基于 Raw 证据重建 TOC/章节/表格/逻辑结构）；RawMaterial2CleanMaterial 作为独立的后续清洗阶段（消费前两者的产出以生成干净语料）。任何后续层级都必须保留对源对象、任务 ID、服务版本和输出哈希的严格追溯能力（Provenance），且绝对不可隐式覆盖或删除前置证据。

项目进入 v0.4 阶段时，代码现状已经跑在 PRD v0.2 描述的"中后段"：Docker Compose、MinIO、`db-server`、`POST /tasks` 统一入口、`ParseTaskWorker`、`AiMetadataWorker`、Markdown 直通、AI 回填均已实现，并在 Mac Mini Docker 环境完成过端到端验证。但同时暴露出几个结构性问题：

1. **状态机事实上由多个模块共同解释**：前端列表页、资产详情页、`ParseTaskWorker`、`AiMetadataWorker`、`db-server` 各自对状态字符串做判断与映射（例如前端把 `success`、`ai-pending`、`completed` 都计入"已完成"，而 AI 回调又把 `confirmed` 映射为 `completed`），没有单一事实来源。
2. **新旧两条链路共存**：`POST /tasks` 已是新主入口，但 `POST /parse/analyze`、`POST /parse/local-mineru`、`POST /parse/download` 等旧端点仍与 `Material.metadata` 直接耦合，前端资产详情页的 `handleAiAnalyze` 仍走旧链路。
3. **ID 约定不一致**：`db-server` 已按字符串 ID 进行路由与存取，但 `materials` 列表排序仍按数字比较，部分一致性扫描脚本与旧代码仍隐含"数字 ID"假设。
4. **PRD v0.2 为"愿景型"而非"契约型"**：把"增加任务模型、队列、Worker、AI Job"列为下一阶段开发任务，但这些在代码上均已实现，PRD 已落后于代码。
5. **实时性与恢复机制不足**：前端缺乏统一的 SSE 任务事件推送，高度依赖手动刷新；`ParseTaskWorker` 缺乏类似 `AiMetadataWorker` 的启动恢复与超时自愈机制。

因此 v0.4 的修订动机是：**把 PRD 从"愿景型"升级为"工程契约型"**。把当前事实清清楚楚写下来，把字段与状态收敛成唯一契约，把下一阶段开发任务改为"稳定状态机、补齐 Retry/Re-AI、完善任务详情视图、引入 SSE 推送、修复一致性扫描"，让开发、测试、部署三方围绕同一份可验证文档工作。

## 2. 产品目标与非目标

### 2.1 产品目标

Luceon2026 在 v0.4 阶段的产品目标，用一句话表述为：

> **复刻官方 MinerU Extractor 的任务式交互，服务于本地教育资源的解析与元数据审核。**

具体拆解为以下四条：

1. **任务式主流程**：用户与系统的主要交互对象是"任务（Task）"而不是"资料（Material）"。用户的心智是"我创建了一个解析任务 → 我看着它在队列里推进 → 我查看它的结果 → 失败了我重试 → 成功了我导出"。
2. **可见的管线状态**：任意时刻，任意任务的状态都可以在任务列表与任务详情页被准确看到，不会出现"前端说在处理、后端其实已经失败"这类漂移。
3. **可控的失败恢复**：任何一步失败都不会让任务"消失"或"永远卡住"。系统既有 Worker 侧的超时自愈，也有用户侧的 Retry / Reparse / Re-AI 显式操作。
4. **可审可用的 AI 元数据**：AI 识别结果以结构化字段写回 `Material`，并对低置信度结果进入 `review-pending` 状态，等待人工在任务详情页审核确认。

### 2.2 非目标（本版不做）

> **注意：关于 Clean Material 的业务实现（如 Mineru2Table 接入、RawMaterial2CleanMaterial 清洗阶段、CleanServiceWorker 开发）均属于未来阶段，不在当前 Phase 1 已实现的基线范围内。当前 PRD 仅在架构契约上确立其为下一阶段的资产链条，但明确不在此版本进行业务代码落地。**

v0.4 明确不承担以下职责，避免再次出现"PRD 堆功能、工程跟不上"的偏差：

- 不引入新的大模型 Provider，不重写 Prompt 编排框架。现有 Ollama / OpenAI 兼容 Provider 足够。
- 不做多租户、多用户权限、审计日志这类企业化能力。
- 不做 Markdown 在线富文本编辑，仅提供只读预览与元数据表单编辑。
- 不做前端的大规模架构重构（例如从 Context + Zustand 混合状态迁移到完全服务端状态）。本版聚焦于"让现状稳定、让契约清晰"。
- 不做复杂 BPM 工作流引擎。

## 3. 官方原型对标：MinerU Extractor

本项目的参考原型为 [MinerU Extractor](https://mineru.net/OpenSourceTools/Extractor)。对标的重点不是 API 细节，也不是 UI 像素级复刻，而是**任务式交互体验**。从原型中可以清晰看到以下要点：

- 左侧导航以 **Create Task / Tasks / My Collections** 三段为主，Tasks 是一等公民。
- 创建任务支持 **Upload File** 与 **Web Link** 两种入口，并在入口处展示配额与限制（"5k/day、≤200p/file"）。
- 任务创建后进入队列，Tasks 页面列出每个任务的状态、进度与结果入口。
- 结果可被查看、导出（Markdown、JSON、ZIP）、加入 Collections 以便复用。
- 任务是独立的可寻址资源，可以被点开查看详情、失败可重试。

Luceon2026 v0.4 继承该范式，但做以下本地化裁剪：

| 维度 | 官方 MinerU Extractor | Luceon2026 v0.4 |
| :--- | :--- | :--- |
| 输入源 | 文件上传、Web 链接 | 仅文件上传（PDF 与 Markdown 直通） |
| 任务组织 | Create Task / Tasks / Collections | 工作台 / 任务管理 / 成果库 |
| 引擎 | MinerU 云端服务 | 本地 MinerU FastAPI（首选） + 云端 MinerU（回退） |
| AI 元数据 | 不提供 | 提供（Ollama / OpenAI 兼容，结果回写 Material） |
| 审核 | 不提供 | 提供（`review-pending` 状态 + 任务详情页表单审核） |
| 账号体系 | 登录强制 | 本地部署，默认无强制登录 |

## 4. 当前基线事实（Baseline Facts）

以下事实已在仓库 `shcming2023/Luceon2026` 当前 HEAD（`e7a08ec711c113be02ed9e4c356651bb443adc7b`）中验证，v0.4 以此为不可回退的基线。

### 4.1 部署与基础设施

- Docker Compose 包含：Nginx（反代 8081 → Node.js 服务）、`upload-server`、`db-server`、MinIO、本地 MinerU FastAPI（外挂，通过 `host.docker.internal:8083`）。
- 对象存储使用 MinIO，分为 `raw`（原始文件）与 `parsed`（解析产物）两个 Bucket。Markdown 与切图写入 `parsed` Bucket，以 `parsed/{materialId}/...` 为前缀。
- 持久化由 `db-server` 提供：内存 `dbCache` + 防抖落盘 + 备份文件恢复，具备优雅停机与数据不丢失的保证。
- v0.7.0 里程碑在 Mac Mini（`192.168.31.33:8081`）完成 Docker 部署端到端验证。

#### 4.1.1 本地第二级 UAT 基线（2026-05-02 已验证）

以下内容是 **Lucia + Director 本地第二级 UAT 环境契约**，用于后续日常开发补丁的本地沙盒验收；它不是生产部署契约，也不替代 luceonHMM 在真实 Mac mini 上执行的第三级真实验收。

- 本地预检入口为 `npx pnpm@10.4.1 run local:check`；Windows 宿主机可使用 `npx.cmd pnpm@10.4.1 run local:check`。该命令用于检查 Node/npm/npx、Docker daemon、Docker Compose、关键端口与 Compose 配置合法性。
- 本地轻量沙盒入口为 `docker compose -f docker-compose.yml -f docker-compose.tier2-lite.yml -f docker-compose.override.yml up -d --build`。
- Tier 2 Lite 档位包含 `cms-frontend`、`upload-server`、`db-server`、MinIO、Ollama 轻量服务、MinerU mock 与 `minio-init`。
- `minio-init` 在本地沙盒首次启动时幂等创建 `eduassets` 与 `eduassets-parsed`，不得删除 bucket、volume 或已有对象。
- MinerU mock 必须提供 `/health` HTTP 200，以满足依赖健康检查；该 mock 只用于验证链路连通性，不代表真实 MinerU 解析能力。
- Ollama 在 Tier 2 Lite 中不强制拉取模型；缺少模型时允许 AI Metadata Worker 走 skeleton fallback，并将任务推进到 `review-pending`，不得阻塞 Markdown 上传、MinIO 落盘或 Markdown 直通解析。
- 2026-05-02 本地二级 UAT 已验证 Markdown 上传链路：前端点按正常、Markdown 上传成功、原始文件写入 `eduassets`、ParseTask 创建、Markdown 直通产物写入 `eduassets-parsed`、AI skeleton fallback 闭环、任务进入 `review-pending`，一致性审计返回 `ok=true` 且 `findings=[]`。
- Tier 2 Lite 明确不验证真实 PDF MinerU 解析质量、不验证真实大模型推理质量、不作为稳定版标签依据；涉及真实大体积 PDF、真实历史数据、真实模型或公网/宿主机资源时，仍需由 Lucia 视里程碑级别决定是否转交 luceonHMM 执行第三级真实验收。

#### 4.1.2 本地第二级 UAT Standard 档决策（2026-05-06 已收口）

Tier 2 Standard 当前对齐第一阶段主线：本地真实 MinerU、MinIO、Ollama `qwen3.5:9b` 和禁止 AI skeleton fallback。旧版 online MinerU v4 + `qwen3.5:0.8b` 路线仅保留为 compatibility-only 历史上下文，不再作为当前主门槛。

- MinerU 使用本机 conda MinerU FastAPI，通过 `LOCAL_MINERU_ENDPOINT` 暴露给容器，默认 `http://host.docker.internal:8083`。
- Ollama 使用本机真实服务，通过 `OLLAMA_API_URL` 暴露给容器，默认 `http://host.docker.internal:11434`。
- AI 模型固定为当前主线 `qwen3.5:9b`，可通过 `OLLAMA_TIER2_MODEL` 覆盖；模型不可用时 Standard 预检必须失败。
- `DISABLE_AI_SKELETON_FALLBACK=true` 与 `ALLOW_AI_SKELETON_FALLBACK=false` 只表达“禁止 AI skeleton fallback”，不得隐式切换 MinerU 到 online 模式。
- online MinerU 仅可由 `MINERU_MODE=online`、`MINERU_ENGINE=online` 或 `MINERU_ONLINE_ENABLED=true` 显式开启；缺少 online 配置时不得影响当前本地真实运行主线。

### 4.2 统一任务入口与前端路由

- `POST /tasks`（`upload-server.mjs`）已实现：接收 multipart 上传，统一完成
  1. 写入 MinIO（`originals/{materialId}/{fileName}`）。
  2. Upsert `Material`（状态置为 `processing`，带 `metadata.provider/bucket/objectName`）。
  3. 创建 `ParseTask`（`engine: 'local-mineru'`, `state: 'pending'`, `stage: 'upload'`, 携带合并后的 `optionsSnapshot`）。
- 前端上传 hook `useFileUpload.ts` 已切换为调用 `/__proxy/upload/tasks`，并在注释中明确说明"不再手动 upsert Material，由后端 `/tasks` 统一负责"。
- 前端主路由已包含：`/tasks`（任务管理）、`/tasks/:id`（任务详情）、`/library`（成果库）、`/settings`（系统设置）、`/audit`（一致性审计）、`/ops/health`（系统健康）。`/workspace` 与 `/source-materials` 保留为兼容重定向到 `/tasks`，不再作为主入口。

### 4.3 解析与 AI Worker

- `ParseTaskWorker`（`server/services/queue/task-worker.mjs`）已实现：
  - 轮询 `state=pending` 的任务（当前间隔 10 秒），调用本地 MinerU FastAPI（`/tasks` + `/tasks/{id}` + `/tasks/{id}/result`），将 Markdown 与切图写入 MinIO。
  - 对 Markdown 原始输入走直通路径（不调用 MinerU）。
  - 完成后推进任务至 `ai-pending`，并通过 `metadata-job-client.mjs` 创建 `AiMetadataJob`（带去重保护）。
- `AiMetadataWorker`（`server/services/ai/metadata-worker.mjs`）已实现：
  - 严格串行（每轮最多 1 个 job），按 `createdAt` 升序挑选 `pending` job。
  - 支持 stale-running 自愈（超过 `defaultTimeoutMs + 60s` 缓冲期重置为 `pending`，并记录 `ai-stale-running-recovered` 事件）。
  - 支持 Ollama / OpenAI 兼容 Provider，按 `providers` 数组的 `enabled` 与 `priority` 选取。
  - 内容长度超过 32000 字符时截断并记录 `ai-content-truncated` 事件。
  - Provider 全部失败时 `degradeToSkeleton` 兜底，保证链路闭合。
  - 提取 JSON 鲁棒性已增强（支持 `<think>` 清理、代码块提取、花括号兜底解析）。
- `AiMetadataWorker` 通过 `onComplete(job, update)` 将结果回填（`upload-server.mjs` 第 3377–3434 行）：
  - 写 `Material.aiStatus`（`confirmed | review-pending → analyzed`，其它 → `failed`），并把结果并入 `Material.metadata`。
  - 写 `ParseTask.state`（`confirmed → completed`，`review-pending → review-pending`，其它 → `failed`），并把结果写入 `ParseTask.metadata`。

### 4.4 数据与 ID

- `db-server` 中 `materials`、`tasks`、`aiMetadataJobs`、`taskEvents`、`settings`、`secrets` 均为一等资源，路由全部按 `String(req.params.id)` 处理。
- `materials` 列表 `GET /materials` 返回时仍按数字做排序（遗留），这是一致性扫描需要修复的点之一。
- ParseTask ID 形如 `task-{timestamp}`，Material ID 既可能是前端生成的数字字符串，也可能是 `mat-{timestamp}`。

### 4.5 已知现实约束与遗留链路

- `upload-server.mjs` 仍是高耦合单体文件（上传、MinerU、AI、备份、审计等集中在一个入口）。
- ParseTask Worker 采用"定时扫描 + 内存锁"模式，尚非完整持久队列框架。
- ParseTask Worker 缺乏类似 AI Worker 的启动恢复与超时自愈机制。
- 任务事件目前可查询（`/task-events`），但未提供统一 SSE 事件流接口。
- 任务操作 API 仍偏基础（缺少标准化重试/取消/批量动作端点）。
- 旧端点仍然存在并被部分前端页面调用：
  - `POST /parse/local-mineru`：直接触发本地 MinerU 解析（非任务式）。
  - `POST /parse/analyze`：同步调用 AI 并直接改写 `Material.metadata`，不经由 `AiMetadataJob`。
  - `POST /parse/download`：将外部 ZIP 拉回并按 `parsed/{materialId}/` 前缀拆包到 MinIO。
- 资产详情页 `AssetDetailPage.tsx` 的 `handleMineruParse` 已迁移至 `/tasks`，但 `handleAiAnalyze` 仍走旧 `/parse/analyze`，写回目标仍是 `material.metadata`。

v0.4 不要求一次性删除这些旧端点，但要求把它们**明确标为遗留**，并在下一阶段改造到任务视图。

## 5. 用户角色与主流程

### 5.1 角色

本版本只定义一个角色：**本地操作员（Operator）**。负责上传资料、观察任务、审核 AI 结果、导出产物。

### 5.2 主流程

1. **上传与建任务**。Operator 在工作台页或任务管理页点击上传，前端通过 `/__proxy/upload/tasks` 发起 multipart 请求，后端同步完成 MinIO 落盘、Material upsert 与 ParseTask 创建，返回 `{ taskId, materialId }`。
2. **队列推进**。`ParseTaskWorker` 轮询 `pending` 任务，推进到 `running`，调用 MinerU 生成产物，切换到 `result-store` 写入 MinIO，完成后切换到 `ai-pending` 并创建 `AiMetadataJob`。
3. **AI 元数据**。`AiMetadataWorker` 串行处理 `pending` 的 AI Job，提取结构化元数据；高置信度直接终态 `confirmed`，低置信度进入 `review-pending`。在当前 Standard 严格模式下，Provider 全部失败必须进入 `failed`，不得生成 skeleton 结果；Lite 兼容档的 skeleton fallback 只能用于明确的轻量回归场景。`onComplete` 回填 Material 与 ParseTask。
4. **审核**。Operator 在任务详情页看到 `review-pending` 的任务，直接查看 Markdown、JSON 与可编辑的元数据表单，确认或修改后将任务置为 `completed`。
5. **重试与重跑**。对于 `failed` 任务，Operator 可发起 Retry（整任务重跑）或 Reparse（仅解析阶段重跑）；对 `completed`/`review-pending` 任务可发起 Re-AI（仅 AI 阶段重跑）。
6. **导出**。Operator 在任务详情页或任务列表中下载解析 ZIP（`/parsed-zip`）、Markdown、JSON。

## 6. 统一状态机（Canonical State Machine）

本章是 v0.4 的核心契约，所有前后端组件必须严格遵守。不允许任何模块把多个状态合并解释、或引入未列入下表的状态字符串。

### 6.1 状态定义与写入责任

| 状态 | 含义 | 唯一合法写入方 | 典型驻留时长 |
| :--- | :--- | :--- | :--- |
| `uploading` | 前端正在上传文件，后端尚未返回 `/tasks` 响应 | 前端 upload hook（可选本地态，不落 `tasks` 表） | 秒级 |
| `pending` | 任务已入库，等待 `ParseTaskWorker` 调度 | `upload-server` `POST /tasks` | 秒级–分钟级 |
| `running` | `ParseTaskWorker` 正在调用 MinerU 并轮询结果 | `ParseTaskWorker` | 分钟级 |
| `result-store` | 解析完成，正在把 Markdown / 图片写入 MinIO | `ParseTaskWorker` | 秒级 |
| `ai-pending` | 解析产物已落盘，`AiMetadataJob` 已创建、待 AI Worker 拾取 | `ParseTaskWorker` | 秒级–分钟级 |
| `ai-running` | `AiMetadataWorker` 正在调用 Provider | `AiMetadataWorker` | 秒级–分钟级 |
| `review-pending` | AI 结果置信度低于阈值或 `needsReview=true`，待人工审核 | `AiMetadataWorker.onComplete` | 天级 |
| `completed` | 全链路完成（高置信度自动终态，或人工审核通过） | `AiMetadataWorker.onComplete` / 审核 API | 持久终态 |
| `failed` | 解析或 AI 阶段发生不可恢复错误（降级到骨架后仍视为失败） | 各 Worker 异常分支 / `onComplete` | 持久终态（可重试） |
| `canceled` | Operator 主动取消 | 取消 API | 持久终态 |

> 说明：`ai-running` 为 v0.4 新增的显式状态，用于把"AI 阶段正在跑"从 `ai-pending` 里分离出来。当前代码中 `AiMetadataJob.state` 已有 `running`，在 `ParseTask.state` 中暂以 `ai-pending` 表达，v0.4 要求补齐 `ai-running` 在 ParseTask 上的写入。

### 6.2 合法流转边

下列是唯一允许的状态迁移集合：

```
uploading   → pending
pending     → running | canceled | failed
running     → result-store | failed | canceled
result-store→ ai-pending | failed
ai-pending  → ai-running | canceled | failed
ai-running  → review-pending | completed | failed
review-pending → completed | failed | canceled
failed      → pending            （Retry / Reparse 触发）
completed   → ai-pending         （Re-AI 触发，仅清理 AI 产物与状态）
review-pending → ai-pending      （Re-AI 触发）
```

任何其它迁移都必须被视作一致性缺陷，由一致性扫描记录与修复。

### 6.3 前端展示桶（Display Buckets）

为了避免"前端自行把多个状态合并成一个 UI 桶"这种分散解释，v0.4 统一如下展示桶：

| 展示桶 | 包含状态 |
| :--- | :--- |
| 等待中 | `pending`, `ai-pending` |
| 处理中 | `running`, `result-store`, `ai-running` |
| 待复核 | `review-pending` |
| 已完成 | `completed` |
| 已失败 | `failed` |
| 已取消 | `canceled` |

前端可以基于上表做筛选。`review-pending` 的 Operator-facing display bucket 必须显示为"待复核"，不得显示为"待审核"或归入"已完成"桶；`ai-pending` 也不得计入"已完成"桶（v0.2 代码中存在这种误判，v0.4 要求修复）。

## 7. 数据模型与对象命名约定

### 7.1 Material

```
{
  id: string,                  // 前端数字字符串或 mat-{ts}
  title: string,
  fileName: string,
  fileSize: number,
  mimeType: string,
  status: 'processing' | 'analyzed' | 'failed' | 'idle',
  mineruStatus?: 'pending' | 'running' | 'done' | 'failed',
  aiStatus?: 'pending' | 'running' | 'analyzed' | 'failed',
  tags?: string[],                       // Operator current tags / 人工当前标签事实源
  metadata: {
    provider: 'minio',
    bucket: string,
    objectName: string,                   // originals/{materialId}/{fileName}
    markdownObjectName?: string,          // parsed/{materialId}/full.md
    parsedPrefix?: string,                // parsed/{materialId}/
    archiveStatus?: {
      version: 'v0.1',
      hdd?: {
        status: 'pending' | 'synced' | 'verified' | 'failed',
        bundlePath?: string,              // HDD 归档包路径或逻辑对象名，不写入完整文件清单
        manifestPath?: string,            // manifest.json 路径或逻辑对象名
        checksum?: string,                // 归档包或 manifest 的 sha256 摘要
        syncedAt?: string,
        verifiedAt?: string,
        error?: string
      },
      offsite?: {
        provider: 'none' | 'gdrive-crypt' | 's3-compatible' | 'nas',
        status: 'not-configured' | 'pending' | 'synced' | 'verified' | 'failed',
        objectName?: string,              // 异地归档包对象名，不写入完整文件清单
        checksum?: string,
        syncedAt?: string,
        verifiedAt?: string,
        error?: string
      }
    },
    aiJobId?: string,
    aiAnalyzedAt?: string,
    // AI 提取的结构化元数据（subject/grade/chapter/tags/summary 等）
    ...
  },
  createTime: number,
  updateTime: number
}
```

关键约定：

- `id` 一律按字符串处理。后端不再对 `materials` 做数字排序，改为按 `updateTime DESC` 排序。
- `metadata.objectName` 与 `metadata.markdownObjectName` 必须使用 `originals/{id}/…` 与 `parsed/{id}/…` 前缀，禁止使用 `originals/{taskId}/…` 以保证"同一资料的产物收敛在同一前缀下"。
- `metadata.archiveStatus` 只能保存归档摘要、状态、校验值和 manifest 指针，禁止把 parsed 文件完整清单写入 DB。完整清单必须写在归档侧 `manifest.json` 中，避免再次引发 DB 大 payload/OOM。
- `Material.tags` 是 Operator current tags / 人工当前标签的后端事实源。人工在审核界面看到、添加、保存后的当前标签必须以 `Material.tags` 为准。
- `metadata.tags` 只表示 AI/解析阶段给出的标签来源，不等同于人工当前标签，也不得作为 Operator current tags 的事实源覆盖 `Material.tags`。
- v0.4 当前把 MinIO 视为解析与预览主事实源。HDD / offsite 归档在未完成恢复演练前，只能作为旁路备份，不得驱逐 MinIO 热区对象。

### 7.2 ParseTask

```
{
  id: string,                  // task-{ts}
  materialId: string,
  engine: 'local-mineru' | 'cloud-mineru' | 'markdown-passthrough',
  stage: 'upload' | 'mineru' | 'result-store' | 'ai' | 'review' | 'done',
  state: <Canonical State>,
  progress: number,            // 0–100，按 stage 分段
  message?: string,
  optionsSnapshot: {
    localEndpoint, localTimeout, backend, ocrLanguage,
    enableOcr, enableFormula, enableTable, maxPages,
    material                    // 创建时的 Material 快照
  },
  metadata: {
    markdownObjectName?: string,
    parsedPrefix?: string,
    aiJobId?: string,
    aiCompletedAt?: string,
    ...AI 结果
  },
  retryOf?: string,             // 若由 Retry/Reparse 产生，指向前一个 task-id
  createdAt: string,
  updatedAt: string
}
```

### 7.3 AiMetadataJob

```
{
  id: string,                  // ai-job-{ts}-{rand}
  parseTaskId: string,
  materialId: string,
  state: 'pending' | 'running' | 'review-pending' | 'confirmed' | 'failed',
  progress: number,
  providerId?: 'ollama' | 'openai-compatible',
  model?: string,
  inputMarkdownObjectName?: string,
  result?: object,             // 归一化的结构化元数据
  confidence?: number,
  needsReview?: boolean,
  message?: string,
  createdAt: string,
  updatedAt: string
}
```

v0.4 要求把 `AiMetadataJob.state` 的终态命名统一为 `confirmed | review-pending | failed`，废弃 `succeeded` 字面量。`metadata-job-client.mjs` 的去重集合需相应更新为 `{ pending, running, confirmed, review-pending }`。

### 7.4 TaskEvent

`taskEvents` 用于记录任务生命周期中的关键事件（`task-created`、`mineru-started`、`mineru-completed`、`ai-provider-request-started/succeeded/failed`、`ai-content-truncated`、`ai-stale-running-recovered`、`retry-requested` 等）。`taskId` 允许为 ParseTask ID 或 AI Job ID，`taskType` 区分 `parse | ai`。

## 8. API 契约清单

下表分三类：**已实现并保留**、**v0.4 必须补齐**、**标记为遗留待废弃**。

### 8.1 已实现并保留

| 方法 | 路径 | 说明 |
| :--- | :--- | :--- |
| `POST` | `/tasks` | 上传 + 建 Material + 建 ParseTask 的唯一入口 |
| `GET` | `/tasks` | 任务列表（支持按 state 过滤） |
| `GET` | `/tasks/:id` | 任务详情 |
| `PATCH` | `/tasks/:id` | Worker 写状态、前端写审核结果 |
| `DELETE` | `/tasks` | 批量删除任务记录（不影响 Material） |
| `GET` | `/ai-metadata-jobs` | AI Job 列表 / 过滤 |
| `GET` | `/ai-metadata-jobs/:id` | AI Job 详情 |
| `PATCH` | `/ai-metadata-jobs/:id` | AI Worker 更新 |
| `POST` | `/task-events` | 追加事件 |
| `GET` | `/task-events` | 查询事件（按 taskId） |
| `GET` | `/presign` | 为对象签发同源 proxy URL |
| `GET` | `/proxy-file` | 流式读取 MinIO 对象，支持 Range |
| `POST` | `/parsed-zip` | 将 `parsed/{materialId}/` 打包为 ZIP 返回 |

### 8.2 v0.4 必须补齐

| 方法 | 路径 | 语义 |
| :--- | :--- | :--- |
| `POST` | `/tasks/:id/retry` | 将 `failed` 任务整体重跑：克隆出新 ParseTask（`retryOf` 指向原任务），重新进入 `pending`，并清理 `parsed/{materialId}/` 下属于原任务的残留产物 |
| `POST` | `/tasks/:id/reparse` | 仅重跑解析阶段：保留 Material 的原文件，直接把当前任务从 `failed`/`completed` 置回 `pending`，Worker 会重新生成 Markdown 与图片 |
| `POST` | `/tasks/:id/re-ai` | 仅重跑 AI 阶段：删除或置失效当前 `aiJobId`，创建新 AI Job，并把 ParseTask 置回 `ai-pending` |
| `POST` | `/tasks/:id/cancel` | 将 `pending`/`ai-pending`/`review-pending` 任务置为 `canceled`，通知 Worker 放弃拾取 |
| `POST` | `/tasks/batch/retry` | 批量重试 `failed` 任务 |
| `POST` | `/tasks/:id/review` | 人工审核接口：接受修正后的元数据，写回 `Material.metadata`，并把任务置为 `completed` |
| `GET` | `/tasks/stream` | **SSE 接口**：实时推送任务状态变更与事件日志，替代前端高频轮询 |

### 8.3 标记为遗留、v0.5 再下线

| 方法 | 路径 | 遗留原因 | 过渡期要求 |
| :--- | :--- | :--- | :--- |
| `POST` | `/parse/local-mineru` | 绕过任务模型直接触发解析 | v0.4 内部不再新增调用点，仅保留兼容 |
| `POST` | `/parse/analyze` | 直接改写 `Material.metadata`，不经由 AI Job | 同上；资产详情页的 `handleAiAnalyze` 在 v0.4 内迁移到 `/tasks/:id/re-ai` |
| `POST` | `/parse/download` | 为"云端 MinerU ZIP 导入"而设，与任务模型解耦 | 维持现状，未来接入云端引擎时并入 ParseTask |

## 9. 一致性不变量与修复动作

> 这一章不写"系统会自然保证"，而写"**可被验证的不变量 + 对应修复动作**"。一致性扫描脚本必须能对每一条不变量生成可执行的修复建议。

### 9.1 ID 与引用

| 不变量 | 修复动作 |
| :--- | :--- |
| `ParseTask.materialId` 必须对应存在的 `Material.id`（字符串严格相等） | 若 Material 缺失：保留 Task，但写 `state=failed, message='orphan-task: material missing'`，并在任务详情页提示 |
| `AiMetadataJob.parseTaskId` 必须对应存在的 `ParseTask.id` | 若 ParseTask 缺失：把 Job 置为 `failed`，`message='orphan-ai-job'` |
| `Material.metadata.aiJobId`（若存在）必须对应一个真实 Job | 若对应 Job 缺失：清空 `aiJobId` 并把 `Material.aiStatus` 重置为 `pending` |
| 一致性扫描必须按字符串全匹配，不允许把 ID 转成 Number 比较 | 修复路由与脚本的数字比较遗留 |

### 9.2 对象存储

| 不变量 | 修复动作 |
| :--- | :--- |
| `Material.metadata.objectName` 必须以 `originals/{materialId}/` 开头 | 扫描发现异常时记录告警；不自动移动文件 |
| `Material.metadata.markdownObjectName`（若存在）必须以 `parsed/{materialId}/` 开头 | 同上 |
| `ParseTask.state ∈ {completed, review-pending}` 时，`parsed/{materialId}/full.md` 必须存在 | 若缺失：把 ParseTask 置为 `failed`，提示运行 Reparse |
| `mode=user` 导出 ZIP 且存在 `full.md` 时，禁止在 ZIP 内重复包含原始大模型输出的同名或同内容主 Markdown | 若为 legacy 数据（无 `primaryMarkdownPath`）：后端基于内容比对进行动态启发式去重（Dynamic Deduplication），跳过内部重复 md。 |
| `archiveStatus.hdd.status ∈ {synced, verified}` 时，必须存在可读取的 `manifestPath` 与 `bundlePath`，且 checksum 能通过校验 | 若缺失或校验失败：将对应归档状态置为 `failed`，不得删除 MinIO 热区对象 |
| `archiveStatus.offsite.status ∈ {synced, verified}` 时，必须存在可追踪的 `provider/objectName/checksum` | 若缺失：将 offsite 状态置为 `failed`，不得把该资料计入“异地已备份” |
| DB 不得保存归档包内部的完整 parsed 文件清单 | 若发现 `archiveStatus` 或 `metadata` 中写入大文件清单：迁移到外部 `manifest.json`，DB 仅保留摘要 |

### 9.3 状态与 AI Job 的联动

| 不变量 | 修复动作 |
| :--- | :--- |
| `ParseTask.state=ai-running` 时，必存在一个 `AiMetadataJob.state ∈ {pending, running}` 且 `parseTaskId` 匹配 | 若缺失：把 ParseTask 置回 `ai-pending`，让 Worker 重新创建 Job |
| `AiMetadataJob.state=running` 且 `updatedAt` 超过 `timeoutMs + 60s` | `AiMetadataWorker.recoverStaleRunningJobs` 将其重置为 `pending`（已实现） |
| `ParseTask.state=running` 且 `updatedAt` 超过 `MINERU_TIMEOUT + 60s` | v0.4 待补：`ParseTaskWorker` 增加对应 stale-recovery |

### 9.4 前端桶与状态字符串

| 不变量 | 修复动作 |
| :--- | :--- |
| 前端任何列表/筛选必须完整支持第 6.3 节"展示桶"表，禁止自创桶 | 在一致性扫描中对前端枚举进行静态检查（可通过约定的 `STATE_BUCKETS` 常量集中管理） |
| `review-pending` 不得被算进"已完成"桶 | 修复 `TaskManagementPage.tsx` 中把 `ai-pending` 误并入"completed" 的逻辑 |

## 10. 下一阶段开发任务（Scope of v0.4）

按优先级从高到低列出。v0.4 的里程碑目标是：**所有 P0 项完成并通过 UAT；P1 项作为收敛项；P2 项按排期推进。**

### 10.1 P0 — 稳定状态机与重启恢复

1. **对齐 Canonical 状态机**。在 `server/services/queue/task-worker.mjs`、`server/services/ai/metadata-worker.mjs`、`server/upload-server.mjs` 内把所有状态字面量统一到第 6.1 节十项。
2. **废弃 `succeeded`**，统一使用 `confirmed` 作为 AI Job 的成功终态；更新 `metadata-job-client.mjs` 的去重集合。
3. **补齐 `ai-running` 写入**。`AiMetadataWorker` 进入 Provider 调用前，除了写 `AiMetadataJob.state=running`，也要把对应 `ParseTask.state` 写为 `ai-running`。
4. **补齐 `ParseTaskWorker` 的 stale-recovery**，超时阈值读取 `optionsSnapshot.localTimeout`。启动时扫描 `pending/running/ai-pending` 任务并执行补偿。

### 10.2 P0 — 任务动作 API 与 SSE 推送

1. 按第 8.2 节实现 Retry / Reparse / Re-AI / Cancel / Review / Batch Retry API，并提供 OpenAPI 样例。每个接口都要写 `taskEvents`。
2. 实现 `/tasks/stream` SSE 接口，推送任务状态变更与事件日志。前端任务管理页与详情页接入 SSE 替代高频轮询。

### 10.3 P0 — 任务详情页（Task Detail Page）与管理页增强

1. **任务详情页 (`/tasks/:id`)**：
   - **头部**：任务 ID、Material 标题、引擎、创建时间、当前状态徽章、进度条。
   - **操作区**：按状态动态呈现 `重试 / 重新解析 / 重新 AI / 取消 / 审核通过 / 保存元数据 / 下载 ZIP` 按钮。
   - **Tab 1 Markdown**：从 `/presign` 取 `markdownObjectName` 渲染只读 Markdown。
   - **Tab 2 原件预览**：PDF 使用 `/proxy-file` 嵌入预览（Range 支持已具备）。
   - **Tab 3 AI 元数据 / MetadataTab**：以表单呈现 `result` 字段；`review-pending` 时可编辑并提交至 `/tasks/:id/review`。默认信息架构必须按"审核摘要 → 当前保存值 → AI 建议与证据 → 技术详情"组织，其中技术详情（`Technical Details`）默认折叠。
   - **Tab 4 事件日志**：按时间倒序展示 `taskEvents`，支持级别过滤。
2. **任务管理页 (`/tasks`)**：
   - 支持按状态筛选、搜索、失败聚合。
   - 提供单任务重试与批量重试。
   - 在列表中展示阶段、进度、最近事件。

### 10.4 P1 — 一致性扫描对 String ID 的完全支持与服务拆分

1. 修正 `GET /materials` 的排序为 `updateTime DESC`，去掉数字比较。
2. 重写一致性扫描脚本（`server/lib/consistency-routes.mjs`），对每条不变量生成具体的修复建议，打印到日志并回写到 `taskEvents`（`consistency-checked`）。
3. 在任务详情页"事件日志"中展示扫描结果。
4. **`upload-server.mjs` 第一阶段拆分**：将路由（routes）与服务（services）分离，固化任务域与资源域边界。

### 10.5 P1 — 资产详情页向任务详情页过渡

- `AssetDetailPage.tsx` 的 `handleAiAnalyze` 改为调用 `POST /tasks/:id/re-ai`；
- 页面上方增加 "查看任务"跳转；
- 原"手动触发 MinerU"按钮保留，但底层走 `/tasks/:id/reparse`。

### 10.6 P2 — 文档与运维

- README、docs/deploy/DEPLOY.md 更新至 v0.4 的任务式心智。
- Docker Compose 健康检查：为 `upload-server`、`db-server`、`MinIO` 增加 `healthcheck`。
- 一致性扫描以 `GET /__proxy/upload/audit/consistency` 为当前入口，执行结果可在运维审计页复核。

### 10.7 P1/P2 — 存储生命周期与归档防线

本节来自 2026-05-02 对《Luceon2026 存储架构演进方案 V2.0》的独立评估。v0.4 当前只固化“旁路归档与可恢复性”原则，不直接固化 Google Drive、透明回源或自动驱逐策略。

#### 10.7.1 已确定需求

1. **先归档，不驱逐**。新增任何存储生命周期能力时，第一阶段只能做只读审计、归档、校验和恢复演练，不得删除 MinIO 热区对象。
2. **归档必须基于 manifest**。每个 Material 的归档产物必须包含：
   - `manifest.json`：记录 materialId、objectName、parsedPrefix、parsedFilesCount、bundle 文件名、checksum、生成时间与版本。
   - 原始文件归档。
   - parsed 产物归档包（ZIP / TAR.ZST 等格式待验证）。
   - `checksums.sha256` 或等价校验文件。
3. **DB 只保存摘要**。`Material.metadata.archiveStatus` 只保存状态、指针、checksum、时间戳和错误摘要；完整文件清单不得写入 DB。
4. **DB 快照是独立保护对象**。db-server 的 JSON 数据、secrets/config、taxonomy 版本与归档 manifest index 需要进入快照策略；恢复脚本必须能在独立环境中验证快照可用。
5. **恢复优先于透明回源**。冷/温数据访问第一阶段应表现为“恢复任务”，先把归档包恢复回 MinIO，再复用现有预览/下载链路。

#### 10.7.2 待验证策略

以下内容暂不得作为稳定开发需求，只能作为后续 PoC 或 Research Patch：

1. **Google Drive + rclone crypt 作为异地冷备候选**。该策略受 Google Drive API quota、上传限制、服务条款、账号合规与密钥保管影响，必须先完成合规与可用性验证。
2. **HDD 解压态目录作为近线查询缓存**。HDD 可保存归档包；是否同时维护解压态缓存，需要根据小文件数量、随机 IO、恢复速度与校验成本实测决定。
3. **高低水位线自动淘汰**。自动驱逐 MinIO 对象必须等归档、校验、恢复演练稳定后才可评估；默认先考虑驱逐 parsed，不驱逐 raw。
4. **透明回源**。透明回源会侵入 `/proxy-file`、`/parsed-zip`、详情页预览和任务重解析链路，需在恢复任务模型稳定后再评估。

#### 10.7.3 下一步最小任务

下一步只允许下达只读研究任务：

`P1 Research Patch：Luceon 存储占用审计、归档 manifest 契约与只读容量报告`

关闭标准：

- 只读统计 MinIO raw/parsed 占用、对象数、按 materialId 的分布、最大 parsed 对象数、DB 文件大小与近似日增长。
- 输出 `archive-manifest.v0.1` 草案和样例。
- 不移动、不删除、不上传云端、不修改现有 MinIO 对象。
- 给出 HDD / offsite / watermark 的下一步可行性判断，但不实现驱逐。

## 11. 明确不做的事项（Out of Scope）

- **云端 MinerU 的任务化改造**：本版仍以本地 MinerU FastAPI 为主链路，云端接入留待 v0.5。
- **多用户登录与权限**：本版仍是单操作员本地部署。
- **Markdown 在线编辑器**：仅保留只读预览。
- **新 Provider 接入**：v0.4 不新增 AI Provider。
- **全面前端状态重构**：v0.4 只纠正状态字符串与展示桶，不做状态管理框架的更替。
- **业务代码层面的 Clean Material 落地**：当前版本不包含对 `CleanServiceWorker` 的代码实现、Mineru2Table 的服务编排或任何产生真实 Clean Material 的生产环境重构，这些仅在文档设计中作为未来可追溯资产链进行约束。

## 12. 验收标准（UAT）与度量指标

### 12.1 功能验收清单

1. 上传一个 20 MB 内 PDF，任务依次经过 `pending → running → result-store → ai-pending → ai-running → completed`，全程前端桶展示正确，SSE 实时推送状态变更。
2. 上传一个 Markdown 文件，任务经过 `pending → ai-pending → ai-running → completed`，跳过 MinerU。
3. 故意让本地 MinerU 不可用，任务在 `running` 超时后自动 `failed`；Operator 点 Retry 后任务重新从 `pending` 开始。
4. 强制 AI Provider 失败，任务进入 `failed`；Operator 点 Re-AI 后 AI 阶段重跑，成功进入 `review-pending` 或 `completed`。
5. 对 `review-pending` 任务，Operator 修改元数据并提交，任务进入 `completed`，Material 元数据同步更新。
6. 重启 `upload-server` 与 `db-server`，所有任务状态保持，`running`/`ai-running` 中的僵尸任务在宽限期后被自愈回 `pending`。
7. 一致性扫描对一个人为制造的 orphan 任务生成修复建议，并在任务详情页事件日志中可见。

### 12.2 度量指标（观测用，不做硬门槛）

- `/tasks` 创建到 `pending` 落库的 P95 延迟 < 1s。
- `AiMetadataWorker` 每轮扫描耗时 < 2s（空载）。
- 一次完整 PDF 任务（20 MB 以内）端到端 P95 < 180s（依赖本地 MinerU 性能）。

### 12.3 本地第二级 UAT 基线验收（Tier 2 Lite）

本节定义日常开发补丁进入 Lucia 验收时的本地二级轻量回归基线。该基线服务于快速验证主链路可用性，不验证真实 PDF 解析质量和真实 AI 推理质量。

1. **预检**：执行 `npx pnpm@10.4.1 run local:check`；Windows 宿主机可使用 `npx.cmd pnpm@10.4.1 run local:check`。Docker daemon、Docker Compose、Compose config 与关键端口检查均应输出可解释结果。若沙盒已启动，端口占用可作为"已有服务运行"提示，不直接判失败。
2. **启动**：执行 `docker compose -f docker-compose.yml -f docker-compose.tier2-lite.yml -f docker-compose.override.yml up -d --build` 后，`cms-frontend`、`upload-server`、`db-server`、MinIO、MinerU mock 与 Ollama 容器应处于可访问状态；`minio-init` 可正常退出 0。
3. **依赖健康**：`GET /__proxy/upload/ops/dependency-health` 中 `dependencies.minio.ok=true`、`dependencies.mineru.ok=true`、`blocking=false`。`dependencies.ollama.ok=false` 且缺模型时不阻塞 parse/upload。
4. **前端手动检查**：Director 在 `http://127.0.0.1:8080/cms/` 点按主要页面与导航，确认页面可加载、路由可切换、无明显前端崩溃。
5. **Markdown 上传主链路**：上传一个小型 Markdown 文件后，应创建 Material 与 ParseTask；原始文件写入 `eduassets/originals/{materialId}/...`；Markdown 直通产物 `full.md` 与 `artifact-manifest.json` 写入 `eduassets-parsed/parsed/{materialId}/...`。
6. **AI 降级闭环**：Tier 2 Lite 缺少本地模型时，AI Metadata Worker 允许记录 provider 失败事件并生成 skeleton fallback；最终任务状态应进入 `review-pending`，Material 进入可人工复核状态。
7. **一致性审计**：上传链路完成后，`GET /__proxy/upload/audit/consistency` 应返回 `ok=true`，且不产生新增 unexpected findings。
8. **自动化回归要求**：下一步 P0 开发任务 `P0-markdown-upload-regression` 必须将上述 Markdown 上传主链路沉淀为可重复执行的 smoke test，并纳入后续 Lucia 二级验收默认检查项。

### 12.4 本地第二级 UAT Standard 验收（本地真实 MinerU + 本地 Ollama）

本节定义 Tier 2 Standard 的当前验收口径。该档位用于验证真实 PDF 解析入口、真实 AI 连通性和更接近生产的依赖编排；它不替代第三级真实大数据/压力验收。

1. **MinerU 接入方式**：Standard 档使用本机 conda MinerU FastAPI，不使用 MinerU mock，不要求 online MinerU token。
2. **Ollama 模型要求**：本机 Ollama 必须可达，且 `qwen3.5:9b` 必须存在。Ollama 不可达或模型不可用均视为 Standard 环境未就绪。
3. **依赖健康**：Standard 预检必须同时确认 CMS、MinIO、本地 MinerU、Ollama、后端 dependency-health 均满足要求；任一关键项失败，不得打印通过结论。本地 MinerU 检查不得只依赖 `/health`，还必须通过 `mineruSubmitProbe=true` 验证 `POST /tasks` 可返回有效任务 ID。
4. **Markdown 回归**：Standard 档不得破坏 `P0-markdown-upload-regression` 中已固化的 Markdown 上传、MinIO 落盘、任务创建、AI Job 和一致性审计闭环。
5. **PDF 解析入口**：上传小型 PDF 后，任务必须真实进入 MinerU pipeline；若轮询结束仍未观察到 MinerU 执行痕迹，smoke test 必须失败，并输出最后一次任务状态、message 与 metadata 摘要。
6. **状态约束**：Standard 不允许使用 MinerU mock 或 AI skeleton fallback 来证明 PDF 解析链路成功；Lite 档可继续保留 mock 和 AI skeleton fallback 以服务快速回归。
7. **放行状态**：截至 2026-05-06，`uat/smoke-test.sh`、`pages-smoke.spec.ts` 与 `pipeline-consistency.spec.ts` 已按当前主线通过。

## 13. 风险、回退与发布策略

### 13.1 主要风险

1. **旧端点与新 API 并存导致的数据漂移**：`AssetDetailPage` 在迁移期间仍可能走 `/parse/analyze`，导致 AI 结果不经过 Job。缓解：在迁移期内，`/parse/analyze` 内部改为"创建一个 AiMetadataJob 并立即 run"的桥接实现。
2. **状态字面量历史遗留**：数据库中可能存在 `success`、`succeeded` 等旧值。缓解：v0.4 启动时跑一次性的状态归一化迁移。
3. **一致性扫描的误杀**：修复动作若直接改写状态，可能误伤正在进行中的任务。缓解：所有修复动作默认"仅记录、不自动写回"，由 Operator 在详情页点击确认后再执行。
4. **把消费级云盘误用为生产级灾备**：Google Drive 等个人/机构云盘存在 API quota、上传限制、服务条款和账号策略风险。缓解：在完成合规与 PoC 前，只能作为候选 offsite backend，不得写成唯一灾备承诺。
5. **归档/驱逐导致热区数据误删**：若未完成校验与恢复演练就启用水位线淘汰，可能删除仍被业务依赖的 MinIO 对象。缓解：v0.4 阶段禁止自动驱逐；未来驱逐必须依赖 `archiveStatus.*.status=verified` 和可审计 dry-run。
6. **DB 再次承载大 payload**：如果把 parsed 文件完整清单或归档索引写入 `Material.metadata`，可能重现 DB OOM。缓解：DB 仅保存 manifest 指针和摘要，完整清单写在归档对象中。

### 13.2 回退策略

- v0.4 通过 Docker Compose 发布，镜像带明确 Tag；如发现严重问题可回退至 v0.7.0（Docker 里程碑）镜像。
- 数据库为 JSON，回退后使用同目录备份文件恢复即可。

### 13.3 发布节奏建议

- 第 1 周：状态机归一化 + Retry/Reparse/Re-AI API + 状态字面量迁移脚本 + ParseTaskWorker 启动恢复。
- 第 2 周：SSE 推送接口 + 任务详情页/管理页上线；资产详情页的 `handleAiAnalyze` 迁移。
- 第 3 周：一致性扫描改造 + `upload-server` 拆分 + UAT 全量验收 + 文档刷新。

## 14. 对独立评审意见的核查结论

用户在下达本次修订指令时附上了两份独立评审分析（分别对应 v0.2 和另一团队的 v0.3）。本节记录 Manus AI 的独立核查与采纳结论，避免盲目采纳或盲目否决。

| 评审观点 | 核查结论 | 是否采纳 |
| :--- | :--- | :--- |
| "PRD v0.2 方向正确：从资料库工具转成文档解析任务工作台" | 与仓库现状一致：`/tasks` 已是主入口，Worker 已跑通 | 采纳为 v0.4 的产品目标 |
| "官方原型的关键不是某个 API 细节，而是任务式体验" | 通过访问 `mineru.net/OpenSourceTools/Extractor` 交叉验证：Create Task / Tasks / Collections 是一等导航 | 采纳，写入第 3 章 |
| "PRD v0.2 最大问题是落后于代码" | 交叉核对 `upload-server.mjs`、`task-worker.mjs`、`metadata-worker.mjs`、`db-server.mjs` 后确认 | 采纳，引入第 4 章"Baseline Facts"概念 |
| "必须定义唯一 canonical 状态机，不允许页面各自解释" | 在 `TaskManagementPage.tsx` 发现把 `ai-pending` 误并入"completed"桶的分散解释证据；在 `onComplete` 中发现 `confirmed/review-pending → completed` 的二次映射 | 采纳，新增第 6 章 |
| "一致性条款改成可验证不变量 + 修复动作" | 当前 `consistency-routes.mjs` 对字符串 ID 的处理不完整；修复需要显式动作 | 采纳，新增第 9 章并显式 P1 任务 |
| "下一步不是加新模型而是稳定状态机、补 Retry/Reparse/Re-AI、修一致性扫描、补任务详情视图、扩 UAT" | 与仓库现状吻合；已有的 `/tasks/:id` 前端跳转存在但详情页尚未成熟 | 采纳，作为第 10 章 P0/P1 |
| "PRD 需要从愿景型升级为工程契约型" | 这是 v0.4 的根本定位调整 | 采纳，作为文档版本定位写在扉页 |
| "评审建议的 canonical 状态集 `uploading, queued, mineru-running, result-storing, ai-pending, ai-running, review-pending, completed, failed, canceled`" | 与当前代码字面量（`pending`、`running`、`result-store`、`ai-pending`、`review-pending`、`completed`、`failed`）存在命名差异。若直接采用评审命名（`queued`、`mineru-running`、`result-storing`）会产生一次数据迁移且语义收益有限 | **部分采纳**：引入 `ai-running` 作为补齐；保留 `pending`、`running`、`result-store` 的既有命名，减少一次破坏性迁移。状态集合与流转见第 6 章 |
| "无统一任务事件推送（仍以页面手动刷新/轮询为主）" | 核查代码确认，`TaskDetailPage.tsx` 依赖手动刷新，后端无 SSE 接口 | 采纳，新增 `/tasks/stream` SSE 接口作为 P0 任务 |
| "队列恢复与重试策略仍不完整（尤其 ParseTask 链路）" | 核查代码确认，`AiMetadataWorker` 有 `recoverStaleRunningJobs`，但 `ParseTaskWorker` 没有 | 采纳，将 `ParseTaskWorker` 的启动恢复与超时自愈列为 P0 任务 |
| "前端主入口仍以 Material 工作台为中心，尚未完全转为'新建任务 + 任务管理'双核心" | 核查代码确认，`WorkspacePage.tsx` 仍是主入口，顶层导航有"任务管理"但无"新建任务" | 采纳，明确前端页面改造目标 |
| "`upload-server.mjs` 仍是高耦合单体文件" | 核查代码确认，该文件包含路由、业务逻辑、Worker 调度等 | 采纳，将服务拆分列为 P1 任务 |

结论：评审意见的方向与重点全部采纳；在**状态命名**上选择"最小破坏 + 语义补齐"的折中方案，避免一次无必要的全库迁移。同时，将另一团队 PRD 中指出的 SSE 推送、ParseTask 恢复机制、服务拆分等关键缺失项纳入 v0.4 的核心任务。

## 15. 术语表

- **Material**：一条资料记录，绑定一个原始文件与其 MinIO 对象。
- **ParseTask**：一次解析任务的生命周期对象。
- **AiMetadataJob**：一次 AI 元数据提取的子任务。
- **Canonical State**：第 6.1 节定义的状态集合。
- **Display Bucket**：前端把若干 Canonical State 合并成的 UI 分组，定义在第 6.3 节。
- **Baseline Fact**：已经在仓库 HEAD 中实现、v0.4 不可回退的既定事实，见第 4 章。
- **Invariant**：系统必须保持为真的断言，违反即是一致性缺陷，见第 9 章。

## 16. 变更记录

- **v0.4-luceon-lucode-local-dual-thread-2026-05-24（2026-05-24）**：修订 Luceon/Lucode 协同模型的工作区与触发边界。
  - 背景：用户确认不再以外部 IDE 作为 Lucode 的活跃工作入口，改为在同一项目机器上用两个本地 worktree 隔离 Luceon 与 Lucode 线程。
  - 确定需求：Luceon 线程工作区为 `/Users/concm/prod_workspace/Luceon2026`；Lucode 线程工作区为 `/Users/concm/Dev_workspace/Luceon2026`；双方继续以 GitHub `main`、分支和 `TaskAndReport/` 为共享控制面。
  - 触发策略：初期仍由用户手工在 Lucode 线程发送 `Lucode, check task`；Lucode 回报先体现在远端 `lucode/<task-id>` 分支的报告和分支内台账上，Luceon 在 `origin/main` 没有 `Next Actor=Luceon` 行时需要检查最早 Lucode open row 对应的远端分支 handoff；后续 heartbeat 自动化需在手工流稳定后另行授权。
  - 子智能体边界：Luceon 可在用户显式授权时使用 Codex 子智能体做探索、测试、日志分析、证据提取和审查辅助；子智能体不是项目角色，不拥有任务台账、验收、readiness 表述或生产授权。
  - 影响范围：`docs/codex/roles/luceon.md`、`docs/codex/LUCODE_LOCAL_WORKFLOW.md`、`TaskAndReport/README.md`、`docs/codex/PROJECT_STATE.md`、`docs/codex/HANDOFF.md`。
- **v0.4-milestone-6.9.1-team-retirement-2026-05-16（2026-05-16）**：记录 6.9.1 里程碑和协同体系退休。
  - 背景：用户确认当前主流程已基本跑通，Task 205 暴露的一个 AI 残留失败和 MinerU 日志通道归属/新鲜度缺口暂不构成 6.9.1 阻塞。
  - 确定需求：以当前代码和文档状态保存 `v6.9.1` GitHub 里程碑标签，作为后续深入开发前的可回滚锚点。
  - 协同状态：2026-05-16 前的 Director/ProductManager/Architect/DevelopmentEngineer/TestAcceptanceEngineer 角色化协同流程解散；Lucia/Lucode 历史材料和多角色团队材料均仅保留为追溯档案，不再作为活跃派单入口。
  - 保留边界：所有历史任务书、任务列表、任务回报、技术文档继续存放，便于查询追溯。
  - 影响范围：`AGENTS.md`、`README.md`、`docs/codex/PROJECT_STATE.md`、`docs/codex/HANDOFF.md`、`docs/codex/MILESTONE_6.9.1.md`、`TaskAndReport/README.md`、`TaskAndReport/TASK_TRACKING_LIST.md`、`archive/team-model-retired-2026-05-16/`。
- **v0.4-post-6.9.1-luceon-lucode-2026-05-16（2026-05-16）**：建立下一阶段 Luceon/Lucode 双角色协作模型。
  - 背景：项目进入精细化、专业化开发阶段，Luceon 与 Lucode 分属不同工作区，需要通过 GitHub 共享任务、代码、报告和审查证据。
  - 确定需求：Luceon 承担 Director、Architect、TestAcceptanceEngineer 职责；Lucode 在外部 IDE 承担 DevelopmentEngineer、ProductManager 职责；双方以 GitHub `main`、分支和 `TaskAndReport/` 为控制面。
  - 调试策略：`check task` 必须先访问 GitHub 上的任务列表、任务书和回报书，不再依赖单一工作区的本地任务状态。
  - 影响范围：`AGENTS.md`、`docs/codex/roles/luceon.md`、`TaskAndReport/README.md`、`docs/codex/PROJECT_STATE.md`、`docs/codex/HANDOFF.md`。
- **v0.4-team-contract-2026-05-07（2026-05-07）**：固化 Director、Lucia、Lucode 两级执行团队契约。
  - 背景：项目进入持续迭代优化阶段，需要用稳定团队角色提升协作效率、任务质量、报告质量和文档代码一致性。
  - 确定需求：Lucia 作为产品研发总监和 Director 高级参谋，负责目标讨论、技术路线分析、PRD、项目总账、任务书、报告审查和文档对齐；Lucode 作为开发测试经理，严格按 Lucia 任务书执行开发和测试并按统一格式回报。
  - 调试策略：历史角色可作为参考材料，但不再作为当前协作入口或任务承接角色。
  - 影响范围：`AGENTS.md`、`docs/codex/TEAM_CONTRACT.md`、`docs/codex/roles/`、`docs/codex/TASK_BRIEF_TEMPLATE.md`、`docs/codex/PROJECT_STATE.md`、`docs/codex/HANDOFF.md`、PRD 维护规程。
- **v0.4-tier2-standard-local-real-runtime-2026-05-06（2026-05-06）**：将 Tier 2 Standard 收口为本地真实 MinerU + 本地 Ollama `qwen3.5:9b`。
  - 背景：第一阶段当前主线已经转为 local conda MinerU、Docker MinIO、host Ollama `qwen3.5:9b` 与 strict no-skeleton；旧 online MinerU v4 + `qwen3.5:0.8b` 不再是当前主门槛。
  - 确定需求：Standard 档不得用 `ALLOW_AI_SKELETON_FALLBACK=false` 隐式切换 online MinerU；online MinerU 只能通过显式 online mode 开关进入 compatibility-only 验证。
  - 验证结果：2026-05-06 治理验证中，`uat/smoke-test.sh`、`pages-smoke.spec.ts`、`mineru-deep-check.mjs` 与 `pipeline-consistency.spec.ts` 均在本地真实运行链路中通过。
  - 影响范围：第 4 章 Baseline Facts、第 12 章 UAT 验收基线、`docker-compose.tier2-standard.yml`、`scripts/tier2-standard-check.mjs` 与 `.env.example`。
- **v0.4-review-pending-tags-contract-2026-05-03（2026-05-03）**：补齐 `review-pending` 展示术语与当前标签事实源契约。
  - 背景：MetadataTab 首轮信息架构、current-tags persistence contract、latest UI/Metadata/Task Detail interaction review 已在真实本地运行栈中复验，并由 Lucia 判定 `PASS`。
  - 确定需求：`review-pending` 的 Operator-facing 展示桶统一为"待复核"，不得归入"已完成"；`Material.tags` 是人工当前标签事实源；`metadata.tags` 保持为 AI/解析标签来源；MetadataTab 默认信息架构为"审核摘要、当前保存值、AI 建议与证据、技术详情默认折叠"。
  - 待验证边界：其他 task states、tag deletion、multi-tag editing、duplicate-tag handling、concurrent edits、toast stability、full-site UI review 与 L3 readiness 均未在本条中声明完成。
  - 影响范围：第 6.3 节前端展示桶、第 7.1 节 Material 数据模型、第 10.3 节任务详情页与 MetadataTab。
- **v0.4-local-tier2-uat-2026-05-02（2026-05-02）**：固化本地第二级 UAT 基线与 Tier 2 Lite 环境契约。
  - 背景：Lucia 与 Director 完成本地 Docker 二级 UAT 底座建设和手动验收，确认该环境可作为后续日常开发补丁的本地沙盒验收基础。
  - 确定需求：`npx pnpm@10.4.1 run local:check` 为本地预检入口；Windows 宿主机可使用 `npx.cmd pnpm@10.4.1 run local:check`；`docker-compose.tier2-lite.yml` 与 `docker-compose.override.yml` 共同组成本地轻量沙盒入口；Tier 2 Lite 必须提供 MinIO 自动建桶、MinerU mock `/health`、Markdown 上传直通解析、AI skeleton fallback 和一致性审计闭环。
  - 调试策略：Lite 档位不验证真实 PDF MinerU 解析质量、不验证真实大模型推理质量；Ollama 缺模型时允许 skeleton fallback，且不得阻塞 Markdown 上传与解析链路。
  - 影响范围：第 4 章 Baseline Facts、第 12 章 UAT 验收基线、后续 `P0-markdown-upload-regression` 与 `P0-task-state-observability` 开发任务。
  - 关联证据：2026-05-02 本地二级 UAT 已完成前端点按、Markdown 上传、MinIO 落盘、ParseTask 创建、Markdown parsed artifact 写入、AI 降级闭环与 consistency audit `ok=true` 验收；本事项不触发 luceonHMM 第三级真实验收。
- **v0.4-patch-1.2-2026-05-02（2026-05-02）**：增加 Legacy 数据动态启发式去重策略。
  - 背景：真实环境验收时发现，缺乏 `primaryMarkdownPath` 的遗留数据在 `mode=user` 下载包中仍会包含重复的内部 Markdown 和外部 `full.md`。
  - 确定需求：对于 `mode=user` 导出，当 Manifest 缺失或无指针时，自动推断内部主 Markdown，并与外部 `full.md` 针对文件长度和内容校验（Buffer Equality）。若一致则剔除内部副本。此策略作为兼容历史数据的确定性需求。
- **v0.4-storage-2026-05-02（2026-05-02）**：纳入存储架构演进的 PRD 分层结论。
  - 背景：用户提交《Luceon2026 存储架构演进方案 V2.0（高可用与容灾固化版）》，要求 Lucia 独立评估并维护 PRD。
  - 确定需求：先归档不驱逐；归档必须基于 manifest/checksum；DB 只保存归档摘要和指针；DB 快照与恢复演练是存储演进的一等需求；恢复任务优先于透明回源。
  - 调试策略：Google Drive + rclone crypt、HDD 解压态缓存、水位线自动淘汰、透明回源均为待验证策略，未通过 PoC 与恢复演练前不得实现为生产默认链路。
  - 影响范围：Material.metadata.archiveStatus、对象存储一致性不变量、下一阶段 P1 Research Patch、风险与发布策略。
  - 关联证据：2026-05-02 Lucia 对存储方案的独立分析；Google Drive API limits 与 Terms 文档表明 Drive API 存在 quota、上传限制和用例政策约束。
- **v0.4-maintenance-2026-05-02（2026-05-02）**：设立 PRD 维护机制。
  - 背景：项目进入长期迭代与生产准入收口阶段，AI Metadata、MinerU 稳定性、批量压力测试等事项需要 PRD 随进度持续更新，避免需求事实散落在聊天、评审和任务书中。
  - 确定需求：`docs/prd/Luceon2026-PRD-v0.4.md` 仍为当前唯一有效 PRD；PRD 维护由 Lucia 执行；每次 PRD 迭代必须区分确定需求、调试策略和历史记录。
  - 调试策略：具体模型参数、Evidence Pack 阈值、压测策略等仍需基于真实复验逐步固化，未验证前不得写成稳定需求。
  - 影响范围：PRD 维护流程、协作角色分工、文档唯一性约束。
  - 关联证据：用户 2026-05-02 明确要求设立 PRD 维护机制，并要求 PRD 与当前进度、任务目标和迭代记录保持一致。
- **v0.4（2026-04-22）**：综合修订版。在 v0.3 基础上，交叉比对另一团队 PRD 与代码事实，补充了 SSE 实时推送、ParseTaskWorker 启动恢复与超时自愈、`upload-server` 服务拆分等关键缺失项。完善了对评审意见的核查结论。
- **v0.3（2026-04-22）**：重写为工程契约型 PRD。确立 Canonical 状态机、引入 Baseline Facts 与 Invariants、将下一阶段开发聚焦到 Retry/Reparse/Re-AI API、任务详情页与一致性扫描。
- **v0.2**：首次以"任务式"视角重写 PRD，但以愿景驱动为主，列出任务模型、队列、Worker 等作为待开发项，与后续落地代码产生偏差，由本版替代。
- **v0.1**：资料库管理工具起步版，以 Material 为核心。
