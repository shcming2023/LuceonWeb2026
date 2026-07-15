# LuceonWeb2026 三域工作台开发验收报告

日期：2026-07-15

分支：`codex/three-domain-workspaces`

基线提交：`f41d192`

结论：**本迭代开发验收通过**

## 1. 验收边界

本迭代完成产品结构、持久化任务、谱系聚合、资产下载与权限边界，不修改 MinerU、Popo、Worker V2.3 的核心处理算法，不修改锁定模板、`elegantbook.cls` 或质量门禁。本轮未开启真实 GPU 服务器；状态机使用受控替身和已有冻结资产验证。真实 GPU 批量贯通烟测必须在下一独立任务中执行，不能把本报告解释成真实 GPU 生产放行。

没有删除或重刷既有数据，没有为样本、书名、文件名、`material_id` 或页码加入专用分支，没有合并主分支、创建 tag、Release 或部署正式目标 Mac mini。

## 2. 最终信息架构与产品决策

一级入口已调整为：工作概览、PDF资产、解析任务、精修任务、比对审查、运行设置。

- **PDF资产**是长期资产台账：上传、去重、材料身份、当前投影、谱系、历史运行和所有可下载资产。
- **解析任务**是一套持久化批次系统：普通用户一次提交后自动执行 MinerU 批量、逐本冻结、模型切换、Popo 批量、逐本冻结和元数据调度；不再要求普通用户手动提交 Popo。
- **精修任务**继续复用既有 Worker V2.3 模型，支持批量创建、阶段进度、`needs_review` 交接和重新验证、当前接受输出与候选产物分离。
- **比对审查**保持独立，只做渲染和审阅，并能返回同一 `material_pk` 的完整谱系。
- 同一材料不在菜单间搬家。三个工作区是同一个不可变材料根的不同视图。

旧 `/files` 路由在前端兼容重定向到 `/assets`；Nginx 对 `/assets` 增加精确 SPA location，避免与静态目录同名时发生错误的 `/assets/` 重定向。

## 3. 数据模型、迁移与历史审计

新增最小模型：

- `pipeline_run_items`：批次不可变快照中的逐本状态。
- `pipeline_stage_attempts`：MinerU、冻结、Popo、冻结等追加式尝试与错误证据。
- `metadata_jobs`：AI 元数据输入 manifest、模型/提示版本、领取、租约、重试和结果状态。
- `pipeline_runs` 扩展幂等键、全局 GPU queue slot、请求快照、worker、attempt、heartbeat 和 lease 字段。
- `materials.page_count`：新上传 PDF 的可信页数。

迁移 `20260715_add_domain_workspaces` 先在数据库副本执行 upgrade → downgrade → upgrade 并检查完整性，再应用于开发数据库。应用前一致性备份为：

- `runtime/backups/mineru-pre-three-domain-20260715T1642.db`
- 大小约 1.5 GiB
- SHA-256：`79c1ce6ddcf52f3f7777edcf85d108de360b14e3d7c7a8ce152c7661a98e7e6f`
- `PRAGMA integrity_check`：`ok`

迁移前审计结果：materials 1120、pipeline runs 92、outputs 420、metadata 358；发现 2 组 `(user_id, material_id)` 重复、2 条 output→material 孤立引用、7 条 output→review_asset 孤立引用、2 条 metadata 孤立引用。它们未被删除或伪造修复；无法可靠重建的旧运行明确投影为 `legacy_unverified`。

迁移后材料和既有运行计数保持不变，`alembic_version=20260715_add_domain_workspaces`。新任务表当前为 0，符合本轮不开 GPU、不伪造任务记录的边界。

## 4. 状态机、幂等、部分失败与恢复

API 先写数据库，再由独立 `material-task-worker` 领取；任务不再依赖 API 进程中的 daemon thread。领取具有 lease、heartbeat、attempt 和 stale recovery，API 重启不会静默丢失已持久化任务。

常规批次由后端强制最多 5 本并固化 `material_pk`、`material_id` 和源 SHA 快照；同一批次拒绝重复 SHA。幂等键和数据库唯一 GPU queue slot 防止重复点击与并发 GPU 重任务。

批次投影规则：

- 全部项目成功才是 `succeeded`。
- 有成功冻结资产且有失败项目时是 `partial`，不能假成功。
- 每本材料独立保留已经冻结的 MinerU/Popo 结果。
- Popo 失败恢复只从已冻结 MinerU 继续，不重跑 MinerU。
- “恢复 Popo”仅管理员界面可见，后端同样强制管理员权限。
- 元数据任务持久化、可重试；失败不阻断已有 Popo 冻结输入的 Worker；人工元数据 revision 不会被后台重试覆盖。

Worker V2.3 未另建数据库模型，继续使用 `WorkflowJob`、`StageRun`、`ArtifactVersion`、`QaFinding` 和 `RepairAttempt`。`needs_review` 保持非终态成功语义，候选产物与已接受 output 分别展示。

## 5. 谱系与 API 契约

