# LuceonWeb2026 三样本生产级端到端 UAT 报告

日期：2026-07-14
执行入口：公网 `http://152.136.183.144:15000/`
最终结论：**生产通过**

## 1. 决策摘要

三个真实 PDF 均通过公网页面完成上传、身份与去重、GPU 串行 MinerU、逐本冻结、GPU 串行 Popo、逐本冻结、Worker V2.3、核心质量门禁、PDF 对比、页面下载 ZIP 和独立 XeLaTeX 复编。

最终状态同时满足：

- 文件名、material ID、Worker job、review asset 和 output ID 一一对应；
- 三本 MinerU/Popo 均有正式清单和冻结标记，活动标记、运行中任务、Redis pending 和 Worker 活动任务均为 0；
- Worker V2.3 三本最终均为 `succeeded`；所有中间 `needs_review` 均保留候选件、问题清单和人工交接记录，并从最小失败阶段重新验证闭环；
- 三本最终缺字数 0、大于 10pt 溢出 0、未解析图片/资源 0；
- ZIP 根目录、大小、图片大小、图片文件名与数量、模板、固定 figure 资产和自定义命令/环境约束全部通过；
- 三个下载 ZIP 均在独立 TeX Live 2025 XeLaTeX 环境两遍复编成功，首/中/末页渲染抽检通过；
- 三个公网对比页均显示正确对象，原 PDF 和编译 PDF 均实际渲染，最终复核无 404、502 或超时；
- 后端、Worker、前端和 Redis 均无 OOM 或异常重启，队列无滞留。

GPU 已由用户在冻结结果确认后关闭。关机前未执行本轮 GPU 临时目录清理；为避免重新开机计费，本轮不再唤醒 GPU。该项记为 Minor 运维偏差，不影响已经写入 MinIO 的冻结产物和本次生产判定。

## 2. 范围与原则

本轮只处理 `/Users/concm/Desktop/test` 的三个样本，不重刷历史对象、不删除生产数据、不修改锁定模板、不降低门禁、不用 API 200 冒充页面通过，也未提交或推送 Git。命令行、数据库、MinIO、日志和容器只用于监控、取证、通用修复、部署及最小失败阶段恢复。

## 3. 源文件与身份映射

| 源文件 | 大小（bytes） | 页数 | SHA-256 | material ID | DB PK | review asset | Worker job | output ID |
| --- | ---: | ---: | --- | --- | ---: | ---: | --- | ---: |
| `Coxhead AWL.pdf` | 78,077 | 2 | `c953cb08f79c2d114c55e4078c82f53af69bc154a73ed0f78a38634183f278ab` | `pdf-c953cb08f79c2d11` | 1334 | 2412 | `9ee93a13-89cf-4215-968c-d5bd452099e5` | 553 |
| `2025.pdf` | 175,841 | 3 | `642599641f3b15e11b19f383379864081464be1f9c79bdd4f1e9334489c4b1ad` | `pdf-642599641f3b15e1` | 1335 | 2410 | `dc6e5234-c45d-41e7-a009-f744675b2a8a` | 554 |
| `数学寒假生活G7 A册.pdf` | 905,120 | 31 | `6f3dd4b91dedf81e0a2f7508b4518b9b20ad0012f535aedafc8da80dcde39992` | `pdf-6f3dd4b91dedf81e` | 1336 | 2411 | `d06e3173-8b57-44d7-9d64-a883d4cb52b6` | 555 |

上传前按文件名和预期 material ID 搜索均为 0；页面上传后新增且仅新增上述三条记录。源对象名称、字节数和完整 SHA-256 与本地源文件一致。

## 4. GPU 串行执行与冻结

页面 Pipeline run 为 90。MinerU 和 Popo 各自以三文档批次提交，但 Wrapper 内按 001、002、003 串行执行；单本成功立即冻结，因此任一本失败不会回滚其他样本。

### 4.1 批次

