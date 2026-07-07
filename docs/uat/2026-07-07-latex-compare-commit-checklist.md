# LuceonWeb2026 LaTeX Compare Commit Checklist

日期：2026-07-07

## 提交目标

把当前混合工作区按 6 个批次收口，并把下一阶段产品主入口固定为
`/review/compare` 的 PDF/ElegantBook 比对。

## 推荐批次顺序

### 1. 认证/路由

包含：

- `backend/app/api/auth.py`
- `backend/app/services/auth.py`
- `backend/app/utils/user_dep.py`
- `backend/tests/test_auth_api.py`
- `docker-compose.luceon-review.yml`
- `frontend/src/App.vue`
- `frontend/src/api/index.ts`
- `frontend/src/router/index.ts`

提交前检查：

```bash
docker run --rm --entrypoint python \
  -v /Users/concm/prod_workspace/luceonweb2026/backend:/app \
  -w /app luceonweb2026-review-backend:local \
  -m pytest tests/test_auth_api.py
npm run build
```

### 2. 元数据

包含：

- `backend/alembic/versions/20260702_add_material_metadata.py`
- `backend/app/models/material_metadata.py`
- `backend/app/models/__init__.py`
- `backend/app/api/materials.py`
- `backend/app/services/material_metadata.py`
- `backend/tests/test_material_metadata_api.py`
- `frontend/src/api/materials.ts`
- `frontend/src/types/material.ts`
- `frontend/src/views/Files.vue`

提交前检查：

```bash
docker run --rm --entrypoint python \
  -v /Users/concm/prod_workspace/luceonweb2026/backend:/app \
  -w /app luceonweb2026-review-backend:local \
  -m pytest tests/test_material_metadata_api.py
npm run build
```

### 3. LaTeX 比对

包含：

- `backend/alembic/versions/20260705_add_latex_material_stage.py`
- `backend/app/models/material.py`
- `backend/app/services/codex_elegantbook.py`
- `backend/app/services/material_inventory.py`
- `backend/app/api/review.py`
- `backend/tests/test_codex_elegantbook_compare.py`
- `frontend/src/api/review.ts`
- `frontend/src/types/file.ts`
- `frontend/src/views/CompareReview.vue`
- `frontend/src/views/Home.vue`

提交前检查：

```bash
docker run --rm --entrypoint python \
  -v /Users/concm/prod_workspace/luceonweb2026/backend:/app \
  -w /app luceonweb2026-review-backend:local \
  -m pytest tests/test_codex_elegantbook_compare.py
npm run build
```

### 4. legacy self-loop 导入

包含：

- `backend/scripts/import_legacy_selfloop_latex.py`
- `backend/tests/test_legacy_selfloop_latex_import.py`

提交前检查：

```bash
docker run --rm --entrypoint python \
  -v /Users/concm/prod_workspace/luceonweb2026/backend:/app \
  -w /app luceonweb2026-review-backend:local \
  -m pytest tests/test_legacy_selfloop_latex_import.py
```

### 5. pipeline/inventory

包含：

- `backend/Dockerfile`
- `backend/app/database.py`
- `backend/app/services/material_inventory.py`
- `backend/scripts/luceon_pdf_pipeline.py`
- `backend/scripts/uat_clean_scope_smoke.py`
- `backend/tests/test_material_inventory_pipeline_counts.py`
- `backend/tests/test_luceon_pdf_pipeline_scheduler.py`
- `backend/alembic/versions/20260630_add_weknora_chapter_status_fields.py`
- `frontend/src/components/PdfSourceViewer.vue`
- `frontend/src/views/FilePreview.vue`

提交前检查：

```bash
docker run --rm --entrypoint python \
  -v /Users/concm/prod_workspace/luceonweb2026/backend:/app \
  -w /app luceonweb2026-review-backend:local \
  -m pytest \
  tests/test_material_inventory_pipeline_counts.py \
  tests/test_luceon_pdf_pipeline_scheduler.py
npm run build
```

### 6. UAT 文档

包含：

- `docs/project-hygiene/2026-07-07-phase-review.md`
- `docs/project-hygiene/2026-07-07-six-batch-closeout.md`
- `docs/uat/2026-07-02-clean-scope-uat-execution.md`
- `docs/uat/2026-07-02-clean-scope-tester-handoff.md`
- `docs/uat/2026-07-02-clean-scope-commit-checklist.md`
- `docs/uat/2026-07-07-latex-compare-uat-handoff.md`
- `docs/uat/2026-07-07-latex-compare-commit-checklist.md`
- `README.md`
- `README.zh-CN.md`

提交前检查：

```bash
git diff --check
./graphify update .
```

## 全量收口验证

```bash
git diff --check
docker run --rm --entrypoint python \
  -v /Users/concm/prod_workspace/luceonweb2026/backend:/app \
  -w /app luceonweb2026-review-backend:local \
  -m pytest \
  tests/test_auth_api.py \
  tests/test_material_inventory_pipeline_counts.py \
  tests/test_luceon_pdf_pipeline_scheduler.py \
  tests/test_codex_elegantbook_compare.py \
  tests/test_legacy_selfloop_latex_import.py \
  tests/test_material_metadata_api.py
npm run build
./graphify update .
```

运行态抽查：

```bash
curl -s http://127.0.0.1:28080/ping
curl -s http://127.0.0.1:28080/api/materials/summary
curl -s 'http://127.0.0.1:28080/api/review/assets?page=1&page_size=5&view=compare'
```

## 不提交范围

- `.env.luceon-review`
- `runtime/`
- `frontend/dist/`
- `frontend/node_modules/`
- `graphify-out/`
- Python bytecode and pytest caches

## 口径提醒

- 这轮不是 Clean-scope UAT 的延续；Clean-scope 只作为历史基线。
- 主 UI 只保留 PDF/ElegantBook 比对。
- Raw/Clean/Standard/Final Review 研究代码和历史证据可以保留，但不得作为本轮主产品入口。