服务层按 `material_pk` 聚合 SQLite、Workflow MySQL 与 MinIO，不以文件名关联，也不要求 MinerU 与 Popo run ID 相同。

关键新增或强化契约：

- `GET /api/materials/{material_pk}/lineage`：聚合源 SHA、解析批次、逐本阶段、metadata、Worker、output 和 review 对象。
- `GET /api/materials/pipeline/runs`、`GET /api/materials/pipeline/runs/{run_id}`：分页批次与逐本详情。
- `POST /api/materials/pipeline/preflight`、`POST /api/materials/pipeline/start`：以 `material_pks` 固化快照并幂等提交。
- `POST /api/materials/{material_pk}/pipeline/resume-popo/*`：管理员异常入口。
- `POST/GET /api/materials/{material_pk}/metadata/jobs` 和 retry：持久化元数据任务。
- `GET /api/materials/{material_pk}/artifacts`：统一只读资产目录。
- `GET /api/materials/{material_pk}/artifacts/{artifact_id}/download`：受控 ID 下载代理。
- `POST /api/workflow-v2/jobs/batch`、分页 job summary/detail：精修批量创建与追踪。
- `GET /api/workflow-v2/jobs/{public_id}/review-candidate/{kind}`：受保护的候选 PDF/ZIP/证据下载。
- compare 返回 `material_pk`，审阅页可回到材料谱系。

列表 URL 保存 page、filter、selected object 等稳定参数；浏览器刷新与深链恢复已验证。

## 6. 统一资产目录与下载安全

统一目录覆盖源 PDF、冻结 MinerU 归档/manifest、冻结 Popo 归档/manifest、`needs_review` 候选 ZIP/PDF/证据、当前及历史接受的 LaTeX ZIP/编译 PDF/质量证据。

前端只能传服务端生成的受控 artifact ID、run ID、job ID 或 output ID。后端根据当前用户、数据库记录、冻结标记和已验证 manifest 解析真实对象；不接受任意 bucket/object path。下载实现使用分块流式响应并支持 Range，返回 Content-Length、文件名及可用的 ETag/SHA。

安全规则：

- 生产默认 `ALLOW_RAW_ASSET_DOWNLOAD=false`，即使关闭普通认证也不会默认公开源 PDF、MinerU 或 Popo 完整资产。
- 管理员邮箱 allowlist 和材料 owner 双重约束恢复与下载权限。
- 未授权、跨用户、路径穿越、失效对象、冻结标记缺失和大文件流式传输均有回归。
- 历史对象缺少可靠 manifest/冻结标记时显示 `legacy_unverified` 或不可下载，不伪装成已冻结。

真实浏览器下载的长度与 SHA 见 [下载证据清单](./evidence/download-manifest.md)。

## 7. 自动回归与 clean build

最终回归结果：

- 后端：使用封版 backend 镜像并只读挂载整仓执行，`593 passed, 820 warnings`，0 failed，32.04 秒。
- 前端：认证、Popo 恢复权限、Worker recovery/source-trace、theme、Nginx backend DNS 契约全部通过。
- 前端生产构建：通过。
- `git diff --check`：通过。
- `graphify update .`：完成，4508 nodes / 4635 edges；没有把 graphify 生成噪声纳入业务差异。

新增测试覆盖三本批次 2 成功 + 1 Popo 失败、逐本冻结保留、Popo 最小恢复、重复提交、全局 GPU slot、stale lease 恢复、人工元数据保护、metadata 失败不阻断 Worker、普通用户禁止恢复、跨用户下载、路径穿越、Range/分块读取、上传 SHA/页数、谱系聚合和 compose worker 契约。

最终 arm64 clean/no-cache 镜像：

| 镜像 | Image ID |
|---|---|
| backend | `sha256:2703949580841c1e19f8eddd17755d146162632cc96c7b63901427a7fea1703e` |
| frontend | `sha256:740a77f9219d73e7d0831c2e362d3340cfb3828ccf10e9f8f3c9c84e30cab51e` |

## 8. 浏览器 UAT

隔离栈使用上述封版镜像、独立 compose project、独立网络、独立数据库副本和端口 `38080/38081`；验证期间不改代码、不重建、不重部署。浏览器完成真实登录和页面操作，而非只检查 API 200。

通过项：

- PDF资产页身份、状态、完整谱系和统一下载面板；深链打开抽屉后刷新仍保持对象。
- 解析任务页批次和三本逐项状态；普通用户没有恢复 Popo 按钮，直接调用得到 403。
- 精修任务页任务 ID、输入 Popo、stage、attempt、output 和 review 跳转。
- `needs_review` 页面候选 PDF、待修复 ZIP、问题证据、人工交接和重新验证入口均存在，未显示成最终成功。
- 比对审查的源 PDF 与编译 PDF 均实际渲染；返回按钮回到同一 `material_pk=1335`。
- 实际下载源 PDF、MinerU、Popo、LaTeX ZIP 和编译 PDF；另下载 120118467 字节 MinerU 大包验证内存与流式行为。
- `/files` 兼容跳转；无效材料在浏览器显示 404；有效页面无 404、502 或资源超时。
- 本地和公网开发入口最终均能正常打开 `/assets`，公网截图不是隔离栈截图。

