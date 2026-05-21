# TASK-20260522-063003-P0-CleanService-Disabled-Runtime-Adoption-Preflight

## 1. Task Summary

Adopt the already accepted Task 237 CleanService endpoint configuration into the running `cms-upload-server` container while keeping CleanService disabled.

This is a disabled runtime adoption preflight. It must not dispatch any CleanService job, must not inject credentials, and must not touch real Raw Material.

## 2. Mainline Objective

Answer the next critical-path question:

> Can the running Luceon upload-server process load the durable Mineru2Table endpoint configuration (`http://mineru2table:8000`) while CleanService remains disabled and no job-store mutation occurs?

This bridges the gap between "configuration persisted in Compose" and "runtime process has loaded the disabled configuration".

## 3. Current Project State From Luceon

Luceon reviewed current state before issuing this task:

- Luceon `main` and `origin/main`: `65fdbef4159a9ec83e3ceb20c78e2ec4e4874291`.
- Task 237 accepted `CLEANSERVICE_ENDPOINT=http://mineru2table:8000` and `CLEANSERVICE_ENABLED=false` in `docker-compose.yml` / `.env.example`.
- Rendered Compose config already shows:

```text
CLEANSERVICE_ENABLED: "false"
CLEANSERVICE_ENDPOINT: http://mineru2table:8000
CLEANSERVICE_STORAGE_ENDPOINT: minio:9000
CLEANSERVICE_STORAGE_USE_SSL: "false"
CLEANSERVICE_SUBMITTED_BY: luceon2026/cleanservice-worker
```

- The currently running `cms-upload-server` process does not yet expose `CLEANSERVICE_*` env values because Task 237 did not restart/recreate it.
- Current containers:

```text
mineru2table-api Up ... (healthy) 127.0.0.1:8000->8000/tcp
cms-upload-server Up ... (healthy) 8788-8789/tcp
```

- Current Mineru2Table job-store:

```text
/Users/concm/prod_workspace/Mineru2Tables/data/jobs.json
size: 718 bytes
sha256: 29d5621bcca3d626b8f27289caabd13ba6cd835913a76b9e2cbd8fd8d4577413
key count: 1
key: luceon-optionb-mock-job-1779399902295
```

## 4. Critical Path Scope

Do only this:

1. Confirm preflight state and `jobs.json` baseline.
2. Recreate/restart only the Luceon `upload-server` service so the already committed Compose env is loaded.
3. Verify the new `cms-upload-server` container env includes:
   - `CLEANSERVICE_ENABLED=false`
   - `CLEANSERVICE_ENDPOINT=http://mineru2table:8000`
   - `CLEANSERVICE_STORAGE_ENDPOINT=minio:9000`
   - `CLEANSERVICE_STORAGE_USE_SSL=false`
   - `CLEANSERVICE_SUBMITTED_BY=luceon2026/cleanservice-worker`
4. From inside `cms-upload-server`, perform GET-only verification:
   - `GET http://mineru2table:8000/health`
5. Verify upload-server remains healthy.
6. Verify `jobs.json` remains byte/hash/key-count identical.
7. Write a report and update the ledger.

## 5. Authorized Runtime Operation

The only authorized runtime mutation is a controlled recreate/restart of the Luceon `upload-server` service.

Preferred command shape:

```bash
docker compose up -d --no-deps --no-build --force-recreate upload-server
```

If this exact shape is not supported by the local Docker Compose version, stop and report `BLOCKED_UPLOAD_SERVER_RECREATE_COMMAND_GAP` unless an equivalent command can be proven to:

- target only the `upload-server` service;
- not rebuild images;
- not start/recreate dependencies;
- not touch volumes.

Do not target `staging-cms-upload-server`.

## 6. Environment And Write Boundary

Allowed Luceon2026 files:

