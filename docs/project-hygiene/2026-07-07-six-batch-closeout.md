# LuceonWeb2026 Six-Batch Closeout - 2026-07-07

Purpose: turn the mixed post-baseline worktree into reviewable batches while
locking the next product surface to PDF/ElegantBook comparison as the main UI.

## Product Surface Decision

For the next stage, the main UI is:

- Home
- Files / material catalog
- PDF/ElegantBook comparison at `/review/compare`
- Settings

Raw, Clean, Standard, and Final Review pages are retired from the main UI. Their
old frontend routes redirect to `/review/compare`, and old embedded LaTeX /
Overleaf workspace API routes return `410 Gone`. Research scripts and backend
artifact readers for Raw/Clean/Standard may remain for provenance, legacy
support, and background validation, but they are no longer the primary product
workflow.

## Current Closeout Status

| Batch | Status | Current evidence | Commit |
| --- | --- | --- | --- |
| Auth and routing | Committed | `tests/test_auth_api.py`; frontend router/source shows visible review entry is `/review/compare` | `cf7411b` |
| Material metadata catalog | Committed | `tests/test_material_metadata_api.py`; Files UI/API types include metadata filters and drawer | `815e7dd` |
| LaTeX/ElegantBook comparison | Committed | `tests/test_codex_elegantbook_compare.py`; runtime `view=compare` returned LaTeX assets; old workspace API returned `410` | `88cdba1` |
| Legacy self-loop import bridge | Committed | `tests/test_legacy_selfloop_latex_import.py`; bridge docs say import-only, no skill rerun | `4dd75ed` |
| Pipeline and inventory | Committed | `tests/test_material_inventory_pipeline_counts.py`; `tests/test_luceon_pdf_pipeline_scheduler.py`; runtime material summary reports LaTeX availability | `fbd5bdd` |
| UAT and handoff docs | Ready to commit | New LaTeX compare UAT handoff and commit checklist; old Clean-scope docs marked historical | this docs batch |

## Batch 1 - Auth And Routing

Scope:

- Public workspace auth mode and optional legacy auth mode.
- `admin` alias to `admin@luceon.local`.
- Sidebar and router simplification.
- `/login`, `/review/pdf`, `/review/outline`, `/review/standard`,
  `/review/final`, and `/review/preview/:id` route compatibility.

Files:

- `backend/app/api/auth.py`
- `backend/app/services/auth.py`
- `backend/app/utils/user_dep.py`
- `backend/tests/test_auth_api.py`
- `docker-compose.luceon-review.yml`
- `frontend/src/App.vue`
- `frontend/src/api/index.ts`
- `frontend/src/router/index.ts`

Verification:

- `tests/test_auth_api.py`
- frontend build
- browser/source check that the visible nav only points to `/review/compare`

## Batch 2 - Material Metadata Catalog

Scope:

- `material_metadata` database table and model.
- Manual metadata editing, AI extraction, catalog-context reuse, and filters.
- Frontend metadata drawer, batch extraction, and search/filter behavior.

Files:

- `backend/alembic/versions/20260702_add_material_metadata.py`
- `backend/app/models/material_metadata.py`
- `backend/app/models/__init__.py`
- `backend/app/api/materials.py`
- `backend/app/services/material_metadata.py`
- `backend/tests/test_material_metadata_api.py`
- `frontend/src/api/materials.ts`
- `frontend/src/types/material.ts`
- `frontend/src/views/Files.vue`

Verification:

- `tests/test_material_metadata_api.py`
- frontend build
- one manual metadata update through the API or UI

## Batch 3 - LaTeX/ElegantBook Comparison

Scope:

- `latex_done` material stage and manifest references.
- Codex ElegantBook output discovery and priority selection.
- Legacy self-loop fallback when Codex output is absent.
- `/review/compare` as the product comparison surface.
- Artifact proxying for compiled PDFs, ZIPs, compile reports, polish reports,
  render review, final review, and run state.

Files:

- `backend/alembic/versions/20260705_add_latex_material_stage.py`
- `backend/app/models/material.py`
- `backend/app/services/codex_elegantbook.py`
- `backend/app/services/material_inventory.py`
- `backend/app/api/review.py`
- `backend/tests/test_codex_elegantbook_compare.py`
- `frontend/src/api/review.ts`
- `frontend/src/types/file.ts`
- `frontend/src/views/CompareReview.vue`
- `frontend/src/views/Files.vue`
- `frontend/src/views/Home.vue`

Verification:

- `tests/test_codex_elegantbook_compare.py`
- `/api/review/assets?view=compare`
- `/api/review/assets/{asset_id}/latex_compare`
- source PDF and compiled PDF both render in `/review/compare`

## Batch 4 - Legacy Self-Loop Import Bridge

Scope:

- Import already finished four-skill self-loop outputs into LuceonWeb LaTeX
  stage compatibility artifacts.
- Preserve source run evidence and exact material/popo run matching.
- Do not rerun skills from this bridge.

Files:

- `backend/scripts/import_legacy_selfloop_latex.py`
- `backend/tests/test_legacy_selfloop_latex_import.py`

Verification:

- `tests/test_legacy_selfloop_latex_import.py`
- dry-run import report against the intended self-loop run before any apply

## Batch 5 - Pipeline And Inventory

Scope:

- First-stage scheduler count/status handling.
- Material sync across input, MinerU, Popo, LaTeX, and Codex ElegantBook output
  buckets.
- SQLite timeout and backend runtime support changes.
- Docker socket / Docker CLI support only if the next-stage workflow still
  needs a named controlled operation.

Files:

- `backend/Dockerfile`
- `backend/app/database.py`
- `backend/app/services/material_inventory.py`
- `backend/scripts/luceon_pdf_pipeline.py`
- `backend/tests/test_material_inventory_pipeline_counts.py`
- `backend/tests/test_luceon_pdf_pipeline_scheduler.py`

Verification:

- `tests/test_material_inventory_pipeline_counts.py`
- `tests/test_luceon_pdf_pipeline_scheduler.py`
- `/api/materials/summary`
- `/api/materials/sync`

## Batch 6 - UAT And Handoff Docs

Scope:

- Mark 2026-07-02 Clean-scope UAT as historical.
- Add the LaTeX comparison UAT handoff and commit checklist.
- Keep Raw/Clean/Standard exclusions explicit so testers do not reopen retired
  main UI lanes.

Files:

- `docs/project-hygiene/2026-07-07-phase-review.md`
- `docs/project-hygiene/2026-07-07-six-batch-closeout.md`
- `docs/uat/2026-07-02-clean-scope-*.md`
- `docs/uat/2026-07-07-latex-compare-uat-handoff.md`
- `docs/uat/2026-07-07-latex-compare-commit-checklist.md`
- `README.md`
- `README.zh-CN.md`

Verification:

- docs mention `/review/compare` as the only main review UI
- docs preserve the old Clean-scope evidence as historical context only
- `git diff --check`

## Whole-Closeout Verification

Recommended before publication:

```bash
git diff --check
npm run build
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
./graphify update .
```
