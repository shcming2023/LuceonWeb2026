# TASK-20260525-094618-P0-RawMaterial2CleanMaterial-Single-Sample-Algorithm-Skeleton-MockSafe-NoDBWrite-NoMinIOWrite-NoRuntime Luceon Review

Review time: 2026-05-25T10:04:53+0800

Decision:

```text
RETURNED_FOR_NUMERIC_SOURCE_REFERENCE_GAP
```

## Reviewed Evidence

Task brief:

```text
TaskAndReport/2026-05-25T09-46-18+0800_P0-RawMaterial2CleanMaterial-Single-Sample-Algorithm-Skeleton-MockSafe-NoDBWrite-NoMinIOWrite-NoRuntime_TASK.md
```

Lucode branch-local report:

```text
TaskAndReport/2026-05-25T09-46-18+0800_P0-RawMaterial2CleanMaterial-Single-Sample-Algorithm-Skeleton-MockSafe-NoDBWrite-NoMinIOWrite-NoRuntime_REPORT.md
```

Reviewed remote branch:

```text
origin/lucode/TASK-20260525-094618-P0-RawMaterial2CleanMaterial-Single-Sample-Algorithm-Skeleton-MockSafe-NoDBWrite-NoMinIOWrite-NoRuntime
```

Reviewed remote HEAD:

```text
fd014b851962e8155932a175197a2231eac7a1d4
```

Review baseline:

```text
origin/main@5a2022004b9d0b563db1d4587cd5ccaa92bf183e
```

Lucode's report did not self-embed the final pushed branch HEAD. Luceon
verified the GitHub-visible remote HEAD above.

## Scope Review

Changed files on the Lucode branch:

```text
A       TaskAndReport/2026-05-25T09-46-18+0800_P0-RawMaterial2CleanMaterial-Single-Sample-Algorithm-Skeleton-MockSafe-NoDBWrite-NoMinIOWrite-NoRuntime_REPORT.md
M       TaskAndReport/TASK_TRACKING_LIST.md
A       server/tests/rawmaterial2cleanmaterial-algorithm-skeleton-smoke.mjs
A       src/app/utils/rawMaterial2CleanMaterialAlgorithm.ts
```

The branch stayed inside the task's allowed file scope and did not touch DB,
MinIO, runtime, Docker, UI, package, PRD, or CleanService runtime files.

## Blocking Finding

### P0 Return: numeric source ids are misclassified as missing source refs

Task red line:

```text
ID-only / reference-backed extraction: extracted source content must preserve
stable Block IDs, node IDs, or source references when available.
```

The algorithm's source-reference extraction only accepts string values. If an
injected structured artifact uses numeric ids such as:

```json
{ "id": 101, "title": "Numeric section id" }
{ "node_id": 201, "title": "Numeric node id" }
{ "id": 301, "text": "Numeric block id" }
```

the skeleton returns:

```text
ok = false
code = MISSING_SOURCE_REFERENCE
reason = source-derived item is missing a source reference: logic_tree
```

This is a mainline blocker because numeric block/node ids are still stable
source references and must be preserved rather than treated as absent.

Required fix:

- normalize finite numeric `id`, `blockId`, `block_id`, `nodeId`, `node_id`, or
  equivalent source-id fields into string source refs;
- keep the existing block behavior for genuinely missing source references;
- add focused smoke coverage for at least numeric `id`, numeric `node_id`, and
  numeric block id/reference;
- keep the fix inside the algorithm skeleton and focused test only.

## Checks

```text
git diff --name-status origin/main...origin/lucode/TASK-20260525-094618-P0-RawMaterial2CleanMaterial-Single-Sample-Algorithm-Skeleton-MockSafe-NoDBWrite-NoMinIOWrite-NoRuntime
```

Result: file list shown in scope review.

```text
git diff --check origin/main...origin/lucode/TASK-20260525-094618-P0-RawMaterial2CleanMaterial-Single-Sample-Algorithm-Skeleton-MockSafe-NoDBWrite-NoMinIOWrite-NoRuntime
```

Result: PASS.

Checks run in temporary review worktree:

```text
node server/tests/rawmaterial2cleanmaterial-input-bundle-smoke.mjs
```

Result: PASS.

```text
node server/tests/rawmaterial2cleanmaterial-protocol-runner-smoke.mjs
```

Result: PASS.

```text
node server/tests/rawmaterial2cleanmaterial-algorithm-skeleton-smoke.mjs
```

Result: PASS.

```text
npx pnpm@10.4.1 exec tsc --noEmit
```

Result: PASS.

```text
npx pnpm@10.4.1 run build
```

Result: PASS with existing Vite chunk-size warning.

Additional Luceon probe:

```text
numeric id / numeric node_id / numeric flooded_content id source-reference probe
```

Result: FAIL with `MISSING_SOURCE_REFERENCE` on `logic_tree`.

## Return Boundary

Do not broaden into:

- real RawMaterial2CleanMaterial algorithm;
- live artifact reads;
- DB or MinIO operation;
- endpoint, worker, scheduler, transport, Docker service, or UI workflow;
- AI/model calls;
- output persistence;
- readiness/go-live wording.

## Required Resubmission

Lucode should revise the same branch or a replacement branch and update the
branch-local report/ledger. The resubmission should include:

- exact branch and full HEAD;
- changed files;
- focused explanation of numeric source-reference preservation;
- command exit codes;
- explicit no DB/MinIO/runtime/Docker/readiness statement.
