# TASK-20260524-171454-P0-CleanMaterial-Operator-Decision-Semantics-Planning-NoRuntime

Issued at: 2026-05-24T17:14:54+0800

Actor: Lucode

## Mainline Objective

Define the minimum operator decision semantics needed after Clean Material
artifact inspection.

The current mainline has reached:

```text
toc-rebuild v4 durable metadata
=> product-visible Clean Material summary
=> read-only artifact inspection
=> operator must decide whether this Clean Material can feed the next stage
```

This task should produce a narrow planning artifact only. It must not implement
business code, write DB state, run runtime jobs, or grow into an approval system.

## Critical Path Scope

Plan the smallest durable decision model for one Clean Material version.

The plan must answer:

1. What are the minimum decision states?
2. Where should the decision be represented in task/material metadata later?
3. What is the minimum UI behavior for a future implementation task?
4. What evidence must be recorded when an operator makes a decision?
5. Which transitions are allowed and which are forbidden?
6. What must remain deferred until after this stage?
7. What should the next implementation task brief include and forbid?

Use these candidate states as the starting point, but refine or reject them if
the repo evidence suggests a better minimal model:

```text
pending-review
accepted
needs-repair
rejected
superseded
```

The planning must explicitly distinguish:

- CleanService execution status, such as `completed` or `failed`;
- artifact inspection/readability status;
- operator decision status;
- later RawMaterial2CleanMaterial or downstream cleaning status.

Do not collapse these into one field.

## Current Evidence Anchors

Use current `main` and these accepted milestones:

- Task 267: durable `toc-rebuild v4` metadata applied for the canonical sample.
- Task 268: minimal Clean Material summary is product-visible.
- Task 269: accepted Clean Material artifacts are read-only inspectable.

Canonical sample:

```text
materialId = 1842780526581841
taskId = task-1779085089451
serviceName = toc-rebuild
assetVersion = v4
jobId = luceon-task-1779085089451-toc-rebuild-v4
```

## Allowed Files

Allowed files:

- a planning artifact under `TaskAndReport/`, preferably:
  `TaskAndReport/2026-05-24T17-14-54+0800_P0-CleanMaterial-Operator-Decision-Semantics-Planning-NoRuntime_DESIGN.md`
- the required Lucode report under `TaskAndReport/`;
- branch-local update to `TaskAndReport/TASK_TRACKING_LIST.md`.

Lucode may read source files and prior TaskAndReport evidence as needed, but
must not edit source code, runtime code, PRD docs, deployment files, or local
private role files in this planning task.

## Forbidden Operations

Forbidden:

- any business-code implementation;
- edits under `src/`, `server/`, `scripts/`, `uat/`, package files, Docker files,
  PRD docs, or runtime config;
- DB `POST` / `PATCH` / `PUT` / `DELETE`;
- MinIO put/copy/move/delete/write/delete-marker/cleanup;
- CleanService runtime run;
- Mineru2Table POST, submit-probe, live job query, or alternate endpoint probe;
- Docker/Compose restart/recreate/build/down/up/volume/prune/network mutation;
- job-store edit/delete/cleanup/reset;
- upload, retry, reparse, Re-AI, repair, rollback, batch, or pressure test;
- production deployment or production runtime validation;
- model, env, secret, sample, source asset, or local override mutation;
- implementation of approve/reject buttons, DB schema, state machine, workflow,
  RawMaterial2CleanMaterial, or scheduler/worker behavior;
- UAT, L3, pressure PASS, production readiness, release readiness, production
  online, or go-live claims.

## Required Planning Content

The design artifact must include:

1. **State Model**
   - state names;
   - meaning of each state;
   - terminal vs non-terminal classification;
   - which state is the default for existing inspected v4 metadata.

2. **Metadata Shape Proposal**
   - proposed minimal metadata fields;
   - whether fields belong under material clean metadata, task clean metadata, or
     both;
   - exact example JSON for the canonical `toc-rebuild v4` sample;
   - explicit note that this task does not write the example to DB.

3. **Transition Rules**
   - allowed transitions;
   - forbidden transitions;
   - what happens when a newer asset version supersedes an older accepted or
     rejected version;
   - how `needs-repair` differs from `rejected`.

4. **Evidence Requirements**
   - required operator identity/timestamp fields;
   - required artifact refs or artifact snapshot fields;
   - required reason/note fields for negative decisions;
   - whether content hashes must be included or can reference existing refs.

5. **Product Behavior Boundary**
   - minimal UI behavior for a future implementation;
   - empty-state/read-only-state behavior;
   - forbidden UI behavior that would create a broad approval system.

6. **Next Implementation Task Boundary**
   - proposed next task name;
   - allowed files;
   - forbidden operations;
   - acceptance criteria;
   - checks.

7. **Deferred Items**
   - RawMaterial2CleanMaterial;
   - batch decisions;
   - multi-user permission/governance;
   - audit export/reporting;
   - production validation/readiness.

## Stop Rule

Stop and write a blocked report if a useful planning answer appears to require:

- live DB inspection beyond existing TaskAndReport evidence;
- runtime POST/query/probe;
- schema migration;
- broad workflow design;
- implementation before Director/Luceon approval.

## Acceptance Boundary

Luceon can accept this task if it provides a narrow, implementable operator
decision model and a next implementation-task boundary.

Acceptance of this planning task does not accept:

- any DB metadata mutation;
- any UI implementation;
- any operator decision workflow;
- RawMaterial2CleanMaterial;
- production validation;
- readiness/go-live.

## Required Checks

At minimum:

```bash
git diff --check origin/main...HEAD
```

If Lucode edits only Markdown/ledger files, no TypeScript/build check is
required. If any non-TaskAndReport file is changed, that is a scope problem and
must be explained or reverted before handoff.

## Required Report

Write:

```text
TaskAndReport/2026-05-24T17-14-54+0800_P0-CleanMaterial-Operator-Decision-Semantics-Planning-NoRuntime_REPORT.md
```

The report must include:

- task id and task brief path;
- exact remote branch and full HEAD;
- files changed;
- planning summary;
- commands run with exit codes;
- skipped checks and exact reasons;
- risks, blockers, and residual debt;
- explicit boundary statement confirming no source-code edits, no DB write, no
  runtime, no MinIO write/delete, no Docker/production operation, and no
  readiness/go-live claim;
- whether Luceon review is required.

## Handoff

After completion, update the branch-local ledger row to:

```text
Status = Lucode 已回报待 Luceon 审查
Next Actor = Luceon
```

Push a remote branch named like:

```text
lucode/TASK-20260524-171454-P0-CleanMaterial-Operator-Decision-Semantics-Planning-NoRuntime
```

Do not merge to `main`.
