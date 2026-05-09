# P0 Parsed ZIP User Export Slimming - Lucia Review

Time: 2026-05-09T15:48:29+0800

## Trigger

Director manually downloaded:

`/Users/concm/Downloads/parsed-Cambridge IGCSE(0580)  Core and Extended Mathematics_2018(Cambridge  University Press).zip`

and reported that the MinerU parsed artifact package still contained too much.

## Findings

Read-only inspection of the downloaded ZIP confirmed the issue:

- Total entries: 4473
- Root entries: `artifact-manifest.json`, `full.md`, `mineru-result.zip`
- Expanded raw MinerU tree also present under the Cambridge IGCSE folder
- File mix: 4461 `.jpg`, 5 `.json`, 2 `.md`, 1 `.pdf`, 1 `.zip`
- The Director clarified that the intended default user package is the extracted `ocr/` directory plus root `full.md`
- The clarified `ocr/` directory contains 4467 files: 4461 `.jpg`, 4 `.json`, 1 `.pdf`, and 1 `.md`

Conclusion: default `mode=user` for `POST /parsed-zip` was still behaving too close to a diagnostic/raw export. It included the raw ZIP plus the expanded raw tree rather than a user-facing readable package.

## Code-Level Correction

Updated `server/upload-server.mjs` so default `mode=user` now exports the Director-confirmed package boundary:

- include `full.md`
- include all files under the MinerU `ocr/` directory
- resolve `ocr/` contents from `mineru-result.zip` or expanded MinIO objects
- exclude outer `mineru-result.zip`, outer `artifact-manifest.json`, and non-`ocr/` raw tree content from the default user package

Preserved export boundaries:

- `mode=mineru-raw` still streams original `mineru-result.zip`
- `mode=diagnostic` still includes raw ZIP plus full diagnostic content

## Verification

Checks run:

- `node server/tests/parsed-zip-export-modes-smoke.mjs` -> PASS
- `git diff --check` -> PASS
- `npx pnpm@10.4.1 exec tsc --noEmit` -> PASS
- `npx pnpm@10.4.1 run build` -> PASS

On the Director-provided ZIP, the corrected default export boundary should reduce the package from 4473 entries to approximately 4468 entries: root `full.md` plus the 4467 files under the extracted `ocr/` directory.

## Review Decision

`ACCEPTED_CODE_LEVEL_WITH_PRODUCTION_REVALIDATION_REQUIRED`

This is not a production release-readiness declaration. Production deployment and real download revalidation are still required before Task 60 can be decided.
