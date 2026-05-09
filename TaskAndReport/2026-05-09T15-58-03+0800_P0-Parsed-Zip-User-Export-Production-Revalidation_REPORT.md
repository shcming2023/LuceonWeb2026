# P0 Parsed ZIP User Export Production Revalidation - Lucode Report

Time: 2026-05-09T15:58:03+0800

## Basis

This work was executed by Lucode based on Lucia task brief:

- `TASK-20260509-154829-P0-Parsed-Zip-User-Export-Production-Revalidation`
- Task file: `TaskAndReport/2026-05-09T15-48-29+0800_P0-Parsed-Zip-User-Export-Production-Revalidation_TASK.md`
- Lucia review basis: `TaskAndReport/2026-05-09T15-48-29+0800_P0-Parsed-Zip-User-Export-Slimming_LUCIA_REVIEW.md`

No production release-readiness declaration is made in this report.

## Branch And HEAD

- Development branch: `lucode/p0-parsed-zip-user-export-production-revalidation`
- Development HEAD before report commit: `86a0d0e3c6b902557a707f78bf164567bd9b0d63`
- Final report commit on `main`: `56c5aa1f6aa596031eaae5f010804323614dd02e`
- Production path: `/Users/concm/prod_workspace/Luceon2026`
- Production code HEAD used for deploy/rebuild: `86a0d0e3c6b902557a707f78bf164567bd9b0d63`
- Production final Git HEAD after report-only sync: `56c5aa1f6aa596031eaae5f010804323614dd02e`
- Production deployed code commit: `86a0d0e fix: slim parsed zip user export`
- Production local dirty file preserved: `docker-compose.override.yml`

## Files Changed

- `TaskAndReport/2026-05-09T15-58-03+0800_P0-Parsed-Zip-User-Export-Production-Revalidation_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

No source-code files were changed by this task. The accepted code-level fix was already on `origin/main` at `86a0d0e`.

## Deployment Summary

- Fast-forwarded production from `fc74d664a96b72bbea30a41b050b5f0109e4ad92` to `86a0d0e3c6b902557a707f78bf164567bd9b0d63`, then after the report-only commit was pushed, fast-forwarded production Git state to `56c5aa1f6aa596031eaae5f010804323614dd02e`.
- Rebuilt and restarted only `upload-server` with `docker compose up -d --build upload-server`.
- No second rebuild was needed after the report-only sync because no runtime source changed after `86a0d0e`.
- `cms-upload-server` was healthy after restart.
- Production dependency health with `mineruSubmitProbe=true` returned `blocking=false`; MinIO, MinerU submit probe, and Ollama were OK.

## Verification Material

The Director-observed material requested by the task was unavailable in current production parsed storage:

- Requested material: `409615937854928`
- `POST /__proxy/upload/parsed-zip` response: HTTP 400, `parsed/409615937854928/ 目录下暂无文件`

Fallback material used per task brief:

- Material: `417987242893597`
- Title: `教科协和八下数学同步练习册A`
- Task: `task-1778301456949`
- Task state/stage: `review-pending` / `review`
- Parsed prefix: `parsed/417987242893597/`
- Parsed files count metadata: `196`
- MinerU task id: `a37963a6-b057-4a06-aaee-4ad54b15d89a`

## ZIP Evidence

Temporary validation files were written under `/tmp` only.

Default `mode=user`:

- Download: `/tmp/luceon-parsed-user-417987242893597.zip`
- Size: `4321809` bytes
- Response headers: `X-Luceon-Object-Count: 3`, `X-Parsed-Files-Count: 195`
- ZIP file entries: `195` files plus `3` directory entries
- Root entries: `full.md` only
- OCR files included: `194`
- Non-root, non-`ocr/` files: `0`
- Root raw/diagnostic entries absent: `mineru-result.zip`, `artifact-manifest.json`
- OCR completeness check against `mode=mineru-raw`: raw OCR files `194`, user OCR files `194`, missing from user `0`, extra in user `0`

Raw `mode=mineru-raw` sanity:

- Download: `/tmp/luceon-parsed-raw-417987242893597.zip`
- Size: `4238143` bytes
- Response header: `Content-Disposition: attachment; filename="mineru-raw-417987242893597.zip"`
- Raw ZIP file entries: `194`
- Raw ZIP contains the original MinerU `ocr/` tree.

Diagnostic `mode=diagnostic` sanity:

- Download: `/tmp/luceon-parsed-diagnostic-417987242893597.zip`
- Size: `8535421` bytes
- Response headers: `X-Luceon-Object-Count: 3`, `X-Parsed-Files-Count: 197`
- ZIP file entries: `197` files plus `3` directory entries
- Root entries include `mineru-result.zip`, `artifact-manifest.json`, and `full.md`

Comparator count:

- Diagnostic/full package: `197` file entries
- Default user package after fix: `195` file entries
- Default package removed root raw/diagnostic package entries and preserved root `full.md` plus all OCR files.

## Important Boundary Note

The default user package matches the Director-confirmed package boundary recorded by Lucia: root `full.md` plus the complete extracted MinerU `ocr/` directory.

The fallback material's `ocr/` directory itself contains five MinerU-generated files whose names end with `_middle.json`, `_model.json`, `_content_list.json`, `_content_list_v2.json`, and `_origin.pdf`. They are present only inside `ocr/`, and there are no non-`ocr/` raw-tree files in the default package. This is consistent with "include every file under the MinerU `ocr/` directory", but Lucia should review the wording tension with the task checklist item that literally says those suffixes should be excluded.

## Commands Run

- `git status --short --branch` in development: exit 0
- `git fetch origin` in development: exit 0
- `git pull --ff-only origin main` in development: exit 0
- Read task brief, Lucia review, team contract, Lucode role, test policy, project state, handoff, and PRD references: exit 0
- `node server/tests/parsed-zip-export-modes-smoke.mjs`: exit 0, `Pass ✅`
- `git diff --check` in development: exit 0
- `git status --short --branch` in production: exit 0
- `git fetch origin && git pull --ff-only origin main` in production: exit 0
- `docker compose ps upload-server cms-frontend db-server minio`: exit 0
- `docker compose up -d --build upload-server`: exit 0
- `docker compose ps upload-server`: exit 0, `cms-upload-server` healthy
- `curl http://localhost:8081/__proxy/upload/health`: exit 0
- `curl http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true`: exit 0, `blocking=false`
- Requested material `409615937854928` default parsed ZIP probe: HTTP 400, no parsed files available
- Fallback material `417987242893597` default parsed ZIP download and entry inspection: exit 0
- Fallback material `417987242893597` `mode=mineru-raw` download and entry inspection: exit 0
- Fallback material `417987242893597` `mode=diagnostic` download and entry inspection: exit 0
- Node ZIP classification/comparison script over `/tmp` downloads: exit 0

## Skipped Checks

- No new upload was created because the task explicitly forbids new uploads unless separately authorized.
- The requested material `409615937854928` could not be used because production returned `parsed/409615937854928/ 目录下暂无文件`; fallback validation used existing material `417987242893597`.
- No production release-readiness judgment was made because the task forbids Lucode from declaring production release readiness.

## Risks And Residual Debt

- Lucia should decide whether the checklist phrase excluding `_middle.json`, `_model.json`, `_content_list.json`, `_content_list_v2.json`, and `_origin.pdf` should apply even inside `ocr/`, because that would conflict with the accepted boundary "include every file under the MinerU `ocr/` directory".
- Production remains with local `docker-compose.override.yml` dirty by design; it was preserved and not edited.

## Review Required

Lucia review is required. Task 60 release decision remains Director-owned and was not decided by this Lucode execution.
