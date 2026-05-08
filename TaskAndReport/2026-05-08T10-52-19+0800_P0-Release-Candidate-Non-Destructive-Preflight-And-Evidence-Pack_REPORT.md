# P0 Release Candidate Non-Destructive Preflight And Evidence Pack Report

## Basis

- Based on Lucia task brief: `TaskAndReport/2026-05-08T10-41-37+0800_P0-Release-Candidate-Non-Destructive-Preflight-And-Evidence-Pack_TASK.md`.
- Assignee: Lucode.
- Scope executed: read-only release-candidate preflight and evidence pack.
- Explicit boundary: no production release readiness is claimed by this report.

## Branch And HEAD

- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Development branch: `main`.
- Development baseline HEAD during checks: `d73293d docs: record release scope decision wait`.
- Production workspace: `/Users/concm/prod_workspace/Luceon2026`
- Production workspace observed HEAD: `4cc6d3e docs: accept observation semantics and assign deployment validation`.

## Files Changed

- `TaskAndReport/2026-05-08T10-52-19+0800_P0-Release-Candidate-Non-Destructive-Preflight-And-Evidence-Pack_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

## Development Workspace Evidence

| Item | Evidence |
| --- | --- |
| Git status before execution | `## main...origin/main` |
| Git sync | `git fetch origin` exit 0; `git pull --ff-only origin main` exit 0, `Already up to date.` |
| HEAD | `d73293d docs: record release scope decision wait` |
| Diff check | `git diff --check` exit 0 |
| TypeScript | `npx pnpm@10.4.1 exec tsc --noEmit` exit 0 |
| Build | `npx pnpm@10.4.1 run build` exit 0 |
| Build warning | Existing Vite warning: chunk larger than 500 kB after minification; build still passed |
| Dependency smoke | `node server/tests/dependency-health-smoke.mjs` exit 0, `31 passed, 0 failed` |

## Production Workspace Boundary

| Item | Evidence |
| --- | --- |
| Git status | `## main...origin/main [behind 2]`; `M docker-compose.override.yml` |
| HEAD | `4cc6d3e docs: accept observation semantics and assign deployment validation` |
| Local diff stat | `docker-compose.override.yml | 6 +++++-` |
| Boundary | Production workspace was inspected read-only only. No pull, rebuild, restart, rollback, Docker command, DB/MinIO/task mutation, or override edit was performed. |

This remains a blocker for any release-candidate naming: the production workspace is not at current `origin/main`, and the local override must be accepted or reviewed before release-readiness can be considered.

## Runtime Evidence

All runtime checks were read-only against the already-running `http://localhost:8081` service.

### Dependency Health

Command:

```bash
curl -fsS 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true'
```

Exit: 0.

Summary:

- `ok=true`
- `blocking=false`
- `minio.ok=true`
- `mineru.ok=true`
- `mineru.healthOk=true`
- `mineru.submitProbe.enabled=true`
- `mineru.submitProbe.ok=true`
- `mineru.submitProbe.status=202`
- `mineru.submitProbe.taskId=2bb55bbf-caaa-4ab7-b7d7-933b3a14a591`
- `ollama.ok=true`
- `ollama.chatOk=true`
- `ollama.model=qwen3.5:9b`

### Ops Session Status

Command:

```bash
curl -fsS http://localhost:8081/__proxy/upload/ops/dependency-repair/status
```

Exit: 0.

Summary:

- `ok=true`
- `message=Supervisor running`
- `sessions.sidecar=true`
- `services.mineruReachable=true`
- `services.ollamaReachable=true`
- `ownership.mineru.managed=false`, reachable through unmanaged sessions `mineru_api`, `mineru_gradio`
- `ownership.ollama.managed=false`, reachable but not managed by expected `luceon-ollama` tmux session

Interpretation: this is not a current dependency outage, but it is still an ops-session/release-readiness warning.

### DB Health

Command:

```bash
curl -fsS http://localhost:8081/__proxy/db/health
```

Exit: 0.

Summary:

- `ok=true`
- `service=db-server`
- `dataPath=/data/db-data.json`
- `secretsPath=/data/secrets.json`

## Commands Run

