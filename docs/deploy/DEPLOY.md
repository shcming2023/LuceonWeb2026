# EduAsset CMS — Docker 部署说明

> Current Phase 1 note: the standard path is local MinerU FastAPI + Docker MinIO + host Ollama `qwen3.5:9b`. Online MinerU, Kimi/Moonshot, and tmpfiles routes remain compatibility surfaces unless a task explicitly assigns them.

## 一、架构概览

```
宿主机
│
├── Docker: cms-frontend（Nginx，对外端口 ${CMS_PORT:-8080}）
│   ├── 托管前端静态文件（/cms/）
│   ├── /__proxy/upload/   → upload-server:8788
│   ├── /__proxy/db/       → db-server:8789
│   ├── /api/              → host.docker.internal:3001（备份后端，可选）
│   ├── /__proxy/mineru-cdn/ → cdn-mineru.openxlab.org.cn（compatibility）
│   ├── /__proxy/mineru/   → mineru.net（compatibility）
│   ├── /__proxy/kimi/     → api.kimi.ai（compatibility）
│   ├── /__proxy/moonshot/ → api.moonshot.cn（compatibility）
│   └── /__proxy/tmpfiles/ → tmpfiles.org（legacy）
│
├── Docker: upload-server（Node.js，内部端口 8788）
│   ├── 接收文件上传（最大 200 MB），基于磁盘缓冲防 OOM，转存到 MinIO
│   ├── 当前主线转存到 MinIO；core parse/AI 路径不允许 silent fallback
│   ├── 提供 MinerU 解析结果转存接口
│   └── 支持优雅停机（Graceful Shutdown）防数据损坏
│
├── Docker: db-server（Node.js，内部端口 8789）
│   ├── JSON 文件 REST API（完整 CRUD，带基础输入验证）
│   ├── 数据文件：/data/db-data.json（数据卷 cms-db-data 持久化）
│   ├── 支持集合：materials、assetDetails、processTasks、tasks、products、flexibleTags、aiRules、settings
│   └── 支持优雅停机（Graceful Shutdown）防数据丢失
│
├── Docker: minio（MinIO 对象存储）
│   ├── MinIO API：内部端口 9000
│   ├── MinIO Web 控制台：9001（可对外暴露用于管理）
│   └── 数据卷：cms-minio-data
│
└── [可选] backup-backend（独立部署，非本仓库）
    └── 提供 /api/* 接口（宿主机默认端口 3001）
```

**数据持久化层次**：
- `cms-minio-data` 卷 → 上传的原始文件（PDF、图片等）；原始文件路径格式：`originals/{materialId}/{timestamp}-name.pdf`
- `cms-db-data` 卷 → 业务数据（资料库、标签、规则等，JSON 文件存储），同时包含批处理队列快照
- 浏览器 `localStorage` → 当前会话缓存，启动时优先从 db-server 加载

> **重要**：`cms-db-data` 和 `cms-minio-data` 是**状态卷，不是镜像卷**。
> - `docker compose up -d --build` 只重建镜像，不会清空这些卷
> - 生产环境默认行为：重启后保留所有数据和队列状态
> - 开发期如需全新启动：`docker compose down -v && docker compose up -d --build` 或设置 `CLEAR_QUEUE_ON_BOOT=true`

---

## 二、三个子系统说明

### 2.1 教育资产管理系统（EduAsset CMS）

**功能**：管理教育资料从原始文件到成品的完整生命周期。

**核心流水线**：原始资料 → MinerU 解析（Rawcode）→ AI 清洗（Cleancode）→ 成品

**依赖的外部服务**：

| 服务 | 地址 | 用途 | 配置方式 |
|------|------|------|---------|
| Local MinerU FastAPI | `http://host.docker.internal:8083` | 当前主线 PDF/文档解析 | 运行环境 `LOCAL_MINERU_ENDPOINT` |
| Host Ollama | `http://host.docker.internal:11434` | 当前主线 AI 元数据识别，模型 `qwen3.5:9b` | 运行环境 `OLLAMA_API_URL` / `OLLAMA_TIER2_MODEL` |
| Online MinerU | `https://mineru.net` | compatibility-only | 仅在显式任务中启用 |
| Kimi/Moonshot | `https://api.moonshot.cn` | compatibility-only | 系统设置页面或环境变量 |
| MinIO | `minio:9000`（内部） | 持久化文件存储 | `.env` 中配置，upload-server 自动使用 |
| tmpfiles.org | `https://tmpfiles.org` | legacy 临时文件中转 | 当前主线不依赖 |

