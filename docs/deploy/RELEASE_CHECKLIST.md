# Luceon2026 v6.9.x 上线发布收口计划（Checklist 模板）

本文件是 Luceon2026 项目 v6.9.x 版本上线收口的官方标准 Checklist。上线相关工作分为 **Stage 0** 至 **Stage 7** 共 8 个阶段，每个阶段包含明确的**准入门槛**、**测试/核查动作**、**通过判据**和**证据产物**。

测试部门将基于本模板（即 Issue #9 验收台账）对每一次发布进行逐项核签并归档证据。

---

## ▌ 版本基础元信息（发布前填报）

| 填报字段 | 实际填报内容（示例与回填项） | 填报要求说明 |
| :--- | :--- | :--- |
| **上线版本号** | `v6.9.0-rc1` (当前示范) | 格式通常为 `v6.9.x-rcX` |
| **Git 发布分支** | `release/6.9.x` (当前已冻结) | 严禁直接 Push 任意提交 |
| **锁定 Git HEAD** | `[回填 Commit Hash, 如 e30adad9]` | Stage 0 阶段最终确认的 SHA |
| **发布责任人 (Dev/Ops)**| `[回填 负责人姓名]` | 生产/运维 + 开发联合负责人 |
| **验收责任人 (Test)** | `[回填 验收人姓名]` | 测试部门联合签字验收人 |
| **最终合并 PR 链接** | `[回填 PR URL, 如 #8]` | 必须包含 "Closes #8" 描述 |

### 镜像构建产物 Digest 签名回填表

镜像推送至私有仓库后，请回填以下 Digest 信息（以确保生产部署镜像的唯一与安全性）：

-   **Nginx 前端镜像 (`cms-frontend`)**
    -   *Tag*: `shcming2023/luceon-frontend:6.9.0-rc1` *(注: 属于占位镜像名，待 Stage 1 任务确立规范后统一正式回填)*
    -   *Digest*: `sha256:7f9a8b8c8d8e...[回填实际 Digest]`
-   **后端上传服务 (`upload-server`)**
    -   *Tag*: `shcming2023/luceon-upload-server:6.9.0-rc1` *(注: 属于占位镜像名，待 Stage 1 任务确立规范后统一正式回填)*
    -   *Digest*: `sha256:4a3b2c1d0e9f...[回填实际 Digest]`
-   **JSON 数据库服务 (`db-server`)**
    -   *Tag*: `shcming2023/luceon-db-server:6.9.0-rc1` *(注: 属于占位镜像名，待 Stage 1 任务确立规范后统一正式回填)*
    -   *Digest*: `sha256:9f8e7d6c5b4a...[回填实际 Digest]`
-   **私有对象存储 (`minio`)**
    -   *Tag*: `minio/minio:RELEASE.2024-04-18T19-09-00Z`
    -   *Digest*: `sha256:de1234567890...[回填实际 Digest]`

---

## ▌ 8 阶段收口计划 Checklist

### Stage 0: 代码冻结与分支管控 (Code Freeze & Branch Protection)

*   **阶段目标**: 锁定发布包的代码基础，严格保护核心发布分支，防止非授权变更流向生产环境。
*   **本阶段责任人**: `[开发部门负责人]`

| 序号 | 核查子项 | 准入门槛 | 测试/核查动作 | 通过判据 | 证据产物 | 状态 |
| :---: | :--- | :--- | :--- | :--- | :--- | :---: |
| 0.1 | **分支保护生效** | 所有 Phase 1 需求开发完成，代码合入 `main`。 | 1. 确认已在 GitHub 仓库开启 `release/6.9.x` 分支的保护规则（Branch Protection Rules）。<br>2. 限制直推，强制要求 PR 与 Review。 | 直接向该分支执行 `git push` 被拒绝拦截。 | 截图或命令行拦截日志 | - [ ] |
| 0.2 | **锁定 Git HEAD** | 所有最后修复 PR 已合入。 | 1. 在 `codex/release-checklist-skeleton` 上检出最终 HEAD commit 校验和。<br>2. 登记至元信息表。 | Git HEAD 锁定，无脏工作区，远端与本地完全一致。 | `git log -1` 命令行输出 | - [ ] |

> [!NOTE]
> **本阶段必须交付产物**: `TaskAndReport/Stage0-EVIDENCE.md` （记录锁定 Commit ID 及分支保护证明）。

