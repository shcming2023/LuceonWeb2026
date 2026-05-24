# P0 Lucode Branch Handoff CheckTask Correction Decision

- Timestamp: 2026-05-24T11:02:07+0800
- Decision owner: User
- Recorded by: Luceon

## Problem

The first local dual-thread trial showed a handoff gap:

- Lucode correctly pushed a task branch with a branch-local report and task-ledger handoff.
- `origin/main` still showed the task as `Next Actor=Lucode`.
- Luceon's `check task` only read `origin/main`, so it reported no Luceon task and did not inspect the pushed Lucode branch.

## Decision

Keep GitHub `main` plus `TaskAndReport/` as the shared control plane, but make Lucode branch handoff an explicit part of `check task`.

When `origin/main` has no open `Next Actor=Luceon` row, Luceon must inspect the earliest open `Next Actor=Lucode` row for a matching remote `lucode/<task-id-or-short-slug>` branch.

If that remote branch's task row says `Lucode 已回报待 Luceon 审查` or `Next Actor=Luceon`, Luceon treats the branch as a pending review even though main still says Lucode.

Branch review should inspect the branch's own changes with merge-base / three-dot diff syntax, such as `git diff --name-status origin/main...origin/<branch>`. Two-dot `origin/main..origin/<branch>` is unsafe after main advances beyond the Lucode branch.

## Lucode Requirements

Lucode must:

- push the remote `lucode/<task-id-or-short-slug>` branch;
- record the exact pushed branch and full HEAD in the report and final reply;
- use merge-base / three-dot diff evidence unless the branch is confirmed current with `origin/main`;
- update the branch-local ledger row to `Status=Lucode 已回报待 Luceon 审查`, `Next Actor=Luceon`;
- not expect branch-local ledger updates to appear on `origin/main` before Luceon review.

## Safety Boundary

This correction does not authorize production mutation, runtime rerun, DB/MinIO/Docker/model/secret/sample mutation, automatic heartbeat, direct main push by Lucode, or readiness/go-live claims.
