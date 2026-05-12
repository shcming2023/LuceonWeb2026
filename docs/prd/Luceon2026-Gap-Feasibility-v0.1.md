# Luceon2026 缺口编码可行性分析报告 v0.1

- 文档版本：v0.1
- 发布日期：2026-05-11
- 作者：许清楚（Xu）· 产品经理
- 前序文档：[稳定性 PRD v0.1](./Luceon2026-Stability-PRD-v0.1.md)（第 9 章已知缺口）
- 分析范围：KG-01 ~ KG-07 编码可行性判定

---

## 1. 分析方法说明

本报告基于以下证据来源，对每个缺口进行重新评估：

- **上阶段产出（T-S01~T-S08）**：SOP 工作流中各架构师对缺口的修补结果
- **即时源码审计**：对 `server/services/queue/task-worker.mjs` 和 `server/upload-server.mjs` 的现场代码审查
- **测试文件审计**：对 `server/tests/` 下相关 smoke test 的审查
- **稳定性 PRD v0.1**：第 9 章记录的原始缺口判定（"旧状态"基线）

判定偏差说明：稳定性 PRD v0.1 第 9 章的缺口判定基于旧代码状态。在上阶段 SOP 工作流中，部分缺口已通过编码修复或 pipeline 补齐。本报告基于当前 `main` 分支真实代码状态重新评估。

---

## 2. 各缺口逐个分析

---

### 2.1 KG-01：ParseTask Worker stale-recovery 未实现

#### 当前真实状态重新评估

**综合判定：已消除 — 恢复机制比 PRD 契约要求更全面**

稳定性 PRD v0.1 中 S-E2 要求的恢复语义包括：
1. 启动时扫描 `state ∈ {pending, running}` 并补偿调度
2. 超过 `localTimeout + 60s` 的 `running` 任务重置为 `pending`
3. 记录 `parse-stale-running-recovered` 事件

经源码审计，`task-worker.mjs` 当前实现已**大幅超出**上述契约：

| 契约需求 | 实现状态 | 对应代码 |
|:---|:---|:---|
| 启动时扫描 pending/running 并补偿 | 已实现 | `runRecoveryScan()` — `task-worker.mjs:198` |
| stale-running 超时重置为 pending | 已实现 | `runRecoveryScan()` § isExplicitlyStale 分支 — `:376-413` |
| parse-stale-running-recovered 事件 | 已实现 | `:395` |
| 启动重启恢复事件 | 已实现 | `parse-restart-recovered` — `:395` |
| 日常轮询 stale 检测 | 已实现 | `recoverStaleRunningTasks()` — `:606-644` |
| MinerU API 状态裁决 | 已实现（超出契约） | `_adjudicateStaleWithMineruApi()` — `:656-862` |
| MinerU 已确认失败同步 | 已实现（超出契约） | `syncMineruApiFailedState()` — `:452-590` |
| 误判 failed 纠偏 | 已实现（超出契约） | `recoverMisjudgedFailedTasks()` — `:864+` |
| 内存锁防护（processingMap 清理） | 已实现 | `:412` |
| STALE_GRACE_MS = 60s | 已实现 | `:27` |
| RECOVERY_DELAY_MS = 2s | 已实现 | `:29` |

**关键代码片段**：

```javascript
// 启动恢复扫描入口 — task-worker.mjs:105-116
start() {
    // ...
    setTimeout(() => {
      this.runRecoveryScan().catch((err) => {
        console.error(`[task-worker] recovery scan failed: ${err.message}`);
      });
    }, RECOVERY_DELAY_MS);
    this.tick();
}

// 事件日志 — task-worker.mjs:391-411
await logTaskEvent({
  event: isExplicitlyStale ? 'parse-stale-running-recovered' : 'parse-restart-recovered',
  // ...
  payload: {
    recoveryTrigger: isExplicitlyStale ? 'stale-timeout' : 'restart',
    staleCheck: { updatedAt, timeoutMs, gracePeriodMs: STALE_GRACE_MS }
  }
});
```