---

### Stage 1: 依赖安全与静态构建预检 (Dependency Audit & Build Preflight)

*   **阶段目标**: 阻断带有已知漏洞的依赖包合入，并确保代码在静态编译与契约核实层级完全一致。
*   **本阶段责任人**: `[开发工程师]`

| 序号 | 核查子项 | 准入门槛 | 测试/核查动作 | 通过判据 | 证据产物 | 状态 |
| :---: | :--- | :--- | :--- | :--- | :--- | :---: |
| 1.1 | **依赖安全扫描** | Stage 0 通过。 | 在根目录运行依赖安全性扫描命令，校验本地包依赖树。 | 零严重漏洞（Critical Vulnerabilities）及高风险漏洞报告。 | 扫描工具（如 pnpm audit）命令行日志 | - [ ] |
| 1.2 | **静态编译无错** | 静态扫描通过。 | 在根目录执行静态类型检查及打包命令：<br>`npx tsc --noEmit` && `pnpm build` | 编译过程无 `TypeError`、未定义引用或构建脚本异常，顺利输出 `dist/`。 | 打包构建命令输出的日志文本 | - [ ] |
| 1.3 | **配置契约匹配** | 本地打包成功。 | 逐项核对 `.env.example` 与各 `docker-compose.*.yml` 的端口、数据卷映射、公共端点契约匹配性，消除遗漏。 | 没有出现遗漏的环境变量，对外端口配置和代理路由一一对应。 | 配置对比记录 | - [ ] |
| 1.4 | **无损预检测试** | 配置契约核对完成。 | 在开发工作区中运行只读预检脚本：<br>`bash ops/runtime-ownership-status.sh` | 预检输出中除了 MinerU submit-path 外的所有内部依赖与端口监听显示为已运行可用。 | 预检脚本的控制台输出摘要 | - [ ] |

> [!NOTE]
> **本阶段必须交付产物**: `TaskAndReport/Stage1-EVIDENCE.md` （包含包安全性、`tsc` 编译通过证据以及契约匹配确认）。

---

### Stage 2: 镜像安全构建与签名声明 (Docker Build & Image Signatures)

*   **阶段目标**: 生成完全可追溯的二进制容器构建镜像，并在 Check 列表中对镜像的唯一签名进行确信固化。
*   **本阶段责任人**: `[生产运维工程师]`

| 序号 | 核查子项 | 准入门槛 | 测试/核查动作 | 通过判据 | 证据产物 | 状态 |
| :---: | :--- | :--- | :--- | :--- | :--- | :---: |
| 2.1 | **无缓存构建** | Stage 1 通过。 | 运行无缓存干净构建：<br>`docker compose build --no-cache` | 所有微服务容器镜像（frontend/upload/db）构建成功，无 Native 构建报错。 | Docker 干净构建终端日志 | - [ ] |
| 2.2 | **签收 Digest** | 所有镜像构建完毕。 | 运行 `docker images --digests` 或者是推送私有镜像仓库后提取各服务镜像唯一的 `sha256` 签名。 | 成功获取四大组件的完整 SHA256 digest 签名，并准确登记在基础信息表中。 | 本 Checklist 头部镜像 Digest 登记 | - [ ] |

> [!NOTE]
> **本阶段必须交付产物**: `TaskAndReport/Stage2-EVIDENCE.md` （记录 Docker 无缓存打包记录以及 4 个基础镜像的 digest 详情）。

---

### Stage 3: 灰度环境拉起与常规冒烟测试 (Staging Deploy & Smoke Verification)

*   **阶段目标**: 在受控的灰度/UAT 环境中拉起基于 Stage 2 镜像的整套服务，以自动化冒烟验证全链路联通性。
*   **本阶段责任人**: `[测试/验收工程师]`

