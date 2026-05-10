# Lucia Review: P1 Task Page MinerU Progress Semantics Restoration

- Reviewed task: `TASK-20260510-171943-P1-Task-Page-MinerU-Progress-Semantics-Restoration`
- Review time: `2026-05-10T22:58:07+0800`
- Reviewed by: Lucia
- Report: `TaskAndReport/2026-05-10T17-19-43+0800_P1-Task-Page-MinerU-Progress-Semantics-Restoration_REPORT.md`
- Implementation branch: `lucode/p1-task-page-mineru-progress-semantics-restoration`
- Implementation HEAD: `d202cf1de93de44f2239032bcb1dc9531b7383fb`
- Report HEAD: `9bf8bd29ff3dd926c745cbaeb20597966a8d9907`
- Review decision: `ACCEPTED_CODE_LEVEL_PRODUCTION_DEPLOYMENT_REQUIRED`

## Decision

Lucia accepts Task 77 at code level.

The implementation satisfies Director's hard requirement that this must not be a mere page-copy change. The code restores structured MinerU progress semantics from native log signals into task/API/UI-facing surfaces, including backend, phase, batch, page progress, freshness, and safe Chinese operator messages.

This is not production deployment validation, not pressure-test PASS, not manual pressure-test readiness, not L3/full-site acceptance, and not production release readiness.

## Evidence Reviewed

Accepted implementation facts:

- Pipeline run lines are parsed, including total pages, window size, and total batches.
- Pipeline batch/page-window lines are parsed, including batch index/total, current pages, total pages, batch pages, and page slices.
- `progressSemantics` now carries normalized backend, phase, phase label, freshness, batch, page, stage, and message fields.
- Local MinerU polling can surface the normalized operator message while preserving explicit failure behavior.
- Task list/detail UI can show the normalized Chinese progress line.
- Task detail UI no longer exposes absolute host log paths; it shows safe log status/freshness information instead.

Lucia independently reviewed the diff and reran:

```bash
git diff --check
node server/tests/mineru-log-progress-smoke.mjs
node server/tests/mineru-diagnostics-smoke.mjs
node server/tests/mineru-submit-circuit-breaker-smoke.mjs
npx pnpm@10.4.1 exec tsc --noEmit
npx pnpm@10.4.1 run build
```

Results:

- `git diff --check`: PASS.
- `mineru-log-progress-smoke`: `134 passed, 0 failed`.
- `mineru-diagnostics-smoke`: PASS.
- `mineru-submit-circuit-breaker-smoke`: `10 passed, 0 failed`.
- `tsc --noEmit`: PASS.
- `build`: PASS with existing Vite chunk-size warning only.

Lucia fast-forward integrated the branch into `main`.

## Runtime Boundary

Lucia also performed read-only runtime checks after the code review:

- `/api/ps` currently showed `qwen3.5:9b` resident with an expiry time.
- `dependency-health?mineruSubmitProbe=true` still returned `ollama.ok=false`, `chatOk=false`, and `durationMs=15025` because the Ollama smoke timed out.
- MinerU submit-probe remained HTTP `202`; admission circuit remained closed; parse counts were still `parseRunning=1`, `parsePending=17`.

This confirms Director's broader judgment: Task 77 repairs the MinerU progress-observability code path, but the local long-running production line is still not release-ready. Ollama keep-alive / cold-warm dependency-health semantics remain a separate blocker and must not be hidden inside the Task 77 acceptance.

## Boundaries Preserved

- No production upload was created.
- No pressure retry was run.
- No Task 75/76 task was repaired or mutated.
- No DB, MinIO object, Docker volume, sample file, secret, model, timeout, production override, or service ownership was changed by Lucia's review.
- No L3/full-site, pressure PASS, manual pressure-test readiness, or production release-readiness claim is made.

## Follow-Up

Lucia issued:

`TASK-20260510-225807-P1-Ollama-Keep-Alive-And-Cold-Warm-Health-Semantics`

This follow-up is separate from Task 77. Its purpose is to make Ollama residency and dependency-health semantics explicit and stable for the local long-running production line.