- MinerU batch：`mineru-20260714045935-staged_mineru_20260714045932-4ca11b88`，`succeeded`，批次 61.979s。
- Popo batch：`popo-20260714050108-staged_popo_20260714050105-5f3cccff`，`succeeded`，批次 331.419s。

### 4.2 单本 run 与耗时

| 样本 | MinerU run / 耗时 | Popo run / 耗时 |
| --- | --- | --- |
| Coxhead | `mineru-20260714045935-staged_mineru_20260714045932-4ca11b88--001-staged_c953cb08f79c2d11_001` / 22.780s | `popo-20260714050108-staged_popo_20260714050105-5f3cccff--001-popo_c953cb08f79c2d11_001` / 146.971s |
| 2025 | `mineru-20260714045935-staged_mineru_20260714045932-4ca11b88--002-staged_642599641f3b15e1_002` / 9.543s | `popo-20260714050108-staged_popo_20260714050105-5f3cccff--002-popo_642599641f3b15e1_002` / 1.083s |
| G7 | `mineru-20260714045935-staged_mineru_20260714045932-4ca11b88--003-staged_6f3dd4b91dedf81e_003` / 26.079s | `popo-20260714050108-staged_popo_20260714050105-5f3cccff--003-popo_6f3dd4b91dedf81e_003` / 165.441s |

### 4.3 MinIO 清单和状态标记

每本在 `eduassets-input/_status/<material_id>/` 下均准确存在三类终态标记：

1. `<mineru-run>.mineru_done_frozen.json`；
2. `<popo-run>.popo_done_frozen.json`；
3. `<popo-run>.done.json`。

三本对应的正式 `eduassets-mineru/mineru/.../manifest.json`、`eduassets-minerupopo/minerupopo/.../manifest.json` 和最终 Worker/LaTeX manifest 均存在；单本清单大小分别为：

| 样本 | MinerU manifest | Popo manifest | 最终 LaTeX manifest |
| --- | ---: | ---: | ---: |
| Coxhead | 19,654 bytes | 30,923 bytes | 4,832 bytes |
| 2025 | 16,555 bytes | 26,577 bytes | 4,198 bytes |
| G7 | 187,405 bytes | 136,890 bytes | 39,328 bytes |

最终活动状态标记为 0，三条材料 `pipeline_status=idle`，不存在遗留 submitted/running/processing 标记。

## 5. Worker V2.3、重试与最小阶段恢复

| 样本 | 开始至最终完成 | 最终排版 attempt | 最终核心 QA attempt | 最终状态 |
| --- | --- | ---: | ---: | --- |
| Coxhead | 05:25:32–06:39:19 UTC（73m47s，含人工审阅/部署等待） | 4 / 7s | 3 / 1s | `succeeded` |
| 2025 | 05:25:31–06:40:33 UTC（75m02s，含人工审阅/部署等待） | 5 / 6s | 6 / 1s | `succeeded` |
| G7 | 05:25:26–06:41:24 UTC（75m58s，含人工审阅/部署等待） | 5 / 10s | 5 / 3s | `succeeded` |

所有恢复均从具体失败阶段开始，未重跑冻结 MinerU/Popo：

- Coxhead：早期 canonical/排版失败后恢复；核心 QA 曾因错误的 ZIP 超限判定进入 `needs_review`。
- 2025：outline 深度、错误 ZIP 超限及缺人工交接记录曾进入 `needs_review`。
- G7：outline 父级/层级、语义审阅项、Unicode 数学符号缺字曾进入 `needs_review`。
- 最终图片清单修复后，页面使用新增的“从排版构建重新运行”，仅重跑 `deterministic_elegantbook` 及核心 QA。

闭环证据：每个 `needs_review` attempt 都保留不可变 manifest 和候选 artifact；三本均存在 `manual_handoff=succeeded`；候选 PDF、问题证据和待修复项目 ZIP 可由 Worker 抽屉访问；重跑后新 attempt 独立写入且最终均 `succeeded`，未覆盖失败证据。

