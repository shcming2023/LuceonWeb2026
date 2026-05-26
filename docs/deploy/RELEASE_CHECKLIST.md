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

-   **Nginx 前端服务镜像 (`cms-frontend:6.9.0-rc1`)** *(注: 属于占位镜像名，待 Stage 1 任务确立规范后统一正式回填)*
    -   *Digest*: `sha256:7f9a8b8c8d8e...[回填实际 Digest]`
-   **后端上传服务镜像 (`upload-server:6.9.0-rc1`)** *(注: 属于占位镜像名，待 Stage 1 任务确立规范后统一正式回填)*
    -   *Digest*: `sha256:4a3b2c1d0e9f...[回填实际 Digest]`
-   **JSON 数据库服务镜像 (`db-server:6.9.0-rc1`)** *(注: 属于占位镜像名，待 Stage 1 任务确立规范后统一正式回填)*
    -   *Digest*: `sha256:9f8e7d6c5b4a...[回填实际 Digest]`
-   **私有对象存储镜像 (`minio:RELEASE.2024-04-18T19-09-00Z`)**
    -   *Digest*: `sha256:de1234567890...[回填实际 Digest]`

---

## ▌ 8 阶段收口计划 Checklist

### Stage 0: 代码冻结与分支管控 (Code Freeze & Branch Protection)

*   **阶段目标**: 锁定发布包的代码基础，严格保护核心发布分支，防止非授权变更流向生产环境。
*   **本阶段责任人**: `[开发部门负责人]`

| 序号 | 核查子项 | 准入门槛 | 测试/核查动作 | 通过判据 | 证据产物 | 状态 |
| :---: | :--- | :--- | :--- | :--- | :--- | :---: |
| 0.1 | **分支保护生效** | 所有 Phase 1 需求开发完成，代码合入 `main`。 | 1. 确认已在 GitHub 仓库开启 `release/6.9.x` 分支的保护规则（Branch Protection Rules）。<br>2. 限制直推，强制要求 PR 与 Review。 | 1. 直接向该分支执行 `git push` 被拒绝拦截。<br>2. **对 main 与 release/6.9.x 的 PR 合并规则必须配置至少 1 个 Approver 强制审查**（杜绝 owner 自审自合）。 | 截图或命令行拦截日志 | - [ ] |
| 0.2 | **锁定 Git HEAD** | 所有最后修复 PR 已合入。 | 1. 在 `codex/release-checklist-skeleton` 上检出最终 HEAD commit 校验和。<br>2. 登记至元信息表。 | Git HEAD 锁定，无脏工作区，远端与本地完全一致。 | `git log -1` 命令行输出 | - [ ] |

> [!NOTE]
> **本阶段必须交付产物**: `TaskAndReport/Stage0-EVIDENCE.md` （记录锁定 Commit ID 及分支保护与多 Approver 规则设置证明）。

---

### Stage 1: 依赖安全与静态构建预检 (Dependency Audit & Build Preflight)

*   **阶段目标**: 阻断带有已知漏洞的依赖包合入，并确保代码在静态编译与契约核实层级完全一致。
*   **本阶段责任人**: `[开发工程师]`

| 序号 | 核查子项 | 准入门槛 | 测试/核查动作 | 通过判据 | 证据产物 | 状态 |
| :---: | :--- | :--- | :--- | :--- | :--- | :---: |
| 1.1 | **依赖安全扫描** | Stage 0 通过。 | 执行本地安全性扫描检查已知漏洞阻断：<br>`npx pnpm@10.4.1 audit --audit-level high` | 零 High 及以上等级的高风险包依赖报错。<br>*(注: 允许已接受的安全例外清单文件以白名单方式记录在 `docs/deploy/dependency-audit-waivers.md` 中)* | 依赖扫描命令行日志 | - [ ] |
| 1.2 | **静态编译无错** | 静态扫描通过。 | 在根目录执行静态类型检查及打包构建以校验契约：<br>`npx pnpm@10.4.1 exec tsc --noEmit` && `npx pnpm@10.4.1 run build` | 编译过程无 `TypeError`、未定义引用或打包构建报错，顺利输出 `dist/`。 | 静态类型与打包成功终端日志 | - [ ] |
| 1.3 | **配置契约匹配** | 本地打包成功。 | 逐项核对 `.env.example` 与各 `docker-compose.*.yml` 的端口、数据卷映射、公共端点契约匹配性，消除遗漏。 | 没有出现遗漏的环境变量，对外端口配置和代理路由一一对应。 | 配置对比记录 | - [ ] |
| 1.4 | **无损预检测试** | 配置契约核对完成。 | 在开发工作区中运行只读预检脚本：<br>`bash ops/runtime-ownership-status.sh` | 预检脚本成功执行（`exit 0`）。且 MinerU submit-path 一行可以正常显示 `submit-probe-not-run`，除此外的内部依赖与端口显示为已监听可用。 | 预检脚本的控制台输出摘要 | - [ ] |

