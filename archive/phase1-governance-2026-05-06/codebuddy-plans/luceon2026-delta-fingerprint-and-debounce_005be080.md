---
name: luceon2026-delta-fingerprint-and-debounce
overview: 合并执行两批优化：①为 processTasks/tasks/products/flexibleTags/aiRules 加入差量指纹检测；②writeDB() 添加 100ms debounce；③补全 MaterialMetadata 类型并消除断言；④修复重置配置按钮遗漏 minio_config；⑤修正 3 处过时注释。
todos:
  - id: types-interface
    content: 在 types.ts 新增 MaterialMetadata 接口，修改 Material.metadata 类型，修复 AppAction 注释（D项）
    status: completed
  - id: asset-detail-cleanup
    content: 在 AssetDetailPage.tsx 移除全部 as string 断言，补充必要的 || '—' 兜底
    status: completed
    dependencies:
      - types-interface
  - id: reset-config-fix
    content: 在 SourceMaterialsPage.tsx handleResetConfig 补全 app_minio_config 和 app_ai_rule_settings 的清除
    status: completed
  - id: frontend-fingerprints
    content: 在 appContext.tsx 新增5个指纹 useRef，修改5个 useEffect 改为差量指纹写入
    status: completed
  - id: backend-debounce
    content: 在 db-server.mjs 将 writeDB() 改为 100ms debounce，简化各路由 handler
    status: completed
  - id: comment-fixes
    content: 修复 server/Dockerfile 和 vite.config.ts 的过期注释（C项、E项）
    status: completed
  - id: commit-push
    content: 使用 [mcp:GitHub MCP Server] push_files 原子提交全部7个文件变更到 main 分支
    status: completed
    dependencies:
      - types-interface
      - asset-detail-cleanup
      - reset-config-fix
      - frontend-fingerprints
      - backend-debounce
      - comment-fixes
---

## 用户需求

将两批独立任务合并为一个完整执行计划，涵盖性能优化和代码质量修订共 7 项改动，涉及 7 个文件。

## 产品概述

EduAsset CMS（Luceon2026）第三轮综合修订：消除批量操作下的冗余网络请求与磁盘写入，同时修复类型安全缺陷、配置重置遗漏，并更新若干过期注释。

## 核心功能

### 批次1：性能优化

- **差量指纹检测**：为 `processTasks`、`tasks`、`products`、`flexibleTags`、`aiRules` 五个集合各加一个 `useRef<Map<number,string>>` 指纹缓存，仅对内容变化的记录发送 POST 请求（与已有的 materials/assetDetails 方案保持一致）
- **writeDB debounce**：`db-server.mjs` 的 `writeDB()` 改为 100ms 防抖落盘，`dbCache` 仍实时更新，各路由 handler 简化（移除包裹 writeDB 的 try/catch，直接 `res.json({ ok: true })`）

### 批次2：代码质量修订

- **A（P1）**：`types.ts` 新增 `MaterialMetadata` 接口（21 个具名可选字段 + 索引签名），`AssetDetailPage.tsx` 移除约 20 处 `as string` 断言
- **B（P1）**：`SourceMaterialsPage.tsx` 重置配置函数补全 `app_minio_config` 和 `app_ai_rule_settings` 的清除
- **C/D/E（P3）**：`server/Dockerfile`、`types.ts`、`vite.config.ts` 三处过期注释更新

## 技术栈

- 前端：TypeScript + React（useRef / useEffect），与现有代码完全一致
- 后端：Node.js ESM（setTimeout / clearTimeout），无新依赖
- 工具链：pnpm + tsc（lint 验证）
- 提交：使用 [mcp:GitHub MCP Server] push_files 工具原子提交所有变更

## 实现方案

### 差量指纹（appContext.tsx）

严格复用 materials 的现有模式（第 314-321 行）：在第 298-299 行的指纹 Ref 声明块后新增 5 个 Ref，然后将第 347-420 行的 5 个 useEffect 中的全量 `dbPost` 循环替换为指纹差量循环。`tasks` 的 `id` 字段类型为 `string`（`Task` 接口第 87 行），Map 键类型需对应调整为 `Map<string, string>`。

### writeDB debounce（db-server.mjs）

模块顶层声明 `let writeTimer = null`，替换第 73-79 行的 `writeDB()` 函数体为 100ms debounce 实现。各路由 handler 原有的 `try/catch` 包裹 `writeDB()` 调用的目的是捕获同步写磁盘异常；debounce 后 writeDB 不再同步抛出，因此 handler 可简化：移除 `try/catch`，`dbCache` 赋值后直接 `res.json({ ok: true })`。磁盘错误在 setTimeout 回调内通过 `console.error` 记录。

### MaterialMetadata 接口（types.ts）

在第 51 行之前新增 `MaterialMetadata` 接口，包含 21 个具名可选字段（均为 `string | undefined`）及索引签名 `[key: string]: string | undefined`（保留动态 key 访问兼容性）。`Material.metadata` 类型由 `Record<string, string>` 改为 `MaterialMetadata`。同时修复第 265 行 AppAction 注释（SQLite → db-server）。

### AssetDetailPage.tsx 断言清理

`MaterialMetadata` 所有字段推断类型已为 `string | undefined`，直接删除各处 `as string | undefined` 和 `as string` 断言即可，TypeScript 自动推断，无需额外处理。

## 实现注意事项

- `tasks` 集合的 `id` 为 `string` 类型（`Task` 接口），指纹 Ref 声明为 `Map<string, string>` 而非 `Map<number, string>`
- debounce 后 writeDB 内部错误不向请求方返回 500，这在 fire-and-forget 写入模式下可接受；`bulk-restore` 路由数据量大，同样适用 debounce
- 移除 `as string` 断言后，若存在 `metadata.format as string` 直接嵌入 JSX（无 `| undefined`），移除断言后 TypeScript 会推断为 `string | undefined`，需确保 JSX 消费处有 `|| '—'` 或可选链兜底（AssetDetailPage 中已有此模式，核查后按需补充）
- 修改仅限 7 个文件，不触碰任何其他逻辑

## 目录结构

```
src/store/types.ts                    [MODIFY] 新增 MaterialMetadata 接口（21字段+索引签名）；修改 Material.metadata 类型；修复 AppAction 注释（D项）
src/app/pages/AssetDetailPage.tsx     [MODIFY] 移除约20处 as string / as string | undefined 断言；JSX 中直接访问的字段按需补充 || '—' 兜底
src/app/pages/SourceMaterialsPage.tsx [MODIFY] handleResetConfig 补全 app_minio_config 和 app_ai_rule_settings 的 removeItem
src/store/appContext.tsx              [MODIFY] 新增5个指纹 useRef；修改5个 useEffect 改为差量指纹循环
server/db-server.mjs                  [MODIFY] 顶层添加 writeTimer；writeDB() 改为 debounce 落盘；各路由 handler 移除 try/catch，简化为 res.json({ ok: true })
server/Dockerfile                     [MODIFY] 第6行注释：SQLite REST API → JSON 文件持久化 REST API（C项）
vite.config.ts                        [MODIFY] headers 块前添加注释说明仅开发环境有效（E项）
```

## Agent Extensions

### MCP

- **GitHub MCP Server**
- Purpose: 使用 push_files 工具将 7 个文件的变更原子性地推送到 main 分支，完成最终提交
- Expected outcome: 单次 commit 包含所有修改，提交信息清晰描述两批任务内容，远端 main 分支更新成功