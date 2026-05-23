# Task 255: CleanService Explicit New-Version Intent Policy Report

本报告记录了在 `taskId=task-1779085089451` 和 `materialId=1842780526581841` 包含已对齐完成的历史 `toc-rebuild` `v2` 材质时，Mock-Safe 编排运行器显式 `intent: 'create-new-version'` 结合 `newVersionReason` 重新清洗策略的逻辑实现与验证结论。

---

## 1. 基础信息与 Baseline 验证

### 1.1 Git 环境与 Baseline 分支状态
* **当前分支**：`lucode/TASK-20260523-080011-P0-CleanService-Explicit-New-Version-Intent-Policy-MockSafe-NoRuntime`
* **对比基线 (origin/main)**：`06663bb8f379d1b71ad6d8e507217ff86a482567` (已与之完全对齐)
* **HEAD Commit Hash**：`8889ee898b04a8bca2eb8488e0b62e49c8d5069d` (将在本次提交合并后在台账中最终锁定)

### 1.2 物理变更文件清单 (Git Status & Diff)
根据任务书安全红线，本任务仅允许且仅修改了授权的 2 个源文件/测试文件，以及报告与台账：
* **`git diff --name-status origin/main..HEAD` 真实输出**：
  ```text
  M       server/services/cleanservice/orchestration-runner.mjs
  M       server/tests/cleanservice-orchestration-runner-smoke.mjs
  A       TaskAndReport/2026-05-23T08-00-11+0800_P0-CleanService-Explicit-New-Version-Intent-Policy-MockSafe-NoRuntime_REPORT.md
  M       TaskAndReport/TASK_TRACKING_LIST.md
  ```
* **`git diff --check origin/main..HEAD` 真实输出**：
  ```text
  (无输出，说明无合并冲突或空白格式违规)
  ```

---

## 2. 意图分流与重新清洗决策逻辑

### 2.1 前置阻断与旁路分流逻辑 (Preflight Intent Check & Bypass)
1. **意图验证前置阻断 (Intent Validation Check)**：
   在 `runCleanServiceTocRebuildOnce` 入口处对传入的 `config.intent` 意图进行安全校验：
   * 若意图存在且不等于 `create-new-version`，前置阻断并返回 `BLOCKED_UNSUPPORTED_CLEANSERVICE_INTENT`。
   * 若意图等于 `create-new-version` 但缺失重新清洗理由 `newVersionReason`，前置阻断并返回 `BLOCKED_NEW_VERSION_REASON_REQUIRED`。
2. **Current-State Noop 旁路分流 (Bypass)**：
   在 `CURRENT_CLEAN_MATERIAL_NOOP` 决策前加入了 `!hasNewVersionIntent` 的判定：
   * 仅在 `config.intent !== 'create-new-version'`（即默认缺省状态）下才进行 noop 预检。
   * 当意图明确为重新清洗时，主动绕过 noop 分支，允许正常向下分配生成 `v3` 临时版本，并走入 Mock Dryrun 编排。
3. **注入审计追溯结构 (Audit Traceability)**：
   在返回结果的 `audit` 对象中注入 `newVersionIntent` 对象，自解释地记录本次显式意图、重新清洗理由、上一版本 `v2` 的 version/jobId 以及生成的新版本 `v3` 标识。

### 2.2 重新清洗 Mock Dry-Run 结果 Shape
在 Test 17 正向 rerun 中，返回结果形态完美闭环：
```json
{
  "ok": true,
  "status": "DRY_RUN_SUCCESS",
  "classification": "DRY_RUN_SUCCESS",
  "jobId": "luceon-task-clean-123-toc-rebuild-v3",
  "materialId": "1842780526581841",
  "taskId": "task-clean-123",
  "assetVersion": "v3",
  "dryRun": true,
  "audit": {
    "costSource": "unavailable",
    "tokensTotal": 6266,
    "cleanState": "completed",
    "timestamp": "2026-05-23T00:00:00.000Z",
    "newVersionIntent": {
      "intent": "create-new-version",
      "triggerReason": "operator-requested-rerun",
      "previousAssetVersion": "v2",
      "previousJobId": "luceon-task-clean-123-toc-rebuild-v2",
      "newAssetVersion": "v3"
    }
  },
  "warnings": [],
  "verificationSummary": {
    "ok": true,
    "cleanState": "completed",
    "errors": [],
    "warnings": [],
    "unresolvedAnchorCount": 0,
    "inputSizeBytes": 31543,
    "sourceInput": {
      "bucket": "eduassets-raw",
      "object": "mineru/1842780526581841/v1/content_list_v2.json",
      "sha256": "f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db",
      "sizeBytes": 31543
    },
    "costSource": "unavailable"
  },
  "observedAt": "2026-05-23T00:22:51.393Z"
}
```

