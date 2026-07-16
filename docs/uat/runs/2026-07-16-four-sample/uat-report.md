# LuceonWeb2026 四样本用户链路 UAT 封版报告

> 当前判定：**当前开发环境功能 UAT 已通过，封版收口仍等待外部备份作业 #4 与独立恢复复验完成**。本轮验收面仅为当前开发环境，不要求在另一台 Mac mini 安装、迁移或验收；另一台机器的 SSH、配置和烟测证据均不是本轮门禁。最终代码与当前开发镜像基线为 `f8be353`。

## 1. 范围与验收口径

- 页面入口：公网 `http://152.136.183.144:15000/`。页面是验收面；SQLite、MinIO、GPU Wrapper、容器和日志只用于取证、诊断和通用修复。
- 按用户 2026-07-16 的最终范围，本轮只验收当前开发环境；不在另一台 Mac mini 安装、迁移或验收，也不把缺少目标机 SSH/配置写成阻断。本报告通过后仅说明当前开发环境达到生产部署候选标准，不宣称另一台机器已经正式上线。
- 四本分别验收，不用总平均掩盖失败，不覆盖历史冻结版本，不按文件名、SHA、material ID 或页码做样本专用硬编码。
- MinerU/Popo 要求技术、结构、冻结和下载完整；Worker V2.3 要求流程无断点、目录门禁通过、结果可人工接手。扫描件无人工逐字真值，因此不虚称 OCR 字符零误差。
- 目录独立真值见 [source-truth.md](source-truth.md)。

## 2. 源样本与资产身份

| UAT 文件 | 字节 | 页数 | 类型 | SHA-256 | 规范文件名 | material PK / material_id |
|---|---:|---:|---|---|---|---|
| `test20260716001.pdf` | 175,841 | 3 | born-digital | `642599641f3b15e11b19f383379864081464be1f9c79bdd4f1e9334489c4b1ad` | `2025.pdf` | 1335 / `pdf-642599641f3b15e1` |
| `test20260716002.pdf` | 78,077 | 2 | born-digital 五栏词表 | `c953cb08f79c2d114c55e4078c82f53af69bc154a73ed0f78a38634183f278ab` | `Coxhead AWL.pdf` | 1334 / `pdf-c953cb08f79c2d11` |
| `test20260716003.pdf` | 905,120 | 31 | image PDF | `6f3dd4b91dedf81e0a2f7508b4518b9b20ad0012f535aedafc8da80dcde39992` | `数学寒假生活G7 A册.pdf` | 1336 / `pdf-6f3dd4b91dedf81e` |
| `test20260716004.pdf` | 60,553,426 | 252 | image PDF | `5c08239421effc942ceacca225d9cbb950b89018c1fd3ed2d82266dd8758cfb2` | `新教材全解 五上 数学.pdf` | 1337 / `pdf-5c08239421effc94` |

页面批量上传两次后，每个 SHA 仍只有一个 Material；上传结果逐文件区分“本次提交文件名”和“系统规范资产”。四个原 PDF 页面下载的字节数和 SHA 与源文件一致。

## 3. 设置与预检

- 登录、角色、九个 MinIO bucket、LLM/视觉模型、Redis、Worker、XeLaTeX 和 GPU staged API 均实际核验。
- 配置文件权限为 `0600`，保存后哈希为 `61447055794e4728d20cb89121f351e0996f2aea675bf69c0f869816e2254849`，重启后未回退。
- GPU 通过持久入口完成两波真实任务，Wrapper 最终 `ok`，队列、MinerU/Popo 批次均为 0。
- 四样本功能 UAT 当时，开发环境的外部备份明确显示“未就绪 / 无作业记录”，后端返回 `backup_disabled`，页面没有把它伪装成通过。封版收口已改为外置盘 copy 模式并执行全量真实备份；最终复制、恢复演练和告警结论见第 9.4 节。
- GPU 开机并初始化完成后，设置页显示“在线可用 / 0 个活动任务”，与 Wrapper 实时状态一致；离线策略与实时状态没有混为一谈。

