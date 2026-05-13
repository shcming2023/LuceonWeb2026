# Task: P0 Post-Validation Ollama And MinerU Progress Blockers

Assignee:
DevelopmentEngineer

Issued by:
Director

Project:
Luceon2026

Development workspace:
/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026

Production deployment path:
/Users/concm/prod_workspace/Luceon2026

GitHub:
https://github.com/shcming2023/Luceon2026

TaskAndReport record:
TaskAndReport/2026-05-13T13-58-10+0800_P0-Post-Validation-Ollama-And-MinerU-Progress-Blockers_TASK.md

## Required Reading Before Execution

- AGENTS.md
- docs/codex/TEAM_CONTRACT.md
- docs/codex/roles/development-engineer.md
- docs/codex/PROJECT_STATE.md
- docs/codex/HANDOFF.md
- docs/prd/Luceon2026-PRD-v0.4.md
- docs/codex/TEST_POLICY.md
- docs/codex/TEST_MATRIX.md
- docs/codex/REPOSITORY_STRUCTURE.md
- docs/deploy/PRODUCTION_RUNTIME_OWNERSHIP.md
- TaskAndReport/README.md
- TaskAndReport/TASK_TRACKING_LIST.md
- TaskAndReport/2026-05-13T13-41-16+0800_P0-Controlled-Live-Task-Progress-Semantics-Validation-With-Prod-Testpdf-Source_TASK.md
- TaskAndReport/2026-05-13T13-41-16+0800_P0-Controlled-Live-Task-Progress-Semantics-Validation-With-Prod-Testpdf-Source_REPORT.md
- TaskAndReport/2026-05-13T13-58-10+0800_P0-Controlled-Live-Task-Progress-Semantics-Validation-With-Prod-Testpdf-Source_DIRECTOR_REVIEW.md

## Background

Task 86 executed exactly one authorized production upload from:

`/Users/concm/prod_workspace/Luceon2026/testpdf/2025_2026学年春季课程中数G8_提取.pdf`

The run proved that the corrected sample source is usable and that MinerU can parse/store artifacts for this sample, but it failed the validation objective:

- task `task-1778651226016`
- material `validation-progress-1778651225`
- MinerU completed and stored `21` parsed artifacts.
- API observation did not show `task.metadata.mineruObservedProgress`.
- API observation did not show `task.metadata.mineruObservedProgress.progressSemantics`.
- AI terminal state was `failed`.
- Two Ollama provider attempts failed at about `30s` with `UND_ERR_HEADERS_TIMEOUT`, while the job-level provider timeout was `180000ms`.
- Strict no-skeleton behavior was preserved and must remain preserved.

## Current Known Facts

Director rechecked the production task and events read-only:

- final task state: `failed / ai / 100`;
- final material state: `failed`, `mineruStatus=completed`, `aiStatus=failed`;
- task metadata includes parsed artifact fields but no `mineruObservedProgress`;
- material metadata includes only generic `progressEventKey=...logStatus=missing...`;
- task events show provider `ollama`, model `qwen3.5:9b`, base URL `http://host.docker.internal:11434`, input length `3240`, timeout `180000ms`;
- both Ollama failures report `errorCauseCode=UND_ERR_HEADERS_TIMEOUT` at roughly `30s`;
- current provider code in `server/services/ai/providers/ollama.mjs` uses undici `Agent({ headersTimeout: 30000, bodyTimeout: this.timeoutMs })`;
- current progress observation logic can leave fast completed tasks with no `mineruObservedProgress`, which gives the operator no explicit explanation on the task page.

## Objective

Implement scoped code and test fixes for the two observed blockers:

1. Ollama runtime timeout contract:
   - real non-streaming `/api/chat` metadata inference must not be unintentionally capped by a hard 30-second `headersTimeout`;
   - provider errors must still remain bounded, classified, and visible in raw task events;
   - strict no-skeleton failure semantics must be preserved.

2. MinerU progress semantics visibility:
   - task API/UI state must expose truthful operator-facing progress semantics when structured MinerU log progress exists;
   - when a fast completed task has no captured business progress signal, the system must expose a structured, provenance-bearing diagnostic instead of silently omitting `mineruObservedProgress`;
   - do not invent fake page/batch progress. If no business signal was observed, say so structurally and safely.

## Non-Goals

- Do not perform production deployment.
- Do not perform a validation upload.
- Do not repair, retry, reparse, re-AI, or clean up task `task-1778651226016` or any historical task.
- Do not run pressure tests or 24-PDF retry.
- Do not change the required model name.
- Do not pull, delete, replace, reload, or mutate Ollama models.
- Do not change secrets, production overrides, DB schema, MinIO data, Docker volumes, PRD truth, role contracts, or release judgments.
- Do not relax strict no-skeleton semantics.
- Do not represent skeleton fallback as real AI recognition.

## Allowed Files, Modules, Or Operations

Allowed code areas:

- `server/services/ai/providers/ollama.mjs`
- AI metadata worker/provider timeout details only if needed:
  - `server/services/ai/metadata-worker.mjs`
  - related tests under `server/tests/`
