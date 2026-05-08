# P0 MinIO Console Local-Only Production Override Implementation

Task:
P0 MinIO Console Local-Only Production Override Implementation

Task ID:
`TASK-20260508-134708-P0-MinIO-Console-Local-Only-Production-Override-Implementation`

Assignee:
Lucode

Issued by:
Lucia

Issued at:
2026-05-08T13:47:08+0800

Project:
Luceon2026

Development workspace:
`/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`

Production deployment path:
`/Users/concm/prod_workspace/Luceon2026`

GitHub:
`https://github.com/shcming2023/Luceon2026`

TaskAndReport record:
`TaskAndReport/2026-05-08T13-47-08+0800_P0-MinIO-Console-Local-Only-Production-Override-Implementation_TASK.md`

## Required Reading Before Execution

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/lucode.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/codex/TEST_POLICY.md`
- `docs/deploy/DEPLOY.md`
- `TaskAndReport/2026-05-08T12-52-45+0800_P0-MinIO-Console-Local-Only-Implementation-Authorization_DECISION.md`
- `TaskAndReport/2026-05-08T13-47-08+0800_P0-MinIO-Console-Local-Only-Implementation-Authorization_LUCIA_REVIEW.md`
- `TaskAndReport/2026-05-08T12-43-08+0800_P0-MinIO-Console-Local-Only-Binding-Change-Plan_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

## Background

Director approved a scoped production-local override implementation. The purpose is to reduce the MinIO console exposure boundary before release-candidate naming by binding the console only to loopback.

The accepted plan is:

```yaml
- "19001:9001"
```

to:

```yaml
- "127.0.0.1:19001:9001"
```

Strict AI/model configuration must remain unchanged:

```yaml
- DISABLE_AI_SKELETON_FALLBACK=true
- OLLAMA_TIER2_MODEL=qwen3.5:9b
```

## Objective

Apply and validate the scoped production-local override change.

## Authorized Production File

Only this production file may be edited:

`/Users/concm/prod_workspace/Luceon2026/docker-compose.override.yml`

Allowed edit:

- Replace the MinIO console mapping string `"19001:9001"` with `"127.0.0.1:19001:9001"`.

Forbidden edits:

- Any change to strict AI/model settings.
- Any change to MinIO API port, buckets, objects, credentials, data paths, Docker volumes, DB configuration, task state, artifacts, or secrets.
- Any unrelated production override line.

## Authorized Runtime Operations

Lucode may run the minimum necessary Docker/Compose operations to apply and verify this binding only.

Allowed operation categories:

- Inspect effective compose configuration or container port mapping.
- Recreate or restart only the service required to apply the MinIO console binding if Compose requires it.
- Inspect listeners and reachability.
- Run non-destructive health checks.

Forbidden operations:

- `docker compose down -v`
- Docker volume deletion or pruning.
- DB/MinIO data deletion, migration, repair, or rewrite.
- Production application rebuild unrelated to this binding.
- Broad deployment, rollback, or sync outside this task.
- Secret changes.
- Release-readiness declaration.

## Required Checks And Evidence

Before change:

- `git status --short --branch` in development workspace.
- `git fetch origin` in development workspace.
- If development `main` is behind `origin/main` and clean, `git pull --ff-only origin main`.
- `git status --short --branch` in production workspace.
- `git log -1 --oneline` in production workspace.
- Read and record production override before-change content for relevant lines.
- Confirm whether active parse/AI work is running if a restart/recreate is required.

Implementation:

- Apply only the authorized one-line mapping change.
- Preserve strict AI/model settings unchanged.
- Record exact command used to apply or verify the effective binding.

Validation:

- Confirm `http://127.0.0.1:19001` is reachable from the production host.
- Confirm `http://localhost:19001` behavior from the production host.
- Confirm port `19001` is not listening on wildcard, LAN, or non-local interfaces.
- Confirm CMS remains reachable at the production manual-review URL.
- Confirm dependency-health remains acceptable for the current runtime boundary.
- Confirm strict AI/model settings remain present in effective configuration or production override.
- Confirm no DB, MinIO object, Docker volume, task, artifact, or secret mutation occurred.

Rollback evidence:

- Provide exact rollback line from `"127.0.0.1:19001:9001"` back to `"19001:9001"`.
- Provide the minimum command category needed to re-apply rollback if Director later authorizes it.
- Do not perform rollback unless the scoped implementation fails and rollback is required to restore the prior operational boundary.

## Allowed Repository Files

- One `TaskAndReport/*_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

Do not edit application code or docs unless blocked and the report explains why. The expected repository output is a report and task-list update.

## Completion Report Requirements

Write report to:

`TaskAndReport/YYYY-MM-DDTHH-MM-SS+0800_P0-MinIO-Console-Local-Only-Production-Override-Implementation_REPORT.md`

The report must include:

- Production file changed.
- Before and after mapping.
- Confirmation strict AI/model settings stayed unchanged.
- Commands run with exit codes.
- Validation results.
- Any restart/recreate performed and the exact service scope.
- Confirmation that forbidden data/secret/volume/task/artifact mutations did not occur.
- Rollback instructions.
- Final production workspace status.
- Final development workspace status.
- Production release readiness remains unclaimed.

Update `TaskAndReport/TASK_TRACKING_LIST.md` with:

- Status `已回报待审`
- `Next Actor=Lucia`
- Report path
- Branch/HEAD
- Summary notes

Commit and push the report/task-list update to GitHub `main`.

## Acceptance Criteria

- MinIO console binding is changed to local-only.
- Strict AI/model settings remain unchanged.
- Local console access works from the production host.
- Non-local exposure is not present for port `19001`.
- CMS and dependency-health checks remain acceptable.
- No forbidden production data/secret/volume/task/artifact mutation occurred.
- Production release readiness remains unclaimed.