## 6. 核心质量门禁

三个当前 output 的核心报告均为 `passed`，blocker 数组为空，三遍编译字节一致性通过。

| 门禁 | Coxhead | 2025 | G7 |
| --- | ---: | ---: | ---: |
| 缺字数 | 0 | 0 | 0 |
| 大于 10pt 溢出 | 0 | 0 | 0 |
| 未解析图片/资源 | 0 | 0 | 0 |
| LaTeX error / undefined ref | 0 / 0 | 0 / 0 | 0 / 0 |
| 模板/固定 figure 完整 | 通过 | 通过 | 通过 |
| 新增自定义命令/环境 | 0 | 0 | 0 |
| Popo 图片清单保持 | 3/3，完全一致 | 0/0，完全一致 | 168/168，完全一致 |

锁定模板哈希：

- `elegantbook.cls`：`048c3b90da41be64f4744da3bff6ae8c5ea7abd30a5f3e2a6ad1a98f3b0d71fe`（三本一致）；
- `figure/logo-blue.png`：`e11c44cd0d23767e58140ef2abe77025d817220717d734fcd68fc3d402de7bb0`；
- `figure/cover.png`：`a756e026bf8ca0f59e0cc9820f45d765709103137a2c6fcc9f5ee8b15cb25a30`；
- 三本 `main.tex` 导言区均与锁定模板一致，正文未增加命令或环境定义。

## 7. 页面 PDF 对比与截图

| 样本 | 公网 compare 对象 | 原 PDF / 编译 PDF | 页面结果 |
| --- | --- | --- | --- |
| Coxhead | `asset_id=2412&output_id=553` | 2 / 7 页 | 两侧实际渲染，HTTP 200 |
| 2025 | `asset_id=2410&output_id=554` | 3 / 4 页 | 两侧实际渲染，HTTP 200 |
| G7 | `asset_id=2411&output_id=555` | 31 / 46 页 | 两侧实际渲染，HTTP 200 |

最终公网 `/files` 及三个 compare URL 均为 HTTP 200，响应约 0.13–0.16s；最终浏览器复核无 404、502 或超时。

主要页面证据：

- `docs/uat/evidence/2026-07-14-three-sample/01-files-run-90-running.jpeg`：页面 run 90，三本任务对应；
- `docs/uat/evidence/2026-07-14-three-sample/17-final-three-succeeded.jpeg`：三本 Worker V2.3 最终 succeeded，SHA-256 `e85a6e55ccc178db63ed0ce09e14bbd58feab8e46c788d5a9f7f5d32a7aa4c90`；
- `14-g7-compare.jpeg`：SHA-256 `f9b4c0aa4b0efcda447e44b017f4c1da1629e7206220c6d5b6518c3d57961b49`；
- `15-2025-compare.jpeg`：SHA-256 `9432a149277405e8871c325044e7fe2ec8832a03f245389db5da082b60d8432d`；
- `16-cox-compare.jpeg`：SHA-256 `07850592226dc2b77091d5b975b6368049c364d3f37b95c8f1d1c4b9c18d899b`。

## 8. 页面下载 ZIP 与独立复编

ZIP 均从 compare 页面点击下载，不是通过后端或 MinIO 绕过 UI 获取。

| 样本 | ZIP 大小 | ZIP SHA-256 | 图片数 | 最大图片 | 根目录约束 |
| --- | ---: | --- | ---: | ---: | --- |
| Coxhead | 1,277,661 bytes | `87928dc8fba2dda9def8376b14a73c7e1a56e0b36ac62bc660b7dc7c50e45e2c` | 3 | 420,527 bytes | 通过 |
| 2025 | 613,615 bytes | `481c03a9a2a04cf118eb10a7d2e3086ca1bcb9a63928132cdd9057f7f32c96bc` | 0 | 0 | 通过 |
| G7 | 1,712,534 bytes | `879a0cd0e7893527f7d7632ad97fb65b482ca3520075d48faf299dde4979ee0a` | 168 | 138,730 bytes | 通过 |

