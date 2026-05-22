# Task 254: CleanService Existing Applied Current-State Noop Policy Report

本报告记录了在 `taskId=task-1779085089451` 和 `materialId=1842780526581841` 包含已对齐完成的历史 `toc-rebuild` `v2` 材质时，Mock-Safe 编排运行器前置幂等 `CURRENT_CLEAN_MATERIAL_NOOP` 的逻辑实现与验证结论。

---

## 1. 基础信息与 Baseline 验证

### 1.1 Git 环境与 Baseline 分支状态
* **当前分支**：`lucode/TASK-20260523-073349-P0-CleanService-Existing-Applied-Current-State-Noop-Policy`
* **对比基线 (origin/main)**：`a2b9178a1e4ab6e6ab478ee3d34880bc9717677c` (已与之保持完全对齐)
* **HEAD Commit Hash**：`c0e3b34ec1cb4a30ff13994e43faec3b6ce18683` (将在本次提交合并后在台账中最终锁定)

### 1.2 物理变更文件清单 (Git Status & Diff)
根据任务书安全红线，本任务仅允许且仅修改了授权的 2 个源文件/测试文件，以及报告与台账：
* **`git diff --name-status origin/main..HEAD` 真实输出**：
  ```text
  M       server/services/cleanservice/orchestration-runner.mjs
  M       server/tests/cleanservice-orchestration-runner-smoke.mjs
  A       TaskAndReport/2026-05-23T07-33-49+0800_P0-CleanService-Existing-Applied-Current-State-Noop-Policy_REPORT.md
  M       TaskAndReport/TASK_TRACKING_LIST.md
  ```
* **`git diff --check origin/main..HEAD` 真实输出**：
  ```text
  (无输出，说明无合并冲突或空白格式违规)
  ```

---

## 2. CURRENT_CLEAN_MATERIAL_NOOP 决策逻辑

### 2.1 物理前置逻辑分支 (Preflight Current-State Noop Check)
在调用 `allocateAssetVersion` 分配新版本（从而避免自动将 `v2` 递增至 `v3` 导致 incompatible metadata 被阻断）以及 `buildCleanServiceJobRequest` 之前，增加了独立的判断分支：
```js
  const serviceName = config.serviceName || 'toc-rebuild';

  // 3. Preflight - Current State Noop Check (MUST run before allocateAssetVersion)
  const existingTaskJob = task.metadata?.cleanServiceJobs?.[serviceName];
  const existingMaterialJob = material.metadata?.cleanMaterials?.[serviceName];

  if (existingTaskJob && existingMaterialJob) {
    const assetVersionAligned = existingTaskJob.assetVersion === existingMaterialJob.latestVersion;
    const taskCompleted = existingTaskJob.status === 'completed' || existingTaskJob.cleanState === 'completed';
    const materialCompleted = existingMaterialJob.status === 'completed';
    const jobIdExists = !!existingTaskJob.jobId;

    if (assetVersionAligned && taskCompleted && materialCompleted && jobIdExists) {
      return {
        ok: true,
        status: 'CURRENT_CLEAN_MATERIAL_NOOP',
        classification: 'CURRENT_CLEAN_MATERIAL_NOOP',
        materialId: material.id,
        taskId: task.id,
        serviceName,
        assetVersion: existingTaskJob.assetVersion,
        jobId: existingTaskJob.jobId,
        cleanState: existingTaskJob.cleanState || existingTaskJob.status || 'completed',
        reason: 'Already-applied completed clean material matches task and material current records exactly',
        observedAt: getNow(),
      };
    }
  }
```

### 2.2 返回的 Bounded Noop Result Shape
返回的结果完美过滤了大型正文和 artifact arrays，仅包含标识、轻量 refs、状态与计数：
```json
{
  "ok": true,
  "status": "CURRENT_CLEAN_MATERIAL_NOOP",
  "classification": "CURRENT_CLEAN_MATERIAL_NOOP",
  "materialId": "1842780526581841",
  "taskId": "task-clean-123",
  "serviceName": "toc-rebuild",
  "assetVersion": "v2",
  "jobId": "luceon-task-clean-123-toc-rebuild-v2",
  "cleanState": "completed",
  "reason": "Already-applied completed clean material matches task and material current records exactly",
  "observedAt": "2026-05-22T23:37:51.387Z"
}
```

---

## 3. 单元测试与 Focused Smoke Cases (16/16 Passed)

我们在 `cleanservice-orchestration-runner-smoke.mjs` 中追加了完整的 focused smoke 验证。在执行 noop 预检时，如果调用了任何 dependency (例如 submitJob, queryJob 等)，就会抛出错误以证明零依赖泄露。

* **Test 12: Positive aligned path (CURRENT_CLEAN_MATERIAL_NOOP)**
  * *条件*：`task` 和 `material` 存在对齐且 completed 的 `toc-rebuild v2` 记录。
  * *验证*：返回 `CURRENT_CLEAN_MATERIAL_NOOP`，且未调用任何 dispatch/query 依赖。
