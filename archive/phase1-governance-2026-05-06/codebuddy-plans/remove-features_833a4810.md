---
name: remove-features
overview: 从 AssetDetailPage 及相关 store 中删除「权限级别」「处理溯源」「操作历史」「版本管理」四个功能模块
todos:
  - id: clean-types
    content: 清理 types.ts：删除 PermissionLevel 类型、AssetDetail 的四个字段、三个接口定义、UPDATE_ASSET_PERMISSION Action
    status: completed
  - id: clean-reducer
    content: 清理 appReducer.ts：删除初始化的 permission/lineage/history/versions、UPDATE_ASSET_PERMISSION case、任务完成时 history 追加逻辑
    status: completed
    dependencies:
      - clean-types
  - id: clean-mockdata
    content: 清理 mockData.ts：删除所有 assetDetail 对象中的 permission、lineage、history、versions 字段及数据
    status: completed
    dependencies:
      - clean-types
  - id: clean-page
    content: 清理 AssetDetailPage.tsx：删除常量、expandHistory state、handlePermissionChange、displayedHistory、四个 UI 区块，整理 import
    status: completed
    dependencies:
      - clean-reducer
      - clean-mockdata
---

## 用户需求

从 `AssetDetailPage` 页面及相关 store 层中，彻底移除以下四个功能模块：

- **权限级别**（Permission Level）
- **处理溯源**（Lineage）
- **操作历史**（History）
- **版本管理**（Versions）

## 功能范围

- UI 层：删除四个模块对应的卡片区块及相关状态变量、事件处理函数、常量
- Store 类型层：删除对应的接口定义（`AssetLineageNode`、`AssetHistoryEntry`、`AssetVersion`）、`PermissionLevel` 类型、`AssetDetail` 中对应字段、以及 `UPDATE_ASSET_PERMISSION` Action 类型
- Reducer 层：删除初始化时写入 `lineage/history/versions/permission` 的代码、`UPDATE_ASSET_PERMISSION` case、任务完成时追加 history 的逻辑
- Mock 数据层：清除所有 `assetDetail` 对象中的 `permission`、`lineage`、`history`、`versions` 字段及其数据
- import 清理：删除不再使用的 lucide 图标导入（`Shield`、`Clock`、`GitBranch`、`FileText`、`ChevronDown`、`ChevronUp`）以及 `PermissionLevel` 类型导入

## 技术栈

现有项目：React + TypeScript，Zustand-like Context store，shadcn/ui 组件。

## 实施思路

纯删除型重构，不新增任何逻辑。按照依赖顺序从底层（types → mockData → appReducer）到上层（AssetDetailPage UI）逐层删除，保证每一层改完后类型仍然一致，避免 TS 编译报错。

**关键注意点**：

1. `appReducer.ts` 中 `handleStartProcessing` 对应的 `UPDATE_ASSET_PERMISSION` 调用（第 121 行）也需同步删除，该调用原本是用于"触发 assetDetails 更新"的变通写法，删除后不影响任务创建逻辑
2. `AssetDetail` 接口中 `history/lineage/versions/permission` 字段删除后，`appReducer` 中所有访问 `state.assetDetails[x].history` 的位置（第 255-263 行的任务完成追加逻辑）必须同步清除，否则 TS 报错
3. `UPDATE_ASSET_PERMISSION` Action 在 types、reducer、页面三处均有使用，须全部清除
4. `mockData.ts` 中产品溯源（products）里的 `lineage` 字段是另一个数据结构（字符串数组），与 `AssetDetail.lineage`（`AssetLineageNode[]`）不同，**不应删除**

## 目录结构

```
src/
├── app/pages/
│   └── AssetDetailPage.tsx          # [MODIFY] 删除常量、state、handler、UI 区块；清理 import
├── store/
│   ├── types.ts                      # [MODIFY] 删除类型定义和字段
│   ├── appReducer.ts                 # [MODIFY] 删除初始化字段、case、history 追加逻辑
│   └── mockData.ts                   # [MODIFY] 删除 assetDetail 中四个字段的数据
```