# LuceonWeb2026 Clean-Scope UAT 提交清单

日期：2026-07-02

> 历史基线说明：本文只适用于 2026-07-02 Clean-scope 收口。当前
> 2026-07-07 阶段的提交与验收请使用
> `docs/uat/2026-07-07-latex-compare-commit-checklist.md`。

## 提交范围

本次 Clean-scope UAT 收口提交应包含：

- `backend/app/services/material_inventory.py`
- `backend/alembic/versions/20260630_add_weknora_chapter_status_fields.py`
- `backend/scripts/uat_clean_scope_smoke.py`
- `backend/tests/test_material_inventory_pipeline_counts.py`
- `frontend/src/components/PdfSourceViewer.vue`
- `frontend/src/router/index.ts`
- `frontend/src/views/FilePreview.vue`
- `docs/uat/2026-07-02-clean-scope-uat-execution.md`
- `docs/uat/2026-07-02-clean-scope-tester-handoff.md`
- `docs/uat/2026-07-02-clean-scope-commit-checklist.md`

## 不提交范围

不要提交以下本地/运行产物：

- `.env.luceon-review`
- `runtime/`
- `frontend/dist/`
- `frontend/node_modules/`
- `graphify-out/`
- `backend/**/__pycache__/`
- `backend/**/*.pyc`
- `backend/.pytest_cache/`

## 推荐验证

提交前建议执行：

```bash
docker compose --env-file .env.luceon-review -f docker-compose.luceon-review.yml ps
docker compose --env-file .env.luceon-review -f docker-compose.luceon-review.yml exec -T backend python -m alembic current
docker compose --env-file .env.luceon-review -f docker-compose.luceon-review.yml exec -T backend python -m pytest tests/test_material_inventory_pipeline_counts.py
python backend/scripts/uat_clean_scope_smoke.py --skip-model-check --samples 1
python -m py_compile backend/scripts/uat_clean_scope_smoke.py
npm run build
docker compose --env-file .env.luceon-review -f docker-compose.luceon-review.yml build frontend
docker compose --env-file .env.luceon-review -f docker-compose.luceon-review.yml up -d frontend
curl -I -s http://localhost:28081/ | head
git diff --check
graphify update .
```

Clean-scope 全量后端回归命令见 `docs/uat/2026-07-02-clean-scope-uat-execution.md` 的 `Verification Commands` 段；当前证据为 `102 passed, 6 warnings`。

本轮追加浏览器证据：

- `/cms/tasks` 旧入口已重定向到 `/files`，避免登录 redirect 后空白主区域。
- `AMC8_2026_Solutions.pdf` 已执行 Popo -> Raw -> Clean，当前 UAT 用户下 Raw availability 为 `25`、Clean availability 为 `7`。

## 范围提醒

本提交不声明完成 GPU 服务器侧测试、Clean -> Standard、Standard 输出审查、Final Review 或终审报告导出。这些项仍按本轮产品边界排除。
