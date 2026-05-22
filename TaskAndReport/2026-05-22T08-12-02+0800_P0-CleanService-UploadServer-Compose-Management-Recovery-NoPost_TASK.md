# TASK-20260522-081202-P0-CleanService-UploadServer-Compose-Management-Recovery-NoPost

## 1. Task Summary

Recover the `cms-upload-server` runtime management boundary after Task 238's
manual `docker run` workaround.

This task is not a CleanService dispatch task. It exists only to restore or
prove a Compose-recognized `upload-server` runtime while keeping CleanService
disabled and while preserving the Mineru2Table job store.

## 2. Mainline Objective

Answer the next critical-path question:

> Can Luceon restore `upload-server` to a Compose-visible, single-service
> manageable runtime state without touching dependencies, data, images, volumes,
> credentials, or dispatch flow?

This must be solved before the next real dispatch step. A worker that is
reachable but not visible to Compose is not an acceptable mainline runtime
foundation.

## 3. Current Project State From Luceon

Luceon reviewed the host state before issuing this task:

- Luceon `main` and `origin/main`:
  `06692f0044b1061e57863bb15036de69f5fa475b`.
- Task 238 is not accepted. Return review:
  `CHANGES_REQUIRED_RUNTIME_MANAGEMENT_DRIFT_AND_CONTROL_PLANE_EVIDENCE_GAPS`.
- Current `cms-upload-server` positive facts:
  - container is running and healthy;
  - runtime env contains `CLEANSERVICE_ENABLED=false`;
  - runtime env contains `CLEANSERVICE_ENDPOINT=http://mineru2table:8000`;
  - GET-only `/health` from `cms-upload-server` to `mineru2table:8000` works.
- Current `cms-upload-server` blocking facts:
  - `docker compose ps upload-server` does not list the service;
  - `docker-compose ps upload-server` does not list the service;
  - current container labels only include:
    - `com.docker.compose.project`
    - `com.docker.compose.service`
    - `com.docker.compose.version`
  - Compose-managed sibling services include additional labels such as
    `com.docker.compose.config-hash`,
    `com.docker.compose.container-number`,
    `com.docker.compose.oneoff`,
    `com.docker.compose.project.config_files`, and
    `com.docker.compose.project.working_dir`.
- Current Mineru2Table job store remains:
  - path:
    `/Users/concm/prod_workspace/Mineru2Tables/data/jobs.json`
  - size: `718` bytes
  - sha256:
    `29d5621bcca3d626b8f27289caabd13ba6cd835913a76b9e2cbd8fd8d4577413`
  - key count: `1`
  - key: `luceon-optionb-mock-job-1779399902295`

## 4. Critical Path Scope

Do only this:

1. Reconfirm the runtime baseline with read-only checks.
2. Restore `cms-upload-server` so both Compose CLIs list `upload-server` again:
   - `docker compose ps upload-server`
   - `docker-compose ps upload-server`
3. Keep the CleanService runtime configuration disabled:
   - `CLEANSERVICE_ENABLED=false`
   - `CLEANSERVICE_ENDPOINT=http://mineru2table:8000`
   - `CLEANSERVICE_STORAGE_ENDPOINT=minio:9000`
   - `CLEANSERVICE_STORAGE_USE_SSL=false`
   - `CLEANSERVICE_SUBMITTED_BY=luceon2026/cleanservice-worker`
4. Verify GET-only network reachability from `cms-upload-server` to:
   - `http://mineru2table:8000/health`
5. Verify upload-server remains healthy.
6. Verify the Mineru2Table job store is byte/hash/key-count unchanged.
7. Write a report and update the ledger.

## 5. True Preconditions

All must pass before any runtime mutation:

- Git tree is clean except expected report/ledger edits after work begins.
- Current `cms-upload-server` is running.
- Current `mineru2table-api`, `cms-db-server`, `cms-minio`, and `cms-frontend`
  are running and must not be recreated.
- `CLEANSERVICE_ENABLED` in the running upload-server is currently `false`.
- `jobs.json` matches the size, hash, and key count listed above.
- No real Raw Material candidate is selected.

If any precondition fails, stop and report a specific blocked classification.

## 6. Authorized Runtime Operation

The only authorized runtime mutation is a controlled recovery of the single
`cms-upload-server` / `upload-server` service.

Permitted only if all preconditions pass:

- stop/remove/recreate only `cms-upload-server`, if required;
- reuse the existing `luceon2026-upload-server` image;
- reconnect only to the existing `cms-network`;
- preserve the existing read-only MinerU log mount;
- preserve existing upload-server service semantics while redacting
  credential-bearing values from reports;
- restore enough Compose metadata for both Compose CLIs to list the service.

Preferred recovery is a Compose-native single-service operation if it can be
proven not to recreate networks, dependencies, images, or volumes.

If local Compose again reports that `cms-network` must be recreated, do not run
`docker compose down`, do not remove/recreate `cms-network`, and do not touch
dependency services. Either use a proven single-container recovery that restores
Compose visibility, or stop with:

```text
BLOCKED_COMPOSE_MANAGEMENT_RECOVERY_REQUIRES_NETWORK_RECREATE
```

## 7. Forbidden Runtime/Data Operations

Forbidden:

