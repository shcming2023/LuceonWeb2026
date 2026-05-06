---
name: luceon2026-bug-fixes
overview: 按优先级修复评审报告中的15个问题，涵盖db-server.mjs的数据安全问题（原子写入、内存缓存、失败响应），appReducer.ts的状态联动一致性问题，SourceMaterialsPage的ID冲突问题，mineruApi.ts的超时和错误检测问题，以及Dockerfile冗余依赖清理。
todos:
  - id: fix-db-server-p0
    content: 修复 db-server.mjs：引入内存缓存消除全量读磁盘(#6)、原子写入(#5)、写入失败返回500(#9)、Number(id)修复(#1)、添加全局错误中间件(#13)
    status: completed
  - id: fix-reducer-p1
    content: 修复 appReducer.ts：UPDATE_MATERIAL联动assetDetails(#2)、标签更新联动(#3)、UPDATE_ASSET_TAGS守卫(#10)、ADD_MATERIAL metadata可选链(#12)
    status: completed
  - id: fix-frontend-p1
    content: 修复 SourceMaterialsPage.tsx 多文件ID冲突(#11)；修复 mineruApi.ts OSS上传超时(#8)和网络错误检测(#14)
    status: completed
  - id: fix-context-pagination-p2p3
    content: 修复 appContext.tsx 差量upsert(#7)；修复 pagination.ts 分页重置依赖(#4)；清理 Dockerfile 冗余编译依赖(#15)
    status: completed
    dependencies:
      - fix-reducer-p1
  - id: commit-and-push
    content: git commit 全部修复；使用 [mcp:GitHub MCP Server] push_files 同步到远程 main 分支
    status: completed
    dependencies:
      - fix-db-server-p0
      - fix-reducer-p1
      - fix-frontend-p1
      - fix-context-pagination-p2p3
---

## 用户需求

根据对 Luceon2026 项目全面评审报告中发现的 15 个问题，按优先级 P0 → P1 → P2 → P3 逐一修复，使项目达到生产可用级别。

## 产品概述

EduAsset CMS 教育资料管理系统，修复目标涵盖服务端数据安全、前端状态一致性、性能优化、鲁棒性防御、代码冗余清理五个维度。

## 核心修复内容

### P0 — 数据安全（server/db-server.mjs）

- **#5** JSON 文件写入改为 write-tmp + renameSync 原子操作，防止进程崩溃时数据截断损坏
- **#6** 引入模块级内存缓存（`let dbCache`），所有读取从内存返回，写入时同步刷盘；消除每次请求全量 readFileSync，同时解决并发写冲突
- **#9** `writeDB` 失败时抛出异常，所有调用方在 try/catch 中返回 HTTP 500，客户端可感知写入失败

### P1 — 状态一致性（src/store/appReducer.ts + SourceMaterialsPage.tsx）

- **#2** `UPDATE_MATERIAL` 同步更新 `assetDetails[id]`（title/status/tags/metadata 有则同步），参照 `UPDATE_MATERIAL_AI_STATUS` 的联动写法
- **#3** `UPDATE_MATERIAL_TAGS` 和 `BATCH_ADD_TAGS` 同步更新 `assetDetails[id].tags`
- **#10** `UPDATE_ASSET_TAGS` 添加守卫：若 `assetDetails[id]` 不存在则直接返回原 state，不创建残缺对象
- **#12** `ADD_MATERIAL` 中对 `m.metadata` 使用可选链 `m.metadata?.subject` 防御 undefined
- **#11** 多文件上传循环中使用递增计数器替代 `Date.now()` 直接赋值，确保 ID 唯一性

### P2 — 性能与可靠性

- **#7** `appContext.tsx` 全量 upsert 改为 diff 检测，只对发生变化的记录执行 dbPost/dbPut
- **#8** `mineruApi.ts` OSS 上传添加 `AbortSignal.timeout(120_000)`（2分钟超时）
- **#13** `db-server.mjs` 添加 Express 全局错误处理中间件（四参数）
- **#3（含）** BATCH_ADD_TAGS 联动 assetDetails 同 P1 一并处理

### P3 — 代码质量

- **#14** `mineruApi.ts` 网络错误检测去除宽泛的 `includes('fetch')` 和 `includes('abort')`，改用 `err.name === 'AbortError'` 及 `err.cause?.code` 精确匹配
- **#15** `server/Dockerfile` 删除不再需要的 `python3 make g++` 编译工具及对应注释
- **#4** `pagination.ts` 分页重置依赖改为 `data`（数组引用）而非 `data.length`
- **#1** db-server.mjs 中 `PUT /materials/:id` 和 `PUT /asset-details/:id` 的 `id: Number(id)` 改为原样保留 id 字段，保持类型与客户端一致

## 技术栈

与现有项目完全一致，无新增依赖：

- 服务端：Node.js ESM（.mjs）+ Express + Node.js 内置 `fs` 模块（`renameSync` 已在标准库中）
- 前端：React + TypeScript + Zustand-style useReducer

## 实现方案

### db-server.mjs 重构策略（#5 + #6 + #9 + #1 + #13）

**内存缓存 + 原子写入 + 写入失败抛异常：**

```
启动时 → readFileSync 初始化 dbCache（模块级变量）
所有 GET handler → 直接读 dbCache（不再 readFileSync）
所有写 handler → 修改 dbCache → 调用 writeDB(dbCache) → 抛异常或返回 ok
writeDB 内部 → writeFileSync(tmp) → renameSync(tmp, DATA_PATH)
```

关键要点：

- `dbCache` 为模块级 `let` 变量，启动时一次性从磁盘加载
- `writeDB` 改为**同步抛出**（不再 try/catch 吞掉），调用方用 try/catch 包裹并返回 `res.status(500).json({ error })`
- 原子写入：先 `writeFileSync(DATA_PATH + '.tmp', ...)` 再 `renameSync(DATA_PATH + '.tmp', DATA_PATH)`
- `id: Number(id)` 改为 `id: req.body.id ?? id`，保留客户端传入的 id 类型

### appReducer.ts 修复策略（#2 + #3 + #10 + #12）

参照同文件中 `UPDATE_MATERIAL_AI_STATUS`（第 137-178 行）已有的联动写法：

- `UPDATE_MATERIAL`：若 `updates` 含 `title/status/tags`，同步写入 `assetDetails[id]`；若含 `metadata`，合并到 `assetDetails[id].metadata`；存在性检查用 `existingDetail ?`守卫
- `UPDATE_MATERIAL_TAGS` + `BATCH_ADD_TAGS`：在更新 `materials` 的同时，对每个命中的 id 同步写 `assetDetails[id].tags`
- `UPDATE_ASSET_TAGS`：先判断 `state.assetDetails[action.payload.id]` 是否存在，不存在直接 `return state`
- `ADD_MATERIAL`：`m.metadata?.subject` 可选链

### SourceMaterialsPage.tsx（#11）

在 `handleFileChange` 函数外部（组件作用域）维护 `const idCounterRef = useRef(0)`，循环内使用：

```ts
const newId = Date.now() * 1000 + (idCounterRef.current++ % 1000);
```

确保同一毫秒内多文件 ID 严格递增且唯一。

### appContext.tsx 差量 upsert（#7）

在 `prevMaterialsRef` 旁维护 `prevMaterialsMapRef`（`useRef<Map<number, string>>`，存储每条 material 的 JSON 指纹），每次 `useEffect` 触发时：

1. 计算当前各 material 的 `JSON.stringify` 哈希
2. 只对哈希发生变化的条目执行 `dbPost`
同理处理 assetDetails 的 `dbPut`。

### mineruApi.ts（#8 + #14）

- OSS 上传添加 `signal: AbortSignal.timeout(120_000)`
- 网络错误检测：去除 `includes('fetch')` 和 `includes('abort')`，改为：

```ts
const isNetworkErr = err.name === 'AbortError'
|| ['EAI_AGAIN','ECONNRESET','ETIMEDOUT','ENOTFOUND','ECONNREFUSED'].includes(err.cause?.code ?? '')
|| msg.includes('EAI_AGAIN') || msg.includes('ECONNRESET') || msg.includes('ETIMEDOUT');
```

同时对 `AbortError` 额外判断是否为用户主动取消（通过外部传入的 AbortSignal），是则不重试。

### pagination.ts（#4）

```ts
useEffect(() => {
  setCurrentPage(1);
}, [data]);
```

直接依赖 `data` 引用，每次过滤产生新数组时自动重置。

## 性能与向后兼容说明

- 内存缓存对 db-server 是单进程无状态服务（Docker 单容器），不存在多实例同步问题，安全
- 差量 upsert 使用 `JSON.stringify` 作指纹，略有序列化开销，但相比每次 N 次网络请求收益明显
- 所有修改均向后兼容，不改变 API 接口和 localStorage 格式

## 目录结构

```
server/
  db-server.mjs      # [MODIFY] P0+P1: 内存缓存、原子写入、写入失败500、全局错误中间件、Number(id)修复
  Dockerfile         # [MODIFY] P3: 删除 python3 make g++ 及对应注释

src/
  store/
    appReducer.ts    # [MODIFY] P1: UPDATE_MATERIAL联动、标签联动、UPDATE_ASSET_TAGS守卫、metadata可选链
    appContext.tsx   # [MODIFY] P2: 差量upsert（materials + assetDetails）
  utils/
    mineruApi.ts     # [MODIFY] P2+P3: OSS上传超时、网络错误检测精确化
    pagination.ts    # [MODIFY] P3: 分页重置依赖data引用
  app/pages/
    SourceMaterialsPage.tsx  # [MODIFY] P1: ID冲突修复（递增计数器）
```

## Agent Extensions

### MCP

- **GitHub MCP Server**
- Purpose: 所有修复完成并本地 git commit 后，通过 push_files 将修改同步到远程 GitHub 仓库
- Expected outcome: 远程 main 分支包含本次全部修复提交，可供代码审查