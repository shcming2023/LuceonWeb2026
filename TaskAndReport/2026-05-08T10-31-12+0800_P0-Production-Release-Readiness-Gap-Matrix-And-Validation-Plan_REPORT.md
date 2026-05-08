# P0 Production Release Readiness Gap Matrix And Validation Plan Report

## Basis

- Based on Lucia task brief: `TaskAndReport/2026-05-08T10-19-44+0800_P0-Production-Release-Readiness-Gap-Matrix-And-Validation-Plan_TASK.md`.
- Assignee: Lucode.
- Scope executed: non-destructive release-readiness analysis and validation planning only.
- Explicit boundary: this report does not claim production release readiness, staging readiness, L3 readiness, UAT completion, or full-site acceptance.

## Branch And HEAD

- Development branch: `main`.
- Execution baseline HEAD before report commit: `19e2465 docs: issue release readiness gap task`.
- Report/tracking commit: `FINAL_COMMIT_PLACEHOLDER`.
- Production workspace observed HEAD: `4cc6d3e docs: accept observation semantics and assign deployment validation`.
- Production workspace observed state: `main...origin/main [behind 2]` with local modified `docker-compose.override.yml`; no production pull, rebuild, restart, or cleanup was performed.

## Files Changed

- `TaskAndReport/2026-05-08T10-31-12+0800_P0-Production-Release-Readiness-Gap-Matrix-And-Validation-Plan_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

## Accepted Evidence Versus Release Readiness

Phase 1 has accepted evidence for the local/production manual-review path: upload through `/cms/tasks`, local MinerU parsing, MinIO raw/parsed persistence, Ollama `qwen3.5:9b` metadata recognition with strict no-skeleton behavior, and operator review reaching `review-pending` on controlled samples.

That evidence supports manual-review readiness only. Production release readiness remains unclaimed because release-level evidence is still missing for soak/long-running behavior, concurrency, error paths, recovery/rollback, security/permission boundaries, deployment repeatability, and broader acceptance coverage.

## Release-Readiness Gap Matrix

| Area | Current accepted evidence | Current boundary label | Release-readiness requirement | Gap | Proposed validation method | Required command or manual check | Risk if skipped | Priority | Suggested owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Upload path | `/cms/tasks` upload has created controlled PDF tasks and UAT smoke has passed. | Manual-review ready. | Repeatable browser and API evidence for supported upload types and size limits. | Folder upload, larger PDFs, and upload error paths are not closed. | Run browser UAT plus targeted API/file-size matrix. | `BASE_URL=http://localhost:8081 bash uat/smoke-test.sh`; add assigned large/folder upload checks. | Release may fail on real operator uploads outside small controlled samples. | P0 | Lucode, Lucia review |
| MinerU submit path | Dependency health with `mineruSubmitProbe=true` now verifies `/tasks` returns task id; current curl passed. | Standard dependency gate accepted. | Submit path must pass before every release candidate and after restart/rebuild. | No long-run MinerU soak or degraded-runtime matrix yet. | Preflight submit probe plus controlled PDF parse plus failure injection in non-prod. | `curl -fsS 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true'`; `node server/tests/mineru-deep-check.mjs` when assigned. | `/health` can look OK while real parse submission fails. | P0 | Lucode |
| MinIO raw and parsed persistence | Controlled samples produced raw/parsed artifacts including `full.md` and `artifact-manifest.json`. | Manual-review ready. | Raw object, parsed manifest, ZIP export, and consistency audit must pass across representative files. | No release matrix for missing object, partial parsed artifact, or MinIO restart/recovery. | Artifact manifest audit and restore/readback checks without mutation. | Consistency audit endpoint, ZIP export manual check, MinIO object readback assigned in a validation task. | Operators may see completed tasks with missing or unrecoverable artifacts. | P0 | Lucode |
| AI metadata and strict no-skeleton | Ollama `qwen3.5:9b` controlled samples reached `review-pending`; strict worker smoke proves provider failure does not create skeleton output. | Manual-review ready with mitigated AI repair debt. | Required AI failure must fail explicitly; successful metadata must identify provider/model and not be skeleton. | Long AI latency, timeout, malformed JSON, and repair-path stress are not release-covered. | Run AI focused smoke, real sample smoke, and timeout/error injection in non-prod. | `node server/tests/ai-metadata-repair-hardening-smoke.mjs`; `node server/tests/worker-smoke.mjs`; assigned real-runtime AI sample. | Silent or slow AI failures could block tasks or mislead operators. | P0 | Lucode |
| Operator review flow | Review-pending samples display `待复核`; deterministic repair success is shown as completed/review-needed; tag/review flows have historical PASS evidence. | Manual-review ready. | Full review state matrix across pending/running/failed/review-pending/completed must be validated. | Current evidence is sample-centered, not full state matrix or full-site UI acceptance. | Browser UAT for task list/detail/review actions and failed-state UI. | Playwright UAT suites plus manual Director review checklist. | Operators may approve/reject from misleading UI states. | P1 | Lucode, Director manual review |
| Large-PDF and long-running tasks | Small controlled PDFs pass; historical large-PDF/pressure boundaries remain open. | Release gap. | Representative large PDFs must parse without DB OOM, timeout ambiguity, or artifact bloat. | No large-PDF soak or long-running task recovery acceptance. | Non-destructive staged soak with capped fixtures and monitoring. | Assigned soak script/check; DB size and task event-log inspection. | Production may fail on realistic教材 PDFs. | P0 | Lucode, Lucia gates fixture scope |
| Concurrency | No current release-level concurrency acceptance. | Release gap. | Concurrent upload/parse/AI jobs must preserve queue integrity and object/task consistency. | Race and capacity behavior unknown. | Bounded concurrent upload test in non-prod or controlled production window. | Assigned concurrency runner plus consistency audit. | Queue starvation, cross-task artifact attribution, or inconsistent states. | P0 | Lucode |
| Error-path behavior | Some strict failure semantics and dependency-health failures are covered by focused smoke tests. | Partial evidence. | MinerU down, MinIO down, Ollama down, invalid files, timeout, retry/re-AI boundaries must be explicit and operator-visible. | Retry/Reparse/Re-AI APIs are non-goals/open; all error paths not validated. | Non-destructive mock/focused tests first; runtime failure injection only when explicitly assigned. | Existing smoke tests plus new assigned error-path matrix. | Failures may appear as success, blocked dependencies, or irrecoverable tasks. | P0 | Lucia briefs, Lucode executes |
| Permissions and security | Single-operator local deployment; no multi-user permission model is in scope for v0.4. | Director-owned release decision. | Release note must state single-operator/local boundary and protect secrets/artifacts. | No security review, auth boundary, or secret-handling release check. | Documentation/security checklist and `.env`/secret scan. | Read-only config review; secret scan if assigned. | Misstated deployment security boundary or credential leakage. | P0 | Lucia, Director |
| Rollback and recovery | Restart/self-heal behavior is PRD acceptance item; some ops sessions recovered manually. | Release gap. | Rollback rehearsal must prove code/service rollback without DB/MinIO loss. | No rollback rehearsal; production workspace currently behind `origin/main` and has local override. | Dry-run plan first, then explicit Director-approved rehearsal. | `git status`, deployment doc review, docker image/base preflight; no mutation without approval. | A bad deploy may not be recoverable quickly. | P0 | Director approval, Lucode executes |
| Docker/frontend base-image preflight | Task 16 diagnosed `nginx:1.27-alpine` metadata hang as Docker Desktop/buildx registry issue. | Documented deployment reliability debt. | Exact base image metadata resolution/pull must pass before rebuild release work. | Base image was missing locally and metadata resolution can hang. | Non-destructive preflight and pre-pull only when assigned/approved. | `docker image inspect nginx:1.27-alpine`; `docker buildx imagetools inspect nginx:1.27-alpine`; optional `docker pull` only with approval. | Release rebuild may stall before frontend image creation. | P0 | Lucode |
| Observability and ops-session semantics | Sidecar/supervisor recovered; reachability is separated from tmux ownership; current repair/status curl passed with unmanaged MinerU/Ollama warnings. | Manual-review ready with ops debt. | Release should have predictable startup/ownership semantics after deployment/restart. | Reachable but unmanaged MinerU/Ollama sessions remain; long-term session survival not guaranteed. | Read-only status checks plus later ops automation task. | `curl -fsS http://localhost:8081/__proxy/upload/ops/dependency-repair/status` | Operators may see confusing repair guidance after service restarts. | P1 | Lucode |
| Legacy route compatibility | `/cms/tasks` is main route; legacy redirects remain documented. | Non-blocking technical debt. | Redirects should remain tested or be formally retired. | Compatibility coverage is not release-central but should not regress silently. | Pages smoke plus route redirect tests. | Playwright pages smoke. | Old bookmarks may break or mask route-state bugs. | P2 | Lucode |
| Documentation and PRD alignment | Project state, handoff, test policy, and task ledger distinguish manual-review readiness from release readiness. | Mostly aligned. | Release decision must cite exact accepted evidence, missing evidence, and Director-owned boundaries. | PHASE1 summary still lists TD-001 open historically, while PROJECT_STATE marks it closed. | Lucia doc reconciliation after reviewing this report. | Lucia review and ledger update. | Conflicting docs may cause premature release claims. | P1 | Lucia |

