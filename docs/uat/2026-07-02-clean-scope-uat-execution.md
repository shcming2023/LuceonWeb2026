# LuceonWeb2026 Clean-Scope UAT Execution Record

Date: 2026-07-02
Baseline compose: `docker-compose.luceon-review.yml`
Tester handoff: `docs/uat/2026-07-02-clean-scope-tester-handoff.md`
Commit checklist: `docs/uat/2026-07-02-clean-scope-commit-checklist.md`

> Historical baseline: this record describes the 2026-07-02 Clean-scope pass.
> The active 2026-07-07 product surface has moved to PDF/ElegantBook comparison
> at `/review/compare`. Do not use this document to require Raw/Clean/Standard
> review pages as main UI entries in the current stage.

## Scope

This record covers the current UAT收口 boundary confirmed for this baseline:

- Included: Auth, Settings/MinIO/model-key readiness, Files, existing MinIO PDF/MinerU/Popo assets, Popo -> Raw, Raw -> Clean, PDF parse review, outline rebuild review.
- Excluded by product decision for this run: GPU-server-side testing, new GPU parsing load, Clean -> Standard, Standard output review, Final Review, report export.
- GPU note: MinIO already contains 100+ GPU-produced MinerU/Popo samples. Validation in this run uses those durable MinIO artifacts instead of probing or loading the GPU server.

## Environment Evidence

- Local services: frontend/backend/redis were running under `docker-compose.luceon-review.yml`.
- Backend Alembic head: `20260630_add_weknora_chapter_status_fields`.
- Frontend build: `npm run build` passed.
- Backend Clean-scope regression excluding Standard/Final Review: `102 passed, 6 warnings`.
- Focused recheck after the GPU-excluded refresh: `tests/test_material_inventory_pipeline_counts.py` passed in the rebuilt backend image (`10 passed, 1 warning`); `npm run build` passed.
- Graph refresh: `graphify update .` completed.
- Refresh after GPU shutdown: a fresh UAT user was registered, MinIO/model checks were run, and existing MinIO samples were verified without calling `/runtime/gpu/check` or starting new GPU parsing.
- Running container/code alignment: backend container contains `assign_input_review_asset` and `pipeline_result_counts`; frontend served bundle contains `无溯源数据`.
- Repeatable Clean-scope API smoke entrypoint: `python backend/scripts/uat_clean_scope_smoke.py`.
- Automated smoke result: `status=pass`; `gpu_checked=false`; `standard_checked=false`; `final_review_checked=false`; default smoke user reuse was verified with `auth.mode=reused`. Latest light smoke used `--skip-model-check --samples 1` after backend rebuild.
- Final revision regression after tester feedback:
  - Backend Clean-scope whitelist: `102 passed, 6 warnings`.
- Frontend production build: `npm run build` passed.
- Frontend review container was rebuilt/recreated; `http://localhost:28081/` returned `200`.
- Served frontend bundle contains `无溯源数据` and `/cms/tasks` route compatibility.
- Clean-scope smoke passed against existing MinIO samples with `gpu_checked=false`, `standard_checked=false`, `final_review_checked=false`.
- `python -m py_compile backend/scripts/uat_clean_scope_smoke.py` and `git diff --check` passed.
- Follow-up browser UAT from the in-app browser verified `/login?redirect=/cms/tasks` no longer leaves the user on a blank deprecated route; `/cms/tasks` redirects to `/files`.
- Follow-up browser UAT executed `AMC8_2026_Solutions.pdf` (`material_id=pdf-037fdccc525f7536`, `asset_id=1844`) through Popo -> Raw -> Clean:
  - Before run: `popo_done`, no Raw/Clean manifests.
  - Popo -> Raw preflight dialog showed Material ID, Popo Run, MinerU Run, target `eduassets-raw` path, and Clean-stale semantics.
  - Popo -> Raw run `60` succeeded (`1/1`), and the Files page showed `Clean 失效`, Raw count `25`, `重建Raw`, and `生成Clean`.
  - Raw -> Clean preflight dialog showed Raw Run, source `eduassets-raw`, target `eduassets-clean`, and strict Raw-outline inheritance copy.
  - Raw -> Clean run `61` succeeded (`1/1`), and the Files page showed `Clean`, Clean count `7`, `重建Raw`, and `重建Clean`.
  - `/review/outline?asset_id=1844` opened with Raw and Clean panels visible, one directory unit, PDF page links, and rendered images.

