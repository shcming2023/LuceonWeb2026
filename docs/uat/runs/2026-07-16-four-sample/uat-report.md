# LuceonWeb2026 四样本用户链路 UAT 封版报告

> 最终判定：**生产阻断**。四本从页面上传到 GPU、Worker、审阅、下载和独立复编的功能链均已贯通；但当前开发部署存在 SQLite 索引损坏/重复审阅行、外部备份禁用、7.75 GiB Docker VM 下多次真实重启，以及最终代码部署后未完成一轮完全不改代码、不重部署的封版烟测。不得将本报告解释为生产批准。

## 1. 范围与验收口径

- 页面入口：公网 `http://152.136.183.144:15000/`。页面是验收面；SQLite、MinIO、GPU Wrapper、容器和日志只用于取证、诊断和通用修复。
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
- **阻断**：设置页备份依赖明确返回 `backup_disabled`，不是“备份写入通过”。正式环境必须配置并验证外部备份目标、写入、恢复演练和告警。
- 页面曾显示 GPU “按需关闭”，而 SSH/Wrapper 同时证明 GPU 在线；该状态刷新/语义漂移列为 Major，不能把静态策略文字当实时状态。

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
| 001 | `a4522e8c-0fb1-4c75-8b4d-232ca962d9c0` | 560 | succeeded；`03:44:19–03:44:54` | 2424 |
| 002 | `3c08ec78-3ab8-40dc-8f4d-adcdd2e7cbe3` | 559 | succeeded；`03:43:49–03:44:53` | 2420 |
| 003 | `470e2608-e123-44a1-a3d3-26b13e8440c6` | 561 | succeeded；`03:44:19–03:44:57` | 2425 |
| 004 | `7c27cde1-403a-4ca9-abde-c870d5ecfd5c` | 562 | succeeded；`03:43:50–04:21:10` | 2423 |

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

未发现样本名称、SHA、material ID、具体页码的生产代码硬编码；未降低门禁，未修改锁定模板。

## 8. 回归、构建与部署记录

- 后端最终全量：`625 passed, 905 warnings in 103.13s`。
- 后端晚期谱系定向回归：8 passed；前端 `npm run build` 通过；theme/auth/nginx/workflow-recovery/popo-resume/source-trace 契约测试通过。
- `graphify update .` 完成：4,646 nodes / 4,795 edges；`git diff --check` 通过。
- 当前开发镜像已重建/部署并恢复健康；但晚期谱系修复及数据库调查之后没有再完成一轮严格的“不改代码、不重部署”封版 UI 烟测，因此发布基线门禁仍未闭合。

## 9. 环境与数据库阻断证据

### 9.1 容量稳定性

- Docker VM 只有约 7.75 GiB。本轮真实压力下共享 MySQL restart counter 从 94 增至 109；backend 也发生过 restart 0→1→2，并出现一次 `Lost connection to MySQL server during query`。最终容器当前健康/restart=0只代表重新创建后的当前实例，不能抹去已发生的稳定性失败。
- 功能链通过，但不能据此证明正式 Mac mini 在目标并发与构建压力下无 OOM/重启。目标机必须提高/隔离内存，并以封版镜像进行不重部署贯通烟测。

### 9.2 SQLite 索引损坏与重复审阅行

- 最终一一对应核验发现 `PRAGMA quick_check` 报 8 个 `review_assets` 索引条目数错误。
- 使用 `NOT INDEXED` 的原始表扫描确认 3 组完全相同 manifest 的重复行：004 为 `2422,2423`，001 为 `2418,2424`，003 为 `2419,2425`。这解释了普通索引查询出现重复/错指。
- 已在停服务窗口创建 `runtime/backups/uat-20260716-index-repair/mineru-before-reindex.db`，SHA-256 `e4e457721c1f76324710eff5ac47730d21fe234f988ec45c33460e3c8d57bdf4`，权限 `0600`。`REINDEX` 因真实唯一键冲突被 SQLite 正确拒绝；未删除、合并或改写任何生产行，随后由该备份原样恢复，服务健康。
- 代码层的输出绑定已按本轮 Popo run 选择正确审阅对象；但物理库尚未恢复一致性，仍不满足生产门禁。需要另行授权：备份后重定向所有外键/引用、合并精确重复行、重建唯一索引、跑全量一致性与回归，再做封版烟测。

## 10. GPU 清理与关机条件

- MinIO 冻结和清单核验后，只清理本轮 GPU 临时批次/工作包：24 个目标，约 1,211,876,189 字节。
- GPU 磁盘使用率约 78.96% → 77.50%；Wrapper 队列、batch、MinerU、Popo 均为 0，GPU util 0%，无未同步目标目录。
- 结论：**GPU 可以关闭**。由用户关闭服务器。

## 11. 页面证据索引

- `screenshots/01-settings-system-status.png`：设置与依赖状态。
- `screenshots/02-assets-after-dedup.png`：四样本上传去重。
- `screenshots/03-large-wave-running.png`、`04-large-wave-frozen.png`：大样本解析与冻结。
- `screenshots/05-worker-single-submit.png` 至 `09-large-outline-needs-review.png`：单本/批量提交及目录阻断。
- `10-worker-needs-review-handoff.png`、`11-large-candidate-pdf-render.png`：人工交接闭环。
- `12-four-sample-worker-succeeded.png`：四本 Worker succeeded。
- `13-large-compare-both-rendered.png`、`14-small-compare-both-rendered.png`：原/编译 PDF 渲染。
- `screenshots/15-final-lineage-downloads.png`：阶段下载。
- `screenshots/16-final-no-redeploy-compare.png`：晚期修复前的封版烟测；因其后仍有代码部署，不能作为最终发布烟测证据。

## 12. 生产决策

**生产阻断。**

功能层结论是：四样本上传/去重、MinerU→Popo 自动串行、逐本冻结、AI 元数据、Worker V2.3、目录重建、needs_review 闭环、阶段下载、对比审阅和独立复编均已通过，精修质量已达到“可由人工继续完善”的本版本边界。

解除阻断必须同时满足：

1. 经授权修复 SQLite 重复行和全部损坏索引，`PRAGMA integrity_check` 为 `ok`，一一对应查询不依赖损坏索引也一致。
2. 启用外部备份并完成真实写入与恢复演练。
3. 在目标 Mac mini 提供足够且隔离的内存，证明无 OOM、异常重启或长期无进度任务。
4. 用同一封版 Git commit/镜像，在不改代码、不重建、不重部署条件下完成一轮批量 UI 贯通烟测。

以上四项完成前，不批准生产部署。
