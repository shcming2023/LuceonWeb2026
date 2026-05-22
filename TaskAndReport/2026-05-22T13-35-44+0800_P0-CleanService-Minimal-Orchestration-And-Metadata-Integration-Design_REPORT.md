# TASK-20260522-133544-P0-CleanService-Minimal-Orchestration-And-Metadata-Integration-Design REPORT

## 1. 交付摘要 (Delivery Summary)

本报告为 **Task 247** 的 `docs/design-only` 任务交付报告。
我们已严格按照 **Luceon2026 双特工本地协同契约** 的 SOP 管线，完成了针对 Luceon 最小 Mineru2Table 编排与元数据接入的实现级设计。
本交付成果不仅深入审计了现有代码基，还针对 Task 242 false-success、Task 245/246 的 `v2` 产物证据，构建了包括 7 件套 MinIO 对象内容拉取、Token 校验、Provenance 输入哈希匹配、以及针对 `size_bytes=0` 的本地体积补偿机制在内的“硬护栏”门控设计。

---

## 2. 交付与分支固化信息

* **交付分支 (Delivery Branch)**: `lucode/TASK-20260522-133544`
* **最终 Commit SHA (HEAD SHA)**: ecd0021
* **变更文件列表 (Changed Files)**:
  - **[DESIGN.md](file:///workspace/dev/Luceon2026/TaskAndReport/2026-05-22T13-35-44+0800_P0-CleanService-Minimal-Orchestration-And-Metadata-Integration-Design_DESIGN.md)** (实现级设计说明书)
  - **[REPORT.md](file:///workspace/dev/Luceon2026/TaskAndReport/2026-05-22T13-35-44+0800_P0-CleanService-Minimal-Orchestration-And-Metadata-Integration-Design_REPORT.md)** (本交付报告)
  - **[TASK_TRACKING_LIST.md](file:///workspace/dev/Luceon2026/TaskAndReport/TASK_TRACKING_LIST.md)** (台账更新)

---

## 3. 只读证据审计来源 (Read-Only Evidence Sources)

在设计过程中，本特工仅以**只读**方式，深度参考了以下契约与事实文件，未对它们做任何修改：
1. **[CleanService-Protocol-v1.md](file:///workspace/dev/Luceon2026/docs/contracts/CleanService-Protocol-v1.md)**: 详细审计了 Payload 结构、Error 状态以及 Isolation 策略。
2. **[output-verifier.mjs](file:///workspace/dev/Luceon2026/server/services/cleanservice/output-verifier.mjs)**: 审计了现有验证逻辑的缺陷，找到了 metrics 与 7 件套缺失的 Gap。
3. **[asset-version.mjs](file:///workspace/dev/Luceon2026/server/services/cleanservice/asset-version.mjs)**: 审计了版本分配与排除逻辑。
4. **[cleanservice-worker.mjs](file:///workspace/dev/Luceon2026/server/services/cleanservice/cleanservice-worker.mjs)**: 审计了 Worker 状态检查与资格准入流程。
5. **历史 Task 242/245/246 运行报告**: 审计了 `v2` 成功产物证据与 LLM 401 失败现象，将其归纳为设计的门控前置条件。

---

## 4. 安全治理与边界承诺声明

本特工郑重声明：
> [!IMPORTANT]
> **【零变动、零侵入、零污染承诺】**
> 1. 本次任务期间，**未修改任何业务或运行态代码**（`server/**` 和 `src/**` 绝对保持原样，无任何代码改动）。
> 2. **未进行任何运行态或数据 Mutation 变动**：绝对没有调用 `POST /api/v1/jobs`，没有 LLM 调用，没有对 MinIO 对象执行写入/删除/移动/清理，没有 DB 写入，也未进行任何 Docker 重建、down 或 restart 动作。
> 3. 绝对保持了开发容器和生产工作区的强隔离，控制面行为 100% 绿色、安全。

---

## 5. 针对下一阶段实现的最终建议 (Final Recommendation)

鉴于目前 `output-verifier.mjs` 中对 7 件套校验的明显缺失，我们强烈建议：
* **下一阶段首要卡片**: 立即着手开发 **Card 2 (7 件套 MinIO 拉取与 Token 硬校验门控)**。
* **开发策略**:
  - 只有在验证器能够安全读取 MinIO 并能彻底防御虚假的 completed 状态后，才能开启 Card 1 (手动触发 API) 的对接。
  - 通过优先构建坚固的“安全哨所”（校验器），确保在引入真正的服务编排时，Luceon 能够在第一时间拦截任何潜在的上游故障或非预期产物。
* **控制权交接**:
  - 状态已在台账中标记为 `Ready for luceon Review`。
  - Next Actor 设为 `luceon`。
  - 交付分支已固化最终 Commit，控制权在此移交！
