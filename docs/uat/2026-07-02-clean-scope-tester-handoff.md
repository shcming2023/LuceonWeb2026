# LuceonWeb2026 Clean-Scope UAT 测试交接清单

日期：2026-07-02

> 历史基线说明：本文记录 2026-07-02 的 Clean-scope 验收边界。当前
> 2026-07-07 阶段已切换到 `/review/compare` 的 PDF/ElegantBook 比对主线；
> 不要再把 Raw/Clean/Standard/Final Review 页面作为主 UI 验收入口。

## 本轮边界

本轮只验收到 Clean：

- 包含：登录注册、设置页 MinIO/模型 Key 感知、文件管理、已有 MinIO 样本、PDF 审查、目录审查、Popo -> Raw、Raw -> Clean。
- 不包含：GPU 服务器侧探针、新 GPU 解析压测、Clean -> Standard、Standard 输出审查、Final Review、终审报告导出。
- GPU 说明：GPU 服务器可关闭。本轮使用 MinIO 中已有的 100+ 份 MinerU/Popo 产物做验证，不需要启动 GPU。

## 环境启动

在项目根目录执行：

```bash
docker compose --env-file .env.luceon-review -f docker-compose.luceon-review.yml up -d
```

访问地址：

- 前端：`http://localhost:28081`
- 后端 API：`http://localhost:28080/api`
- 旧入口兼容：`/cms/tasks` 应自动进入 `/files`，不得出现只有侧边栏、主区域空白的页面。

启动后先确认：

```bash
docker compose --env-file .env.luceon-review -f docker-compose.luceon-review.yml ps
docker compose --env-file .env.luceon-review -f docker-compose.luceon-review.yml exec -T backend python -m alembic current
```

验收标准：

- frontend/backend/redis 均为 `Up`。
- Alembic revision 为 `20260630_add_weknora_chapter_status_fields (head)`。

## 可选自动冒烟

如果只想快速确认 Clean-scope API 合同，可运行：

```bash
python backend/scripts/uat_clean_scope_smoke.py
```

该脚本会：

- 默认复用 `uat-clean-smoke@example.test`，不存在时自动注册，并验证错误密码拦截。
- 检查 MinIO 合约桶和模型 Key。
- 执行 `/materials/sync?limit=1000`。
- 从已有 Clean 材料中抽样 3 个 review asset，验证 PDF、首页图片、MinerU/Page/Popo Markdown、`source_map`、`outline_review`。
- 检查已有下游资产的材料没有指向 input-only review asset。
- 明确跳过 GPU、Standard、Final Review。

当前 UAT 用户 `uat-clean-smoke@example.test` 的最新样本池：

- Total materials: 122
- Popo: 119
- Raw: 25
- Clean: 7
- Standard: 3，仍属于本轮排除项。
- `AMC8_2026_Solutions.pdf` 已从 popo-only 执行到 Clean，可用于验证新材料后续节点自然进入 Raw/Clean 审查链路。

## 必测用例

### 1. 认证

步骤：

1. 打开 `/login`。
2. 使用新邮箱和 6 位以上密码注册。
3. 退出后重新登录。
4. 用错误密码尝试登录。

预期：

- 注册成功并进入系统。
- 正确密码登录成功。
- 错误密码提示 `邮箱或密码错误`，不得进入系统。

缺陷定级：失败则记为 Blocker/Critical。

### 2. 设置页状态

步骤：

1. 登录后进入“设置-系统状态”。
2. 检查 MinIO、模型 Key 状态。
3. 不要求检查 GPU；如果页面显示 GPU warning，本轮不按 blocker 处理。

预期：

- MinIO 合约桶存在。
- LLM/Vision 模型 Key 可用或给出清晰阻断提示。
- 不因 GPU 关闭阻断本轮 Clean-scope 验收。

缺陷定级：

- MinIO 合约桶缺失且无法创建：Blocker/Critical。
- 模型 Key 缺失但 Raw/Clean 必需节点无明确提示：Blocker/Critical。
- GPU warning：本轮排除，不记录为本轮 blocker。

### 3. 文件列表与阶段防呆

步骤：

1. 在文件管理页执行同步或刷新。
2. 观察已有样本的阶段标识。
3. 找一个 input-only 材料，确认不会展示“生成 Raw / 生成 Clean”可执行按钮。
4. 找一个已有 Popo/Raw/Clean 样本，确认 Raw/Clean 相关入口只在前置条件满足时出现。

预期：