> Online MinerU API Key 和 Kimi API Key 属于兼容路径配置，**不得写入代码仓库**。当前生产运行口径以环境变量和 `docs/deploy/PRODUCTION_RUNTIME_OWNERSHIP.md` 为准。

### 2.2 Overleaf 备份系统

**功能**：备份 Overleaf 实例的所有项目，支持灾备备份、文件浏览、定时调度。

**依赖**：需要独立的备份后端服务（`backup-backend`，不在本仓库），前端通过 `/api/*` 接口通信。

**认证方式**：请求头 `x-access-token`，可通过 URL 参数 `?token=xxx` 自动注入浏览器。

**访问地址**：`http://your-host:8080/cms/backup`

### 2.3 LaTeX 工具集

**功能**：对 LaTeX ZIP 压缩包进行图片去冗余和大图压缩（>1MB 压缩至 ≤1MB）。

**特点**：完全在浏览器本地处理，**无需后端，无网络请求**。

**访问地址**：`http://your-host:8080/cms/backup/latex`

---

## 三、快速部署步骤

### 前置要求

- 宿主机已安装 Docker 20.10+ 和 Docker Compose v2
- 已克隆本仓库到宿主机

### 步骤

```bash
# 1. 进入项目目录
cd /path/to/Luceon2026

# 2. 复制并配置环境变量
cp .env.example .env
# 用编辑器修改 .env，至少检查并设置以下关键项：
#   CMS_PORT            — 前端对外端口（默认 8080）
#   MINIO_ACCESS_KEY    — MinIO 访问密钥（生产环境请替换）
#   MINIO_SECRET_KEY    — MinIO 私钥（生产环境请替换）
#   OVERLEAF_ACCESS_TOKEN — 如需备份功能请填写

# 3. 构建并启动全部服务
docker compose up -d --build

# 4. 验证服务状态（应显示 healthy）
docker compose ps

# 5. 查看各服务日志
docker compose logs -f cms-frontend
docker compose logs -f upload-server
docker compose logs -f db-server

# 6. 访问应用
open http://localhost:8080/cms/
```

### 停止服务

```bash
docker compose down
```

### 更新部署

```bash
git pull
docker compose up -d --build
```

---

## 四、环境变量说明

完整的环境变量列表见 `.env.example`，以下是关键配置项说明：

### 通用配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `CMS_PORT` | `8080` | 前端对外暴露的宿主机端口 |
| `UPLOAD_PORT` | `8788` | 上传服务内部端口（通常无需修改） |
| `TZ` | `Asia/Shanghai` | 容器时区 |

### MinIO 对象存储

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `STORAGE_BACKEND` | `minio` | 存储后端：`minio`（私有存储）或 `tmpfiles`（公开临时存储） |
| `MINIO_ENDPOINT` | `minio` | MinIO 服务端点（Docker 内部 DNS，通常无需修改） |
| `MINIO_PORT` | `9000` | MinIO API 端口 |
| `MINIO_ACCESS_KEY` | `minioadmin` | **生产环境请替换为强密钥** |
| `MINIO_SECRET_KEY` | `minioadmin` | **生产环境请替换为强密钥** |
| `MINIO_BUCKET` | `eduassets` | 存储桶名称（首次启动自动创建） |
| `MINIO_PRESIGNED_EXPIRY` | `3600` | 预签名 URL 有效期（秒），控制文件临时访问时间 |

### Overleaf 备份系统

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `OVERLEAF_BASE_URL` | `http://host.docker.internal:80` | Overleaf 实例地址 |
| `OVERLEAF_ADMIN_EMAIL` | — | Overleaf 管理员邮箱 |
| `OVERLEAF_ADMIN_PASSWORD` | — | Overleaf 管理员密码 |
| `HOST_BACKUP_PATH` | — | 备份文件宿主机存储路径（绝对路径） |
| `OVERLEAF_ACCESS_TOKEN` | — | 备份系统 API Token（见第五节） |

### AI / Parser 兼容配置

