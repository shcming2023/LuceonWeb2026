# Luceon Review v2 - TASK-20260522-164820-P0-CleanService-Verified-Metadata-Persistence-Payload-Planner-NoDB

## Review Result

`RETURNED_IMPLEMENTATION_GAP`

The delivery branch is now GitHub-visible and the focused smoke tests pass, but
the implementation does not yet satisfy the Task 250 persistence-planning
contract. This return is narrow: fix the planner/candidate contract and the
focused smoke coverage only.

## Reviewed Branch

```text
origin/lucode/TASK-20260522-164820
```

Actual reviewed remote HEAD:

```text
313889aece310f9742a33aea18099e705022f4a8
```

Reviewed against:

```text
origin/main=48d254050de5f42aa4ce4924c6f941b0c2218e46
```

## Verification Run By Luceon

Review worktree:

```text
/tmp/luceon-task250-review-313889a
```

Commands run:

```bash
node server/tests/cleanservice-metadata-persistence-smoke.mjs
node server/tests/cleanservice-output-ingestion-candidate-smoke.mjs
node server/tests/cleanservice-output-verifier-smoke.mjs
git diff --check origin/main..HEAD
```

Observed result:

- `cleanservice-metadata-persistence-smoke`: PASS 6/6.
- `cleanservice-output-ingestion-candidate-smoke`: PASS 7/7.
- `cleanservice-output-verifier-smoke`: PASS 8/8.
- `git diff --check origin/main..HEAD`: no output.

Additional Luceon reproduction:

```text
sourceInput in candidate: {"bucket":"eduassets-raw","object":"mineru/1842780526581841/v1/content_list_v2.json","sha256":"source-sha","sizeBytes":31543}
sourceInput persisted in generated patches: false
missing identity candidate: {"materialId":null,"assetVersion":null,"jobId":null}
missing identity plan result: {"ok":true,"shouldApply":true}
```

## Blocking Findings

### F1. Source Input Is Validated But Not Persisted In Either Patch

Task 250 requires the generated dry-run DB PATCH payloads to preserve source
input bucket/object/sha256/size before any real DB apply is authorized.

The implementation validates `candidate.verificationSummary.sourceInput`, but
the generated `taskPatch` and `materialPatch` copy only `taskSummary` and
`materialSummary`. `sourceInput` remains only in the non-persisted
`verificationSummary`.

Relevant code:

```text
server/services/cleanservice/metadata-persistence.mjs:81-92
server/services/cleanservice/metadata-persistence.mjs:129-151
server/services/cleanservice/metadata-summary.mjs:163-207
```

Risk:

- A later real DB persistence task would write Clean Material output refs
  without the canonical Raw Material source ObjectRef/hash/size needed for
  audit and rollback.
- This breaks the PDF -> Raw Material -> Clean Material traceability contract.

Required correction:

- Include bounded source input evidence in at least the task-side
  `cleanServiceJobs['toc-rebuild']` summary, and preferably also in the
  material-side `cleanMaterials['toc-rebuild']` summary if that is the chosen
  asset audit record.
- The persisted shape must remain ID-only/source-reference-only and must not
  include full artifact contents.
- Add focused assertions that inspect `taskPatch` and/or `materialPatch` and
  prove source bucket/object/sha256/size are present.

### F2. Missing Core Identity Fields Still Produce An Apply Plan

Task 250 requires hard traceability fields before any PATCH payload is generated:

- `materialId`;
- `assetVersion`;
- `jobId`;
- `parseTaskId` when available.

The planner copies `candidate.materialId` and `candidate.parseTaskId`, but it
does not gate missing `materialId`, `assetVersion`, or `jobId`. Luceon's
independent reproduction created a candidate with all three missing and the
planner still returned:

```text
{"ok":true,"shouldApply":true}
```

Relevant code:

```text
server/services/cleanservice/metadata-persistence.mjs:51-53
server/services/cleanservice/metadata-persistence.mjs:81-120
server/services/cleanservice/metadata-persistence.mjs:157-170
```

Risk:

- The planner could generate a future DB patch that cannot be reliably tied to
  a material, asset version, or external job.

Required correction:

- Add explicit gates for missing `materialId`, `assetVersion`, and `jobId`.
- Return `shouldApply=false` with precise reasons, such as:

  ```text
  missing-material-id
  missing-asset-version
  missing-job-id
  ```

- Add focused smoke coverage for these missing-identity paths.

### F3. Control-Plane HEAD Evidence Still Points At The Intermediate Commit

The actual reviewed remote branch HEAD is:

```text
313889aece310f9742a33aea18099e705022f4a8
```

But the ledger and report still identify `94dbb9f6139e6da06f7ec75af56d3c546ae7f0a1`
as the branch/head evidence:

```text
TaskAndReport/TASK_TRACKING_LIST.md:256
TaskAndReport/2026-05-22T16-48-20+0800_P0-CleanService-Verified-Metadata-Persistence-Payload-Planner-NoDB_REPORT.md:5-7
```

Required correction:

- On resubmission, record the actual final remote branch HEAD, not the
  intermediate implementation commit.
- If Lucode wants to retain the implementation commit as a separate reference,
  label it as implementation baseline, not final delivery HEAD.

## Narrow Return Requirements

Lucode should make the smallest implementation correction needed:

1. Preserve source input bucket/object/sha256/size in the generated dry-run
   persistence patch shape.
2. Gate missing `materialId`, `assetVersion`, and `jobId` before generating
   applyable patches.
3. Add focused smoke assertions for F1 and F2.
4. Correct report/ledger HEAD evidence to the actual final remote branch HEAD.
5. Re-run the required Task 250 checks and report exact exit codes.

Do not widen into:

- real DB writes;
- `POST /api/v1/jobs`;
- MinIO read/write/delete/list;
- LLM calls;
- Docker/Compose/env mutation;
- worker activation;
- upload-server wiring;
- RawMaterial2CleanMaterial;
- UAT/L3/readiness/pressure PASS/go-live claims.

## Review Boundary

No code was merged. Task 250 remains open and returned to Lucode.
