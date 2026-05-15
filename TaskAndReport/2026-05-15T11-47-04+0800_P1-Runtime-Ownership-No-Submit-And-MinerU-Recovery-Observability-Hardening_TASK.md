# Task Brief: P1 Runtime Ownership No-Submit And MinerU Recovery Observability Hardening

- Task ID: `TASK-20260515-114704-P1-Runtime-Ownership-No-Submit-And-MinerU-Recovery-Observability-Hardening`
- Created: 2026-05-15T11:47:04+0800
- Created by: Director
- Assigned role: `DevelopmentEngineer`
- Expected report: `TaskAndReport/2026-05-15T11-47-04+0800_P1-Runtime-Ownership-No-Submit-And-MinerU-Recovery-Observability-Hardening_REPORT.md`
- Based on Director review: `TaskAndReport/2026-05-15T11-47-04+0800_P1-MinerU-Only-Recovery-And-Submit-Path-Verification_DIRECTOR_REVIEW.md`
- Based on prior blocker evidence: `TaskAndReport/2026-05-15T11-12-51+0800_P1-Rollback-Recovery-And-Error-Path-Read-Only-Evidence-Pack_DIRECTOR_REVIEW.md`

## Context

Task 173 recovered the live MinerU submit path by restarting only the host MinerU API and running exactly one authorized submit-probe. Director accepted that recovery as runtime-only evidence.

During the preceding evidence work, a separate engineering hygiene issue became clear: `ops/runtime-ownership-status.sh` is used like a read-only status helper, but it currently invokes:

```bash
$UPLOAD_BASE/ops/dependency-health?mineruSubmitProbe=true
```

That request creates a bounded synthetic MinerU task and may open or close the durable admission circuit. It is useful when explicitly authorized, but it is not read-only. Future role-thread diagnostics must not accidentally mutate MinerU runtime state while claiming read-only evidence.

## Required Reading

Before acting, read:

1. `AGENTS.md`
2. `docs/codex/TEAM_CONTRACT.md`
3. `docs/codex/roles/development-engineer.md`
4. `docs/codex/PROJECT_STATE.md`
5. `docs/codex/HANDOFF.md`
6. `docs/prd/Luceon2026-PRD-v0.4.md`
7. `docs/codex/TEST_POLICY.md`
8. `docs/codex/REPOSITORY_STRUCTURE.md`
9. `TaskAndReport/README.md`
10. `TaskAndReport/TASK_TRACKING_LIST.md`
11. This task brief
12. Task 170 Director review
13. Task 173 report and Director review

If the task row, role file, or required evidence files are missing locally, stop and report `本地任务列表或角色文档未更新/疑似不同步`.

## Objective

Make runtime ownership/status tooling and documentation safe and unambiguous:

1. `ops/runtime-ownership-status.sh` must be read-only/no-submit by default.
2. The MinerU submit-probe must require explicit opt-in, such as an environment variable or flag with clear naming.
3. The script output must clearly label whether the MinerU submit-probe was skipped or intentionally executed.
4. Documentation that mentions runtime status, dependency-health, admission circuit, or submit-probe must clearly distinguish:
   - read-only health/status checks;
   - side-effecting submit-path verification that creates a synthetic MinerU task and requires explicit authorization.

Keep this task focused on tooling, docs, and small diagnostic clarity. Do not change business logic, public API behavior, upload behavior, MinerU admission semantics, worker behavior, AI behavior, PRD truth, or role contracts.

## Allowed Files

Expected files may include:

- `ops/runtime-ownership-status.sh`
- `docs/deploy/PRODUCTION_RUNTIME_OWNERSHIP.md`
- `docs/codex/TEST_MATRIX.md`
- focused tests or static checks if you add them
- `TaskAndReport/2026-05-15T11-47-04+0800_P1-Runtime-Ownership-No-Submit-And-MinerU-Recovery-Observability-Hardening_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

If you believe another source file must change, stop first and explain why in a blocked report unless the change is only a very small diagnostic label/comment needed to satisfy this task.

## Required Behavior

At minimum:

- Default invocation of `bash ops/runtime-ownership-status.sh` must not call `mineruSubmitProbe=true`.
- There must be a clear opt-in path for the submit-probe, for example:
  - `RUN_MINERU_SUBMIT_PROBE=1 bash ops/runtime-ownership-status.sh`; or
  - `bash ops/runtime-ownership-status.sh --submit-probe`.
- The script must print a clear warning or section label when the submit-probe is enabled.
- The script must print a clear skipped/no-submit line when submit-probe is not enabled.
- Documentation must use exact command examples for read-only checks and side-effecting checks separately.

## Forbidden Operations

Forbidden:

- running `mineruSubmitProbe=true` during this task unless you are only updating code/tests and a test fixture simulates it without touching production;
- PDF upload, Markdown upload, pressure/batch/soak/fresh serial validation, or user validation artifact creation;
- production deployment, production pull/fast-forward, rollback, rebuild, Docker compose mutation, service restart, MinerU/Ollama/supervisor/sidecar mutation;
- DB/MinIO/Docker volume/data mutation, restore/import, cleanup, cancel, repair, retry, reparse, re-AI, takeover, automatic retry/requeue;
- settings, secrets, config, model, sample-library mutation;
- PRD truth, role contract, project state, or handoff changes;
- skeleton fallback weakening or silent degradation;
- declaring pressure PASS, L3, release-readiness, production-readiness, production上线, or go-live readiness.

## Required Checks

Run applicable checks and record exact commands and exit codes:

- `bash -n ops/runtime-ownership-status.sh`
- `git diff --check`
- If any `.mjs` file is changed, run `node --check` for the changed file and the relevant focused smoke test.
- If any TypeScript source is changed, run `npx pnpm@10.4.1 exec tsc --noEmit`.
- If you add or change a test, run it.

Do not run live submit-probe or production-mutating commands as part of validation for this task.

## Completion

Write:

`TaskAndReport/2026-05-15T11-47-04+0800_P1-Runtime-Ownership-No-Submit-And-MinerU-Recovery-Observability-Hardening_REPORT.md`

Update row 174 in `TaskAndReport/TASK_TRACKING_LIST.md`:

- Status: `已回报待 Director 审查` or a precise blocked status;
- Next Actor: `Director`;
- Report path populated;
- Notes include changed files, behavior summary, checks, and whether submit-probe remained unrun.

## GitHub Sync

Do not fetch, pull, push, merge, or create commits unless Director explicitly instructs you. Work in the current synchronized workspace. Director will review and handle GitHub synchronization.
