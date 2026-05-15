# Decision: P1 AI Residual Release Boundary

- Decision ID: `TASK-20260515-100418-P1-AI-Residual-Release-Boundary-Decision`
- Created: 2026-05-15T10:04:18+0800
- Created by: Director
- Current owner: User
- Related review: `TaskAndReport/2026-05-15T10-04-18+0800_P1-Dependency-Health-Timing-Semantics-Production-Deployment-And-Read-Only-Validation_DIRECTOR_REVIEW.md`

## Current Facts

- Pressure-semantics production behavior was accepted earlier: the recent 24-task pressure window is no longer treated as systemic/whole-run failure.
- The accepted pressure-window interpretation is mixed outcome:
  - `21` tasks reached `review-pending/review`;
  - `3` tasks remained `failed/ai`.
- Those `failed/ai` tasks are now classified as AI residuals/manual retry candidates, not MinerU parse failure and not whole-system failure.
- Task 164 dependency-health timing semantics were accepted at code/test level.
- Task 166 production deployment/read-only validation is accepted: production exposes the new Ollama readiness/timing fields and dependency-health is currently non-blocking.
- No repair, retry, reparse, re-AI, cleanup, upload, pressure rerun, or destructive mutation has been authorized or performed for those residual `failed/ai` tasks.
- No pressure PASS, L3, release-readiness, production-readiness, production上线, or go-live readiness has been declared.

## Decision Needed

How should known `failed/ai` residual tasks be treated for the next release-readiness decision?

## Options

### Option A: Accept Known AI Residuals As Manual Retry Candidates (Director Recommended)

Accept that a small number of visible `failed/ai` residuals may remain as manual retry candidates for this release-readiness track, provided the UI/task semantics do not flatten them into success and do not hide them.

This option means:

- the known pressure-window AI residuals do not block moving to rollback/error-path evidence;
- they are not counted as systemic pressure failure;
- they remain visible as failed AI/manual retry candidates;
- no automatic repair/retry/reparse/re-AI is authorized;
- no release-readiness or go-live claim is made by this decision alone.

Why recommended:

- The user has already clarified that a few AI recognition failures among 24 tasks should not make the whole run failed, especially when large files mostly succeeded.
- The system now exposes these failures as AI residuals instead of hiding them or misclassifying them as MinerU/system failure.
- Requiring repair before moving on would mix product policy with data mutation and could stall release-readiness evidence gathering.

### Option B: Require Repair Or Retry Before Release-Readiness Decision

Require the known `failed/ai` residuals to be manually retried/repaired before any release-readiness decision can proceed.

Impact:

- This would require a separate explicitly authorized task because retry/repair/re-AI is currently forbidden.
- It may produce useful evidence, but it changes existing runtime data and can mask whether the system's normal residual-handling policy is acceptable.

### Option C: Hold And Ask For More Product Analysis

Pause and ask for a ProductManager-style analysis before choosing whether AI residuals are acceptable.

Impact:

- This avoids an immediate policy decision, but the project remains blocked at the same release-readiness boundary.
- It is useful only if the user wants a fuller written policy before deciding.

## Director Recommendation

Choose Option A.

This is the most conservative operational route because it does not mutate production data and does not pretend failed AI tasks succeeded. It treats AI residuals as visible operator work items while allowing the next blocker, rollback/error-path evidence, to be addressed.

Because this is an owner-level product/release boundary, Director should not auto-accept Option A as a release fact without user approval. The heartbeat auto-progress rule may be used only to record continued waiting or to move to a read-only analysis task, not to declare that residual AI failures are release-acceptable.

## User Decision

Pending.

## Not Authorized By This Decision Row

No upload, pressure/batch/soak/fresh serial validation, cleanup/cancel/repair/retry/reparse/re-AI, destructive DB/MinIO/Docker volume/data mutation, Docker down/volume cleanup/prune, broad service restart/rollback, MinerU/Ollama/supervisor mutation, settings/secrets/config/model/sample mutation, automatic retry/requeue, skeleton fallback weakening, pressure PASS, L3, release-readiness, production-readiness, production上线, or go-live claim is authorized by this decision row.