| 序号 | 核查子项 | 准入门槛 | 测试/核查动作 | 通过判据 | 证据产物 | 状态 |
| :---: | :--- | :--- | :--- | :--- | :--- | :---: |
| 3.1 | **灰度环境启动** | Stage 2 通过。 | 使用新生成的发布镜像一键拉起灰度服务：<br>`docker compose up -d` | 容器状态全部呈现为 `Up` 且 `healthy`，主对外端口监听拉起。 | `docker compose ps` 的输出截图或文本 | - [ ] |
| 3.2 | **常规冒烟测试** | 灰度容器运行中。 | 运行一键门禁脚本冒烟模式验证全链路联通性：<br>`BASE_URL=http://localhost:8081 bash uat/release-gate.sh --smoke-only` | 控制台最终输出冒烟测试结果 `12/0/0` 完全通过。包括：前端可达性、后端 API 健康、DB 功能、MinIO 代理及控制台可用性。 | 门禁冒烟测试终端日志（含冒烟全绿标志） | - [ ] |

> [!NOTE]
> **本阶段必须交付产物**: `TaskAndReport/Stage3-EVIDENCE.md` （灰度容器运行状态截图、`release-gate.sh --smoke-only` 验证成功的完整日志）。

---

### Stage 4: 故障注入与系统鲁棒自愈验证 (Fault Injection & Self-Healing Verification)

*   **阶段目标**: 通过主动破坏系统组件运行状态，强力校验系统的熔断、隔离与进程异常退出自愈能力。
*   **本阶段责任人**: `[测试/验收工程师]`

| 序号 | 核查子项 | 准入门槛 | 测试/核查动作 | 通过判据 | 证据产物 | 状态 |
| :---: | :--- | :--- | :--- | :--- | :--- | :---: |
| 4.1 | **准入熔断隔离** | Stage 3 冒烟测试全绿通过。 | 注入 MinerU 下游异常故障验证熔断行为：<br>`bash uat/release-gate.sh --with-fault` （选取 mineru-down 模式） | 1. PDF 上传立即遭到拦截并准确返回 `503`（熔断开启）。<br>2. 与此同期的 Markdown 纯文本上传不受任何影响。 | 准入电路开启 503 拦截命令行日志及 Markdown 上传成功 taskId 记录 | - [ ] |
| 4.2 | **Worker 异常自愈** | 准入电路测试完毕。 | 模拟核心 Worker 服务进程崩溃（`docker kill`），随后重启：<br>`bash uat/release-gate.sh --with-fault` | 1. 原正在 running 中的解析任务自动优雅重置为 pending。<br>2. 自愈恢复事件 `parse-stale-running-recovered` 完整记录并有据可查。 | Worker Crash 恢复事件 trace 记录日志及最终任务平稳收敛至终态的轨迹 | - [ ] |

> [!NOTE]
> **本阶段必须交付产物**: `TaskAndReport/Stage4-EVIDENCE.md` （准入熔断 503 记录、Markdown 旁路正常日志、Worker Crash 后恢复扫描事件的 trace 归档）。

---

### Stage 5: 重并发压力测试与阶段排队验证 (Stress & Concurrency Queue Verification)

*   **阶段目标**: 在并发重负载压力下，严格验证系统的“阶段排队并发模型”是否起效，避免宿主机资源被 MinerU/Ollama 彻底压垮导致崩溃。
*   **本阶段责任人**: `[测试/验收工程师]`

| 序号 | 核查子项 | 准入门槛 | 测试/核查动作 | 通过判据 | 证据产物 | 状态 |
| :---: | :--- | :--- | :--- | :--- | :--- | :---: |
| 5.1 | **并发压力与排队** | Stage 4 通过。 | 执行一键门禁完整模式，启动并发与压力测试：<br>`bash uat/release-gate.sh --full-gate` | 1. 快速并发提交 5 个以上的 PDF 任务测试。<br>2. MinerU heavy-stage 活跃数及 AI 识别活跃数在压力下**始终控制在 `<= 1` 违规次数为 0**（排队隔离有效）。 | 并发提交成功耗时记录、多任务轮询活跃任务监控文本 | - [ ] |
| 5.2 | **终态收敛平稳** | 并发任务进入队列。 | 保持门禁持续监听直至全部高并发任务到达最终状态。 | 所有提交的并发测试任务全部平稳过渡收敛至终态（`review-pending`、`completed` 或 `failed`），无任何数据库崩溃、MinIO 挂起、容器 OOM 重启等异常行为。 | 并发任务终态分布统计结果（completed/review-pending/failed） | - [ ] |

> [!NOTE]
> **本阶段必须交付产物**: `TaskAndReport/Stage5-EVIDENCE.md` （`release-gate.sh --full-gate` 运行的详细日志、并发轮询任务状态表格、排队违规率分析摘要）。