## Recommended Validation Sequence

1. P0 release-candidate preflight: verify repository clean state, production workspace HEAD/override boundary, Docker base-image metadata, dependency health with MinerU submit probe, DB health, and ops-session status.
2. P0 repeat current Standard checks: TypeScript, build, dependency-health smoke, Tier 2 Standard check, UAT smoke, and focused MinerU/AI smoke tests on the candidate commit.
3. P0 controlled production candidate validation: one small PDF and one Markdown upload through `/cms/tasks`, verify MinIO raw/parsed artifacts, AI provider/model, no skeleton fallback, consistency audit, and operator review to `review-pending` or `completed` as applicable.
4. P0 release-gap validation: large-PDF soak, long-running task observation, bounded concurrency, and explicit error-path matrix.
5. P0 recovery validation: restart/self-heal and rollback rehearsal only after Director explicitly approves the operational window and rollback boundary.
6. P1 UI/full-site validation: task state matrix, legacy redirects, library visibility, settings/diagnostics, browser console, and manual Director review.
7. Lucia release-readiness review: only after all P0 checks pass and skipped checks have explicit accepted reasons.

## Checks Required Before Lucia Can Consider Release-Readiness Review

- `git status --short --branch` clean in dev and an explicitly accepted production workspace state.
- `git log -1 --oneline` matches the intended release candidate.
- `npx pnpm@10.4.1 exec tsc --noEmit`.
- `npx pnpm@10.4.1 run build`.
- `node server/tests/dependency-health-smoke.mjs`.
- `BASE_URL=http://localhost:8081 npx pnpm@10.4.1 run tier2:standard:check`.
- `BASE_URL=http://localhost:8081 bash uat/smoke-test.sh`.
- `curl -fsS 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true'`.
- `curl -fsS http://localhost:8081/__proxy/upload/ops/dependency-repair/status`.
- Controlled PDF and Markdown browser/runtime evidence with artifact and AI metadata verification.
- Large-PDF soak, concurrency, error-path, and rollback/recovery validation, unless Director explicitly defers them from production release scope.

