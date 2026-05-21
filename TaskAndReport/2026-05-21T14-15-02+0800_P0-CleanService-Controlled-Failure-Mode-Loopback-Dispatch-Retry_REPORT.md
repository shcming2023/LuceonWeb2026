# CleanService Controlled Failure Mode Loopback Dispatch Retry Report

## 1. 任务摘要 (Task Summary)

根据 **Task 233** (`TASK-20260521-141502-P0-CleanService-Controlled-Failure-Mode-Loopback-Dispatch-Retry`) 的 mainline 目标与 Director 的 Option B 授权，我们在 Docker 开发容器内对已集成 Task 232 契约字段修复的 `lucode/task-233-dispatch-retry` 分支进行了真实调度前的 preflight 和门控审计。

特别地，我们在 `POST /api/v1/jobs` 发起前，额外确认了 **`Storage Endpoint Allowlist Gate`** 的一致性校验：
- **拦截规则**: candidate payload 里的 `source.endpoint` 和 `sink.endpoint` 必须完全在 `mineru2table-api` 容器内定义的 `ALLOWED_MINIO_ENDPOINTS` 允许列表中。
- **匹配结果**: 默认生成的 payload 中 source / sink endpoint 为 **`minio:9000`**，而 downstream API 容器定义的允许列表为 **`[ "localhost:9000" ]`**。两者存在字面量不匹配，在 POST 前成功触发了强力阻断。
- **交付状态**: 绝对未发送任何真实 POST 请求（请求数：0），且没有任何 MinIO/LLM/DB 读写或 scheduler 激活行为。物理 job-store `jobs.json` 保持干净且无任何突变。

最终任务分类正式宣告为：**`BLOCKED_STORAGE_ENDPOINT_ALLOWLIST_GAP`**。

---

## 2. 交付物基本信息 (Delivery Information)

- **交付分支**: `lucode/task-233-dispatch-retry`
- **交付 HEAD SHA**: `7128e702ae01c9c5206cd2eb28d588096d5c0495`
- **Luceon Review Correction**: 原报告中的 `3dab24bc5c71c9821d487789652af6eaf64b760a` 是 Task 233 下达时的 Luceon main，不是交付分支 HEAD。Luceon 以 GitHub-visible delivery branch `7128e702ae01c9c5206cd2eb28d588096d5c0495` 为验收锚点。
- **是否发送 POST**: `no`
- **实际发送 POST 计数**: `0`
- **生成的 Job ID**: `none`
- **最终分类**: `BLOCKED_STORAGE_ENDPOINT_ALLOWLIST_GAP`

---

## 3. 门控审计结果 (Preflight Gates Matrix)

| 门控名称 (Gate Name) | 校验内容 | 校验结果 | 状态 (Status) |
| :--- | :--- | :--- | :--- |
| **Gate 1: Container Running** | `mineru2table-api` 处于 Running & Healthy 状态 | `true` (Up 2 hours, healthy) | **PASS** |
| **Gate 2: Loopback Binding** | 容器端口绑定 strictly 限制在 `127.0.0.1:8000` | `true` (`HostIp=127.0.0.1`, `HostPort=8000`) | **PASS** |
| **Gate 3: Health API** | `/health` 接口 dependencies 诚实上报未配置 | `true` (`minio=unconfigured`, `llm=not_configured`) | **PASS** |
| **Gate 4: Credentials Empty** | 敏感环境变量为空，无凭证注入泄漏 | `true` (全部 `[EMPTY]` 或 `[ABSENT]`) | **PASS** |
| **Gate 5: OpenAPI Schema Gate** | 契约字段完整度对比 live `/openapi.json` | `true` (`missing: []`，无缺失字段) | **PASS** |
| **Gate 6: Storage Endpoint Allowlist** | payload 的 source/sink endpoint 在允许列表中 | `false` (`minio:9000` 不在 `[ "localhost:9000" ]` 中) | **BLOCKED** |

---

## 4. 绝对客观证据 (Objective Evidence)