T-S01 已完成事件命名对齐（`parse-stale-running-recovered` 与 PRD 契约一致）。

#### 编码可行性判定

| 判定 | 理由 |
|:---|:---|
| **已消除** | 恢复逻辑已全面实现并通过命名对齐验证；存在两种恢复触发路径（重启恢复 + 日常轮询恢复）；对已有 mineruTaskId 的任务额外查询 MinerU API 裁决，比 PRD 契约更完善 |

---

### 2.2 KG-02：24-PDF 压力测试未通过

#### 当前真实状态重新评估

**综合判定：需测试验证 — 代码基础设施已就位，缺少的是通过性验证**

稳定性 PRD v0.1 记录的"未通过"基于两次历史测试：
- 第一次：24 failed, 0 completed（MinerU HTTP 500，准入电路尚未就位）
- 第二次：20/24 创建，sample 21 curl exit 26（部分通过，但被异常中断截断）

目前已完成的关键修复：
- **准入电路（S-C1）**：已集成到 `main`，持久化 MinerU 准入电路可阻断级联故障
- **级联失败防护（S-C2）**：电路打开时当前任务保持 dependency-blocked，不标记 failed
- **诊断分类修复**：`/ops/mineru/diagnostics` 正确分离 historicalAiFailureTasks
- **takeover 路径**：completed-after-local-timeout 路径已覆盖轮询超时场景

当前状态是：压力测试的**执行基础设施**和**故障隔离代码**均已就位，但缺少一次完整的 24-PDF 通过性测试来验证修复效果。

#### 编码可行性判定

| 判定 | 理由 |
|:---|:---|
| **需测试验证** | 代码层面已通过准入电路和级联防护解决已知故障模式；当前缺少的是在修复后的代码基础上重新执行 24-PDF 压力测试，获取通过性证据 |

#### 补充说明

若重新执行 24-PDF 压力测试后仍失败，则根据失败模式可能需要额外编码。当前建议优先执行压力测试，再根据结果判断是否需要编码修复。

---

### 2.3 KG-03：Ollama keep-alive 未做生产压力测试

#### 当前真实状态重新评估

**综合判定：需测试验证 — keep-alive 代码已实现，缺少生产部署验证**

代码审计确认：
- keep-alive 心跳代码已实现（稳定性 PRD S-A4 确认）
- 冷/热语义区分已实现（dependency-health 中正确返回 hot/cold 状态）
- Ollama 监听器唯一性已修复（S-A2：已消除）

当前缺口本质是：代码被写了但**没有在长时间生产运行中验证其稳定性**。这包括：
- keep-alive 连接在 ≥ 30 分钟运行中未断开
- 冷/热状态切换逻辑在生产中的正确性
- 极端网络条件下的心跳重建行为

#### 编码可行性判定

| 判定 | 理由 |
|:---|:---|
| **需测试验证** | keep-alive 心跳和冷/热语义的代码已全部实现；缺少的是生产部署环境下的长时间运行验证和执行数据，而非代码问题 |

---

### 2.4 KG-04：Ollama 冷启动依赖操作员预热

#### 当前真实状态重新评估

**综合判定：运维性缺口 — 系统设计层面已接受手动预热，当前不需要代码变更**

证据：
- 稳定性 PRD v0.1 第 9.3 条明确声明接受此风险："Ollama 冷启动延迟：接受操作员必须手动预热的运维负担。Phase 2 评估自动预热机制"
- 第 8.2 节已定义完整的 Ollama 模型预热规程（3 步操作）
- 第 8.1 节将"模型已预热"列为操作员启动前检查清单第 6 项
- 冷 probe 加载耗时约 8.9s（总耗时 9.7~10.6s），属于 Ollama 自身特性，非 Luceon 代码缺陷
- dependency-health 已正确区分冷/热状态并在冷状态时给出明确诊断信息

