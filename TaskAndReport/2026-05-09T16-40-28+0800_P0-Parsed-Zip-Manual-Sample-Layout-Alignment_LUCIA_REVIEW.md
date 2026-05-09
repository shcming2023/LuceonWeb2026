# Lucia Review: P0 Parsed ZIP Manual Sample Layout Alignment

- Review Time: `2026-05-09T16:40:28+0800`
- Reviewer: Lucia
- Trigger: Director manual test and expected ZIP sample
- Expected Sample: `/Users/concm/Downloads/Cambridge IGCSE(0580)  Core and Extended Mathematics_2018(Cambridge  University Press).zip`
- Prior Accepted Task: `TASK-20260509-154829-P0-Parsed-Zip-User-Export-Production-Revalidation`
- Decision: `ACCEPTED_CODE_LEVEL_PENDING_PRODUCTION_REVALIDATION`

## Director Clarification

Director provided a manually prepared ZIP as the expected output for clicking "下载 MinerU 解析输出物".

Lucia inspected the sample ZIP structure and determined the previous accepted boundary, "root `full.md` plus retained `ocr/` directory", was still not aligned with Director's intended user-facing package.

The corrected expected default user ZIP boundary is:

- one top-level material folder named after the parsed document/material;
- `full.md` inside that top-level folder;
- contents of the MinerU `ocr/` directory lifted directly into the top-level material folder;
- no intermediate `ocr/` path segment in the user-facing ZIP;
- no root `mineru-result.zip`;
- no root `artifact-manifest.json`;
- no non-OCR legacy expanded files;
- no app-generated `__MACOSX` or `.DS_Store` entries.

The manually prepared sample contains Finder-created `__MACOSX` and `.DS_Store` entries. Lucia treats those as local ZIP tooling artifacts, not as application output requirements.

## Code-Level Correction

Lucia updated `server/upload-server.mjs` default `mode=user` ZIP generation:

- derive a user export root from the folder immediately before the `ocr` path segment, falling back to material/task title or material id;
- write `full.md` to `<material-folder>/full.md`;
- remap inner MinerU ZIP `*/ocr/...` files to `<material-folder>/...`;
- remap legacy expanded MinIO `*/ocr/...` objects to `<material-folder>/...`;
- keep `mineru-raw` and `diagnostic` export modes unchanged for raw/debug access.

Lucia updated `server/tests/parsed-zip-export-modes-smoke.mjs` to assert:

- default user ZIP includes `book/full.md`;
- default user ZIP includes `book/book.md`, `book/images/...`, and `book/book_middle.json`;
- default user ZIP excludes root `full.md`, `book/ocr/...`, root raw package files, non-OCR legacy files, and macOS ZIP artifacts.

## Verification

Code-level verification run:

- `node server/tests/parsed-zip-export-modes-smoke.mjs` -> PASS
- `git diff --check`
- `npx pnpm@10.4.1 exec tsc --noEmit`
- `npx pnpm@10.4.1 run build`

Remaining pending item:

- production deployment/download revalidation by Lucode under Task 62

## Boundary

This review does not declare production release readiness. The production release-readiness decision remains Director-owned under Task 60 and is blocked pending Task 62 production revalidation.