每个 ZIP 解压后根目录且仅有 `images/`、`figure/`、`main.tex`、`elegantbook.cls`；全部小于 50MB，每张图片小于 1MB，Popo 冻结图片文件名与数量完全保持。

独立环境为 ShareLaTeX 容器内 TeX Live 2025；每个浏览器下载 ZIP 全新解压后运行两遍 XeLaTeX：

| 样本 | 复编 PDF | 页数 | PDF SHA-256 | 结果 |
| --- | ---: | ---: | --- | --- |
| Coxhead | 651,254 bytes | 7 | `8f00f5a6d64c9c12464eff802f57692f58213058caaa5b6d05682889c06f865a` | 成功，缺字/溢出/error/ref 均 0 |
| 2025 | 779,763 bytes | 4 | `8ccf5e4e2e54202861e13942fa2c0e8e40989f51c10f13537a6b674ef2bd30a6` | 成功，缺字/溢出/error/ref 均 0 |
| G7 | 2,038,585 bytes | 46 | `1f5a424aa9172e7b0ac119e4f7d5812220a3e6ca10939c5d6b23286e0fcb4952` | 成功，缺字/溢出/error/ref 均 0 |

首/中/末页共 9 页使用 Ghostscript 独立渲染并人工抽检，图文、中文、公式和图片均可见，无明显裁切；证据在 `docs/uat/evidence/2026-07-14-three-sample/rendered/`。

## 9. 缺陷、根因与修复

| ID | 判级 | 现象与根因 | 通用最小修复 | 回归/闭环 |
| --- | --- | --- | --- | --- |
| UI-001 | Minor | 未选择目标时预检走全局慢路径，用户感知卡死 | 本轮终止未提交 GPU 的残留预检；明确三目标后走定向预检 | 三本精确选择并成功创建 run 90；建议后续补空选择即时提示 |
| NET-001 | 恢复事件 | 后端至 GPU Wrapper 一次超时，预检以 `GPU_OFFLINE` 正确阻断 | 核验 Wrapper/端口后从提交阶段重试 | 未创建重复 GPU job，随后三本串行通过 |
| OUT-001 | Blocker，已修复 | 同事务注册 output 后未 flush，compare 可能拿不到 output ID | current 查询前 flush | compare 的 asset/output/download 一致 |
| ORCH-001 | Blocker，已修复 | 旧 V1 自动队列可能与 V2.3 重复消费 | 冻结 V1 batch/auto-retry，仅允许显式 V2.3 | health 显示两项 frozen，三本仅一个 V2.3 job |
| NET-002 | Blocker，已修复 | Nginx 缓存后端容器 IP，重建后可出现 502 | 使用 Docker DNS 动态解析 | 前端静态回归通过，最终公网无 502 |
| DATA-001 | Blocker，已修复 | raw/outline/semantic 对短文档和练习层级的通用规则会错误 needs_review 或丢层级 | 修正守恒、层级与 problem-group 通用规则 | 三本从原失败 stage 恢复；未按文件名/material ID 硬编码 |
| UI-002 | Blocker，已修复 | 非排版 `needs_review` 缺少可操作恢复，且 retry 有重复入队风险 | 增加精确阶段恢复、人工交接和单次入队 | 三本 handoff 均 succeeded，失败 attempt 保留，最终闭环 |
| LATEX-001 | Blocker，已修复 | 空 `images/`/`figure/`、Unicode `∠/∵/△` 和错误 ZIP 体积证据造成假失败 | 恢复必需空目录、通用符号归一化、校正 bundle 证据 | 缺字 0、ZIP 约束通过 |
| IMG-001 | Blocker，已修复 | Worker 只复制被正文引用的图片，Popo 3/0/168 张变成 0/0/145 张，违反清单保持 | 从冻结 Popo manifest 校验 SHA 并按原名物化全部图片；写 `delivery-image-inventory.json`，漂移即 blocker | 最终 3/3、0/0、168/168 完全一致；新增 runner/validation 测试 |
| DEPLOY-001 | 已恢复事件 | 增量部署时共享镜像一度继承 Worker CMD，后端短暂 502 | 重新 commit 时显式保留 backend uvicorn CMD，并分别按 compose command 启动 | 无任务/数据影响；最终所有容器 restart=0、OOM=false |
| BUILD-001 | Minor | Docker Desktop 镜像源 `mirror.baidubce.com` DNS 阻止完整远程构建 | 使用已构建基础镜像做可复现的容器内增量验证与部署 | 运行镜像和代码已核对；建议修复镜像源后补一次 clean build |
| TOOL-001 | 工具限制 | bundled Browser 插件报 `Cannot redefine property: process` | 改用已启用的 Computer Use 控制 Chrome，关键用户链路仍由页面完成 | 页面截图和下载证据齐全，不影响产品判定 |