## 4. MinerU + Popo + AI 元数据

### 批次

- 小样本 #93：UTC `02:37:57–02:45:42`，3/3 成功。MinerU batch `mineru-20260716023759-staged_mineru_20260716023759-8c27e5d2`；Popo batch `popo-20260716023939-staged_popo_20260716023938-c4f4771a`；AI metadata job 1、2、3 均成功。
- 大样本 #94：UTC `02:58:59–03:30:29`，1/1 成功。MinerU batch `mineru-20260716025901-staged_mineru_20260716025901-5c74d0a1`；Popo batch `popo-20260716030533-staged_popo_20260716030418-323c3bc0`；AI metadata job 4 成功。
- 两波均严格执行 MinerU 批量 → 逐本拉回/冻结 → 退出 MinerU 模型 → Popo 批量 → 逐本拉回/冻结。没有要求普通用户手动提交 Popo；“恢复 Popo”仅保留为管理员异常入口。

### 逐本 run、归档与冻结

| 样本 | MinerU run / 归档（字节，SHA-256） | Popo run / 归档（字节，SHA-256） | MinIO 清单核验 |
|---|---|---|---|
| 001 | `mineru-20260716023759-staged_mineru_20260716023759-8c27e5d2--002-staged_642599641f3b15e1_002`<br>369,547 / `8e3ca7d354ce2ce5474ff76115995a6039b660f33be604391ae64dd23238fbe2` | `popo-20260716023939-staged_popo_20260716023938-c4f4771a--002-popo_642599641f3b15e1_002`<br>401,253 / `237a2f2a9cec60d62469ba1ff22ee332d006d3774e89ecb7587b72c3ed0cdf70` | MinerU 14/14；Popo 27/27 |
| 002 | `mineru-20260716023759-staged_mineru_20260716023759-8c27e5d2--001-staged_c953cb08f79c2d11_001`<br>819,713 / `3c9e2247a48c3781b773015b5fbdc4a97d7b5f239e20661c87126b0e6b16ed6c` | `popo-20260716023939-staged_popo_20260716023938-c4f4771a--001-popo_c953cb08f79c2d11_001`<br>1,514,856 / `09619e1c18303233c68a6a2cae02f44d4890b2dbad33a709a9244d77a9165c31` | MinerU 20/20；Popo 33/33 |
| 003 | `mineru-20260716023759-staged_mineru_20260716023759-8c27e5d2--003-staged_6f3dd4b91dedf81e_003`<br>2,979,815 / `20ae055fc74dc8a37d4ae4e86add8eedbf6ade49793faf74060d441af7147406` | `popo-20260716023939-staged_popo_20260716023938-c4f4771a--003-popo_6f3dd4b91dedf81e_003`<br>4,438,494 / `4880d607d46b7b72d00c012f612a1a728d7c6e390265cc936f584ec012b76dbe` | MinerU 350/350；Popo 207/207 |
| 004 | `mineru-20260716025901-staged_mineru_20260716025901-5c74d0a1--001-staged_5c08239421effc94_001`<br>120,114,259 / `803eed5672de913c11d7507e3ebb81b6ee864106f1e4062037d6e3b43766c1b6` | `popo-20260716030533-staged_popo_20260716030418-323c3bc0--001-popo_5c08239421effc94_001`<br>131,340,668 / `680000828746eaf7e7495a1405f5dede50ca238e269cdde6f930b1a71660bb5b` | MinerU 2,384/2,384；Popo 1,224/1,224 |

四本对象逐项 stat，无缺失、无 size mismatch；`mineru_done_frozen`、`popo_done_frozen` 和完成标记均存在，无遗留运行标记。页面实测大样本 MinerU/Popo 下载完成，无 404/502/超时。

## 5. Worker V2.3、目录与人工闭环