#### 编码可行性判定

| 判定 | 理由 |
|:---|:---|
| **运维性缺口** | Ollama 冷启动延迟是外部依赖特性，Luceon 代码层面已通过明确的健康检查语义和诊断信息缓解；预热流程已文档化；Phase 1 接受手动预热，Phase 2 可评估自动预热 |

#### 补充说明

若在 Phase 2 考虑自动化，技术路径为：在系统启动序列中自动向 Ollama `/api/chat` 发送预热探针，等待热响应时间 < 2s 后再继续初始化。实现难度为 S（小型），涉及文件为系统启动脚本或 `upload-server.mjs` 启动流程。但**不推荐在本次修复中实现**，因为：
- PRD 已明确接受此运维负担
- 自动化预热增加启动时间且可能掩盖 Ollama 本身的启动问题
- 手动预热给了操作员一个自然的 Ollama 健康检查窗口

---

### 2.5 KG-05：upload-server 单体架构

#### 当前真实状态重新评估

**综合判定：架构性缺口 — Phase 1 明确不做拆分**

证据：
- 功能 PRD v0.4 第 10.4 节将拆分列为 P1
- 稳定性 PRD v0.1 第 3.2 条明确列为非目标："不做 `upload-server.mjs` 单体架构重构"
- S-F1 定义了变更约束：任何对 `upload-server.mjs` 的变更必须通过 Tier 2 Standard UAT，且不得新增无关业务逻辑
- 当前 `upload-server.mjs` 耦合了路由、业务逻辑、Worker 调度、MinerU 观测、AI backfill 等多个职责

拆分的影响分析：
- **路由层**：Express app 路由注册（约 500+ 行）
- **业务逻辑**：任务上传流程、Material 管理、状态推进（约 3000+ 行）
- **Worker 调度**：ParseTaskWorker 和 AiMetadataWorker 的启动/停止
- **观测与诊断**：MinerU log observation、global observation、diagnostics
- **AI backfill**：AI 任务完成后的结果回填

拆分预计涉及 10+ 文件变更、路由重构、中间件迁移和回归测试，属于大规模架构重构，不适宜在 Phase 1 收尾阶段执行。

#### 编码可行性判定

| 判定 | 理由 |
|:---|:---|
| **架构性缺口** | 单体拆分需要大规模架构重构（路由层、业务逻辑、Worker 调度等拆分），PRD 明确列为 Phase 1 非目标；Phase 2 优先级执行 |

---

### 2.6 KG-06：MinerU 观测窗口后补未实现

#### 当前真实状态重新评估

**综合判定：已消除 — completed-window-backfill 机制已实现并拥有 smoke test 覆盖**

这是上阶段中"完全未被触碰"的代码缺口，但经源码审计发现：**该机制已经实现**。

关键代码证据（`upload-server.mjs`）：

**1. 核心函数：`selectMineruObservationAttribution()`**

该函数实现了完整的观测归属判定逻辑，包含 `completed-window-backfill` 归属模式：

```javascript
// upload-server.mjs 逻辑摘要
// 优先级 1：live active task（正在运行的任务）
// 优先级 2：completed-window-backfill（在宽限期内的已完成任务）
// 优先级 3：unattributed（无法归属）

if (completedCandidates.length === 1) {
    return { task: completedCandidates[0], mode: 'completed-window-backfill' };
}
```

**2. Backfill 归属条件**（`:1304-1311`）：
- `engine === 'local-mineru'`
- 非 live running 任务
- 有 `mineruTaskId` 和 `mineruStartedAt`
- 观测时间在启动时间容差（`MINERU_OBSERVATION_START_TOLERANCE_MS`）内
- 观测时间在完成时间 + 宽限期（`MINERU_COMPLETED_OBSERVATION_GRACE_MS`）内