### A. Downstream 端口绑定与敏感环境变量 (Docker Inspect 证据)
执行 `docker inspect mineru2table-api` 截获的真实配置：
- **Host 端口绑定限制**:
  ```json
  "Ports": {
      "8000/tcp": [
          {
              "HostIp": "127.0.0.1",
              "HostPort": "8000"
          }
      ]
  }
  ```
- **敏感环境变量矩阵（脱敏掩码）**:
  ```json
  "Env": [
      "ALLOWED_MINIO_ENDPOINTS=localhost:9000",
      "MINIO_ACCESS_KEY=",
      "MINIO_SECRET_KEY=",
      "DEEPSEEK_API_KEY=",
      "TOC_REBUILD_CALLBACK_SECRET=",
      "IMPLEMENTATION_COMMIT=af80ced635755384a2c878110013c3e2d8f9cb9a"
  ]
  ```

### B. Health 状态检查 (`GET /health` 证据)
通过开发容器内部网络对 `mineru2table-api` 健康度探测：
```json
{
  "status": "unhealthy",
  "service_name": "toc-rebuild",
  "service_version": "1.0.0",
  "protocol_version": "v1",
  "checks": {
    "minio": "unconfigured",
    "llm": "not_configured",
    "dependencies": "ok"
  },
  "timestamp": "2026-05-21T06:30:54.410252Z"
}
```

### C. Storage Endpoint Allowlist 校验细节
- **Luceon 侧生成的默认 Candidate Payload 包含 of 6 项契约字段**:
  - `submitted_at`: `"2026-05-21T06:30:54.412Z"`
  - `submitted_by`: `"luceon2026/cleanservice-worker"`
  - `inputs[0].source.endpoint`: `"minio:9000"` (mismatched)
  - `inputs[0].source.use_ssl`: `false`
  - `sink.endpoint`: `"minio:9000"` (mismatched)
  - `sink.use_ssl`: `false`
- **Downstream ALLOWED_MINIO_ENDPOINTS**: `[ "localhost:9000" ]`
- **对比判定**: `"minio:9000"` 与 `"localhost:9000"` 字面量不匹配，在 POST 调度前成功被 Allowlist 拦截。

---

## 5. Job-Store 物理基线校验 (No-Mutation Audit)

我们对物理 job-store `jobs.json` 进行了前、后状态的 SHA256 哈希值与内容完整度验证：
- **物理路径**: `/workspace/ops/Mineru2Tables/data/jobs.json`
- **Baseline 前状态**:
  - 大小: `2` 字节
  - 记录数: `0`
  - 内容: `{}`
  - SHA256 Hash: `44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a`
- **Post-State 后状态**:
  - 大小: `2` 字节
  - 记录数: `0`
  - 内容: `{}`
  - SHA256 Hash: `44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a`

**结论**: 前后 Hash 与大小完全一致，证明在整个 preflight 周期中没有发送任何 real POST 请求，未产生任何数据突变。

---

## 6. 本地全自动验证日志片段 (Console Log)

以下为我们在容器内部运行全自动 preflight / stop 验证脚本 `scratch/task233_controlled_failure.mjs` 输出的真实终端日志：

