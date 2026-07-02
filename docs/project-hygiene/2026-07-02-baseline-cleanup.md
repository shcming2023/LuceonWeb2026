# LuceonWeb2026 Baseline Cleanup - 2026-07-02

Purpose: prepare the repository for the next development stage without losing
runtime lineage, review evidence, or the currently usable review stack.

## Cleanup Policy

This cleanup intentionally separates four classes of files:

- Core source: backend, frontend, migrations, tests, compose files, and product docs.
- Active runtime state: `runtime/backend/mineru.db`, `runtime/backend/runtime_config.json`,
  and live pipeline evidence needed by the review UI.
- Research and audit assets: `docs/standard-research/`, `docs/clean-standard/`,
  `docs/standard-acceptance-gates.md`, and Standard/Final Review scripts.
- Disposable local artifacts: caches, generated frontend output, scratch folders,
  Python bytecode, local dependency installs, and one-off debug workdirs.

The cleanup favors preserving evidence over reclaiming every gigabyte. Large
pipeline workdirs are retained unless they are clearly debug-only.

## Actions Performed

Deleted disposable generated artifacts:

- `.DS_Store` files across the workspace.
- Python `__pycache__/`, `*.pyc`, and `backend/.pytest_cache`.
- `frontend/dist/`.
- `frontend/node_modules/`.
- root scratch folder `tmp/`.
- `backend/mineru.db`, an ignored local SQLite file outside the active runtime mount.
- `runtime/backend/pdf-page-cache/`.
- one-off runtime scratch directories:
  - `runtime/backend/tmp-aadfa-level-check/`
  - `runtime/backend/tmp-aadfa-raw-check/`
  - `runtime/backend/tmp-aadfa-tree-check/`
  - `runtime/backend/tmp-clean-gate-check/`
  - `runtime/backend/tmp-clean-gate-check-2/`
  - `runtime/backend/tmp-clean-gate-container/`
  - `runtime/backend/tmp-gf6-bootstrap-fix/`
  - `runtime/backend/tmp-gf6-bootstrap-fix2/`
  - `runtime/backend/tmp-rex-sb2-check/`

Archived historical runtime artifacts under `runtime/archive/20260702-baseline/`:

- DB backups:
  - `runtime/archive/20260702-baseline/db-backups/mineru.db.backup-before-admin-password-reset-20260701162401`
  - `runtime/archive/20260702-baseline/db-backups/mineru.db.corrupt-backup-20260620194029`
- Debug-only workdirs:
  - `runtime/archive/20260702-baseline/debug-workdirs/debug-grammar-llm-check/`
  - `runtime/archive/20260702-baseline/debug-workdirs/debug-popo2raw-grammar/`

Updated ignore rules:

- Added `tmp/` so root scratch output does not reappear in `git status`.
- Added `graphify` because the checkout-local helper is generated beside the
  already ignored `graphify-out/` index.

## Preserved Deliberately

Preserved active runtime state:

- `runtime/backend/mineru.db`
- `runtime/backend/runtime_config.json`

Preserved source-fidelity and review evidence:

- `runtime/backend/pipeline-work/audits/` because current Standard research
  documents cite audit outputs from this tree.
- `runtime/backend/pipeline-work/clean2standard/`
- `runtime/backend/pipeline-work/raw2clean/`
- `runtime/backend/pipeline-work/popo2raw/`

The retained `popo2raw/` tree is still large, around 27G. It contains historical
pipeline run materializations and should only be cold-archived after confirming
that old run detail pages and artifact downloads no longer need local workdirs.

Preserved active development changes:

- Standard Basic Print scripts and docs.
- Final Review backend/frontend changes.
- Material inventory/runtime settings changes.
- Graphify output under `graphify-out/` remains ignored but available locally.

## Current Baseline Shape

After cleanup, the intended top-level categories are:

- `backend/`: FastAPI app, models, migrations, service code, tests, and pipeline scripts.
- `frontend/`: Vue app source and build config; dependency and build outputs are regenerated.
- `docs/`: deployment docs, Standard/Clean contracts, research trail, and hygiene notes.
- `runtime/backend/`: active ignored runtime mount for the local review stack.
- `runtime/archive/`: ignored local archive for baseline cleanup artifacts.
- `graphify-out/`: ignored local graph index.

## Verification Checklist

Required post-cleanup checks:

- `docker compose --env-file .env.luceon-review -p luceonweb2026-review -f docker-compose.luceon-review.yml ps`
- `curl http://127.0.0.1:28080/ping`
- `curl http://127.0.0.1:28080/api/system/mineru-health`
- confirm no cache files remain with `find . -name '.DS_Store' -o -name '__pycache__' -o -name '.pytest_cache' -o -name '*.pyc'`
- run `./graphify update .` after code/doc changes.

## Next Cleanup Candidates

These were not moved in this pass because they can affect traceability:

- Cold-archive old `runtime/backend/pipeline-work/popo2raw/run-*` directories
  only after a run-id to artifact-path audit.
- Split `backend/scripts/` into subfolders only after checking script imports,
  docs references, and service entry points such as `standard_from_clean.py`.
- Consider replacing some large runtime workdirs with MinIO-backed manifests
  once the review UI no longer depends on local materialized outputs.