| 样本 | Worker job | output ID | 状态 / UTC 时间 | 当前 review asset |
|---|---|---:|---|---:|
| 001 | `a4522e8c-0fb1-4c75-8b4d-232ca962d9c0` | 560 | succeeded；`03:44:19–03:44:54` | 2418 |
| 002 | `3c08ec78-3ab8-40dc-8f4d-adcdd2e7cbe3` | 559 | succeeded；`03:43:49–03:44:53` | 2420 |
| 003 | `470e2608-e123-44a1-a3d3-26b13e8440c6` | 561 | succeeded；`03:44:19–03:44:57` | 2419 |
| 004 | `7c27cde1-403a-4ca9-abde-c870d5ecfd5c` | 562 | succeeded；`03:43:50–04:21:10` | 2422 |

- 001、002 无正式目录，正确保持“无正式 TOC”，各生成 2 个源证据导航节点，未虚构出版社章节。
- 003 无正式目录，生成 33 个按源顺序的 worksheet 导航节点，未伪称源目录。
- 004 真值 50 节点、6 个根、最大深度 3；标题 precision/recall/F1、层级、顺序、印刷页映射均为 100%，统一 PDF 偏移 +8。
- 004 的最小阶段恢复记录：outline attempt 1 因仅 2 个根进入 `needs_review`，通用源目录重建后 attempt 2 通过；deterministic attempt 2 因嵌套 `textcircled` 失败，通用规范化后 attempt 3 通过；bounded attempt 2 完成候选 PDF/ZIP、问题证据、人工交接和重新验证闭环，attempt 3 通过。已冻结 MinerU/Popo 未重跑。

## 6. 最终包、PDF 与独立复编

四个 ZIP 根目录均严格只有 `images/`、`figure/`、`main.tex`、`elegantbook.cls`；均小于 50 MB；单图均小于 1 MB；固定 class 哈希均为 `048c3b90da41be64f4744da3bff6ae8c5ea7abd30a5f3e2a6ad1a98f3b0d71fe`。验证报告均为：缺字 0、>10pt 明显溢出 0、未解析资源 0、未授权自定义命令/环境 0。

| 样本 | ZIP 字节 / SHA-256 | images / 最大图 | 系统 PDF（页数 / SHA-256） | 独立 XeLaTeX 两遍复编（页数 / SHA-256） |
|---|---|---|---|---|
| 001 | 613,615 / `481c03a9a2a04cf118eb10a7d2e3086ca1bcb9a63928132cdd9057f7f32c96bc` | 0 / 0 | 4 / `8ccf5e4e2e54202861e13942fa2c0e8e40989f51c10f13537a6b674ef2bd30a6` | 4 / `0bca561fec21f26029dd8eff82c8bfa9ac41052b24f1769433b027ec1efb05ff` |
| 002 | 1,277,661 / `87928dc8fba2dda9def8376b14a73c7e1a56e0b36ac62bc660b7dc7c50e45e2c` | 3 / 420,527 B | 7 / `8f00f5a6d64c9c12464eff802f57692f58213058caaa5b6d05682889c06f865a` | 7 / `a09e8659efed2772d9aa087aa8fbe29b3fca3f3bd12c629e5553ef6201c0669c` |
| 003 | 1,712,258 / `2e7123285d7162848624aaa2d55cc97effaa92e3d3cec6d89246d197a8b832d4` | 168 / 138,730 B | 46 / `a10be6de80451327a27fefe16433424671f8305852189e478a656fb625c0940a` | 46 / `b81bc1efc971c5d53c52b887fd479df3e58e5126188799f9d39fe26eef4fd9c3` |
| 004 | 9,517,198 / `0fdd769735b0861b50533f0160d404bb08a03551b7ff9842a79fe29d6e5da28f` | 1,185 / 253,670 B | 227 / `2f89c80bf0f3355d51db4be7469ade6b5d8b0d9132b7e43cb7ed720f0e8d95ac` | 227 / `9925f4e2822b2df07ce4f15a62e13c479454327829ea81f211929b6ba31cc9f5` |

PDF 对比页实测四本审阅对象不串样；重点复核 004：原 PDF 252 页、编译 PDF 227 页均实际渲染，控制台无 error/warn。页面阶段下载覆盖原 PDF、MinerU、MinerU+Popo、精修 ZIP/PDF。