所有生产修复均为通用规则，未按书名、文件名、material ID 或具体页码硬编码。

## 10. 测试与部署记录

- 三样本首次收口时完整后端回归：**555 passed**；补充手工样本修复后再次运行当前工作树完整后端回归：**561 passed**。初次用旧 committed image 运行时出现 1 个已修复的环境依赖测试失败，挂载当前工作树重跑后全部通过。
- 图片清单/runner/validation 定向回归：33 passed。
- 前端 Worker V2 恢复契约脚本通过；`vue-tsc` 与 Vite 生产构建通过。
- `git diff --check` 通过。
- 当前部署镜像：backend/Worker `sha256:abab50c266c86ec330d39a7fc58d148c2def4f522082769d0e68ba32991475a9`；frontend `sha256:f5f3a123e844574f09a40c228d9bf3a88e844938a9a78640b76f9403cb8f976c`。
- backend、Worker、frontend、Redis 均 `restart=0`、`OOMKilled=false`；Worker V2.3 health 为 MySQL ready、worker available。
- Redis stream 1530 条均已消费，pending=0、lag=0、execution lock=0；Workflow DB 全局 queued/running=0，PipelineRun 全局 queued/running=0。
- 公网 `/files` 和三个最终 compare URL 均 HTTP 200。
- 未执行 Git commit 或 push。

## 11. 清理、磁盘与关机

- 本机数据卷可用约 286GiB；Docker build cache 可回收约 18.68GB，属于本机环境，不在本轮自动删除范围。
- 本轮本地验证临时文件约 11.2MB，不影响生产服务；ShareLaTeX 复编临时目录在取证后可安全清理。
- MinIO 冻结结果已确认；不存在本轮遗留 Worker/GPU 活动任务。
- GPU 服务器已由用户关闭，停止继续计费。
- 偏差：GPU 关机前未执行仅本轮临时目录清理。由于重新开机只为清理会产生新费用且不能改善冻结产物，本轮不再唤醒；下次开机时应先按 run/batch ID 做范围限定清理，不删除其他历史对象。

## 12. 遗留问题与建议

无未解决 Blocker 或 Major。

Minor：

1. GPU 临时目录清理延后到下次开机窗口；必须只按本轮 batch/run ID 清理。
2. 空选择预检缺少即时 UI 提示，可补前端禁用态/提示和请求取消测试。
3. Docker Desktop 镜像源 DNS 应修复，并补一次从 Dockerfile 的 clean rebuild；当前运行产物不受影响。
4. Python/SQLAlchemy 存在弃用与字符串转义警告，未影响本轮结果，建议单独治理，避免混入 UAT 修复。

## 13. 最终生产判定

**生产通过。**

