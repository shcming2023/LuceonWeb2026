# TASK-20260524-214126-P0-CleanMaterial-Operator-Decision-Accepted-Single-Sample-Material-Patch-Apply-OnePatch-NoRuntime-NoMinIOWrite

Issued at: 2026-05-24T21:41:26+0800

Actor: Luceon

## Mainline Objective

Complete the current Clean Material stage breakthrough by durably recording a
single-sample operator decision:

```text
toc-rebuild v4 Clean Material -> operatorDecision.state = accepted
```

The goal is not to improve the UI, broaden workflow semantics, or implement a
production approval system. The goal is to close the current phase loop for the
canonical sample so Clean Material becomes a durable human-gated product object.

## Critical Path Scope

Apply exactly one material metadata patch for the canonical sample:

```text
materialId = 1842780526581841
taskId = task-1779085089451
serviceName = toc-rebuild
assetVersion = v4
jobId = luceon-task-1779085089451-toc-rebuild-v4
```

Allowed operation:

```text
PATCH /__proxy/db/materials/1842780526581841
```

The patch may update only:

```text
material.metadata.cleanMaterials.toc-rebuild.operatorDecision
```

It must preserve existing material metadata, sibling metadata branches, sibling
Clean Material services, and existing `toc-rebuild` summary fields.

## True Preconditions

Before patching, Luceon must confirm with read-only GETs:

- material exists;
- task exists;
- material and task both point to `toc-rebuild v4`;
- job id is `luceon-task-1779085089451-toc-rebuild-v4`;
- artifact refs are present;
- sourceInput object/hash/size remain present;
- no non-pending operator decision is already persisted for this service.

## Patch Shape

The accepted decision must be shaped like:

```json
{
  "state": "accepted",
  "decidedAt": "<ISO timestamp>",
  "decidedBy": "local-operator",
  "reason": null,
  "note": "Luceon-authorized single-sample accepted decision for toc-rebuild v4 stage breakthrough.",
  "artifactSnapshot": {
    "assetVersion": "v4",
    "jobId": "luceon-task-1779085089451-toc-rebuild-v4",
    "provenanceObjectName": "toc-rebuild/1842780526581841/v4/provenance.json",
    "sourceInput": "<existing sourceInput object>",
    "artifactRefs": "<existing artifact refs>",
    "tokensTotal": "<existing token total when available>",
    "unresolvedAnchorCount": "<existing unresolved anchor count when available>"
  },
  "supersededBy": null,
  "updatedAt": "<same ISO timestamp>"
}
```

## Forbidden Operations

Forbidden:

- any task metadata PATCH or task write;
- DB POST/PUT/DELETE;
- more than one material PATCH;
- CleanService runtime run;
- Mineru2Table POST/query/probe;
- MinIO put/copy/move/delete/write/delete-marker/cleanup;
- Docker/Compose restart/recreate/build/down/up/volume/prune/network mutation;
- job-store edit/delete/cleanup/reset;
- upload, retry, reparse, Re-AI, repair, rollback, batch, pressure test;
- model, env, secret, sample, source asset, or local override mutation;
- production deployment or production runtime validation;
- broad approval workflow, task metadata mirroring, RawMaterial2CleanMaterial,
  audit export, batch decisions, or permissions/governance work;
- UAT, L3, pressure PASS, release readiness, production readiness, production
  online, or go-live claims.

## Fast Validation Target

After the exactly-one material PATCH, Luceon must perform read-only GETs and
confirm:

- material `operatorDecision.state = accepted`;
- `decidedBy`, `decidedAt`, `updatedAt`, and `artifactSnapshot` are present;
- existing `latestVersion`, `status`, `jobId`, `provenanceObjectName`,
  `sourceInput`, `stats`, and `warnings` are preserved;
- sibling metadata branches are preserved;
- task metadata is unchanged for operator decision purposes;
- no runtime, MinIO, Docker, or task write occurred.

## Stop Rule

Stop and report blocked without patching if:

- material/task GET fails;
- current metadata is not aligned on `toc-rebuild v4`;
- artifact refs or sourceInput are missing;
- a non-pending operator decision already exists;
- preserving existing metadata would require a broader mutation;
- the apply would require a task write, runtime, MinIO, Docker, or second DB
  write.

## Acceptance Boundary

Acceptance of this task means only:

```text
canonical sample toc-rebuild v4 material operatorDecision accepted was durably persisted by exactly one material PATCH
```

It does not mean production readiness, L3, UAT, pressure PASS, release
readiness, go-live, RawMaterial2CleanMaterial readiness, batch readiness, or
general approval workflow acceptance.

## Required Report

Write:

```text
TaskAndReport/2026-05-24T21-41-26+0800_P0-CleanMaterial-Operator-Decision-Accepted-Single-Sample-Material-Patch-Apply-OnePatch-NoRuntime-NoMinIOWrite_REPORT.md
```

The report must include:

- task id and task brief path;
- base `main` HEAD;
- preflight GET summary;
- exact patch boundary;
- PATCH count and endpoint;
- post-read verification;
- explicit non-operations statement;
- risks and residual debt;
- final decision.