封版后再次通过公网、管理员认证和修复后的唯一对象 `review_asset=2422&output_id=562` 读取 compare：返回 material `pdf-5c08239421effc94`、Worker run `7c27cde1-403a-4ca9-abde-c870d5ecfd5c`。原 PDF 下载 60,553,426 字节、SHA `5c082394...f5b2`；审阅副本 252 页；编译 PDF 6,347,950 字节、SHA `2f89c80b...95ac`；ZIP 9,517,198 字节、SHA `0fdd7697...a28f`，均与冻结账本一致。

## 7. 通用缺陷与代码修复

已修复并有回归覆盖：

1. 已完成资产的管理员“新版本重解析”入口与普通提交幂等隔离；恢复 Popo 限管理员。
2. 部分失败/过期 cancelled job 不再投影为成功或遮蔽可靠 output；逐本冻结与批量失败隔离。
3. 上传结果显示提交别名、规范文件名和去重含义；AI 编目状态语义修正。
4. 解析/精修任务自动刷新；运行中阶段、模式、租约、禁用原因和 needs_review 动作语义修正。
5. MinIO endpoint 解析、阶段下载归属和 output → 不可变 Popo run → review asset 精确绑定。
6. SQLite 长事务先提交逐本终态，库存同步独立 session 重试，心跳遇锁回滚后继续。
7. 目录重建通用回退、嵌套 `textcircled` 规范化、needs_review 候选生成前后交接时序修复。
8. Worker 批量创建后自动提交，单本失败不丢失其他成功结果。
9. 近期相同合约的成功备份会阻止 24 小时调度重复排队；显示标签变化不再触发 215 GB 级重复复制。
10. SQLite 备份快照会把自身 job 写成可恢复的终态，不再恢复出假 `running`；恢复后 job 3 计数与清单一致。
11. Worker 最终成功时会终结仍为 `queued` 的修复请求，避免父任务 `succeeded`、子修复“假排队”。本机 4 条旧记录按精确父任务边界归一化，记录保留、未删除。

未发现样本名称、SHA、material ID、具体页码的生产代码硬编码；未降低门禁，未修改锁定模板。

## 8. 回归、构建与部署记录

- 后端封版最终全量：`639 passed, 990 warnings in 21.34s`；包含 SQLite 修复、可恢复外置备份、调度去重、成功任务关闭排队修复、发布容量门禁和长任务进度持久化回归。
- 前端 `npm run build` 通过：2,009 modules transformed，生产包生成完成。
- `graphify update .` 完成：4,696 nodes / 4,841 edges；`git diff --check` 通过。
- 代码基线 commit `f8be35310c8806b49bb1f80e1fb74c6488cb9cee` 已推送 `origin/codex/three-domain-workspaces` 和 `origin/codex/luceon-v1-release`。本机 clean-build backend/worker OCI index digest 为 `sha256:0cdce59c7879dbb91dcd3e9424b0f402909a29f428cd6b228c92403e8e80e995`，可 `docker save/load` 的 arm64 平台 digest 为 `sha256:36d47f4548bb5a668c438540d34dfd8e206bc37f14e3f7e9e8af2d41f768cb34`；frontend index 为 `sha256:d271e986ce8444037e3249d80f82e3399fc1d170ac3bb544f4739499ce958a47`，平台 digest 为 `sha256:be9f37b727073f7afbd13e25d2405dcf22634ff27ecdb80835c0766bb01c9fd8`。两者 OCI revision 均精确指向该 commit，四个修复/测试文件在镜像内外 SHA-256 一致。
- GitHub Actions run `29487066924` 对同一 commit 完成无缓存 arm64 clean build，结论 `success`；registry backend index digest 为 `sha256:a355542dfd139fd4b2bec743b1a767bd3df5af5ff0d3a7d52f2568192c272195`，frontend 为 `sha256:471456b3b401e600a8df8089d2b96341d2a4d7d254352d5c860a046fe2ebf072`。开发机两次直拉 backend 大层均长时间无进展后主动终止，因此本轮离线包锁定并装入已在本机完成 639 项测试和稳定烟测的本机 clean-build 摘要；registry 摘要作为独立可复建基线记录，不能与离线候选混写成同一镜像。
- 两份业务镜像及 Redis/MongoDB/ShareLaTeX 依赖镜像均已写入 arm64 离线包；backend/frontend 分别实测 `docker save` → 删除本地 tag → `docker load` 后仍可按锁定 `repository@sha256` 解析，未用本地漂移镜像代替。
- 旧 `7bbe8c6` 迁移包已作废，不得交付。新的 `f8be353` 单文件私密迁移包采用未压缩 `.tar`（Docker layer 已压缩，避免无收益的双重 gzip），包含上述固定平台镜像、当前 `0600` 环境文件、运行配置、数据库恢复材料、锁定 skill、报告提交 Git bundle 和目标机任务书；外层 SHA-256 写入同名 `.tar.sha256`。目标机只能 `docker load`/固定 digest 启动，不得从源码重建，目标机部署与烟测仍是最终生产通过的必要条件。
- 最终开发栈已实际切换至上述 `f8be353` 镜像；在最后一次部署后的冻结窗口内没有再改代码、构建或重部署。backend/frontend/三类 Worker 和 Redis 均 `restart=0`、`OOM=false`。

