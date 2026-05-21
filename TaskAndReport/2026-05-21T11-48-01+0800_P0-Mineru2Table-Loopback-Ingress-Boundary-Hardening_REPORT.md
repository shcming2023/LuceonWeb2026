# Mineru2Table Loopback Ingress Boundary Hardening Report

## 1. Executive Summary (摘要)

本报告记录了 **TASK-20260521-114801-P0-Mineru2Table-Loopback-Ingress-Boundary-Hardening** 的完整执行过程与结果。

根据任务书要求，我们已精准完成以下工作：
1. **外部分支创建**：在 `shcming2023/Mineru2Table2026` 创建 `lucode/task-227-mineru2table-loopback-ingress` 分支，仅修改 `docker-compose.yml` 端口映射和 `.env.example` 文档。
2. **端口映射收窄**：默认绑定从 `0.0.0.0:8000` / `[::]:8000` 收窄为 `127.0.0.1:8000`（loopback-only），通过可选 `API_BIND_HOST` 环境变量保留显式覆盖能力。
3. **部署区同步与容器重建**：将分支同步至宿主机部署区，重建镜像并 recreate 容器，无 volume 清理。
4. **端口验证**：`docker ps` 确认 `127.0.0.1:8000->8000/tcp`，不再显示 `0.0.0.0` 或 `[::]`。
5. **只读端点验证**：`/health` 返回 HTTP 200 且诚实报告依赖未配置状态；`/openapi.json` 暴露 Protocol v1 全部路径。

---

## 2. Source Branch And Final SHA

- **外部仓库**：`shcming2023/Mineru2Table2026`
- **分支**：`lucode/task-227-mineru2table-loopback-ingress`
- **最终 SHA**：`af80ced635755384a2c878110013c3e2d8f9cb9a`
- **父提交**：`b43852485d9f0e7d2918578df494afefe6b2f687`（Task 225/226 验收 SHA）
- **GitHub 远端**：已推送至 `origin/lucode/task-227-mineru2table-loopback-ingress`

---

## 3. Changed-File Audit (变更文件审计)

仅修改 2 个允许文件，`git diff --check` 通过：

```
 .env.example       | 2 ++
 docker-compose.yml | 2 +-
 2 files changed, 3 insertions(+), 1 deletion(-)
```

### A. `docker-compose.yml`
```diff
-      - "${API_PORT:-8000}:8000"  # 支持自定义端口映射，默认 8000
+      - "${API_BIND_HOST:-127.0.0.1}:${API_PORT:-8000}:8000"  # 默认仅 loopback 可达；需要跨容器/LAN 访问时设置 API_BIND_HOST=0.0.0.0
```

### B. `.env.example`
```diff
 # ---- Docker 部署配置 (可选) ----
+# API 监听绑定地址（默认 127.0.0.1 仅 loopback；需要跨容器/LAN 访问时设置为 0.0.0.0）
+API_BIND_HOST=127.0.0.1
 # API 对外暴露端口
 API_PORT=8000
```

**未修改文件**：`src/**`、`api_server.py`、业务逻辑、存储逻辑、LLM 逻辑、解析逻辑、协议行为、真实数据、样本资产、生成输出、密钥、运行时卷数据均未触及。

---

## 4. Compose Config Validation (Compose 静态校验)

```bash
git diff --check
# exit code: 0 — PASSED（无空白/格式问题）
```

---

## 5. Local Rebuild/Recreate Evidence (本地重建证据)

### A. 部署区同步
```bash
# 通过 alpine/git 容器将分支传入部署区
docker run --rm \
  -v /Users/concm/prod_workspace/Mineru2Tables:/repo_dest \
  -v /Users/concm/Dev_workspace/Luceon2026/scratch/Mineru2Table2026:/repo_src \
  alpine/git -C /repo_dest fetch /repo_src lucode/task-227-mineru2table-loopback-ingress:lucode/task-227-mineru2table-loopback-ingress

# checkout 分支
docker run --rm -v /Users/concm/prod_workspace/Mineru2Tables:/repo -w /repo \
  alpine/git checkout lucode/task-227-mineru2table-loopback-ingress
```

部署区 HEAD 确认：`af80ced635755384a2c878110013c3e2d8f9cb9a`

