---
name: metadata-minio-enhancement
overview: 扩展元数据字段（9个标准化字段）、AI识别结果直接填入可编辑下拉框、pages从上传文件中计算、MinIO配置持久化到db-server的settings表并增加配置页面和测试连接功能。
todos:
  - id: types-store-update
    content: 扩展 types.ts 新增 MinioConfig/language/country/UPDATE_MINIO_CONFIG，更新 appReducer.ts 和 appContext.tsx 初始化及 bulk-restore
    status: completed
  - id: upload-server-enhance
    content: 改造 upload-server.mjs：引入 pdf-lib 计算 PDF 页数，/upload 响应增加 pages/format，新增 MinIO 配置动态管理接口（GET/PUT /settings/storage、POST /settings/storage/test）
    status: completed
  - id: asset-detail-metadata-form
    content: 重构 AssetDetailPage.tsx AI 元数据面板为可编辑表单：9个字段下拉框/输入框，AI 分析结果自动填充，新增"保存元数据"按钮
    status: completed
    dependencies:
      - types-store-update
      - upload-server-enhance
  - id: settings-minio-tab
    content: 在 SettingsPage.tsx 新增"存储配置" Tab，实现 MinIO 配置表单、测试连接、保存并持久化到 db-server
    status: completed
    dependencies:
      - types-store-update
      - upload-server-enhance
---

## 用户需求

### 产品概述

对 EduAsset CMS 的资料管理流程进行三个方向的优化，提升元数据质量和存储配置的可管理性。

### 核心功能

**1. 元数据字段标准化（9个字段）**

- 语言（中文/英文/双语/其他）、年级（G1-G12）、科目（语文/英语/数学等12项）、国家（中国/英国/美国/新加坡等7项）、格式（从文件扩展名自动填入，无需AI）、size（上传时从文件自动获取）、pages（上传PDF时用pdf-lib计算页数，图片=1，其他=空）、summary（AI生成）、type（课本/讲义/练习册/试卷等9项）
- AI提示词扩展：在现有 subject/grade/materialType/summary 基础上增加 language/country 的识别提示词

**2. 元数据可编辑表单**

- AssetDetailPage 的 AI 元数据分析面板改为：AI分析完成后结果直接填入对应下拉框/输入框
- 枚举字段（语言/年级/科目/国家/类型）使用 `<select>` 下拉，summary 使用 `<textarea>`，pages 使用只读文本（上传时计算）
- 用户随时可修改任意字段，修改后点击"保存元数据"按钮 dispatch UPDATE_MATERIAL 持久化
- 右侧原"元数据"卡片展示已保存的完整元数据（format/size/pages等上传自动填入的字段也显示）

**3. MinIO 存储配置页面**

- SettingsPage 新增第三个 Tab "存储配置"
- 表单项：存储后端切换（minio/tmpfiles）、MinIO 端点、端口、Access Key（密码框可显隐）、Secret Key（密码框）、Bucket 名称、Presigned URL 有效期
- "测试连接"按钮：调用 upload-server 新接口，实时显示连通成功/失败原因
- "保存配置"：写入 db-server settings 表持久化，同时通知 upload-server 更新运行时配置
- 页面加载时从 db-server 读取已保存配置回填表单

## 技术栈

基于现有项目栈：React 18 + TypeScript + Tailwind CSS + Vite，服务端 Node.js + Express（ESM），db-server JSON文件持久化，upload-server 处理文件上传与MinIO交互。

---

## 实现思路

### 总体策略

分三条并行改动链路，各自独立，互不阻塞：

1. **上传增强链路**：upload-server 的 `/upload` 接口在接收文件后，利用 `pdf-lib` 解析 PDF 页数，将 `pages/format/size` 随上传响应返回给前端，前端写入 `material.metadata`
2. **AI 分析增强链路**：扩展 prompt 增加 language/country 识别，前端改为可编辑表单，AI结果填入后用户可随时修改保存
3. **MinIO 配置链路**：db-server 已有 settings 接口，upload-server 新增3个配置接口（读/写/测试），前端 SettingsPage 新增第三 Tab

### pages 计算方案

在 upload-server 中使用 `pdf-lib`（纯 JS，无原生依赖，已支持 ESM）：

```js
import { PDFDocument } from 'pdf-lib';
const pdf = await PDFDocument.load(buffer, { ignoreEncryption: true });
pages = pdf.getPageCount();
```

