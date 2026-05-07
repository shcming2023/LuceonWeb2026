# Lucia Task Brief

Task ID: `TASK-20260507-131426-P1-AI-Deterministic-Repair-UI-And-Ops-Status-Semantics`

Task name: P1 AI Deterministic Repair UI And Ops Status Semantics

Issued at: `2026-05-07T13:14:26+0800`

Issuer: Lucia

Assignee: Lucode

Priority: P1

## Background

Production manual review showed that a task could display AI recognition as blocked or impeded even though the AI job completed with provider `ollama`, model `qwen3.5:9b`, and deterministic repair succeeded.

Observed task: `task-1778130398304`.

Accepted AI facts:

- AI job `ai-job-1778130435700-d611` reached `review-pending`.
- Provider/model: `ollama` / `qwen3.5:9b`.
- `aiClassificationTwoPassAttempted=true`.
- `aiClassificationDeterministicRepairSucceeded=true`.
- `aiClassificationRepairSucceeded=true`.
- No skeleton provider was used.
- The correct operator meaning is: AI completed with deterministic normalization and needs review. It is not an AI dependency block.

Related ops-status fact:

- `/ops/dependency-repair/status` can show `sessions.ollama=false` while `services.ollamaReachable=true`.
- UI must not turn a missing tmux session into an AI dependency failure when the service is reachable and dependency health is green.

## Objective

Align UI and diagnostics semantics so deterministic repair success and reachable-but-unmanaged Ollama are represented accurately to the operator.

## Non-Goals

- Do not change AI metadata extraction logic.
- Do not change deterministic repair behavior.
- Do not change strict no-skeleton behavior.
- Do not change MinerU parsing, MinIO storage, production runtime config, or task terminal states.
- Do not claim release readiness.

## Allowed Files, Modules, Or Operations

- Frontend task detail/list/status components that render AI job state or dependency warnings.
- Frontend dependency health / repair status components.
- Focused UI/unit smoke tests under `uat/` or `server/tests/` if applicable.
- `TaskAndReport/` report and tracking-list updates.

If backend fields are missing for a precise UI distinction, Lucode may propose a narrow backend field addition, but must keep it scoped and covered by tests.

## Required Work

1. Locate where the UI currently labels AI recognition as blocked, impeded, or unavailable.
2. Ensure the following state is displayed as completed/review-needed, not blocked:
   - `state=review-pending`
   - `provider=ollama`
   - `aiClassificationDeterministicRepairSucceeded=true`
   - `aiClassificationRepairSucceeded=true`
3. Distinguish:
   - AI dependency unreachable or provider failure
   - AI strict failure without skeleton
   - AI deterministic repair success with review required
   - low confidence / taxonomy review required
4. Split ops-session warnings from service dependency failures:
   - `services.ollamaReachable=true` should not be displayed as Ollama dependency failure only because `sessions.ollama=false`.
5. Add focused regression evidence for the rendering or status mapping.

## Forbidden Changes

- Do not use broad wording that hides real AI failures.
- Do not make failed AI jobs look successful.
- Do not remove dependency-health warnings; classify them accurately.
- Do not use `.skip`, assertion weakening, or mocked success that does not cover the accepted state.

## Required Checks

Lucode must run and report exit codes for:

```bash
git status --short --branch
git fetch origin
git pull --ff-only origin main
npx pnpm@10.4.1 exec tsc --noEmit
npx pnpm@10.4.1 run build
BASE_URL=http://localhost:8081 bash uat/smoke-test.sh
git diff --check
```

If UI/UAT tests are added or updated, run and report them.

## Required Evidence

- Files changed.
- Exact status-mapping decision table or equivalent summary.
- Test evidence showing deterministic repair success is not displayed as AI blocked.
- Test evidence showing actual AI dependency failure still displays as a warning/failure.
- Confirmation that no AI backend behavior, strict mode, production DB, MinIO, or runtime state was changed.

## GitHub Sync Requirements

- Use branch `lucode/p1-ai-deterministic-repair-ui-ops-semantics`.
- Commit and push branch if repository files are changed.
- Store completion report under `TaskAndReport/`.
- Update `TaskAndReport/TASK_TRACKING_LIST.md` with report path, branch, HEAD, status, next actor, next action, and required output.
- Do not merge before Lucia review.

## Acceptance Criteria

- Deterministic repair success is shown as completed/review-needed, not AI blocked.
- Reachable Ollama with missing tmux session is shown as an ops-session warning, not an AI dependency outage.
- Real AI dependency failure remains visible.
- Build/type checks and relevant smoke tests pass.
