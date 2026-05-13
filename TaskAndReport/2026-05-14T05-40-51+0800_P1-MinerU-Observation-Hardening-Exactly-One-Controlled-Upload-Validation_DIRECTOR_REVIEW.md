# Director Review: P1 MinerU Observation Hardening Exactly One Controlled Upload Validation

- Review time: 2026-05-14T05:40:51+0800
- Role: Director
- Reviewed task: `TaskAndReport/2026-05-14T05-21-59+0800_P1-MinerU-Observation-Hardening-Exactly-One-Controlled-Upload-Validation_TASK.md`
- Reviewed report: `TaskAndReport/2026-05-14T05-21-59+0800_P1-MinerU-Observation-Hardening-Exactly-One-Controlled-Upload-Validation_REPORT.md`
- Production workspace: `/Users/concm/prod_workspace/Luceon2026`
- Production HEAD verified: `159d80e Accept MinerU log observation hardening`
- Result: `ACCEPTED_CONTROLLED_UPLOAD_VALIDATION_PASS_WITH_RESIDUAL_DIAGNOSTIC_PROGRESS_LIMITATION`

## Decision

Task 104 is accepted within its explicitly narrow boundary.

The exactly-one controlled upload produced the evidence this task was designed to collect: `log-observation-unreadable` occurred while MinerU API was still processing, but the deployed hardening kept it as `mineru-log-observation-diagnostic-only` instead of a terminal failure. The task continued through MinerU completion, AI metadata extraction, and reached `review-pending`.

This acceptance does not claim pressure PASS, L3, production readiness, release readiness, go-live readiness, or production上线.

## Evidence Reviewed

TestAcceptanceEngineer reported:

- exactly one upload only;
- sample path: `/Users/concm/prod_workspace/Luceon2026/testpdf/2025_2026学年春季课程中数G8_提取.pdf`;
- sample size: `530205`;
- sample SHA-256: `71b95d983cdf73507c7334d3682f117f1dfce454286a6bb9f60d437a070b3cfb`;
- task id: `task-1778708005470`;
- material id: `task104-mineru-observation-1778708003`;
- MinerU task id: `c3d3e548-2b4f-4b6e-ae0d-0c11e17bb5a2`;
- AI job id: `ai-job-1778708023060-2c3d`;
- while MinerU API showed `processing_tasks=1`, task metadata showed `mineruObservedProgress.activityLevel=log-observation-unreadable`, `observationStale=true`, and `mineruLogObservationWarning.kind=mineru-log-observation-diagnostic-only`;
- task terminal state: `review-pending`;
- material terminal state: `reviewing`;
- parsed files count: `21`;
- AI job terminal state: `review-pending`;
- final active-task and admission circuit surfaces were clean.

Director independently spot-checked:

- production git state remained `159d80e Accept MinerU log observation hardening`;
- Docker services `cms-db-server`, `cms-frontend`, `cms-minio`, and `cms-upload-server` were healthy;
- upload health returned ok;
- dependency-health returned `ok=true`, `blocking=false`;
- MinerU submit-probe returned HTTP `202`;
- Ollama `qwen3.5:9b` remained resident and `chatOk=true`;
- admission circuit was closed/open=false;
- active-task surface was clean except historical AI failures;
- screenshots `/tmp/luceon-task104-list.png` and `/tmp/luceon-task104-detail.png` existed and showed the task as `待复核`, `状态一致`, `已生成 (Markdown)`, and `需人工审核`, without an operator-visible false failed state.

## Accepted Boundary

Accepted:

- The Task 101 hardening is live in production for this one controlled upload.
- The target defect class did not recur as terminal failure or operator-visible false failed semantics.
- Runtime surfaces ended clean after the validation.

Not accepted or not evidenced:

- Pressure, batch-concurrent, soak, broad long-run stability, L3, production readiness, release readiness, go-live readiness, or production上线.
- Rich MinerU business-progress visibility. The UI still reports `MinerU 已完成，但本次未捕获可归因业务进度日志` for this sample, which is honest diagnostic behavior but not progress-rich observability.
- Any repair or mutation of historical failed tasks.

## Residual Risk

The false-failed adjudication defect is now bounded-pass for this single upload. The remaining issue is observability quality: the task page can accurately avoid false failure, but for this sample it still cannot show attributable MinerU business progress such as page/batch progress. For long-running tasks, that limitation still affects operator confidence and unattended monitoring.

## Follow-Up

Director recorded Task 105 as a User decision item. Director recommendation is to avoid pressure testing for now and first dispatch a read-only Architect task to determine the real source of MinerU business-progress signals and whether the current diagnostic-only outcome is an acceptable product boundary or a fixable code/ops ownership gap.
