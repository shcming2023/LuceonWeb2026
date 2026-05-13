# Director Review: P0 Exactly One Controlled Upload Validation After Batched Fixes

Review time:
2026-05-13T19:13:44+0800

Reviewed task:
`TASK-20260513-183148-P0-Exactly-One-Controlled-Upload-Validation-After-Batched-Fixes`

Reviewed report:
`TaskAndReport/2026-05-13T18-31-48+0800_P0-Exactly-One-Controlled-Upload-Validation-After-Batched-Fixes_REPORT.md`

## Decision

`ACCEPTED_FAILED_VALIDATION_EVIDENCE_WITH_PARTIAL_FIX_CONFIRMED`

The TestAcceptanceEngineer report is accepted as valid failed-validation evidence.

This is not production readiness, L3, pressure PASS, release-readiness, or a go-live signal.

## Evidence Accepted

The report satisfies the exactly-one-upload validation boundary:

- safe production preflight passed;
- exactly one authorized upload was performed from:
  `/Users/concm/prod_workspace/Luceon2026/testpdf/2025_2026学年春季课程中数G8_提取.pdf`;
- sample SHA-256 matched:
  `71b95d983cdf73507c7334d3682f117f1dfce454286a6bb9f60d437a070b3cfb`;
- created task/material/job:
  - task: `task-1778670208778`;
  - material: `validation-batched-fixes-1778670207`;
  - AI job: `ai-job-1778670234560-4a6f`;
- MinerU completed and stored 21 parsed artifacts;
- task list/material view showed improved terminal MinerU diagnostic:
  `MinerU 已完成，但本次未捕获可归因业务进度日志`;
- the previous 30s `UND_ERR_HEADERS_TIMEOUT` did not recur;
- first Ollama pass succeeded after `101519ms` under `timeoutMs=180000`;
- JSON Repair failed after `154520ms`, and strict no-skeleton behavior correctly blocked skeleton fallback;
- task/material ended failed at AI stage;
- no evidence showed duplicate processing after successful AI finalization, but successful finalization was not reached in this run;
- post-terminal admission circuit and active-task diagnostics were clean;
- no second upload, pressure/batch/soak test, failed-task repair, reparse, re-AI, cleanup, destructive DB/MinIO/Docker volume/data mutation, model operation, broad restart/rollback, sample mutation, GitHub push by the tester, L3, pressure PASS, production-readiness, or release-readiness claim occurred.

Director spot-check of production read-only APIs confirmed the reported terminal state:

- task `task-1778670208778`: `state=failed`, `stage=ai`, `mineruStatus=completed`, `parsedFilesCount=21`;
- material `validation-batched-fixes-1778670207`: `status=failed`, `mineruStatus=completed`, `aiStatus=failed`;
- AI job `ai-job-1778670234560-4a6f`: `state=failed`, `currentPhase=repair-failed`;
- event stream includes first-pass success, repair-pass parse failure, and strict no-skeleton failure.

## Diagnosis

The current primary release blocker has shifted.

Resolved or improved:

- production deployment of Task 91 and Task 93 is active;
- MinerU completes and stores parsed artifacts for the controlled sample;
- Ollama no longer fails at the previous 30s headers-timeout boundary for this sample;
- strict no-skeleton semantics remain intact;
- task-list terminal MinerU wording is materially better than before.

Still blocking:

- AI metadata does not yet produce a stable valid non-skeleton terminal result for this small/medium sample;
- the repair pass asked `qwen3.5:9b` to output canonical JSON, but the raw repair output was malformed JSON, not truncated, with `responseFormatRequested=true` and `expectJson=true`;
- therefore the system correctly failed rather than accepting a skeleton or untrusted output.

Residual P1 observability debt:

- task metadata still retains stale `log-observation-unreadable` after terminal MinerU completion while material/task-list view has the improved terminal diagnostic;
- the worker still briefly emits false failed events for unreadable MinerU logs and then corrects them;
- task detail overview did not expose the terminal MinerU diagnostic in the captured UI body, while task list did.

Those MinerU issues remain important, but they are not the current P0 end-to-end blocker. The P0 blocker is AI JSON/schema reliability under strict no-skeleton semantics.

## Next Action

Director is issuing:

`TASK-20260513-191344-P0-AI-Metadata-JSON-Repair-And-Schema-Reliability`

Assignee:
`DevelopmentEngineer`

Purpose:
diagnose and implement a scoped code/test-level remediation for the Task 95 AI JSON Repair / schema reliability failure, without weakening strict no-skeleton behavior or changing production/runtime state.

Not authorized:
production deployment, upload, pressure test, failed-task repair, reparse, re-AI, cleanup, destructive DB/MinIO/Docker volume/data mutation, model operation, broad restart/rollback, sample mutation, L3, pressure PASS, production-readiness, or release-readiness claim.
