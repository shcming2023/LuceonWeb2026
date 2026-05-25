# Unified Owner Workflow Change Decision

Decision time: 2026-05-25T12:45:43+0800

## User Direction

The user canceled the separate collaboration-role model and assigned unified
project responsibility to Luceon because the project is near closeout and the
remaining work is primarily convergence, testing, and acceptance.

Luceon now owns:

- planning;
- requirements;
- architecture;
- product decisions within user-approved scope;
- code implementation;
- tests and validation;
- acceptance and closure.

The separate Lucode role is no longer used for new work.

## Workspace Boundary

The workspace split remains strict:

- Development workspace: `/Users/concm/Dev_workspace/Luceon2026`
- Production/control/deployment workspace: `/Users/concm/prod_workspace/Luceon2026`
- GitHub repository: `https://github.com/shcming2023/Luceon2026`

Business code implementation should happen in the development workspace. The
production/control workspace remains the source for control-plane truth,
acceptance, mainline closure, and explicitly authorized deployment/runtime
operations.

## Control-Plane Changes

- New task rows must use `Next Actor=Luceon`, `User`, or `None`.
- `Next Actor=Lucode` is retired for new active rows.
- `docs/codex/LUCODE_LOCAL_WORKFLOW.md` is retained as a retired historical
  workflow record only.
- `check task` no longer performs Lucode branch handoff polling for new work.
- Current Task 280 is reassigned from the retired Lucode model to Luceon direct
  execution.

## Safety Boundary

This workflow change does not authorize production deployment, runtime restart,
runtime POST, submit-probe, upload, DB mutation, MinIO mutation/list/delete,
Docker volume mutation, model/secret/sample mutation, cloud-server operation,
pressure testing, UAT/L3/readiness/go-live claims, or other destructive
operations.

Those actions still require explicit user authorization or a task/decision file
that grants the exact operation.