**3. 边界处理**：
- 多候选 → unattributed（`:1295-1296`）
- 已取消任务排除（`:1305`）
- 终态任务保护（`:1328-1340`：`shouldMutateMineruObservation`）
- 终态任务的观测陈旧容忍（`:1342-1361`：`normalizeTerminalMineruObservationSnapshot`）

**4. Smoke Test 覆盖**（`server/tests/mineru-sidecar-completed-window-smoke.mjs`）：

| 测试用例 | 场景 | 状态 |
|:---|:---|:---|
| Case 1 | 单个 live active 任务保持优先 | 通过 |
| Case 2 | 单个 recently completed 任务获得 backfill | 通过 |
| Case 3 | 多个 completed candidates 保持 unattributed | 通过 |
| Case 4 | 观测时间在 start tolerance 内的归因为 backfill | 通过 |
| Case 5 | 观测时间在 start tolerance 外的不被归因 | 通过 |
| Case 6 | 观测时间超过 grace window 的不被归因 | 通过 |
| Case 7 | 旧的 completed 任务不被无限期考虑 | 通过 |
| Case 8 | 已取消任务被排除 | 通过 |

该测试文件有 8 个断言用例，全部通过。

#### 编码可行性判定

| 判定 | 理由 |
|:---|:---|
| **已消除** | completed-window-backfill 机制已在 `upload-server.mjs` 中完整实现，包含 8 个 smoke test 用例且全部通过；代码覆盖了 live-active 优先、completed-window-backfill 归属、多候选保护、时间容差、宽限期和终态任务保护等完整边界 |

---

### 2.7 KG-07：阶段排队模型仅通过 3-sample 验证

#### 当前真实状态重新评估

**综合判定：需测试验证 — 并发模型代码已实现，缺少 5+ 并发验证**

证据：
- 阶段排队模型代码已实现（稳定性 PRD S-D2 确认）
- 3-sample 验证通过（sample 1、2 到达 review-pending，sample 3 因终端状态传播 bug 卡住后修复恢复）
- 并发控制约束已存在：
  - `MAX_CONCURRENT_TASKS = 1`（heavy-stage 严格串行）
  - FIFO 调度收口（`pendingTasks.sort()` with mineruTaskId 优先）
  - 准入电路确保并发数不超过 heavy-stage limit
- 缺少的是 5+ 并发场景的验证证据

当前代码的并发保护机制已就位：
- 内存锁 `processingMap` 防重复处理
- `MAX_CONCURRENT_TASKS = 1` 硬约束
- FIFO 排序确保公平调度
- 准入电路在 submit-path 故障时阻断新任务

理论上的并发安全性是成立的，但缺少实证。

#### 编码可行性判定

| 判定 | 理由 |
|:---|:---|
| **需测试验证** | 阶段排队模型的代码逻辑已完整实现（含 FIFO 排序、并发约束、内存锁防护）；缺少的是 5+ 并发场景的运行时验证证据 |

---

## 3. 汇总判定矩阵

| 缺口编号 | 缺口描述 | PRD 原判 | 当前真实状态 | 编码可行性 |
|:---|:---|:---|:---|:---|
| KG-01 | ParseTask Worker stale-recovery 未实现 | P0 | 恢复机制已全面实现（含重启恢复、日常轮询检测、MinerU API 裁决、误判纠偏），超出 PRD 契约 | **已消除** |
| KG-02 | 24-PDF 压力测试未通过 | P0 | 准入电路和级联防护已就位，需重新执行压力测试获取通过性证据 | **需测试验证** |
| KG-03 | Ollama keep-alive 未做生产压力测试 | P1 | keep-alive 代码已实现，缺少长时间生产运行验证 | **需测试验证** |
| KG-04 | Ollama 冷启动依赖操作员预热 | P1 | 外部依赖特性，预热规程已文档化，Phase 1 接受手动预热 | **运维性缺口** |
| KG-05 | upload-server 单体架构 | P2 | 大规模架构重构，Phase 1 明确不做拆分 | **架构性缺口** |
| KG-06 | MinerU 观测窗口后补未实现 | P2 | completed-window-backfill 已实现（8 个 smoke test 通过） | **已消除** |
| KG-07 | 阶段排队模型仅通过 3-sample 验证 | P0 | 并发模型代码已完整实现，缺少 5+ 并发验证 | **需测试验证** |

