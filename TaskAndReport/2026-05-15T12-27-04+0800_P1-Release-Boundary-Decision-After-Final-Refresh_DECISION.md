# User Decision Required: P1 Release Boundary Decision After Final Refresh

- Task ID: `TASK-20260515-122704-P1-Release-Boundary-Decision-After-Final-Refresh`
- Created: 2026-05-15T12:27:04+0800
- Created by: Director
- Next Actor: `User`
- Based on Architect report: `TaskAndReport/2026-05-15T12-17-39+0800_P1-Release-Readiness-Final-Refresh-After-MinerU-Recovery-And-Helper-Sync_REPORT.md`
- Based on Director review: `TaskAndReport/2026-05-15T12-27-04+0800_P1-Release-Readiness-Final-Refresh-After-MinerU-Recovery-And-Helper-Sync_DIRECTOR_REVIEW.md`

## Current State

Architect recommends `CONDITIONAL_GO_WITH_EXPLICIT_LIMITATIONS`.

Director accepts that recommendation as a decision-ready status, not as a production-readiness declaration.

Current accepted positives:

- pressure-result semantics are corrected and accepted;
- known pressure-window `failed/ai` tasks are visible manual retry candidates, not hidden or counted as success;
- dependency-health timing semantics are deployed and accepted;
- production source drift/local override is classified and disclose-only;
- MinerU submit-path HTTP 500 blocker was recovered by scoped MinerU-only recovery;
- admission circuit is currently closed and active-task diagnostics are clean;
- no-submit helper hazard is fixed and synced to production source.

Current limitations:

- no fresh real PDF upload has been run after MinerU recovery;
- no rollback/restore/failure-injection rehearsal has been run;
- deployment remains a local/single-machine stack with MinerU, Ollama, Docker/MinIO, and app services sharing resources;
- historical `failed/ai` tasks remain visible;
- production workspace intentionally has local dirty/override files.

## Options

### Option A: Accept Conditional Go With Explicit Limitations

Accept the current state as enough for a conditional release-boundary decision in the current local/single-machine deployment context.

Director would record the accepted limitations and proceed to a release-boundary closure record. This still would not mean L3, pressure PASS, HA readiness, rollback readiness, or unrestricted production go-live.

### Option B: One Real PDF Post-Recovery Validation First

Recommended for higher confidence before any production-use acceptance.

Authorize `TestAcceptanceEngineer` to run exactly one controlled real PDF upload after MinerU recovery and no-submit helper sync, using the existing production sample source, then observe it to terminal state or clear failure.

Strict scope:

- exactly one PDF;
- no pressure/batch/soak;
- no cleanup/repair/retry/reparse/re-AI;
- no submit-probe unless the task explicitly requires and separately authorizes it;
- stop on dependency blocking or admission circuit open;
- no readiness/go-live claim by the tester.

### Option C: Rollback/Recovery Rehearsal First

Authorize a separately scoped rehearsal plan before any release-boundary acceptance. This should be designed carefully because rollback/failure-injection can carry blast-radius risk.

### Option D: Hold / No-Go

Do not move toward release-boundary acceptance yet. Record `NO_GO` pending further implementation or operational hardening.

## Director Recommendation

Choose Option B if the next step is meant to support real operator-facing use. It is the smallest remaining confidence check after the MinerU submit-path recovery and avoids accepting a release boundary without any real post-recovery PDF.

Choose Option A only if you explicitly accept the limitations above.

## User Decision

User approved Option B in-thread at `2026-05-15T12:32:50+0800`:

> 同意选 Option B，做一个最小真实 PDF 验证

Director will issue a scoped `TestAcceptanceEngineer` task for exactly one real PDF post-recovery validation. This decision does not authorize pressure/batch/soak testing, submit-probe, cleanup, repair, retry/reparse/re-AI, production deployment/restart, or any readiness/go-live claim.
