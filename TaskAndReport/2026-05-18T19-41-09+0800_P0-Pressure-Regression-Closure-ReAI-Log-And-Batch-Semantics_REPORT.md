# Lucode 执行报告：Task 219 压力测试回归缺陷收尾与语义订正

- **任务 ID**：`TASK-20260518-194109-P0-Pressure-Regression-Closure-ReAI-Log-And-Batch-Semantics`
- **执行分支**：`lucode/task-219-pressure-regression-closure`
- **最终提交 HEAD**：`lucode/task-219-pressure-regression-closure@f53baba59476733b8d41dbc28fc22f9597c14c24`
- **基础提交 (Base)**：`009b5d1 Accept Task 223 CleanService docs`
- **报告时间**：2026-05-20
- **执行人**：`lucode`
- **当前状态**：`Ready for luceon Review` (交还控制权给 `luceon`)

---

## 一、任务背景与修正概述 (Background & Core Fixes)

针对 2026-05-18 生产 24-PDF 压力测试和手动 Re-AI 中暴露的控制面与 worker 缺陷，本任务旨在对以下核心问题进行闭环修复与语义订正：

1. **P0 Re-AI 任务重建契约**：
   - 彻底重构 Re-AI 逻辑，使其显式调用 `POST /ai-metadata-jobs` 创建全新的 `aiJobId`；
   - 实现了获取正在运行的 pending 任务的幂等性逻辑，防止双击或重复触发引起 duplicate metadata 异常；
   - 支持创建失败时正确捕获并回滚状态，向上层抛出 explicit `create-failed` 并将任务状态标记为 `failed/ai`，在 `errorMessage` 记录明细。
   - **本次新增**：重构并新增了专门的 `re-ai-task-smoke.mjs` 单体与契约覆盖测试，独立拦截所有的 GET/POST 路由，完整验证了 Success case、Idempotent/Duplicate case 和 Failure case 逻辑。

2. **P1 日志新鲜度与去陈旧化**：
   - 订正了 `server/lib/progress-snapshot.mjs` 中的 `defaultOperatorMessage`，确保当任务的数据库状态已进入终态（如 `review-pending`、`completed`、`failed` 等）时，屏蔽 stale 状态下的 MinerU 活跃处理语义（如 “MinerU API 仍在处理”），避免用户界面上的陈旧提示。
   - 在 `server/lib/ops-mineru-log-parser.mjs` 中强化了新鲜度优先裁决算法，确保 host-side 日志更新鲜时覆盖 container-mounted 日志判定。

3. **P1 `/ops/mineru/diagnostics` 观测接口重构**：
   - 在活跃任务诊断中，重构了 `populateObservabilityDetails`，使得能在接口返回数据中暴露完整的 `observabilityDetails` 核心字段（包括 `observationStale`、`logState`、`activityLevel` 等），用于高精度观测。

4. **P1 批量提交计数可审计性与 broken copy 订正**：
   - 纠正了 `src/app/components/BatchUploadModal.tsx` 里 Toast 提示中 broken 文本 `任务状态请{`，订正为清晰的完成提示。
   - 强化了批量上传时的可审计对账机制。在 `statsRef.current` 引入精细化的 `auditLogs`（包含每份文件的 `fileName`、`materialId`、`taskId`、`ok`、`error` 及 `timestamp` 等）。
   - 在本轮批量上传结束时，不论全部成功还是部分失败，都将通过 `console.table(stats.auditLogs)` 将对账单打印至控制台，并将其挂载在 `window.__luceonLastBatchAudit` 上，方便测试人员在浏览器 F12 中一目了然对账。

---

## 二、变更文件清单 (Surgical Changes)

本次改动 strictly 收敛于与 Task 219 直接关联的文件中，严禁进行无关格式化或重构：