## 9. 环境与数据库风险及闭环

### 9.1 容量稳定性

- Docker VM 曾只有约 7.75 GiB。本轮在共享开发 VM 同时构建、独立 XeLaTeX 复编及运行其他项目容器时，Docker event 记录了 5 次真实 exit 137；旧 MySQL restart counter 最高到 112，backend 到 2。后续容器重建后的 restart=0不能抹去这些历史证据。
- OOM 发生在开发机 Docker VM 扩容前的并发构建/复编压力下，而不是 GPU MinerU/Popo 或四本 Worker 业务阶段。扩容和容量门禁修复后，本轮同一候选镜像、三类 Worker和独立 XeLaTeX 复编共同运行，未再出现 exit 137、异常重启或长期无进度任务。
- 当前 Docker VM 已调整为 16 GB 档，容器内 `MemTotal=16,748,535,808` bytes（约 15.6 GiB）；发布 `preflight` 已把不少于 15 GiB 固化为硬门禁，并要求外置备份目录和 `state/backend` 位于不同设备。调整后的 backend、三类 Worker、MySQL 和 MinIO 当前均 `restart=0`、`OOM=false`。

### 9.2 公网入口稳定性

- 最终稳定烟测中，六个页面入口绝大多数为 HTTP 200；曾捕获一次 `/refinement-tasks` TCP 连接超时 7.8 秒，同时 GPU health 外链一次超时。该时刻本地 `28081/28080`、容器 ID、restart 和 die event 均正常，定位为外部网络/反向隧道抖动，不是应用重启。
- 紧接着本地前端、后端、公网 `/refinement-tasks`、GPU health 各连续 5 次全部成功；随后公网 compare、60.5 MB 原 PDF、19.8 MB 审阅副本、6.3 MB 编译 PDF 和 9.5 MB ZIP 均完整下载并通过页数/SHA 核验。
- 本轮封版复测又对公网 health、runtime status、解析任务、精修任务和 compare API 各连续采样 5 次，25/25 均为 HTTP 200；除解析任务列表为 3.98–4.91 秒外，其余为 0.14–0.61 秒。历史孤立抖动已不再构成本轮阻断，但正式域名仍应保留连接监控和自动恢复。

### 9.3 SQLite 索引损坏与重复审阅行

