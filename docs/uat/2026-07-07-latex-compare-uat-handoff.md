# LuceonWeb2026 LaTeX Compare UAT Handoff

日期：2026-07-07

## 本轮边界

本轮验收主线正式切到 PDF/ElegantBook 比对：

- 包含：公共工作区访问、文件/材料目录、教材元数据、材料同步、LaTeX/ElegantBook 可用性、PDF 比对页、源 PDF 渲染、编译 PDF 渲染、ZIP/报告下载、legacy self-loop fallback。
- 不包含：Raw 审查页、Clean 审查页、Standard 审查页、Final Review 页面、内置 LaTeX 编辑器、内置 Overleaf 工作流。
- 兼容行为：旧 `/review/pdf`、`/review/outline`、`/review/standard`、`/review/final`、`/review/preview/:id` 前端路由应进入 `/review/compare`。
- API 边界：旧内置 LaTeX/Overleaf workspace API 返回 `410 Gone`，不应重新启用。

## 环境启动

```bash
docker compose --env-file .env.luceon-review -f docker-compose.luceon-review.yml up -d
```

访问地址：

- 前端：`http://localhost:28081`
- 后端：`http://localhost:28080/api`
- 主审查入口：`http://localhost:28081/review/compare`

基础检查：

```bash
docker compose --env-file .env.luceon-review -f docker-compose.luceon-review.yml ps
curl -s http://127.0.0.1:28080/ping
docker compose --env-file .env.luceon-review -f docker-compose.luceon-review.yml exec -T backend python -m alembic current
curl -s http://127.0.0.1:28080/api/materials/summary
```

预期：

- backend/frontend/redis 均运行。
- `/ping` 返回 `{"msg":"pong"}`。
- Alembic head 至少包含 `20260705_add_latex_material_stage`。
- `materials/summary` 中 `availability.latex_done` 大于 0，才适合执行本轮比对验收。

## 必测用例

### 1. 主 UI 入口

步骤：

1. 打开 `/`。
2. 检查侧边栏和首页按钮。
3. 点击“PDF比对”。
4. 直接访问旧入口 `/review/pdf`、`/review/outline`、`/review/standard`、`/review/final`。

预期：

- 可见主审查入口只有 PDF 比对。
- 旧入口不再展示旧审查页，均进入 `/review/compare`。
- 页面不出现 Raw/Clean/Standard/Final Review 作为主导航项。

### 2. 文件/材料目录

步骤：

1. 打开 `/files`。
2. 同步材料。
3. 使用阶段筛选 `LaTeX`。
4. 搜索一个已有 `material_id`、书名或元数据字段。
5. 对有 LaTeX 的材料点击“PDF比对”。

预期：

- 材料列表展示 PDF、MinerU、Popo、LaTeX 阶段轨迹。
- LaTeX 可用材料显示“可进行 PDF 比对”或等价状态。
- 没有 LaTeX 的材料不能进入比对，需提示尚无 ElegantBook 输出。
- 搜索/筛选可结合元数据字段工作。

### 3. 元数据编辑和 AI 抽取

步骤：

1. 在 `/files` 选择一条材料，打开元数据编辑。
2. 手工保存书名、学科、系列、出版年份等字段。
3. 再选一条材料执行 AI 抽取。
4. 使用学科、国家、系列、年份筛选。

预期：

- 手工保存后状态为人工或混合来源。
- 人工确认字段不会被普通 AI 抽取静默覆盖。
- AI 抽取结果带 evidence/sample 信息。
- 筛选项能反映已存在的元数据值。

### 4. PDF/ElegantBook 比对页

步骤：

1. 打开 `/review/compare`。
2. 选择一个已有 ElegantBook 输出的材料。
3. 检查左侧源 PDF、右侧 ElegantBook 编译 PDF。
4. 下载 ZIP、编译报告、最终审查/渲染审查报告。

预期：

- 左侧源 PDF 可渲染。
- 右侧编译 PDF 可渲染。
- 输出来源标签能区分 `Codex 精修`、`Codex ElegantBook` 或 `legacy baseline`。
- 下载按钮返回文件，不应 404。
- `compile_report` 或 manifest 中能看到编译状态。

### 5. Codex 优先和 legacy fallback

步骤：

1. 找一条同时存在 legacy self-loop 和 Codex ElegantBook 输出的材料。
2. 打开 `/review/compare?asset_id=...`。
3. 再找一条只有 legacy self-loop 输出的材料。

预期：

- 同时存在时优先展示 Codex refined / Codex ElegantBook 输出。
- 只有 legacy 时可回退展示 legacy baseline。
- 页面保留源 PDF 与编译 PDF 的并排比较，不退回文本编辑器或内置 Overleaf。

### 6. 旧 API 边界

可用 curl 或浏览器网络请求验证：

```bash
curl -i http://127.0.0.1:28080/api/review/assets/1/latex_workspace
curl -i http://127.0.0.1:28080/api/review/assets/1/overleaf
```

预期：

- 返回 `410 Gone`。
- 响应说明 LuceonWeb 不再提供内置 LaTeX 工作区或 Overleaf 接入。

## 不作为本轮失败项

- Raw/Clean/Standard 页面没有主导航入口。
- `/review/outline` 不再打开目录审查页。
- `/review/final` 不再打开 Final Review 页面。
- GPU 服务器未开启。
- 新 PDF 从 GPU 解析到 Popo 的吞吐或成功率。

## 缺陷报告模板

```markdown
### 缺陷标题

- 定级：Blocker/Critical 或 Major/Minor/Enhancement
- 模块：公共工作区 / Files / 元数据 / PDF比对 / Artifact 下载 / 旧 API 边界
- Material ID：
- Asset ID：
- 输出来源：Codex refined / Codex ElegantBook / legacy baseline
- 触发步骤：
- 预期结果：
- 实际结果：
- 网络请求状态码：
- 后端响应 detail：
- 截图或录屏：
- 是否属于本轮排除项：否 / 是，原因：
```