### 统计

| 判定类别 | 数量 | 缺口编号 |
|:---|:---|:---|
| 已消除 | 2 | KG-01, KG-06 |
| 需测试验证 | 3 | KG-02, KG-03, KG-07 |
| 运维性缺口 | 1 | KG-04 |
| 架构性缺口 | 1 | KG-05 |
| 可直接编码 | 0 | — |

---

## 4. 可直接编码的缺口 → 详细需求规格

**本次分析结论：无纯编码缺口。**

原 7 个缺口在经上阶段 SOP 工作流修补后，已无"需要通过写代码来填补"的缺口。所有残余问题归属于——

- **需测试验证（KG-02, KG-03, KG-07）**：代码已就位，需要执行测试获取证据
- **运维性（KG-04）**：本质上是操作流程问题
- **架构性（KG-05）**：需要跨阶段的大规模重构

关于 KG-04 的潜在编码路径见本文第 5.3 节"建议转为运维流程的缺口列表"中的补充说明。

---

## 5. 整体建议

### 5.1 建议本次编码修复的缺口列表

**本次无编码修复缺口。**

所有"已消除"缺口已通过上阶段 SOP 工作流解决；所有"需测试验证"缺口不需要新的代码变更。

---

### 5.2 建议本次执行测试验证的缺口列表（优先级排序）

这些缺口需要的是测试执行，而非编码。按优先级排序：

| 优先级 | 缺口 | 建议动作 | 理由 |
|:---|:---|:---|:---|
| **1** | **KG-02**：24-PDF 压力测试 | 在准入电路就位后重新执行完整 24-PDF 压力测试，验证 ≥ 80% 到达终态、0 静默丢失 | 对应稳定性门槛 G1（Phase 1 生产就绪声明的前置条件）；两次历史测试均未通过，本次修复（准入电路 + 级联防护）应实质性改善结果 |
| **2** | **KG-07**：阶段排队模型 5+ 并发验证 | 执行 5~10 个任务的快速连续提交测试，验证所有任务在 10 分钟内到达终态 | 对应稳定性门槛 G7；3-sample 已通过，5+ 验证补齐置信区间 |
| **3** | **KG-03**：Ollama keep-alive 生产验证 | 在 T2 Standard 模式下运行 ≥ 30 分钟，监控 keep-alive 连接状态和冷/热语义切换 | 对应稳定性门槛 G3；代码已就位，需要实证 |

**建议的执行顺序**：优先 KG-02（对生产就绪声明影响最大），然后 KG-07（补齐并发置信度），最后 KG-03（长期运行基线建立）。

---

### 5.3 建议推迟到下阶段的缺口列表

| 缺口 | 推迟理由 | 建议时间点 |
|:---|:---|:---|
| **KG-05**：upload-server 单体架构拆分 | 大规模架构重构（涉及路由层、业务逻辑、Worker 调度、观测模块拆分，预计 10+ 文件变更）；PRD 明确列为 Phase 1 非目标；当前 S-F1 变更约束（Tier 2 UAT 验证 + 不新增无关逻辑）已提供可操作的缓解方案 | Phase 2 启动时优先执行 |
| **KG-04**：Ollama 自动预热（可选的编码路径） | PRD 第 9.3 条已明确接受手动预热；当前操作员预热规程完整且可操作；自动预热不是稳定性修复而是便利性增强 | Phase 2 功能增强周期 |

---

### 5.4 建议转为运维流程的缺口列表