- 终态同步的 `sqlite3.OperationalError: disk I/O error` 触发深查；`PRAGMA integrity_check` 报多个索引条目数错误。使用 `NOT INDEXED` 原始表扫描确认 3 组完全相同 manifest 的重复行：004 为 `2422,2423`，001 为 `2418,2424`，003 为 `2419,2425`。
- 停止四个 SQLite 写入容器后，先创建 1,647,013,888 字节一致性备份；三组重复行除 `id`、`created_at` 外全部业务列完全一致。所有引用并到最早的不可变对象，删除冗余身份行并重建索引。
- 修复后完整 `PRAGMA integrity_check = ok`；`foreign_key_check` 0；重复 identity 0；孤儿引用 0。修复后备份同为 1,647,013,888 字节，冷盘 `quick_check(1) = ok`。详细证据见 [sqlite-integrity-repair.md](sqlite-integrity-repair.md)。
- 重放 runs 93/94 的目录同步后，四本均保持唯一映射：001 `2418`、002 `2420`、003 `2419`、004 `2422`；material Popo run、Worker output Popo run 和 review asset run 完全一致。

### 9.4 外置备份与恢复闭环

- 备份根目录位于 `/Volumes/Elements/LuceonWeb2026-backups/luceonweb2026-review`，权限 `0700`，与 `runtime/backend` 的设备 ID 不同；运行配置已启用 `copy` 模式、包含历史 bucket、对象上限 2,000,000。定时调度在首次恢复演练前保持关闭，避免未验证备份自动重复排队。
- MinIO 实际清单约 1,646,506 个对象、224,481,701,460 bytes。job 1（上限 500,000）和 job 2（上限 1,000,000）均在清单达到上限时正确失败并产生 critical 告警，没有把截断清单标记为成功，也没有遗留 final 目录。
- job 3 使用上限 2,000,000 执行全量复制，UTC `05:45:44–07:51:35` 一次成功：清单和复制均为 1,565,474 个对象，复制 215,795,726,391 bytes，`truncated=false`、warnings 为空；原子 final 目录存在，`.partial` 目录不存在。586,742,968 字节 manifest 完整写入。
- 外置备份内含 1,647,013,888 字节应用 SQLite 快照，SHA-256 `0c244aaac0167edb741c8c88e29da167af6156e270179d9be801e8454fd44c9f`，`integrity_check=ok`、24 张表、权限 `0600`。
- 使用封版 backend 镜像在隔离目录执行真实恢复演练：10 个当前/历史 bucket 各选择一个非空对象，备份副本与实时 MinIO SHA 10/10 一致；SQLite 大小、SHA、完整性和表数全部一致，restore report 为 `passed`。演练失败的前两次仅为容器 Python 搜索路径调用错误，发生在读取 manifest 之前，未创建恢复目录；设置 `PYTHONPATH=/app` 后同一封版镜像一次通过。
- 恢复演练通过后，运行配置已启用 24 小时定时 copy、历史 bucket 和 2,000,000 对象上限；job 1/2 的 critical 上限告警保留失败历史并已确认，当前无 queued/running 备份任务。整个复制和恢复期间 backup Worker、backend、MySQL 与 MinIO 均 `restart=0`、`OOM=false`。
- 深度审计发现 job #3 的原始内嵌 `databases/application.db` 捕获了复制过程中的中间状态：job #3 自身为 `running`。资产副本、manifest、SQLite完整性和10个恢复样本没有损坏，但该数据库不能单独作为最终恢复点。原 job #3 目录保持不可变，没有为了报告变绿而篡改。
- commit `8538eb5` 修正 SQLite 快照自身终态，并让调度器跳过同一备份合约在间隔内的近期成功；commit `f8be353` 再补齐成功父任务与排队修复的一致性。新镜像启动并恢复 24 小时调度后，连续多个 5 秒轮询周期仍只有 job 1–3，没有创建 job 4/5、没有复制对象；job 3 为 `succeeded`、1,565,474/1,565,474、215,795,726,391 bytes、`truncated=false`。
- 为保留 job #3 资产副本的不可变性并提供立即可用的数据库恢复点，同一外置盘另建 `database-snapshot-f8be353-20260716` 恢复补充层，绑定 job #3 manifest SHA-256 `b10dfbd...b34a1`。该 1,647,013,888 字节 SQLite 由最终镜像在线快照，SHA-256 `3fcbeaa9...8d92`、`integrity_check=ok`、foreign key error 0、活动备份任务 0，job 3 终态/计数与清单一致。开发机内部盘对隔离副本执行冷盘全量 SHA+integrity 时，在高磁盘压力下 15 分钟无进展，已终止并删除临时副本；外置源快照未受影响。目标 Mac 必须把该补充层的隔离恢复复验作为生产硬门禁。下一次自然到期的全量 job 将由新代码直接生成包含正确终态的新整体备份。