依据不是单一 API 状态，而是三个真实样本逐本完成页面用户链路、MinIO 冻结、Worker V2.3、核心门禁、对比渲染、页面 ZIP 下载、图片与模板审计、独立 XeLaTeX 复编及运行时队列/容器健康核验。当前无生产阻断项。

## 14. 补充手工样本回归（不替代三样本主判定）

三样本生产判定完成后，用户又从同一真实样本目录补充提交 `新教材全解 五上 数学.pdf`，并要求手工走完页面流程。本样本用于扩大到 252 页、1,192 张图片的大体量教材场景；它不替代第 3 节的三个主样本，但其最终结果进一步支持“生产通过”。

### 14.1 身份、GPU 冻结与最小恢复

| 项目 | 结果 |
| --- | --- |
| 源文件 | 60,553,426 bytes，252 页，SHA-256 `5c08239421effc942ceacca225d9cbb950b89018c1fd3ed2d82266dd8758cfb2` |
| material / DB PK | `pdf-5c08239421effc94` / 1337 |
| MinerU batch / run | `mineru-20260714070955-staged_mineru_20260714070953-2be9e23b` / `mineru-20260714070955-staged_mineru_20260714070953-2be9e23b--001-staged_5c08239421effc94_001` |
| MinerU 结果 | `mineru_done_frozen`，162.268s；清单 1,224,303 bytes；该前置结果后续未重跑 |
| Popo batch / run | `popo-20260714074632-staged_popo_20260714074622-cd92463c` / `popo-20260714074632-staged_popo_20260714074622-cd92463c--001-popo_5c08239421effc94_001` |
| Popo 结果 | `popo_done_frozen`，1,295.831s；清单 737,909 bytes；2,402 个对象、68,181,346 bytes |
| 页面 Pipeline | run 91 在 MinerU 已冻结后因连接拒绝失败；页面“恢复 Popo”创建 run 92，复用冻结 MinerU 后成功，未制造重复 GPU 任务 |
| 最终状态标记 | 仅 `mineru_done_frozen`、`popo_done_frozen`、`done` 三个终态标记；submitted/running 活动标记为 0 |

### 14.2 Worker V2.3 与审阅闭环

- Worker job：`ac4e305a-a996-4126-8ad6-d2da93b4c20a`，08:21:07–09:06:19 UTC，最终 `succeeded`；review asset 2414；output 558，`promoted / passed / current`。
- canonical、outline、semantic 均只执行一次并冻结为 artifact 1418、1419、1420；最终排版 artifact 1429，最终核心 QA artifact 1430。所有修复只重跑 `deterministic_elegantbook` 和其后的核心 QA。
- 排版 attempts 1/2 为编译失败，3 为符号缺字 `needs_review`，4/5 暴露旧诊断假阴性，6 在完整日志门禁下正确回到 `needs_review`，7 最终成功；两次人工交接和“修复后重新验证”均有记录，候选件与失败 manifest 未覆盖。
- 最终排版 manifest SHA-256 `afa9cdf3476af8d489323edfbd6b65584f85d434a66309a7e80fc268ee66bb04`；最终核心 QA manifest SHA-256 `7f5c38a39af92bb8f706e8ead1be050c20e3cf83d020d8b2a0b14c055f92a264`。

### 14.3 本样本发现并完成闭环的通用缺陷

