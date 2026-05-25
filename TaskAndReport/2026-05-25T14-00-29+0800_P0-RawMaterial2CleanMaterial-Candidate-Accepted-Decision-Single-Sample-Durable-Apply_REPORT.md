# P0 RawMaterial2CleanMaterial Candidate Accepted Decision Single Sample Durable Apply Report

Task ID: `TASK-20260525-135405-P0-RawMaterial2CleanMaterial-Candidate-Accepted-Decision-Single-Sample-Durable-Apply`

Report time: 2026-05-25T14:00:29+0800

Status: `SUCCESS_SINGLE_SAMPLE_ACCEPTED_DECISION_APPLIED`

Implementation branch: `codex/TASK-20260525-135405-accepted-decision`

Implementation HEAD: `e53175b85002d2593d76be1353f169f7d83f9711`

## Summary

The canonical RawMaterial2CleanMaterial durable candidate now has a durable
single-sample `accepted` decision in task and material metadata.

This crosses the intended narrow phase boundary: the candidate is no longer
only inspectable; it can be read back as an operator-accepted product asset
candidate. This is not final CleanMaterial quality acceptance or readiness.

## Changed Files

- `server/services/rawmaterial2cleanmaterial/candidate-decision.mjs`
- `server/tests/rawmaterial2cleanmaterial-candidate-decision-smoke.mjs`
- `server/tests/rawmaterial2cleanmaterial-candidate-decision-apply.mjs`
- `server/tests/rawmaterial2cleanmaterial-candidate-view-smoke.mjs`
- `src/app/utils/rawMaterial2CleanMaterialCandidateView.ts`
- `src/app/components/RawMaterial2CleanMaterialCandidateCard.tsx`

## Durable Decision Shape

The metadata decision is lightweight and scoped:

- `state`: `accepted`
- `decision`: `accepted`
- `decidedBy`: `Luceon`
- `scope`: `single-sample-durable-boundary`
- `materialId`: `1842780526581841`
- `taskId`: `task-1779085089451`
- `serviceName`: `raw-material-2-clean-material`
- `assetVersion`: `v1`
- `jobId`: `luceon-task-1779085089451-raw2clean-v1`
- `candidate.sha256`:
  `49a6189e12fe1c65ffdfbdf2e5b73d204c432002dff55812dc8c3be17ac2ce27`

Boundary fields explicitly keep:

- `finalQualityAccepted: false`
- `runtimePost: false`
- `serviceExecution: false`
- `minioMutation: false`
- `batch: false`
- `readinessClaimed: false`

No full candidate JSON, sections, blocks, or raw content are embedded in DB
metadata.

## Pre-Apply Evidence

The apply script first reloaded the canonical task and material through:

- `GET /__proxy/db/tasks/task-1779085089451`
- `GET /__proxy/db/materials/1842780526581841`

It then read the existing candidate artifact through:

```json
{
  "bucket": "eduassets-clean",
  "object": "raw-material-2-clean-material/1842780526581841/v1/candidate.json",
  "sha256": "49a6189e12fe1c65ffdfbdf2e5b73d204c432002dff55812dc8c3be17ac2ce27",
  "size_bytes": 21767
}
```

Artifact proxy read-back returned 200 and matched the expected SHA and size.

## Real Apply Evidence

Command:

```bash
RAW2CLEAN_DECISION_REAL_APPLY=1 node server/tests/rawmaterial2cleanmaterial-candidate-decision-apply.mjs
```

Exit code: 0

Real operation count:

```json
{
  "dbPatch": 2,
  "minioPutObject": 0,
  "minioDelete": 0,
  "minioList": 0,
  "runtimePost": 0,
  "dockerOperation": 0
}
```

Affected DB IDs:

- `tasks/task-1779085089451`
- `materials/1842780526581841`

Post-apply read-back confirmed:

- task raw2clean status: `accepted`
- task raw2clean cleanState: `accepted-candidate`
- task decision state: `accepted`
- material currentCandidate status: `accepted`
- material currentCandidate cleanState: `accepted-candidate`
- material currentCandidate decision state: `accepted`
- material candidates.v1 decision state: `accepted`
- material currentDecision state: `accepted`
- decision candidate SHA:
  `49a6189e12fe1c65ffdfbdf2e5b73d204c432002dff55812dc8c3be17ac2ce27`

## Product Surface Evidence

Local dev server was started with read proxies:

```bash
DB_PROXY_TARGET=http://localhost:8081/__proxy/db \
UPLOAD_PROXY_TARGET=http://localhost:8081/__proxy/upload \
npx pnpm@10.4.1 dev --host 127.0.0.1 --port 5176
```

Browser verification target:

```text
http://127.0.0.1:5176/cms/asset/1842780526581841
```

Verification result:

```json
{
  "hasCard": true,
  "hasDecision": true,
  "hasFinalQualityBoundary": true,
  "hasSha": true,
  "hasCandidateJson": true,
  "errors": [],
  "badResponses": [],
  "screenshotPath": "/tmp/luceon-task284-accepted-decision-product-surface.png"
}
```

The page displays:

- `Decision: accepted`
- `FINAL QUALITY ACCEPTED false`
- candidate ObjectRef;
- candidate SHA;
- candidate JSON preview.

## Checks

| Check | Exit |
| --- | ---: |
| `node server/tests/rawmaterial2cleanmaterial-candidate-decision-smoke.mjs` | 0 |
| `node server/tests/rawmaterial2cleanmaterial-candidate-view-smoke.mjs` | 0 |
| `node server/tests/rawmaterial2cleanmaterial-candidate-decision-apply.mjs` | 0 |
| `npx pnpm@10.4.1 exec tsc --noEmit` | 0 |
| `npx pnpm@10.4.1 run build` | 0 |
| `git diff --check` | 0 |
| Playwright product-surface verification | 0 |

Build emitted only the existing Vite chunk-size warning.

## Boundary Confirmation

No MinIO put/copy/move/delete/list/bucket scan/cleanup was performed. No
runtime POST, service execution, Docker/Compose rebuild/restart/recreate, batch
processing, source/sample/env/secret/model mutation, final quality acceptance,
readiness, UAT, L3, pressure PASS, release readiness, production readiness,
production online, or go-live claim was made.

The only real data mutation was exactly two DB PATCHes against the authorized
task and material.

## Residual Debt

- Candidate content is still skeletal and not final quality accepted.
- No repair/reject durable decision path exists yet.
- No full approval workflow exists.
- No runtime raw2clean service/worker exists.
- No multi-sample or batch decision path is validated.
- Metadata shape may need consolidation after the mainline stabilizes.

## Recommended Next Mainline Step

Do not broaden into cleanup or schema governance yet. The next mainline step
should be a second canonical-sample pilot or a minimal runtime entrypoint
decision, depending on whether the Director wants to prove repeatability first
or start turning the closed loop into an executable service boundary.
