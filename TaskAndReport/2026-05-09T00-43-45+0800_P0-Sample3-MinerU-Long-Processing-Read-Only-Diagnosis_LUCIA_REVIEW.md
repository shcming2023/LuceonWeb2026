# Lucia Review: P0 Sample 3 MinerU Long-Processing Read-Only Diagnosis

- Task ID: `TASK-20260508-234438-P0-Sample3-MinerU-Long-Processing-Read-Only-Diagnosis`
- Review time: `2026-05-09T00:43:45+0800`
- Reviewed report: `TaskAndReport/2026-05-09T00-11-06+0800_P0-Sample3-MinerU-Long-Processing-Read-Only-Diagnosis_REPORT.md`
- Report commits observed: `d39e698`, ledger head `cf7dbb2`
- Decision: `ACCEPTED_DIAGNOSIS_CODE_LEVEL_CORRECTION_REQUIRED`

## Decision

Lucia accepts Lucode's read-only diagnosis.

The issue is not current MinerU throughput. Direct MinerU API evidence shows task `ec9452cc-94e4-4b36-bb64-efba86f38cf6` is `completed`, MinerU health reports `processing_tasks=0`, and the result endpoint is available. Luceon still shows `task-1778249434820` as `running` / `mineru-processing`, material `mat-1778249419780` as `processing`, and no AI metadata job exists.

Lucia classifies this as a terminal-state propagation / result-ingestion stuck state after local MinerU timeout, with stale log observation as a related observability symptom.

Production write-side recovery is not authorized by this review. Lucia is issuing a code-level correction task first so the recovery path can be implemented and verified without mutating the existing production task.

Production release readiness remains unclaimed.

## Independent Checks

Lucia independently refreshed:

- `GET /__proxy/db/tasks/task-1778249434820`: still `running` / `mineru-processing`, message `本地等待超时但 MinerU 仍在 processing，后台将继续观测`.
- `GET /__proxy/db/materials/mat-1778249419780`: material still `processing`, `metadata.mineruStatus=processing`.
- `GET /__proxy/db/ai-metadata-jobs?parseTaskId=task-1778249434820`: `[]`.
- `GET http://192.168.31.33:8083/health`: `processing_tasks=0`, `queued_tasks=0`, `completed_tasks=26`.
- `GET http://192.168.31.33:8083/tasks/ec9452cc-94e4-4b36-bb64-efba86f38cf6`: `status=completed`, `completed_at=2026-05-08T15:14:21.454388+00:00`, `error=null`.

These checks support the report's conclusion.

## Accepted Evidence

- The external sample directory remained read-only.
- No reparse, retry, upload, cleanup, DB mutation, MinIO mutation, Docker mutation, service restart, config/model/timeout/secret/override change, signed URL persistence, or production release-readiness claim occurred.
- The stuck state is reproducible via read-only API checks.

## Next Action

Lucia issued `TASK-20260509-004345-P0-MinerU-Completed-After-Local-Timeout-Takeover-Code-Fix` to Lucode.

The new task is code-level only. It must implement and test a safe takeover path for local MinerU tasks that time out locally but later report completed through the MinerU API. It must not perform production recovery or mutate `task-1778249434820`.

After code-level acceptance, Lucia will decide whether to request a separate Director authorization for a narrowly scoped production recovery of the existing stuck task.
