# P0 Parsed ZIP User Export Production Revalidation

Task ID: TASK-20260509-154829-P0-Parsed-Zip-User-Export-Production-Revalidation
Created: 2026-05-09T15:48:29+0800
Owner: Lucode
Next Actor: Lucode
Priority: P0

## Context

Director manually downloaded a MinerU parsed artifact ZIP and found the default package still too large. Director clarified the expected default package boundary: the extracted MinerU `ocr/` directory plus root `full.md`. Lucia corrected the code-level default `mode=user` export behavior to match that boundary.

The code-level fix is accepted, but production release readiness remains unclaimed. This task is for scoped production deployment and revalidation only.

## Goal

Deploy the accepted main code containing the parsed ZIP user-export slimming fix to the production deployment path and verify the default UI/API download no longer includes raw diagnostic MinerU content.

## Scope

Allowed:

- Fast-forward production deployment path from `origin/main`.
- Apply the minimum necessary production service restart/rebuild to run the accepted code.
- Run read-only checks against existing parsed artifacts.
- Call `POST /__proxy/upload/parsed-zip` or the equivalent production endpoint in default mode.
- Validate the resulting ZIP structure using local temporary download/output paths outside the repo.

Forbidden:

- Do not delete, overwrite, or mutate DB rows, MinIO objects, Docker volumes, samples, artifacts, secrets, or production override settings.
- Do not create a new upload unless Director separately authorizes it.
- Do not change MinerU, Ollama, model selection, timeout policy, production override, or sample files.
- Do not declare production release readiness.

## Required Validation

Use the Director-observed material if it is available in production:

- material id from manifest: `409615937854928`
- expected default user package boundary: root `full.md` plus all files under the MinerU `ocr/` directory

If that material is unavailable, use an existing completed production material with root `full.md` and a MinerU `ocr/` directory. Record the material/task ID used.

Required checks:

1. `git status --short --branch` in production and development paths.
2. Production deployment HEAD matches accepted `origin/main` after the fix.
3. Default parsed ZIP download excludes:
   - `mineru-result.zip`
   - `artifact-manifest.json`
   - `_middle.json`
   - `_model.json`
   - `_content_list.json`
   - `_content_list_v2.json`
   - `_origin.pdf`
   - non-`ocr/` raw tree content
4. Default parsed ZIP includes:
   - root `full.md`
   - every file under the MinerU `ocr/` directory, preserving its relative path
5. `mode=mineru-raw` still returns the original raw MinerU ZIP if available.
6. `mode=diagnostic` still remains available for full diagnostic export if needed.
7. Run `node server/tests/parsed-zip-export-modes-smoke.mjs`.
8. Run `git diff --check`.

## Required Report

Create a report in `TaskAndReport/` including:

- production HEAD
- material/task ID used for verification
- exact ZIP entry count before/after if available
- proof that forbidden raw diagnostic entries are absent from default user export
- proof that the `ocr/` directory contents are present
- raw/diagnostic mode sanity result
- any residual risk
- explicit statement that production release readiness was not declared
