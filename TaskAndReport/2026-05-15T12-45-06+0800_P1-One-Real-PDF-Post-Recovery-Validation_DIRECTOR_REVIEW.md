# Director Review: P1 One Real PDF Post-Recovery Validation

- Task ID: `TASK-20260515-123250-P1-One-Real-PDF-Post-Recovery-Validation`
- Reviewed report: `TaskAndReport/2026-05-15T12-32-50+0800_P1-One-Real-PDF-Post-Recovery-Validation_REPORT.md`
- Review time: 2026-05-15T12:45:06+0800
- Reviewer: `Director`
- Result: `ACCEPTED_ONE_REAL_PDF_REVIEW_READY_WITH_BOUNDARY_NOTE`

## Judgment

Accepted.

The one authorized real PDF post-recovery validation reached manual review state. This closes the specific Task 178 limitation that no fresh real PDF had been run after MinerU submit-path recovery and no-submit helper sync.

This is not pressure PASS, L3, release-readiness, production-readiness, production上线, or go-live approval.

## Evidence Reviewed

Selected source PDF:

- `/Users/concm/prod_workspace/Luceon2026/testpdf/向树叶学习：人工光合作用.pdf`
- size: `86884` bytes
- SHA-256: `2230acbb40524e1de80f1ebe57a13c5f41db353e15c6727f5ebb97383154e16c`

Created production records:

- task: `task-1778819826484`
- material: `mat-1778819825152`
- MinerU task: `d57e4095-ef63-41b2-b060-35fda4ac5db1`
- AI job: `ai-job-1778819849438-1c43`

Director read-only spot-check confirmed:

- DB task `task-1778819826484`:
  - `state=review-pending`;
  - `stage=review`;
  - `progress=100`;
  - `message=AI 识别完成: review-pending (待人工复核)`.
- DB material `mat-1778819825152`:
  - `status=reviewing`;
  - `mineruStatus=completed`;
  - `aiStatus=analyzed`.
- Direct MinerU task `d57e4095-ef63-41b2-b060-35fda4ac5db1`:
  - `status=completed`;
  - `error=null`;
  - `backend=pipeline`;
  - file name `向树叶学习：人工光合作用`.
- AI job `ai-job-1778819849438-1c43`:
  - `state=review-pending`;
  - `progress=100`;
  - `providerId=ollama`;
  - `model=qwen3.5:9b`;
  - `message=AI 识别完成 (61563ms)`;
  - `needsReview=true`.
- Current runtime read-only checks:
  - dependency-health without submit-probe `ok=true`, `blocking=false`;
  - active-task diagnostics clean;
  - direct MinerU `/health` healthy;
  - admission circuit closed;
  - known historical `failed/ai` tasks remain visible.

## Boundary Note

The task brief forbade manual or extra submit-probe actions. TestAcceptanceEngineer did not manually call `dependency-health?mineruSubmitProbe=true`, did not run `RUN_MINERU_SUBMIT_PROBE=1`, and did not run the helper with `--submit-probe`.

However, the production non-Markdown/PDF upload route itself performs an internal MinerU admission check with `mineruSubmitProbe: true` before accepting the PDF. That is part of the authorized real PDF upload path and should not be recorded as tester scope breach.

Runtime evidence shows the internal admission probe:

- `lastSubmitProbe.taskId=a9c55f8a-10c0-440c-97f0-ab5098155a7a`;
- probe file name `luceon-health-probe`;
- probe status `completed`;
- admission circuit remained `closed`.

Future task wording should say "no separate/manual submit-probe outside the authorized PDF upload path" when a real non-Markdown upload is authorized.

## Remaining Limitations

- Only one small real PDF was validated after recovery.
- This is not pressure, batch, soak, large-file, L3, rollback/failure-injection, or HA evidence.
- The small-file MinerU log observer still produced a stale/fast-complete diagnostic note before terminal success; this is an observability limitation, not a blocker for this validation.
- AI metadata is review-ready with low confidence/manual review required, not automatically accepted catalog metadata.
- Historical `failed/ai` tasks remain visible and were not repaired or retried.
- Production remains a local/single-machine stack with known local dirty/override files.

## Next Step

Record a User decision row for release-boundary disposition after the successful one-real-PDF post-recovery validation.

Director recommendation: accept conditional release-boundary status for the current local/single-machine deployment only if the User accepts the listed limitations. If the User wants stronger operational assurance, run a separately scoped rollback/recovery rehearsal before acceptance.
