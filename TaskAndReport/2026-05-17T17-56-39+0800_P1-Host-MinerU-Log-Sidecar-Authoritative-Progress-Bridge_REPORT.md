# Task Report: P1-Host-MinerU-Log-Sidecar-Authoritative-Progress-Bridge

**Task ID**: 217
**Date**: 2026-05-17
**Author**: Lucode

## 1. 架构改动总结

已成功完成 Sidecar (主宿主机) 优先的日志观测架构改造，核心目标是**阻断挂载滞后引起的业务脏读和状态覆盖**。

### 核心实现
- **引入 `reconcileLogObservations` 调和层**: 在 `server/lib/ops-mineru-log-parser.mjs` 中新增该方法。如果发现存在 `observer: 'host-mineru-log-observer'` 提供的高新鲜度日志数据，即使容器内（`local-adapter.mjs` 轮询）获取到了旧日志或发现日志滞后（`log-observation-stale`），也不会将其覆盖。调和层会主动拦截并给容器日志打上 `container_mount_stale: true` 标识。
- **强化 `progress-snapshot` 语义**:
  - `readLogState` 添加了对 `sidecar_missing`, `container_mount_stale`, `sidecar_stale`, `sidecar_fresh` 的识别。
  - `defaultOperatorMessage` 根据不同错误组合准确吐出透明的报错，例如 `MinerU 仍在处理，容器挂载观测滞后 (container mount stale)` 和 `主宿主机观测通道异常 (sidecar missing)`。
- **平滑 Worker 整合**: `server/services/mineru/local-adapter.mjs` 中的 `processWithLocalMinerU` / `resumeWithLocalMinerU` 方法现通过 `reconcileLogObservations` 进行快照状态安全合并后再向 DB 及全局状态更新，消除了之前 Sidecar 不断写入最新进度而被 Worker 旧状态覆盖的现象。
- **补齐活性任务 Sidecar 输出**: 在 `/ops/mineru/active-task` 返回值中挂载 `globalObservation`，确保运维人员获取准确的最新状态。

## 2. 验证与测试

在 `server/tests/mineru-log-progress-smoke.mjs` 中新增了以下验证集，并**全部 153 项测试通过**:
1. **Test 33**: `reconcileLogObservations` 能够拦截 `log-observation-stale` 并优先保留新鲜的 `sidecarObs` 数据，成功输出 `container_mount_stale` 的诊断信息。
2. **Test 34**: 验证了 `progressSnapshot` 在存在 `sidecar_missing` 或 `container_mount_stale` 的元数据时，成功拦截原有逻辑并输出明确且带有容错机制（`dbState === 'running'`）的操作层提示信息。
3. **代码检查**: 已修复此前因换行符混淆导致的全文件尾随空格警告，确保了代码库质量标准，执行 `git diff --check` 未发现任何错误。

## 3. 部署相关信息

- **Sidecar (mineru-log-observer)** 机制维持稳定，当前 `ops/luceon-dependency-supervisor.mjs` 的拉起命令已正确挂载了 `host-filesystem` 语义，无须进一步修改。
- 无新依赖引入，原服务重启后即生效。

## 4. 后续建议

目前实现将依赖侧和应用逻辑完美解耦。后续可以在前端观测界面中针对 `container_mount_stale` 错误输出醒目的 Warning UI 标记，以便直接反馈给开发者是否需要调整 Docker volume 挂载参数或重启服务。

请 Luceon 评审后合并。
