# Director Review: P1 Dependency Health Timing Semantics Hardening

- Review ID: `TASK-20260515-092917-P1-Dependency-Health-Timing-Semantics-Hardening-Director-Review`
- Reviewed task: `TASK-20260515-090601-P1-Dependency-Health-Timing-Semantics-Hardening`
- Task brief: `TaskAndReport/2026-05-15T09-06-01+0800_P1-Dependency-Health-Timing-Semantics-Hardening_TASK.md`
- Report: `TaskAndReport/2026-05-15T09-06-01+0800_P1-Dependency-Health-Timing-Semantics-Hardening_REPORT.md`
- Reviewer: Director
- Review time: `2026-05-15T09:29:17+0800`

## Decision

`ACCEPTED_CODE_TEST_LEVEL_PRODUCTION_DEPLOYMENT_DECISION_REQUIRED`

Task 164 is accepted at code/test level. The implementation makes Ollama dependency-health timing semantics explicit without weakening strict no-skeleton behavior and without turning AI readiness failures into parse/upload blockers.

Production deployment, runtime validation, pressure PASS, L3, release-readiness, production-readiness, production上线, and go-live readiness are not accepted or declared by this review.

## What Was Accepted

- `server/upload-server.mjs` now reports explicit Ollama readiness/timing fields in dependency-health:
  - `readinessState`;
  - `readinessSeverity`;
  - `timingNote`;
  - `probeTimeoutMs`;
  - `recommendedClientTimeoutMs`;
  - `blockingAi`;
  - `readinessBlocking`;
  - `coldStartChatSucceeded` for slow-but-successful cold-before-chat probes.
- `blockingParse` remains false for Ollama/AI issues.
- Slow but successful cold-before-chat probing remains a success with explicit caveat semantics.
- Cold timeout, warm timeout, HTTP chat failure, tags failure, service unreachable, and missing-model conditions are classified as AI readiness blockers.
- Focused smoke coverage now covers the new response contract.

## Review Evidence

Director reviewed the task brief, DevelopmentEngineer report, scoped code diff, and focused tests.

Commands run in the shared development workspace:

```text
node --check server/upload-server.mjs
node --check server/tests/dependency-health-smoke.mjs
git diff --check -- server/upload-server.mjs server/tests/dependency-health-smoke.mjs
node server/tests/dependency-health-smoke.mjs
node server/tests/ai-metadata-repair-hardening-smoke.mjs
node server/tests/mineru-runtime-progress-truth-smoke.mjs
node server/tests/pressure-result-semantics-smoke.mjs
npx pnpm@10.4.1 exec tsc --noEmit
```

Observed results:

- syntax checks passed;
- `git diff --check` passed;
- dependency-health smoke passed: `89 passed, 0 failed`;
- AI metadata repair hardening smoke passed;
- MinerU runtime progress truth smoke passed;
- pressure-result semantics smoke passed;
- TypeScript check passed.

Director also replayed the scoped code/test diff into a clean GitHub sync clone and installed dependencies there with:

```text
npx pnpm@10.4.1 install --frozen-lockfile --ignore-scripts
```

Then re-ran:

```text
node --check server/upload-server.mjs
node --check server/tests/dependency-health-smoke.mjs
git diff --check -- server/upload-server.mjs server/tests/dependency-health-smoke.mjs
node server/tests/dependency-health-smoke.mjs
node server/tests/ai-metadata-repair-hardening-smoke.mjs
node server/tests/mineru-runtime-progress-truth-smoke.mjs
node server/tests/pressure-result-semantics-smoke.mjs
npx pnpm@10.4.1 exec tsc --noEmit
```

Clean sync clone results:

- syntax checks passed;
- `git diff --check` passed;
- dependency-health smoke passed: `89 passed, 0 failed`;
- AI metadata repair hardening smoke passed;
- MinerU runtime progress truth smoke passed;
- pressure-result semantics smoke passed;
- TypeScript check passed.

## Boundaries

Not performed or authorized by this review:

- production deployment, fast-forward, rebuild, restart, rollback, or service mutation;
- upload, pressure/batch/soak/fresh serial validation;
- cleanup, cancel, repair, retry, reparse, re-AI, or automatic retry/requeue;
- destructive DB/MinIO/Docker volume/data mutation;
- settings, secrets, config, model, or sample mutation;
- skeleton fallback weakening;
- pressure PASS, L3, release-readiness, production-readiness, production上线, or go-live claim.

## Remaining Risk

The code/test contract is now stronger, but production still needs a scoped deployment and read-only validation before this can be treated as runtime evidence. In particular, production clients/operators must confirm the new dependency-health fields are visible and that slow successful Ollama cold-start behavior is no longer misread as a hard service failure.

## Next Step

Director records a User decision row for scoped production deployment and read-only validation of this accepted code/test change. Recommended path is a minimal, reversible deployment/read-only validation task assigned to `DevelopmentEngineer`, with no upload, pressure, cleanup, retry/reparse/re-AI, destructive operation, or readiness/go-live declaration.
