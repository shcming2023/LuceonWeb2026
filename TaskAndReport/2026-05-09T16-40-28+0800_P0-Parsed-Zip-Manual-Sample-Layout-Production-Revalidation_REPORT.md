# P0 Parsed ZIP Manual Sample Layout Production Revalidation - Lucode Report

Time: 2026-05-09T16:49:03+0800

## Basis

Executed by Lucode based on Lucia task brief:

- `TASK-20260509-164028-P0-Parsed-Zip-Manual-Sample-Layout-Production-Revalidation`
- Task file: `TaskAndReport/2026-05-09T16-40-28+0800_P0-Parsed-Zip-Manual-Sample-Layout-Production-Revalidation_TASK.md`
- Lucia review basis: `TaskAndReport/2026-05-09T16-40-28+0800_P0-Parsed-Zip-Manual-Sample-Layout-Alignment_LUCIA_REVIEW.md`

No production release-readiness declaration is made in this report.

## Branch And HEAD

- Development branch: `lucode/p0-parsed-zip-manual-sample-layout-production-revalidation`
- Development HEAD before report commit: `cd1812af0084c3b19b2a885102af2b7f56a45c86`
- Production path: `/Users/concm/prod_workspace/Luceon2026`
- Production branch: `main`
- Production HEAD after sync: `cd1812af0084c3b19b2a885102af2b7f56a45c86`
- Production commit: `cd1812a Record parsed zip layout task head`
- Production local dirty file preserved: `docker-compose.override.yml`

## Files Changed

