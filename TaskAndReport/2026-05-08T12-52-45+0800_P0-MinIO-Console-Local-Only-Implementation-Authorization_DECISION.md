# P0 MinIO Console Local-Only Implementation Authorization

Decision ID:
`TASK-20260508-125245-P0-MinIO-Console-Local-Only-Implementation-Authorization`

Issued by:
Lucia

Issued at:
2026-05-08T12:52:45+0800

Next Actor:
Director

## Background

Director selected the release-boundary direction in task 24: MinIO console exposure must be narrowed to local-only binding before release-candidate naming. Lucode then completed task 25 with a non-destructive plan.

The accepted plan proposes changing production-local override mapping from:

```yaml
- "19001:9001"
```

to:

```yaml
- "127.0.0.1:19001:9001"
```

Strict AI/model settings remain unchanged:

```yaml
- DISABLE_AI_SKELETON_FALLBACK=true
- OLLAMA_TIER2_MODEL=qwen3.5:9b
```

## Decision Required

Director should decide whether to authorize Lucia to issue a scoped Lucode implementation task for the production-local override change.

The implementation task would allow only:

- Editing `/Users/concm/prod_workspace/Luceon2026/docker-compose.override.yml` to change the MinIO console port mapping from `"19001:9001"` to `"127.0.0.1:19001:9001"`.
- Preserving strict AI/model settings unchanged.
- Running the minimum Docker/Compose operations needed to apply or verify the binding, only if the task explicitly lists them.
- Running non-destructive validation: local console reachability, listener binding inspection, CMS reachability, and dependency-health checks.
- Recording exact production HEAD, override content before/after, commands, validation evidence, and rollback instructions.

The implementation task would still forbid:

- Production release-readiness declaration.
- DB, MinIO object, Docker volume, task, artifact, secret, or data mutation.
- Any unrelated production override change.
- Broad deployment or application rebuild beyond the minimum explicitly authorized operation.

## Lucia Recommendation

Lucia recommends approving a scoped implementation task, because the accepted plan is narrow, reversible, and directly closes a release-boundary blocker without changing application logic or data.

## Required Output

Director decision:

- Approve scoped implementation task.
- Hold implementation and request more evidence.
- Cancel this boundary reduction for now.

If approved, Lucia will issue a task brief to Lucode with exact allowed file, exact intended mapping, validation checks, rollback evidence, and explicit forbidden operations.