- input-only 材料不得允许直接生成 Raw/Clean。
- 如果绕过前端直接请求后端 start 接口，后端应返回 `409` preflight blocker，而不是 500 硬报错。
- 已有下游资产的材料不得被重复上传污染为 input-only 审查资产。
- `/cms/tasks`、登录 redirect 或旧收藏链接不得落到废弃空白页，应回到 `/files`。

缺陷定级：

- 前端按钮放开且后端未拦截，导致硬报错：Blocker/Critical。
- 下游审查资产被覆盖，导致 Popo/PDF 审查 404：Blocker/Critical。

### 4. Raw/Clean 单点预检弹窗

步骤：

1. 选择已有 Popo 的材料，点击“生成 Raw”或“重建 Raw”，只打开弹窗，不确认执行。
2. 选择已有 Raw 的材料，点击“生成 Clean”或“重建 Clean”，只打开弹窗，不确认执行。

预期：

- Raw 弹窗显示 Material ID、Popo Run、MinerU Run、目标 `eduassets-raw` 路径。
- Clean 弹窗显示 Material ID、Raw Run、来源 `eduassets-raw`、目标 `eduassets-clean` 路径。
- 文案能区分首次生成、重建覆盖、Clean stale 影响。

缺陷定级：

- 信息缺失但流程可用：Major/Minor。
- 弹窗误导导致可能覆盖错误材料：Blocker/Critical risk。

### 5. PDF 解析审查

建议抽样：

- `AMC8_2026_Solutions.pdf`
- `Grammar Friends 6 (Students Book) (Flannigan E.) (Z-Library).pdf`
- `Reading Explorer 1 Students Book.pdf`
- `中学生世界 八上 数学 上册.pdf`

步骤：

1. 从文件列表点击“PDF审查”。
2. 检查源 PDF 能加载。
3. 切换 MinerU/Popo/对照视图。
4. 翻页或点击溯源框。

预期：

- 源 PDF 不返回 404。
- MinerU/Popo 文本视图加载成功。
- `source_map` 缺失或为空时，应显示 `无溯源数据`，不能空白或崩溃。

缺陷定级：

- 源 PDF 404：Blocker/Critical。
- Popo/MinerU 视图 404 且无降级提示：Blocker/Critical。
- 空 source_map 文案不友好：Enhancement。

### 6. 目录重建审查

步骤：

1. 对已有 Raw 或 Clean 的材料点击“目录审查”。
2. 检查目录树、Raw 内容、Clean 内容和 PDF 联动。
3. 对 dry-run 材料，确认页面有 dry-run 或待发布语义提示。
4. 对 `AMC8_2026_Solutions.pdf`，确认 `/review/outline?asset_id=1844` 可打开 Raw/Clean 两栏，且列表阶段为 Clean。

预期：

- 目录树正常加载。
- Raw/Clean 可审状态清楚。
- 缺失内容有友好提示，不阻断页面整体加载。

缺陷定级：

- 目录审查接口或页面整体不可用：Blocker/Critical。
- 目录层级、标题归属、图片归属不完美：Major/Minor/Enhancement，除非直接阻断流程。

### 7. 批量 Clean 队列

本轮不建议对真实大批样本做破坏性批量重跑。测试时可只做小样本或代码/页面行为核对。

预期：

- 批量队列按顺序单线执行。
- 点击“停止后续”后，当前任务完成，后续队列不再启动。
- 不应出现任务永久卡在 `running` 且无法恢复。

缺陷定级：

- 卡死、状态无法恢复、无 error_message：Blocker/Critical。
- 进度条不够平滑：Major/Minor。

## 本轮不测项

以下项不要作为本轮失败项提交：

- GPU 探针不通。
- 新上传 PDF 的 GPU 解析吞吐或成功率。
- Standard 输出审查。
- Final Review。
- 终审报告导出。

如果测试人员误入 Standard/Final 页面，可记录为“观察项”，但不要作为 Clean-scope UAT 结论。

## 缺陷报告模板

```markdown
### 缺陷标题

- 定级：Blocker/Critical 或 Major/Minor/Enhancement
- 模块：Auth / Settings / Files / PDF审查 / 目录审查 / Raw / Clean
- Material ID：
- 文件名：
- 触发步骤：
- 预期结果：
- 实际结果：
- 网络请求状态码：
- 后端响应 detail：
- 截图或录屏：
- 是否属于本轮排除项：否 / 是，原因：
```

## 当前研发留档

详细证据记录见：

- `docs/uat/2026-07-02-clean-scope-uat-execution.md`
- `docs/uat/2026-07-02-clean-scope-commit-checklist.md`