```text
=== Task 233 Preflight and Storage Endpoint Allowlist Gate Audit ===

Current Branch HEAD SHA: 3dab24bc5c71c9821d487789652af6eaf64b760a
[Gate 1] Checking mineru2table-api container...
  Container Running & Healthy: true

[Gate 2] Checking loopback binding (127.0.0.1:8000)...
  HostIp: 127.0.0.1, HostPort: 8000
  Loopback binding strictly enforced: true

[Gate 3] Checking /health API...
  Health response: {"status":"unhealthy","service_name":"toc-rebuild","service_version":"1.0.0","protocol_version":"v1","checks":{"minio":"unconfigured","llm":"not_configured","dependencies":"ok"},"timestamp":"2026-05-21T06:30:54.410252Z"}
  Health Check Status OK (unconfigured dependencies): true

[Gate 4] Checking credentials are empty...
  Credentials Matrix: {
  "MINIO_ACCESS_KEY": "[EMPTY]",
  "MINIO_SECRET_KEY": "[EMPTY]",
  "DEEPSEEK_API_KEY": "[EMPTY]",
  "TOC_REBUILD_CALLBACK_SECRET": "[EMPTY]"
}
  All empty/absent: true

[Gate 5] Running OpenAPI Schema Gate...
  Generated Candidate Payload:
 {
  "job_id": "luceon-optionb-mock-parse-task-toc-rebuild-v1",
  "material_id": "optionb-mock-material",
  "parse_task_id": "optionb-mock-parse-task",
  "asset_version": "v1",
  "submitted_at": "2026-05-21T06:30:54.412Z",
  "submitted_by": "luceon2026/cleanservice-worker",
  "inputs": [
    {
      "role": "mineru-content",
      "source": {
        "type": "minio",
        "bucket": "eduassets-raw",
        "object": "mineru/optionb-mock-material/v1/content_list_v2.json",
        "endpoint": "minio:9000",
        "use_ssl": false
      },
      "hash": "mock-sha256-hash-value-1234567890abcdef"
    }
  ],
  "sink": {
    "type": "minio",
    "bucket": "eduassets-clean",
    "prefix": "toc-rebuild/optionb-mock-material/v1/",
    "endpoint": "minio:9000",
    "use_ssl": false
  },
  "callback_secret_ref": "TOC_REBUILD_CALLBACK_SECRET",
  "options": {
    "max_cost_cny": 8
  }
}
  Schema Gate Pass: true

[Gate 6] Running Storage Endpoint Allowlist Gate...
  Allowed minio endpoints in mineru2table-api env: [ 'localhost:9000' ]
  Candidate source endpoint: "minio:9000"
  Candidate sink endpoint:   "minio:9000"
  Source endpoint match allowlist: false
  Sink endpoint match allowlist:   false
  Allowlist Gate Pass: false

[Jobs Store] Gathering jobs.json baseline stats...
  Baseline stats: {
  "sizeBytes": 2,
  "hash": "44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a",
  "recordCount": 0,
  "contentExcerpt": "{}"
}

=== Final Handoff Decision ===
[BLOCKED] Classification: BLOCKED_STORAGE_ENDPOINT_ALLOWLIST_GAP (Storage Endpoint Allowlist Gate failed)
  >> PROHIBITED: Do not send POST. Do not edit config. Do not edit source code.

[Jobs Store] Gathering jobs.json post-state stats...
  Post-state stats: {
  "sizeBytes": 2,
  "hash": "44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a",
  "recordCount": 0,
  "contentExcerpt": "{}"
}
```

---

## 7. 遗留风险与审查建议 (Risks & Recommendations)

1. **配置不匹配风险**: 默认生成的 payload (`minio:9000`) 与 api 接收端点 (`localhost:9000`) 之间存在字面量差异。若要进行后续真实的 success-path 联调，必须统筹更新 Luceon 侧的 `CLEANSERVICE_STORAGE_ENDPOINT` 环境变量或 `mineru2table-api` 的 `ALLOWED_MINIO_ENDPOINTS` 配置，以消除 allowlist gap。但必须由 luceon 在控制面作为后续 Task 正式下达，本次 Lucode 执行过程已按照红线完美就地阻断。
2. **专注于 mock-safe 冒烟测试验证**: 本次交付中，我们使用 `tsc --noEmit` 进行类型检验，并成功全量通过了四个 focused cleanservice 冒烟测试，保障了现有 mock-safe 测试套件没有任何损坏。

---

## 8. 控制权交接 (Handoff)

我们已在本地更新了台账 `TASK_TRACKING_LIST.md`，将控制权和交接状态转回给 **luceon**：
- **Status**: `Ready for luceon Review`
- **Next Actor**: `luceon`
- **交付分支**: `lucode/task-233-dispatch-retry`

请 **luceon** 确认分支状态并进行最终验收！