- MinerU progress observation and task-view utility paths only if needed:
  - `server/services/mineru/local-adapter.mjs`
  - `server/services/mineru/v4-online-adapter.mjs`
  - `server/upload-server.mjs`
  - `server/lib/ops-mineru-log-parser.mjs`
  - `server/lib/ops-mineru-diagnostics.mjs`
  - `src/app/utils/taskView.ts`
  - relevant UI components/pages only if the backend state already contains the new truthful diagnostic and the UI must display it.
- Focused smoke tests under `server/tests/`.
- Task completion report and ledger row.

If another file is required, explain why in the report and keep the change narrowly tied to this task.

## Forbidden Changes

- Do not start from vague oral instructions or self-created tasks.
- Do not broaden scope beyond this task brief.
- Do not perform broad rewrites or framework-level refactors.
- Do not change unrelated files.
- Do not change PRD truth, project ledger facts, role contracts, or release judgments except the assigned task row/report.
- Do not commit secrets, tokens, local private credentials, or machine-only artifacts.
- Do not run destructive production, MinIO, DB, Docker volume, model, or data cleanup commands.
- Do not restore deprecated heuristic chapter-preprocessing logic as a main path.
- Do not configure silent degradation for required parsing, preprocessing, or AI recognition paths.
- Do not claim UAT, L2, L3, production readiness, pressure PASS, or release readiness.
- Do not copy local sample files into the repository.

## Suggested Direction

For Ollama:

- Treat `UND_ERR_HEADERS_TIMEOUT` around 30 seconds as a bug in the provider's runtime timeout contract for non-streaming `/api/chat`.
- Prefer making the request headers timeout configurable and aligned with the actual provider call deadline for metadata inference, while preserving a shorter dependency-health smoke timeout.
- Ensure error details still include `timeoutKind`, `headersTimeoutMs`, `bodyTimeoutMs`, `durationMs`, provider, model, and base URL.
- Update stale tests that currently assert a hardcoded `30000` provider headers timeout if that value no longer reflects the real production contract.

For MinerU progress semantics:

- Preserve real parsed log semantics when available.
- If the task completes before a useful log snapshot can be attributed, persist a structured diagnostic observation that explains the absence of business progress signal, with enough provenance for the task page to tell the operator what happened.
- The diagnostic must be clearly different from real page/batch progress and must not fabricate batch, page, or phase data.
- Keep absolute host log paths out of UI-safe fields.
- Add or update focused tests for:
  - fast-complete/no-business-signal observation;
  - useful progress semantics when parser data exists;
  - no post-terminal misleading mutation;
  - UI/task-view line for the new diagnostic if UI code changes.

## Required Checks

Run all checks that apply to changed files. Minimum expected set:

```bash
git diff --check
node --check server/services/ai/providers/ollama.mjs
node server/tests/ai-metadata-real-sample-smoke.mjs
node server/tests/dependency-health-smoke.mjs
node server/tests/mineru-log-progress-smoke.mjs
node server/tests/mineru-diagnostics-smoke.mjs
npx pnpm@10.4.1 exec tsc --noEmit
npx pnpm@10.4.1 run build
```

If you touch additional server files, run `node --check` on them.

If a required check cannot run, report the exact command, exit code or failure reason, and whether it is environmental or caused by the patch.

## Required Evidence

The completion report must include:

- confirmation that work was based on this Director task brief;
- branch and HEAD;
- files changed;
- implementation summary for Ollama timeout behavior;
- implementation summary for MinerU progress semantics/diagnostic behavior;
- before/after explanation of the `headersTimeoutMs` and `bodyTimeoutMs` contract;
- test evidence proving strict no-skeleton behavior remains intact;
- test evidence proving progress semantics are not silently omitted for fast completed tasks;
- commands run with exit codes;
- skipped checks and exact reasons;
- risks and residual debt;
- GitHub sync status;
- whether a follow-up TestAcceptanceEngineer production validation task is required.

## GitHub Sync Requirements

- Before starting repository-changing work:

```bash
cd /Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026
git status --short --branch
git fetch origin
git pull --ff-only origin main
```

- If the current worktree has unrelated dirty files, do not overwrite, revert, stash, or format them. Work around them only if safe; otherwise write a blocked report.
- Use a scoped branch for code changes when possible.
- Commit and push completed repository changes to GitHub.
- Do not merge to `main` unless the current role contract and task execution path explicitly permit it; Director will review and sequence production validation separately.

## Completion Report Storage Requirements

- Write the completion report into `TaskAndReport/` using this naming rule:
  `2026-05-13T13-58-10+0800_P0-Post-Validation-Ollama-And-MinerU-Progress-Blockers_REPORT.md`
- Update `TaskAndReport/TASK_TRACKING_LIST.md` with report path, branch/HEAD, status, `Next Actor=Director`, next action, and required output.
- Do not rely on chat relay for completion reporting.

## Acceptance Criteria

- Ollama metadata provider no longer has an unintended 30-second effective inference deadline for real non-streaming `/api/chat` metadata calls.
- Dependency-health short smoke remains bounded and separate from real metadata inference readiness.
- Strict no-skeleton semantics are preserved.
- Fast completed MinerU tasks produce either real structured progress semantics or a truthful structured no-business-signal / fast-complete diagnostic visible through task API/UI paths.
- Tests cover both observed blocker classes.
- No production deployment, upload, pressure test, failed-task repair, cleanup, destructive mutation, model operation, L3, pressure PASS, or release-readiness claim is made.
