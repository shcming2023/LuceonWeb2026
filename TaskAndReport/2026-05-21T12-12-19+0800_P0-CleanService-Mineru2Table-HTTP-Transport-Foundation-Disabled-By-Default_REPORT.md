# CleanService Mineru2Table HTTP Transport Foundation Report

## 1. Executive Summary (摘要)

本报告记录 **TASK-20260521-121219-P0-CleanService-Mineru2Table-HTTP-Transport-Foundation-Disabled-By-Default** 的完整执行结果。

根据任务书要求，已精准完成以下工作：
1. **新增 HTTP Transport 模块**：`server/services/cleanservice/http-transport.mjs`，实现 `createMineru2TableHttpTransport()` 工厂函数，支持 Protocol v1 的 `POST /api/v1/jobs` 和 `GET /api/v1/jobs/{jobId}`。
2. **保持 disabled-by-default**：生产/默认运行时 `CLEANSERVICE_ENABLED=false` 不变，不会自动发起任何 HTTP POST。
3. **新增 7 场景 mock HTTP smoke test**：使用 Node.js `http.createServer` 创建临时 mock 服务器，全部通过。
4. **零回归**：4 个既有 cleanservice smoke test 全部通过。
5. **零真实调用**：没有任何请求到达 `127.0.0.1:8000` 的真实 Mineru2Table 服务。

---

## 2. Changed-File Audit (变更文件审计)

仅新增 2 个允许文件，未修改任何既有文件：

```
 server/services/cleanservice/http-transport.mjs       | [NEW] 173 lines
 server/tests/cleanservice-http-transport-smoke.mjs    | [NEW] 387 lines
 2 files changed, 560 insertions(+)
```

### 未修改文件确认
- `server/services/cleanservice/config.mjs` — 未修改
- `server/services/cleanservice/protocol.mjs` — 未修改
- `server/services/cleanservice/cleanservice-worker.mjs` — 未修改
- `server/services/cleanservice/raw-material-adapter.mjs` — 未修改
- 前端 `src/**` — 零变更
- Docker/Compose/env/secrets — 零变更
- DB migrations — 零变更

---

## 3. Final Branch And Commit SHA

- **分支**：`lucode/task-228-cleanservice-http-transport`
- **最终 SHA**：`4a3ae56bd55aea086c29df81b54f511423da3373`
- **父提交**：`a611c40133f2c9efe442604ad238a4d4dbbdbab4`（Task 228 任务书下发 SHA）
- **GitHub 远端**：已推送至 `origin/lucode/task-228-cleanservice-http-transport`

---

## 4. Mock Request Payload Shape (请求载荷形状)

以下是 mock smoke test 中捕获的 `POST /api/v1/jobs` 请求载荷：

```json
{
  "job_id": "luceon-task-transport-1-toc-rebuild-v1",
  "material_id": "mat-transport-1",
  "parse_task_id": "task-transport-1",
  "asset_version": "v1",
  "inputs": [
    {
      "role": "mineru-content",
      "source": {
        "type": "minio",
        "bucket": "eduassets-raw",
        "object": "mineru/mat-transport-1/v1/content_list_v2.json"
      },
      "hash": "sha256-test-fixture"
    }
  ],
  "sink": {
    "type": "minio",
    "bucket": "eduassets-clean",
    "prefix": "toc-rebuild/mat-transport-1/v1/"
  },
  "callback_secret_ref": "TOC_REBUILD_CALLBACK_SECRET",
  "options": {
    "max_cost_cny": 8
  }
}
```

**载荷合规性审查**：
- ✅ `job_id`：包含 Luceon task ID、service name、asset version
- ✅ `material_id`：来自 canonical Raw Material
- ✅ `inputs[0].role = "mineru-content"`：Protocol v1 角色标识
- ✅ `inputs[0].source.bucket = "eduassets-raw"`：强制 raw bucket
- ✅ `inputs[0].source.object` 以 `/content_list_v2.json` 结尾
- ✅ `sink.bucket = "eduassets-clean"`：目标 clean bucket
- ✅ `options.max_cost_cny = 8`：cost hard limit
- ✅ `callback_secret_ref`：webhook 回调密钥引用（字段存在但实际回调集成后置）
- ✅ 无源文本复制或编造

---

## 5. Focused Smoke Test Commands And Exit Codes