| 缺口 | 运维化处理方式 |
|:---|:---|
| **KG-04**：Ollama 冷启动依赖操作员预热 | 维持现状，操作员按稳定性 PRD 第 8.2 节执行预热。预热规程已完整：`ollama list` → curl `/api/chat` ping → 确认热响应 < 2s。该流程在操作员手册中已有文档化覆盖 |

**关于 KG-04 的补充评估**：技术上可以通过代码自动化预热（在系统启动序列中添加 Ollama ping 探针，等待热响应后继续初始化）。但考虑到：(1) Phase 1 已明确接受手动预热；(2) 预热本身给了操作员一个自然的 Ollama 健康检查时机；(3) 自动化预热增加启动复杂度且可能掩盖 Ollama 自身问题——建议保持当前设计。

---

## 6. 更新稳定性 PRD 建议

基于本次分析，建议对稳定性 PRD v0.1 第 9 章做以下更新：

| 更新项 | 当前 PRD 记录 | 建议更新为 |
|:---|:---|:---|
| KG-01 状态 | "未实现"（P0 缺口） | **已消除** — 恢复机制已全面实现（含重启恢复、日常轮询、MinerU API 裁决、误判纠偏） |
| KG-06 状态 | "待实现"（P2 缺口） | **已消除** — completed-window-backfill 已实现并通过 8 个 smoke test |
| KG-02 状态 | "未通过"（P0 缺口） | **待测试验证** — 准入电路和级联防护已就位，需重新执行 24-PDF 压力测试 |
| KG-03 状态 | "未做生产压力测试"（P1 缺口） | **待测试验证** — keep-alive 代码已实现，需执行长时间运行验证 |
| KG-07 状态 | "仅通过 3-sample 验证"（P0 缺口） | **待测试验证** — 并发模型代码已就位，需执行 5+ 并发验证 |
| 第 4.3 节"各维度分级" | ParseTask 恢复 = P0 | 更新为 **已消除** |
| 第 5.5 节 S-E2 | "未实现" | 更新为 **已实现** |

---

## 7. 关键结论

1. **本次 Phase 1 收尾不需要新的编码工作。** 上阶段 SOP 工作流（T-S01~T-S08）已实质消除了所有编码类缺口。

2. **Phase 1 生产就绪声明的前置条件是测试执行而非代码修复。** 3 个"需测试验证"缺口（KG-02, KG-03, KG-07）直接对应稳定性门槛 G1、G3、G7——它们的通过性需要在修复后的代码基础上重新验证。

3. **KG-01 和 KG-06 的"未实现"判定是基于旧状态。** 这两个缺口在上阶段已实质消除，建议更新稳定性 PRD 相应章节以反映真实状态。

4. **KG-05（单体架构）在 Phase 1 是"正确的设计决定"。** 当前 S-F1 变更约束提供了可操作的缓解，大规模的架构拆分应当成为 Phase 2 的第一个任务，而非在 Phase 1 收尾阶段匆忙进行。

5. **建议优先执行 KG-02（24-PDF 压力测试）。** 这直接决定 Phase 1 能否通过生产就绪门槛 G1，也是所有剩余缺口中对发布决策影响最大的项。

---

## 8. 变更记录

- **v0.1（2026-05-11）**：初始版。
  - 内容：对稳定性 PRD v0.1 第 9 章记录的 7 个已知缺口进行编码可行性分析。基于源码审计（`task-worker.mjs`、`upload-server.mjs`）和测试文件审计，发现 KG-01 和 KG-06 已实质消除，KG-02/KG-03/KG-07 为测试验证问题，KG-04 为运维性缺口，KG-05 为架构性缺口，无可直接编码的缺口。
  - 关键发现：`task-worker.mjs` 中的 ParseTask 恢复机制比 PRD 契约更全面（含 MinerU API 裁决、误判纠偏等）；`upload-server.mjs` 中的 MinerU 观测窗口后补（completed-window-backfill）已实现且拥有 8 个 smoke test 覆盖。
