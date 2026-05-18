# Task 217 Report: P1 Host MinerU Log Sidecar Authoritative Progress Bridge

## 1. 提交环境与产物
- **开发分支**: `lucode/task-217-resubmit-v2`
- **提交 HEAD**: `fd50b98f4daf781e3e7e9100906ba689d44574d9`
- **Changed Files** (代码实现确已包含):
  - `server/services/queue/task-worker.mjs`
  - `server/services/mineru/local-adapter.mjs`
  - `server/lib/ops-mineru-log-parser.mjs`
  - `server/lib/progress-snapshot.mjs`
  - `server/upload-server.mjs`
  - `server/tests/mineru-log-progress-smoke.mjs`

## 2. 架构改动总结（第三次修复）
已完成对 Sidecar 优先日志架构的最后修补，彻底阻断了任何形式的 stale `task.metadata` 复写：
- **修复 `ParseTaskWorker.transition()` DB 写入竞争**: 将原来 `metadata: { ...(task.metadata || {}), progressEventKey: semanticKey }` 修改为仅更新 `progressEventKey` 字段。由于底层 `db-server` 的 `PATCH /tasks/:id` 默认执行 `metadata` 的浅合并，移除了 `task.metadata` 的展开操作，完美阻断了旧状态的回滚。
- **修复 `local-adapter.mjs` 的 DB 写入竞争**:
  - `resumeWithLocalMinerU` 在更新 `metadata` 时现使用通过 `getLatestTask()` 抓取的 `currentMetadata`。
  - `updateCompletionObservation` 也移除了对旧 `task.metadata` 的铺平展开操作。
- **确保 `reconcileLogObservations` 正确性**: 确保传入调和层的 baseline 是最新抓取的 metadata。

## 3. 测试与验证门控
- **DB Write Race Regression Test**: 在 `mineru-log-progress-smoke.mjs` 中新增了 Test 35。该测试 Mock 了 `updateTask`，模拟了一个拥有滞后 20% 容器进度缓存的 Worker，并在 `transition('progress-update')` 时验证了 PATCH payload。测试确保 `mineruObservedProgress` **不被包含在更新负载中**，从而不会覆盖 Sidecar 在 DB 里提交的 70% 进度。
- `node server/tests/mineru-log-progress-smoke.mjs`:
  - 156 passed, 0 failed (包含新增的 Test 35)
  - Exit code: 0
- `npx pnpm@10.4.1 exec tsc --noEmit`:
  - Exit code: 0
- `node --check server/services/mineru/local-adapter.mjs`:
  - Exit code: 0

## 4. 残留风险与已知问题
- 此改造不包含功能特性的删减，所有更改均在安全边界内进行。
- 只有 local MinerU 引擎（`engine: local-mineru`）受影响；线上/远程适配器逻辑不受影响。

## 5. Next Actor 建议
建议 `Next Actor` 流转给 Luceon 进行第三次复查。
复查完毕并合并后，Task 218 阻断即可解除。
