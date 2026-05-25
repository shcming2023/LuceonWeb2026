# TASK-20260525-130654-P0-RawMaterial2CleanMaterial-Single-Sample-Draft-To-Output-Contract-DryRun-NoDBWrite-NoMinIOWrite-NoRuntimePost Report

Reported at: 2026-05-25T13:19:24+0800

Status: SUCCESS_MOCK_SAFE_DRAFT_TO_OUTPUT_CONTRACT_PREVIEW

Branch: `codex/TASK-20260525-130654-output-contract`

Implementation HEAD before report/ledger closure: `18c116097556d38b73ef67c928f5ec3b095b6c70`

## Summary

Task 281 implemented a pure in-memory RawMaterial2CleanMaterial output contract
preview helper. It converts a ready artifact-backed draft into a deterministic
candidate output contract while preserving material/task identity, source Clean
Material provenance, source input, source artifact refs, section/block source
refs, and dry-run boundary flags.

No durable raw2clean output was written. This is not a DB apply, MinIO write,
runtime service execution, product-quality cleaning acceptance, readiness, UAT,
L3, pressure PASS, or go-live result.

## Changed Files

- `src/app/utils/rawMaterial2CleanMaterialOutputContract.ts`
- `server/tests/rawmaterial2cleanmaterial-output-contract-smoke.mjs`
- `TaskAndReport/2026-05-25T13-19-24+0800_P0-RawMaterial2CleanMaterial-Single-Sample-Draft-To-Output-Contract-DryRun-NoDBWrite-NoMinIOWrite-NoRuntimePost_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

## Implementation Evidence

Added output contract constants and a pure builder:

- `kind = raw-material-2-clean-material-output-candidate`
- `contractVersion = v0.dry-run`
- deterministic stable JSON serialization
- SHA-256 and byte-size preview
- source Clean Material metadata preservation
- source input and source artifact ObjectRef preservation
- section/block source-ref preservation
- explicit dry-run boundary flags:
  - `dbAccess=false`
  - `dbWrites=false`
  - `minioAccess=false`
  - `minioWrites=false`
  - `runtimePost=false`
  - `dockerOperation=false`
  - `durableArtifactCreated=false`

Blocked cases covered:

- missing draft -> `MISSING_DRAFT`
- unsupported draft kind -> `UNSUPPORTED_DRAFT_KIND`
- non-ready draft -> `DRAFT_NOT_READY`
- missing source refs -> `MISSING_SOURCE_REFERENCE`
- live dependency markers -> `LIVE_DEPENDENCY_NOT_ALLOWED`

## Commands And Exit Codes

All commands ran in `/Users/concm/Dev_workspace/Luceon2026` unless noted.

| Command | Exit |
| --- | ---: |
| `node server/tests/rawmaterial2cleanmaterial-output-contract-smoke.mjs` | 0 |
| `node server/tests/rawmaterial2cleanmaterial-input-bundle-smoke.mjs` | 0 |
| `node server/tests/rawmaterial2cleanmaterial-protocol-runner-smoke.mjs` | 0 |
| `node server/tests/rawmaterial2cleanmaterial-algorithm-skeleton-smoke.mjs` | 0 |
| `node server/tests/rawmaterial2cleanmaterial-artifact-backed-draft-smoke.mjs` | 0 |
| `npx pnpm@10.4.1 exec tsc --noEmit` | 0 |
| `npx pnpm@10.4.1 run build` | 0 |
| `git diff --check origin/main...HEAD` | 0 |

`vite build` emitted only the known chunk-size warning for the main bundle.

## Canonical Read-Only Rehearsal

Target:

```text
materialId = 1842780526581841
taskId = task-1779085089451
serviceName = toc-rebuild
assetVersion = v4
jobId = luceon-task-1779085089451-toc-rebuild-v4
```

Read-only inputs:

- `GET /__proxy/db/materials/1842780526581841` -> 200
- `GET /__proxy/db/tasks/task-1779085089451` -> 200
- exact artifact GETs through `/__proxy/upload/proxy-file` for required roles:
  - `readable_tree` -> 200, SHA matched `bba5cf360fa7c0d92a9489ce84dfc40458de6072f812d7ab5d381b8e828946d7`
  - `logic_tree` -> 200, SHA matched `b61ee669b63bccb597f9ff31e5773ac1cc53a7bf6d6ef7a5ba73d467c7267665`
  - `skeleton` -> 200, SHA matched `c004915e79dde976f68cbb460ae3e6bf34e81be6b7cc8bdc28d5252d5ec15f9e`
  - `flooded_content` -> 200, SHA matched `e1a8355a80a5014b5a616ed441a4d0851c47d6a3d6092711ce765ffe11eea7b7`

Result:

```json
{
  "ok": true,
  "kind": "raw-material-2-clean-material-output-candidate",
  "contractVersion": "v0.dry-run",
  "draftStatus": "MOCK_ALGORITHM_DRAFT_READY",
  "sectionCount": 73,
  "blockCount": 71,
  "sourceRefCount": 72,
  "preview": {
    "contentType": "application/json",
    "size_bytes": 21706,
    "sha256": "d641c3dbfda693049e740341c86ad7a37e9970d13af8e530591f6af25316f3b3"
  }
}
```

The rehearsal used DB GETs and exact artifact GETs only. It did not call DB
POST/PATCH/PUT/DELETE, MinIO write/delete/list/bucket scan, runtime POST,
service execution, Docker/Compose, job-store edit, upload/retry/reparse/Re-AI,
model/env/secret mutation, or source/sample mutation.

## Residual Debt

- The output contract is still an in-memory preview; no durable raw2clean
  artifact exists.
- The current draft algorithm is still skeletal and does not claim final
  content-cleaning quality.
- No DB apply or operator workflow for raw2clean output exists yet.
- Multi-sample/batch behavior remains intentionally untested.

## Recommended Next Mainline Step

Proceed to a narrowly authorized single-sample dry-run artifact materialization
task that writes the raw2clean candidate JSON to a temporary/local or explicitly
approved non-production target, or, if the Director wants to cross the durable
boundary now, issue a separate task with exact DB/MinIO apply authorization and
rollback/evidence requirements.
