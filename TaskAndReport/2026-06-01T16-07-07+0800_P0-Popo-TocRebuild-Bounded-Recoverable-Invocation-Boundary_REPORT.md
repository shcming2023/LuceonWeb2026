# P0 Popo TocRebuild Bounded/Recoverable Invocation Boundary Report

Reported by: Luceon
Reported at: 2026-06-02T09:35:19+0800
Task ID: TASK-20260601-160707-P0-Popo-TocRebuild-Bounded-Recoverable-Invocation-Boundary
Branch: `codex/task-314-popo-bounded-recoverable`

## Result

Status: `IMPLEMENTED_READY_FOR_PRODUCTION_VALIDATION`

Task 314 has been implemented within the Luceon adapter/integration boundary. MinerU-Popo core, model files, upstream chunking code, MinIO credentials, DB secrets, Docker volumes, and sample PDFs were not modified.

## Changes

- Added Luceon adapter preflight estimation for normalized pages, normalized blocks, per-family chunk counts, aggregate chunk count, and MPS duration risk.
- Fixed progress probing for wrapped normalized labels so `data["pages"]` is counted instead of top-level metadata keys.
- Added bounded interactive mode as the default adapter invocation profile.
- Added bounded normalized-label copy generation under `outputs/label_normalization_bounded/mineru/`, leaving the original normalized label available for evidence.
- Added explicit full/recoverable mode plumbing through request options; full mode preserves the work directory and passes `--resume` to MinerU-Popo `run_inference.py`.
- Added metadata/request visibility for `invocation.mode` so running/failed job records distinguish `bounded` from `full`.
- Updated TaskDetail and AssetDetail manual toc-rebuild calls to send bounded intent explicitly; backend still defaults to bounded if the UI does not send it.
- Added focused Python smoke tests for 891-page wrapped-label estimation, bounded selection, and raw chunk progress parsing.

## Key Evidence

Focused 891-page fixture result:

```text
normalized_pages=891
chunks_by_task={contd: 90, title: 90, image: 90}
inference_chunks_total=270
bounded_selected_pages=24
bounded_selected_chunks={contd: 3, title: 3, image: 3}
bounded_selected_total=9
```

The estimate is intentionally operational, not a byte-for-byte reimplementation of every MinerU-Popo prompt boundary. It is in the observed large-PDF risk range from production evidence (`contd=92`, `title=96`, `image=95`, total about `283`) and prevents the previous false `normalized_pages=4` / `inference_chunks_total=1` report.

## Verification

Commands passed:

```bash
PYTHONPATH=. python3 luceon_service/tests/test_popo_invocation_boundary.py
python3 -m py_compile luceon_service/app.py luceon_service/service.py luceon_service/tests/test_popo_invocation_boundary.py
node --check server/lib/task-actions-routes.mjs
npx tsc --noEmit
npm run build
git diff --check
```

`npm run build` completed successfully with the existing Vite large-chunk warning.

## Boundaries Preserved

- No MinerU-Popo core or model changes.
- No source asset/hash rename.
- No MinIO credential, DB secret, Docker volume, or sample-file mutation.
- No second-large-PDF MinIO AccessKey repair.
- No pressure PASS, release readiness, L3, go-live, or production deployment claim.

## Remaining Production Validation

After merging/deploying this branch, production validation should verify:

- manual Popo rerun on a large Raw Material submits bounded mode by default;
- job metadata exposes `invocation.mode=bounded`;
- progress reports the original normalized page count truthfully;
- explicit full mode records recoverable/background intent and does not masquerade as interactive UAT.
