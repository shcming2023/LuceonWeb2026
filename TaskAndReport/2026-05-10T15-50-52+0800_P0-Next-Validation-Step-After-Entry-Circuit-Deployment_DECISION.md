# Director Decision Required: P0 Next Validation Step After Entry Circuit Deployment

- Decision ID: `TASK-20260510-155052-P0-Next-Validation-Step-After-Entry-Circuit-Deployment`
- Created At: `2026-05-10T15:50:52+0800`
- Created By: Lucia
- Status: 完成关闭
- Next Actor: -
- Basis: Task 73 accepted as deployed and non-destructive runtime surfaces pass.

## Decision Needed

The durable MinerU admission circuit is now deployed in production, and non-destructive runtime evidence shows:

- dependency-health with `mineruSubmitProbe=true` is non-blocking;
- MinerU submit probe returns HTTP `202`;
- admission circuit is closed;
- active parse/AI queues are empty;
- Ollama `qwen3.5:9b` is resident.

Director must decide the next validation step.

## Director Decision

At `2026-05-10T15:54:51+0800`, Director selected `Option B`.

Lucia interprets this as authorization for one bounded restart of the previously failed 24-PDF pressure-validation track under the deployed durable admission circuit and explicit stop rules.

This decision authorizes exactly one controlled pressure-validation run with a maximum of 24 PDFs from the same pressure-validation set. If Lucode cannot identify the same 24-PDF set from the previous pressure-validation evidence, Lucode must stop and report blocked instead of substituting other samples.

This decision still does not authorize production release readiness, failed-task repair, data cleanup, destructive operations, broad restart/rollback, secret/model/config/override mutation, or sample-library mutation.

## Options

### Option A: Controlled Validation Upload

Authorize one small controlled validation upload from the read-only external sample library, with the durable admission circuit and stage-queued heavy-stage limits active.

This option must still forbid pressure testing, failed-task repair, data deletion, secret/model/config/override mutation, and release-readiness declaration.

### Option B: Controlled Pressure-Test Restart

Authorize a bounded restart of the previously failed 24-PDF pressure-validation track under the new admission circuit and explicit stop rules.

This option must define exact sample count, stop conditions, and what constitutes pass/fail before Lucia issues a Lucode task.

### Option C: Hold

Keep validation paused and request more read-only observability or planning.

## Lucia Recommendation

Lucia recommends Option A before any 24-PDF pressure restart.

Reason: the admission circuit is newly deployed and should first be validated on a small controlled upload path before reopening a larger pressure run. This reduces blast radius while checking that intake admission, MinerU submit, parsed artifact flow, and AI metadata handoff remain coherent under the new runtime contract.

## Forbidden Without Separate Approval

- Production release-readiness declaration;
- broad pressure testing without a bounded task brief;
- failed-task repair, retry, closure, deletion, or cleanup;
- DB row deletion, MinIO object deletion, Docker volume deletion/pruning;
- secret/model/timeout/config/override mutation;
- broad stack restart, rollback, or unrelated recovery;
- sample-library mutation, sync, copy into repo, deletion, rename, or pollution;
- skeleton fallback or silent degradation.

## Autonomy Rule

Director has answered. Lucia issued `TASK-20260510-155451-P0-Bounded-24-PDF-Pressure-Restart-Under-Entry-Circuit` to Lucode.