## Verification Commands

Clean-scope backend regression command, excluding Standard and Final Review:

```bash
docker compose --env-file .env.luceon-review -f docker-compose.luceon-review.yml exec -T backend python -m pytest \
  tests/test_auth_api.py \
  tests/test_health_api.py \
  tests/test_runtime_settings_env.py \
  tests/test_settings_api.py \
  tests/test_minio_client.py \
  tests/test_file_parser_worker.py \
  tests/test_file_preview_api.py \
  tests/test_file_delete_api.py \
  tests/test_export_api.py \
  tests/test_mineru_api_client.py \
  tests/test_mineru_api_pages_patch.py \
  tests/test_parse_progress_api.py \
  tests/test_parser_service_sidecar.py \
  tests/test_popo_client.py \
  tests/test_popo_to_raw_qa.py \
  tests/test_artifact_sync.py \
  tests/test_stats_api.py \
  tests/test_backend_types.py \
  tests/test_material_inventory_pipeline_counts.py
```

Focused and smoke commands:

```bash
docker compose --env-file .env.luceon-review -f docker-compose.luceon-review.yml exec -T backend python -m pytest tests/test_material_inventory_pipeline_counts.py
python backend/scripts/uat_clean_scope_smoke.py --skip-model-check --samples 1
python -m py_compile backend/scripts/uat_clean_scope_smoke.py
npm run build
docker compose --env-file .env.luceon-review -f docker-compose.luceon-review.yml build frontend
docker compose --env-file .env.luceon-review -f docker-compose.luceon-review.yml up -d frontend
git diff --check
graphify update .
```

## MinIO Sample Pool

After `/api/materials/sync?limit=1000` for the latest UAT user:

- Total materials: 122
- MinerU/Popo availability: 119
- Raw availability: 25 after the AMC8 Popo -> Raw run.
- Clean availability: 7 after the AMC8 Raw -> Clean run.
- Standard availability: 3, but Standard is excluded from this run.

Latest runtime readiness checks within Clean-scope:

- MinIO contract: `contract_ok=true`; required buckets exist: `eduassets-input`, `eduassets-mineru`, `eduassets-minerupopo`, `eduassets-raw`, `eduassets-clean`, `eduassets-parsed`.
- Model connectivity: `ok=true`; LLM and Vision checks returned HTTP `200`.
- GPU connectivity: intentionally not probed in this refresh because the GPU server was shut down and GPU-side testing is excluded.

## Black-Box Checks Completed

### Auth

- Registered a fresh UAT user.
- Verified correct login.
- Verified wrong password returns `401` with `邮箱或密码错误`.

### Files And Stage Guarding

- Uploaded PDF successfully and confirmed list visibility.
- Verified input-only material does not expose Raw/Clean actions in its row.
- Verified backend guardrails:
  - Popo -> Raw without material_id/Popo/MinerU returns `409` with blockers `missing_material_id`, `missing_popo_asset`, `missing_mineru_asset`.
  - Raw -> Clean without material_id/Raw returns `409` with blockers `missing_material_id`, `missing_raw_asset`.
- Verified existing Clean materials expose Raw/Clean rebuild actions.
- Verified `/cms/tasks` legacy task route redirects to `/files` instead of rendering an empty main panel.

### Preflight Dialogs

Opened dialogs without confirming execution:

- Raw rebuild dialog includes Material ID, Popo Run, MinerU Run, target `eduassets-raw` path, and overwrite/Clean-stale semantics.
- Clean rebuild dialog includes Material ID, Raw Run, source `eduassets-raw` path, target `eduassets-clean` path, and Raw-outline inheritance semantics.
- AMC8 first-generation Raw/Clean dialogs showed the same action/overwrite/downstream semantics before execution.

Screenshots:

- `/tmp/luceon-uat-raw-confirm.png`
- `/tmp/luceon-uat-clean-confirm.png`

### Existing MinIO Asset Review

Sampled existing MinIO-backed materials:

