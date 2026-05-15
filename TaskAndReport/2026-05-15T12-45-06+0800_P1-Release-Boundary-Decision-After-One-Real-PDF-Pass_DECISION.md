# User Decision Required: P1 Release Boundary Decision After One Real PDF Pass

- Task ID: `TASK-20260515-124506-P1-Release-Boundary-Decision-After-One-Real-PDF-Pass`
- Created: 2026-05-15T12:45:06+0800
- Created by: Director
- Next Actor: `User`
- Based on TestAcceptanceEngineer report: `TaskAndReport/2026-05-15T12-32-50+0800_P1-One-Real-PDF-Post-Recovery-Validation_REPORT.md`
- Based on Director review: `TaskAndReport/2026-05-15T12-45-06+0800_P1-One-Real-PDF-Post-Recovery-Validation_DIRECTOR_REVIEW.md`

## Current State

The one authorized real PDF post-recovery validation passed its boundary:

- one small real PDF was uploaded;
- MinerU completed;
- Ollama AI metadata completed;
- task reached `review-pending`;
- material reached `reviewing`;
- active-task diagnostics returned clean after completion.

This evidence removes the prior "no fresh real PDF after MinerU recovery" limitation.

## Remaining Limitations

- Only one small real PDF was validated after recovery.
- No pressure/batch/soak/large-file run was performed in this task.
- No rollback/restore/failure-injection rehearsal has been performed.
- The deployment remains local/single-machine, with MinerU, Ollama, Docker/MinIO, DB, upload-server, and frontend sharing one host.
- Historical `failed/ai` tasks remain visible manual retry candidates.
- Production workspace remains intentionally dirty/local because of override/source-boundary files.
- PDF upload path internally performs a MinerU admission submit-probe by design; this is now recorded and should be reflected in future task wording.

## Options

### Option A: Accept Conditional Release Boundary

Accept `CONDITIONAL_GO_WITH_EXPLICIT_LIMITATIONS` for the current local/single-machine production deployment boundary.

This means:

- the main path has enough evidence for limited operator-facing use under explicit limitations;
- manual review remains required for AI metadata;
- historical AI failures remain visible retry candidates;
- rollback/failure-injection and broader pressure evidence are not claimed;
- this is not HA readiness, L3, pressure PASS, unrestricted production go-live, or external/multi-user rollout approval.

### Option B: Require Rollback/Recovery Rehearsal First

Authorize a separate, carefully scoped rollback/recovery rehearsal before accepting any release boundary. This should be designed with explicit blast-radius limits and may require additional user approval depending on the planned actions.

### Option C: Require More Real-PDF Validation First

Authorize a further bounded validation, such as a strict serial small set or a medium/large PDF, before deciding.

### Option D: Hold / No-Go

Do not accept a release boundary now. Record no-go/hold pending further implementation or operational hardening.

## Director Recommendation

For the current local/single-machine deployment boundary, choose Option A if you accept the limitations above.

Choose Option B if your standard for "production" requires rollback/recovery rehearsal before operator-facing use.
