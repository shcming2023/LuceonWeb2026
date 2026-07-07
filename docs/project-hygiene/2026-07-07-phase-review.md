# LuceonWeb2026 Phase Review - 2026-07-07

Purpose: summarize the current project state, identify code cleanup boundaries,
and prepare the next development stage without blurring runtime evidence, stage
ownership, or product direction.

## Evidence Checked

- Graph entry: `./graphify query "LuceonWeb2026 current architecture review compare workflow material stages backend frontend tests"`.
- Working tree: `git status --short --branch`, `git diff --stat`, and `git diff --check`.
- Runtime stack: `docker compose --env-file .env.luceon-review -f docker-compose.luceon-review.yml ps`.
- Backend: `curl http://127.0.0.1:28080/ping`, `python -m alembic current`, and focused pytest.
- Frontend: `npm run build`, plus `curl -I http://127.0.0.1:28081/`.
- Project notes: 2026-07-02 baseline cleanup and Clean-scope UAT docs.

## Current Runtime Snapshot

- Backend `/ping`: ok.
- Frontend `28081`: HTTP 200.
- Alembic head in running backend: `20260705_add_latex_material_stage`.
- Material summary in the running review stack:
  - total materials: 251
  - availability: PDF 123, MinerU 126, Popo 125, LaTeX 248
  - stage counts: input 2, mineru_done 1, popo_done 0, latex_done 248, failed 0
- Latest recorded pipeline run is an old `popo2raw` failure from 2026-07-02:
  `Raw mechanical QA failed: heading_parent_order:4`.

This means the live review stack is usable, but its visible latest task history
still carries an older Raw/Clean-era failure that should be explained, archived,
or superseded before a clean handoff.

## Phase Verdict

The project has moved beyond the 2026-07-02 Clean-scope baseline. That baseline
validated Auth, Settings, Files, existing MinIO samples, PDF review, outline
review, Popo -> Raw, and Raw -> Clean while explicitly excluding Standard and
Final Review.

The current code is now centered on a narrower next product surface:

1. Material inventory and metadata governance.
2. PDF source viewing plus ElegantBook/LaTeX comparison.
3. Importing legacy four-skill self-loop LaTeX outputs into LuceonWeb.
4. Selecting Codex refined ElegantBook outputs ahead of legacy self-loop outputs.
5. Keeping old Raw/Clean/Standard and embedded Overleaf/LaTeX workspace routes
   behind redirects or `410 Gone` boundaries.

Product decision for the next stage: Raw/Clean/Standard review pages are
intentionally retired from the main UI. The visible review surface is
`/review/compare`, focused on source PDF vs ElegantBook compiled PDF comparison.
Raw/Clean/Standard research code and artifacts may remain as background
evidence, but they are not the primary product workflow.

## Cleanup Boundaries

Recommended commit/review batches:

1. Public workspace auth and route simplification.
   Include `LUCEON_AUTH_DISABLED`, public workspace user behavior, `/login`
   redirect, sidebar simplification, and auth tests.
2. Material metadata catalog layer.
   Include the `material_metadata` migration/model/service/API, frontend drawer,
   filters, batch extraction UI, and metadata tests.
3. LaTeX/ElegantBook comparison contract.
   Include `codex_elegantbook.py`, `latex_done` material fields, compare API,
   `CompareReview.vue`, artifact proxying, and compare tests.
4. Legacy self-loop import bridge.
   Include `import_legacy_selfloop_latex.py`, its tests, and any one-time import
   documentation. Keep clear that it imports finished artifacts and does not
   rerun skills.
5. First-stage scheduler and inventory status changes.
   Include `luceon_pdf_pipeline.py`, material inventory counts, and pipeline
   status tests.
6. UAT and handoff docs.
   Refresh the 2026-07-02 Clean-scope docs or add a new 2026-07-07 LaTeX
   comparison handoff so testers do not apply the old Raw/Clean scope to the
   new product surface.

## Code Organization Priorities

- `frontend/src/views/Files.vue` is now 2388 lines. Split it after behavior is
  frozen, starting with metadata drawer, batch metadata extraction, stage/status
  helpers, and pipeline ticker logic.
- `backend/app/api/review.py` is 1985 lines. Split only along stable API domains:
  asset listing/import, parsed/source-map review, final-review routes, and
  artifact/LaTeX comparison routes.
- `backend/app/services/material_metadata.py` is 963 lines. Split into sampling,
  catalog context, model call, and normalization modules.
- `backend/app/services/material_inventory.py` is 826 lines. Separate MinIO
  discovery/sync from first-stage subprocess orchestration.
- `backend/scripts/import_legacy_selfloop_latex.py` is 878 lines. Keep it as a
  one-time bridge until the import is complete; avoid turning it into the new
  mainline worker.

## Risks To Resolve Before Next Stage

- Auth defaults to public workspace mode. This is convenient for a local review
  station, but production or shared deployments must explicitly set the intended
  auth mode.
- The backend image now installs Docker and the compose file mounts the host
  Docker socket. Keep this only if it has a named product need and a runbook.
- Old review routes redirect to `/review/compare`, while old API routes return
  `410 Gone`. This is clean only if the product decision is documented.
- The running UI may show the 2026-07-02 failed `popo2raw` task as latest
  history even though the current stage is LaTeX comparison.
- The worktree is large and mixed. Do not publish it as one opaque commit unless
  the goal is an explicit full-baseline sync.

## Verification Results

Passed:

- `git diff --check`
- `npm run build`
- Mounted-current-source backend pytest:
  `tests/test_auth_api.py`,
  `tests/test_material_inventory_pipeline_counts.py`,
  `tests/test_codex_elegantbook_compare.py`,
  `tests/test_legacy_selfloop_latex_import.py`,
  `tests/test_material_metadata_api.py`
  -> 30 passed.
- `./graphify update .`

Local note: system `python3` does not have `pytest`, so backend tests were run
with the current `backend/` mounted into `luceonweb2026-review-backend:local`.

## Next Stage Priorities

1. Convert the current large diff into the cleanup batches above, with tests per
   batch.
2. Add a LaTeX comparison UAT handoff that checks material sync, metadata,
   source PDF, compiled PDF, ZIP download, artifact reports, and legacy fallback.
3. Before publication, verify that no visible main navigation or tester handoff
   treats Raw/Clean/Standard/Final Review as the active product surface.