- `Grammar Friends 6 (Students Book) (Flannigan E.) (Z-Library).pdf` (`asset_id=1963`, `material_id=pdf-ff4c7f59964ad54f`)
- `Reading Explorer 1 Students Book.pdf` (`asset_id=1955`, `material_id=pdf-e71fe159994b50f3`)
- `中学生世界 八上 数学 上册.pdf` (`asset_id=1926`, `material_id=pdf-aadfa33fb0485c1a`)

For all sampled materials:

- Source PDF range request returned `206`.
- Source PDF first-page image returned `200`.
- MinerU parsed variants returned `200`.
- Page Markdown variants returned `200`.
- Popo parsed variants returned `200`.
- `source_map` returned `200`.
- Outline review returned `200`.
- Raw and Clean were available.

Observed outline unit counts:

- Grammar Friends 6: 40 directory units, 98 source-map pages.
- Reading Explorer 1: 69 directory units, 160 source-map pages.
- 中学生世界 八上 数学 上册: 39 directory units, 84 source-map pages.

### AMC8 Popo -> Raw -> Clean Browser Closure

Executed allowlist sample:

- `AMC8_2026_Solutions.pdf`
- `material_id=pdf-037fdccc525f7536`
- `material_pk=671`
- `review_asset_id=1844`

Results:

- Files page before Raw: stage `Popo`; `生成Raw` enabled; `目录审查` disabled; `PDF审查` opened `/review/pdf?asset_id=1844`.
- PDF review: source PDF rendered, MinerU/Popo content loaded, source map showed `147 个溯源框`, and inline images loaded.
- Popo -> Raw run `60`: UI ticker showed running stage and latest event; DB ended `succeeded`, `processed=1`, `success=1`; material became `clean_stale` with Raw manifest.
- Files page after Raw: Raw count `25`, stage `Clean 失效`, `目录审查` enabled, `生成Clean` enabled.
- Raw -> Clean run `61`: UI ticker showed running stage and latest event; DB ended `succeeded`, `processed=1`, `success=1`; material became `clean_done` with Clean manifest.
- Files page after Clean: Clean count `7`, stage `Clean`, `重建Clean` enabled.
- Outline review: `/review/outline?asset_id=1844` opened with Raw and Clean tags, one directory unit, Raw/Clean content, PDF page links, and 31 images in the rendered page DOM.

### Source Map Fallback

Forced `/source_map` to return `{ "pages": [] }` in the browser while keeping the PDF/review asset otherwise valid.

Result:

- PDF still loaded.
- UI displayed `无溯源数据` instead of a blank or cryptic bbox message.

Screenshot:

- `/tmp/luceon-uat-empty-source-map-forced.png`

## UAT Case Matrix

| Area | Case | Status | Evidence | Defect Grade |
| --- | --- | --- | --- | --- |
| Auth | Register/login/wrong-password rejection | Pass | Fresh UAT user created; correct login passed; wrong password returned `401` and `邮箱或密码错误`. | None |
| Settings | Runtime readiness | Pass within Clean-scope | MinIO contract returned `contract_ok=true`; LLM/Vision model checks returned HTTP `200`; frontend/backend/redis verified. GPU probing is excluded after server shutdown because MinIO artifacts are the source for this pass. | None |
| Files | PDF upload/list visibility | Pass | Uploaded UAT PDFs; input-only material visible in Files list. Duplicate-upload behavior fixed so downstream review assets are not polluted. | Fixed Blocker/Critical risk |
| Files | Parse preflight / GPU parsing | Excluded for this pass | Existing MinerU/Popo artifacts in MinIO are used instead of starting GPU work. | Not assessed |
| Files | Stage operation guarding | Pass | Input-only material row does not expose Raw/Clean actions; backend start endpoints return `409` preflight blockers instead of hard errors. | None |
| Files | Single Raw/Clean preflight dialogs | Pass | Raw/Clean rebuild dialogs opened without confirming execution; required IDs and paths visible. | None |
| Files | Legacy task redirect | Pass after fix | `/cms/tasks` now redirects to `/files`; before fix the login redirect rendered sidebar plus blank main content. | Fixed Major |
| Files | Popo -> Raw -> Clean single material closure | Pass | AMC8 progressed Popo -> Clean through runs `60` and `61`; Files counts, row stage, manifests, ticker, and outline review agreed. | None |
| Files | Batch Clean queue and stop-after-current | Implementation verified, not run as destructive batch | Frontend has serial queue and `停止后续` sets a stop flag before the next row. Current running task is not interrupted. | Non-blocking note |
| Review | PDF parse review | Pass | Existing MinIO samples returned PDF `206`, first-page image `200`, source_map `200`, and MinerU/Page/Popo parsed variants `200`. | None |
| Review | Outline rebuild review | Pass | Existing MinIO samples returned outline review `200`; directory unit counts: 40, 69, 39; Raw and Clean markdown were available. | None |
| Review | Empty source_map fallback | Pass after fix | Forced `{ "pages": [] }`; UI displayed `无溯源数据` and PDF still loaded. | Fixed Enhancement |
| Standard | Standard output review | Excluded | Product decision: Standard is not developed enough for this pass. | Not assessed |
| Final Review | Final Review and export | Excluded | Depends on Standard; not part of Clean-scope UAT. | Not assessed |

