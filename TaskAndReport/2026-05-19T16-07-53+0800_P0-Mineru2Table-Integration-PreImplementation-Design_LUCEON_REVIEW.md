# P0 Mineru2Table Integration Pre-Implementation Design - Luceon Acceptance Review

- Task ID: `TASK-20260519-152658-P0-Mineru2Table-Integration-PreImplementation-Design`
- Reviewed at: `2026-05-19T16:07:53+0800`
- Reviewed by: `Luceon`
- Reviewed branch: `origin/lucode/task-221-mineru2table-design`
- Reviewed branch HEAD: `1b364c2b5f1c2677a40434ab1da900237b076fc6`
- Decision: `ACCEPTED_DESIGN_LEVEL_WITH_LUCEON_CLARIFICATIONS`

## 1. Judgment

Accepted at design level.

The resubmitted branch resolves the blocking points from the second Luceon review closely enough to become the implementation-control basis for the next mock-safe task. The branch stays inside `TaskAndReport/` and does not modify source code, runtime config, production services, DB, MinIO, Docker volumes, models, sample files, private role files, or the external Mineru2Table workspace.

This acceptance is not implementation acceptance, production validation, UAT, L3, release readiness, pressure PASS, or go-live approval. No real CleanServiceWorker startup, Mineru2Table dispatch, production deployment, data migration, upload, submit-probe, retry, reparse, re-AI, or RawMaterial2CleanMaterial implementation is accepted here.

## 2. Accepted Evidence

Luceon verified the submitted branch from `/Users/concm/prod_workspace/Luceon2026`.

Observed evidence:

- `origin/main` before merge: `b7ab250ecbf7dcb77a9fb78f7553a62a95c6c7c2`
- accepted branch HEAD: `1b364c2b5f1c2677a40434ab1da900237b076fc6`
- branch history is based on current `origin/main`;
- `git diff --check origin/main..HEAD` produced no output and exit code `0`;
- changed paths before Luceon acceptance remained limited to:

```text
A	TaskAndReport/2026-05-19T15-26-58+0800_P0-Mineru2Table-Integration-PreImplementation-Design_DESIGN.md
A	TaskAndReport/2026-05-19T15-26-58+0800_P0-Mineru2Table-Integration-PreImplementation-Design_REPORT.md
M	TaskAndReport/TASK_TRACKING_LIST.md
```

## 3. Resolved Findings

The revised design/report now satisfy the Task 221 design-level gate:

- F1: report separates a design baseline commit from the final remote branch authority, avoiding the recursive final-commit-hash problem;
- F2: the task ledger is actually updated to `Ready for luceon Review / Next Actor=Luceon`, and `TASK_TRACKING_LIST.md` appears in the branch path audit;
- F3: webhook HMAC is correctly represented as HTTP headers plus raw-body verification before any DB mutation;
- F4: storage wording uses the current DB/API task/material metadata abstraction instead of unauthorized PostgreSQL-specific language;
- F5: persisted metadata summaries are expanded to include bounded identity, input/sink ObjectRefs, version, status, timestamps, errors, provenance, and output refs while keeping large artifacts in MinIO.

## 4. Luceon Clarifications For Implementation

These clarifications are part of the acceptance boundary for all follow-up implementation tasks:

1. The actual accepted Task 221 branch anchor is `1b364c2b5f1c2677a40434ab1da900237b076fc6`, regardless of the report's self-referential final HEAD wording.
2. Future implementation must follow the expanded bounded metadata summaries in the revised design. Do not implement the stale sentence that says only `jobId` and state are synced.
3. Task A must treat canonical Raw Material evidence as a strict prerequisite. Legacy `eduassets-parsed` evidence such as `artifactManifestObjectName`, `markdownObjectName`, or `parsedPrefix` must not be silently converted into canonical `eduassets-raw` provenance.
4. The accepted safe behavior for legacy parsed-only assets in Task A is `skipped-policy` / `not-applicable` at classification level. No existing asset reparse, migration, backfill, deletion, or pseudo-provenance creation is authorized.
5. Asset version allocation for Task A is Luceon-owned: use monotonic `vN` semantics, preserve existing active job identity for idempotency, and allocate the next clean version only from bounded metadata evidence.
6. Task 219 remains a separate open P0 item and must not be modified, closed, or folded into CleanService work.

## 5. Next Authorization

Task 222 is issued for Task A only: mock-safe CleanService Raw Material canonical adapter and assetVersion allocator.

Real HTTP transport, webhook route registration, output verification hardening, UI read surface, external Mineru2Table protocol changes, production deployment, and real dispatch remain blocked until separately tasked and accepted.