---

## 3. 单元测试与 Focused Smoke Cases (19/19 Passed)

我们在 `cleanservice-orchestration-runner-smoke.mjs` 中追加了 Test 17、Test 18 和 Test 19 聚焦测试。所有的负向阻断测试均使用 tripwire dependencies 抛出错误以物理证明零外部依赖泄露：

* **Test 17: Positive rerun intent + reason path (v3 dry-run bypass noop)**
  * *条件*：传入 `intent: 'create-new-version'`，`newVersionReason: 'operator-requested-rerun'`。
  * *验证*：成功绕过 noop 分支，升级并分配 `v3` 临时版本进行 Mock dry-run 编排跑通，且返回结果中注入完备的自解释 audit 审计块。
* **Test 18: create-new-version without reason blocking**
  * *条件*：传入 `intent: 'create-new-version'`，但 `newVersionReason` 缺失或为空。
  * *验证*：前置阻断返回 `BLOCKED_NEW_VERSION_REASON_REQUIRED`，且零依赖泄露。
* **Test 19: Unsupported intent blocking**
  * *条件*：传入不支持的非法 `intent`。
  * *验证*：前置阻断返回 `BLOCKED_UNSUPPORTED_CLEANSERVICE_INTENT`，且零依赖泄露。

---

## 4. 项目静态与 Smoke 全量验证检查

在 Dev 容器环境 `/workspace/dev/Luceon2026` 中串行运行了全量合规测试，全数一次性通过：
* **Syntax 静态语法检查** (Node `--check`)
  * `node --check server/services/cleanservice/orchestration-runner.mjs` -> **Exit Code: 0**
  * `node --check server/tests/cleanservice-orchestration-runner-smoke.mjs` -> **Exit Code: 0**
* **Smoke Tests 运行结果**
  * `node server/tests/cleanservice-orchestration-runner-smoke.mjs` -> **Exit Code: 0**
  * 日志片断：
    ```text
      [17] Testing CURRENT_CLEAN_MATERIAL_NOOP bypass on create-new-version rerun...
      [18] Testing create-new-version without reason blocking...
      [19] Testing unsupported intent blocking...
    ALL cleanservice orchestration runner smoke tests PASSED! (19/19)
    ```
* **单测与 Smoke 脚本套件全量跑通**
  * `for f in server/tests/cleanservice-*.mjs; do node "$f" || exit 1; done` -> **Exit Code: 0**
* **TypeScript 类型静态检查** (Pnpm tsc)
  * `npx pnpm@10.4.1 exec tsc --noEmit` -> **Exit Code: 0**
* **Git 安全格式检查**
  * `git diff --check origin/main..HEAD` -> **Exit Code: 0**

---

## 5. 诚实红线与安全声明

我们在此作出绝对诚实的控制面声明，在本任务中**没有任何高危、脏写或超出授权的操作**：
1. **零 DB 写入/修改**：没有发起任何真实的 DB API 写入、修改、删除或重写操作；
2. **零 MinIO 写入/清理**：没有对 MinIO bucket 或对象执行任何写、静默清理、删除操作；
3. **零实际任务派发**：没有发送任何真实的 `POST /api/v1/jobs`，没有与 Mineru2Table 进行任何实际的网络 job query；
4. **零外部 LLM/Ollama 交互**：绝对没有调用任何大模型 API；
5. **零非授权文件修改**：未改变 `server/upload-server.mjs`、`docker-compose`、`.env` 等任何禁用范围的文件；
6. **零超前承诺**：没有声称实现了完整的 runtime 自动重跑、webhook 连通或生产/UAT 就绪。

---

## 6. 遗留债务与下一步建议

### 6.1 遗留技术债务
* 当前的显式重新清洗意图完全在 Mock-Safe 单元/Smoke测试下得到了闭环校验。在真正的端到端 runtime 执行路径中，尚不具备真正的 `v3` 实体重新从 Mineru2Table 进行真实 POST 调度、物理 MinIO 材质写入以及最终的真实的 DB PATCH 写入与授权。

### 6.2 建议的下一个 mainline 窄任务 (Next Task)
既然显式意图、重新清洗理由、前置阻断以及 Mock 审计结构已经极其完备：
1. **支持 UAT 级 Success-path Rerun 物理执行规划 (UAT Planning)**：在一个单独的、得到 Director 显式授权的新版本运行任务中，开始允许将 `v3` 调度任务物理 POST 分发给真实/Ephemeral 挂载在 cms-network 的 Mineru2Table，验证其完成性并在 dry-run 状态下输出全新的 `v3` 材质。