* **Test 13: Mismatched assetVersion blocking**
  * *条件*：`task`（`v2`）与 `material`（`v1`）版本不一致。
  * *验证*：拒绝 noop，且照常进入 `BLOCKED_EXISTING_TOC_REBUILD_METADATA` 阻断。
* **Test 14: Non-completed task status blocking**
  * *条件*：历史任务的 `status` 为 `failed`。
  * *验证*：拒绝 noop，且照常进入 `BLOCKED_EXISTING_TOC_REBUILD_METADATA` 阻断。
* **Test 15: Missing jobId blocking**
  * *条件*：`task` 缺失 `jobId` 字段。
  * *验证*：拒绝 noop，且照常进入 `BLOCKED_EXISTING_TOC_REBUILD_METADATA` 阻断。
* **Test 16: One-sided metadata blocking**
  * *条件*：单侧材质存在而任务缺失。
  * *验证*：拒绝 noop，且照常进入 `BLOCKED_EXISTING_TOC_REBUILD_METADATA` 阻断。

---

## 4. 项目静态与 Smoke 全量验证检查

在 Dev 容器环境 `/workspace/dev/Luceon2026` 中串行运行了全量合规测试，全数一次性跑通：
* **Syntax 静态语法检查** (Node `--check`)
  * `node --check server/services/cleanservice/orchestration-runner.mjs` -> **Exit Code: 0** (无语法错误)
  * `node --check server/tests/cleanservice-orchestration-runner-smoke.mjs` -> **Exit Code: 0** (无语法错误)
* **Smoke Tests 运行结果**
  * `node server/tests/cleanservice-orchestration-runner-smoke.mjs` -> **Exit Code: 0**
  * 日志片断：
    ```text
      [11] Testing dynamic raw input propagation without hardcoding...
      [12] Testing CURRENT_CLEAN_MATERIAL_NOOP positive aligned path...
      [13] Testing mismatched assetVersion blocking...
      [14] Testing non-completed task status blocking...
      [15] Testing missing jobId blocking...
      [16] Testing one-sided metadata blocking...
    ALL cleanservice orchestration runner smoke tests PASSED! (16/16)
    ```
* **单测与 Smoke 脚本套件全量跑通**
  * `for f in server/tests/cleanservice-*.mjs; do node "$f" || exit 1; done` -> **Exit Code: 0**
    ```text
    PASS cleanservice worker factory & retriable semantics smoke (8/8)
    PASS cleanservice worker shell smoke
    ```
* **TypeScript 类型静态检查** (Pnpm tsc)
  * `npx pnpm@10.4.1 exec tsc --noEmit` -> **Exit Code: 0** (无任何类型报错)
* **Git 安全格式检查**
  * `git diff --check origin/main..HEAD` -> **Exit Code: 0** (无任何尾随空格违规)

---

## 5. 诚实红线与安全声明

我们在此作出绝对诚实的控制面声明，在本任务中**没有任何高危、脏写或超出授权的操作**：
1. **零 DB 写入/修改**：没有发起任何真实的 DB API 写入、修改、删除或重写操作；
2. **零 MinIO 写入/清理**：没有对 MinIO bucket 或对象执行任何写、静默清理、删除操作；
3. **零实际任务派发**：没有发送任何真实的 `POST /api/v1/jobs`，没有与 Mineru2Table 进行任何实际的网络 job query；
4. **零外部 LLM/Ollama 交互**：绝对没有调用任何大模型 API；
5. **零非授权文件修改**：未改变 `server/upload-server.mjs`、`docker-compose`、`.env` 等任何禁用范围的文件；
6. **零极简边界声明**：没有声称实现了完整的 runtime 自动重跑、webhook 连通或生产/UAT 就绪。

---

## 6. 遗留债务与下一步建议

### 6.1 遗留技术债务
* 现有的 `CURRENT_CLEAN_MATERIAL_NOOP` 决策完全基于内存与 mock-safe 级别完成，真正的 Director 执行层面尚不具备在主调度环中通过已存在的 noop 直接跳过调度逻辑。

### 6.2 建议的下一个 mainline 窄任务 (Next Task)
既然免重跑的 `CURRENT_CLEAN_MATERIAL_NOOP` 幂等决策策略已经完备：
1. **引入 rerun/new-version 明确的授权策略 (Option Check)**：当下一次调度需要重新执行以覆盖现有 `v2` 材质并生成 `v3` 时，设计一套可选参数，例如在 `config` 传入 `allowRerun: true`。若是 `allowRerun === false` 则走 `CURRENT_CLEAN_MATERIAL_NOOP`，若是 `true` 则走 `allocateAssetVersion` 升级到新版本进行 rerun 执行。
