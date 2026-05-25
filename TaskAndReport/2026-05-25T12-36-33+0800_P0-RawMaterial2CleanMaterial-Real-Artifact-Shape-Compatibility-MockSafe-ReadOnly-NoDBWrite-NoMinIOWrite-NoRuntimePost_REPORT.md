# TASK-20260525-123633 Lucode Report

## Task

- Task: `TASK-20260525-123633-P0-RawMaterial2CleanMaterial-Real-Artifact-Shape-Compatibility-MockSafe-ReadOnly-NoDBWrite-NoMinIOWrite-NoRuntimePost`
- Branch: `lucode/TASK-20260525-123633-P0-RawMaterial2CleanMaterial-Real-Artifact-Shape-Compatibility-MockSafe-ReadOnly-NoDBWrite-NoMinIOWrite-NoRuntimePost`
- Branch base: `dcc23eccaa7b69d1b3304a0fc3f68e9aa3bd1b92`
- Final pushed branch HEAD: see pushed branch tip and Lucode final response.
- Status: Lucode implemented the real-artifact shape compatibility bridge and returned the task for Luceon review.

## Changed Files

- `src/app/utils/rawMaterial2CleanMaterialAlgorithm.ts`
- `server/tests/rawmaterial2cleanmaterial-algorithm-skeleton-smoke.mjs`
- `TaskAndReport/TASK_TRACKING_LIST.md`
- `TaskAndReport/2026-05-25T12-36-33+0800_P0-RawMaterial2CleanMaterial-Real-Artifact-Shape-Compatibility-MockSafe-ReadOnly-NoDBWrite-NoMinIOWrite-NoRuntimePost_REPORT.md`

## Implementation Summary

- Replaced the top-level-array-only parser path with a bounded structured traversal.
- Added support for real-shaped `logic_tree.json` root objects with `node_id`, `title`, `level`, `status`, and `children`.
- Added support for real-shaped `skeleton.json` objects with top-level `blocks`.
- Added support for nested `flooded_content.json` arrays/records, including text stored under `content.paragraph_content` and `content.title_content`.
- Added stable source-ref extraction for `block_uid`, `node_id`, `uid`, `id`, and `__meta_flooding__.L1_id`.
- Preserved the no-invention rule: text-bearing fragments without stable refs are skipped and reported as warnings when enough referenced items remain; if an artifact has source text but no stable refs, the helper blocks with `MISSING_SOURCE_REFERENCE`.
- Kept the dry-run boundary unchanged: no final raw2clean output, no DB persistence, no runtime/service wiring, no UI workflow.

## Focused Real-Shape Fixture Evidence

`server/tests/rawmaterial2cleanmaterial-algorithm-skeleton-smoke.mjs` now includes a real-shape regression fixture:

- `logic_tree`: root object with `node_id=root` and nested `children`.
- `skeleton`: object with `blocks` using `block_uid`.
- `flooded_content`: nested arrays using `__meta_flooding__.L1_id`.
- Assertion: output reaches `MOCK_ALGORITHM_DRAFT_READY`.
- Assertion: source refs include `root`, `p0_80_77_359_96_title`, and `p0_78_120_443_135_paragraph`.
- Assertion: unreferenced flooded text is not promoted into draft output.
- Assertion: warning includes `flooded_content:skipped-unreferenced-text-fragments=1`.

## Read-Only Canonical Rehearsal Evidence

Only task-authorized read-only GETs were used:

- canonical material GET;
- canonical task GET;
- exact required artifact ObjectRef GETs through the upload proxy.

No POST/PATCH/PUT/DELETE, DB write/apply, MinIO write/list/delete, Docker, service execution, job-store edit, upload, retry, reparse, repair, rollback, batch, pressure, model/env/secret/source mutation, or readiness claim was performed.

Canonical result:

```json
{
  "ok": true,
  "draftStatus": "MOCK_ALGORITHM_DRAFT_READY",
  "materialHttpStatus": 200,
  "taskHttpStatus": 200,
  "sectionCount": 73,
  "blockCount": 71,
  "sampleSourceRefs": [
    "root",
    "p0_80_77_359_96_title",
    "p0_80_77_359_96_title",
    "p0_78_120_443_135_paragraph",
    "p0_80_149_280_164_paragraph",
    "p0_80_198_408_214_paragraph",
    "p0_80_228_307_242_paragraph",
    "p0_78_278_556_293_paragraph"
  ],
  "warnings": [
    "mock-algorithm-skeleton-only",
    "flooded_content:skipped-unreferenced-text-fragments=71"
  ]
}
```