| 变量名 | 说明 |
|--------|------|
| `LOCAL_MINERU_ENDPOINT` | 当前主线本机 MinerU FastAPI endpoint |
| `OLLAMA_API_URL` | 当前主线本机 Ollama endpoint |
| `OLLAMA_TIER2_MODEL` | 当前主线模型，当前为 `qwen3.5:9b` |
| `MINERU_API_KEY` | 在线 MinerU compatibility-only 配置 |
| `KIMI_API_KEY` | Kimi/Moonshot compatibility-only 配置 |

### Mac vs Linux：host.docker.internal 与 extra_hosts

- **Mac（Docker Desktop）**：默认支持 `host.docker.internal`，一般不需要在 compose 中配置 `extra_hosts`。
- **Linux**：如需容器访问宿主机服务（例如宿主机 Ollama `http://host.docker.internal:11434`），通常需要在 compose 中添加 `extra_hosts: host.docker.internal:host-gateway`。

### 生产本地 override 契约

当前生产部署路径 `/Users/concm/prod_workspace/Luceon2026` 允许保留本地 `docker-compose.override.yml`，但该 override 是生产本地运行配置，不是生产发布就绪声明，也不能替代 release-candidate 的 HEAD 与配置边界确认。

生产运行所有权和 endpoint truth 见 `docs/deploy/PRODUCTION_RUNTIME_OWNERSHIP.md`。其中 `LOCAL_MINERU_ENDPOINT`、`OLLAMA_API_URL`、`OLLAMA_TIER2_MODEL` 与 strict AI fallback 开关必须由运行环境或 compose 固定；DB settings 不能作为生产运行口径。

当前已接受的 production-local override 边界如下：

| 项目 | 当前要求 | 发布边界 |
|------|----------|----------|
| `DISABLE_AI_SKELETON_FALLBACK=true` | 必须保留，用于 Phase 1 严格 AI 语义，避免 skeleton fallback 被当作真实 AI 识别结果。 | 属于必需运行语义；变更前需要单独任务和验证。 |
| `OLLAMA_TIER2_MODEL=qwen3.5:9b` | 必须保留，用于当前 Standard 模型。 | 属于当前主线模型约束；变更前需要单独任务和验证。 |
| MinIO console | 生产本地要求 local-only 绑定，例如 `127.0.0.1:19001:9001`。 | 发布边界确认必须检查实际 production override；仓库根 override 不能替代生产事实。 |

Release-candidate 命名前必须同时确认：

- 生产工作区的精确 Git HEAD。
- `docker-compose.override.yml` 的实际内容和上述边界是否一致。
- MinIO console 暴露策略已经被明确接受或变更。
- 没有把本地 override 的存在表述为生产发布就绪。

以下操作仍需单独用户授权或未来明确记录的治理流程授权，不得仅凭本节执行：

- production sync、rebuild、restart、deploy、rollback。
- Docker pull/build/compose 操作。
- production `docker-compose.override.yml` 新增、删除或修改。
- DB、MinIO、Docker volume、任务、产物、secret 或本地运行数据变更。

---

## 五、API Token 配置（Overleaf 备份）

备份系统使用 `x-access-token` 请求头认证，有两种注入方式：

**方式一（推荐）**：通过 URL 参数自动写入浏览器 localStorage：

```
http://your-host:8080/cms/?token=YOUR_TOKEN_HERE
```

访问后 Token 自动保存，后续无需重复传入。支持任意页面进入方式：
- 硬刷新带 token 参数 → `main.tsx` 启动时处理
- SPA 内部跳转带 token 参数（如外部链接跳转到 `/backup`）→ `Layout.tsx` 自动捕获，并清除 URL 中的 token 参数

**方式二**：在系统设置页面（`/cms/settings`）的"连接设置" Tab 中查看当前 Token 状态。

---

## 六、Overleaf 备份后端配置

### 方式 A：后端在宿主机独立运行（推荐）

备份后端已在宿主机独立运行（监听 3001 端口），`docker/nginx.conf` 中代理配置默认为：

```nginx
location /api/ {
    proxy_pass http://host.docker.internal:3001/;
}
```

修改后重启前端容器：

```bash
docker compose restart cms-frontend
```

### 方式 B：后端作为 Docker 服务运行

