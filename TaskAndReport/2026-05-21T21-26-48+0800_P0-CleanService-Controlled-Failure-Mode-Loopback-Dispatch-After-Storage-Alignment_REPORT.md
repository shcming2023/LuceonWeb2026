# TASK-20260521-212648-P0-CleanService-Controlled-Failure-Mode-Loopback-Dispatch-After-Storage-Alignment REPORT

## 1. 任务基础执行事实

- **Task ID**: TASK-20260521-212648-P0-CleanService-Controlled-Failure-Mode-Loopback-Dispatch-After-Storage-Alignment
- **Execution Time**: 2026-05-21T21:45:00Z
- **Luceon Branch**: `lucode/TASK-20260521-212648-P0-CleanService-Controlled-Failure-Mode-Loopback-Dispatch-After-Storage-Alignment`
- **Luceon BASE HEAD**: `b00d015a272829b005b5f096a8d407e5b53b13ca` (TASK-235: 接收存储网络对齐并下达受控调度重试)
- **Mineru2Table Workspace HEAD**: `f487fd82337bbef550e79789440ca45a5a2dd424` (TASK-235: 对齐网络至cms-network及存储端点至minio:9000)
- **Was POST Sent**: `yes`
- **Total POST Count**: `1`
- **Job ID**: `luceon-optionb-mock-job-1779399902295`
- **Final Classification**: `CONTROLLED_FAILURE_DISPATCH_OBSERVED`

---

## 2. Preflight 门控及安全验证证据

### 2.1. 端口与 Ingress 绑定验证
通过 `docker inspect mineru2table-api` 确证端口绑定为本地回环（Loopback）`127.0.0.1:8000`。
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