### 9.5 当前开发环境封版复测

- 最终 `f8be353` 部署后，公网管理员登录 200。冻结窗口内连续 10 次公网 `/api/system/health` 与 `/settings` 共 20/20 返回 200，耗时分别约 0.12–0.14 秒和 0.13–0.15 秒；管理员 `/api/runtime/status` 返回 200/0.24 秒。
- 页面逐项核验工作概览、PDF 资产、解析任务、精修任务、比对审阅和运行设置。资产页显示 126 本；解析页显示 18 个管理员批次，#93 为 3/3、#94 为 1/1 成功且租约释放；精修页四本最新 Worker V2.3 均 succeeded，output 559–562 与各自 Popo run 一致。
- 运行状态显示 `ready`、blocker 0、warning 0、MinIO contract true、外部备份 ready、SQLite/Redis/Workflow MySQL/三类 Worker/Overleaf 全部 ready；GPU 为 `expected_off`、活动任务 0，没有把用户关机误报成应用故障。
- SQLite 再次 `integrity_check=ok`、foreign key error 0、重复 review identity 0、孤儿 material/output review 引用 0；四个 material ID 各唯一一行。Workflow MySQL `ready/ok`，WorkflowJob queued/running 0；Redis stream pending 0、lag 0。审计发现并归一化 4 条父任务已成功但仍显示 queued 的旧 sidecar 修复记录，精确 ID 为 40、41、49、53，记录保留并写入 `superseded by successful workflow completion`，处理后 repair queued 0。
- 四本 MinerU manifest 均实际存在并标记 `mineru_done_frozen`；四本 Popo manifest 均实际存在，schema 为 `luceon-gpu-wrapper-popo-from-frozen-mineru-manifest/v1`，material ID/run ID 与 SQLite、Worker input和审阅对象一致。GPU保持关机，本轮没有创建新 GPU batch 或恢复 Popo任务。
- 大样本 `asset_id=2422&output_id=562` 和小样本 `asset_id=2418&output_id=560` 的原/编译 PDF均在页面实际生成 canvas、无404/502或加载错误。大样本通过公网重新下载：原 PDF 60,553,426 bytes / 252页 / SHA `5c082394...f5b2`，审阅副本19,775,184 bytes / 252页，编译 PDF 6,347,950 bytes / 227页 / SHA `2f89c80b...95ac`，ZIP 9,517,198 bytes / SHA `0fdd7697...a28f`。
- ZIP顶层仍仅含 `images/`、`figure/`、`main.tex`、`elegantbook.cls`；图片1,185张，最大253,670 bytes，无超过1 MiB图片。使用当前固定 ShareLaTeX image ID在隔离、无网络、4 GiB限制容器中执行 `latexmk -xelatex` 成功，独立输出227页 PDF；ShareLaTeX复编前后均 `restart=0`、`OOM=false`。

### 9.6 Workflow MySQL 凭据与恢复

