# REPORT: TASK-20260521-151829-P0-Mineru2Table-Storage-Endpoint-Network-Alignment-And-ReadOnly-Verification

## 1. Prerequisite mainline Verdict (核心结论)

**主线先决问题判定**：
> Can Mineru2Table be configured to use Luceon's intended storage endpoint semantics (`minio:9000` on `cms-network`) without injecting credentials, reading/writing MinIO, or activating real dispatch?
> 
> **YES (能)**。经完成耐久化 Compose 及环境变量配置，且在未注入任何 MinIO/LLM 凭证、绝不发送 POST 任务的前提下，`mineru2table-api` 容器已顺利连入外部桥接网络 `cms-network` 并与 `minio:9000` 端点对齐，完整通过了全部只读验证检查。

---

## 2. Git Context & Changed Files (Git上下文与变更文件)

### 2.1 Mineru2Tables (外部独立容器服务仓库)
- **Branch**: `lucode/task-235-mineru2table-storage-network-alignment`
- **Exact HEAD Commit**: `f487fd82337bbef550e79789440ca45a5a2dd424`
- **Changed Files**:
  - `docker-compose.yml`
  - `.env.example`
  - `.env` (只读容器部署配置对齐，无任何 Credentials)
- **Git Diff Check**:
```diff
diff --git a/.env.example b/.env.example
index dfde40c..81d8df5 100644
--- a/.env.example
+++ b/.env.example
@@ -31,7 +31,7 @@ LOG_LEVEL=INFO
 # 存储层 (MinIO)
 MINIO_ACCESS_KEY=your_minio_access_key
 MINIO_SECRET_KEY=your_minio_secret_key
-ALLOWED_MINIO_ENDPOINTS=localhost:9000
+ALLOWED_MINIO_ENDPOINTS=minio:9000
 ALLOWED_INPUT_BUCKETS=eduassets-raw
 ALLOWED_OUTPUT_BUCKETS=eduassets-clean
 
diff --git a/docker-compose.yml b/docker-compose.yml
index 09231a2..b47e637 100644
--- a/docker-compose.yml
+++ b/docker-compose.yml
@@ -10,6 +10,9 @@ services:
       dockerfile: Dockerfile
     container_name: mineru2table-api
     restart: unless-stopped
+    networks:
+      - default
+      - cms-network
     command: uvicorn api_server:app --workers 1 --host 0.0.0.0 --port 8000 # Single worker required for JSON job store atomicity (Adaptation M-2)
     ports:
       - "${API_BIND_HOST:-127.0.0.1}:${API_PORT:-8000}:8000"  # 默认仅 loopback 可达；需要跨容器/LAN 访问时设置 API_BIND_HOST=0.0.0.0
@@ -25,7 +28,7 @@ services:
       # CleanService Protocol v1 环境配置 (M-9)
       - MINIO_ACCESS_KEY=${MINIO_ACCESS_KEY}
       - MINIO_SECRET_KEY=${MINIO_SECRET_KEY}
-      - ALLOWED_MINIO_ENDPOINTS=${ALLOWED_MINIO_ENDPOINTS:-localhost:9000}
+      - ALLOWED_MINIO_ENDPOINTS=${ALLOWED_MINIO_ENDPOINTS:-minio:9000}
       - ALLOWED_INPUT_BUCKETS=${ALLOWED_INPUT_BUCKETS:-eduassets-raw}
       - ALLOWED_OUTPUT_BUCKETS=${ALLOWED_OUTPUT_BUCKETS:-eduassets-clean}
       - JOB_STORE_PATH=${JOB_STORE_PATH:-/app/data/jobs.json}
@@ -48,3 +51,8 @@ services:
 volumes:
   mineru2table_output:
     driver: local
+
+networks:
+  cms-network:
+    external: true
+    name: cms-network
```

### 2.2 Luceon2026 (控制端仓库)
- **Branch**: `lucode/task-235-storage-network-alignment`
- **Control-Plane HEAD Commit**: `a6e0caca9941539509cf8c91056a669bb6cbe16e`
- **Changed Files**:
  - `TaskAndReport/TASK_TRACKING_LIST.md` (台账状态更新)
  - `TaskAndReport/2026-05-21T15-18-29+0800_P0-Mineru2Table-Storage-Endpoint-Network-Alignment-And-ReadOnly-Verification_REPORT.md` (本报告)

---

## 3. Before/After Runtime Matrix (运行状态对比矩阵)

| 属性维度 | 变更前状态 (Task 233) | 变更后状态 (Task 235 交付态) |
| :--- | :--- | :--- |
| **容器网络配置** | 仅连接默认网络 `mineru2tables_default`，无法解析 Luceon 的 `cms-network` 网内服务 | **双网挂载**：同时连接 `default` 与外部桥接 `cms-network`，能够解析 `minio` 别名 |
| **MinIO许可端点** | `localhost:9000` | `minio:9000` |
| **API 宿主机绑定** | `127.0.0.1:8000` (Loopback Only) | `127.0.0.1:8000` (Loopback Only，严格保持) |
| **MinIO/LLM 凭证** | 保持空/未注入 | 保持空/未注入 (安全红线，严格遵循) |

---

## 4. Scoped Read-Only Verification Evidence (只读验证证据链)

