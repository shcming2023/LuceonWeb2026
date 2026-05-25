# TASK-20260525-102604-P0-RawMaterial2CleanMaterial-Single-Sample-Artifact-Backed-Draft-DryRun-ReadOnly-NoDBWrite-NoMinIOWrite-NoRuntimePost Luceon Review

Review time: 2026-05-25T11:27:42+0800

Decision:

```text
ACCEPTED_CODE_TEST_LEVEL_WITH_CANONICAL_ARTIFACT_READ_BLOCKED
```

## Reviewed Evidence

Task brief:

```text
TaskAndReport/2026-05-25T10-26-04+0800_P0-RawMaterial2CleanMaterial-Single-Sample-Artifact-Backed-Draft-DryRun-ReadOnly-NoDBWrite-NoMinIOWrite-NoRuntimePost_TASK.md
```

Lucode report:

```text
TaskAndReport/2026-05-25T10-26-04+0800_P0-RawMaterial2CleanMaterial-Single-Sample-Artifact-Backed-Draft-DryRun-ReadOnly-NoDBWrite-NoMinIOWrite-NoRuntimePost_REPORT.md
```

Reviewed remote branch:

```text
origin/lucode/TASK-20260525-102604-P0-RawMaterial2CleanMaterial-Single-Sample-Artifact-Backed-Draft-DryRun-ReadOnly-NoDBWrite-NoMinIOWrite-NoRuntimePost
```

Reviewed remote HEAD:

```text
00f18124475c2bf967c55dcb5167e193a024b7db
```

Review baseline:

```text
origin/main@318bd775afb94fd69dc7535323760908f431494f
```

Lucode's report did not self-embed the final pushed branch HEAD. Luceon
verified the GitHub-visible remote HEAD above.

## Scope Review

Changed files on the reviewed branch:

```text
A       TaskAndReport/2026-05-25T10-26-04+0800_P0-RawMaterial2CleanMaterial-Single-Sample-Artifact-Backed-Draft-DryRun-ReadOnly-NoDBWrite-NoMinIOWrite-NoRuntimePost_REPORT.md
M       TaskAndReport/TASK_TRACKING_LIST.md
A       server/tests/rawmaterial2cleanmaterial-artifact-backed-draft-smoke.mjs
A       src/app/utils/rawMaterial2CleanMaterialArtifactBackedDraft.ts
```

The implementation stayed inside the task boundary. It adds a focused
reader-injected artifact-backed dry-run helper and smoke coverage. It does not
touch DB writers, MinIO writers, runtime endpoints, workers, Docker, UI,
package/dependency files, PRD/architecture docs, or local private role files.

## Acceptance Findings

### Accepted: code-level artifact-backed dry-run bridge

`buildRawMaterial2CleanMaterialArtifactBackedDraftDryRun()` correctly composes:

```text
material/task or accepted bundle/request
-> Task 273 input bundle
-> Task 275 request
-> required artifact body reader
-> Task 276 draft skeleton
```

The helper reads only required roles:

```text
readable_tree
logic_tree
skeleton
flooded_content
```

Focused smoke verifies success, request-direct input, missing input/reader
blocking, artifact read failure blocking, draft build blocking, live dependency
marker blocking, optional artifact non-read, and numeric source-ref preservation.

### Blocked: canonical artifact-backed rehearsal did not reach draft success

The task's stage-breakthrough target was a real canonical artifact-backed
dry-run. That target is still blocked.

Lucode's read-only rehearsal and Luceon's independent read-only probe both show:

```text
GET /__proxy/db/materials/1842780526581841 -> 200
GET /__proxy/db/tasks/task-1779085089451 -> 200
metadata task assetVersion -> v4
metadata readable_tree object -> toc-rebuild/1842780526581841/v4/readable_tree.md
GET /__proxy/upload/proxy-file?objectName=toc-rebuild%2F1842780526581841%2Fv4%2Freadable_tree.md&bucket=eduassets-clean -> 500
response -> {"error":"The specified key does not exist."}
```

The first required artifact body is not retrievable by its recorded ObjectRef, so
the real artifact-backed draft cannot be produced yet. Lucode correctly stopped
under the task Stop Rule instead of converting this into mock-only acceptance.

This is not returned as a Lucode code defect. The next blocker is data/control
plane diagnosis: artifact availability, bucket/config mismatch, stale metadata,
or ObjectRef mismatch.

## Luceon Checks

| Command / Probe | Exit | Result |
| --- | ---: | --- |
| `git diff --name-status origin/main...origin/lucode/TASK-20260525-102604-P0-RawMaterial2CleanMaterial-Single-Sample-Artifact-Backed-Draft-DryRun-ReadOnly-NoDBWrite-NoMinIOWrite-NoRuntimePost` | 0 | Scope matched task boundary |
| `git diff --check origin/main...origin/lucode/TASK-20260525-102604-P0-RawMaterial2CleanMaterial-Single-Sample-Artifact-Backed-Draft-DryRun-ReadOnly-NoDBWrite-NoMinIOWrite-NoRuntimePost` | 0 | No whitespace errors |
| `node server/tests/rawmaterial2cleanmaterial-input-bundle-smoke.mjs` | 0 | Passed |
| `node server/tests/rawmaterial2cleanmaterial-protocol-runner-smoke.mjs` | 0 | Passed |
| `node server/tests/rawmaterial2cleanmaterial-algorithm-skeleton-smoke.mjs` | 0 | Passed |
| `node server/tests/rawmaterial2cleanmaterial-artifact-backed-draft-smoke.mjs` | 0 | Passed |
| `npx pnpm@10.4.1 exec tsc --noEmit` | 0 | TypeScript check completed with no diagnostics |
| `npx pnpm@10.4.1 run build` | 0 | Vite production build completed; existing chunk-size warning only |
| Luceon independent exact read-only canonical artifact probe | 2 | Confirmed `readable_tree.md` ObjectRef returns HTTP 500 key-not-found through proxy |

## Acceptance Boundary

This accepts only the code/test-level bridge and the stop-rule-compliant blocked
canonical evidence.

This does not accept:

- a successful real artifact-backed RawMaterial2CleanMaterial draft;
- final RawMaterial2CleanMaterial output;
- raw2clean DB/MinIO apply;
- raw2clean service/runtime existence;
- content-cleaning quality;
- product UI completion;
- UAT, L3, pressure PASS, release readiness, production readiness, production
  online, or go-live.

## Next Mainline Recommendation

Issue a narrow Luceon read-only diagnosis task for the canonical v4 artifact
ObjectRef availability mismatch. The task should determine whether the missing
read is caused by:

- artifact object missing from `eduassets-clean`;
- bucket/config mismatch;
- stale DB metadata/ObjectRef;
- proxy resolver behavior;
- prior v4 job artifact persistence gap.

No DB or MinIO correction should be performed without a separate explicit task
and authorization.