图片文件（image/*）= 1页，其他文件 = null（不填 pages 字段）。

### MinIO 配置动态更新

upload-server 将 MinIO 配置抽象为可变对象（`let minioState = {}`），`/settings/storage/test` 和 `PUT /settings/storage` 接口用传入参数创建临时 Client 验证，`PUT` 成功后更新运行时 minioClient 和 STORAGE_BACKEND 变量，同时转发 `PUT /__proxy/db/settings/minioConfig` 写入持久化。前端保存时直接调用 `PUT /__proxy/upload/settings/storage`，由 upload-server 负责双写。

### 性能与可靠性

- pdf-lib 解析仅在 PDF 文件时触发，在 multer buffer 基础上同步操作，不增加额外 I/O
- MinIO 连接测试超时设为 5s（`bucketExists` 调用），避免长时间阻塞
- 前端元数据表单变更只在点击"保存"时 dispatch，不做频繁更新

---

## 实现细节

### 关键注意事项

1. `pdf-lib` 需在 `server/` 目录 package 中安装（检查 pnpm-workspace 结构）；若 server 无独立 package.json，则在根 package.json 添加依赖
2. upload-server 的 MinIO Client 初始化由静态改为动态：启动时从环境变量初始化，运行时接口可覆盖；所有使用 `minioClient` / `MINIO_BUCKET` 的地方改为函数调用 `getMinioClient()` / `getMinioBucket()`
3. `AiPromptConfig` 扩展 language/country 字段，`AppAction` 扩展 `UPDATE_MINIO_CONFIG`；`AppState` 新增 `minioConfig: MinioConfig`
4. `appContext.tsx` 的 bulk-restore 调用需同步加入 minioConfig 字段
5. 前端 SettingsPage 的 MinIO Tab 初始化时调用 `GET /__proxy/upload/settings/storage` 读取当前配置，密钥返回脱敏（`***`）；保存时若密钥字段为 `***` 则不传该字段（保留服务端现有值）
6. vite.config.ts 的 proxy 已覆盖 `/__proxy/upload/` 和 `/__proxy/db/`，无需新增

---

## 架构设计

```mermaid
flowchart TD
    subgraph 前端
        A[文件上传\nSourceMaterialsPage] -->|multipart/file| B[POST /__proxy/upload/upload]
        C[AssetDetailPage\nAI元数据面板] -->|下拉框+textarea| D[可编辑元数据表单]
        D -->|保存| E[dispatch UPDATE_MATERIAL\n→ db-server]
        F[SettingsPage\n存储配置Tab] -->|GET| G[/__proxy/upload/settings/storage]
        F -->|PUT| H[/__proxy/upload/settings/storage]
        F -->|POST| I[/__proxy/upload/settings/storage/test]
    end

    subgraph upload-server
        B -->|pdf-lib计算pages| J[返回 pages/format/size]
        H --> K[更新运行时minioClient]
        K --> L[PUT /__proxy/db/settings/minioConfig]
        I --> M[临时Client测试bucketExists]
    end

    subgraph db-server
        L --> N[settings.minioConfig 持久化]
        E --> O[materials记录更新]
    end

    style D fill:#93c5fd,color:#000
    style F fill:#4ade80,color:#000
    style K fill:#fbbf24,color:#000
```

---

## 目录结构

```
project-root/
├── server/
│   └── upload-server.mjs          # [MODIFY] 1)引入pdf-lib计算pages; 2)POST /upload响应增加pages/format; 3)新增GET/PUT /settings/storage和POST /settings/storage/test; 4)MinIO客户端改为动态可更新
├── src/
│   ├── store/
│   │   ├── types.ts               # [MODIFY] AiPromptConfig加language/country; 新增MinioConfig接口; AppState加minioConfig; AppAction加UPDATE_MINIO_CONFIG
│   │   ├── appReducer.ts          # [MODIFY] 新增UPDATE_MINIO_CONFIG case处理
│   │   └── appContext.tsx         # [MODIFY] 初始化minioConfig默认值; bulk-restore加minioConfig; 启动时从db读取minioConfig
│   └── app/
│       └── pages/
│           ├── AssetDetailPage.tsx # [MODIFY] 1)AI分析面板结果区改为可编辑表单(select+textarea); 2)新增"保存元数据"按钮; 3)右侧元数据卡片展示完整9字段; 4)handleAiAnalyze写入新字段language/country
│           └── SettingsPage.tsx    # [MODIFY] 新增第三Tab"存储配置"; MinIO配置表单; 测试连接; 保存配置; 页面加载时回填
└── package.json                   # [MODIFY] 若server无独立package.json则在根添加pdf-lib依赖
```