- `TaskAndReport/2026-05-09T16-40-28+0800_P0-Parsed-Zip-Manual-Sample-Layout-Production-Revalidation_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

No source-code files were changed by Lucode in this task.

## Deployment Summary

- Production was fast-forwarded from `10d17a581a2d0ee49164ee6f471c7bed30c77c54` to `cd1812af0084c3b19b2a885102af2b7f56a45c86`.
- Rebuilt and restarted only `upload-server` with `docker compose up -d --build upload-server`.
- `cms-upload-server` was healthy after restart.
- `GET /__proxy/upload/health` returned `{"ok":true,"service":"upload-server"}`.

## Director Sample

- Expected sample path: `/Users/concm/Downloads/Cambridge IGCSE(0580)  Core and Extended Mathematics_2018(Cambridge  University Press).zip`
- File size: `97133800` bytes
- Total raw ZIP entries from `unzip -Z1`: `8942`
- Normalization ignored `__MACOSX/**` and `.DS_Store`.
- Normalized file count: `4468`
- Normalized dir count: `2`
- Ignored entries: `4472`
- Normalized top-level folder: `Cambridge IGCSE(0580)  Core and Extended Mathematics_2018(Cambridge  University Press)`
- Normalized extension counts: `.jpg=4461`, `.json=4`, `.md=2`, `.pdf=1`
- Normalized structure has `<material-folder>/full.md`, no root `full.md`, no root `mineru-result.zip`, no root `artifact-manifest.json`, and no intermediate `<material-folder>/ocr/...`.

## Production Download

The exact Cambridge material was not available in production DB/material/task search, and direct probe for material `409615937854928` returned:

```json
{"error":"parsed/409615937854928/ 目录下暂无文件"}
```

Per the task's no-new-upload boundary, no new upload was created. The production layout behavior was validated on existing material:

- Material: `417987242893597`
- Task: `task-1778301456949`
- Title: `教科协和八下数学同步练习册A`
- Download path: `/tmp/luceon-parsed-user-417987242893597-layout.zip`
- Download endpoint: `POST http://localhost:8081/__proxy/upload/parsed-zip`
- Response headers: `X-Luceon-Object-Count: 3`, `X-Parsed-Files-Count: 195`
- Downloaded ZIP size: `4318611` bytes

Normalized production manifest:

- File count: `195`
- Dir count: `2`
- Ignored entries: `0`
- Top-level folders: `["教科协和八下数学同步练习册A"]`
- Root files: `[]`
- Extension counts: `.jpg=188`, `.json=4`, `.md=2`, `.pdf=1`
- Sample paths:
  - `教科协和八下数学同步练习册A/full.md`
  - `教科协和八下数学同步练习册A/images/00ec2fc03072e2c5ac98d16165ae47a9ddfa495a456a050f663025abc4ece6a6.jpg`
  - `教科协和八下数学同步练习册A/教科协和八下数学同步练习册A.md`
  - `教科协和八下数学同步练习册A/教科协和八下数学同步练习册A_content_list.json`
  - `教科协和八下数学同步练习册A/教科协和八下数学同步练习册A_origin.pdf`

Raw/diagnostic sanity:

- `mode=mineru-raw`: `/tmp/luceon-parsed-raw-417987242893597-layout.zip`, size `4238143` bytes; raw ZIP retains intermediate `ocr/` tree.
- `mode=diagnostic`: `/tmp/luceon-parsed-diagnostic-417987242893597-layout.zip`, size `8535421` bytes; diagnostic ZIP retains root `mineru-result.zip`, root `artifact-manifest.json`, and root `full.md`.

## Required Validation Result

| Item | Result | Evidence |
| --- | --- | --- |
| Production code HEAD includes manual-sample layout correction | PASS | production HEAD `cd1812a`; `upload-server` rebuilt after sync |
| Default parsed ZIP downloaded through production endpoint | PASS_WITH_FALLBACK_MATERIAL | default ZIP downloaded for material `417987242893597`; Cambridge material unavailable |
| Normalized manifest for production download produced | PASS | `/tmp/luceon-parsed-user-417987242893597-layout.zip`, summary above |
| Normalized manifest for Director sample produced | PASS | sample ZIP at `/Users/concm/Downloads/...zip`, summary above |
| Exactly one user-facing top-level material folder | PASS | production top-level folders: one |
| `<material-folder>/full.md` exists | PASS | `教科协和八下数学同步练习册A/full.md` |
| OCR contents directly under `<material-folder>/...` | PASS | images and OCR sidecar files are under the top-level folder |
| No `<material-folder>/ocr/...` | PASS | `hasIntermediateOcrSegment=false` |
| No root `full.md` | PASS | root files `[]` |
| No root `mineru-result.zip` | PASS | absent |
| No root `artifact-manifest.json` | PASS | absent |
| No non-OCR legacy expanded files | PASS | no legacy non-OCR sample paths found in normalized production manifest |
| No app-generated `__MACOSX` or `.DS_Store` | PASS | production ignored/mac artifact count `0` |
| `mineru-raw` raw access retained | PASS | raw mode download succeeded and retained `ocr/` tree |
| `diagnostic` debug access retained | PASS | diagnostic mode download succeeded and retained root raw/debug package entries |

## Commands Run

- `git status --short --branch` in development: exit 0
- `git fetch origin`: exit 0
- `git pull --ff-only origin main`: exit 0
- Read task brief, Lucia review, role/team rules, and task tracking list: exit 0
- `node server/tests/parsed-zip-export-modes-smoke.mjs`: exit 0, `Pass ✅`
- `git diff --check`: exit 0
- `git status --short --branch` in production: exit 0
- `git fetch origin && git pull --ff-only origin main`: exit 0
- `docker compose up -d --build upload-server`: exit 0
- `docker compose ps upload-server`: exit 0, `cms-upload-server` healthy
- `curl -fsS http://localhost:8081/__proxy/upload/health`: exit 0
- `ls -l` and `unzip -Z1` on Director sample ZIP: exit 0
- Production DB material/task search for Cambridge/IGCSE/0580/Mathematics: exit 0, no matching records found
- Direct parsed ZIP probe for material `409615937854928`: HTTP 400 with no parsed files
- Default production ZIP download for material `417987242893597`: exit 0
- `mode=mineru-raw` and `mode=diagnostic` downloads for material `417987242893597`: exit 0
- Node normalized manifest comparison script: exit 0

## Skipped Checks

- Exact same-material production comparison against the Cambridge sample was not possible because no Cambridge material/task was found in production and material `409615937854928` has no parsed objects.
- No new upload was created because the task explicitly forbids new validation upload unless Lucia issues a separate task.
- No production release-readiness judgment was made because the task forbids Lucode from declaring production release readiness.

## Risks And Residual Debt

- The production layout behavior is validated on a real existing parsed material, but not on the exact Cambridge material from the Director sample. This leaves a sample-specific revalidation gap unless Lucia authorizes a separate upload or restores the missing Cambridge parsed object.
- The Director sample itself contains Finder-created `__MACOSX` and `.DS_Store` entries; these were ignored during comparison as Lucia instructed.

## Review Required

Lucia review is required. Task 60 release decision remains Director-owned and was not decided by this Lucode execution.
