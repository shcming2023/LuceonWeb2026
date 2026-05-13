# Director Task: P0 AI Metadata Smoke Timeout Semantics Alignment

- Task ID: `TASK-20260513-105212-P0-AI-Metadata-Smoke-Timeout-Semantics-Alignment`
- Created At: `2026-05-13T10:52:12+0800`
- Created By: Director
- Assignee: `DevelopmentEngineer`
- Priority: P0
- Status: 下达待执行
- Related Review: `TaskAndReport/2026-05-13T10-52-12+0800_P1-Ollama-Keep-Alive-And-Cold-Warm-Health-Semantics_DIRECTOR_REVIEW.md`

## Required Reading Before Execution

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/development-engineer.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/prd/Luceon2026-PRD-v0.4.md`
- `docs/codex/TEST_POLICY.md`
- `docs/codex/REPOSITORY_STRUCTURE.md`
- `TaskAndReport/README.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`
- This task brief.

## Background

Director reviewed Task 78 and accepted the Ollama keep-alive / cold-warm dependency-health semantics at code level. During Director spot-checks on current `main`, the focused dependency-health smoke passed, but the broader AI metadata real sample smoke failed:

```text
node server/tests/ai-metadata-real-sample-smoke.mjs
exit 1
AssertionError [ERR_ASSERTION]: 30000 == 12345
at server/tests/ai-metadata-real-sample-smoke.mjs:830
```

The current `OllamaProvider` sets:

- Undici `headersTimeout: 30000`;
- `error.headersTimeoutMs = 30000`;
- `bodyTimeout` and `error.bodyTimeoutMs` from `this.timeoutMs`.

This appears to come from the later `e7c68ba` Phase 1 stability enhancement, whose commit message describes AI Worker first-byte timeout behavior. The smoke test still expects the old behavior where `headersTimeoutMs` equals the provider timeout passed into `new OllamaProvider({ timeoutMs })`.

## Objective

Restore a truthful, passing AI metadata smoke suite on current `main` by aligning the test with the current intended Ollama timeout semantics, or by correcting the provider if investigation shows the provider behavior contradicts the accepted stability design.

## Non-Goals

- Do not change Ollama model selection.
- Do not change `OLLAMA_KEEP_ALIVE` behavior unless a direct contradiction is found.
- Do not alter AI JSON/schema/repair strictness.
- Do not change production runtime, production overrides, secrets, DB rows, MinIO objects, Docker volumes, task states, artifacts, or local sample-library files.
- Do not create uploads, rerun pressure tests, repair Task 75/76 tasks, or claim production readiness.

## Allowed Files, Modules, Or Operations

Primary allowed file:

- `server/tests/ai-metadata-real-sample-smoke.mjs`

Conditional allowed file, only if analysis proves provider behavior is wrong rather than the test stale:

- `server/services/ai/providers/ollama.mjs`

Required report and ledger updates:

- `TaskAndReport/2026-05-13T10-52-12+0800_P0-AI-Metadata-Smoke-Timeout-Semantics-Alignment_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

## Suggested Direction

1. Inspect `e7c68ba` and current `server/services/ai/providers/ollama.mjs`.
2. Determine whether the intended current contract is:
   - `headersTimeoutMs = 30000` for first-byte/header timeout;
   - `bodyTimeoutMs = provider timeoutMs`.
3. If yes, update the stale assertions in `server/tests/ai-metadata-real-sample-smoke.mjs` so Test 5 and any related repair-detail assertions expect the current split timeout semantics.
4. If no, explain why and make the smallest provider/test correction that restores the intended contract.

## Required Checks

Run and report exact exit codes:

```bash
git diff --check
node --check server/services/ai/providers/ollama.mjs
node server/tests/ai-metadata-real-sample-smoke.mjs
node server/tests/dependency-health-smoke.mjs
npx pnpm@10.4.1 exec tsc --noEmit
npx pnpm@10.4.1 run build
```

If any required check cannot be run, report the exact reason and do not mark the task complete.

## Required Evidence

The completion report must include:

- branch and HEAD;
- exact files changed;
- whether the provider behavior or the smoke assertion was corrected;
- before/after timeout contract;
- exact command outputs or concise pass/fail summaries with exit codes;
- clear statement that no production runtime, model, upload, pressure task, DB, MinIO, Docker volume, secret, sample, or release-readiness operation occurred.

## Acceptance Criteria

- `node server/tests/ai-metadata-real-sample-smoke.mjs` passes on current `main`.
- `node server/tests/dependency-health-smoke.mjs` still passes.
- The timeout semantics are explicit enough that future reviewers can tell the difference between header/first-byte timeout and body/provider timeout.
- No production readiness, L3, pressure PASS, or deployment claim is made.
