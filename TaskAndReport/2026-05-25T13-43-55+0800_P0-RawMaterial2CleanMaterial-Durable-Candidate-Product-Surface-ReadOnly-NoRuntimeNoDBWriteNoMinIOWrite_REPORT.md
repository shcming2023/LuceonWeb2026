# TASK-20260525-133541-P0-RawMaterial2CleanMaterial-Durable-Candidate-Product-Surface-ReadOnly-NoRuntimeNoDBWriteNoMinIOWrite Report

Reported at: 2026-05-25T13:43:55+0800

Status: SUCCESS_READONLY_PRODUCT_SURFACE_VERIFIED

Branch: `codex/TASK-20260525-133541-product-surface`

Implementation HEAD before report/ledger closure: `9acd3fe355448eccf307b834e18e18073e037f59`

## Summary

Task 283 added and verified a narrow read-only product surface for the durable
RawMaterial2CleanMaterial candidate created in Task 282. The material detail
page can now derive candidate metadata from material/task records, show the
candidate ObjectRef and provenance summary, and preview/open the candidate JSON
through the existing upload proxy path.

This does not accept final content quality and does not add an approval workflow,
runtime service, DB/MinIO mutation, batch behavior, readiness, UAT, L3, pressure
PASS, release readiness, production readiness, production online, or go-live.

## Changed Files

- `src/app/utils/rawMaterial2CleanMaterialCandidateView.ts`
- `src/app/components/RawMaterial2CleanMaterialCandidateCard.tsx`
- `src/app/pages/AssetDetailPage.tsx`
- `server/tests/rawmaterial2cleanmaterial-candidate-view-smoke.mjs`
- `TaskAndReport/2026-05-25T13-43-55+0800_P0-RawMaterial2CleanMaterial-Durable-Candidate-Product-Surface-ReadOnly-NoRuntimeNoDBWriteNoMinIOWrite_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

## Implementation Evidence

The new view helper derives a read-only candidate view from:

- `material.metadata.rawMaterial2CleanMaterial.currentCandidate`;
- `material.metadata.rawMaterial2CleanMaterial.candidates.v1`;
- `task.metadata.rawMaterial2CleanMaterialJobs["raw-material-2-clean-material"]`.

The card shows:

- service name, status, asset version, job id;
- candidate ObjectRef, SHA, size, and open URL;
- source `toc-rebuild v4` Clean Material identity;
- source input;
- section/block/sourceRef counts;
- candidate JSON preview;
- warning and conflict state.

The asset detail page renders the card immediately after the existing Clean
Material card.

## Canonical Read-Only Evidence

Canonical target:

```text
materialId = 1842780526581841
taskId = task-1779085089451
candidate = eduassets-clean/raw-material-2-clean-material/1842780526581841/v1/candidate.json
```

Live read-only verification:

```json
{
  "ok": true,
  "present": true,
  "status": "candidate",
  "assetVersion": "v1",
  "candidateProxyGet": 200,
  "sha256": "49a6189e12fe1c65ffdfbdf2e5b73d204c432002dff55812dc8c3be17ac2ce27",
  "size_bytes": 21767,
  "sectionCount": 73,
  "blockCount": 71,
  "conflict": null
}
```

Browser verification against local dev server:

```json
{
  "hasCard": true,
  "hasObject": true,
  "hasCandidateJson": true,
  "hasSha": true,
  "errors": [],
  "badResponses": []
}
```

Screenshot evidence path:

```text
/tmp/luceon-task283-product-surface.png
```

The browser run used a local Vite server with proxies pointed at the existing
`http://localhost:8081/__proxy/*` runtime. The first browser attempt using
default Vite proxy settings failed because local `8788/8789` were not exposed;
no mutation occurred.

## Commands And Exit Codes

All commands ran in `/Users/concm/Dev_workspace/Luceon2026` unless noted.

| Command | Exit |
| --- | ---: |
| `node server/tests/rawmaterial2cleanmaterial-candidate-view-smoke.mjs` | 0 |
| canonical live read-only verification script | 0 |
| `npx pnpm@10.4.1 exec tsc --noEmit` | 0 |
| `npx pnpm@10.4.1 run build` | 0 |
| `git diff --check origin/main...HEAD` | 0 |
| Playwright browser verification on `http://127.0.0.1:5175/cms/asset/1842780526581841` | 0 |

`vite build` emitted only the known chunk-size warning.

## Boundary Confirmation

No DB POST/PATCH/PUT/DELETE, MinIO put/copy/move/delete/list/bucket scan/cleanup,
runtime POST/service execution/job submission, Docker/Compose mutation,
upload/retry/reparse/Re-AI/rollback/batch, source/sample/env/secret/model
mutation, approval workflow, final quality acceptance, or readiness/go-live
claim occurred in this task.

## Residual Debt

- The candidate remains draft/skeletal output.
- No operator approval workflow exists for raw2clean candidate.
- No raw2clean runtime service exists.
- No multi-sample or batch discovery is validated.

## Recommended Next Mainline Step

Move one notch from visibility to operator decision: implement a minimal
mock-safe raw2clean candidate decision preview, scoped to `accept candidate` /
`needs repair` / `reject`, without DB writes first. Only after that should a
separate task authorize any durable decision apply.