---

### Stage 6: 生产环境部署演练与 Override 契约核实 (Production Rehearsal & Contract Check)

*   **阶段目标**: 在向生产主线交付控制权前，由生产开发联合对生产实际 override 配置进行终极比对，保证生产边界的极致纯净与安全。
*   **本阶段责任人**: `[生产运维工程师 + 开发工程师]`

| 序号 | 核查子项 | 准入门槛 | 测试/核查动作 | 通过判据 | 证据产物 | 状态 |
| :---: | :--- | :--- | :--- | :--- | :--- | :---: |
| 6.1 | **Override 安全核实** | Stage 5 压力测试全项通过。 | 1. 打开 生产工作区根目录 内的本地 `docker-compose.override.yml`。<br>2. 逐项核对三项安全准入线口径。 | 1. `DISABLE_AI_SKELETON_FALLBACK` 必须为 `true`。<br>2. `OLLAMA_TIER2_MODEL` 必须锁定为 `qwen3.5:9b`。<br>3. MinIO 控制台端口绑定必须严格为本地回环 `127.0.0.1:19001:9001`。 | Override 文件比对合格记录文本 | - [ ] |
| 6.2 | **带探针准入验证** | Override 比对合格。 | 在生产工作区运行带有 MinerU 实际任务探针的预检命令：<br>`RUN_MINERU_SUBMIT_PROBE=1 bash ops/runtime-ownership-status.sh` | 预检顺利连通，探针向 MinerU 成功提交测试任务并安全返回 HTTP `202`，且携带有效探针 ID，`blocking=false`。 | 生产预检控制台带探针输出结果 | - [ ] |

> [!NOTE]
> **本阶段必须交付产物**: `TaskAndReport/Stage6-EVIDENCE.md` （生产实际 override 配置复制截图、带探针预检的合格日志输出，证明生产准入完全健康）。

---

### Stage 7: 正式上线收口与资产签署交付 (Final Go-Live & Asset Signature)

*   **阶段目标**: 将经过所有前置校验与测试充分证实安全的版本正式推向生产交付，完成验收签字，彻底归零交付债务。
*   **本阶段责任人**: `[项目负责人 (Luceon Owner) + 测试验收负责人]`

| 序号 | 核查子项 | 准入门槛 | 测试/核查动作 | 通过判据 | 证据产物 | 状态 |
| :---: | :--- | :--- | :--- | :--- | :--- | :---: |
| 7.1 | ** Checklist 全项签收** | Stage 6 带探针准入检查全通，EVIDENCE 0-6 全部齐备。 | 联合检查本发布 Checklist 上的每一项勾选状态，确认无跳项、漏项或未决项。 | 全项均已打勾，无任何残存遗留风险，或残存风险已有明确的降级 issue 挂牌。 | 本 Checklist 完整勾选固化 | - [ ] |
| 7.2 | **联合电子签字** | 清单核实无遗漏。 | 项目负责人与测试负责人在此 Checklist 底部以 PR Approve / 合并、或者电子文本方式联合签署姓名与日期。 | 双方签字齐备，签署日期确认，宣布版本上线就绪。 | 联合签字记录 | - [ ] |
| 7.3 | **PR 合并归零** | 签字完成。 | 提起发布收口 PR 并由测试部门审核通过后将其安全合入 `main` 主线分支。 | PR 正常合入，PR 描述附带 `Closes #8`，关闭 GitHub 对应任务。 | 成功合并的 PR 编号及最终 Commit Handoff | - [ ] |

> [!NOTE]
> **本阶段必须交付产物**: `TaskAndReport/Stage7-EVIDENCE.md` （联合签字最终本 Checklist 文档、合并 PR 详情截图与 main 分支最新 HEAD 指针确认）。

---

## ▌ 联合验收签字栏

本项目负责人与测试验收负责人，已依照收口 Checklist 对 v6.9.x 的全部阶段进行了严苛审查与实测。现共同证实所有准入门槛、测试动作、通过判据及证据产物均已百分百合法归档，没有残存未决或带病上线的未决项。同意将该版本正式推向生产运行。

```
项目负责人 (Luceon Owner) 签字:  ______________________      日期: 2026-____-____

测试验收负责人 签字:              ______________________      日期: 2026-____-____
```