取消注释 `docker-compose.yml` 中的 `backup-backend` 服务块，并确保 `docker/nginx.conf` 中 `/api/` 指向 `http://backup-backend:3001/`。

---

## 七、生产环境安全建议

1. **修改 MinIO 默认密钥**：将 `.env` 中 `MINIO_ACCESS_KEY` 和 `MINIO_SECRET_KEY` 替换为强密钥（随机字符串）
2. **MinIO 控制台端口**：生产本地应使用 local-only 绑定，例如 `127.0.0.1:19001:9001`
3. **HTTPS**：建议在 Docker 前面加 Caddy 或 Nginx 反向代理处理 HTTPS：
   ```
   Internet → Caddy（443）→ Docker cms-frontend（8080）
   ```
4. **Token 有效期**：根据实际需要调整 `MINIO_PRESIGNED_EXPIRY`（文件访问有效期）

---

## 八、部署验证里程碑（2026-04-14）

### 里程碑：Docker 部署首次测试通过 ✅

在 Mac Mini 局域网环境下，使用 Docker Compose 部署的完整系统成功通过端到端功能验证。

#### 验证环境
- **宿主机**：Mac Mini（`192.168.31.33`）
- **部署方式**：Docker Compose（`docker compose up -d --build`）
- **前端端口**：`8081`（`CMS_PORT=8081`）
- **访问地址**：`http://192.168.31.33:8081/cms/`
- **MinerU 引擎**：云端 API（`mineru.net`）
- **测试文件**：`FastTest01.pdf`（16.73 KB）

#### 验证结果
- ✅ 所有容器启动成功（`cms-frontend`、`upload-server`、`db-server`、`minio`）
- ✅ 前端静态文件正常加载
- ✅ 文件上传成功（`upload-server` 接收并转存到 MinIO）
- ✅ MinerU 解析流程完整运行成功
- ✅ 解析结果正确转存并展示

#### 关键发现
**问题根因**：MinerU API Key 未正确配置

- 错误现象：`HTTP 401 - {"msgCode":"A0202","msg":"user authenticate failed"}`
- 根本原因：系统设置页面的 MinerU `API Key` 填写错误或带 `Bearer ` 前缀
- 修正方法：
  1. 打开系统设置页面（`/cms/settings`）
  2. 在 MinerU 配置中填入正确的 API Key（裸 key，**不带 `Bearer ` 前缀**）
  3. 保存配置
  4. 重新上传测试文件

**配置注意事项**：
- MinerU API Key 在系统设置页面配置，**不要在 `.env` 中填写**（当前前端未实现环境变量注入）
- 填写 API Key 时：
  - ✅ 正确：`sk-xxxxx-xxxxx-xxxxx`（裸 key）
  - ❌ 错误：`Bearer sk-xxxxx-xxxxx-xxxxx`（带前缀，会导致双重前缀）
  - ❌ 错误：`"sk-xxxxx-xxxxx-xxxxx"`（带引号）
- API Key 会持久化到 `db-server`（`/data/db-data.json`），但为了安全不写入 `localStorage`

---

## 九、常见问题

**Q: 访问 `/cms/` 后页面空白？**
A: 检查 `docker compose logs cms-frontend`，确认 Nginx 启动正常。打开浏览器 Console 查看 JS 错误。

**Q: 文件上传失败？**
A: 检查 `docker compose logs upload-server`。当前本地 UAT 常用 `http://localhost:8081/__proxy/upload/health` 验证服务健康；如使用其他 `CMS_PORT`，请替换端口。

**Q: MinIO 无法启动？**
A: 检查 `docker compose logs minio`，确认数据卷 `cms-minio-data` 可用。MinIO 默认密钥为 `minioadmin`，请通过 `.env` 修改。

**Q: 文件上传时 MinIO 连接失败？**
A: 确认 `docker compose ps minio` 显示 healthy，并检查 upload-server 日志。当前主线依赖 MinIO 持久化对象存储，不应把 tmpfiles legacy fallback 当作核心链路成功。

**Q: 如何访问 MinIO Web 控制台？**
A: 本地/UAT 通常访问 `http://localhost:19001`，使用 `.env` 中配置的 `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` 登录。生产发布边界要求控制台 local-only。

**Q: 如何切换存储后端？**
A: 当前主线使用 `STORAGE_BACKEND=minio`。`tmpfiles` 仅为 legacy compatibility，启用前需要单独任务说明和验证。

