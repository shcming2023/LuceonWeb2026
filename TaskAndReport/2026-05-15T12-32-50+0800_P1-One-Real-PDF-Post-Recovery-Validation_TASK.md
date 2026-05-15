# Task Brief: P1 One Real PDF Post-Recovery Validation

- Task ID: `TASK-20260515-123250-P1-One-Real-PDF-Post-Recovery-Validation`
- Created: 2026-05-15T12:32:50+0800
- Created by: Director
- Assigned role: `TestAcceptanceEngineer`
- Expected report: `TaskAndReport/2026-05-15T12-32-50+0800_P1-One-Real-PDF-Post-Recovery-Validation_REPORT.md`
- Based on user decision: `TaskAndReport/2026-05-15T12-27-04+0800_P1-Release-Boundary-Decision-After-Final-Refresh_DECISION.md`
- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production workspace: `/Users/concm/prod_workspace/Luceon2026`
- Test PDF source: `/Users/concm/prod_workspace/Luceon2026/testpdf`

## Context

Task 177 accepted the Architect recommendation `CONDITIONAL_GO_WITH_EXPLICIT_LIMITATIONS`, but one important limitation remains: no fresh real PDF upload has been run after the MinerU submit-path recovery and no-submit helper sync.

The user chose Option B: perform one minimal real PDF post-recovery validation before any release-boundary acceptance.

## Required Reading

Before acting, read:

1. `AGENTS.md`
2. `docs/codex/TEAM_CONTRACT.md`
3. `docs/codex/roles/test-acceptance-engineer.md`
4. `docs/codex/PROJECT_STATE.md`
5. `docs/codex/HANDOFF.md`
6. `docs/prd/Luceon2026-PRD-v0.4.md`
7. `docs/codex/TEST_POLICY.md`
8. `docs/codex/REPOSITORY_STRUCTURE.md`
9. `TaskAndReport/README.md`
10. `TaskAndReport/TASK_TRACKING_LIST.md`
11. Task 173, 176, and 177 reports/reviews
12. Task 178 decision
13. This task brief

If the task row, role file, or required evidence files are missing locally, stop and report `本地任务列表或角色文档未更新/疑似不同步`.

## Objective

Run exactly one controlled real PDF validation after MinerU recovery:

1. choose one small/medium PDF from `/Users/concm/prod_workspace/Luceon2026/testpdf`;
2. upload exactly that one PDF to production CMS;
3. observe it through terminal state or bounded timeout;
4. report whether the real path reaches review/manual-ready state, fails, blocks, or remains non-terminal.

This is not pressure testing and not release readiness approval.

## Allowed Operations

Allowed:

- read development and production task/docs/status files;
- list PDFs under `/Users/concm/prod_workspace/Luceon2026/testpdf` read-only;
- select exactly one small/medium PDF, record path, file size, and SHA-256;
- run preflight read-only checks:
  - upload health;
  - dependency-health without submit-probe;
  - MinerU admission circuit state;
  - active-task diagnostics;
  - direct MinerU `/health`;
- upload exactly one selected PDF through the production CMS UI or documented production upload path;
- observe the resulting Luceon task/material through UI and read-only HTTP/API endpoints;
- observe task page progress semantics and whether MinerU/AI progress is understandable to an operator;
- poll until one of these outcomes:
  - review/manual-ready success;
  - explicit failed state;
  - dependency/admission blocked;
  - observation timeout with evidence of current state;
- write the report and update this task row.

## Required Stop Conditions

Stop and write a blocked report before upload if:

- dependency-health without submit-probe is `blocking=true`;
- MinerU admission circuit is open;
- active-task diagnostics show active parse/AI work, queued parse work, or takeover-required work;
- direct MinerU `/health` is unhealthy;
- the `testpdf` directory is missing or has no suitable PDF;
- selecting/uploading exactly one PDF is not possible without broader cleanup or mutation.

Stop after upload and report if:

- upload creates more than one task or artifact unexpectedly;
- the system asks for cleanup, repair, retry, reparse, re-AI, service restart, or submit-probe;
- the run reaches a systemic blocker or service unreachable state.

## Forbidden Operations

Forbidden:

- more than one PDF upload;
- pressure/batch/soak/fresh serial validation beyond this one PDF;
- `mineruSubmitProbe=true`, `RUN_MINERU_SUBMIT_PROBE=1`, `--submit-probe`, or any submit-probe action;
- cleanup, cancel, repair, retry, reparse, re-AI, takeover, automatic retry/requeue, or historical task mutation;
- production deploy, source sync, pull/fast-forward, rebuild, rollback, Docker Compose, Docker restart/down/down-v/prune, service restart, MinerU/Ollama/supervisor/sidecar mutation;
- DB/MinIO/Docker volume/data mutation, restore/import, object deletion/overwrite;
- settings, secrets, config, model, sample-library mutation;
- PRD truth, role contract, project state, or handoff changes;
- skeleton fallback weakening or silent degradation;
- declaring pressure PASS, L3, release-readiness, production-readiness, production上线, or go-live readiness.

## Observation Boundary

Use a bounded observation window appropriate for one small/medium PDF. Suggested maximum: 45 minutes after upload unless terminal state is reached earlier.

If the task is still running at timeout, do not call it pass or fail. Report `OBSERVATION_TIMEOUT_NON_TERMINAL` with current UI/API/MinerU evidence and whether logs show progress.

## Required Report Structure

The report must include:

1. **Preflight**
   - dependency-health without submit-probe;
   - admission circuit;
   - active-task diagnostics;
   - direct MinerU `/health`;
   - confirmation that no submit-probe was run.

2. **Selected PDF**
   - absolute path;
   - size;
   - SHA-256;
   - why this sample qualifies as small/medium.

3. **Upload Evidence**
   - exact upload method;
   - created task/material identifiers;
   - confirmation exactly one PDF was uploaded.

4. **Progress And Terminal Evidence**
   - task page/operator-facing semantics;
   - backend task/material state;
   - MinerU/AI stage evidence;
   - final or timeout state.

5. **Outcome**
   - one of:
     - `ONE_REAL_PDF_REVIEW_READY`;
     - `ONE_REAL_PDF_FAILED`;
     - `BLOCKED_BEFORE_UPLOAD`;
     - `BLOCKED_AFTER_UPLOAD`;
     - `OBSERVATION_TIMEOUT_NON_TERMINAL`;
     - `VALIDATION_SCOPE_BREACH_STOPPED`.

6. **Release-Boundary Impact**
   - what this evidence adds or fails to add to Task 178.

7. **Forbidden Operations Confirmation**

## Completion

Write:

`TaskAndReport/2026-05-15T12-32-50+0800_P1-One-Real-PDF-Post-Recovery-Validation_REPORT.md`

Update row 179 in `TaskAndReport/TASK_TRACKING_LIST.md`:

- Status: `已回报待 Director 审查` or a precise blocked status;
- Next Actor: `Director`;
- Report path populated;
- Notes include outcome, selected PDF, created task/material ids, and whether terminal state was reached.

## GitHub Sync

Do not fetch, pull, push, merge, or create commits unless Director explicitly instructs you. Work in the current synchronized workspace. Director will review and handle GitHub synchronization.