## Director Decision Items

- Whether this iteration is targeting production release readiness, continued manual-review hardening, Phase 2 planning, or iteration closure.
- Whether large-PDF soak, concurrency validation, and rollback rehearsal are mandatory before release or can be staged after a limited internal release.
- Whether production workspace local `docker-compose.override.yml` should be preserved as local runtime configuration, normalized into documented deployment config, or reviewed separately.
- Whether to authorize any future production restart/rebuild/rollback rehearsal window.
- Whether single-operator/no-auth local deployment is acceptable for the intended release audience.

## Commands Run

| Command | Exit | Evidence |
| --- | ---: | --- |
| `git status --short --branch` | 0 | Dev workspace clean: `## main...origin/main`. |
| `git fetch origin` | 0 | Completed without output. |
| `git pull --ff-only origin main` | 0 | `Already up to date.` |
| `sed -n '1,260p' TaskAndReport/..._TASK.md` | 0 | Read Lucia task brief. |
| `sed -n '1,220p' docs/codex/TEAM_CONTRACT.md` | 0 | Read team contract. |
| `sed -n '1,220p' docs/codex/roles/lucode.md` | 0 | Read Lucode role. |
| `sed -n '1,220p' docs/codex/PROJECT_STATE.md` | 0 | Read current project ledger. |
| `sed -n '220,520p' docs/codex/PROJECT_STATE.md` | 0 | Read validation ledger and technical debt. |
| `sed -n '1,220p' docs/codex/HANDOFF.md` | 0 | Read handoff. |
| `sed -n '1,220p' docs/codex/TEST_POLICY.md` | 0 | Read validation policy. |
| `sed -n '1,220p' docs/reviews/PHASE1_ACCEPTANCE_SUMMARY.md` | 0 | Read Phase 1 acceptance summary. |
| `sed -n '538,590p' docs/prd/Luceon2026-PRD-v0.4.md` | 0 | Read UAT/Tier 2 Standard and risk sections. |
| `rg -n '12\\.4|Tier 2|生产|release|验收|并发|回滚|权限|安全|大文件|large|folder|文件夹|错误' docs/prd/Luceon2026-PRD-v0.4.md` | 0 | Located relevant PRD passages. |
| `git log -1 --oneline` | 0 | `19e2465 docs: issue release readiness gap task`. |
| `curl -fsS 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true'` | 0 | `ok=true`, `blocking=false`, `mineru.submitProbe.ok=true`, `mineru.submitProbe.status=202`, `ollama.ok=true`. |
| `curl -fsS http://localhost:8081/__proxy/upload/ops/dependency-repair/status` | 0 | `ok=true`, sidecar managed, MinerU/Ollama reachable but unmanaged by expected tmux sessions. |
| `sed -n '1,220p' scripts/tier2-standard-check.mjs` | 0 | Confirmed Tier 2 check requires MinerU submit probe and Ollama model. |
| `git status --short --branch` in production workspace | 0 | `## main...origin/main [behind 2]`; `M docker-compose.override.yml`. |
| `git log -1 --oneline` in production workspace | 0 | `4cc6d3e docs: accept observation semantics and assign deployment validation`. |
| `curl -fsS http://localhost:8081/__proxy/db/health` | 0 | DB health `ok=true`. |