**Q: MinerU 解析超时？**
A: 当前主线优先检查本机 MinerU FastAPI、submit-probe、host/container endpoint 口径和 MinerU 日志；在线 MinerU 超时排查仅适用于 compatibility 路径。

**Q: 在线 MinerU 解析返回 401 "user authenticate failed"？**
A: 这是 MinerU 鉴权失败，检查以下配置：
   1. 系统设置页面的 MinerU API Key 是否正确
   2. API Key 是否带 `Bearer ` 前缀（不应该）
   3. API Key 是否含引号或空格（不应该）
   4. 可用 `curl` 直测验证 Key 有效性（见下方命令）

**Q: 如何验证在线 MinerU API Key 是否有效？**
A: 仅在 online compatibility 路径中需要。在宿主机运行以下命令（替换 `YOUR_KEY` 为真实 key）：
```bash
curl -i https://mineru.net/api/v4/file-urls/batch \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_KEY' \
  -d '{"enable_formula":true,"enable_table":true,"language":"ch","is_ocr":false,"model_version":"vlm","files":[{"name":"test.pdf","data_id":"test-1"}]}'
```
返回 `200` 则 key 有效，返回 `401` 则 key 无效或错误。

**Q: Overleaf 备份 API 返回 401/403？**
A: 通过 URL `?token=xxx` 重新注入 Token，或检查备份后端的 Token 配置。

**Q: Overleaf 备份 API 返回 503？**
A: 备份后端未启动，或 `docker/nginx.conf` 中的代理地址不正确。

**Q: Docker 构建失败（better-sqlite3 native 编译）？**
A: db-server 当前使用 JSON 文件存储，不依赖 better-sqlite3。项目已在 v0.6 版本中彻底移除了 `better-sqlite3` 依赖，如仍出现此错误，请执行 `docker compose build --no-cache` 清理构建缓存。

**Q: LaTeX 工具处理失败？**
A: LaTeX 工具完全在浏览器本地运行。如果失败，检查上传的 ZIP 文件是否包含 `.tex` 文件和 `images/` 目录。

---

## 十、Mac Mini 局域网部署指南

### 9.1 网络架构

```
局域网客户端 (192.168.31.x)
    ↓ http://192.168.31.33:8081
Mac Mini 宿主机 :8081 → Docker: cms-frontend (Nginx:80)
                            ├─ /cms/                → 前端静态文件
                            ├─ /__proxy/upload/     → upload-server:8788
                            ├─ /__proxy/db/         → db-server:8789
                            ├─ /minio/              → minio:9000
                            ├─ /__proxy/mineru-local → host MinerU :8083
                            └─ host Ollama           → :11434
```

> MinIO 控制台本地管理入口通常为：`http://127.0.0.1:19001`

### 9.2 部署步骤

```bash
# 1. 在 Mac Mini 宿主机上进入项目目录
cd /path/to/Luceon2026

# 2. 复制并配置环境变量
cp .env.example .env

# 3. 编辑 .env，至少修改以下关键项：
#   CMS_PORT=8081
#   MINIO_ACCESS_KEY=<强密码>
#   MINIO_SECRET_KEY=<强密码>
#   MINIO_PUBLIC_ENDPOINT=http://192.168.31.33:8081/minio
#
#   注意：MINIO_ENDPOINT 保持默认值 minio（Docker 内部 DNS）

# 4. 构建并启动全部服务
docker compose up -d --build

# 5. 验证部署
docker compose ps
curl http://localhost:8081/__proxy/upload/health
curl http://localhost:8081/__proxy/db/health
```

### 9.3 服务管理

```bash
# 查看日志
docker compose logs -f cms-frontend
docker compose logs -f upload-server

# 重启单个服务
docker compose restart upload-server

# 停止所有服务
docker compose down

# 停止并删除数据卷（⚠️ 数据不可恢复）
docker compose down -v
```

### 9.4 环境区分说明

| 运行环境 | `MINIO_ENDPOINT` | 说明 |
|---------|-----------------|------|
| Docker Compose 部署（生产/UAT） | `minio` | 容器间内部 DNS，**默认值** |
| 开发容器内直接 `node` 运行 | `192.168.31.33` | 需连接宿主机上已运行的 MinIO |