### B. 镜像重建
```bash
docker run --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /Users/concm/prod_workspace/Mineru2Tables:/Users/concm/prod_workspace/Mineru2Tables \
  -w /Users/concm/prod_workspace/Mineru2Tables \
  docker:latest \
  docker compose build --build-arg GIT_COMMIT=af80ced635755384a2c878110013c3e2d8f9cb9a mineru2table
```
- 镜像 `mineru2tables-mineru2table:latest` 重建完成时间：`2026-05-21 04:00:31 UTC`

### C. 容器 Recreate
```bash
docker compose up -d --no-deps mineru2table
```
```text
Container mineru2table-api Recreate
Container mineru2table-api Recreated
Container mineru2table-api Starting
Container mineru2table-api Started
```

---

## 6. Port/Listener Evidence Before And After (端口证据)

### Before（Task 226 状态）
```text
NAMES              STATUS                    PORTS
mineru2table-api   Up 15 minutes (healthy)   0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp
```

### After（Task 227 loopback 收窄后）
```text
NAMES              STATUS                    PORTS
mineru2table-api   Up 10 seconds (healthy)   127.0.0.1:8000->8000/tcp
```

**验证通过**：
- `[YES]` `127.0.0.1:8000->8000/tcp` 出现
- `[YES]` `0.0.0.0:8000` 不再出现
- `[YES]` `[::]:8000` 不再出现

---

## 7. Read-Only Endpoint Evidence (只读端点验证)

### A. Health Endpoint (`GET /health`)
```bash
curl -fsS http://host.docker.internal:8000/health
```
- **HTTP 状态码**：`200 OK`
- **JSON 响应**：
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
    "timestamp": "2026-05-21T04:06:43.336531Z"
  }
  ```

### B. OpenAPI Paths (`GET /openapi.json`)
```text
/health
/api/v1/jobs
/api/v1/jobs/{job_id}
/api/v1/jobs:from-storage
/api/v1/extract
/api/v1/tasks
/api/v1/tasks/{task_id}
```

Protocol v1 路径完美就绪。无 `POST` 路由被调用。

---

## 8. Safety Boundary Statement (安全边界声明)

- **零 Job 提交**：未调用 `POST /api/v1/jobs`、`POST /api/v1/jobs:from-storage` 或任何废弃创建端点。
- **零 MinIO 操作**：未读写任何 MinIO 对象或存储桶。
- **零 LLM 调用**：未调用任何 DeepSeek/LLM API。
- **零 DB 变更**：未修改任何数据库行。
- **零 Volume 操作**：未执行 `docker compose down -v`、`docker volume prune` 或删除任何数据目录。
- **零密钥操作**：未创建、修改、打印或读取任何 `.env` 密钥文件。
- **零防火墙/网络重配置**：未修改宿主机防火墙、路由器、VPN 或 host-level 网络配置。
- **零 Luceon 连线**：未进行任何 Luceon CleanService orchestrator wiring。

---

## 9. Residual Risks And Next-Step Recommendation (遗留风险与下一步建议)

### 已解决
- `mineru2table-api` 不再在所有网络接口暴露 Protocol v1 job-submission 端点。

### 遗留（按任务书明确后置）
- **Bearer/API-token 强制验证**：当前 `API_KEY` 配置已存在但为可选。是否需要在 Luceon wiring 前强制启用有待决策。
- **Luceon CleanServiceWorker HTTP Transport wiring**：需要通过 loopback `127.0.0.1:8000` 进行集成。
- **Webhook callback 集成**：签名回调端点联调。
- **MinIO/LLM end-to-end 行为验证**：需要配置真实凭证后验证。
- **部署区分支状态**：部署区当前在 `lucode/task-227-mineru2table-loopback-ingress` 分支而非 `main`。合并至 `main` 需 luceon 审核决策。

---

## 10. Final Status Recommendation (最终状态建议)

> [!IMPORTANT]
> **Lucode 角色建议**：本任务已完全实现所有正面验收条件——端口 loopback 收窄、只读端点验证、无越界操作。建议将本任务状态推荐为待审。

控制权与台账现在正式交还给 **Luceon** 角色。

---
*Reported by lucode on 2026-05-21.*