| ID | 判级 | 根因与修复 | 回归结果 |
| --- | --- | --- | --- |
| LATEX-002 | Blocker，已修复 | 复编门禁读取 XeLaTeX 控制台尾部，未读取完整 `main.log`，导致页面下载 ZIP 实际有 7 个缺字仍显示绿色；改为容器内读取完整 `main.log` 并明确记录 `diagnostic_log=main.log` | 新增完整日志优先回归；最终内部与独立复编缺字均为 0 |
| LATEX-003 | Blocker，已修复 | 缺字解析器只识别 `(U+XXXX)`，未识别 XeTeX 的 `("XXXX)` 形式；正则同时支持两种格式 | 新增 quoted-hex 回归；attempt 6 正确检出 141 个缺字而非假通过 |
| LATEX-004 | Blocker，已修复 | 旧自动 CJK fallback 全局向正文注入 IPAexMincho，造成锁定 `main.tex` 漂移并扩大缺字；删除全局 fallback，只在数学和 `array` 内用锁定 `zhsong` 包裹 CJK，同时将 `ⓞ` 做通用锁定符号归一化 | 普通正文、模板、导言区不再改写；相关定向回归 152 passed，完整后端回归 561 passed |

修复未按书名、material ID 或页码硬编码，未新增自定义命令/环境，未修改 `elegantbook.cls` 或固定 figure 资产。

### 14.4 最终门禁、页面下载与独立复编

| 项目 | 最终结果 |
| --- | --- |
| 内部 XeLaTeX | TeX Live 2025，4 遍；228 页；最后两遍 PDF SHA-256 均为 `efd26a0da42115e48951563b0eb8c35678e20cdd31360106d8437ec0d4cb0324` |
| 核心门禁 | 缺字 0；overfull hbox 0；大于 10pt 溢出 0；未解析引用/资源 0；blocker 为空 |
| 页面下载 ZIP | 9,521,760 bytes；SHA-256 `b29523d0c04718e6ce59a8ebe73a992df315b7073a11751b170c2f943cd57b27`；与 Worker 清单完全一致 |
| ZIP 内容 | 仅 `images/`、`figure/`、`main.tex`、`elegantbook.cls`；1,196 个文件；1,192 张图片；最大图片 253,670 bytes；超 1MB 图片为 0 |
| 模板与固定资产 | `elegantbook.cls` SHA-256 `048c3b90da41be64f4744da3bff6ae8c5ea7abd30a5f3e2a6ad1a98f3b0d71fe`；logo/cover 哈希与第 6 节一致 |
| 独立复编 | 浏览器下载 ZIP 全新解压后，在 ShareLaTeX/Overleaf 目标 XeLaTeX 环境 4 遍成功；228 页、6,336,753 bytes，完整 `main.log` 的四项核心诊断均为 0 |
| 公网 compare | `asset_id=2414&output_id=558`；正确显示文件名、material ID、Worker job；原 PDF 252 页和编译 PDF 228 页均实际渲染 |

截图证据：

- `18-extra-overleaf-xelatex-success.jpeg`：独立 Overleaf 项目复编成功并实际渲染，SHA-256 `a7425ec5e0bc0f286f7e57a3fa54d5d6d21413974eea0e970852c1d32bbbb1e4`；
- `19-extra-compare.jpeg`：公网 compare 正确对象及双 PDF 渲染，SHA-256 `53c9ae9af578b15a797cbf36284ab4de503aff5795d206b3a3bb295605745d3c`。

最终运行时复核：Workflow job、stage run 和 Pipeline run 的 queued/running 均为 0；backend、Worker、frontend、Redis 均 `restart=0`、`OOMKilled=false`。公网入口曾出现一次约 8 秒瞬时不可达，随后远端 `:15000` 监听、远端回环访问及公网连续三次 `/files`/compare 均恢复为 HTTP 200（约 0.13–0.15s），未发生容器重启或任务重跑，归类为已恢复网络事件。本轮补充样本的本机解压目录、复编日志/PDF 和 ShareLaTeX 临时目录已按明确路径清理；浏览器实际下载 ZIP 与报告截图作为 UAT 证据保留。GPU 主机当前 SSH 立即断开且 Wrapper 无服务响应，已处于不可操作/停止态，因此未为清理本轮 GPU 缓存重新开机，仍按第 11–12 节的下次开机范围限定清理建议处理。

**补充手工样本结论：通过；三样本生产结论仍为生产通过。**
