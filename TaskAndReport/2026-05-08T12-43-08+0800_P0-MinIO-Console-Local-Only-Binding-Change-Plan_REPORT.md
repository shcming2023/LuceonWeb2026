# P0 MinIO Console Local-Only Binding Change Plan Report

## Basis

- Based on Lucia task brief: `TaskAndReport/2026-05-08T12-38-16+0800_P0-MinIO-Console-Local-Only-Binding-Change-Plan_TASK.md`.
- Assignee: Lucode.
- Scope executed: non-destructive implementation planning only.
- Explicit boundary: production release readiness is not claimed.

## Branch And HEAD

- Branch: `main`
- Initial HEAD: `a688863 docs: correct minio binding task head`
- Final report HEAD: `PENDING_FINAL_HEAD`

## Files Changed

- `TaskAndReport/TASK_TRACKING_LIST.md`
- `TaskAndReport/2026-05-08T12-43-08+0800_P0-MinIO-Console-Local-Only-Binding-Change-Plan_REPORT.md`

## Files Read

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/lucode.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/codex/TEST_POLICY.md`
- `docs/deploy/DEPLOY.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`
- `TaskAndReport/2026-05-08T12-38-16+0800_P0-MinIO-Console-Local-Only-Binding-Change-Plan_TASK.md`
- `TaskAndReport/2026-05-08T12-30-45+0800_P0-Production-Override-Release-Boundary-Decision_DECISION.md`
- `TaskAndReport/2026-05-08T12-38-16+0800_P0-Production-Override-Release-Boundary-Decision_LUCIA_REVIEW.md`
- `/Users/concm/prod_workspace/Luceon2026/docker-compose.override.yml` read-only, first 80 lines only.

## Current Observed Mapping

Read-only production-local override observation:

```yaml
services:
  upload-server:
    environment:
      - DISABLE_AI_SKELETON_FALLBACK=true
      - OLLAMA_TIER2_MODEL=qwen3.5:9b

  minio:
    ports:
      - "19001:9001"
```

Current MinIO console mapping requiring change:

```yaml
      - "19001:9001"
```

This maps host port `19001` without an explicit loopback bind. Per Director decision, this is not accepted as-is before release-candidate naming.

## Proposed Local-Only Mapping

Proposed production-local override change for a future separately authorized implementation task:

```yaml
  minio:
    ports:
      - "127.0.0.1:19001:9001"
```

This preserves the same local host port for administrator access while narrowing the bind address to loopback. Strict AI/model settings remain unchanged:

```yaml
  upload-server:
    environment:
      - DISABLE_AI_SKELETON_FALLBACK=true
      - OLLAMA_TIER2_MODEL=qwen3.5:9b
```

## Validation Plan

Validation should be performed only after a separate Director-approved production override implementation task.

1. Pre-change capture:
   - Confirm production worktree state and exact HEAD with `git status --short --branch` and `git log -1 --oneline`.
   - Read current `docker-compose.override.yml` and confirm the only intended change is MinIO console port binding from `"19001:9001"` to `"127.0.0.1:19001:9001"`.
   - Confirm no active parse or AI work before any restart/recreate operation if the future implementation requires Docker Compose.

2. Compose/config verification:
   - Use the future task's approved Docker/Compose command set to verify the effective mapping.
   - Expected effective mapping: host loopback `127.0.0.1:19001` to container `9001`.
   - Strict AI/model environment values must remain present and unchanged.

3. Local reachability:
   - From the production host, verify MinIO console remains reachable at `http://127.0.0.1:19001`.
   - If the Director expects browser access through `localhost`, verify `http://localhost:19001` also reaches the console from the same host.

4. Non-local exposure check:
   - Verify the service is not listening on wildcard or LAN interfaces for port `19001`.
   - A future authorized validation can use non-destructive listener inspection such as `lsof -nP -iTCP:19001 -sTCP:LISTEN` or an approved equivalent.
   - Expected listener address: `127.0.0.1:19001` only, not `0.0.0.0:19001`, `[::]:19001`, or the LAN IP.

5. Application regression smoke:
   - Confirm CMS remains reachable at the production manual-review URL.
   - Confirm dependency-health remains non-blocking with existing required probes if runtime checks are authorized by the future task.
   - Confirm this change does not alter MinIO API port `9000`, buckets, objects, DB data, tasks, parsed artifacts, or strict AI/model behavior.

## Rollback Plan

Rollback should also require explicit authorization if performed against production.

1. Restore the previous MinIO console mapping:

```yaml
  minio:
    ports:
      - "19001:9001"
```

2. Keep strict AI/model settings unchanged:

```yaml
  upload-server:
    environment:
      - DISABLE_AI_SKELETON_FALLBACK=true
      - OLLAMA_TIER2_MODEL=qwen3.5:9b
```

3. Re-apply only the approved production runtime operation from the future task.
4. Re-run the same local reachability and dependency-health checks assigned by that task.
5. Record rollback reason, exact production HEAD, final override content, and command evidence in `TaskAndReport/`.

