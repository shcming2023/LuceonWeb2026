# Task Report: P1-Host-MinerU-Log-Sidecar-Authoritative-Progress-Bridge (Resubmit)

**Task ID**: 217
**Date**: 2026-05-18
**Author**: Lucode

## 1. 提交环境与产物
- **开发分支**: `lucode/task-217-resubmit`
- **提交 HEAD**: `209920d` (修复二审发现的 race condition)
- **Changed Files** (代码实现确已包含):
  - `server/services/queue/task-worker.mjs` (传递 getLatestTask)
  - `server/lib/ops-mineru-log-parser.mjs`
  - `server/lib/progress-snapshot.mjs`
  - `server/services/mineru/local-adapter.mjs`
  - `server/upload-server.mjs`
  - `server/tests/mineru-log-progress-smoke.mjs`

## 2. 架构改动总结
已成功完成 Sidecar 优先的日志观测架构改造，核心目标是**阻断容器挂载滞后引起的业务脏读和状态被旧数据覆盖**。
- **修复 Race Condition (二审要求)**: 在 `server/services/mineru/local-adapter.mjs` 轮询中注入 `getLatestTask`，每次读取最新 DB 的 task.metadata。防止 Sidecar 写入后，被轮询中的 stale 内存状态复写。
- **引入 `reconcileLogObservations` 调和层**: 在 `local-adapter` 每次更新前进行调和。如果发现高新鲜度的 `sidecarObs` 数据，则拦截滞后的容器日志，并抛出 `container_mount_stale: true`。
- **强化 `progress-snapshot` 语义**: `readLogState` 现支持识别 `sidecar_missing`, `container_mount_stale`, `sidecar_stale`, `sidecar_fresh`；向操作员暴露出透明的报错如“主宿主机观测通道异常”。
- **平滑 Worker 整合**: `server/services/mineru/local-adapter.mjs` 现通过调和层合并快照后再向全局更新。
- **补齐诊断 API**: 在 `/ops/mineru/active-task` 返回值中注入 `globalLogObservation`。

## 3. 验证与测试证据
- **运行命令与退出码**:
  - `node server/tests/mineru-log-progress-smoke.mjs` (执行完成，退出码 `0`)
  - `git diff --check` (执行完成，无任何尾随空格问题，退出码 `0`)
- **Required Test Evidence**: 153 项测试全量通过，其中包含新增的 Test 33 与 Test 34，专门覆盖 `reconcileLogObservations` 逻辑及快照异常语义（如 `container_mount_stale` 的输出）。
- **Skipped Checks**: 未执行生产部署验证和真实 UI 测试，原因在于当前任务仅限后端核心观测语义重构（Code/Test Only）。
- **Residual Risks**: 即使调和层覆盖了滞后，Docker Volume 底层的更新依然可能由于高并发慢几秒（我们现在能够准确检测此漂移而不影响状态追踪）。暂无系统级 block。
- **Luceon Review Required**: **Yes**. 请 Luceon 进行代码合并与生产验证。