- No `POST /api/v1/jobs`.
- No CleanService worker tick or scheduler activation.
- No `CLEANSERVICE_ENABLED=true`.
- No real Raw Material selection.
- No MinIO object/bucket read/write/list/delete.
- No Luceon DB write.
- No LLM/API call.
- No new credential injection.
- No secret or credential value printing in reports, terminal excerpts, or
  task notes.
- No Docker image build.
- No Docker volume cleanup/prune.
- No `docker compose down`.
- No `docker network rm` or `docker network create`.
- No dependency service restart/rebuild/recreate.
- No Mineru2Table restart/rebuild/recreate.
- No job-store cleanup, truncation, or manual edit.

Preserving existing upload-server runtime environment is allowed only as a
service recovery requirement, and all credential-bearing values must be
reported as present/absent or redacted, never as raw values.

## 8. Environment And Write Boundary

Allowed Luceon2026 files:

- `TaskAndReport/2026-05-22T08-12-02+0800_P0-CleanService-UploadServer-Compose-Management-Recovery-NoPost_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

Forbidden file changes:

- No `server/**` or `src/**`.
- No `docker-compose*.yml`.
- No `.env*`.
- No package or lock files.
- No PRD, architecture, or contract docs.
- No AGENTS.md or `.agents/**`.
- No external Mineru2Table repository changes.

## 9. Fast Validation Target

Smallest useful proof:

- `docker compose ps upload-server` lists `cms-upload-server`.
- `docker-compose ps upload-server` lists `cms-upload-server`.
- `cms-upload-server` is healthy.
- Runtime env contains disabled CleanService config.
- GET-only `http://mineru2table:8000/health` from `cms-upload-server` succeeds.
- `jobs.json` remains unchanged.
- No POST occurred.

## 10. Stop Rules

Stop immediately and report if:

1. Recovery would require network recreation.
2. Recovery would require dependency service restart/recreate.
3. Recovery would require image build.
4. Recovery would require volume cleanup or prune.
5. `CLEANSERVICE_ENABLED` would become anything other than `false`.
6. `jobs.json` changes unexpectedly.
7. Any credential value would need to be printed to prove success.
8. A POST would be needed for verification.
9. `docker compose ps upload-server` and `docker-compose ps upload-server`
   cannot both be made to list the service through a single-container recovery.

Do not repair by widening scope.

## 11. Positive Acceptance Criteria

Luceon can accept if:

- Only `cms-upload-server` / `upload-server` was affected.
- Both Compose CLIs list `upload-server`.
- Runtime env contains the accepted disabled CleanService values.
- `GET http://mineru2table:8000/health` from `cms-upload-server` succeeds.
- `jobs.json` remains unchanged.
- No source/config files are modified except report and ledger.
- No `POST`, activation, new credentials, raw secret printing, MinIO/DB/LLM
  operation, Docker build, volume mutation, dependency recreate, or real
  material selection occurs.
- `git diff --check` passes.

## 12. Negative Acceptance Criteria

The task fails if:

- `upload-server` remains absent from either Compose CLI's `ps` output.
- Any CleanService dispatch POST is sent.
- `CLEANSERVICE_ENABLED=true` or equivalent activation is observed.
- Any credential value is printed in the report or ledger.
- Any job-store mutation occurs.
- Any real MinIO object or Luceon DB/LLM operation occurs.
- Any source/config/runtime file outside the allowed report/ledger files is
  changed.
- Docker build, network recreate, dependency recreate, staging service mutation,
  volume prune, or cleanup is performed.
- The report claims UAT, L3, release-readiness, production-readiness, pressure
  PASS, production上线, or go-live.

## 13. Required AI/Data Governance Red Lines

Preserve these even though this is runtime recovery:

1. ID-only extraction: no model output or source truth generation is allowed.
2. Asset hash locking: no source asset names or hashes may be renamed or
   rewritten.
3. Pure layout/code-generation boundary: no LaTeX/TikZ or custom command
   generation is in scope.

## 14. Report Requirements

Create:

```text
TaskAndReport/2026-05-22T08-12-02+0800_P0-CleanService-UploadServer-Compose-Management-Recovery-NoPost_REPORT.md
```

The report must include:

- Branch and exact HEAD.
- Baseline `docker compose ps upload-server` and `docker-compose ps upload-server`
  output.
- Baseline and post-state `cms-upload-server` identity/status.
- The exact recovery command shape used, with credential-bearing values
  redacted.
- Post-state Compose visibility evidence from both Compose CLIs.
- Runtime disabled CleanService env evidence.
- GET-only Mineru2Table health evidence from `cms-upload-server`.
- `jobs.json` before/after size/hash/key-count.
- Whether any POST was sent: must be `no`.
- Confirmation that no Docker build, network recreate, dependency recreate,
  staging mutation, volume cleanup, credential printing, DB write, MinIO object
  operation, LLM call, or real material selection occurred.
- Final classification:
  - `UPLOAD_SERVER_COMPOSE_MANAGEMENT_RECOVERED_NO_POST`, or
  - a specific blocked classification.

## 15. Review Boundary

Acceptance means only:

- `upload-server` is again visible/manageable through Compose while holding the
  disabled CleanService runtime configuration.

Acceptance does not mean:

- CleanService dispatch is active.
- MinIO credentials are configured for Mineru2Table.
- LLM credentials are configured for Mineru2Table.
- Real Raw Material success path has been tested.
- Clean Material artifacts are valid.
- UAT, L3, pressure PASS, release readiness, production readiness,
  production上线, or go-live.
