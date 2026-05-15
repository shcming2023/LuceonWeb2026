# Director Review: P0 Production Dirty Source Backup Reconcile And Progress Snapshot Deploy

- Task ID: `TASK-20260516-070758-P0-Production-Dirty-Source-Backup-Reconcile-And-Progress-Snapshot-Deploy`
- Reviewed at: `2026-05-16T07:23:05+0800`
- Reviewed by: `Director`
- Report reviewed: `TaskAndReport/2026-05-16T07-07-58+0800_P0-Production-Dirty-Source-Backup-Reconcile-And-Progress-Snapshot-Deploy_REPORT.md`
- Report commit reviewed: `117502c`
- Result: `ACCEPTED_DEPLOYED_READ_ONLY_VALIDATED_WITH_P0_MINIO_BINDING_CORRECTION_REQUIRED`

## Judgment

Accepted with a required P0 correction.

DevelopmentEngineer completed the core authorized recovery path:

- production dirty tracked source was backed up outside the repository;
- production tracked source was restored by explicit paths, not by `git reset --hard`;
- production fast-forwarded from `1716add` to `00d83bb`;
- Task 193 progress-snapshot implementation is now deployed in production;
- read-only validation passed for CMS routes, upload health, dependency-health without submit-probe, active-task direct diagnostics, and log-channel ownership;
- no upload, pressure test, submit-probe, task repair/retry/reparse/re-AI, data cleanup, Docker volume mutation, model/secret/sample mutation, or readiness/go-live claim was performed.

The implementation objective is therefore accepted as production-deployed/read-only-validated.

## Director Spot-Check

Director spot-checked the production runtime read-only:

- `docker compose ps` shows `cms-db-server`, `cms-frontend`, `cms-minio`, and `cms-upload-server` up and healthy.
- dependency-health with `mineruSubmitProbe=false` returned `ok=true`, `blocking=false`, and `progressSnapshot.version=progress-snapshot-v0.1` with `lagKind=dependency-health-readiness-only`.
- `/ops/mineru/active-task?queryApi=true` returned no active/current/queued/result-ingestion-lag tasks and `diagnosticMode.directMineruChecked=true`; one historical AI failure remains visible.
- production source is clean at `00d83bb`.

## Required Correction

The report also surfaced a real production exposure regression:

- current production `docker-compose.override.yml` maps MinIO console as `"19001:9001"`;
- the previous backed-up production override mapped it as `"127.0.0.1:19001:9001"`;
- `docker port cms-minio` now shows `9001/tcp -> 0.0.0.0:19001` and `9001/tcp -> [::]:19001`;
- repository docs explicitly require MinIO console local-only binding, including `docs/deploy/PRODUCTION_RUNTIME_OWNERSHIP.md` and `docs/deploy/DEPLOY.md`.

This is not acceptable as a long-lived production state. It is a bounded configuration correction, not a new release decision. Director issued Task 198 to DevelopmentEngineer to restore the local-only MinIO console binding in repo and production, then validate read-only.

## Boundaries

This review does not declare pressure PASS, L3, release readiness, production readiness, go-live readiness, or production上线.

No pressure validation or active-task retry/repair is authorized by this review.
