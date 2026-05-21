# TASK-20260522-055920-P0-CleanService-Durable-Mineru2Table-Endpoint-Configuration-NoPost-Preflight REPORT

## 1. 任务基本信息

- **Branch**: `lucode/task-237` (基于 `main`)
- **HEAD Commit**: `ae9708bc5a76b87ccc912e860fc8d87d74f94ddd`
- **操作环境**: Docker 运行时/开发容器网络 `cms-network`
- **执行时间**: 2026-05-21T22:11Z

---

## 2. 候选端点探测矩阵 (Candidate Endpoint Probe Matrix)

在 `cms-upload-server` 容器内部，使用 `wget` 针对备选的 Docker DNS 端点进行只读 `GET /health` 探测：

| 探测端点 | 连通状态 | 响应 HTTP 状态码 | 返回内容/说明 |
| :--- | :--- | :--- | :--- |
| `http://mineru2table:8000/health` | **SUCCESS** | `200 OK` | `{"status":"unhealthy","service_name":"toc-rebuild",...}` |
| `http://mineru2table-api:8000/health` | **SUCCESS** | `200 OK` | `{"status":"unhealthy","service_name":"toc-rebuild",...}` |

### 探测命令及完整日志片段：

```bash
# 1. 探测首选端点 mineru2table:8000
$ docker exec cms-upload-server wget -S -O- http://mineru2table:8000/health
Connecting to mineru2table:8000 (172.24.0.6:8000)
  HTTP/1.1 200 OK
  date: Thu, 21 May 2026 22:10:16 GMT
  server: uvicorn
  content-length: 220
  content-type: application/json
  connection: close

{"status":"unhealthy","service_name":"toc-rebuild","service_version":"1.0.0","protocol_version":"v1","checks":{"minio":"unconfigured","llm":"not_configured","dependencies":"ok"},"timestamp":"2026-05-21T22:10:17.382537Z"}

# 2. 探测备用端点 mineru2table-api:8000
$ docker exec cms-upload-server wget -S -O- http://mineru2table-api:8000/health
Connecting to mineru2table-api:8000 (172.24.0.6:8000)
  HTTP/1.1 200 OK
  date: Thu, 21 May 2026 22:10:21 GMT
  server: uvicorn
  content-length: 220
  content-type: application/json
  connection: close

{"status":"unhealthy","service_name":"toc-rebuild","service_version":"1.0.0","protocol_version":"v1","checks":{"minio":"unconfigured","llm":"not_configured","dependencies":"ok"},"timestamp":"2026-05-21T22:10:21.446431Z"}
```

---

## 3. 端点选择与决策理由 (Chosen Endpoint & Rationale)

- **所选持久端点**: `http://mineru2table:8000`
- **决策理由**:
  1. 探测矩阵证实 `mineru2table:8000` 在 Docker 网络 `cms-network` 下完全可达且稳定解析（与 `mineru2table-api` 均指向容器 IP `172.24.0.6`）。
  2. 根据 `Endpoint Selection Rules`，首选端点可达时应直接采用首选端点。
  3. 该端点完美解耦了具体的宿主机或容器临时 IP，属于持久化的 Docker 容器级 DNS 解析。

---

## 4. 持久化配置渲染证据 (Rendered Config Evidence)

通过修改 `docker-compose.yml` 与 `.env.example`，将选定的持久端点写入 Luceon 配置面。

### `docker-compose config` 渲染输出：
```bash
$ docker-compose config | grep CLEANSERVICE
      CLEANSERVICE_ENABLED: "false"
      CLEANSERVICE_ENDPOINT: http://mineru2table:8000
      CLEANSERVICE_STORAGE_ENDPOINT: minio:9000
      CLEANSERVICE_STORAGE_USE_SSL: "false"
      CLEANSERVICE_SUBMITTED_BY: luceon2026/cleanservice-worker
```
- **配置结论**:
  - `CLEANSERVICE_ENABLED` 被明确置为 `false`（不启用调度，不启用自动分发）。
  - `CLEANSERVICE_ENDPOINT` 成功指向持久化的 `http://mineru2table:8000`。

---

## 5. 脱敏凭证检查矩阵 (Masked Credential Matrix)

本次任务严格遵守安全边界，没有任何凭证注入。脱敏状态如下：

| 配置项名称 | 当前值 | 是否包含真实密钥 | 状态 |
| :--- | :--- | :--- | :--- |
| `MINIO_ACCESS_KEY` | *(empty)* | 否 | 脱敏/安全 |
| `MINIO_SECRET_KEY` | *(empty)* | 否 | 脱敏/安全 |
| `DEEPSEEK_API_KEY` | *(empty)* | 否 | 脱敏/安全 |
| `TOC_REBUILD_CALLBACK_SECRET` | *(empty)* | 否 | 脱敏/安全 |

---

## 6. Job-Store (jobs.json) 状态校验

本次任务前后，宿主机关联的 job-store 状态完全一致，未发生任何改变：

| 校验维度 | 任务前基准 (Task 236 终态) | 任务后实际状态 | 是否发生变化 |
| :--- | :--- | :--- | :--- |
| **Path** | `/workspace/ops/Mineru2Tables/data/jobs.json` | `/workspace/ops/Mineru2Tables/data/jobs.json` | 否 |
| **Size** | `718` 字节 | `718` 字节 | 否 |
| **SHA256 Hash** | `29d5621bcca3d626b8f27289caabd13ba6cd835913a76b9e2cbd8fd8d4577413` | `29d5621bcca3d626b8f27289caabd13ba6cd835913a76b9e2cbd8fd8d4577413` | **否** |
| **Key/Mock Job** | `luceon-optionb-mock-job-1779399902295` | `luceon-optionb-mock-job-1779399902295` | 否 |

---

## 7. 业务红线校验 (Red Lines Compliance)

- **是否向 `mineru2table` 发送过 `POST` 请求？**: **否 (No)** (完全为只读 GET /health)
- **是否修改了任何业务源码 (`server/**`, `src/**`)？**: **否 (No)**
- **是否修改了包/锁文件？**: **否 (No)**
- **是否改动了 Luceon 数据库、MinIO 数据、容器卷或外部资产文件？**: **否 (No)**
- **是否重启了任何 Docker 容器或重建了服务？**: **否 (No)**

---

## 8. 任务结论与分类交付

- **报告文件路径**: `TaskAndReport/2026-05-22T05-59-20+0800_P0-CleanService-Durable-Mineru2Table-Endpoint-Configuration-NoPost-Preflight_REPORT.md`
- **最终分类结果**: `DURABLE_ENDPOINT_CONFIGURED_NO_POST`
