# TASK-20260524-215051 Lucode Report

Report time: 2026-05-24T21:58:19+0800

## Branch And HEAD

- Branch: `lucode/TASK-20260524-215051-P0-RawMaterial2CleanMaterial-Accepted-CleanMaterial-Input-Bundle-Builder-MockSafe-NoRuntime`
- Base HEAD before Lucode changes: `d8c3aa5bb340f469140db3542bdbfc4199105756`
- Implementation commit anchor before report HEAD backfill: `dba7d6293f9e3488c807880bb9d342db7b3374d6`
- Final pushed branch HEAD: see Lucode final thread reply for the exact pushed commit SHA.

## Scope Implemented

Implemented a pure mock-safe RawMaterial2CleanMaterial input bundle builder for
accepted `toc-rebuild` Clean Material metadata.

The helper:

- accepts material/task-like objects shaped around
  `material.metadata.cleanMaterials[serviceName]` and
  `task.metadata.cleanServiceJobs[serviceName]`;
- supports only `serviceName=toc-rebuild`;
- requires `operatorDecision.state=accepted`, completed service state, current
  asset version alignment, job id, provenance object, source input object plus
  sha256, and the four required artifact object refs;
- emits a small JSON bundle with material/task ids, service name, asset version,
  job id, provenance object, source input, artifact refs, and accepted decision
  metadata;
- includes optional object refs for `metrics`, `provenance`, and
  `unresolved_anchors` when already present;
- refuses body-shaped artifacts instead of reading/fetching artifact content.

## Files Changed

- `src/app/utils/rawMaterial2CleanMaterialInputBundle.ts`
- `server/tests/rawmaterial2cleanmaterial-input-bundle-smoke.mjs`
- `TaskAndReport/TASK_TRACKING_LIST.md`
- `TaskAndReport/2026-05-24T21-50-51+0800_P0-RawMaterial2CleanMaterial-Accepted-CleanMaterial-Input-Bundle-Builder-MockSafe-NoRuntime_REPORT.md`

## Blocking Semantics Covered

The helper returns structured blocked results for:

- missing material or task;
- unsupported service name;
- missing Clean Material summary;
- missing CleanService task summary;
- material/task mismatch;
- non-accepted operator decision;
- service not completed;
- missing or mismatched asset version;
- missing or mismatched job id;
- missing provenance object;
- missing source input object or sha256;
- missing required artifact refs;
- artifact prefix mismatch outside `toc-rebuild/{materialId}/{assetVersion}/`;
- body-shaped artifact refs that would imply artifact body reads.

Stable codes include the task-required examples:

- `CLEAN_MATERIAL_NOT_ACCEPTED`
- `MISSING_SOURCE_INPUT`
- `MISSING_REQUIRED_ARTIFACT`
- `ASSET_VERSION_MISMATCH`
- `ARTIFACT_PREFIX_MISMATCH`

## Checks

| Command | Exit | Evidence |
| --- | ---: | --- |
| `node server/tests/rawmaterial2cleanmaterial-input-bundle-smoke.mjs` | 0 | accepted canonical-shape bundle path plus non-accepted, missing sourceInput, every missing required artifact role, assetVersion mismatch, missing jobId, prefix mismatch, missing material/task, and body-shaped artifact blocking all passed |
| `npx pnpm@10.4.1 exec tsc --noEmit` | 0 | TypeScript check completed with no diagnostics |
| `npx pnpm@10.4.1 run build` | 0 | Vite production build completed; existing chunk-size warning only |
| `git diff --check origin/main...HEAD` | 0 | no whitespace errors |

## Boundary Statement

No live DB read/write, MinIO read/write/delete/list/get, Docker/Compose,
runtime service execution, RawMaterial2CleanMaterial transport/service,
Mineru2Table call, upload/retry/reparse/Re-AI, model, secret, sample asset, or
production validation operation was performed.

This report does not claim UAT, L3, pressure PASS, release readiness,
production readiness, production online, or go-live.

## Risks And Residual Debt

- The helper only builds a traceable input bundle; downstream
  RawMaterial2CleanMaterial protocol, service execution, persistence, UI launch
  workflow, and production validation remain intentionally deferred.
- Artifact body/content validation remains deferred by design; this task only
  carries ObjectRefs.