## Defect Register

| ID | Finding | Grade | Status | Evidence / Fix |
| --- | --- | --- | --- | --- |
| UAT-001 | Current DB was stamped with `20260630_add_weknora_chapter_status_fields`, but the repository did not know that Alembic revision. | Blocker/Critical | Fixed | Added no-op compatibility revision; `alembic current` reports the revision as head. |
| UAT-002 | Successful first-stage pipeline runs could show `processed/success` as `0`, making the task ticker misleading. | Major | Fixed | Pipeline subprocess now derives counts from staged JSON result; covered by regression tests. |
| UAT-003 | Re-uploading a PDF whose material already had downstream assets could overwrite `review_asset_id` with an input-only asset, causing Popo variants to return `404`. | Blocker/Critical risk | Fixed | Input upload/sync preserves downstream review assets and relinks to existing resolved review assets. DB invariant check found `0` downstream materials pointing at input-only review assets out of `712` downstream rows. |
| UAT-004 | Empty `source_map` displayed bbox-oriented copy instead of a user-facing fallback. | Enhancement | Fixed | UI now displays `无溯源数据` / `无溯源`; verified with forced empty source map. |
| UAT-005 | Login redirect or external links targeting legacy `/cms/tasks` could land on a blank main area with only the sidebar visible. | Major | Fixed | Added frontend route redirect `/cms/tasks` -> `/files`; rebuilt frontend container and verified in browser. |

## Fixes Landed During UAT

### Alembic Compatibility

Added a compatibility no-op migration:

- `backend/alembic/versions/20260630_add_weknora_chapter_status_fields.py`

Purpose:

- Allows local review DBs already stamped with the shared WeKnora lab revision to validate `alembic current/upgrade head` without mutating LuceonWeb review schema.

### Pipeline Progress Counts

Updated `backend/app/services/material_inventory.py` so first-stage pipeline subprocess completion parses the staged JSON result and fills:

- `PipelineRun.total`
- `PipelineRun.processed`
- `PipelineRun.success`
- `PipelineRun.failed`

This prevents successful first-stage runs from showing `0/1` or `0 success` in the task ticker.

### Duplicate Upload Review-Asset Preservation

Updated input upload/sync behavior so repeated upload of a PDF whose material already has downstream MinerU/Popo/Raw/Clean assets does not overwrite the material's downstream `review_asset_id` with an input-only review asset.

This prevents Popo parsed variants from becoming `404` after duplicate uploads.

### Friendly Empty Source-Map Copy

Updated frontend copy from bbox-specific labels to user-facing fallback:

- `无溯源数据`
- `无溯源`

### Legacy Task Route Compatibility

Added a frontend router redirect:

- `/cms/tasks` -> `/files`

Purpose:

- Existing login redirects or saved links no longer land on a deprecated blank route; users return to the Files workbench where task status and material location are visible.

## Current Non-Blocking Notes

- Standard entry points may still be visible for rows that already have Standard artifacts, but Standard/Final Review are intentionally outside this UAT pass.
- Batch queue stop-after-current is implemented as frontend local queue control. It stops before starting the next queued row; it does not interrupt the currently running Raw/Clean task.
- Raw -> Clean can spend around a minute in the `clean` stage with no finer-grained UI event until the cleaner returns; this did not block the AMC8 flow, but progress copy could be improved later.

## Current Verdict

Clean-scope UAT is passable for independent testing with the exclusions above.

No Clean-scope Blocker/Critical issue remains in the verified surfaces.
