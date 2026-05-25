# P0 RawMaterial2CleanMaterial Candidate Accepted Decision Single Sample Durable Apply

Task ID: `TASK-20260525-135405-P0-RawMaterial2CleanMaterial-Candidate-Accepted-Decision-Single-Sample-Durable-Apply`

Created: 2026-05-25T13:54:05+0800

Owner: Luceon

Status: Open

## Mainline Objective

Cross the next narrow phase boundary for the canonical RawMaterial2CleanMaterial
sample: move from a durable and inspectable candidate to a durable accepted
candidate decision.

The mainline question is whether a single raw2clean candidate can be:

1. rediscovered from task/material metadata;
2. verified against its exact candidate artifact ObjectRef and SHA;
3. marked as accepted in durable task/material metadata;
4. read back and shown on the product surface.

## Critical Path Scope

Target only:

- material: `1842780526581841`
- parse task: `task-1779085089451`
- service: `raw-material-2-clean-material`
- asset version: `v1`
- candidate object:
  `eduassets-clean/raw-material-2-clean-material/1842780526581841/v1/candidate.json`
- candidate SHA:
  `49a6189e12fe1c65ffdfbdf2e5b73d204c432002dff55812dc8c3be17ac2ce27`

Allowed implementation:

- add a narrow metadata decision helper;
- add focused smoke coverage for decision-plan shape and safety gates;
- update the existing read-only candidate product card to show the decision
  state;
- perform exactly one real accepted decision apply for the canonical sample.

Allowed runtime data mutation:

- `PATCH /tasks/task-1779085089451`
- `PATCH /materials/1842780526581841`

The metadata patch may add only lightweight decision/audit fields under the
existing `rawMaterial2CleanMaterial` metadata area. It must not embed full
candidate JSON, sections, blocks, or raw content.

## True Preconditions

- The candidate must already be present in both task and material metadata.
- The candidate artifact must be read through the existing upload proxy.
- The artifact body SHA and size must match the metadata before any DB PATCH.
- Existing task/material candidate refs must match each other.
- The decision must be scoped to `accepted` for this one canonical sample.

## Deferrable Side Work

- full approval workflow;
- multi-status UI with operator forms;
- reject/repair durable apply;
- runtime service or worker;
- batch/multi-sample decision;
- metadata schema consolidation;
- final CleanMaterial quality acceptance.

## Fast Validation Target

The task is successful only if:

- focused smoke tests pass;
- TypeScript and build pass;
- pre-apply artifact read-back matches the expected ObjectRef/SHA/size;
- real apply performs exactly two DB PATCHes and zero MinIO writes;
- post-apply material and task metadata both show an accepted raw2clean
  candidate decision tied to the same candidate ObjectRef/SHA;
- local product-surface verification shows the accepted decision for
  `/cms/asset/1842780526581841`.

## Stop Rule

Stop and report blocked instead of widening scope if:

- the candidate ObjectRef is missing or mismatched;
- the artifact proxy GET does not return 200;
- the artifact SHA or size differs from metadata;
- task and material candidate refs disagree;
- the required DB PATCH would affect any other material or task;
- the patch would embed full candidate content;
- validation requires MinIO mutation, runtime POST, Docker mutation, or batch
  behavior.

## Review Boundary

Acceptance of this task means only:

- the canonical sample has a durable raw2clean accepted candidate decision;
- the decision can be read back from metadata;
- the product surface can display the decision.

It does not mean final CleanMaterial quality acceptance, UAT, L3, pressure PASS,
release readiness, production readiness, production online, or go-live.

## Forbidden Operations

- MinIO put/copy/move/delete/list/bucket scan/cleanup;
- runtime POST or service execution;
- Docker/Compose rebuild/restart/recreate;
- DB writes outside the one task and one material above;
- source/sample/env/secret/model mutation;
- batch processing;
- final quality certification;
- readiness/go-live claims.

## Required Report

Write a report under `TaskAndReport/` with:

- implementation summary;
- exact changed files;
- pre-apply candidate ObjectRef/SHA/size evidence;
- exact DB PATCH count and affected IDs;
- post-apply read-back evidence;
- product-surface evidence;
- checks and exit codes;
- residual debt and next mainline recommendation.