## Risk Assessment

| Risk | Assessment | Mitigation |
| --- | --- | --- |
| Local admin access changes | Low to medium. Access via `http://127.0.0.1:19001` should remain, but LAN/browser workflows using another host would stop working. | Confirm Director expects local-host-only access before implementation; document changed access URL. |
| Docker Compose syntax support | Low. Compose port syntax supports `HOST_IP:HOST_PORT:CONTAINER_PORT` in common Compose versions, but effective config should still be verified. | Run approved config/effective-mapping verification in future implementation task. |
| Accidental strict AI/model drift | Medium if the override is edited manually. | Future patch must only change the MinIO port string and leave upload-server environment unchanged. |
| Production interruption | Low to medium depending on future Docker operation used to apply the override. | Check active parse/AI work first; use the least disruptive approved operation; avoid data/volume changes. |
| False release-readiness signal | Medium if the binding change is treated as final release approval. | Keep this as one release-boundary reduction only; production release readiness remains unclaimed. |

## Commands Run

| Command | Exit | Evidence |
| --- | ---: | --- |
| `git status --short --branch` | 0 | Dev workspace initially clean: `## main...origin/main` |
| `git fetch origin` | 0 | Completed without output |
| `git pull --ff-only origin main` | 0 | `Already up to date.` |
| `sed -n '1,300p' TaskAndReport/TASK_TRACKING_LIST.md` | 0 | Found task 25 assigned to Lucode |
| `rg -n "Lucode|..." TaskAndReport/TASK_TRACKING_LIST.md` | 0 | Confirmed row 25 `Next Actor=Lucode` |
| `git log -1 --oneline` | 0 | `a688863 docs: correct minio binding task head` |
| `sed -n '1,260p' TaskAndReport/2026-05-08T12-38-16+0800_P0-MinIO-Console-Local-Only-Binding-Change-Plan_TASK.md` | 0 | Read task brief |
| `sed -n '1,220p' AGENTS.md` | 0 | Read operating rules |
| `sed -n '1,220p' docs/codex/TEAM_CONTRACT.md` | 0 | Read team contract |
| `sed -n '1,220p' docs/codex/roles/lucode.md` | 0 | Read Lucode role |
| `sed -n '1,180p' docs/codex/PROJECT_STATE.md` | 0 | Read project state |
| `sed -n '1,180p' docs/codex/HANDOFF.md` | 0 | Read handoff |
| `sed -n '1,180p' docs/codex/TEST_POLICY.md` | 0 | Read test policy |
| `sed -n '176,225p' docs/deploy/DEPLOY.md` | 0 | Read production-local override contract |
| `sed -n '1,220p' TaskAndReport/2026-05-08T12-30-45+0800_P0-Production-Override-Release-Boundary-Decision_DECISION.md` | 0 | Read Director decision record |
| `sed -n '1,220p' TaskAndReport/2026-05-08T12-38-16+0800_P0-Production-Override-Release-Boundary-Decision_LUCIA_REVIEW.md` | 0 | Read Lucia review |
| `sed -n '1,80p' /Users/concm/prod_workspace/Luceon2026/docker-compose.override.yml` | 0 | Read current production-local override mapping |
| `git status --short --branch` in production workspace | 0 | `## main...origin/main [behind 2]`; `M docker-compose.override.yml` |
| `date '+%Y-%m-%dT%H-%M-%S%z'` | 0 | Report timestamp `2026-05-08T12-43-08+0800` |
| `git diff --check` | 0 | No whitespace errors |
| `git status --short --branch` | 0 | Expected task-list/report changes only |
| `git diff --name-only` | 0 | Tracked change limited to `TaskAndReport/TASK_TRACKING_LIST.md`; new report file visible in `git status` |
| `git diff --stat` | 0 | Task-list tracked delta reviewed |

## Checks Skipped

- Runtime checks were skipped because the task states no runtime checks are required.
- Docker checks and Compose effective-config checks were skipped because Docker commands are forbidden.
- Production mutation checks were skipped because production workspace edits, override edits, restart, rebuild, deploy, rollback, sync, and runtime/data/secret mutations are forbidden.

## Production Runtime Confirmation

- Production workspace was read only.
- Production `docker-compose.override.yml` was not edited.
- No Docker command was run.
- No production sync, rebuild, restart, deploy, rollback, DB mutation, MinIO mutation, Docker volume mutation, task mutation, artifact mutation, secret change, or local runtime data mutation occurred.
- Strict AI/model settings are planned to remain unchanged.
- Production release readiness remains unclaimed.

## Remaining Approval Required

- Lucia review of this planning report.
- Separate Director approval before any production override implementation.
- Separate Lucia task brief before any production workspace edit or Docker/Compose operation.
- Exact production HEAD and final override-boundary confirmation before any release-candidate naming.

## GitHub Sync Status

- Report and task-list update are to be committed and pushed to GitHub `main`.
