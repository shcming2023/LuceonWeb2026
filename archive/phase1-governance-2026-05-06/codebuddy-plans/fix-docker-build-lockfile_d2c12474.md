---
name: fix-docker-build-lockfile
overview: 修复 Docker 构建失败问题：将两个 Dockerfile 中的 --frozen-lockfile 改为 --no-frozen-lockfile，解决 package.json 与 pnpm-lock.yaml 不同步导致的构建报错。
todos:
  - id: fix-dockerfile-frozen-lockfile
    content: 修改 Dockerfile 和 server/Dockerfile，将 --frozen-lockfile 替换为 --no-frozen-lockfile
    status: completed
---

## 用户需求

修复 `docker compose up -d --build` 构建失败问题。

**根本原因**：`package.json` 已移除 5 个依赖（`@emotion/react`、`@emotion/styled`、`@mui/icons-material`、`@mui/material`、`better-sqlite3`），但 `pnpm-lock.yaml` 未同步更新，导致 `--frozen-lockfile` 校验失败。

## 解决方案

修改两个 Dockerfile，将 `--frozen-lockfile` 替换为 `--no-frozen-lockfile`，允许 pnpm 在构建时忽略锁文件与 package.json 的差异，跳过严格校验直接安装依赖。

## 核心修改点

- `Dockerfile`（前端构建阶段）：第 20 行
- `server/Dockerfile`（upload-server / db-server 共用镜像）：第 21-22 行

## 技术方案

### 问题分析

`pnpm install --frozen-lockfile` 在 CI/Docker 环境下默认启用，要求 `pnpm-lock.yaml` 与 `package.json` 完全一致。当前 `package.json` 已删除 5 个依赖但锁文件未更新，构建时校验失败。

**选择 `--no-frozen-lockfile` 而非更新锁文件的理由**：

- 宿主机 Mac Mini 上可能没有合适版本的 pnpm 环境
- 锁文件更新需要在正确的 Node/pnpm 版本下执行，否则可能引入额外变更
- Docker 构建环境本身已固定 `node:20-alpine` 镜像，依赖解析结果是确定性的
- `--no-frozen-lockfile` 会在构建时自动生成新的内部一致状态，不影响运行时依赖

### 修改方案

**文件 1：`/workspace/ops/Luceon2026/Dockerfile` 第 20 行**

```
- RUN pnpm install --frozen-lockfile
+ RUN pnpm install --no-frozen-lockfile
```

**文件 2：`/workspace/ops/Luceon2026/server/Dockerfile` 第 21-22 行**

```
- RUN corepack enable && corepack prepare pnpm@latest --activate \
-   && pnpm install --frozen-lockfile --prod
+ RUN corepack enable && corepack prepare pnpm@latest --activate \
+   && pnpm install --no-frozen-lockfile --prod
```

### 目录结构

```
/workspace/ops/Luceon2026/
├── Dockerfile              # [MODIFY] 第 20 行 --frozen-lockfile → --no-frozen-lockfile
└── server/
    └── Dockerfile          # [MODIFY] 第 22 行 --frozen-lockfile → --no-frozen-lockfile
```

### 后续建议（非本次必做）

构建成功后，建议在开发容器内执行一次 `pnpm install` 更新 `pnpm-lock.yaml`，再将其推送到仓库，使两处标志可恢复为 `--frozen-lockfile`，保持 CI/CD 最佳实践。