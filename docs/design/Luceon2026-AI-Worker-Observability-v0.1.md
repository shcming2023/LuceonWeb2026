# AI Worker 可观测性增强 — 根因分析与解决方案 v0.1

- 版本：v0.1
- 日期：2026-05-11
- 作者：齐活林（基于源码分析）
- 适用范围：`server/services/ai/metadata-worker.mjs` + `server/services/ai/providers/ollama.mjs`

---

## 1. 根因确认

### 问题 1：Ollama 调用期间零日志

**根因**：`ollama.mjs:65-71` 使用 `fetch()` + `AbortSignal.timeout()` 做一次性阻塞调用，`stream: false`（line 43）。整个 30-60 秒的 HTTP 请求期间，代码完全卡在 `await response.json()`（line 78），没有任何中间日志。

**证据链**：
```
metadata-worker.mjs:635  _updatePhase('first-pass-running', 20)  ← 调用开始前最后一条日志
ollama.mjs:65-71         await fetch('/api/chat', ...)           ← 30-60s 沉默
ollama.mjs:78            await response.json()                   ← 仍在等待
metadata-worker.mjs:675  logTaskEvent('ai-provider-request-succeeded')  ← 完成后才出现
```

### 问题 2：无法区分慢推理 vs 真挂死

**根因**：唯一的超时保护是 `ollama.mjs:69` 的 `AbortSignal.timeout(this.timeoutMs)`，在 Strict 模式下为 **300000ms（5 分钟）**。而 Ollama 的正常推理时间约 30-60 秒，5 分钟的超时远大于需要，使得"慢推理"和"已挂死"在 5 分钟内完全无法区分。

**关键代码**：
```javascript
// metadata-worker.mjs:511
timeoutMs: STRICT_NO_SKELETON ? 300000 : 120000,

// ollama.mjs:69
signal: AbortSignal.timeout(this.timeoutMs),  // 300000ms = 5分钟
```

### 问题 3：无法跳过卡住任务

**根因**：AI Worker 采用严格串行 + 单任务选取模式。
- `metadata-worker.mjs:157` — `if (!processingMap.has(job.id))` — 同一时间只处理一个
- `metadata-worker.mjs:146-152` — 只选取最早的 1 个 pending job
- `processingMap` 锁在当前 job 上直到 `processJob()` 返回（line 463 add, line 1107 delete）
- stale-recovery 可以将卡住 job 重置为 pending，但不会立即处理下一个 job（需等下一次 tick）

**结果**：一个卡住的 AI job 会阻塞**所有**后续 job，最长阻塞 5 分钟。

---

## 2. 解决方案

### 方案 A：Ollama 调用期间心跳日志（P0）

**目标**：操作员能从 Docker logs 判断 AI Worker 是否还在工作。

**实现**：在 `ollama.mjs` 的 `extractMetadata()` 中增加周期性 console.log。

```javascript
// ollama.mjs:65 之前增加
const heartbeatInterval = setInterval(() => {
  const elapsed = Math.round((Date.now() - startTime) / 1000);
  console.log(`[ai-worker] Ollama ${this.model} 推理中... (已等待 ${elapsed}s)`);
}, 10000);  // 每 10 秒

// ollama.mjs:78 之后增加
clearInterval(heartbeatInterval);
```

**影响**：仅 ~5 行代码变更，无副作用。

---

### 方案 B：Ollama 响应超时独立于请求超时（P0）

**目标**：快速检测 Ollama 是否真的在响应（vs 已挂死）。

**当前问题**：`AbortSignal.timeout(300000)` 是总请求超时。如果 Ollama TCP 连接建立成功但不返回任何数据，5 分钟内无法检测。

**实现**：使用 undici `Agent` 的 `headersTimeout` 作为首字节超时探测。

```javascript
// ollama.mjs:60-62 修改
const dispatcher = new Agent({
  headersTimeout: 30000,      // 首字节超时：30秒内必须开始响应
  bodyTimeout: this.timeoutMs  // 整体超时保持不变
});
```

如果 Ollama 在 30 秒内没有返回任何响应头，`fetch` 会抛出 `HeadersTimeoutError`。这能快速区分"Ollama 可达但慢"和"Ollama 无响应"。

**影响**：约 3 行变更，利用已有 undici Agent 能力。

---

### 方案 C：卡住任务跳过机制（P0）

**目标**：当 AI job 卡住时，不阻塞后续 job。

**实现**：在 `scanAndProcess()` 的 stale-recovery 后立即处理下一个可选 job。

```javascript
// metadata-worker.mjs:143 之后增加
await this.recoverStaleRunningJobs(jobs);

// 如果刚恢复了 stale job(s)，重新获取 pending 列表（可能有新的 pending job）
const recoveredPendingJobs = jobs
  .filter(j => j.state === 'pending' && j.id !== currentJobId)
  .sort((a, b) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime());

if (recoveredPendingJobs.length > 0 && !processingMap.has(recoveredPendingJobs[0].id)) {
  console.log(`[ai-worker] Stale job recovered, picking next: ${recoveredPendingJobs[0].id}`);
  await this.processJob(recoveredPendingJobs[0]);
  return; // 本 tick 已处理一个 job，下次 tick 继续
}
```

**当前行为**：stale-recovery 重置 → 等下一次 tick（10s 后）→ pick 下一个
**优化后**：stale-recovery 重置 → **立即**处理下一个 pending job

**影响**：约 15 行变更，不改变串行语义，只在 stale-recovery 后加速恢复。

---

### 方案 D：减小 Strict 模式 AI 超时（P1）

**目标**：降低卡住时的等待成本。

**当前**：`STRICT_NO_SKELETON ? 300000 : 120000`（5 分钟 vs 2 分钟）

**建议**：`STRICT_NO_SKELETON ? 180000 : 120000`（3 分钟 vs 2 分钟）

Ollama `qwen3.5:9b` 的正常推理时间约 30-60 秒/文档。3 分钟是 3 倍余量，足够覆盖绝大多数场景。如果 3 分钟仍未返回，大概率是挂死。

**影响**：1 行常量变更。

---

## 3. 推荐方案组合与优先级

| 优先级 | 方案 | 改动量 | 文件 |
|--------|------|--------|------|
| P0 | **A. 心跳日志** | ~5 行 | `ollama.mjs` |
| P0 | **B. 首字节超时** | ~3 行 | `ollama.mjs` |
| P0 | **C. 卡住跳过** | ~15 行 | `metadata-worker.mjs` |
| P1 | **D. 减小超时** | 1 行 | `metadata-worker.mjs` |

**总改动量**：< 25 行代码，3 个文件。

---

## 4. 非目标

- 不改为流式（streaming）模式（增加复杂度，当前非流式已稳定）
- 不引入新的外部依赖
- 不改变 strict no-skeleton 语义
- 不改变串行处理的架构决策
- 不修改 MinerU Worker（已有充分可观测性）

---

## 5. 验证

- TypeScript 类型检查必须通过
- 构建必须通过
- 提交一个 Markdown 文件，Docker logs 中应能看到 `Ollama qwen3.5:9b 推理中... (已等待 10s)` 等心跳日志
- 模拟 Ollama 不可达（停止 Ollama），应在 30s 内看到首字节超时日志
