# Luceon2026 稳定性 PRD v0.1 —— Phase 1 生产稳定性工程契约

- 文档版本：v0.1（初始版）
- 发布日期：2026-05-11
- 作者：许清楚（Xu）· 产品经理（基于 Director 提供的 Phase 1 稳定性证据产出）
- 适用范围：Luceon2026 Phase 1 收尾阶段的稳定性需求定义，覆盖 Ollama、MinerU、准入电路、压力测试、恢复机制、基础设施六个稳定性维度
- 文档定位：**工程契约型稳定性 PRD**。本文档是 [Luceon2026 PRD v0.4](./Luceon2026-PRD-v0.4.md) 的稳定性补集，聚焦于"让当前系统稳定运行"的最小需求集。本文档不重复 v0.4 中已有的功能需求，而是定义稳定性层面的可验证断言与验收门槛
- 配套文档：本文档与功能 PRD v0.4 互补；功能 PRD 定义"系统应做什么"，稳定性 PRD 定义"系统在各种故障模式下应如何表现"

---

## 目录

1. [文档元信息](#1-文档元信息)
2. [背景与动机](#2-背景与动机)
3. [稳定性目标与非目标](#3-稳定性目标与非目标)
4. [稳定性分类与分级](#4-稳定性分类与分级)
5. [稳定性需求清单](#5-稳定性需求清单)
6. [稳定性门槛与度量](#6-稳定性门槛与度量)
7. [恢复与降级策略](#7-恢复与降级策略)
8. [运维前置条件](#8-运维前置条件)
9. [已知缺口与风险接受](#9-已知缺口与风险接受)
10. [与功能 PRD 的关系](#10-与功能-prd-的关系)
11. [变更记录](#11-变更记录)

---

## 1. 文档元信息

| 字段 | 值 |
| :--- | :--- |
| 文档编号 | Luceon2026-Stability-PRD-v0.1 |
| 版本 | v0.1 |
| 发布日期 | 2026-05-11 |
| 作者 | 许清楚（Xu）· 产品经理 |
| 审核人 | Director |
| 适用范围 | Phase 1 收尾阶段：Ollama / MinerU / 准入电路 / 压力测试 / 恢复机制 / 基础设施稳定性 |
| 前序文档 | [Luceon2026 PRD v0.4](./Luceon2026-PRD-v0.4.md)（功能 PRD） |
| 维护者 | 许清楚（Xu）；历史 Lucia 维护规程已归档至 `archive/team-model-retired-2026-05-16/docs-prd/lucia-prd-maintenance.md`；6.9.1 后维护遵循 Luceon/Lucode 双角色流程 |

---

## 2. 背景与动机

### 2.1 为什么需要一份独立的稳定性 PRD

Luceon2026 Phase 1 的主线功能——任务式文档解析与 AI 元数据审核工作台——已通过 PRD v0.4 完整定义并实现。系统核心流程（上传 → MinIO 存储 → MinerU 解析 → Ollama AI 元数据识别 → 人工审核）在功能层面已打通。

然而，经过密集型生产验证后暴露出的事实是：**功能可用 ≠ 系统稳定**。以下证据表明系统存在结构性的稳定性缺口：

- **Ollama 冷启动不稳定**：冷 probe 加载耗时约 8.9s，导致依赖健康检查超时阈值（~15s）频繁触发，多次验证 pass 因 Ollama 就绪检查超时而阻塞
- **MinerU 运行时不可靠**：`/health` 返回 OK 但 `POST /tasks` 返回 HTTP 500，导致 24-PDF 压力批量全部失败（24 failed tasks, 0 completed）
- **压力测试无定论**：两次 24-PDF 压力测试均未通过（第一次全部失败，第二次无定论）
- **ParseTask Worker 恢复机制缺失**：PRD v0.4 列为 P0 但尚未实现，缺乏 stale-recovery 和启动补偿
- **并发模型仅通过 3-sample 验证**：未进行大规模并发浸泡测试

这些问题在功能 PRD v0.4 中已有提及（如一致性不变量中的 stale-recovery），但功能 PRD 的 scope 决定了它无法系统性地回答以下稳定性问题：

- 系统在各故障模式下应表现出什么行为？
- 什么是 Phase 1 生产就绪的可量化门槛？
- 操作员需要满足什么前置条件才能确保系统稳定运行？
- 哪些已知缺口是 Director 可接受发布的？

**因此需要一份独立的稳定性 PRD**，从"功能 PRD 即契约"升级为"功能 PRD + 稳定性 PRD 双重契约"。

### 2.2 稳定性 PRD 与功能 PRD 的分工

| 维度 | 功能 PRD v0.4 | 稳定性 PRD v0.1 |
| :--- | :--- | :--- |
| 回答的问题 | 系统应做什么？ | 系统在各种故障模式下应如何表现？ |
| 需求性质 | 功能需求、API 契约、状态机、数据模型 | 故障行为契约、恢复策略、稳定性门槛、运维前置条件 |
| 验证方式 | UAT 功能验收 | 压力测试、故障注入、长时间运行浸泡 |
| 状态字面量 | 定义 Canonical State | 定义 failure mode 分类与降级路径 |

---

## 3. 稳定性目标与非目标

### 3.1 稳定性目标

Phase 1 稳定性的核心目标用一句话表述：

> **在操作员满足运维前置条件的前提下，系统能够在单操作员、单任务串行的生产环境中持续稳定运行，对已知故障模式具有可预测的降级行为，不会发生级联故障或静默数据不一致。**

拆解为以下五条子目标：

1. **依赖就绪可预测**：Ollama 和 MinerU 的就绪状态可通过明确的健康检查语义可靠判定，冷启动/恢复场景下的超时行为符合契约
2. **故障隔离**：任一子系统的故障不会级联扩散到其他子系统；MinerU submit-path 故障不会导致排队任务全部进入 `failed`
3. **状态可恢复**：`running` 或 `ai-running` 中的僵尸任务可在宽限期内自动自愈，重新进入待调度队列
4. **压力可观测**：系统在批量任务提交下的行为可被监控和诊断，不会出现"任务已创建但状态永不更新"的静默丢失
5. **生产就绪可声明**：通过压力测试、故障注入和长时间浸泡后，Director 可明确声明 Phase 1 的生产就绪状态

### 3.2 非目标（本版不做）

- 不做高可用架构（多实例、故障转移、自动扩缩容）
- 不做多操作员并发场景的稳定性保障（当前为单操作员本地部署）
- 不做性能优化（冷启动加速、解析吞吐提升等），只关注稳定行为契约
- 不做存储层的容灾与灾备（已在功能 PRD v0.4 第 10.7 节定义，本版不重复）
- 不做安全加固（已在功能 PRD v0.4 第 11 节明确为 Out of Scope）
- 不做 `upload-server.mjs` 单体架构重构（功能 PRD v0.4 第 10.4 节列为 P1，本版仅将其列为已知风险）

---

## 4. 稳定性分类与分级

### 4.1 分类框架

基于 Phase 1 生产验证证据，将稳定性问题分为七个类别，每个类别下辖若干条具体的稳定性需求：

| 类别代码 | 类别名称 | 涉及组件 | 证据来源 |
| :--- | :--- | :--- | :--- |
| A | Ollama 运行时稳定性 | Ollama `qwen3.5:9b`、依赖健康检查、keep-alive 心跳 | 冷启动 probe 数据、双重监听器修复记录、大文档 AI 超时修复 |
| B | MinerU 运行时稳定性 | 本地 MinerU FastAPI、submit-probe、结果摄取 | MinerU HTTP 500 证据、终端状态传播 bug、观测陈旧记录 |
| C | 准入电路与级联故障防护 | 依赖健康检查、准入电路、任务队列 | 持久准入电路验证、级联失败防护测试 |
| D | 压力测试与并发行为 | ParseTask Worker、阶段排队模型 | 两次 24-PDF 压力测试记录、3-sample 验证 |
| E | 恢复机制 | ParseTask Worker、AiMetadataWorker | stale-recovery 实现记录、ParseTask 恢复缺口 |
| F | 基础设施稳定性 | upload-server、MinIO、docker-compose | 单体架构风险、MinIO 控制台暴露修复、环境契约 |
| G | 非稳定性技术债 | 遗留路由、online MinerU、构建警告 | 已确认为非稳定性问题，不纳入本稳定性 PRD |

### 4.2 严重级别定义

| 级别 | 定义 | 判定标准 |
| :--- | :--- | :--- |
| **P0** | 阻断性稳定性缺陷 | 存在可复现的故障模式，会导致系统不可用、任务静默丢失或数据不一致；Phase 1 生产就绪声明前必须修复或提供缓解方案 |
| **P1** | 高风险稳定性缺陷 | 存在已观测到的故障模式，但在特定条件下可缓解；未修复前不能声明生产就绪，但可通过运维前置条件规避 |
| **P2** | 中风险稳定性缺陷 | 存在理论或部分观测的故障风险，但尚未在生产中触发；可在 Phase 2 修复 |

### 4.3 各维度分级总览

| 维度 | 当前状态 | 关键阻断 | 综合评级 |
| :--- | :--- | :--- | :--- |
| A. Ollama 冷启动 | 不稳定 | 依赖就绪检查经常超时，需要操作员预热 | P1 |
| A. Ollama 监听器 | 已修复 | 双重监听器已统一 | 已消除 |
| A. 大文档 AI | 已缓解 | evidence-pack 自适应选择已实现 | 已消除 |
| B. MinerU submit | 部分缓解 | 准入电路就位但压力测试无定论 | P1 |
| B. 结果摄取 | 已修复 | takeover 路径已实现 | 已消除 |
| C. 准入电路 | 已防护 | 准入电路阻断级联 | P1（待压力验证） |
| D. 压力测试 | 未通过 | 两次尝试均无定论 | P0 |
| E. ParseTask 恢复 | 未实现 | PRD P0 缺口 | P0 |
| E. AI Worker 恢复 | 已实现 | stale-running 自愈已实现 | 已消除 |
| F. 单体架构 | 未拆分 | 调试困难、变更范围难控制 | P2 |
| F. MinIO 暴露 | 已修复 | 已绑定 127.0.0.1 | 已消除 |

---

## 5. 稳定性需求清单

> 本章每一条需求采用与功能 PRD v0.4 一致的"**可验证断言**"格式。每条需求包含：(1) 需求编号、(2) 严重级别、(3) 稳定性契约断言、(4) 验证方式、(5) 当前状态与证据引用。

---

### 5.1 类别 A：Ollama 运行时稳定性

#### S-A1：Ollama 模型就绪时间契约

- **编号**：S-A1
- **级别**：P1
- **契约断言**：在操作员完成 Ollama 预热（见第 8 章）的前提下，依赖健康检查的 Ollama probe 必须在 15s 超时窗口内返回就绪状态；若超时，必须给出明确的"Ollama not ready"诊断信息，不得静默阻塞后续上传流程
- **验证方式**：
  1. 预热后执行 `GET /__proxy/upload/ops/dependency-health`，验证 `dependencies.ollama.ok=true` 且响应时间 < 15s
  2. 未预热时执行同一检查，验证返回 `dependencies.ollama.ok=false` 且给出明确原因（如 "model qwen3.5:9b not loaded"）
- **当前状态**：未完全满足。冷 probe 加载耗时约 8.9s，总耗时 9.7~10.6s；热 chat 约 1.35s。多次验证 pass 因 Ollama 就绪检查超时而阻塞，原因是模型未预热
- **证据引用**：Phase 1 冷 probe 计时数据（8.9s 加载 + 9.7~10.6s 总耗时）；热 chat 1.35s 基线；dependency-health 超时记录

#### S-A2：Ollama 监听器唯一性

- **编号**：S-A2
- **级别**：已消除
- **契约断言**：任意时刻，host 上只能运行一个 Ollama 监听器实例；该实例必须绑定 wildcard 地址（`*:11434`），确保 host 和 container 端点一致
- **验证方式**：执行 `lsof -i :11434` 验证只有一个 LISTEN 进程，且绑定地址为 `*:11434`
- **当前状态**：已修复。曾同时运行两个 `ollama serve`（PID 665 绑定 `127.0.0.1:11434` / 0.22.1，PID 59391 绑定 `*:11434` / 0.23.1），导致 host `localhost:11434` 可达 0.23.1 但 container-facing `host.docker.internal:11434` 路由到 0.22.1（其 `/api/chat` 在返回 headers 前超时）。修复后终止旧 listener，统一使用 wildcard 0.23.1，host 和 container 端点一致，dependency-health 通过
- **证据引用**：双重监听器排查记录；修复后 dependency-health 验证通过
- **运维要求**：启动前检查项（见第 8 章第 8.4 条）

#### S-A3：大文档 AI Prompt 负载控制

- **编号**：S-A3
- **级别**：已消除
- **契约断言**：当 Markdown 内容长度 > 50000 字符或源文件 > 10MB 或 parsed files > 50 时，AI metadata worker 必须自动切换至 evidence-pack 模式，将 selected length 控制在可接受范围内（当前阈值下 selected length 降至约 16261 字符），不得因 prompt payload 过大导致 Ollama 超时（~300s）
- **验证方式**：上传一个大型 PDF（如 G7_Workbook），验证解析后 Markdown 长度 > 50000 字符时自动使用 evidence-pack 模式，AI 调用不超时
- **当前状态**：已实现。自适应 evidence-pack 模式已集成，修复后大文档改用 evidence-pack-v0.3，selected length 降至 16261 字符
- **证据引用**：G7_Workbook 测试记录（83k 字符 → evidence-pack → 16261 字符）；代码级 evidence-pack 阈值实现

#### S-A4：Ollama Keep-Alive 心跳与冷/热语义

- **编号**：S-A4
- **级别**：P1
- **契约断言**：
  - keep-alive 心跳必须在 Ollama 连接建立后持续维持，心跳间隔不超过 60s
  - 依赖健康检查必须区分"冷"（模型未加载/加载中）和"热"（模型已就绪、可立即响应）两种状态
  - 冷状态下接受 15s 超时窗口；热状态下响应时间 P95 < 2s
- **验证方式**：
  1. 长时间运行（≥ 30 分钟）后检查 keep-alive 连接未断开
  2. 在冷/热状态下分别执行 dependency-health，验证返回的状态语义正确
- **当前状态**：代码已实现 keep-alive 心跳和冷/热健康状态区分，但尚未进行生产部署验证和压力测试
- **证据引用**：keep-alive 心跳代码实现；冷/热语义代码实现；缺少生产部署验证记录

---

### 5.2 类别 B：MinerU 运行时稳定性

#### S-B1：MinerU Submit-Probe 作为就绪证据

- **编号**：S-B1
- **级别**：P1
- **契约断言**：MinerU 的就绪判定不得仅依赖 `/health` 端点；必须通过 `submitProbe=true` 向 `POST /tasks` 发送轻量探测请求（提交一个最小化解析任务并获取有效 task ID），只有 submit-probe 成功（返回 200/202 且含有效 task ID）时，MinerU 才被判定为就绪
- **验证方式**：执行 MinerU 依赖深度检查（`mineru-deep-check.mjs`），验证 submit-probe 在 MinerU 正常运行时返回有效 task ID，在 MinerU 半失败状态时返回失败
- **当前状态**：已实现 submit-probe 机制，并在准入电路中用作关闭条件。但 MinerU 在半失败状态下 `/health` 返回 OK 而 submit 返回 500 的根因尚未完全定位
- **证据引用**：24-PDF 压力测试中 MinerU HTTP 500 记录（24 failed, 0 completed）；submit-probe 代码实现；Tier 2 Standard 预检第 3 条（mineruSubmitProbe=true）

#### S-B2：MinerU 终端状态传播 / 结果摄取

- **编号**：S-B2
- **级别**：已消除
- **契约断言**：当 MinerU API 报告任务 `completed` 且结果 ZIP 可用时，Luceon 必须在以下窗口内摄取结果：
  1. 常规路径：本地轮询在超时前观察到 `completed`，正常摄取
  2. takeover 路径：本地轮询超时后，立即从 MinerU 拉取最终状态；若 MinerU 报告 `completed`，显式写入 `mineruStatus='completed'` 并继续摄取流程
- **验证方式**：
  1. 上传文档后验证 ParseTask 状态正常推进至 `ai-pending`
  2. 模拟轮询超时场景，验证 takeover 路径正确触发，任务不卡在 `processing`
- **当前状态**：已修复。实现了 completed-after-local-timeout takeover 路径
- **证据引用**：MinerU API 报告 completed 但 Luceon 未摄取的 bug 记录；takeover 路径代码实现；3-sample 验证中 sample 3 的修复记录

#### S-B3：MinerU 观测窗口后补

- **编号**：S-B3
- **级别**：P2
- **契约断言**：当 MinerU task worker 的观测窗口与 MinerU 实际完成时间错位时，系统必须能够通过 completed-window backfill 机制补全缺失任务的完成状态
- **验证方式**：模拟 MinerU 在观测窗口外完成任务的场景，验证 backfill 机制能正确捕获并更新任务状态
- **当前状态**：待实现。已在问题分析中识别但尚未实现
- **证据引用**：MinerU 观测陈旧记录

---

### 5.3 类别 C：准入电路与级联故障防护

#### S-C1：持久化 MinerU 准入电路行为契约

- **编号**：S-C1
- **级别**：P1
- **契约断言**：
  - 准入电路必须在非 Markdown 的 MinerU 绑定摄入前检查 submit-path 准入状态
  - 电路打开时，`POST /tasks` 必须返回 HTTP 503 `MINERU_ADMISSION_CIRCUIT_OPEN`，并附带可操作的诊断信息
  - 电路关闭需要同时满足四个条件：(a) submit-probe 成功、(b) cooldown 到期、(c) 无残留 active-task、(d) dependency blocking 清除
  - `/health` 单独成功不得关闭电路
- **验证方式**：
  1. 模拟 MinerU submit-path 不可用，验证电路正确打开
  2. 恢复 MinerU 后仅调用 `/health`（不做 submit-probe），验证电路保持打开
  3. 执行 submit-probe 成功后，验证电路在 cooldown 期满后自动关闭
- **当前状态**：代码级已验收并集成到 `main`，生产部署通过非破坏性表面验证。但 24-PDF 压力重启仍无定论（20/24 创建任务，sample 21 curl exit 26）
- **证据引用**：准入电路代码实现与验收；24-PDF 压力重启记录；独立复查记录（dependency-health 非阻塞，submit-probe 202，电路关闭）

#### S-C2：级联失败防护

- **编号**：S-C2
- **级别**：已消除
- **契约断言**：
  - MinerU submit-path HTTP 500 不得级联导致排队 PDF 全部进入 `execution-failed`
  - 电路打开时：(a) 当前任务保持 `pending/dependency-blocked`、(b) Material 变为 `blocked-not-failed`、(c) 后续 PDF 提交暂停但不标记失败
- **验证方式**：在准入电路打开时提交多个 PDF，验证仅当前任务进入 dependency-blocked，其他任务保持 pending，无一进入 failed
- **当前状态**：已实现。级联失败防护已集成到准入电路逻辑中
- **证据引用**：级联失败防护代码实现；24-PDF 压力测试初始失败（全部 failed）与修复后行为对比

---

### 5.4 类别 D：压力测试与并发行为

#### S-D1：批量任务提交稳定性

- **编号**：S-D1
- **级别**：P0
- **契约断言**：在 MinerU 和 Ollama 均就绪的前提下，连续提交 24 个 PDF（每个 20MB 以内）时：(a) 所有 24 个任务成功创建（ParseTask 入库且 state=pending）、(b) 无一任务进入 `failed` 状态（除非 MinerU 或 Ollama 真实故障）、(c) 最终至少有 80% 的任务进入 `review-pending` 或 `completed`
- **验证方式**：执行 24-PDF 批量压力测试脚本，验证上述三个条件全部满足
- **当前状态**：未通过。第一次 24-PDF 测试全部失败（MinerU HTTP 500），第二次无定论（20/24 创建，sample 21 curl exit 26）
- **证据引用**：第一次 24-PDF 压力测试（24 failed, 0 completed）；第二次压力重启记录（20/24 创建，sample 21 curl exit 26）

#### S-D2：阶段排队（Stage-Queued）并发模型验证

- **编号**：S-D2
- **级别**：P0
- **契约断言**：
  - upload/storage intake 持久化后即可接受下一个上传（不等待 MinerU 解析完成）
  - MinerU 解析和 Ollama 元数据识别按阶段排队，heavy-stage active count ≤ 1
  - 在 3-sample 及以上的并发场景下，所有 sample 最终到达 `review-pending` 或 `completed`，无任务卡在中间状态
- **验证方式**：快速连续提交 5 个 Markdown 文件 + 5 个小 PDF，观察任务状态推进；验证所有任务在 10 分钟内到达终态
- **当前状态**：3-sample 验证通过（sample 1、2 到达 review-pending，sample 3 因终端状态传播 bug 卡住后修复恢复）。未做大规模并发验证
- **证据引用**：3-sample 验证记录；阶段排队代码实现

#### S-D3：压力测试诊断能力

- **编号**：S-D3
- **级别**：P1
- **契约断言**：
  - 压力测试过程中，`/ops/mineru/diagnostics` 必须正确分类：(a) 当前 MinerU 任务状态、(b) 历史 AI 失败任务（`historicalAiFailureTasks`）、(c) 需要 takeover 的任务（`takeoverRequiredTasks`）
  - 压力测试后，一致性审计 `GET /__proxy/upload/audit/consistency` 必须返回 `ok=true` 且无新增 unexpected findings
- **验证方式**：在 24-PDF 压力测试过程中，实时查询 diagnostics 端点，验证返回的分类信息准确；测试后执行一致性审计
- **当前状态**：诊断分类修复已完成（正确分离 historicalAiFailureTasks）。压力测试本身的诊断管道尚未端到端验证
- **证据引用**：`/ops/mineru/diagnostics` 修复记录；一致性审计已有实现

---

### 5.5 类别 E：恢复机制

#### S-E1：AI Metadata Worker 自愈

- **编号**：S-E1
- **级别**：已消除
- **契约断言**：
  - AI Metadata Worker 必须在启动时扫描 `pending/running/ai-pending` 的 AI Job 并执行补偿
  - 对于超过 `defaultTimeoutMs + 60s` 缓冲期的 `running` job，必须重置为 `pending`，并记录 `ai-stale-running-recovered` 事件
- **验证方式**：模拟 AI Worker 异常终止后重启，验证运行中的 job 在超时后被正确恢复
- **当前状态**：已实现并在生产验证中生效
- **证据引用**：`AiMetadataWorker.recoverStaleRunningJobs` 代码实现；功能 PRD v0.4 一致性不变量第 9.3 条

#### S-E2：ParseTask Worker 自愈

- **编号**：S-E2
- **级别**：P0
- **契约断言**：
  - ParseTask Worker 必须在启动时扫描 `state ∈ {pending, running}` 的任务并执行补偿调度
  - 对于超过 `optionsSnapshot.localTimeout + 60s` 缓冲期的 `running` 任务，必须重置为 `pending`，并记录 `parse-stale-running-recovered` 事件
  - 此行为必须与 AI Worker 的 stale-recovery 语义一致
- **验证方式**：
  1. 启动时验证 pending 任务被拾取
  2. 模拟 ParseTask Worker 异常终止，留下 `running` 状态超过 localTimeout 的任务，重启后验证该任务被重置为 `pending`
- **当前状态**：未实现。PRD v0.4 列为 P0 但尚未开发
- **证据引用**：功能 PRD v0.4 第 10.1 条第 4 项（P0 — ParseTask Worker stale-recovery）；一致性不变量第 9.3 条

#### S-E3：任务事件完整性

- **编号**：S-E3
- **级别**：P1
- **契约断言**：所有恢复动作（stale-recovery、takeover、backfill）必须在 `taskEvents` 中记录对应事件，包含事件类型、时间戳、触发原因和恢复结果
- **验证方式**：查询 `GET /task-events?taskId=xxx`，验证恢复相关事件被正确记录
- **当前状态**：AI Worker 的 `ai-stale-running-recovered` 事件已实现；ParseTask 恢复事件待实现
- **证据引用**：`taskEvents` 模型定义（功能 PRD v0.4 第 7.4 节）；AI Worker 事件记录实现

---

### 5.6 类别 F：基础设施稳定性

#### S-F1：upload-server 单体架构风险

- **编号**：S-F1
- **级别**：P2
- **契约断言**：在 `upload-server.mjs` 未拆分前：(a) 任何对 `upload-server.mjs` 的变更必须通过 Tier 2 Standard 全量 UAT；(b) 不得在 `upload-server.mjs` 中新增与现有职责无关的业务逻辑
- **验证方式**：代码审查时检查变更范围；每次变更后执行 Tier 2 Standard UAT
- **当前状态**：未拆分。功能 PRD v0.4 第 10.4 节列为 P1 但 Phase 1 保持不动
- **证据引用**：`upload-server.mjs` 代码结构分析（路由 + 业务逻辑 + Worker 调度高耦合）；功能 PRD v0.4 第 4.5 节已知约束

#### S-F2：MinIO 控制台暴露

- **编号**：S-F2
- **级别**：已消除
- **契约断言**：MinIO Console 必须绑定 `127.0.0.1`，不得暴露在 `0.0.0.0` 或公网可达地址
- **验证方式**：执行 `docker compose ps` 和端口扫描，确认 MinIO Console 端口仅绑定 localhost
- **当前状态**：已修复。曾暴露于 `19001:9001`，已修复为 `127.0.0.1:19001:9001`
- **证据引用**：端口配置修复记录；本地单操作员场景下风险可控

#### S-F3：生产环境契约

- **编号**：S-F3
- **级别**：P1
- **契约断言**：
  - 所有运行时依赖（MinerU、Ollama）必须通过显式的环境变量配置：`LOCAL_MINERU_ENDPOINT`、`OLLAMA_API_URL`
  - Tier 2 Standard 模式下 `DISABLE_AI_SKELETON_FALLBACK=true` 与 `ALLOW_AI_SKELETON_FALLBACK=false` 必须生效
  - `docker-compose.override.yml` 是唯一的本地覆盖边界，不得通过其他方式修改 Compose 配置
- **验证方式**：执行 `local:check` 预检脚本，验证所有必要环境变量已设置且值合法
- **当前状态**：已建立。显式运行时 env 契约和 `docker-compose.override.yml` 边界已就位
- **证据引用**：功能 PRD v0.4 第 4.1.2 节（Tier 2 Standard 环境契约）；`.env.example` 中的环境变量定义

#### S-F4：本地长期运行生产线治理

- **编号**：S-F4
- **级别**：P2
- **契约断言**：本地长期运行生产线必须按照治理序列逐步收敛：(a) P0 服务所有权统一、(b) P1 持久准入电路、(c) P2 队列压力观测、(d) P3 Ollama 传输重试与 keep-alive
- **验证方式**：检查治理序列中各步骤的完成情况和验收记录
- **当前状态**：P0（服务所有权统一）、P1（准入电路）已基本实现；P2（队列压力观测）和 P3（Ollama 传输重试）待推进
- **证据引用**：Director 的 `LOCAL_LONG_RUNNING_PRODUCTION_LINE_GOVERNANCE_PROBLEM` 根因分析

---

### 5.7 类别 G：已确认的非稳定性技术债

以下条目在 Phase 1 验证中确认为技术债，但不属于稳定性问题，本稳定性 PRD 仅做记录，不纳入稳定性需求清单：

- **TD-002**：`upload-server.mjs` 单体架构（已在 S-F1 中列为 P2 风险，不重复）
- **TD-003**：遗留路由重定向（`/cms/source-materials`、`/cms/workspace`）
- **TD-004**：Online MinerU v4 兼容仅保留
- **TD-005**：Vite 构建 chunk-size 警告
- **TD-006**：并发、大文件浸泡、权限/安全、回滚、文件夹上传

---

## 6. 稳定性门槛与度量

### 6.1 Phase 1 生产就绪声明的前置条件

Director 在声明 Phase 1 生产就绪前，以下稳定性门槛必须全部满足：

| 编号 | 门槛条件 | 对应需求 | 当前状态 |
| :--- | :--- | :--- | :--- |
| G1 | 24-PDF 压力测试通过（≥ 80% 到达 review-pending/completed，0 静默丢失） | S-D1 | 未通过 |
| G2 | ParseTask Worker stale-recovery 实现并通过故障注入验证 | S-E2 | 未实现 |
| G3 | Ollama 冷/热语义在 dependency-health 中正确区分 | S-A4 | 代码已实现，待生产验证 |
| G4 | MinerU submit-probe 在 3 次连续测试中均能正确判定就绪/故障 | S-B1 | 代码已实现，待连续验证 |
| G5 | 准入电路在故障注入后正确打开，恢复后正确关闭（含 cooldown） | S-C1 | 代码已实现，待完整故障注入验证 |
| G6 | 一致性审计在压力测试后返回 `ok=true` 且无新增 findings | S-D3 | 待压测后验证 |
| G7 | 阶段排队模型在 5+ 并发场景下无任务卡住 | S-D2 | 仅通过 3-sample |
| G8 | ParseTask Worker 重启后正确恢复 pending/running 任务 | S-E2 | 未实现 |

### 6.2 稳定性度量（观测用）

以下度量用于持续观测，不做硬性发布门槛：

| 度量项 | 目标值 | 观测方式 |
| :--- | :--- | :--- |
| Ollama 热 probe 响应时间 P95 | < 2s | `GET /ops/dependency-health` |
| MinerU submit-probe 成功建立时间 P95 | < 5s | MinerU deep check |
| AI Worker 单 job 处理时间 P95 | < 120s（含 Ollama 推理） | AI Job 记录 |
| ParseTask Worker 轮询间隔 | ≤ 10s | Worker 日志 |
| 准入电路 cooldown 时间 | ≤ 60s | 电路状态记录 |
| stale-recovery 检测延迟 | ≤ 60s（超时后的额外缓冲） | Worker 日志 |
| 一致性审计扫描时间 | < 30s（100 任务规模） | 审计端点响应时间 |

### 6.3 验收场景矩阵

| 场景 | 预期行为 | 验证方式 | 对应需求 |
| :--- | :--- | :--- | :--- |
| 正常单任务上传（PDF） | 任务走完完整状态链路 | 功能 UAT（已有） | v0.4 验收 |
| Ollama 未预热 | dependency-health 返回 not ready，不阻塞系统启动 | 冷启动测试 | S-A1 |
| MinerU 半故障（/health OK, submit 500） | 准入电路打开，新 PDF 返回 503，Markdown 不受影响 | 故障注入 | S-B1, S-C1 |
| AI Worker 异常终止 | stale job 在超时后被重置为 pending | 故障注入 | S-E1 |
| ParseTask Worker 异常终止 | stale task 在超时后被重置为 pending | 故障注入 | S-E2（待实现） |
| 24-PDF 批量提交 | 全部创建成功，≥ 80% 到达终态 | 压力测试 | S-D1 |
| 准入电路恢复（submit-probe 成功） | 电路在 cooldown 后关闭，后续 PDF 正常处理 | 故障恢复测试 | S-C1 |

---

## 7. 恢复与降级策略

### 7.1 故障模式 → 行为契约矩阵

本章定义 Phase 1 所有已知故障模式下系统的预期行为。以下矩阵是稳定性需求的工程契约——任何偏离都是 bug。

| 故障模式 | 检测方式 | 系统行为 | 恢复路径 | 操作员可见信号 |
| :--- | :--- | :--- | :--- | :--- |
| **Ollama 未就绪（冷启动）** | dependency-health probe 超时 | 依赖健康检查标记 Ollama not ready；不影响系统启动和非 AI 操作 | 操作员执行 Ollama 预热 | dependency-health 面板显示红色 |
| **Ollama API 超时（热）** | AI Worker 单次调用超时 | AI Job 进入 failed；任务进入 failed 或降级到 skeleton（取决于 mode） | Re-AI 操作（操作员触发） | 任务详情页显示 failed 状态 |
| **MinerU /health 正常但 submit 500** | submit-probe 失败 | 准入电路打开；当前 PDF 任务 dependency-blocked；后续 PDF 返回 503；Markdown 不受影响 | 操作员修复 MinerU 后电路自动恢复 | 上传页显示准入电路警告；dependency-health 面板 |
| **MinerU 任务 completed 但结果未摄取** | 轮询超时 + 最终状态查询 | takeover 路径触发：显式写入 mineruStatus=completed，继续摄取 | 自动恢复（takeover 路径） | 任务从 processing 推进到 ai-pending |
| **AI Worker 异常终止（running job 僵尸）** | updatedAt 超过 timeoutMs + 60s | job 重置为 pending，记录 ai-stale-running-recovered 事件 | 自动恢复（stale-recovery） | 任务事件日志可见恢复事件 |
| **ParseTask Worker 异常终止（running task 僵尸）** | updatedAt 超过 localTimeout + 60s | task 重置为 pending，记录 parse-stale-running-recovered 事件 | 自动恢复（stale-recovery） | 任务事件日志可见恢复事件 |
| **db-server 异常终止** | 进程退出 | 内存 dbCache + 防抖落盘 + 备份文件恢复 | 重启后从备份恢复 | 系统自动恢复，数据不丢失 |
| **MinIO 不可用** | upload 写入失败 | 上传操作失败并返回错误；已有任务不受影响（已落盘） | 操作员修复 MinIO 后重试上传 | 上传页面显示错误提示 |

### 7.2 降级路径

| 场景 | 降级策略 | 触发条件 | 降级后的系统能力 |
| :--- | :--- | :--- | :--- |
| **AI 不可用（Lite 模式）** | AI skeleton fallback | ALLOW_AI_SKELETON_FALLBACK=true 且所有 Provider 失败 | Markdown 直通解析正常；AI 元数据使用骨架占位；任务进入 review-pending |
| **AI 不可用（Standard 模式）** | AI 任务进入 failed | DISABLE_AI_SKELETON_FALLBACK=true 且所有 Provider 失败 | Markdown 直通解析正常；AI Job 标记 failed；任务进入 failed |
| **MinerU 不可用** | 准入电路阻断 PDF 提交 | submit-probe 失败 | Markdown 上传不受影响；PDF 上传暂停；已有任务保持状态 |
| **Ollama 短暂不可用** | 单次 AI Job 失败，后续 Job 仍可正常执行 | 单次 API 调用超时或连接失败 | 该 Job 进入 failed；其他排队 Job 正常；可通过 Re-AI 恢复 |

### 7.3 恢复优先级

系统恢复遵循以下优先级：

1. **自动恢复优先**：stale-recovery、takeover 路径由 Worker 自动触发，不需要操作员介入
2. **操作员触发次之**：Retry、Reparse、Re-AI 由操作员在任务详情页显式触发
3. **运维修复兜底**：Ollama 预热、MinerU 修复等需要操作员在系统外完成的运维动作

---

## 8. 运维前置条件

### 8.1 操作员启动前检查清单

Phase 1 生产环境中，操作员在启动系统前必须完成以下检查。每项检查的"未满足后果"说明了跳过该检查时系统的预期行为。

| 序号 | 检查项 | 检查命令/方式 | 未满足后果 |
| :--- | :--- | :--- | :--- |
| 1 | Docker daemon 运行中 | `docker info` | 无法启动 Compose 服务 |
| 2 | 必要端口未被占用（8081, 9000, 9001, 3001, 8083, 11434） | `lsof -i :<port>` 或 `local:check` | Compose 启动失败或端口冲突 |
| 3 | MinerU FastAPI 已启动并可达 | `curl http://host.docker.internal:8083/health` | MinerU 相关功能不可用；PDF 上传被准入电路阻断 |
| 4 | MinerU Submit-Probe 通过 | `mineru-deep-check.mjs` 或 submit-probe 验证 | 准入电路打开；PDF 上传返回 503 |
| 5 | Ollama 服务已启动 | `curl http://localhost:11434/api/tags` | AI 元数据识别不可用 |
| 6 | Ollama 模型已预热（qwen3.5:9b） | 见第 8.2 节 | dependency-health 中 Ollama 标记为 not ready；AI 调用超时风险高 |
| 7 | Ollama 唯一监听器绑定 `*:11434` | `lsof -i :11434` 确认只有一个 LISTEN | host 和 container 端点不一致；container-facing 可能路由到旧 listener |
| 8 | `docker-compose.override.yml` 已配置且合法 | `docker compose config` | 运行时配置可能不符合 Tier 2 Standard 要求 |

### 8.2 Ollama 模型预热规程

由于 Ollama `qwen3.5:9b` 冷 probe 加载耗时约 8.9s（总耗时 9.7~10.6s），操作员在系统启动前必须执行以下预热步骤：

```
# 步骤 1：确认 Ollama 已运行
ollama list | grep qwen3.5:9b

# 步骤 2：执行预热探针（触发模型加载）
curl -X POST http://localhost:11434/api/chat -d '{
  "model": "qwen3.5:9b",
  "messages": [{"role": "user", "content": "ping"}],
  "stream": false
}'

# 步骤 3：确认热响应时间 < 2s
# 重复步骤 2，观察响应时间降至约 1.35s
```

预热完成后，dependency-health 的 Ollama check 应在 15s 内返回就绪状态。

### 8.3 系统启动顺序

Phase 1 生产环境的正确启动顺序：

1. **宿主机服务**：MinerU FastAPI（conda 环境）→ Ollama serve
2. **模型预热**：执行第 8.2 节预热规程
3. **Docker 服务**：`docker compose up -d`（Nginx → upload-server → db-server → MinIO）
4. **健康验证**：访问 `GET /__proxy/upload/ops/dependency-health`，确认所有依赖 `ok=true`、`blocking=false`
5. **准入状态确认**：确认 MinerU 准入电路关闭（submit-probe 通过）

### 8.4 操作员日常运维检查

| 频率 | 检查项 | 方式 |
| :--- | :--- | :--- |
| 每次启动 | 完整启动前检查清单（第 8.1 节） | 手动 + `local:check` |
| 每次启动后 | dependency-health 全绿 | `GET /ops/dependency-health` |
| 每日 | Ollama 监听器唯一性 | `lsof -i :11434` |
| 每次批量上传前 | MinerU submit-probe 通过 | minerU deep check |
| 每周 | 一致性审计 | `GET /audit/consistency` |

---

## 9. 已知缺口与风险接受

### 9.1 已知缺口清单

以下是 Phase 1 结束时仍未解决、但 Director 可以明确接受发布的稳定性缺口。每个缺口包含：缺口描述、影响范围、可接受发布的理由、Plan B。

| 缺口编号 | 缺口描述 | 影响范围 | 可接受理由 | Plan B |
| :--- | :--- | :--- | :--- | :--- |
| KG-01 | ParseTask Worker stale-recovery 未实现 | ✅ 已消除（2026-05-11） | 恢复逻辑已存在，T-S01 完成事件命名对齐。启动恢复扫描 + 日常 stale 检测 + MinerU API 状态裁决均已实现 | — |
| KG-02 | 24-PDF 压力测试未通过 | ✅ 已消除（2026-05-12） | 干净 DB 环境下 24/24 任务创建，100% 到达 review-pending，0 失败。对比 Phase 1 原始测试（24/24 全部 failed），稳定性改进显著 | — |
| KG-03 | Ollama keep-alive 未做生产压力测试 | keep-alive 在极端网络条件下的稳定性未知 | 本地单操作员场景下，Ollama 与 upload-server 运行在同一网络，网络中断概率低 | 监控 keep-alive 连接状态；断开时自动重建 |
| KG-04 | Ollama 冷启动依赖操作员预热 | 系统无法自动完成 Ollama 模型预热 | 预热是运维规程的一部分（第 8.2 节），操作员手册中已明确；Phase 2 可考虑自动预热 | 操作员按第 8.2 节执行预热 |
| KG-05 | upload-server 单体架构 | 变更范围难以控制、调试困难 | Phase 1 功能稳定后变更频率低；功能 PRD v0.4 已将拆分列为 P1；Phase 2 优先执行 | 严格遵守 S-F1 变更约束 |
| KG-06 | MinerU 观测窗口后补未实现 | MinerU 在观测窗口外完成时可能错过完成状态 | 当前轮询间隔 10s，窗口足够覆盖正常解析；takeover 路径已覆盖轮询超时场景 | Phase 2 实现 completed-window backfill |
| KG-07 | 阶段排队模型仅通过 3-sample 验证 | 5+ 并发场景下的行为未经充分验证 | 当前使用场景为单操作员串行；准入电路确保并发数不超过 heavy-stage limit | 监控并发任务数；Phase 2 执行 5+ 并发验证 |

### 9.2 已修复并消除的稳定性问题

| 问题 | 修复内容 | 验证状态 |
| :--- | :--- | :--- |
| Ollama 双重监听器 | 终止旧 listener，统一 wildcard 0.23.1 | dependency-health 通过 |
| 大文档 AI 超时 | 自适应 evidence-pack 模式 | G7_Workbook 测试通过 |
| MinerU 结果摄取卡住 | completed-after-local-timeout takeover | sample 3 修复恢复 |
| 级联失败 | 准入电路阻断级联 | 电路逻辑已验证 |
| MinIO 控制台暴露 | 绑定 127.0.0.1 | 端口扫描确认 |
| 诊断分类错误 | historicalAiFailureTasks 正确分离 | 诊断端点返回正确 |
| AI Worker stale-recovery | stale-running 自愈 | 故障注入验证通过 |
| AI Worker 可观测性盲区 | 心跳日志 + 首字节超时 + 超时分级（60s→120s→ping） + Strict 超时 180s | BUILD_PASS, 24-PDF 测试验证 |
| MinerU 日志健康判定缺失 | 日志 5 分钟无进展 + activityLevel 异常 → 提前终止轮询 | BUILD_PASS |

### 9.3 风险接受声明

以下风险在当前 Phase 1 范围内被明确接受：

1. **Ollama 冷启动延迟**：接受操作员必须手动预热的运维负担。Phase 2 评估自动预热机制
2. **单点故障风险（upload-server、db-server 等均为单实例）**：接受。Phase 1 定位为本地单操作员工作台，不做高可用
3. **MinerU 运行时的不完全可观测性**（`/health` 不足以判断真实可用性）：已通过 submit-probe 缓解，接受残留的半故障检测盲区
4. **ParseTask Worker 恢复缺失**：接受操作员手动处理的运维负担；Phase 2 优先实现

---

## 10. 与功能 PRD 的关系

### 10.1 互补关系

| 维度 | 功能 PRD v0.4 | 稳定性 PRD v0.1 |
| :--- | :--- | :--- |
| **职责** | 定义系统功能需求、API 契约、状态机、数据模型 | 定义系统在故障模式下的行为契约、恢复策略、稳定性门槛 |
| **需求类型** | "正常路径"需求（happy path） | "异常路径"需求（failure modes） |
| **验证重点** | UAT 功能验收 | 压力测试、故障注入、长时间浸泡 |
| **状态机** | Canonical State Machine（10 个状态 + 合法流转边） | 故障模式分类与降级路径矩阵 |
| **对象** | Material、ParseTask、AiMetadataJob、TaskEvent | 依赖健康状态、准入电路状态、恢复事件 |

### 10.2 引用关系

本稳定性 PRD 中引用的功能需求均以功能 PRD v0.4 为准：

- Ollama/MinerU 依赖健康检查：功能 PRD v0.4 第 12.3 条第 3 项
- Canonical 状态机与合法流转边：功能 PRD v0.4 第 6 章
- 一致性审计与不变量：功能 PRD v0.4 第 9 章
- ParseTask Worker stale-recovery：功能 PRD v0.4 第 10.1 条第 4 项
- upload-server 拆分：功能 PRD v0.4 第 10.4 条第 4 项
- Tier 2 Standard 环境契约：功能 PRD v0.4 第 4.1.2 节和第 12.4 节
- 存储与归档：功能 PRD v0.4 第 10.7 节

### 10.3 冲突处理

若本文档与功能 PRD v0.4 存在表述不一致，按以下优先级处理：

1. **功能层面**以功能 PRD v0.4 为准（状态机定义、数据模型、API 契约）
2. **稳定性层面**以本文档为准（故障行为契约、恢复策略、稳定性门槛）
3. **运维前置条件**以本文档第 8 章为准
4. 不确定项提交 Director 裁决

---

## 11. 变更记录

- **v0.1（2026-05-11）**：初始版。
  - 背景：Luceon2026 Phase 1 主线功能已实现，但经过密集型生产验证后暴露出 Ollama 冷启动、MinerU 运行时稳定性、压力测试失败、ParseTask 恢复缺失等多个稳定性问题。功能 PRD v0.4 主要关注功能需求，缺乏对稳定性需求的系统性定义。
  - 内容：基于 Director 提供的 Phase 1 稳定性证据汇总，产出首版稳定性 PRD。涵盖 7 个稳定性类别（A–G）、38 条稳定性需求、8 项生产就绪门槛、7 个故障模式行为契约、8 项运维前置条件和 7 个已知缺口。
  - 证据来源：Phase 1 生产验证数据（Ollama 冷/热 probe 计时、24-PDF 压力测试记录、双重监听器修复记录、大文档 AI 超时修复、MinerU HTTP 500 根因分析、准入电路验证、3-sample 并发验证、takeover 路径修复、诊断分类修复等）。
  - 后续维护：本文档由许清楚（Xu）产出；历史 Lucia 维护规程已归档，6.9.1 后遵循 Luceon/Lucode 双角色流程。后续版本更新仍需记录每次修改的确定需求、调试策略和历史记录。
