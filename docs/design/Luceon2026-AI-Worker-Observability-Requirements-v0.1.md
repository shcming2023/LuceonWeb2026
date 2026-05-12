# AI Metadata Worker 可观测性与卡死恢复 需求规格文档

**版本**: v0.1
**作者**: 许清楚（产品经理）
**日期**: 2026-05-11
**状态**: Draft

---

## 目录

1. [背景与问题概述](#1-背景与问题概述)
2. [问题代码级确认](#2-问题代码级确认)
3. [解决方案设计](#3-解决方案设计)
4. [推荐方案](#4-推荐方案)
5. [非目标](#5-非目标)
6. [附录：关键代码位置索引](#6-附录关键代码位置索引)

---

## 1. 背景与问题概述

### 1.1 系统上下文

Luceon2026 的 AI Metadata Worker 负责对新上传的教育资源材料进行 AI 元数据识别。每次调用 Ollama `qwen3.5:9b` 进行元数据提取，单次推理耗时约 30-60 秒（少数大文件可达 120 秒以上）。Worker 采用严格串行模式：同一时间只处理一个 job。

### 1.2 核心问题

| # | 问题 | 严重程度 |
|---|------|---------|
| P1 | Ollama 调用期间无心跳日志，操作员无法判断系统"活着还是卡死" | 中 |
| P2 | 无法区分"慢速推理"和"真挂死"，日志表现为完全相同的沉默 | 高 |
| P3 | 严格串行下，一个卡住的任务会阻塞所有后续任务（最长 ~6 分钟） | 中 |

---

## 2. 问题代码级确认

### 2.1 问题 1：Ollama 调用期间无心跳日志

#### 根因分析

`_updatePhase()` 函数（`metadata-worker.mjs:1342`）负责写入"阶段心跳"信息到数据库：

```javascript
// metadata-worker.mjs:1342-1378
async _updatePhase(job, phaseName, progress, message) {
  // 通过 HTTP PATCH 更新 job 的 progress/message/metadata
  // 同时更新关联的 ParseTask 的 state 为 'ai-running'
}
```

然而，`_updatePhase` **只在阶段切换的边界点被调用**：

- `first-pass-running` 在 Ollama 调用**开始前**调用（line 635）
- `first-pass-failed` 在 Ollama 调用抛出异常后调用（line 687）
- `repair-pass-running` 在 repair 阶段开始前调用（line 817）
- `repair-succeeded` / `repair-failed` 等在 repair 结束后调用

**关键缺失**：Ollama API 调用本身（`ollama.mjs:65` 的 `fetch()`）期间，没有任何 `_updatePhase` 或 `console.log` 调用。从 line 635（写入 `first-pass-running`）到 line 687（捕获异常写入 `first-pass-failed`）或 line 674（first pass 成功），中间所有代码路径都是纯 CPU/网络等待，没有任何产物写入。

#### 时间线示意

```
t=0s    _updatePhase('first-pass-running')     # 最后一次可见信号
t=0-60s Ollama API 调用期间                     # ← 完全沉默
t=55s+  Ollama 响应 / 或超时                     # 第一次后续信号
```

对于操作员而言：
- `docker logs` 在 30-60 秒（甚至更长）内完全无输出
- 数据库中的 `updatedAt` 和 `lastHeartbeatAt` 停留在调用开始时刻
- 无法从任何渠道判断系统"在处理中"还是"已卡死"

#### 严重程度判断

- **影响范围**：所有执行中的 AI job
- **严重程度**：**中**。不影响功能正确性，但严重影响运维可观测性和问题诊断效率
- **触发频率**：每次 Ollama API 调用都触发（即每个 job 都受影响）

---

### 2.2 问题 2：无法区分"慢速推理"和"真挂死"

#### 根因分析

##### 2.2.1 唯一的存活检测：stale-recovery 超时

`recoverStaleRunningJobs()`（`metadata-worker.mjs:171-225`）是目前唯一的存活/卡死检测机制：

```javascript
// metadata-worker.mjs:174
const GRACE_PERIOD_MS = 60000; // 60 秒额外缓冲

// metadata-worker.mjs:185
const staleThreshold = updatedAt + this.defaultTimeoutMs + GRACE_PERIOD_MS;

if (now > staleThreshold) {
  // 标记为 stale，重置为 pending
}
```

`defaultTimeoutMs` 的取值：
- `STRICT_NO_SKELETON = true`：300000ms（5 分钟）
- `STRICT_NO_SKELETON = false`：120000ms（2 分钟）

加上 60s grace period，实际首次可检测时间：
- Strict 模式：360s（**6 分钟**）
- 非 Strict 模式：180s（**3 分钟**）

##### 2.2.2 Ollama API 的 AbortController 超时

在 `ollama.mjs:69`，每次 API 调用使用 `AbortSignal.timeout(this.timeoutMs)`：

```javascript
// ollama.mjs:69
signal: AbortSignal.timeout(this.timeoutMs),
```

- 此 timeout 是 **静态的**（来自配置），不是动态判断的
- 超时后抛出 `TimeoutError`/`AbortError`，Worker 捕获后进入失败处理流程

##### 2.2.3 为什么区分不了

在 stale-recovery 的超时窗口内（3-6 分钟），Ollama 慢速推理和 Ollama 已挂死，其外部表现完全相同：

| 维度 | Ollama 慢速推理（处理大文件） | Ollama 已挂死（进程僵尸/死锁） |
|------|----------------------------|------------------------------|
| `updatedAt` | 停留在调用开始时刻 | 停留在调用开始时刻 |
| `_updatePhase` 调用 | 无（等待 API 响应） | 无（等待 API 响应） |
| `console.log` | 无 | 无 |
| Docker logs | 沉默 | 沉默 |
| 数据库状态 | `running` | `running` |

两者唯一的分水岭是 timeout 时间点。在此之前，操作员和系统都无法区分。

##### 2.2.4 现有超时分类机制

Ollama provider 在超时时会尝试分类错误类型（`ollama.mjs:141-146`）：

```javascript
let timeoutKind = 'network-or-fetch-error';
if (err.name === 'TimeoutError' || err.message.includes('AbortError')) {
  timeoutKind = 'abort-timeout';
} else if (err.cause?.code === 'UND_ERR_HEADERS_TIMEOUT' || ...) {
  timeoutKind = 'headers-timeout';
}
```

这是事后分类，发生在 timeout 已经触发之后，不能用于运行时检测。

#### 严重程度判断

- **影响范围**：所有超出预期推理时间的 job（特别是大文件、evidence pack 场景）
- **严重程度**：**高**。这是整个可观测性问题的核心：沉默期太长，且无法区分真实场景和异常场景
- **触发频率**：Ollama 挂死时（低频率，但影响大）；大文件慢速推理（中频率）

---

### 2.3 问题 3：AI Worker 严格串行，无法跳过卡住任务

#### 根因分析

##### 2.3.1 processingMap 的排他锁

`processJob()` 入口（`metadata-worker.mjs:463`）：

```javascript
// metadata-worker.mjs:463
processingMap.add(job.id);
```

出口（`metadata-worker.mjs:1107`）：

```javascript
// metadata-worker.mjs:1107 (finally 块)
processingMap.delete(job.id);
```

`scanAndProcess()` 检查（`metadata-worker.mjs:134`）：

```javascript
// metadata-worker.mjs:134-136
if (processingMap.size > 0) {
  return; // 跳过本轮 tick
}
```

这确保同一时间最多只有一个 job 在执行。

##### 2.3.2 串行选取策略

`scanAndProcess()`（`metadata-worker.mjs:146-159`）每次只选取最早的 1 个 pending job：

```javascript
// metadata-worker.mjs:154-159
if (pendingJobs.length > 0) {
  const job = pendingJobs[0]; // 只选取最早的
  if (!processingMap.has(job.id)) {
    await this.processJob(job);
  }
}
```

##### 2.3.3 卡死→阻塞的链路

1. Job A 的 Ollama 调用卡住（仍在 `fetch()` 等待中）
2. `processingMap` 仍有 Job A 的 id → `scanAndProcess()` 直接 return
3. 每 10s 一次 tick，每次都 return（因为有 processingMap 检查）
4. 直到 Job A 的 `AbortSignal.timeout()` 触发（120s / 300s）或 stale-recovery 超时（+60s）
5. 在这期间，Job B、C、D……全部阻塞

**关键时间线**：
- 非 Strict 模式：job 卡住 → 120s timeout → 可能 re-pick 做 stale recovery（如果 timeout 导致异常但 processingMap 没清理）→ 最终 180s 后 stale recovery 重置为 pending
- Strict 模式：job 卡住 → 300s timeout → 异常捕获 → processingMap 清理 → 但如果有另一个 pending job 在 stale recovery 时已被重置为 running，阻塞继续

##### 2.3.4 现有的"跳过"机制分析

stale-recovery（`recoverStaleRunningJobs`）**已经做了一部分跳过**：
- 它将 `running` 状态且超时的 job 重置为 `pending`
- 但它**不主动 abort 当前正在执行的 job**——它依赖 job 自身 timeout 或外部超时判断
- `recoverStaleRunningJobs` 操作的是数据库中的 job 状态，不是内存中正在执行的 fetch 请求

因此实际情况是：
1. 如果 AI Worker 进程**本身**存活且 fetch 卡在等待中，stale-recovery 把数据库中的 job 重置为 pending
2. 但当 fetch 最终超时或返回时，`processJob` 的后续逻辑可能覆盖这个重置（除非有保护逻辑）

#### 严重程度判断

- **影响范围**：当一个 job 卡住时，队列中所有 pending job 都被阻塞
- **严重程度**：**中**。在正常运维下（Ollama 通常稳定），触发频率低；但一旦触发，影响面大
- **触发频率**：低（Ollama 挂死概率低），但堆积场景（多文件上传时）后果严重

---

## 3. 解决方案设计

### 3.1 问题 1 方案：心跳日志

#### 方案 A：Periodic Heartbeat in `_processJob`（推荐）

在 `processJob` 中，Ollama API 调用期间启动一个 `setInterval` 心跳定时器。

**实现位置**：`metadata-worker.mjs:635`（`_updatePhase('first-pass-running')` 之后）和 `metadata-worker.mjs:817`（repair 阶段类似位置）

**伪代码**：

```javascript
// 在 provider.extractMetadata() 调用外包裹心跳
const heartbeatInterval = setInterval(() => {
  const elapsed = Math.floor((Date.now() - phaseStart) / 1000);
  console.log(`[ai-worker] Job ${job.id} first-pass in progress... (${elapsed}s elapsed)`);
  this._updatePhase(job, 'first-pass-running', 20 + Math.min(elapsed / 5, 10),
    `识别进行中 (${elapsed}s)...`);
}, 10000); // 每 10 秒

try {
  aiResponse = await this._runProviderPass(provider, job, aiSettings, prompt, options);
} finally {
  clearInterval(heartbeatInterval);
}
```

**优点**：
- 实现简单，改动量小
- 每 10s 一次 console.log + 数据库心跳，同时覆盖 docker logs 和数据库两个可观测通道
- 不会干扰 AbortController 的 timeout 处理

**缺点**：
- 心跳是盲目周期性的，不反映实际推理进度
- 每次心跳都调用 `_updatePhase`（两次 HTTP PATCH），增加 DB 负载（但 10s 一次频率可接受）

**可行性**：✅ 高，实现简单，风险低

---

### 3.2 问题 2 方案：挂起检测

#### 方案 A：基于 Ollama API Token 流式输出来判断活跃度

**实现方式**：将 Ollama API 调用从 `stream: false` 改为 `stream: true`，通过流式 token 输出来判断推理正在进行中。

**当前状态**：`ollama.mjs:43` 设置 `stream: false`，意味着 Ollama 在完成全部推理后才返回结果。

```javascript
// ollama.mjs:43
stream: false,
```

**改动要点**：
- 改造 `OllamaProvider.extractMetadata()` 以支持流式响应
- 在流式读取过程中，每个 token/chunk 到达时记录时间戳
- 如果超过 N 秒没有新 token，判定为可能挂死

**优点**：
- 最准确的活跃度判断方式
- 可以同时获得推理进度的额外信息

**缺点**：
- **实现成本高**：需要改造整个 provider 调用链（extractJson → extractMetadata → 流式解析）
- **兼容性风险**：`_runProviderPass` 和其他调用方都期望返回完整的 `{result, rawResponse, usage}` 对象
- **格式依赖**：Ollama `format: 'json'` 流式输出时每个 chunk 不是独立 JSON（JSON 对象片段），需要额外拼装
- **two-pass repair 流程影响**：repair 阶段也需要流式支持

**可行性**：⚠️ 中低，工程量大，风险高，暂不推荐作为首期方案

---

#### 方案 B：基于 TCP 连接活跃度（readable/writable 事件）

**实现方式**：在 undici dispatcher 上监听 TCP socket 的活跃度事件。

**当前状态**：`ollama.mjs:60-63` 使用 undici Agent 设置 headersTimeout 和 bodyTimeout：

```javascript
const dispatcher = new Agent({
  headersTimeout: this.timeoutMs,
  bodyTimeout: this.timeoutMs
});
```

**分析**：
- undici Agent 的 `headersTimeout` 和 `bodyTimeout` 已经是基于 TCP 活动的超时
- 这些是 undici 内部行为，无法被外部代码感知到 socket 活跃度
- Node.js 的 undici 不暴露底层 socket 事件给上层调用方

**可行性**：❌ 低，undici 封装层次太高，无法优雅地获取底层 socket 事件

---

#### 方案 C：基于墙上时钟的超时分级（推荐）

**实现方式**：在 `processJob` 中增加一个独立的看门狗定时器，基于墙上时钟渐进式升级状态。

**伪代码**：

```javascript
const phaseStart = Date.now();
const HEARTBEAT_INTERVAL = 10000;
const WARNING_THRESHOLD = 60000;   // 60s 后开始 warning 日志
const SOFT_TIMEOUT = 120000;       // 120s 后主动检查 Ollama health
const HARD_TIMEOUT = 360000;       // 360s 后强制终止（与现有 stale-recovery 对齐）

const watchdog = setInterval(async () => {
  const elapsed = Date.now() - phaseStart;

  if (elapsed >= HARD_TIMEOUT) {
    console.error(`[ai-worker] Job ${job.id} hard timeout, forcing abort`);
    // 这里需要外部 AbortController 支持（见方案 D）
    clearInterval(watchdog);
  } else if (elapsed >= SOFT_TIMEOUT) {
    // 软超时：尝试 ping Ollama health endpoint
    const ollamaAlive = await this._checkOllamaHealth(provider);
    if (!ollamaAlive) {
      console.error(`[ai-worker] Job ${job.id} detected Ollama unavailable at ${elapsed}ms`);
      clearInterval(watchdog);
      // 触发 abort
    } else {
      console.warn(`[ai-worker] Job ${job.id} running slow (${elapsed}ms), Ollama OK - likely large input`);
    }
  } else if (elapsed >= WARNING_THRESHOLD) {
    console.warn(`[ai-worker] Job ${job.id} running longer than expected (${elapsed}ms)`);
  }
}, HEARTBEAT_INTERVAL);
```

**阈值说明**：
- 60s：正常推理通常 30-60s，超过此时间开始 warning 日志
- 120s：大文件 / evidence pack 场景的正常上限，超过后怀疑异常
- 360s：与 stale-recovery 阈值对齐，强制终止

**优点**：
- 实现简单，不需要改动 provider 层
- 通过 Ollama health check 主动确认服务状态
- 日志分级，操作员可以区分"慢推理"（warning + Ollama OK）和"真挂死"（error + Ollama unavailable）

**缺点**：
- `_checkOllamaHealth` 是一个额外的 HTTP 请求，略微增加网络负载
- 120s 阈值需要根据实际 Ollama 推理时间调优

**可行性**：✅ 高，实现成本低，风险可控

---

#### 方案 D：周期性 Ping Ollama Health Endpoint

**实现方式**：与方案 C 的软超时部分类似，在心跳定时器中增加 Ollama health check。

```javascript
async _checkOllamaHealth(provider) {
  try {
    return await provider.healthCheck();
  } catch {
    return false;
  }
}
```

OllamaProvider 已有 `healthCheck()` 方法（`ollama.mjs:23-31`）：

```javascript
async healthCheck() {
  const resp = await fetch(`${this.baseUrl}/api/tags`, {
    signal: AbortSignal.timeout(5000)
  });
  return resp.ok;
}
```

**结论**：方案 C 已包含此逻辑，方案 D 不单独推荐。

---

### 3.3 问题 3 方案：跳过机制

#### 方案 A：Stale-Recovery 检测到挂死后标记当前 job failed

**分析**：当前 `recoverStaleRunningJobs` 已经将 stale running job 重置为 `pending`。但问题是：

1. 如果 `processJob` 仍在执行（fetch 卡住），它会在 fetch 最终返回/超时后继续执行后续逻辑（updateJob、logTaskEvent 等），可能覆盖 stale-recovery 的数据库更新
2. 在严格串行模式下，`processJob` 不返回，`processingMap` 就有元素，`scanAndProcess` 就跳过

**改进空间**：
- 当前逻辑（重置为 pending）隐式允许该 job 在 timeout 后重试
- 缺少将其直接标记为 `failed`（跳过而非重试）的选项

**可行性**：✅ 当前已部分实现，可进一步优化

---

#### 方案 B：减小 `defaultTimeoutMs`

**分析**：当前 timeout 值：
- Strict no-skeleton：300000ms（5 分钟）
- 非 Strict：120000ms（2 分钟）

如果进一步减小：
- 可能过早终止正常的大文件推理（evidence pack + qwen3.5:9b 可能需要 60-120s）
- 导致不必要的 fallback / skeleton 降级
- 并没有解决"跳过"本身的问题——只是让等待时间变短

**可行性**：❌ 不推荐。timeout 应匹配实际推理时间需求，不应作为跳过机制的手段。

---

#### 方案 C：增加 `maxJobDuration` 独立于 `defaultTimeoutMs` 的硬超时（推荐）

**实现方式**：增加一个独立的 `maxJobDuration` 参数，作为整个 `processJob` 的硬超时上限。此参数独立于 provider 级别的 `timeoutMs`。

**设计原则**：
- `timeoutMs`（provider 级别）：单次 API 调用的超时
- `maxJobDuration`（job 级别）：整个 processJob 的最大运行时长（包含 retry、repair 等）
- 当 `maxJobDuration` 触发时，直接 abort 当前 job，不对结果做任何处理，直接标记 failed

**伪代码**：

```javascript
async processJob(job) {
  processingMap.add(job.id);
  const startTime = Date.now();

  // 环境变量或配置控制的 job 级硬超时
  const MAX_JOB_DURATION_MS = parseInt(process.env.AI_MAX_JOB_DURATION_MS || '360000', 10);
  const abortController = new AbortController();

  try {
    const jobTimer = setTimeout(() => {
      console.error(`[ai-worker] Job ${job.id} exceeded maxJobDuration, aborting`);
      abortController.abort();
    }, MAX_JOB_DURATION_MS);

    // ... 将 abortController.signal 传递给 provider 调用 ...
    // 在 _runProviderPass 或 executeWithFallback 中合并 signal
  } finally {
    clearTimeout(jobTimer);
    processingMap.delete(job.id);
  }
}
```

**优点**：
- 提供 job 级别的独立保护，不依赖 provider timeout
- 可以在 stale-recovery 之前触发（360s < 360s + 60s grace）
- 与现有 timeout 机制不冲突
- 硬超时后的行为明确：直接 abort 并标记 failed

**缺点**：
- 需要将 AbortController 信号传递到 provider 层（改动 _runProviderPass 签名）
- 需要在 provider 中合并外部 signal 和内部 signal

**可行性**：✅ 中高，实现成本可控

---

#### 方案 D：增加 AbortController 的超时自动终止

**实现方式**：利用 Node.js 内置的 `AbortSignal.timeout()`，在 job 级别设置独立的 abort。

**分析**：
- `ollama.mjs:69` 已经使用 `AbortSignal.timeout(this.timeoutMs)`，这是 provider 级别的
- `openai-compatible.mjs:60` 同样使用
- 但这些 signal 是 provider 内部创建的，job 层无法取消

**改进**：在 `_runProviderPass` 中接受一个外部 `AbortSignal`，使用 `AbortSignal.any()` 合并外部信号和内部 timeout。

```javascript
async _runProviderPass(provider, job, aiSettings, prompt, options) {
  const externalSignal = options.externalSignal;
  const internalSignal = AbortSignal.timeout(aiSettings.timeoutMs || 120000);
  const combinedSignal = externalSignal
    ? AbortSignal.any([externalSignal, internalSignal])
    : internalSignal;
  // 传递 combinedSignal 到 provider...
}
```

**注意**：`AbortSignal.any()` 是 Node.js v20+ 的 API。需要确认运行环境。

**可行性**：✅ 中（依赖 Node.js 版本）

---

## 4. 推荐方案

### 4.1 推荐组合

综合考虑**实现成本、风险、收益**，推荐以下方案组合：

| 优先级 | 方案 | 解决问题 | 预估工作量 |
|--------|------|---------|-----------|
| **P1** | 3.1-A：心跳日志（setInterval + _updatePhase） | 问题 1 | 小（~30 行） |
| **P1** | 3.2-C：基于墙上时钟的超时分级 | 问题 2 | 中（~50 行） |
| **P2** | 3.3-C：`maxJobDuration` 硬超时 + AbortController 改造 | 问题 3 | 中（~60 行） |

### 4.2 推荐理由

**P1 组合（问题 1 + 2）**是观测性的核心改进：

1. **心跳日志**（3.1-A）直接解决"docker logs 沉默"问题，每 10 秒在控制台输出进度
2. **超时分级**（3.2-C）通过渐进式升级的 watchdog，在 60s 发出 warning，在 120s 主动检查 Ollama 健康状态，在 360s 强制终止
3. 两者配合：操作员通过 docker logs 看到"识别进行中 (70s)..."，即使看到 warning 日志，也可以检查 Ollama 健康状态字段来区分慢速推理 vs 挂死

**P2 方案（问题 3）**解决阻塞问题：

4. `maxJobDuration` 硬超时确保单个 job 的执行时间不会无限增长
5. 与 AbortController 改造配合，实现 job 级别的 cancel 能力
6. 硬超时触发后，`processingMap` 被清理，后续 job 可以正常开始

### 4.3 不推荐的方案

- **方案 3.2-A（流式 token）**：工程量大，风险高，建议作为 v0.2 或更高版本的增强方案
- **方案 3.2-B（TCP socket 监听）**：undici 封装层次太高，不可行
- **方案 3.3-B（减小 defaultTimeoutMs）**：治标不治本，可能影响正常推理

### 4.4 实施顺序

```
Phase 1 (P1): 心跳日志 + 超时分级
  └── 立即改善可观测性
  └── 无需改动 provider 接口
  └── 零风险

Phase 2 (P2): maxJobDuration + AbortController 改造
  └── 解决串行阻塞问题
  └── 需要调整 provider 调用签名
  └── 需要测试 AbortSignal.any() 兼容性
```

---

## 5. 非目标

以下内容明确不作为本次需求范围：

| 范围 | 原因 |
|------|------|
| 改动 Ollama 配置（模型、部署、keep_alive） | 属于运维配置，非 Worker 逻辑 |
| 改动 MinerU Worker 的日志或超时 | 不同 Worker，关注点分离 |
| 增加多 job 并行处理能力 | 架构决策，串行是设计目标（资源控制），不在本次范围 |
| 引入外部监控系统（Prometheus, Grafana 等） | 新外部依赖，违反约束 |
| 流式 token 粒度的心跳（方案 3.2-A） | 工程量大，暂缓到 v0.2 |
| 增加消息队列（如 BullMQ/Redis） | 新外部依赖，架构变更 |

---

## 6. 附录：关键代码位置索引

| 位置 | 行号 | 描述 |
|------|------|------|
| `metadata-worker.mjs:98` | `defaultTimeoutMs` 初始化 | Strict: 300000ms, 非Strict: 120000ms |
| `metadata-worker.mjs:132-164` | `scanAndProcess()` | 串行选取 pending job, stale recovery 入口 |
| `metadata-worker.mjs:171-225` | `recoverStaleRunningJobs()` | stale recovery 逻辑 (timeout + 60s grace) |
| `metadata-worker.mjs:462-1109` | `processJob()` | 核心处理逻辑 |
| `metadata-worker.mjs:635` | `_updatePhase('first-pass-running')` | Ollama 调用前的最后一个心跳 |
| `metadata-worker.mjs:657-724` | try/catch Ollama 调用 | first pass 的成功/失败处理 |
| `metadata-worker.mjs:687` | `_updatePhase('first-pass-failed')` | Ollama 失败后的第一个心跳 |
| `metadata-worker.mjs:817` | `_updatePhase('repair-pass-running')` | Repair 阶段前的心跳 |
| `metadata-worker.mjs:1107` | `processingMap.delete(job.id)` | 处理完成后的锁释放 |
| `metadata-worker.mjs:1169-1214` | `executeWithFallback()` | Provider 链调用，失败时尝试下一个 provider |
| `metadata-worker.mjs:1342-1378` | `_updatePhase()` | 阶段心跳写入（DB + ParseTask） |
| `ollama.mjs:34-173` | `OllamaProvider.extractMetadata()` | Ollama API 调用实现 |
| `ollama.mjs:43` | `stream: false` | 当前使用非流式模式 |
| `ollama.mjs:60-63` | undici Agent (headersTimeout, bodyTimeout) | TCP 层超时 |
| `ollama.mjs:69` | `AbortSignal.timeout(this.timeoutMs)` | AbortController 超时 |
| `openai-compatible.mjs:60` | `AbortSignal.timeout(this.timeoutMs)` | OpenAI-compatible 的 AbortController |
| `base.mjs:13` | `this.timeoutMs` 默认值 | 120000ms |
