---
name: luceon2026-r4-cascade-delete
overview: 第四轮修订：5 项改动，实现全链路级联删除（MinIO 清理 + processTasks 孤儿清除 + 确认框分级提示）、修复标签双写缺口、补齐后端 DELETE 路由、补全 tasks 删除同步逻辑、清理全局 SQLite 过期注释，共涉及 5 个文件。
todos:
  - id: backend-routes
    content: 在 db-server.mjs 补充 DELETE /process-tasks 和 DELETE /tasks 路由（修订项3）；在 upload-server.mjs 新增 listAllObjects 辅助函数 + POST /delete-material 接口（修订项1a）
    status: completed
  - id: reducer-cascade
    content: 在 appReducer.ts DELETE_MATERIAL case 追加 processTasks 级联清理，修复 L20 SQLite 注释（修订项1b + 修订项5局部）
    status: completed
  - id: context-sync
    content: 在 appContext.tsx 新增 prevTaskIds useRef；materials useEffect 追加 MinIO fire-and-forget 清理；tasks useEffect 补充删除同步逻辑；全局替换所有 SQLite 注释（修订项1c + 修订项4 + 修订项5）
    status: completed
    dependencies:
      - backend-routes
      - reducer-cascade
  - id: ui-delete-confirm
    content: 在 SourceMaterialsPage.tsx 改造 handleDelete/handleBatchDelete/handleClearAll 为分级确认提示，修复 SQLite 注释（修订项1d + 修订项5局部）
    status: completed
    dependencies:
      - reducer-cascade
  - id: tags-dual-write
    content: 在 AssetDetailPage.tsx handleSaveTags 追加 UPDATE_MATERIAL_TAGS dispatch（修订项2）
    status: completed
  - id: commit-push
    content: 使用 [mcp:GitHub MCP Server] push_files 分批推送全部5个文件变更到 main 分支，验证每次 push 返回有效 SHA
    status: completed
    dependencies:
      - backend-routes
      - reducer-cascade
      - context-sync
      - ui-delete-confirm
      - tags-dual-write
---

## 用户需求

Luceon2026 第四轮修订，基线 Commit a575adb2，5 项修订（P1×2、P2×2、P3×1）。

## 产品概述

EduAsset CMS 第四轮综合修订：核心目标是实现全链路级联删除（MinIO 存储清理 + processTasks 孤儿清除 + 分级确认提示），同时修补标签双写缺口、补齐缺失的后端 DELETE 路由、完善 tasks 集合的删除同步、以及清理全局过期注释。

## 核心功能

### 修订项 1（P1）：全链路级联删除

- **1a**：`server/upload-server.mjs` 新增 `POST /delete-material` 接口，接收 `materialIds` 数组，遍历删除两个 MinIO 桶（`originals/{id}/` + `parsed/{id}/`）中的所有对象；MinIO 不可用时跳过；每个 materialId 独立 try/catch；返回每 ID 的删除计数和错误信息
- **1b**：`src/store/appReducer.ts` `DELETE_MATERIAL` case 追加 `processTasks` 级联过滤（守卫 `t.materialId === undefined` 保护无关联任务）
- **1c**：`src/store/appContext.tsx` materials `useEffect` 中，`dbDelete` 之后追加 fire-and-forget `fetch POST /__proxy/upload/delete-material`（30s 超时，catch 仅 console.warn）
- **1d**：`src/app/pages/SourceMaterialsPage.tsx` 改造 `handleDelete`/`handleBatchDelete`/`handleClearAll`，根据资料处理深度（objectName/mineruStatus/aiStatus/关联任务数）展示分级确认提示

### 修订项 2（P1）：handleSaveTags 标签双写同步

`src/app/pages/AssetDetailPage.tsx` `handleSaveTags` 追加 `dispatch({ type: 'UPDATE_MATERIAL_TAGS', ... })`，确保资料库列表页标签实时更新

### 修订项 3（P2）：补齐后端 DELETE 路由

`server/db-server.mjs` 在 process-tasks 区块和 tasks 区块各添加一条 `DELETE` 路由，消除前端已发出但后端404的请求

### 修订项 4（P2）：tasks 集合删除同步

`src/store/appContext.tsx` 补充 `prevTaskIds useRef<Set<string>>` 声明，并在 tasks `useEffect` 中添加删除检测 + `dbDelete('/tasks', ...)` 调用，与其他集合保持一致

### 修订项 5（P3）：清理 SQLite 过期注释

全局替换 3 个文件中共 13 处"SQLite"相关注释，统一描述为 db-server/JSON 文件持久化架构

