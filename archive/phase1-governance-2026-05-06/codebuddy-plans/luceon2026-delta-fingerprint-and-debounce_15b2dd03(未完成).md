---
name: luceon2026-delta-fingerprint-and-debounce
overview: 为 processTasks、products、flexibleTags、aiRules、tasks 五个集合加入差量指纹检测（同 materials/assetDetails 方式），并为 db-server 的 writeDB() 添加 100ms debounce，彻底消除批量操作下的冗余网络请求与磁盘写入。
todos:
  - id: frontend-fingerprints
    content: 在 appContext.tsx 新增5个指纹 useRef，并修改 processTasks/tasks/products/flexibleTags/aiRules 的 useEffect 改为差量指纹写入
    status: pending
  - id: backend-debounce
    content: 在 db-server.mjs 将 writeDB() 改为 100ms debounce 落盘，简化各路由 handler 的 try/catch
    status: pending
  - id: commit-push
    content: lint 验证通过后，commit 并 push 到 main 分支
    status: pending
    dependencies:
      - frontend-fingerprints
      - backend-debounce
---

## 用户需求

### 需求1：对剩余5个集合添加差量指纹检测

`processTasks`、`tasks`、`products`、`flexibleTags`、`aiRules` 这五个集合的持久化 useEffect 目前全量发送 POST 请求——每次 state 引用变化就对全部记录各发一个请求，无论记录内容是否真正改变。

目标：与已有的 `materials` / `assetDetails` 实现保持完全一致，为这五个集合各维护一个 `useRef<Map<number, string>>` 指纹缓存，只对 JSON 指纹发生变化的记录发送网络请求。

### 需求2：为 writeDB() 添加 100ms debounce

`db-server.mjs` 中每收到一个写请求就同步调用 `writeDB()` 落盘一次。批量操作（如批量加标签、批量上传文件）会在几十毫秒内产生数十次写入，绝大多数是冗余的。

目标：`writeDB()` 改为 debounce 落盘（延迟 100ms，期间重复调用重置计时器）；`dbCache` 仍在各路由 handler 中实时更新，保证 GET 请求读取一致性；落盘延迟仅 100ms，对业务无感知。

## 核心功能

- `appContext.tsx`：新增5个指纹 `useRef`，修改对应的5个 `useEffect`，只 POST 真正变化的记录
- `db-server.mjs`：`writeDB()` 改为 debounce 写磁盘，dbCache 修改逻辑保持不变
- 完成后提交并推送到远端

## 技术栈

- 前端：TypeScript + React（useRef / useEffect），与现有代码完全一致
- 后端：Node.js ESM（setTimeout / clearTimeout），无新依赖

## 实现方案

### 前端：差量指纹（appContext.tsx）

严格复用 `materials` 的现有模式（第 314-321 行），对五个集合逐一应用：

1. 在 `materialFingerprintsRef` / `assetDetailFingerprintsRef` 声明处（第 298-299 行）紧接着新增5个指纹 Ref：

```ts
const processTaskFingerprintsRef = useRef<Map<number, string>>(new Map());
const taskFingerprintsRef        = useRef<Map<number, string>>(new Map());
const productFingerprintsRef     = useRef<Map<number, string>>(new Map());
const tagFingerprintsRef         = useRef<Map<number, string>>(new Map());
const aiRuleFingerprintsRef      = useRef<Map<number, string>>(new Map());
```

2. 修改各 `useEffect`，在原有的"删除检测"循环后，将全量 `dbPost` 替换为指纹差量循环：

```ts
for (const item of state.processTasks) {
const fp = JSON.stringify(item);
if (processTaskFingerprintsRef.current.get(item.id) !== fp) {
processTaskFingerprintsRef.current.set(item.id, fp);
dbPost('/process-tasks', item);
}
}
```

`tasks`、`products`、`flexibleTags`、`aiRules` 完全同理。

### 后端：writeDB debounce（db-server.mjs）

在模块顶层声明定时器变量，将 `writeDB()` 拆为"立即的内存一致性检查"和"延迟的磁盘写入"两部分：

```js
let writeTimer = null;

function writeDB() {
  if (writeTimer) clearTimeout(writeTimer);
  writeTimer = setTimeout(() => {
    const dir = path.dirname(DATA_PATH);
    if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
    const tmpPath = DATA_PATH + '.tmp';
    writeFileSync(tmpPath, JSON.stringify(dbCache, null, 2), 'utf-8');
    renameSync(tmpPath, DATA_PATH);
    writeTimer = null;
  }, 100);
}
```

- 各路由 handler 里 `dbCache.xxx = item` 仍然同步执行，GET 请求读内存，始终一致
- `writeDB()` 本身不再抛出异常（落盘在 setTimeout 回调中），需要将 handler 中的 `try/catch` 调整为只捕获 `dbCache` 修改阶段，或直接移除包裹 writeDB 的 try/catch（落盘错误通过进程级 uncaughtException 处理），保持代码简洁

> **注意**：debounce 后 writeDB 内部的磁盘错误不再能直接向请求方返回 500。这是可接受的权衡——该系统为 fire-and-forget 写入模式，磁盘错误极少，且已有全局错误处理中间件和 console.error 日志兜底。

## 执行细节

- 只修改两个文件，改动面极小，无架构变动
- 前端改动：新增5行 useRef + 修改5个 useEffect 的 POST 循环，不触碰任何删除逻辑、prevIds、localStorage 逻辑
- 后端改动：仅替换 writeDB 函数体，各路由 handler 的 dbCache 赋值代码不动；移除 handler 内包裹 writeDB 的 try/catch（因为 writeDB 不再同步抛异常），保留 dbCache 赋值部分的错误处理（实际上赋值不会抛异常，可以简化为无 try/catch，直接 `res.json({ ok: true })`）

## 目录结构

```
src/store/appContext.tsx   [MODIFY] 新增5个指纹 useRef；修改 processTasks/tasks/products/flexibleTags/aiRules 的 useEffect，加入差量指纹循环
server/db-server.mjs       [MODIFY] 顶层添加 writeTimer；writeDB() 改为 debounce 落盘；各路由 handler 移除包裹 writeDB 的 try/catch 块（保留 dbCache 赋值），简化响应为 res.json({ ok: true })
```