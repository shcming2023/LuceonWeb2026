# P0 Controlled Concurrency Validation Plan And Preflight

Task:
P0 Controlled Concurrency Validation Plan And Preflight

Task ID:
`TASK-20260508-191709-P0-Controlled-Concurrency-Validation-Plan-And-Preflight`

Assignee:
Lucode

Issued by:
Lucia

Issued at:
2026-05-08T19:17:09+0800

Project:
Luceon2026

Development workspace:
`/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`

Production deployment path:
`/Users/concm/prod_workspace/Luceon2026`

GitHub:
`https://github.com/shcming2023/Luceon2026`

TaskAndReport record:
`TaskAndReport/2026-05-08T19-17-09+0800_P0-Controlled-Concurrency-Validation-Plan-And-Preflight_TASK.md`

## Required Reading Before Execution

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/lucode.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/codex/TEST_POLICY.md`
- `docs/deploy/DEPLOY.md`
- `TaskAndReport/2026-05-08T19-10-21+0800_P0-Next-Release-Readiness-Validation-Scope_DECISION.md`
- `TaskAndReport/2026-05-08T19-17-09+0800_P0-Next-Release-Readiness-Validation-Scope_LUCIA_REVIEW.md`
- `TaskAndReport/2026-05-08T19-10-21+0800_P0-Adaptive-Evidence-Pack-Warmup-Gated-Production-Validation_LUCIA_REVIEW.md`
- `TaskAndReport/2026-05-08T19-05-34+0800_P0-Adaptive-Evidence-Pack-Warmup-Gated-Production-Validation_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

## Background

Task 38 proved the adaptive evidence-pack path for one controlled production large-PDF sample. Director selected concurrency validation as the next release-readiness validation track.

Concurrency validation can create multiple production validation artifacts, so this first task is planning and preflight only. It must not create concurrent uploads yet.

## Objective

Prepare a safe, bounded concurrency validation plan and collect non-destructive preflight evidence so Lucia can decide whether to authorize the actual concurrent upload run.

## Authorized Scope

Lucode may:

1. Synchronize development workspace metadata with GitHub.
2. In production, run read-only status/fetch/inspection commands.
3. Inspect production service state with read-only commands such as `docker compose ps`.
4. Run CMS, DB, dependency-health with `mineruSubmitProbe=true`, and active task/job checks.
5. Perform at most one bounded non-mutating Ollama warm-up/readiness check if needed for preflight.
6. Inspect available sample files without modifying them.
7. Use the external sample directory only as read-only input inventory:
   - `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/4.XxwlAs2026/sample`
8. Produce a concrete concurrency validation plan with:
   - proposed concurrency level;
   - proposed max upload count;
   - exact sample paths, sizes, and hashes;
   - stop conditions;
   - warm-up/readiness gates;
   - polling strategy;
   - evidence fields to collect;
   - rollback/no-cleanup boundary;
   - risk assessment and recommended next task.

## Hard Limits For This Task

- Planning/preflight only.
- Do not create any production upload in this task.
- Do not mutate production services, Docker, DB, MinIO, Ollama, config, secrets, overrides, samples, artifacts, or logs.
- Do not copy, move, rename, edit, delete, or pollute sample files.
- Do not synchronize external sample files to GitHub.
- Do not claim production release readiness.

## Planning Guidance

Prefer a conservative first concurrency design:

- concurrency level: `2`
- max controlled uploads: `2`
- sample mix: one previously proven large-PDF sample plus one smaller or medium sample, if a suitable read-only sample can be identified.

If no suitable second sample can be safely identified, recommend using two explicitly listed approved samples or return with a Director decision request.

## Required Preflight Evidence

Collect and report:

- Development and production git status.
- Production HEAD and `origin/main`.
- Production override boundary:
  - `DISABLE_AI_SKELETON_FALLBACK=true`
  - `OLLAMA_TIER2_MODEL=qwen3.5:9b`
  - MinIO console mapping `127.0.0.1:19001:9001`
- `docker compose ps` read-only service state.
- CMS reachability.
- DB health.
- Dependency health with `mineruSubmitProbe=true`.
- Active parse/task states and active AI metadata jobs.
- Candidate sample inventory:
  - exact path;
  - size;
  - SHA-256;
  - reason for inclusion or exclusion.

## Forbidden

- Do not claim production release readiness.
- Do not create production uploads.
- Do not run production deploy, fast-forward, rebuild, restart, rollback, or Docker mutation.
- Do not restart, start, stop, kill, or reload Ollama or any production service.
- Do not delete DB rows.
- Do not delete MinIO objects.
- Do not delete or prune Docker volumes.
- Do not change secrets.
- Do not change model or timeout policy.
- Do not change config or production-local override values.
- Do not add skeleton fallback or silent degradation.
- Do not alter external sample files or sync them to GitHub.

## Required Output

Write report to:

`TaskAndReport/YYYY-MM-DDTHH-MM-SS+0800_P0-Controlled-Concurrency-Validation-Plan-And-Preflight_REPORT.md`

The report must include:

- Result classification: `PLAN_READY`, `BLOCKED`, or `INCONCLUSIVE`.
- Exact commands and exit codes.
- Preflight evidence listed above.
- Proposed concurrency validation plan.
- Proposed next Lucode task if Lucia accepts the plan.
- Confirmation that no production upload, mutation, cleanup, sample modification, GitHub sample sync, or production release-readiness claim occurred.

Update `TaskAndReport/TASK_TRACKING_LIST.md`:

- Status `已回报待审`
- `Next Actor=Lucia`
- Report path
- Branch/HEAD
- Summary notes

Commit and push report/task-list changes to GitHub `main`.
