---
name: minio-file-lineage
overview: 为系统增加完整的 MinIO 文件管理与溯源能力：原始文件上传存 MinIO、MinerU 解析产物存 MinIO、详情页展示完整"原始文件 → 解析产物 → AI 分析"溯源链路，并支持文件列表浏览、实时刷新预签名 URL 及预览/下载。
todos:
  - id: add-list-api
    content: 在 server/upload-server.mjs 末尾新增 GET /list 接口，调用 MinIO listObjectsV2 列出指定 prefix 下所有文件并返回预签名 URL 列表，MinIO 不可用时返回空数组兜底
    status: completed
  - id: add-lineage-card
    content: 在 AssetDetailPage.tsx 右侧栏新增"文件溯源"卡片组件，分三层展示原始文件（MinIO 路径+大小+刷新预签名 URL）、MinerU 解析产物文件列表（调用 /list 接口）、AI 分析摘要（时间+置信度）
    status: completed
    dependencies:
      - add-list-api
  - id: record-parsedat
    content: 在 AssetDetailPage.tsx 的 handleMineruParse 成功回调中，向 UPDATE_MATERIAL dispatch 追加 parsedAt 字段写入 metadata，完善溯源时间链路
    status: completed
    dependencies:
      - add-lineage-card
---

## 用户需求

### 产品概述

在现有 CMS 系统中，用户需要原始文件上传后由 MinIO 持久管理，MinerU 解析成功后的产出物（Markdown + 图片）也要存入 MinIO，并在资产详情页提供可视化的完整溯源链路展示（原始文件 → MinerU 解析产物 → AI 分析结果）。

### 核心功能

- **原始文件 MinIO 管理**：上传文件后写入 MinIO `originals/` 目录，记录 `objectName`，支持预签名 URL 按需刷新（过期后可重新获取）
- **MinerU 解析产物 MinIO 管理**：解析完成后 ZIP 解压，将 `full.md` + 图片全部存入 MinIO `parsed/{materialId}/` 目录，并列出产物文件清单
- **完整溯源卡片**：在资产详情页右侧栏新增"文件溯源"卡片，分三层可视化展示：
- 上传层：原始文件 MinIO 路径、大小、格式、存储后端标识、预签名 URL 刷新按钮
- 解析层：解析产物文件列表（来自 MinIO `parsed/{id}/`）、full.md 内容预览、解析时间
- 分析层：AI 分析时间、置信度、学科/年级等关键结果
- **解析产物文件列表**：通过新增后端接口列出 MinIO 指定 prefix 下的所有文件，前端展示文件名 + 大小 + 预览/下载链接
- **时间戳完善**：在 `parsedAt` 字段记录 MinerU 解析完成时间，写入 `material.metadata`

## 技术栈

沿用现有项目技术栈，不引入新依赖：

- **后端**：Node.js + Express（`upload-server.mjs`），MinIO JavaScript SDK（`minio` npm包，已安装）
- **前端**：React + TypeScript + Tailwind CSS，沿用现有组件风格（shadcn/ui 风格手写组件）
- **状态管理**：现有 `useReducer` + Context 模式

## 实现方案

### 整体思路

在现有架构上做最小化增量修改：后端增加 1 个 `/list` 接口，前端新增 1 个"文件溯源"卡片组件，在 MinerU 解析成功回调中补写 `parsedAt` 到 metadata。整个改动不影响现有上传/解析/AI分析流程。

### 关键设计决策

1. **`/list` 接口**：调用 MinIO SDK 的 `listObjectsV2(bucket, prefix, recursive=false)`，返回对象名、大小、最后修改时间，同时为每个对象生成预签名 URL（复用 `getPresignedExpiry()`），前端一次性拿到文件列表+可访问 URL，无需二次请求
2. **预签名 URL 刷新**：溯源卡片挂载时，如果 `objectName` 存在，调用已有的 `/__proxy/upload/presign?objectName=xxx` 刷新原始文件 URL；`/list` 接口本身返回的产物 URL 也是实时生成的
3. **溯源卡片懒加载**：仅在卡片展开/首次渲染时请求 `/list`，避免每次打开详情页都触发 MinIO 列举操作
4. **`parsedAt` 写入时机**：在 `AssetDetailPage.tsx` 的 `handleMineruParse` 中，`/parse/download` 成功后，将 `parsedAt: new Date().toISOString()` 写入 `UPDATE_MATERIAL` dispatch，不需要修改 reducer

### 性能考量

- `/list` 接口单次列举 `parsed/{id}/` 前缀，对象数量通常 < 50，耗时 < 200ms，无需缓存
- 前端溯源卡片用 `useEffect` + `useState` 管理加载状态，防止重复请求（用 `useRef` 标记是否已拉取）

## 架构设计

```mermaid
graph TD
    A[AssetDetailPage 详情页] --> B[文件溯源卡片 FileLineageCard]
    B --> C1[上传层: 原始文件信息]
    B --> C2[解析层: MinerU 产物列表]
    B --> C3[分析层: AI 分析摘要]
    C1 --> D1[/__proxy/upload/presign - 刷新原始文件URL]
    C2 --> D2[/__proxy/upload/list?prefix=parsed/id - 列举产物文件]
    D2 --> E[upload-server /list 接口]
    E --> F[(MinIO: parsed/id/*)]
```

## 目录结构

```
server/
  upload-server.mjs       # [MODIFY] 新增 GET /list 接口，列出 MinIO 指定 prefix 下的文件

src/
  app/
    pages/
      AssetDetailPage.tsx # [MODIFY] 新增文件溯源卡片；handleMineruParse 成功后写入 parsedAt
```

## 关键接口

### 新增后端接口：`GET /list`

```
Query: ?prefix=parsed/123
Response: {
  objects: [
    { objectName: string, name: string, size: number, lastModified: string, presignedUrl: string }
  ],
  total: number
}
```

### 前端卡片数据结构（组件内部 state）

```ts
interface MinioObject {
  objectName: string;
  name: string;        // 去掉 prefix 后的短文件名
  size: number;
  lastModified: string;
  presignedUrl: string;
}
interface LineageState {
  loading: boolean;
  originalUrl: string | null;  // 刷新后的原始文件预签名 URL
  parsedFiles: MinioObject[];  // parsed/ 目录下的文件列表
}
```

## 实现细节说明

- `upload-server.mjs` 中 `/list` 接口：使用 `client.listObjectsV2(bucket, prefix, true)` 流式读取，收集到数组后统一返回；MinIO 不可用时返回空列表而不是 500 错误（防止溯源卡片崩溃）
- `AssetDetailPage.tsx` 中溯源卡片：复用已有 `lucide-react` 图标（`Database`、`FileText`、`ExternalLink`、`RefreshCw`）；样式沿用已有 `bg-white rounded-xl border border-gray-200 p-5` 模式
- `parsedAt` 写入：在现有 `UPDATE_MATERIAL` dispatch 中追加 `parsedAt` 字段，不需要新增 action type，reducer 已支持 metadata 深度合并
- 原始文件预签名 URL 刷新：溯源卡片 mount 时，若 `material.metadata.objectName` 存在则调用 `/presign`，结果存 state，展示"预览"/"下载"按钮