## 技术栈

- 后端：Node.js ESM（upload-server.mjs / db-server.mjs），minio JS SDK（listObjectsV2 + removeObject）
- 前端：TypeScript + React（useRef / useEffect / useReducer），与现有代码完全一致
- 工具链：pnpm + tsc，无新依赖
- 提交：使用 [mcp:GitHub MCP Server] push_files 分批推送变更

## 实现方案

### 修订项 1a：POST /delete-material 接口

新增 `listAllObjects(bucket, prefix)` 辅助函数（Promise 包装 listObjectsV2 流），然后新增路由：

- 检测 `getStorageBackend() !== 'minio'`，非 MinIO 时直接返回 `{ ok: true, skipped: true }`
- 遍历每个 materialId，并行清理两桶；单 ID 失败不影响其他 ID
- 返回 `{ ok: true, results: [{id, originals, parsed}], errors: [] }`

### 修订项 1b：reducer 级联清理

在 DELETE_MATERIAL return 语句中追加：

```typescript
processTasks: state.processTasks.filter(
  (t) => t.materialId === undefined || !idSet.has(t.materialId),
),
```

### 修订项 1c：appContext MinIO 清理触发

materials useEffect 中，紧跟 `dbDelete('/materials', { ids: deletedIds })` 之后追加 fire-and-forget fetch，不 await，catch 仅打印 console.warn。

### 修订项 1d：分级确认提示

复用现有的 `confirmDelete` 工具（SourceMaterialsPage 已使用），根据 `material.metadata?.objectName`、`material.mineruStatus`、`material.aiStatus`、关联 processTasks 数量动态拼接 confirm 消息字符串。

### 修订项 2：方案 A，改动最小

handleSaveTags 中追加一行 dispatch，复用已有的 UPDATE_MATERIAL_TAGS（L148-160），该 action 本身已包含 assetDetails 联动，无需改 reducer。

### 修订项 3：参考现有 DELETE /products（L236-244）模式

完全相同的结构，仅切换操作的 `dbCache` 子集。

### 修订项 4：与 prevProcessIds 模式完全对齐

在 L292 的 useRef 块末尾追加 `prevTaskIds`（Set<string>），tasks useEffect 仿照 processTasks useEffect 的结构。

### 修订项 5：精确搜索替换

按规则替换，不触碰任何逻辑代码，仅修改注释字符串。

## 实现注意事项

- `listObjectsV2` 的第三个参数 `recursive: true` 必须设置，否则只列出顶层虚拟目录，无法列出子对象
- `prevTaskIds` 类型为 `Set<string>`（Task.id 是 string），与 prevProcessIds 的 `Set<number>` 不同，需注意
- MinIO 清理是 fire-and-forget，前端删除已通过 localStorage 完成，MinIO 失败不应阻塞 UI 或报错弹框
- 分级提示的 `\n` 在 `window.confirm` 中可直接换行显示（native dialog）
- db-server.mjs 中 `DELETE /process-tasks` 的 id 类型为 number，`DELETE /tasks` 的 id 类型为 string；`delete dbCache.tasks[id]` 在对象键值操作中自动 toString，无类型问题

## 目录结构

```
server/
├── upload-server.mjs    [MODIFY] 末尾新增 listAllObjects 辅助函数 + POST /delete-material 路由区块
└── db-server.mjs        [MODIFY] process-tasks 区块末尾添加 DELETE /process-tasks；tasks 区块末尾添加 DELETE /tasks

src/store/
├── appReducer.ts        [MODIFY] DELETE_MATERIAL case（L47-56）追加 processTasks 级联过滤；修复 L20 SQLite 注释
└── appContext.tsx        [MODIFY] 新增 prevTaskIds useRef（L292 附近）；materials useEffect 追加 MinIO 清理 fetch（L316 之后）；tasks useEffect 补充删除同步逻辑（L371-382）；全局替换约 12 处 SQLite 注释

src/app/pages/
├── AssetDetailPage.tsx       [MODIFY] handleSaveTags（L679-683）追加 UPDATE_MATERIAL_TAGS dispatch
└── SourceMaterialsPage.tsx   [MODIFY] 改造 handleDelete/handleBatchDelete/handleClearAll 为分级确认提示；修复 L255 SQLite 注释
```

## Agent Extensions

### MCP

- **GitHub MCP Server**
- Purpose: 使用 push_files 工具将所有文件变更原子性推送到 main 分支
- Expected outcome: 单次或分批 commit 包含全部修订，远端 main 分支更新成功，每次 push 均有 SHA 确认