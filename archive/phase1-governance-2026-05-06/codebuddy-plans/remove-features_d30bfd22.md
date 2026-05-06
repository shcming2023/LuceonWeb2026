---
name: remove-features
overview: 删除"Overleaf 备份"分组下的"项目备份"、"灾备备份"、"文件浏览"、"定时调度"四个功能，只保留"LaTeX 工具"。涉及 App.tsx 路由、Layout.tsx 导航、四个页面组件文件及 backupApi.ts 工具文件的清理。
todos:
  - id: delete-files
    content: 删除 ProjectBackupPage.tsx、DatabaseBackupPage.tsx、FilesBrowserPage.tsx、SchedulerPage.tsx 及 backupApi.ts 共5个文件
    status: completed
  - id: clean-app-tsx
    content: 修改 App.tsx：删除4个页面的 import 和对应 Route 声明
    status: completed
    dependencies:
      - delete-files
  - id: clean-layout-tsx
    content: 修改 Layout.tsx：精简 NAV_GROUPS 只保留 LaTeX 工具，删除无用 icon 导入和 token 同步逻辑
    status: completed
    dependencies:
      - delete-files
  - id: sync-github
    content: 提交所有变更并使用 [mcp:GitHub MCP Server] push 同步到远程仓库
    status: completed
    dependencies:
      - clean-app-tsx
      - clean-layout-tsx
---

## 用户需求

在 Overleaf 备份子系统中，删除"项目备份"、"灾备备份"、"文件浏览"、"定时调度"四个功能模块，仅保留"LaTeX 工具"页面。

## 产品概述

对现有项目进行精简，移除四个备份相关功能页面及其所有关联代码（路由、导航菜单、工具函数、页面文件），保留 LaTeX 工具页面（`/backup/latex`）及其完整功能。

## 核心变更

- 删除 4 个页面文件：`ProjectBackupPage.tsx`、`DatabaseBackupPage.tsx`、`FilesBrowserPage.tsx`、`SchedulerPage.tsx`
- 删除工具文件：`src/utils/backupApi.ts`（仅被上述四个页面使用）
- 清理 `App.tsx`：移除 4 个 import 和对应 Route
- 清理 `Layout.tsx`：导航菜单中只保留"LaTeX 工具"一项，移除无用 icon 导入（Archive、Database、Files、Clock）及 token 同步逻辑

## 技术栈

现有项目：React + TypeScript + Vite，路由使用 react-router-dom，导航内联于 Layout.tsx。

## 实现思路

纯代码删减操作，分三步：

1. 删除 4 个页面文件和 `backupApi.ts` 工具文件
2. 修改 `App.tsx` 移除无用 import 和 Route 声明
3. 修改 `Layout.tsx` 精简导航菜单和无用依赖

## 实现注意事项

- `LatexToolPage.tsx` 不依赖 `backupApi.ts`，删除后无断链风险
- `Layout.tsx` 中 `setBackupToken` 来自 `backupApi.ts`，需同步删除该 import 和 token 同步 `useEffect`；相关 lucide-react icon（`Archive`、`Database`、`Files`、`Clock`）也需从 import 中移除，避免 TypeScript 未使用变量警告
- 默认重定向 `/` → `/source-materials` 不变
- "Overleaf 备份"分组仅剩"LaTeX 工具"一项，分组标题保留即可，无需改动分组结构

## 目录结构

```
src/
├── app/
│   ├── App.tsx                              # [MODIFY] 删除4个import和Route
│   ├── components/
│   │   └── Layout.tsx                       # [MODIFY] 精简NAV_GROUPS、icon导入、token逻辑
│   └── pages/
│       └── backup/
│           ├── LatexToolPage.tsx            # [KEEP] 不变
│           ├── ProjectBackupPage.tsx        # [DELETE]
│           ├── DatabaseBackupPage.tsx       # [DELETE]
│           ├── FilesBrowserPage.tsx         # [DELETE]
│           └── SchedulerPage.tsx            # [DELETE]
└── utils/
    ├── backupApi.ts                         # [DELETE] 无任何存活页面引用
    ├── mineruApi.ts                         # [KEEP]
    └── ...
```