> [!NOTE]
> **本阶段必须交付产物**: `TaskAndReport/Stage1-EVIDENCE.md` （包含包安全性 audit、`tsc` 静态类型检查绿通、打包编译通过证据以及契约匹配确认）。

---

### Stage 2: 镜像安全构建与签名声明 (Docker Build & Image Signatures)

*   **阶段目标**: 生成完全可追溯的二进制容器构建镜像，并在 Check 列表中对镜像的唯一签名进行确信固化。
*   **本阶段责任人**: `[生产运维工程师]`

| 序号 | 核查子项 | 准入门槛 | 测试/核查动作 | 通过判据 | 证据产物 | 状态 |
| :---: | :--- | :--- | :--- | :--- | :--- | :---: |
| 2.1 | **生产基线构建** | Stage 1 通过。 | 1. 运行生产基线无缓存干净构建：<br>`docker compose -f docker-compose.yml -f docker-compose.prod.yml build --no-cache`<br>2. 镜像生成后使用与 Stage 6 生产环境完全相同的一致性 override 配置验证构建产物契约可用性。 | 1. 所有核心服务容器镜像成功构建，无 Native 编译报错。<br>2. 经生产 override 核试，构建产物配置与契约一致性通过。 | Docker 生产基线无缓存构建日志 | - [ ] |
| 2.2 | **镜像签收与推送**| 所有镜像构建完毕。 | 1. 将构建的镜像安全推送到私有仓库：<br>`docker push <registry>/<image>:<tag>`<br>2. 运行 `docker buildx imagetools inspect` 提取服务镜像唯一的 `sha256` 签名。 | 成功获取核心组件的完整 SHA256 digest 签名并登记，manifest 签名摘要输出成功。 | 镜像推送命令、`imagetools inspect` 摘要及本 Checklist 头部 digest 回填 | - [ ] |

> [!NOTE]
> **本阶段必须交付产物**: `TaskAndReport/Stage2-EVIDENCE.md` （生产基线构建日志、`docker push` 及 `docker buildx imagetools inspect` 导出的镜像 digest 签名记录）。

---

### Stage 3: 灰度环境拉起与常规冒烟测试 (Staging Deploy & Smoke Verification)

*   **阶段目标**: 在受控的灰度/UAT 环境中拉起基于 Stage 2 镜像的整套服务，以自动化冒烟验证全链路联通性。
*   **本阶段责任人**: `[测试/验收工程师]`

| 序号 | 核查子项 | 准入门槛 | 测试/核查动作 | 通过判据 | 证据产物 | 状态 |
| :---: | :--- | :--- | :--- | :--- | :--- | :---: |
| 3.1 | **灰度环境启动** | Stage 2 通过。 | 1. 在灰度环境容器拉起前，先执行只读脚本 `bash ops/runtime-ownership-status.sh` 确认 Host 端的 `8081/8083/11434/19001` 等基础端口处于监听状态。<br>2. 使用新发布的镜像一键拉起灰度服务：<br>`docker compose up -d` | 1. 预检确认 Host 监听服务已处于运行中。<br>2. 容器状态全部呈现为 `healthy` / `Up`。 | `docker compose ps` 的输出截图或文本 | - [ ] |
| 3.2 | **常规冒烟测试** | 灰度容器运行中。 | 运行一键门禁脚本冒烟模式验证全链路联通性：<br>`BASE_URL=http://localhost:8081 bash uat/release-gate.sh --smoke-only` | 控制台冒烟结果显示：**通过 ≥ 10 / 失败 0 / 跳过 ≤ 1（共 11 项）**，且终端末行出现：`✅ 所有冒烟测试通过，系统运行正常`。 | 门禁冒烟测试终端日志（100% 真实通过绿通记录） | - [ ] |

> [!NOTE]
> **本阶段必须交付产物**: `TaskAndReport/Stage3-EVIDENCE.md` （前置 Host 监听状态、灰度容器运行截图、`release-gate.sh --smoke-only` 全绿冒烟通过日志）。

---

### Stage 4: 故障注入与系统鲁棒自愈验证 (Fault Injection & Self-Healing Verification)