- 在轮换前创建 `runtime/backups/workflow/luceon_workflow-pre-credential-rotation-20260716.sql`，17,675,451 bytes、SHA-256 `8683a4e31494fd02a47ae7c3efde7a1dced1c63e5dfe312fd79f64ac2f3b75a4`、权限 `0600`。
- 隔离临时 schema 真实导入后，8/8 张表恢复，`workflow_jobs` 260/260、`stage_runs` 1,779/1,779；临时 schema 随后删除。第一次导入会话只得到 6/8 张表，严格验证正确失败、该临时 schema 被删除后重新完整恢复，没有把部分导入标成通过。
- Workflow MySQL 密码已轮换，开发和目标机私有 `0600` 环境文件同步更新；新凭据连接成功、旧凭据明确拒绝。旧环境备份和临时密钥仅在最终交付校验完成前保留，随后安全删除，不进入 Git、报告或公开包。
- 状态归一化后重新生成 `luceon_workflow-post-closure-20260716.sql`，17,675,639 bytes、SHA-256 `f742bb0723d1c88b1d58ee582c2dae553aa73da1251775eb54925c4b90b96144`、权限 `0600`。隔离恢复同样为 8 张表、`workflow_jobs=260`、`stage_runs=1779`，repair 状态为 failed 22 / succeeded 131 / superseded 1，临时 schema 已删除；目标迁移包使用这一份，不再使用轮换前 dump。

## 10. GPU 清理与关机条件

- MinIO 冻结和清单核验后，只清理本轮 GPU 临时批次/工作包：24 个目标，约 1,211,876,189 字节。
- 最终复核时 GPU overlay 为 81%，约 15 GiB 可用；Wrapper 队列、batch、MinerU、Popo 均为 0，GPU util 0%，三处工作根目录均无本轮四个 batch/run 的残留目录。百分比回升来自服务器其他数据/运行态，不是本轮临时产物回流。
- 结论：**GPU 可以关闭**。用户已确认服务器关机；封版、备份和目标机烟测阶段禁止创建新 GPU 任务，不因设置页显示离线而误判应用故障。

## 11. 页面证据索引

- `screenshots/01-settings-system-status.png`：设置与依赖状态。
- `screenshots/02-assets-after-dedup.png`：四样本上传去重。
- `screenshots/03-large-wave-running.png`、`04-large-wave-frozen.png`：大样本解析与冻结。
- `screenshots/05-worker-single-submit.png` 至 `09-large-outline-needs-review.png`：单本/批量提交及目录阻断。
- `10-worker-needs-review-handoff.png`、`11-large-candidate-pdf-render.png`：人工交接闭环。
- `12-four-sample-worker-succeeded.png`：四本 Worker succeeded。
- `13-large-compare-both-rendered.png`、`14-small-compare-both-rendered.png`：原/编译 PDF 渲染。
- `screenshots/15-final-lineage-downloads.png`：阶段下载。
- `screenshots/16-final-no-redeploy-compare.png`：大样本当前 Worker output 的原/编译 PDF 同屏渲染；最终物理索引修复不改变 PDF 内容。

## 12. 生产决策

**当前开发环境功能 UAT 已通过；最终生产部署候选结论等待外部备份作业 #4 与独立恢复复验。**

功能层结论是：四样本上传/去重、MinerU→Popo 自动串行、逐本冻结、AI 元数据、Worker V2.3、目录重建、needs_review 闭环、阶段下载、对比审阅和独立复编均已通过，精修质量已达到“可由人工继续完善”的本版本边界。SQLite 业务数据一致性、真实外置资产复制、数据库恢复补充层、16 GB 容量、备份调度去重和当前开发环境稳定窗口也已通过。

本结论严格区分两件事：

1. **当前开发环境功能 UAT 已通过**：四样本页面与资产链不需要重跑 GPU，固定基线为 `f8be353`。
2. **当前开发环境封版尚有一个硬门禁在执行**：必须由新镜像完成外部全量备份 #4，证明其内嵌 SQLite 的 #4 自身为成功终态，再完成隔离恢复复验和不改代码、不重部署烟测。完成前不提前批准生产部署候选。

另一台 Mac mini 不属于本轮范围；本报告既不要求其提供 SSH/配置，也不宣称其已经部署。

非阻断遗留项：解析任务列表公网响应约4–5秒；异步首屏会短暂显示0/空列表后再回填真实数据；独立 `latexmk` 因包内按契约不含 `reference.bib` 而提示 bibliography warning，但最终PDF成功生成且页数一致。这三项均不破坏数据、任务或下载闭环，列为下一版本性能/体验优化，不降低现有门禁。