证据截图：

- [PDF资产、谱系与下载](./evidence/screenshots/01-assets-lineage-downloads.png)
- [解析批次](./evidence/screenshots/02-pipeline-batches.png)
- [精修任务详情](./evidence/screenshots/03-refinement-job-detail.png)
- [PDF双栏实际渲染](./evidence/screenshots/04-compare-review-rendered.png)
- [浏览器安全与404](./evidence/screenshots/05-browser-security-404.png)
- [needs_review人工闭环](./evidence/screenshots/06-needs-review-handoff.png)
- [公网开发入口恢复](./evidence/screenshots/07-public-development-assets.png)

## 9. 本轮发现并修复的缺陷

| 分类 | 级别 | 根因 | 通用最小修复与回归 |
|---|---|---|---|
| UI/Nginx | Blocker | `/assets` 与 Nginx 静态目录同名，直接深链被重定向到错误 `/assets/` | 增加 exact SPA location，并扩展 Nginx 路由契约测试；重新 clean build 后重做浏览器验收 |
| 隔离环境/网络 | UAT blocker | 隔离 compose 复用了开发 backend 的网络别名，前端 DNS 可命中错误容器 | UAT 栈改用独立网络；这是测试编排修复，没有改产品逻辑 |
| 运行状态 | Major | worker 继承 backend HTTP healthcheck，纯后台进程被错误标记 unhealthy | dev/prod compose 显式禁用 worker HTTP healthcheck，并增加发布契约测试 |
| 任务持久化 | Blocker | 旧解析提交仅依赖 API daemon thread，部分失败可被批次级状态压平 | 增加 DB queue、逐本状态、stage attempts、lease/heartbeat、幂等和 partial 聚合测试 |
| 权限/下载 | Blocker | 原资产接口缺少统一 fail-closed 权限与受控 ID 目录 | 增加资产目录、安全代理、owner/admin校验、生产默认关闭和攻击面测试 |

## 10. 开发环境、兼容与回滚

开发数据库迁移后完整性为 `ok`，旧运行仍为 69 succeeded / 23 failed，没有新增运行中任务，没有启动 GPU。开发容器当前使用最终 clean 镜像：backend、frontend healthy，两个 worker 运行且使用 `Healthcheck Test=["NONE"]`；容器 restart 均为 0、OOMKilled 均为 false。

开发入口：

- `http://127.0.0.1:28081/assets`
- `http://152.136.183.144:15000/assets`

回滚材料：

- 数据库：上述一致性备份。
- 镜像：`luceonweb2026-review-backend:pre-three-domain-20260715`、`luceonweb2026-review-frontend:pre-three-domain-20260715`。
- 路由兼容：旧 `/files` 可继续使用。
- Alembic 迁移已验证可 downgrade，但实际回滚必须先停止任务 worker，并结合数据库备份执行，不能只替换前端。

## 11. 修改范围与提交记录

修改严格集中于：材料/Worker/review API，材料模型与迁移，持久化 queue/worker，资产目录与权限，三域前端及复用组件，Nginx/compose/release contract，以及直接对应的测试和 UAT 文档。

分支为 `codex/three-domain-workspaces`；最终提交哈希和远端推送记录以本报告所在提交及交付消息为准。未纳入用户原有未跟踪文件 `codex-final.md` 和 `docs/uat/evidence/`。

## 12. 遗留问题与下一步

### Major

无本目标内遗留 Major。

### Minor / 已知边界

1. 迁移前历史解析批次无法补造逐本 attempt，保持 `legacy_unverified` 是有意的数据保护策略。
2. 旧上传记录没有可追溯页数时显示 `—`；不从文件名或不可信元数据猜测。
3. 最新 Worker attempt 状态与“已有接受输出”是两条独立事实；资产目录和谱系分别展示，不能用一次失败/取消覆盖历史接受输出。
4. SQLite 现有重复和孤立引用只审计未清洗；应另开数据治理任务，在具备业务判定规则后处理。

### 下一独立任务：真实 GPU 批量贯通烟测

开启 GPU 后，用最终代码和至少三本真实 PDF 做一次不改代码的批量烟测，重点验证：常规入口只提交一次；MinerU 批量完成并逐本冻结；退出 MinerU 后再加载 Popo；Popo 批量完成并逐本冻结；失败材料仅从最小阶段恢复；AI 元数据异步跟进；GPU queue slot 串行；冻结后清理本轮 GPU 临时物并停机。该烟测通过后，才讨论合并主分支、正式 tag/Release 和正式目标 Mac mini 部署。

---

**最终结论：本迭代开发验收通过。真实 GPU 批量贯通与正式生产发布不在本目标内，尚未被宣称通过。**
