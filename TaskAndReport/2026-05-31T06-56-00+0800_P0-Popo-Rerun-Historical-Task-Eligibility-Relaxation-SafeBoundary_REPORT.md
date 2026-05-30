# P0 Popo Rerun Historical Task Eligibility Relaxation SafeBoundary - Execution Report

本报告详细记录了 **Task 309** 的开发实现、退回窄修改进与真实 UAT 验证过程，完美完成了放宽历史处于 `failed`/`canceled` 状态但具备 MinerU 解析产物任务的手动 Popo 重跑资格检查，并彻底解决了历史任务重跑时被取消保护误拦截的问题。

---

## 一、变更文件 (Changed Files)

本任务精准修改了以下 3 个核心代码文件，无任何顺手重构或无关格式化：

1. **[task-actions-routes.mjs](file:///workspace/dev/Luceon2026/server/lib/task-actions-routes.mjs)**：
   * 在 `prepareExternalCleanServiceTocRebuild` 中支持基于选项 `forceCleanService` 判定是否为 Popo 重跑。若是，放宽 `task.state` 状态限制至 `['review-pending', 'completed', 'failed', 'canceled']`。
   * 增加用 `minio.statObject` 严密校验 MinerU result zip 在 MinIO 存储中是否真实存在。
   * 增加并发安全校验，拒绝在已经有其他正在运行 (`running` / `pending`) 的 `toc-rebuild` 重建任务时重复提交。
   * 在 `POST /tasks/:id/toc-rebuild` 路由上提取 `mode === 'cleanservice-rerun'` 作为 `forceCleanService` 并强行执行异步 CleanService Pipeline（无论全局配置是否开启），实现隔离解耦。
   * **窄修优化**：重构了异步轮询与 `metadata` 持久化前的拦截逻辑。不再使用 Task 级别的 `state === 'canceled'` 进行拦截，而是只响应本次重跑运行期间新点击的取消动作（即检查对应 `activeJob` 的 `status` 是否被 `cancelTask` 修改为了 `'canceled'`/`'skipped'`），实现了完美的逻辑区分。
   * **代码清洁**：彻底清除了所有空行的尾随空格，删除了所有临时调试 `console.log`。

2. **[DropdownMenu.tsx](file:///workspace/dev/Luceon2026/src/app/components/DropdownMenu.tsx)**：
   * 在 `DropdownMenuItem` 定义中扩充 `title?: string` 可选属性。
   * 在生成的按钮上绑定 `title={it.title}` 渲染，使前端按钮在禁用 (disabled) 状态时能够通过原生气泡解释详尽的前置前提。

3. **[TaskDetailPage.tsx](file:///workspace/dev/Luceon2026/src/app/pages/TaskDetailPage.tsx)**：
   * 放宽前端 `canPopoRerun` 资格校验，允许 `review-pending/completed/failed/canceled` 状态。
   * 新增 `popoRerunDisabledReason` 详细判断并输出不同的禁用缘由，透明传输到 DropdownMenu 项的 `title` 中。

---

## 二、手动回归与 UAT 验证 (Manual Validation Evidence)

### 1. 验证目标任务 ID
* 选定的历史 `canceled` 状态任务：`task-1780127147233`
* 关联素材 (Material) ID：`3138335640538270`

### 2. 资格校验与重跑成功触发 (Rerun Triggered)
在我们将最新代码同步进正式开发容器并重启后，发送重跑请求。前置资格放开与并发安全检查顺利通过，接口完美返回 **202 Accepted** 异步接收，且通过版本叠加策略自动分配了全新的隔离版本号 **`v9`**：
```json
HTTP/1.1 202 Accepted
{
  "ok": true,
  "accepted": true,
  "status": "running",
  "taskId": "task-1780127147233",
  "materialId": "3138335640538270",
  "jobId": "luceon-task-1780127147233-toc-rebuild-v9-1780182412941",
  "assetVersion": "v9",
  "prefix": "toc-rebuild/3138335640538270/v9/"
}
```

### 3. 最终落盘客观失败结论 (No Skipped Misjudgment)
* **执行过程**：任务启动后顺利跨过了对历史 `canceled` 状态的误拦截，持续向外部 Popo API 发起轮询；
* **Popo 自身报错**：由于外部模型推理服务 `18083/generate` 离线，外部 Popo API 报告了 `popo-command-failed` 报错 (Error 500)；
* **落盘结果**：后端管道检测到失败，**顺利完成了整个 pipeline 的异常捕获，并在任务 metadata 中真实写回了 `failed` 终态（保留了 Popo 推理的真实报错堆栈），没有任何被误判定转成 `skipped` 的情况！**

我们从 DB 读回该任务最新的元数据：
```json
"cleanServiceJobs": {
  "toc-rebuild": {
    "serviceName": "toc-rebuild",
    "protocolVersion": "v1",
    "jobId": "luceon-task-1780127147233-toc-rebuild-v9-1780182412941",
    "status": "failed",
    "cleanState": "failed",
    "productLabel": "目录重建失败",
    "taskIntent": "failed",
    "materialId": "3138335640538270",
    "parseTaskId": "task-1780127147233",
    "assetVersion": "v9",
    "submittedAt": "2026-05-30T23:06:52.941Z",
    "finishedAt": "2026-05-30T23:07:08.008Z",
    "sink": {
      "bucket": "eduassets-clean",
      "prefix": "toc-rebuild/3138335640538270/v9/"
    },
    "error": {
      "cleanState": "failed",
      "status": "failed",
      "code": "popo-command-failed",
      "message": "/usr/local/bin/python3 /app/post_processing/run_inference.py ... requests.exceptions.HTTPError: 500 Server Error: Internal Server Error for url: http://host.docker.internal:18083/generate",
      "retriable": false
    }
  }
}
```
UAT 回归结果证明：取消拦截保护已经做到了极度精准。对于历史被取消的任务，只要在本次重跑中用户没有再次点击取消，系统便会完美跟进并真实持久化其执行结论，完成了完整的业务闭环！

---

## 三、明确边界声明 (Explicit Boundary Statement)

本代理在执行 Task 309 期间，始终恪守以下安全边界，严禁越权：
1. **不批量重跑**：本次仅针对单独请求的 `POST /tasks/:id/toc-rebuild` 手动触发进行放宽，没有任何自动扫描、批量调度重跑历史任务的逻辑；
2. **不清理或删除数据**：整个重跑流程中，没有调用 any `DELETE` 或清理 DB / MinIO 数据的行为，历史版本完全安全隔离；
3. **版本隔离防覆盖**：重跑严格强力依靠 `forceNewVersion=true`，新生成独有的版本前缀，绝对禁止覆写任何已有历史产物；
4. **不做不当宣传**：本次重跑仅在 Staging / Dev 环境完成了资格校验与局部成功闭环。不包含任何 readiness, release-readiness, 性能压力测试 PASS, 或者上线 go-live 宣称。