- `TaskAndReport/2026-05-22T06-30-03+0800_P0-CleanService-Disabled-Runtime-Adoption-Preflight_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

Forbidden file changes:

- No `server/**` or `src/**`.
- No `docker-compose*.yml`.
- No `.env*`.
- No package or lock files.
- No PRD, architecture, or contract docs.
- No AGENTS.md or `.agents/**`.

Forbidden runtime/data operations:

- No `POST /api/v1/jobs`.
- No CleanService worker tick or scheduler activation.
- No real material selection.
- No MinIO object/bucket read/write/list/delete.
- No Luceon DB write.
- No LLM/API call.
- No credential injection or secret printing.
- No Docker image build.
- No Docker volume cleanup/prune.
- No Mineru2Table restart/rebuild/recreate.
- No job-store cleanup, truncation, or manual edit.

## 7. True Preconditions

All must pass before recreating upload-server:

- Git tree is clean except expected task report/ledger edits after work begins.
- `docker compose config` still renders the accepted CleanService values from Task 237.
- Current `cms-upload-server` is running.
- Current `mineru2table-api` is running.
- `jobs.json` matches Task 236/237 post-state exactly:
  - size `718`
  - SHA256 `29d5621bcca3d626b8f27289caabd13ba6cd835913a76b9e2cbd8fd8d4577413`
  - key count `1`
  - key `luceon-optionb-mock-job-1779399902295`

If any precondition fails, do not recreate anything; stop and report a specific block reason.

## 8. Fast Validation Target

Smallest useful proof:

- Running `cms-upload-server` env contains the accepted CleanService config.
- `CLEANSERVICE_ENABLED=false`.
- `cms-upload-server` can GET `http://mineru2table:8000/health`.
- `jobs.json` is unchanged.
- No POST occurred.

## 9. Stop Rules

Stop immediately and report if:

1. The recreate command would touch dependencies, staging, images, or volumes.
2. `CLEANSERVICE_ENABLED` would become anything other than `false`.
3. `CLEANSERVICE_ENDPOINT` is not `http://mineru2table:8000`.
4. A POST would be needed for verification.
5. `jobs.json` changes unexpectedly.
6. Any credential appears or would need to be configured.
7. Upload-server fails to return to healthy/running state within a bounded wait.

Do not repair by widening scope.

## 10. Positive Acceptance Criteria

Luceon can accept if:

- Only `cms-upload-server` / `upload-server` is recreated or restarted.
- Runtime env contains the accepted disabled CleanService values.
- `GET http://mineru2table:8000/health` from `cms-upload-server` succeeds.
- `jobs.json` remains unchanged.
- No source/config files are modified except report and ledger.
- No `POST`, credentials, MinIO/DB/LLM operation, Docker build, volume mutation, or real material selection occurs.
- `git diff --check` passes.

## 11. Negative Acceptance Criteria

The task fails if:

- Any CleanService dispatch POST is sent.
- `CLEANSERVICE_ENABLED=true` or equivalent activation is observed.
- Any credentials are configured, printed, or leaked.
- Any job-store mutation occurs.
- Any real MinIO object or Luceon DB/LLM operation occurs.
- Any source/config/runtime files outside the allowed report/ledger files are changed.
- Docker build, dependency recreate, staging service mutation, volume prune, or cleanup is performed.
- The report claims UAT, L3, release-readiness, production-readiness, pressure PASS, production上线, or go-live.

## 12. Required AI/Data Governance Red Lines

Preserve these even though this is a disabled runtime adoption task:

1. ID-only extraction: no model output or source truth generation is allowed.
2. Asset hash locking: no source asset names or hashes may be renamed or rewritten.
3. Pure layout/code-generation boundary: no LaTeX/TikZ or custom command generation is in scope.

## 13. Report Requirements

Create:

```text
TaskAndReport/2026-05-22T06-30-03+0800_P0-CleanService-Disabled-Runtime-Adoption-Preflight_REPORT.md
```

The report must include:

- Branch and exact HEAD.
- Preflight `docker compose config` CleanService values.
- Before/after `cms-upload-server` container identity/status.
- Exact recreate command used.
- Runtime env evidence after recreate.
- GET-only Mineru2Table health evidence from `cms-upload-server`.
- `jobs.json` before/after size/hash/key-count.
- Whether any POST was sent: must be `no`.
- Confirmation that no Docker build/dependency recreate/staging mutation occurred.
- Final classification:
  - `DISABLED_RUNTIME_CONFIG_ADOPTED_NO_POST`, or
  - a specific blocked classification.

## 14. Review Boundary

Acceptance means only:

- The running Luceon upload-server process has adopted disabled CleanService endpoint configuration.

Acceptance does not mean:

- CleanService dispatch is active.
- MinIO credentials are configured.
- LLM credentials are configured.
- Real Raw Material success path has been tested.
- Clean Material artifacts are valid.
- UAT, L3, pressure PASS, release readiness, production readiness, production上线, or go-live.