## Skipped Checks

- `npx pnpm@10.4.1 exec tsc --noEmit`, `npx pnpm@10.4.1 run build`, UAT, Tier 2, deep MinerU checks, and smoke tests were not run because this Lucia task is non-destructive analysis/planning and only required read-only inspection plus optional runtime health checks.
- No Docker build, pull, restart, compose up/down, service restart, DB mutation, MinIO mutation, task mutation, or cleanup was run because the task explicitly forbids production runtime mutation and destructive operations.
- No large-PDF, concurrency, rollback, or error-path validation was run because this task's objective is to produce the plan for those validations, not execute them.

## Runtime Evidence

- Runtime dependency health endpoint was reachable at `http://localhost:8081`.
- MinerU `/health` and `/tasks` submit probe both passed through backend dependency-health.
- MinIO was reported `ok=true`.
- Ollama was reported `ok=true`, `chatOk=true`, model `qwen3.5:9b`.
- Ops status reported sidecar present and services reachable, while MinerU/Ollama were not managed by expected `luceon-*` tmux sessions; this is an ops-readiness warning, not a current dependency outage.
- DB health endpoint returned `ok=true`.

## Risks And Residual Debt

- Production release readiness is still blocked by unexecuted large-PDF soak, concurrency, error-path, recovery/rollback, and deployment repeatability validation.
- Production workspace is behind `origin/main` and has a local modified override file; this is acceptable for observation but must be explicitly decided before any release candidate is named.
- Docker frontend base-image metadata resolution remains a release preflight risk.
- Documentation has a minor historical mismatch: `docs/reviews/PHASE1_ACCEPTANCE_SUMMARY.md` still records TD-001 as open, while `docs/codex/PROJECT_STATE.md` records it closed after the MinerU submit-path probe. Lucia should decide whether to update the historical summary or leave it as a dated snapshot.
- `server/upload-server.mjs` remains monolithic and should not be refactored inside release validation unless Lucia issues a dedicated task.

## GitHub Sync Status

- Development workspace was synced with `origin/main` before execution.
- Report and task tracking update are intended to be committed and pushed to GitHub `main`.
- Final pushed commit: `FINAL_COMMIT_PLACEHOLDER`.

## Required Next Review

- Lucia review is required.
- Director decisions are required for release route, rollback/restart authorization, large-PDF/concurrency/error-path release scope, and single-operator security boundary.
- Recommended next Lucode task after Lucia review: P0 release-candidate preflight and validation execution, if Director/Lucia chooses to continue toward release readiness.
