# Director Review: P0 Exactly One Controlled Upload Validation After Task 87 Deployment

Review time:
2026-05-13T15:17:15+0800

Reviewed task:
`TASK-20260513-144620-P0-Exactly-One-Controlled-Upload-Validation-After-Task-87-Deployment`

Reviewed report:
`TaskAndReport/2026-05-13T14-46-20+0800_P0-Exactly-One-Controlled-Upload-Validation-After-Task-87-Deployment_REPORT.md`

Decision:
`ACCEPTED_FAILED_VALIDATION_EVIDENCE_WITH_TWO_FOLLOW_UPS`

## Summary

Director accepts the TestAcceptanceEngineer report as valid failed-validation evidence.

The controlled upload did not pass end-to-end. However, it narrowed the failure surface materially:

- the previous 30-second Ollama `UND_ERR_HEADERS_TIMEOUT` did not recur;
- Ollama produced real responses, including one successful JSON repair path;
- MinerU completed and stored 21 parsed artifacts;
- task/material records now expose MinerU progress semantics or diagnostics;
- final task/material state still failed at AI;
- meaningful page/batch MinerU business progress was not observed.

This is not production readiness, L3, pressure PASS, or release readiness.

## Evidence Reviewed

TestAcceptanceEngineer reported:

- exactly one authorized upload of `/Users/concm/prod_workspace/Luceon2026/testpdf/2025_2026学年春季课程中数G8_提取.pdf`;
- sample size `530205` bytes and SHA-256 `71b95d983cdf73507c7334d3682f117f1dfce454286a6bb9f60d437a070b3cfb`;
- created task `task-1778655375028`;
- created material `validation-postfix-1778655374`;
- MinerU task `5cc6acce-061f-4418-a29b-b862af8306a6`;
- AI job `ai-job-1778655391785-6d94`;
- MinerU completed and wrote `parsedFilesCount=21`;
- task page showed AI running and terminal failed states;
- task list showed MinerU diagnostic text;
- no second upload, pressure test, failed-task repair, cleanup, destructive operation, model operation, broad restart, L3, pressure PASS, release-readiness claim, or sample mutation.

Director independently rechecked production read-only:

- upload health remained ok;
- dependency health with Ollama chat probe returned `ok=true`, `blocking=false`;
- admission circuit remained `closed`;
- active-task diagnostics had no active/current/queued/takeover-required work;
- historical AI failures included the new `task-1778655375028` and prior `task-1778651226016`;
- Ollama `/api/ps` still listed resident `qwen3.5:9b`;
- task `task-1778655375028` was `state=failed`, `stage=ai`, `progress=100`;
- material `validation-postfix-1778655374` was `status=failed`, `mineruStatus=completed`, `aiStatus=failed`;
- task metadata included `aiClassificationProvider=ollama`, `aiClassificationRepairSucceeded=true`, `aiClassificationV02`, and parsed artifact pointers;
- AI job `ai-job-1778655391785-6d94` was `state=failed`;
- task events showed one Ollama response success, one JSON repair success, then a second Ollama response and JSON repair failure on the same AI job.

## Director Interpretation

The original Task 87 target was partly effective:

- `UND_ERR_HEADERS_TIMEOUT` no longer appears in this validation.
- The AI provider can now stay alive long enough to return real results.
- MinerU parse and artifact ingestion are not the blocker for this sample.

The remaining P0 blocker appears to be AI metadata worker finalization consistency. The same AI job has evidence of a successful classification/repair path and then a later terminal failure. A quick code inspection found a plausible duplicate-processing path in `server/services/ai/metadata-worker.mjs`: `scanAndProcess()` processes a pending job from `postRecoveryJobs`, then continues to process pending jobs from the stale pre-recovery `jobs` snapshot. DevelopmentEngineer must independently verify this before fixing, but the runtime trace is consistent with one AI job being processed twice in one scan cycle.

The MinerU progress issue is now more precise:

- the API/task page is no longer blind;
- it surfaced a diagnostic, not meaningful page/batch progress;
- the production log source was reported as unreadable or empty;
- task and material metadata disagree on the final diagnostic level: task remained `log-observation-unreadable`, while material had `fast-complete-no-business-signal`.

This should be treated as a separate observability/ownership problem, not as the same P0 AI terminal blocker.

## Boundary

Accepted:

- exactly-one-upload validation evidence;
- Task 87 timeout fix partially confirmed;
- MinerU parse/artifact path confirmed for this sample;
- AI terminal failure and MinerU diagnostic limitations confirmed.

Not accepted:

- end-to-end pass;
- meaningful page/batch MinerU progress;
- production release readiness;
- L3;
- pressure PASS.

Not authorized:

- second upload;
- pressure retry/test;
- failed-task repair, reparse, re-AI, deletion, or cleanup;
- DB/MinIO/Docker volume/data mutation;
- model pull/delete/replace/reload;
- broad restart/rollback.

## Follow-Up Tasks Issued

1. `TASK-20260513-151715-P0-AI-Metadata-Single-Pass-Finalization-Guard`
   - Assignee: `DevelopmentEngineer`
   - Goal: fix the AI metadata worker duplicate-processing / terminal-state consistency blocker at code/test level.

2. `TASK-20260513-151715-P1-MinerU-Progress-Diagnostic-And-Log-Source-Ownership-Review`
   - Assignee: `Architect`
   - Goal: produce a read-only architecture/ops analysis and implementation plan for log-source unreadability, task/material diagnostic mismatch, and task-page progress semantics.

No new production deployment or validation upload is authorized by this review.