### 2.2. /health  Honest Response 门控
使用 `curl -s http://172.24.0.6:8000/health` 获取到真实、诚实未配置状态：
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
  "timestamp": "2026-05-21T21:44:21.043327Z"
}
```

### 2.3. 敏感凭证脱敏与空检查矩阵
通过 `docker inspect` 环境变量获取，确证四类敏感凭证均为空且未注入：
- **`MINIO_ACCESS_KEY`**: `<empty>` (未配置)
- **`MINIO_SECRET_KEY`**: `<empty>` (未配置)
- **`DEEPSEEK_API_KEY`**: `<empty>` (未配置)
- **`TOC_REBUILD_CALLBACK_SECRET`**: `<empty>` (未配置)
- **`ALLOWED_MINIO_ENDPOINTS`**: `minio:9000` (符合要求)

### 2.4. MinIO 容器内部 DNS 解析验证
在 `mineru2table-api` 容器内通过 Python 调用 `gethostbyname` 域名解析，确证可成功解析到 `cms-network` 中的 `minio` 容器（IP 为 `172.24.0.3`）：
- **Command**: `docker exec mineru2table-api python -c "import socket; print(socket.gethostbyname('minio'))"`
- **Result**: `172.24.0.3`

### 2.5. OpenAPI Schema 门控验证
经由 `node` 程序检验 live `openapi.json` 文件，确证 `JobSubmitRequest`, `InputRef`, `SourceRef`, `SinkRef` 等模式的字段完全一致。所有 Required 依赖项如 `submitted_at`, `submitted_by`, `endpoint`, `use_ssl` 等均具备对应映射。

---

## 3. In-Memory 候选 payload (无敏感凭证)

以下为此次单次受控测试生成的合成（Synthetic）Payload 结构。本测试未使用任何 Luceon 数据库中的真实素材：
```json
{
  "job_id": "luceon-optionb-mock-job-1779399902295",
  "material_id": "optionb-mock-material",
  "parse_task_id": "optionb-mock-parse-task",
  "asset_version": "v1",
  "inputs": [
    {
      "role": "toc_rebuild_first_pass",
      "source": {
        "type": "minio",
        "endpoint": "minio:9000",
        "use_ssl": false,
        "bucket": "eduassets-raw",
        "object": "mineru/optionb-mock-material/v1/content_list_v2.json"
      }
    }
  ],
  "sink": {
    "type": "minio",
    "endpoint": "minio:9000",
    "use_ssl": false,
    "bucket": "eduassets-clean",
    "prefix": "toc-rebuild/optionb-mock-material/v1/"
  },
  "submitted_at": "2026-05-21T21:45:02.295Z",
  "submitted_by": "luceon2026/cleanservice-worker"
}
```

---

## 4. 单次 POST 发送及只读轮询日志

以下为通过临时单次受控测试脚本执行的控制台真实日志输出片段：

```text
[Scratch Dispatch] target endpoint: http://172.24.0.6:8000
[Scratch Dispatch] Candidate payload:
{
  "job_id": "luceon-optionb-mock-job-1779399902295",
  "material_id": "optionb-mock-material",
  "parse_task_id": "optionb-mock-parse-task",
  "asset_version": "v1",
  "inputs": [
    {
      "role": "toc_rebuild_first_pass",
      "source": {
        "type": "minio",
        "endpoint": "minio:9000",
        "use_ssl": false,
        "bucket": "eduassets-raw",
        "object": "mineru/optionb-mock-material/v1/content_list_v2.json"
      }
    }
  ],
  "sink": {
    "type": "minio",
    "endpoint": "minio:9000",
    "use_ssl": false,
    "bucket": "eduassets-clean",
    "prefix": "toc-rebuild/optionb-mock-material/v1/"
  },
  "submitted_at": "2026-05-21T21:45:02.295Z",
  "submitted_by": "luceon2026/cleanservice-worker"
}
[Scratch Dispatch] Sending submitJob POST...
[Scratch Dispatch] submitJob POST Response:
{
  "job_id": "luceon-optionb-mock-job-1779399902295",
  "status": "queued",
  "service_name": "toc-rebuild",
  "service_version": "1.0.0",
  "protocol_version": "v1",
  "material_id": "optionb-mock-material",
  "parse_task_id": "optionb-mock-parse-task",
  "asset_version": "v1",
  "submitted_at": "2026-05-21T21:45:02Z",
  "started_at": null,
  "finished_at": null,
  "artifacts": {},
  "stats": {},
  "error": null,
  "callback_url": null,
  "callback_secret_ref": null
}
[Scratch Dispatch] Successfully submitted! Job ID: luceon-optionb-mock-job-1779399902295
[Scratch Dispatch] Starting read-only status checks (max 5 times, 5s interval)...
[Scratch Dispatch] Check #1 after 5 seconds...
[Scratch Dispatch] Status Check #1 Result:
{
  "job_id": "luceon-optionb-mock-job-1779399902295",
  "status": "failed",
  "service_name": "toc-rebuild",
  "service_version": "1.0.0",
  "protocol_version": "v1",
  "material_id": "optionb-mock-material",
  "parse_task_id": "optionb-mock-parse-task",
  "asset_version": "v1",
  "submitted_at": "2026-05-21T21:45:02Z",
  "started_at": "2026-05-21T21:45:02Z",
  "finished_at": "2026-05-21T21:45:02Z",
  "artifacts": {},
  "stats": {},
  "error": {
    "code": "processing_failed_permanent",
    "message": "MinIO credentials not configured.",
    "details": null,
    "retriable": false
  }
}
[Scratch Dispatch] Terminal state reached: failed
```

---

## 5. 存储层 (jobs.json) 变化对比

验证了宿主机映射文件 `/workspace/ops/Mineru2Tables/data/jobs.json` 在执行单次 POST 后的状态变动：

### 5.1. 运行前 (Baseline)
- **大小**: `2` 字节
- **SHA256**: `44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a`
- **内容**: `{}`

### 5.2. 运行后 (Post-Dispatch)
- **大小**: `718` 字节
- **SHA256**: `29d5621bcca3d626b8f27289caabd13ba6cd835913a76b9e2cbd8fd8d4577413`
- **内容**:
```json
{
  "luceon-optionb-mock-job-1779399902295": {
    "job_id": "luceon-optionb-mock-job-1779399902295",
    "status": "failed",
    "service_name": "toc-rebuild",
    "service_version": "1.0.0",
    "protocol_version": "v1",
    "material_id": "optionb-mock-material",
    "parse_task_id": "optionb-mock-parse-task",
    "asset_version": "v1",
    "submitted_at": "2026-05-21T21:45:02Z",
    "started_at": "2026-05-21T21:45:02Z",
    "finished_at": "2026-05-21T21:45:02Z",
    "artifacts": {},
    "stats": {},
    "error": {
      "code": "processing_failed_permanent",
      "message": "MinIO credentials not configured.",
      "retriable": false
    },
    "callback_url": null,
    "callback_secret_ref": null
  }
}
```

数据表明，持久化存储中仅且仅多出这 1 条预期的单次受控失败任务记录，未产生任何多余的数据写变动。

---

## 6. 业务红线与宣誓 (Surgical Declaration)

本任务已严格遵守全部业务红线和禁止事项：
1. **禁止真实素材**: 完全使用了 ES Module 内存里动态构建的 Mock 候选 Payload，未从数据库或 MinIO 进行任何真实文件挑选。
2. **禁止凭证注入**: 拒绝了任何形式的凭证注入，MinIO/DeepSeek-API 秘钥维持完全空置，以换取真实安全的受控故障测试结果。
3. **禁止 MinIO 读写修改**: 未对任何实质性存储资源和 MinIO 对象执行上传、删除或更改。
4. **禁止 DB 写入**: 未对 Luceon 端任何数据库持久化层表记录产生插入或更新。
5. **禁止 Docker 变更**: 维持 Docker 容器及 Compose 服务完全的只读检测，未执行重启、重建或环境参数调整。
6. **不宣称生产就绪**: 报告的 `failed` 结果以及 honest error 仅确证了“Luceon 与外部 Mineru2Table 的 HTTP 接口与控制流互通顺利”，不宣称 UAT 成功、上线就绪、或成功生产 Clean Material 等。