*   **阶段目标**: 通过主动破坏系统组件运行状态，强力校验系统的熔断、隔离与进程异常退出自愈能力。
*   **本阶段责任人**: `[测试/验收工程师]`

| 序号 | 核查子项 | 准入门槛 | 测试/核查动作 | 通过判据 | 证据产物 | 状态 |
| :---: | :--- | :--- | :--- | :--- | :--- | :---: |
| 4.1 | **准入熔断隔离** | Stage 3 冒烟测试全项通过。 | **显式执行两步验证校验熔断鲁棒性**：<br>1. **验证 PDF 被熔断与 Markdown 旁路成功**（需手动暂停 `luceon-mineru` 以导致宕机）：<br>`bash uat/fault-injection-admission.sh --mode mineru-down`<br>2. **验证半故障场景下熔断探针功能**（/health OK 但 submit 返回 500）：<br>`bash uat/fault-injection-admission.sh --mode mineru-half-failure` | 1. 在 `mineru-down` 场景下，PDF 上传遭到安全拦截并精准返回 `503` 错误（熔断电路打开），与此同期的 Markdown 纯文本上传不受任何阻碍。<br>2. 在 `mineru-half-failure` 下，电路能够准确认定并使准入保持隔离打开状态。 | 熔断测试命令控制台输出、503 拦截记录、Markdown 上传 taskId 及半故障状态日志 | - [ ] |
| 4.2 | **Worker 异常自愈** | 准入电路测试完毕。 | 模拟核心 Worker 进程强制终止（`docker kill`），随后重启：<br>`bash uat/release-gate.sh --with-fault` | 1. 正在 running 中的解析任务被自动优雅拉回重置为 pending。<br>2. 任务自愈恢复事件流中成功记录并**出现 `parse-stale-running-recovered` 或 `parse-restart-recovered` 之一即可**。 | Worker Crash 恢复事件 trace 记录日志及最终任务平稳收敛至终态的轨迹 | - [ ] |

> [!NOTE]
> **本阶段必须交付产物**: `TaskAndReport/Stage4-EVIDENCE.md` （mineru-down 熔断 503 与旁路验证日志、mineru-half-failure 状态日志、Worker Crash 后恢复扫描事件流 trace 证据）。

---

### Stage 5: 重并发压力测试与阶段排队验证 (Stress & Concurrency Queue Verification)

*   **阶段目标**: 在并发重负载压力下，严格验证系统的“阶段排队并发模型”是否起效，避免宿主机资源被 MinerU/Ollama 彻底压垮导致崩溃。
*   **本阶段责任人**: `[测试/验收工程师]`

| 序号 | 核查子项 | 准入门槛 | 测试/核查动作 | 通过判据 | 证据产物 | 状态 |
| :---: | :--- | :--- | :--- | :--- | :--- | :---: |
| 5.1 | **并发压力与排队** | Stage 4 通过。 | 执行一键门禁完整模式，启动并发与压力测试：<br>`bash uat/release-gate.sh --full-gate` | 1. 快速并发提交 5 个以上的 PDF 任务测试。<br>2. MinerU heavy-stage 活跃数及 AI 识别活跃数在压力下**始终控制在 `<= 1` 违规次数为 0**（排队隔离有效）。<br>3. **`stress-test-concurrency.sh` 脚本最终退出状态码为 0**（如非 0 需依据日志归档具体原因）。 | 并发提交成功耗时记录、多任务轮询活跃任务监控文本 | - [ ] |
| 5.2 | **终态收敛平稳** | 并发任务进入队列。 | 保持门禁持续监听直至全部高并发任务到达最终状态。 | 所有提交的并发测试任务全部平稳过渡收敛至终态（`review-pending`、`completed` 或 `failed`），无任何数据库崩溃、MinIO 挂起、容器 OOM 重启等异常行为。 | 并发任务终态分布统计结果（completed/review-pending/failed） | - [ ] |

> [!NOTE]
> **本阶段必须交付产物**: `TaskAndReport/Stage5-EVIDENCE.md` （`release-gate.sh --full-gate` 运行的详细日志、并发轮询任务状态表格、排队违规率分析及最终 exit code 0 证明）。

---

### Stage 6: 生产环境部署演练与 Override 契约核实 (Production Rehearsal & Contract Check)

*   **阶段目标**: 在向生产主线交付控制权前，由生产开发联合对生产实际 override 配置进行终极比对，保证生产边界的极致纯净与安全。
*   **本阶段责任人**: `[生产运维工程师 + 开发工程师]`

