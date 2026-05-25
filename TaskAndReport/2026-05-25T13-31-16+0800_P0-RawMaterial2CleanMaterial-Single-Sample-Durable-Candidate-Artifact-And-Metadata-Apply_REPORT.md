# TASK-20260525-132001-P0-RawMaterial2CleanMaterial-Single-Sample-Durable-Candidate-Artifact-And-Metadata-Apply Report

Reported at: 2026-05-25T13:31:16+0800

Status: SUCCESS_SINGLE_SAMPLE_DURABLE_CANDIDATE_APPLIED

Branch: `codex/TASK-20260525-132001-durable-boundary`

Implementation HEAD before report/ledger closure: `55e9a09879a4caeb849420cf6589a031c6306b22`

## Summary

Task 282 crossed the RawMaterial2CleanMaterial durable boundary for exactly one
canonical sample. The generated candidate JSON is now durably present in
`eduassets-clean`, and task/material metadata both point to the same ObjectRef.

This is a candidate/draft artifact. It is not final Clean Material quality
acceptance, not an operator approval workflow, not a raw2clean runtime service,
and not UAT/L3/pressure/release/production readiness or go-live.

## Changed Files

- `server/services/rawmaterial2cleanmaterial/durable-candidate.mjs`
- `server/tests/rawmaterial2cleanmaterial-durable-candidate-smoke.mjs`
- `server/tests/rawmaterial2cleanmaterial-durable-candidate-apply.mjs`
- `TaskAndReport/2026-05-25T13-31-16+0800_P0-RawMaterial2CleanMaterial-Single-Sample-Durable-Candidate-Artifact-And-Metadata-Apply_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

## Durable ObjectRef

```json
{
  "bucket": "eduassets-clean",
  "object": "raw-material-2-clean-material/1842780526581841/v1/candidate.json",
  "sha256": "49a6189e12fe1c65ffdfbdf2e5b73d204c432002dff55812dc8c3be17ac2ce27",
  "size_bytes": 21767,
  "content_type": "application/json"
}
```

Output contract preview preserved separately:

```json
{
  "contentType": "application/json",
  "size_bytes": 21706,
  "sha256": "c87cbf75bf91b43700239ea890f9c6fda7ef2e3c61db18a4533397235e872c16"
}
```

The durable ObjectRef SHA/size are for the actual JSON bytes stored in MinIO.
The output contract preview is the Task 281 deterministic contract preview and
is retained as provenance, not used as the stored object checksum.

## Metadata Paths Patched

Exactly these DB metadata paths were patched:

- `tasks/task-1779085089451.metadata.rawMaterial2CleanMaterialJobs["raw-material-2-clean-material"]`
- `materials/1842780526581841.metadata.rawMaterial2CleanMaterial.currentCandidate`
- `materials/1842780526581841.metadata.rawMaterial2CleanMaterial.candidates.v1`

The metadata records:

- candidate/draft status;
- source `toc-rebuild v4` clean material;
- source input ObjectRef;
- source clean artifact refs;
- candidate ObjectRef;
- section/block/sourceRef counts;
- output contract preview;
- candidate artifact preview;
- explicit false flags for runtime/service/final-quality/readiness.

No full candidate JSON content was embedded in DB metadata.

## Runtime Apply Evidence

Pre-apply dry-run:

- regenerated artifact-backed draft from canonical material/task and exact
  source clean artifact GETs;
- reached `MOCK_ALGORITHM_DRAFT_READY`;
- `sectionCount=73`;
- `blockCount=71`;
- `sourceRefCount=72`;
- produced candidate bytes SHA `49a6189e12fe1c65ffdfbdf2e5b73d204c432002dff55812dc8c3be17ac2ce27`, size `21767`.

Durable write:

- first host-side MinIO SDK attempts were blocked by local host/API credential
  mismatch before any put or DB patch occurred;
- final MinIO write used a container-local MinIO client invocation against the
  already-running `cms-upload-server` runtime environment, without rebuild,
  restart, compose change, volume cleanup, or service mutation;
- result: `action=putObject`, target ObjectRef above, SHA/size verified.

DB apply:

- `PATCH /__proxy/db/tasks/task-1779085089451` succeeded;
- `PATCH /__proxy/db/materials/1842780526581841` succeeded;
- post-apply GET verified both metadata refs exactly equal the durable ObjectRef;
- post-apply proxy GET of candidate artifact returned 200 and matched SHA/size.

Post-apply verification output:

```json
{
  "ok": true,
  "dbPatch": 2,
  "candidateProxyGet": 200,
  "sha256": "49a6189e12fe1c65ffdfbdf2e5b73d204c432002dff55812dc8c3be17ac2ce27",
  "size_bytes": 21767
}
```

## Commands And Exit Codes

All commands ran in `/Users/concm/Dev_workspace/Luceon2026` unless noted.

| Command | Exit |
| --- | ---: |
| `node server/tests/rawmaterial2cleanmaterial-durable-candidate-smoke.mjs` | 0 |
| `node server/tests/rawmaterial2cleanmaterial-input-bundle-smoke.mjs` | 0 |
| `node server/tests/rawmaterial2cleanmaterial-protocol-runner-smoke.mjs` | 0 |
| `node server/tests/rawmaterial2cleanmaterial-algorithm-skeleton-smoke.mjs` | 0 |
| `node server/tests/rawmaterial2cleanmaterial-artifact-backed-draft-smoke.mjs` | 0 |
| `node server/tests/rawmaterial2cleanmaterial-output-contract-smoke.mjs` | 0 |
| `node server/tests/rawmaterial2cleanmaterial-durable-candidate-apply.mjs` | 0 |
| `npx pnpm@10.4.1 exec tsc --noEmit` | 0 |
| `npx pnpm@10.4.1 run build` | 0 |
| `git diff --check origin/main...HEAD` | 0 |

`vite build` emitted only the known chunk-size warning.

Real apply operation counts:

- MinIO `putObject`: 1
- DB PATCH: 2
- MinIO delete/list/bucket scan/copy/move/cleanup: 0
- runtime POST/service execution/job submission: 0
- Docker/Compose build/up/down/restart/recreate/volume/prune/network mutation: 0
- job-store edit/source/sample/model/env/secret mutation: 0

## Residual Debt

- The candidate is still skeletal raw2clean output; final cleaning quality is
  not accepted.
- There is no operator approval UI/state machine for this candidate yet.
- There is no raw2clean runtime service/worker/endpoint.
- There is no multi-sample/batch validation.
- Existing metadata is deliberately lightweight and may later need schema
  consolidation after the mainline stabilizes.

## Recommended Next Mainline Step

Do not broaden into batch or cleanup yet. The next mainline step should be a
narrow read-only product-surface verification: prove the durable candidate is
discoverable from material/task metadata and inspectable through an existing or
minimal UI/API surface without creating an approval workflow.
