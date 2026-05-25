# TASK-20260525-094618-P0-RawMaterial2CleanMaterial-Single-Sample-Algorithm-Skeleton-MockSafe-NoDBWrite-NoMinIOWrite-NoRuntime Luceon Review v2

Review time: 2026-05-25T10:17:27+0800

Decision:

```text
ACCEPTED_CODE_TEST_LEVEL
```

## Reviewed Evidence

Task brief:

```text
TaskAndReport/2026-05-25T09-46-18+0800_P0-RawMaterial2CleanMaterial-Single-Sample-Algorithm-Skeleton-MockSafe-NoDBWrite-NoMinIOWrite-NoRuntime_TASK.md
```

Lucode report:

```text
TaskAndReport/2026-05-25T09-46-18+0800_P0-RawMaterial2CleanMaterial-Single-Sample-Algorithm-Skeleton-MockSafe-NoDBWrite-NoMinIOWrite-NoRuntime_REPORT.md
```

Previous Luceon return review:

```text
TaskAndReport/2026-05-25T10-04-53+0800_P0-RawMaterial2CleanMaterial-Single-Sample-Algorithm-Skeleton-MockSafe-NoDBWrite-NoMinIOWrite-NoRuntime_LUCEON_REVIEW.md
```

Reviewed remote branch:

```text
origin/lucode/TASK-20260525-094618-P0-RawMaterial2CleanMaterial-Single-Sample-Algorithm-Skeleton-MockSafe-NoDBWrite-NoMinIOWrite-NoRuntime
```

Reviewed remote HEAD:

```text
4d4620453dce751ea5c328a3f61ddf3bf87f0230
```

Review baseline:

```text
origin/main@5efcf73134df9ea82b47b81973cff9e0ed8bf36c
```

Lucode's revised report does not self-embed the final pushed branch HEAD.
Luceon verified the GitHub-visible remote HEAD above and treats this review as
the authoritative head correction for acceptance.

## Scope Review

Changed files on the reviewed branch:

```text
A       TaskAndReport/2026-05-25T09-46-18+0800_P0-RawMaterial2CleanMaterial-Single-Sample-Algorithm-Skeleton-MockSafe-NoDBWrite-NoMinIOWrite-NoRuntime_REPORT.md
M       TaskAndReport/TASK_TRACKING_LIST.md
A       server/tests/rawmaterial2cleanmaterial-algorithm-skeleton-smoke.mjs
A       src/app/utils/rawMaterial2CleanMaterialAlgorithm.ts
```

The branch stayed inside the task boundary: deterministic mock-safe algorithm
skeleton plus focused smoke coverage and control-plane report update. It did not
touch DB, MinIO, runtime endpoints, Docker, UI workflow, package/dependency
files, AI/model calls, sample files, or production configuration.

## Acceptance Findings

### P0 return blocker fixed: numeric source references preserved

The returned defect was that stable numeric ids such as `id`, `node_id`, and
numeric block ids were classified as missing source references.

The revised implementation normalizes finite numeric source ids to string refs
while still rejecting genuinely missing source references with
`MISSING_SOURCE_REFERENCE`.

Verified numeric preservation includes:

```text
logic_tree id=101 -> sourceRef "101"
skeleton node_id=201 -> sourceRef "201"
flooded_content id=301 -> sourceRef "301"
flooded_content block_id=302 -> sourceRef "302"
```

### Mock-safe draft boundary preserved

The accepted implementation only builds a deterministic in-memory draft from a
Task 275 request plus injected artifact bodies. The draft preserves request
ObjectRefs and hashes, emits `persistencePlan.mode = none`, keeps
`writesPlanned = false`, and records boundary flags for no DB, MinIO, runtime
POST, Docker, or final artifact generation.

## Checks

| Command | Exit | Result |
| --- | ---: | --- |
| `git diff --name-status origin/main...origin/lucode/TASK-20260525-094618-P0-RawMaterial2CleanMaterial-Single-Sample-Algorithm-Skeleton-MockSafe-NoDBWrite-NoMinIOWrite-NoRuntime` | 0 | Scope matched task boundary |
| `git diff --check origin/main...origin/lucode/TASK-20260525-094618-P0-RawMaterial2CleanMaterial-Single-Sample-Algorithm-Skeleton-MockSafe-NoDBWrite-NoMinIOWrite-NoRuntime` | 0 | No whitespace errors |
| `node server/tests/rawmaterial2cleanmaterial-input-bundle-smoke.mjs` | 0 | Existing accepted input bundle smoke still passed |
| `node server/tests/rawmaterial2cleanmaterial-protocol-runner-smoke.mjs` | 0 | Existing accepted protocol runner smoke still passed |
| `node server/tests/rawmaterial2cleanmaterial-algorithm-skeleton-smoke.mjs` | 0 | Draft skeleton success and blocked-code coverage passed, including numeric source refs |
| `npx pnpm@10.4.1 exec tsc --noEmit` | 0 | TypeScript check completed with no diagnostics |
| `npx pnpm@10.4.1 run build` | 0 | Vite production build completed; existing chunk-size warning only |
| Independent numeric source-ref probe | 0 | Verified `101`, `201`, and `301` preservation plus missing-ref blocking outside Lucode's smoke script |

## Acceptance Boundary

This is a code/test-level acceptance of the mock-safe
RawMaterial2CleanMaterial algorithm skeleton and the returned numeric
source-reference fix.

This does not approve or claim real RawMaterial2CleanMaterial algorithm quality,
live artifact reads, DB apply/write, MinIO write/delete, runtime POST,
endpoint/worker execution, Docker/Compose operation, UI workflow, AI/model
execution, batch execution, production validation, UAT, L3, pressure PASS,
release readiness, production readiness, production online, or go-live.

## Residual Debt

- The skeleton remains deterministic and mock-safe; it is not a full cleaning
  algorithm.
- Real artifact IO, persistence, service transport, UI operator workflow, output
  artifact generation, quality policy, and production validation remain deferred.
- A future mainline task should decide whether the next narrow step is stricter
  draft schema/fixture contract or controlled artifact-read integration.