| 序号 | 核查子项 | 准入门槛 | 测试/核查动作 | 通过判据 | 证据产物 | 状态 |
| :---: | :--- | :--- | :--- | :--- | :--- | :---: |
| 6.1 | **Override 安全核实** | Stage 5 压力测试全项通过。 | 1. 打开 生产工作区根目录 内的本地 `docker-compose.override.yml`。<br>2. 逐项核对生产环境必须对齐的 6 项安全核心口径。 | **生产环境 6 项 override 核心配置必须完全符合以下安全要求**：<br>1. `DISABLE_AI_SKELETON_FALLBACK` 必须为 `true`<br>2. `OLLAMA_TIER2_MODEL` 必须锁定为 `qwen3.5:9b`<br>3. MinIO 控制台绑定端口必须严格为本地回环 `127.0.0.1:19001:9001`<br>4. `LOCAL_MINERU_ENDPOINT` 必须匹配 `http://host.docker.internal:8083`<br>5. `OLLAMA_API_URL` 必须匹配 `http://host.docker.internal:11434`<br>6. `ALLOW_AI_SKELETON_FALLBACK` 必须为 `false` | Override 6项安全核心配置对比合格记录文本 | - [ ] |
| 6.2 | **带探针准入验证** | Override 比对合格。 | 在生产工作区运行带有 MinerU 实际任务探针的预检命令：<br>`RUN_MINERU_SUBMIT_PROBE=1 bash ops/runtime-ownership-status.sh` | 预检顺利连通，探针向 MinerU 成功提交测试任务并安全返回 HTTP `202`，且携带有效探针 ID，`blocking=false`。 | 生产预检控制台带探针输出结果 | - [ ] |

> [!NOTE]
> **本阶段必须交付产物**: `TaskAndReport/Stage6-EVIDENCE.md` （生产实际 6 项 override 配置复制截图、带探针预检的合格日志输出，证明生产准入完全健康）。

---

### Stage 7: 正式上线收口与资产签署交付 (Final Go-Live & Asset Signature)

*   **阶段目标**: 将经过所有前置校验与测试充分证实安全的版本正式推向生产交付，完成验收签字，彻底归零交付债务。
*   **本阶段责任人**: `[项目负责人 (Luceon Owner) + 测试验收负责人]`

| 序号 | 核查子项 | 准入门槛 | 测试/核查动作 | 通过判据 | 证据产物 | 状态 |
| :---: | :--- | :--- | :--- | :--- | :--- | :---: |
| 7.1 | ** Checklist 全项签收** | Stage 6 带探针准入检查全通，EVIDENCE 0-6 全部齐备。 | 联合检查本发布 Checklist 上的每一项勾选状态，确认无跳项、漏项或未决项。 | 全项均已打勾，无任何残存遗留风险，或残存风险已有明确的降级 issue 挂牌。 | 本 Checklist 完整勾选固化 | - [ ] |
| 7.2 | **联合电子签字** | 清单核实无遗漏。 | 项目负责人与测试负责人在此 Checklist 底部以 PR Approve / 合并、或者电子文本方式联合签署姓名与日期。 | 双方签字齐备，签署日期确认，宣布版本上线就绪。 | 联合签字记录 | - [ ] |
| 7.3 | **PR 合并归零** | 签字完成。 | 提起发布收口 PR 并由测试部门审核通过后将其合入 `main` 主线分支。 | 1. PR 正常合入，PR 描述附带 `Closes #8`，关闭对应任务。<br>2. **PR 合并强制建议采用 Rebase merge (不 Squash)**，以完整保留完整的 commit graph，防范证据链断裂，便于 evidence 全链追溯。 | 成功合并的 PR 编号及最终 Commit Handoff | - [ ] |

> [!NOTE]
> **本阶段必须交付产物**: `TaskAndReport/Stage7-EVIDENCE.md` （联合签字最终本 Checklist 文档、合并 PR 详情、rebase 合并后 main 分支最新 HEAD 指针确认）。

---

## ▌ 联合验收签字栏

本项目负责人与测试验收负责人，已依照收口 Checklist 对 v6.9.x 的全部阶段进行了严苛审查与实测。现共同证实所有准入门槛、测试动作、通过判据及证据产物均已百分百合法归档，没有残存未决或带病上线的未决项。同意将该版本正式推向生产运行。

```
项目负责人 (Luceon Owner) 签字:  ______________________      日期: 2026-____-____

测试验收负责人 签字:              ______________________      日期: 2026-____-____
```