Artifact roles read:

- `readable_tree`
- `logic_tree`
- `skeleton`
- `flooded_content`

Artifact ObjectRefs read:

- `eduassets-clean/toc-rebuild/1842780526581841/v4/readable_tree.md`
  - HTTP status: 200
  - bytes: 106
  - expected SHA-256: `bba5cf360fa7c0d92a9489ce84dfc40458de6072f812d7ab5d381b8e828946d7`
- `eduassets-clean/toc-rebuild/1842780526581841/v4/logic_tree.json`
  - HTTP status: 200
  - bytes: 375
  - expected SHA-256: `b61ee669b63bccb597f9ff31e5773ac1cc53a7bf6d6ef7a5ba73d467c7267665`
- `eduassets-clean/toc-rebuild/1842780526581841/v4/skeleton.json`
  - HTTP status: 200
  - bytes: 21160
  - expected SHA-256: `c004915e79dde976f68cbb460ae3e6bf34e81be6b7cc8bdc28d5252d5ec15f9e`
- `eduassets-clean/toc-rebuild/1842780526581841/v4/flooded_content.json`
  - HTTP status: 200
  - bytes: 20054
  - expected SHA-256: `e1a8355a80a5014b5a616ed441a4d0851c47d6a3d6092711ce765ffe11eea7b7`

Preserved source input:

- `eduassets-raw/mineru/1842780526581841/v1/content_list_v2.json`
- SHA-256: `f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db`
- size: `31543`

Source Clean Material:

- service: `toc-rebuild`
- assetVersion: `v4`
- jobId: `luceon-task-1779085089451-toc-rebuild-v4`
- provenance: `toc-rebuild/1842780526581841/v4/provenance.json`

Boundary flags from the rehearsal evidence:

```json
{
  "dbWrites": false,
  "minioWrites": false,
  "runtimePost": false,
  "optionalArtifactsRead": false
}
```

## Commands

- `git status --short --branch`
  - Exit code: 0
- `git fetch origin --prune --tags`
  - Exit code: 0
- `git checkout main && git pull --ff-only origin main`
  - Exit code: 0
- `node server/tests/rawmaterial2cleanmaterial-input-bundle-smoke.mjs`
  - Exit code: 0
- `node server/tests/rawmaterial2cleanmaterial-protocol-runner-smoke.mjs`
  - Exit code: 0
- `node server/tests/rawmaterial2cleanmaterial-algorithm-skeleton-smoke.mjs`
  - Exit code: 0
- `node server/tests/rawmaterial2cleanmaterial-artifact-backed-draft-smoke.mjs`
  - Exit code: 0
- `npx pnpm@10.4.1 exec tsc --noEmit`
  - Exit code: 0
- `npx pnpm@10.4.1 run build`
  - Exit code: 0
  - Note: Vite emitted the existing chunk-size warning.
- `git diff --check origin/main...HEAD`
  - Exit code: 0

## Boundary Confirmation

- DB POST/PATCH/PUT/DELETE/apply: not performed.
- DB reads: only task-authorized canonical material/task GETs were performed.
- MinIO write/delete/list/bucket scan: not performed.
- Artifact body reads: only exact required ObjectRefs were read through the upload proxy.
- Optional artifact body reads: not performed.
- Runtime POST, endpoint/service/worker execution: not performed.
- Docker/Compose operations: not performed.
- Job-store edits: not performed.
- Upload/retry/reparse/Re-AI/repair/reset/cancel: not performed.
- UI workflow work: not performed.
- Source/sample/env/secret/model mutation: not performed.
- Readiness, UAT, L3, pressure PASS, production, or go-live claim: not made.

## Residual Debt / Next Step

- This is still a mock-safe draft skeleton, not final RawMaterial2CleanMaterial cleaning quality.
- The canonical proof now reaches `MOCK_ALGORITHM_DRAFT_READY`; the next mainline task can decide whether to improve draft semantics, define final raw2clean output shape, or introduce a separately bounded persistence/service step.
- The current warning `flooded_content:skipped-unreferenced-text-fragments=71` is expected for this conservative pass: unreferenced text is intentionally skipped rather than promoted as source truth.