| Command | Exit | Evidence |
| --- | ---: | --- |
| `git status --short --branch` | 0 | `## main...origin/main` |
| `git fetch origin` | 0 | Completed without output |
| `git pull --ff-only origin main` | 0 | `Already up to date.` |
| `sed -n '1,280p' TaskAndReport/2026-05-08T10-41-37+0800_P0-Release-Candidate-Non-Destructive-Preflight-And-Evidence-Pack_TASK.md` | 0 | Read task brief |
| `sed -n '1,240p' TaskAndReport/2026-05-08T10-41-37+0800_P0-Director-Release-Readiness-Scope-Decisions_DECISION.md` | 0 | Read pending Director decision |
| `sed -n '1,240p' TaskAndReport/2026-05-08T10-41-37+0800_P0-Production-Release-Readiness-Gap-Matrix-And-Validation-Plan_LUCIA_REVIEW.md` | 0 | Read Lucia review |
| `git log -1 --oneline` | 0 | `d73293d docs: record release scope decision wait` |
| `git diff --check` | 0 | No whitespace errors |
| `git status --short --branch` in production workspace | 0 | `## main...origin/main [behind 2]`; `M docker-compose.override.yml` |
| `git log -1 --oneline` in production workspace | 0 | `4cc6d3e docs: accept observation semantics and assign deployment validation` |
| `git diff --stat` in production workspace | 0 | `docker-compose.override.yml | 6 +++++-` |
| `curl -fsS 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true'` | 0 | `blocking=false`; MinerU submit probe OK; Ollama OK |
| `curl -fsS http://localhost:8081/__proxy/upload/ops/dependency-repair/status` | 0 | Supervisor running; sidecar managed; MinerU/Ollama reachable but unmanaged |
| `curl -fsS http://localhost:8081/__proxy/db/health` | 0 | DB health OK |
| `npx pnpm@10.4.1 exec tsc --noEmit` | 0 | TypeScript check passed |
| `npx pnpm@10.4.1 run build` | 0 | Vite build passed with existing chunk-size warning |
| `node server/tests/dependency-health-smoke.mjs` | 0 | `31 passed, 0 failed` |

## Skipped Checks

- Tier 2 Standard check and UAT smoke were not run because task #20 required TypeScript, build, dependency-health smoke, and read-only runtime checks; it did not assign full UAT or runtime workflow execution.
- No Docker pull/build/compose command was run because the task explicitly forbids Docker pull/build/compose operations.
- No production workspace pull or reset was run because the task allows read-only inspection only.
- No controlled upload, task creation, DB mutation, MinIO mutation, restart, rebuild, rollback, or repair was run because the task explicitly forbids production mutation and does not authorize runtime workflow mutation.
- Large-PDF soak, concurrency, error-path, and rollback rehearsal remain planned release-readiness validations, not part of this evidence-pack task.

## Remaining Blockers Before Production Release-Readiness Review

- Production workspace is behind `origin/main` and has local modified `docker-compose.override.yml`; Director/Lucia must define the release-candidate workspace boundary before release review.
- Director release-scope decisions in task #19 remain pending.
- Large-PDF soak has not been executed.
- Concurrent upload/parse/AI validation has not been executed.
- Error-path matrix has not been executed.
- Rollback/recovery rehearsal has not been authorized or executed.
- Docker frontend `nginx:1.27-alpine` base-image metadata/pull preflight remains an operational release blocker before any rebuild.
- Ops ownership remains imperfect: MinerU and Ollama are reachable, but not managed by expected `luceon-*` tmux sessions.
- Full-site/state-matrix browser acceptance and security/no-auth boundary remain unaccepted for production release.

## Pending Director Decisions

From task `TASK-20260508-104137-P0-Director-Release-Readiness-Scope-Decisions`:

- Choose production release readiness, continued manual-review hardening, Phase 2 planning, or iteration closure as the current route.
- Decide whether large-PDF soak, concurrency validation, and rollback rehearsal are mandatory before any production release-readiness claim.
- Decide the boundary for production `docker-compose.override.yml`.
- Decide whether Lucia may later authorize production restart/rebuild/rollback rehearsal.
- Decide whether the single-operator/no-auth local deployment boundary is acceptable for the intended release audience.

## GitHub Sync Status

- Development workspace was synced with `origin/main` before execution.
- Report and tracking update are to be committed and pushed to GitHub `main`.
- Final pushed HEAD will be reported in Lucode's completion response.

## Required Next Review

- Lucia review is required.
- Director decision remains required before any release-readiness claim or production mutation.
- Recommended next step: Lucia should review this evidence pack, then either issue correction, issue the next non-destructive validation task, or wait for Director decision #19.
