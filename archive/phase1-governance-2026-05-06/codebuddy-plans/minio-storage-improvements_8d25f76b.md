---
name: minio-storage-improvements
overview: 三项 MinIO 存储改进：originals/ 路径加入 materialId 目录层（提升文件溯源能力）、/parse/download 增加 full.json 存储、前端上传时将 materialId 传给 upload-server。
todos:
  - id: server-path-and-json
    content: 修改 upload-server.mjs：originals 路径增加 materialId 分层 + /parse/download 增加 .json 存储
    status: completed
  - id: frontend-materialid
    content: 修改 SourceMaterialsPage.tsx：上传时 formData 附带 materialId；AssetDetailPage.tsx 文件列表增加 .json 图标区分
    status: completed
    dependencies:
      - server-path-and-json
---

## 用户需求

对 MinIO 存储的文件组织方式进行两项改进，提升文件可追踪性和数据完整性：

## 核心功能

### 1. 原始文件路径增加 materialId 分层（溯源追踪）

- 上传原始文件时，MinIO 中的存储路径从 `originals/{timestamp}-name.pdf` 改为 `originals/{materialId}/{timestamp}-name.pdf`
- 前端在发送 `/upload` 请求时附带 `materialId`，服务端用其构造分层目录
- 向后兼容：若未传 `materialId`，路径退化为原来的 `originals/` 扁平结构
- 新路径格式使得直接在 MinIO 控制台浏览时也能按资料归属识别文件，无需查数据库

### 2. MinerU 解析产物存储 full.json（数据完整性）

- `/parse/download` 当前只存储 `.md` 和图片文件，将 `.json` 文件也纳入存储范围
- 保留 MinerU 输出的 `full.json`（含段落/标题/公式坐标等结构化信息），供后续精细加工管道使用
- 前端文件溯源卡片的文件列表展示也随之增加对 `.json` 文件的图标区分显示

## 技术栈

- 服务端：Node.js + Express (ESM，`upload-server.mjs`)
- 前端：React + TypeScript
- 存储：MinIO SDK (`minio` npm 包)

## 实现思路

### 改动 1：原始文件路径分层

**服务端（`server/upload-server.mjs`）**

`uploadBufferToMinIO` 函数增加可选的 `materialId` 参数，当传入时路径变为 `originals/{materialId}/{timestamp}-{safeFileName}`，否则保持 `originals/{timestamp}-{safeFileName}`（向后兼容）。

`POST /upload` 路由从 `req.body.materialId` 或 `req.query.materialId` 读取该参数，传入 `uploadBufferToMinIO`。

由于 `/upload` 用的是 `multer`（multipart），`materialId` 需要作为 formData 字段（`req.body.materialId`）传入。multer 解析 multipart 时 body 字段需在 `upload.single('file')` 处理后才可读，这是已有的中间件顺序，无需变更。

**前端（`src/app/pages/SourceMaterialsPage.tsx`）**

在 `formData.append('file', file)` 之后追加 `formData.append('materialId', String(newId))`，`newId` 在第 119 行已经生成，无需调整生成时序。

### 改动 2：存储 full.json

**服务端（`server/upload-server.mjs`）**

`/parse/download` 中的过滤条件扩展：将 `if (!isMd && !isImage) continue;` 改为同时放行 `.json` 文件。对 `.json` 赋予 `application/json` MIME 类型，其余存储逻辑与图片完全一致（putObject → presignedGetObject → push uploadedFiles）。不修改 `markdownObjectName` / `markdownUrl` 的赋值逻辑，AI 分析管道不受影响。

**前端溯源卡片（`src/app/pages/AssetDetailPage.tsx`）**

文件列表渲染时已按文件扩展名给 `.md` 文件设置橙色图标（`f.name.endsWith('.md')`），扩展逻辑为 `.json` 文件添加绿色图标区分，使控制台显示更直观。

## 实现细节

- `materialId` 为可选参数，以 String 形式传递和接收，服务端用 `String(materialId).replace(/[^a-zA-Z0-9_-]/g, '')` 做基本净化，防止路径注入
- 不需要迁移已有数据：存量记录的 `metadata.objectName` 格式不变，只有新上传文件使用新路径
- `full.json` 存入 `parsed/{materialId}/full.json`，与 `full.md` 并列，不影响现有 `markdownObjectName` 的引用
- tmpfiles 降级分支不受影响（tmpfiles 路径无法加目录层级，维持原样）

## 目录结构

```
server/
  upload-server.mjs    [MODIFY] 两处改动：路径分层逻辑 + json 存储过滤
src/app/pages/
  SourceMaterialsPage.tsx  [MODIFY] formData 追加 materialId 字段
  AssetDetailPage.tsx      [MODIFY] 文件列表 json 图标区分（小幅 UI 优化）
```