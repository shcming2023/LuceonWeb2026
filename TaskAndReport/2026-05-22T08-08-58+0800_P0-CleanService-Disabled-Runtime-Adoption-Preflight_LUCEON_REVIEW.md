# TASK-20260522-063003-P0-CleanService-Disabled-Runtime-Adoption-Preflight LUCEON REVIEW

## Decision

`CHANGES_REQUIRED_RUNTIME_MANAGEMENT_DRIFT_AND_CONTROL_PLANE_EVIDENCE_GAPS`

Task 238 is not accepted.

This is not a rejection of the mainline hypothesis. The runtime proof partially
succeeded: `cms-upload-server` now has the disabled CleanService endpoint
environment loaded, can reach `mineru2table:8000` with a GET-only health check,
and the Mineru2Table job store remained unchanged.

The task cannot be closed because the submitted evidence and current runtime
state do not satisfy the task's management and control-plane boundaries.

## Host Review Evidence

Luceon reviewed from `/Users/concm/prod_workspace/Luceon2026` and the current
host runtime after the Lucode handoff.

Verified positive facts:

- `cms-upload-server` is running and healthy.
- Runtime env includes:
  - `CLEANSERVICE_ENABLED=false`
  - `CLEANSERVICE_ENDPOINT=http://mineru2table:8000`
  - `CLEANSERVICE_STORAGE_ENDPOINT=minio:9000`
  - `CLEANSERVICE_STORAGE_USE_SSL=false`
  - `CLEANSERVICE_SUBMITTED_BY=luceon2026/cleanservice-worker`
- `docker exec cms-upload-server wget -qO- http://mineru2table:8000/health`
  returned HTTP content with honest `minio=unconfigured`,
  `llm=not_configured`, and `dependencies=ok`.
- `/Users/concm/prod_workspace/Mineru2Tables/data/jobs.json` remains:
  - size: `718` bytes
  - sha256: `29d5621bcca3d626b8f27289caabd13ba6cd835913a76b9e2cbd8fd8d4577413`
  - key count: `1`
  - key: `luceon-optionb-mock-job-1779399902295`

No Luceon acceptance here implies CleanService activation, successful real Raw
Material processing, UAT, L3, release readiness, production readiness, pressure
PASS, or go-live.

## Blocking Findings

### F1. Delivery Branch Is Not GitHub-Visible

`git ls-remote` returned no remote branch for the reported Task 238 branch.
The primary Luceon workspace remains on `main`/`origin/main` at the Task 238
dispatch commit, and the report file is not present in the production
workspace.

The local Dev workspace has branch
`lucode/TASK-20260522-063003-P0-CleanService-Disabled-Runtime-Adoption-Preflight`
at `8303f2095691ee92a9cd139003e3e03da6fca9ec`, but that is not sufficient for
formal Luceon acceptance.

### F2. Report HEAD Is Incorrect

The local report records the exact HEAD as
`1fa4b9db8f05e191d5f058bb26afcf649bdd5233`, which is the task-dispatch baseline,
not the delivery commit.

### F3. Diff Check Fails

Luceon ran:

```bash
git diff --check 1fa4b9db8f05e191d5f058bb26afcf649bdd5233..8303f2095691ee92a9cd139003e3e03da6fca9ec
```

It failed with trailing whitespace in the Task 238 report.

### F4. Report Prints Credential Values

The task explicitly forbids credential injection or secret printing. The local
report includes unredacted credential-bearing environment variables in the
manual `docker run` command and also claims no credentials were exposed.

Luceon is intentionally not repeating those values in this review.

### F5. Upload-Server Is No Longer Listed By Compose

Both of these read-only checks did not list `upload-server` / `cms-upload-server`
as a Compose service:

```bash
docker compose ps upload-server
docker-compose ps upload-server
```

The full Compose service list currently shows `db-server`, `cms-frontend`, and
`minio`, but not `upload-server`.

This means the manual `docker run` recreation did not prove an equivalent
Compose-managed service adoption. It may have loaded the intended environment,
but it also introduced runtime management drift. Before any further dispatch
work, the project needs a controlled plan to restore or prove the intended
Compose management boundary.

## Required Narrow Return

Do not send any `POST /api/v1/jobs`.

Do not enable CleanService.

Do not inject credentials, touch real material, mutate MinIO objects, write the
Luceon DB, call LLMs, rebuild images, clean volumes, edit the Mineru2Table job
store, or restart/recreate dependency services.

The next step is not a new implementation task yet. Luceon should first present
the Director with a short recovery plan for the upload-server runtime management
drift, then issue a concrete task only after the Director confirms the plan.