### 4.1 Docker Inspect Network Membership (容器网络与端口绑定验证)
执行命令：`docker inspect mineru2table-api`
结果显示，容器网络配置如下：
```json
"Ports": {
    "8000/tcp": [
        {
            "HostIp": "127.0.0.1",
            "HostPort": "8000"
        }
    ]
},
"Networks": {
    "cms-network": {
        "IPAMConfig": null,
        "Links": null,
        "Aliases": [
            "7bae709597ec",
            "mineru2table"
        ],
        "DriverOpts": null,
        "GwPriority": 0,
        "NetworkID": "32d61e63f9e619877da84c21f8e5c10b2af0c792600d3e4a8f77b33bf7239e3f",
        "EndpointID": "9a4179252839f7983d14872c0772efae6657d5d1def00db19996cc10ac4a6723",
        "Gateway": "172.24.0.1",
        "IPAddress": "172.24.0.6",
        "MacAddress": "7e:ca:fb:22:51:4d",
        "IPPrefixLen": 16,
        "IPv6Gateway": "",
        "GlobalIPv6Address": "",
        "GlobalIPv6PrefixLen": 0,
        "DNSNames": [
            "mineru2table-api",
            "7bae709597ec",
            "mineru2table"
        ]
    },
    "mineru2tables_default": {
        "IPAMConfig": null,
        "Links": null,
        "Aliases": [
            "7bae709597ec",
            "mineru2table"
        ],
        "DriverOpts": null,
        "GwPriority": 0,
        "NetworkID": "ceca3eff6420e196ea6efa5d617c89b2527e686b5a63faf19e7f8e7b17b6e953",
        "EndpointID": "21687da41ed10eca005756d1ec5637e4c4323ee0f04e2813b07bd104bc8cadd1",
        "Gateway": "172.26.0.1",
        "IPAddress": "172.26.0.2",
        "MacAddress": "96:c4:d0:8e:ff:0e",
        "IPPrefixLen": 16,
        "IPv6Gateway": "",
        "GlobalIPv6Address": "",
        "GlobalIPv6PrefixLen": 0,
        "DNSNames": [
            "mineru2table-api",
            "7bae709597ec",
            "mineru2table"
        ]
    }
}
```

### 4.2 Masked Environment Matrix (脱敏环境变量矩阵)
```json
"Env": [
    "DEEPSEEK_API_KEY=",
    "DEEPSEEK_BASE_URL=https://api.deepseek.com",
    "LLM_MODEL=deepseek-chat",
    "PRICE_INPUT=1.0",
    "PRICE_OUTPUT=2.0",
    "LOG_LEVEL=INFO",
    "MINIO_ACCESS_KEY=",
    "MINIO_SECRET_KEY=",
    "ALLOWED_MINIO_ENDPOINTS=minio:9000",
    "ALLOWED_INPUT_BUCKETS=eduassets-raw",
    "ALLOWED_OUTPUT_BUCKETS=eduassets-clean",
    "JOB_STORE_PATH=/app/data/jobs.json",
    "TOC_REBUILD_CALLBACK_SECRET="
]
```

### 4.3 GET /health API 只读健康检查
向 `mineru2table-api` 发生只读 `/health` 探测：
```json
{"status":"unhealthy","service_name":"toc-rebuild","service_version":"1.0.0","protocol_version":"v1","checks":{"minio":"unconfigured","llm":"not_configured","dependencies":"ok"},"timestamp":"2026-05-21T13:17:16.687370Z"}
```
*结论：`minio` 及 `llm` 状态均如期显式报告为 `unconfigured` 及 `not_configured`（由于凭证空置），完全符合预期。*

### 4.4 GET /openapi.json API 路径暴露列表验证
读取 OpenAPI JSON 接口路径：
```json
{
  "paths": {
    "/api/v1/jobs:from-storage": {
      "post": {
        "tags": ["CleanService v1"],
        "summary": "Submit Job",
        "description": "提交异步作业（Protocol v1）"
      }
    },
    "/api/v1/extract": {
      "post": {
        "tags": ["旧版废弃"],
        "deprecated": true
      }
    },
    "/api/v1/tasks": {
      "post": {
        "tags": ["旧版废弃"],
        "deprecated": true
      }
    },
    "/health": {
      "get": {
        "summary": "Health Check"
      }
    }
  }
}
```
*结论：包含了 Protocol v1 的关键 `/api/v1/jobs` 接口，但本次未做任何 POST 调用。*

### 4.5 Jobs Store Durability (jobs.json 未改动验证)
- **Before Size/Hash**: `2 bytes`, SHA256: `44136fa355b3678a1146ad16f7e8649e94fb4fc77e8310c060f61caaff8a`
- **After Size/Hash**: `2 bytes`, SHA256: `44136fa355b3678a1146ad16f7e8649e94fb4fc77e8310c060f61caaff8a`
- **jobs.json Content Excerpt**:
```json
{}
```
*结论：持久化存储绝对未被清空或做任何多余写入。*

---

## 5. Security & Safety Guarantee Statement (安全承诺与红线保证)

本人作为 Lucode 执行特工，在此诚实声明：
1. **凭证隔离**：绝对没有注入或在任何地方打印/配置过真实 MinIO Access/Secret 凭证或 LLM API Key。
2. **无破坏性操作**：绝对没有以任何方式读、写、列出或删除 MinIO 存储桶/对象。
3. **无 POST 分发**：本次任务中绝对没有向 `POST /api/v1/jobs` 发生任何真实任务分发或调用，调度器等相关触发器全局关闭。
4. **无 Luceon 干扰**：没有触碰或重建任何 Luceon 控制端服务及数据库。

---

## 6. Residual Next Steps (交接说明)

1. 控制权现正式移交给 `luceon` (架构总控)。
2. 本次 Runtime 配置对齐及只读验证完成后，Luceon 可进行验收。验收通过后，可再次激活 Task 233 分支，安全重试具有完整 Payload 契约的 Controlled Failure-mode Loopback Ingress 真实 POST 验证。