### New HTTP Transport Smoke (7/7)
```bash
$ node server/tests/cleanservice-http-transport-smoke.mjs
# exit code: 0

=== CleanService HTTP Transport Smoke ===
  [1] disabled/default mode makes no HTTP request... PASS
  [2] canonical Raw Material sends exactly one mock POST /api/v1/jobs... PASS
  [3] legacy parsed-only skipped-policy makes no HTTP request... PASS
  [4] mock 4xx response is recorded as explicit dispatch failure... PASS
  [5] mock 5xx response is recorded as explicit failure... PASS
  [6] timeout/network failure is bounded and reported... PASS
  [7] no test calls real 127.0.0.1:8000... PASS
PASS cleanservice http transport smoke (7/7)
```

### Existing Smoke Regression (4/4)
```bash
$ node server/tests/cleanservice-worker-shell-smoke.mjs   # exit 0 — PASS
$ node server/tests/cleanservice-foundation-smoke.mjs     # exit 0 — PASS
$ node server/tests/cleanservice-raw-material-adapter-smoke.mjs  # exit 0 — PASS
$ node server/tests/cleanservice-asset-version-smoke.mjs  # exit 0 — PASS
```

---

## 6. Syntax/Type-Check Commands And Exit Codes

```bash
$ git diff --check
# exit code: 0 — PASSED

$ node -c server/services/cleanservice/http-transport.mjs
# exit code: 0 — syntax OK

$ node -c server/tests/cleanservice-http-transport-smoke.mjs
# exit code: 0 — syntax OK

$ npx tsc --noEmit
# exit code: 0 — no TypeScript errors
```

---

## 7. Safety Boundary Statement (安全边界声明)

- **零真实 Mineru2Table 调用**：没有任何 `POST http://127.0.0.1:8000/api/v1/jobs` 发生。所有测试使用临时 mock HTTP 服务器（随机端口）。
- **零 Job 提交**：生产/默认运行时保持 `CLEANSERVICE_ENABLED=false`，disabled-noop。
- **零 MinIO 操作**：未读写任何 MinIO 对象。
- **零 LLM 调用**：未调用任何 LLM API。
- **零 DB 变更**：未修改任何数据库。
- **零 Docker/Compose/env/secret 变更**：未修改任何部署配置或密钥。
- **零前端变更**：`src/**` 未触及。
- **Legacy parsed-only 安全**：`skipped-policy` 路径经验证不会发起 HTTP 请求。

---

## 8. Residual Risks And Deferred Side Work (遗留风险与后置工作)

### 已实现
- `createMineru2TableHttpTransport`：Protocol v1 HTTP transport 工厂
- 支持 `POST /api/v1/jobs`（submitJob）和 `GET /api/v1/jobs/{jobId}`（queryJob）
- AbortController 超时控制
- 非 2xx 显式错误处理（区分 4xx 不可重试 / 5xx 可重试）
- `X-API-Key` header 注入

### 后置（按任务书明确）
- **真实 loopback dispatch**：需要 `CLEANSERVICE_ENABLED=true` + `CLEANSERVICE_ENDPOINT=http://127.0.0.1:8000`，当前不启用
- **Bearer/API-token 强制验证**：Mineru2Table 端已有可选 `API_KEY` 配置
- **Webhook callback endpoint 集成**：`callback_secret_ref` 字段已在载荷中，但回调端点未实现
- **MinIO 输出验证**：需要真实 job 完成后验证
- **Operator UI 状态**：clean job 状态未连接前端
- **RawMaterial2CleanMaterial 服务集成**：明确后置
- **Retry/backoff 硬化**：超出当前 focused mock failure 语义；client 层 5xx `retriable` 传播仍需后续任务收口
- **`POST /api/v1/jobs:from-storage` 路径**：未在本次 transport 中实现（当前仅覆盖 `/api/v1/jobs`）

---

## 9. Final Status Recommendation (最终状态建议)

> [!IMPORTANT]
> **Lucode 角色建议**：本任务已完全实现所有正面验收条件——disabled-by-default transport、mock 验证 7/7 通过、Protocol v1 载荷合规、legacy 安全、非 2xx 显式错误、零回归、零真实调用。建议推荐为待审状态。

控制权与台账现在正式交还给 **Luceon** 角色。

---
*Reported by lucode on 2026-05-21.*