| 变更类型 | 文件路径 | 变更目的 |
| :--- | :--- | :--- |
| **MODIFY** | [progress-snapshot.mjs](file:///workspace/dev/Luceon2026/server/lib/progress-snapshot.mjs) | 终态任务屏蔽 stale "仍在处理" 消息 |
| **MODIFY** | [ops-mineru-log-parser.mjs](file:///workspace/dev/Luceon2026/server/lib/ops-mineru-log-parser.mjs) | 强化日志新鲜度逻辑 |
| **MODIFY** | [ops-mineru-diagnostics.mjs](file:///workspace/dev/Luceon2026/server/lib/ops-mineru-diagnostics.mjs) | 重写活跃任务诊断以输出 observabilityDetails |
| **MODIFY** | [task-actions-routes.mjs](file:///workspace/dev/Luceon2026/server/lib/task-actions-routes.mjs) | 彻底重构 Re-AI 逻辑，通过 POST 请求新建 aiJobId 并防御并发双击幂等 |
| **MODIFY** | [upload-server.mjs](file:///workspace/dev/Luceon2026/server/upload-server.mjs) | 批量上传接口报错时返回包含 fileName/materialId 富 JSON |
| **MODIFY** | [BatchUploadModal.tsx](file:///workspace/dev/Luceon2026/src/app/components/BatchUploadModal.tsx) | 修复 broken copy 文本，捕获并保存上传与对账失败的 auditLogs |
| **NEW** | [re-ai-task-smoke.mjs](file:///workspace/dev/Luceon2026/server/tests/re-ai-task-smoke.mjs) | 新增 Re-AI 成功、重复及失败三大场景契约单体烟雾测试 |
| **NEW** | [batch-upload-audit-smoke.mjs](file:///workspace/dev/Luceon2026/server/tests/batch-upload-audit-smoke.mjs) | 新增批量上传计数与富审计对账单体烟雾测试 |

---

## 三、容器内全量自动化验证结果 (Goal-Driven Verification)

所有验证命令均在 Dev 容器内全量跑通，实现 **0 exit code**：

### 1. 代码格式与语法性检查 (Syntax & Format Checks)

- **`git diff --check`** (PASS - 0 exit code)：
  ```
  (无任何尾随空格或格式问题输出，Exit Code = 0)
  ```
- **`node --check` 语法校验** (PASS - 0 exit code)：
  ```bash
  $ node --check server/lib/task-actions-routes.mjs \
      && node --check server/lib/ops-mineru-log-parser.mjs \
      && node --check server/lib/ops-mineru-diagnostics.mjs \
      && node --check server/lib/progress-snapshot.mjs \
      && node --check server/upload-server.mjs
  (Exit Code = 0)
  ```
- **TypeScript 静态类型检查** (PASS - 0 exit code)：
  ```bash
  $ npx pnpm@10.4.1 exec tsc --noEmit
  (Exit Code = 0)
  ```

### 2. 核心 Re-AI 契约烟雾测试

- **`node server/tests/re-ai-task-smoke.mjs`** (PASS - 0 exit code)：
  ```
  --- Starting re-ai-task-smoke ---
  [metadata-job-client] Created AI Metadata Job: ai-job-1779266013630-f619 for parseTask=task-1
  [task-events] Network error logging event: fetch failed
  [metadata-job-client] Skipped: parseTaskId=task-1 already has active job existing-job-456 (state=pending)
  [task-events] Network error logging event: fetch failed
  [metadata-job-client] createAiMetadataJob failed: HTTP 500
  SUCCESS: re-ai-task-smoke passed! Re-AI job creation contract is verified.
  ```

### 3. AI 失败/纠偏与重试循环安全卫士测试

- **`node server/tests/ai-failure-retry-loop-smoke.mjs`** (PASS - 0 exit code)：
  ```
  --- Starting ai-failure-retry-loop-smoke ---
  Mock MinerU API running on http://127.0.0.1:44277
  Running recoverMisjudgedFailedTasks...
  [task-worker] recoverMisjudgedFailed: Task task-1 纠偏：MinerU mock-mineru-task-1 已完成，尝试拉取结果
  [Mock UpdateTask] task-1 {
    state: 'running',
    stage: 'result-fetching',
    errorMessage: '',
    message: '纠偏恢复：MinerU 已完成，正在拉取结果入库',
    metadata: {
      mineruTaskId: 'mock-mineru-task-1',
      mineruStatus: 'completed',
      recoveredFromMisjudgedFailed: true,
      previousState: 'failed',
      previousErrorMessage: '',
      recoveredAt: '2026-05-20T08:33:37.905Z'
    }
  }
  [task-events] Network error logging event: fetch failed
  [task-worker] Resuming task: task-1 (mineruTaskId: mock-mineru-task-1)

  --- Assertions ---
  SUCCESS: ai-failure-retry-loop-smoke passed! Infinite retry loop is blocked.
  [task-worker] Task task-1: 提交 MinerU 不可达，第 1 次重试
  [Mock UpdateTask] task-1 {
    state: 'pending',
    stage: 'upload',
    message: 'MinerU 提交不可达，可重试 (已重试 1/5 次)',
    metadata: {
      mineruTaskId: 'mock-mineru-task-1',
      submitRetries: 1,
      lastSubmitError: '本地 MinerU 不可达: http://host.docker.internal:44277'
    }
  }
  ```

### 4. MinerU 日志观察与进度归因测试

- **`node server/tests/mineru-log-progress-smoke.mjs`** (PASS - 0 exit code)：
  ```
  === MinerU Log Structured Activity Signal Smoke Test (v1.1) ===
  Test 1: tqdm 进度行解析 -> Pass ✅
  Test 2: 非 tqdm 行不解析为 progress -> Pass ✅
  Test 3: 结构化信号分类 -> Pass ✅
  Test 4: 活性等级裁决 -> Pass ✅
  Test 5: parseLatestMineruProgress 集成 + stale log rejection -> Pass ✅
  Test 6: 只有 API 噪声 → api-alive-only -> Pass ✅
  Test 12: api-alive-only 在 task list 展示中不显示"正在推进" -> Pass ✅
  Test 13: 日志 mtime 新鲜 → observationStale=false -> Pass ✅
  Test 14: 日志 mtime 超阈值 → log-observation-stale -> Pass ✅
  Test 15: transition progress-update 降噪 -> Pass ✅
  Test 16: transition progress-update：stage 变化写事件 -> Pass ✅
  Test 17: mineruLastStatusAt 变化 -> Pass ✅
  Test 19: log-observation-stale 在任务列表展示 -> Pass ✅
  Test 20: 连续 10 次相同 progress-update -> Pass ✅
  Test 21: A-Sample (pipeline + auto + table=true) -> Pass ✅
  Test 22: B-Sample (pipeline + ocr + table=false) -> Pass ✅
  Test 23: C-Sample (hybrid-auto-engine + auto) -> Pass ✅
  Test 24: Stdout API Noise vs Stderr Business Log -> Pass ✅
  Test 25: 连续任务 err.log 切片 -> Pass ✅
  Test 26: 旧上下文 tqdm 丢弃 -> Pass ✅
  Test 27: hybrid model-units 长尾持续归因 -> Pass ✅
  Test 28: 裸 tqdm 无上下文仍不可归因 -> Pass ✅
  Test 29: 新任务 minObservedAt 晚于旧上下文时不可串任务 -> Pass ✅
  Test 30: Pipeline 批次/页码/相位语义恢复 -> Pass ✅
  Test 31: Fast completed task gets truthful no-business-signal diagnostic -> Pass ✅
  Test 32: MinerU adapters import real server/lib log parser path -> Pass ✅
  Test 33: reconcileLogObservations prefers fresh sidecar over stale container -> Pass ✅
  Test 34: progressSnapshot semantics handles sidecar_missing and container_mount_stale -> Pass ✅
  Test 35: ParseTaskWorker.transition does not spread stale metadata -> Pass ✅

  === Results: 156 passed, 0 failed ===
  ✅ MinerU Log Structured Activity Signal Smoke Test Passed!
  ```

### 5. 依赖就绪性与 Ollama 健康状态测试

- **`node server/tests/dependency-health-smoke.mjs`** (PASS - 0 exit code)：
  ```
  Results: 89 passed, 0 failed
  [upload-server] Received SIGTERM, shutting down...
  [task-worker] ParseTask Worker stopped
  [ai-worker] AI Metadata Worker stopped
  [upload-server] Server closed after SIGTERM.
  [upload-server] EXITED with code 0
  ```

---

## 四、遗留风险与审查建议 (Risks & Recommendations)

1. **宿主机端/容器端日志观测不确定性**：
   - 尽管本次测试和新鲜度算法得到了强化，但在某些物理机共享磁盘环境下，日志写入同步时间差依然可能超过 15s。建议 Luceon 审阅时，关注现场运行中是否会出现极其罕见的 `log-observation-stale`。
2. **批量上传中的前端对账时限**：
   - 如果网络中断持续太久（例如超过 2 分钟），前端的异步 reconciliation 即使向 `/materials` 和 `/tasks` 发起重试也可能超时。对此，我们在 `auditLogs` 中追加了完整的 ok: false 记录和 error 原因，这确保了至少在 F12 中能发现对账结果，而不是无声无息地丢失计数。

---

## 五、控制面与范围红线声明 (Scope & Boundaries)

按照 Luceon2026 双特工本地协同契约与 Task 219 的严格指示，本次任务：
- **绝对没有** 接受任何运行时激活（no runtime activation）；
- **绝对没有** 更改生产环境物理配置、DB 模式、MinIO 存储桶或 Ollama 部署结构；
- **绝对没有** 宣称压力测试通过、L3 就绪或上线结论。

所有的验证均在 `lucode` 本地开发容器内封闭进行。

---
`Report created at 2026-05-20. Control handed back to luceon.`
