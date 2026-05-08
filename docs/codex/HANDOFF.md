# Codex Handoff

Last updated: 2026-05-08

## Current Entry Point

Read these files first:

1. `docs/codex/PROJECT_STATE.md`
2. `docs/codex/TEAM_CONTRACT.md`
3. `docs/codex/roles/lucia.md` or `docs/codex/roles/lucode.md`
4. `docs/reviews/PHASE1_ACCEPTANCE_SUMMARY.md`
5. `docs/codex/REPOSITORY_STRUCTURE.md`
6. `docs/codex/TEST_POLICY.md`
7. `docs/prd/Luceon2026-PRD-v0.4.md`
8. `TaskAndReport/TASK_TRACKING_LIST.md`

Current active development workspace:

- Path: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Branch: `main`
- Durable sync source: GitHub `origin/main`
- Package manager: `npx pnpm@10.4.1`

## Current Phase 1 Baseline

The accepted Phase 1 mainline is local real runtime validation:

- Frontend route: `/cms/tasks`
- Parser: local conda MinerU FastAPI
- Storage: Docker MinIO
- AI: host Ollama `qwen3.5:9b`
- Strict AI mode: `DISABLE_AI_SKELETON_FALLBACK=true`, `ALLOW_AI_SKELETON_FALLBACK=false`
- Current Standard path: local MinerU + MinIO + host Ollama
- Online MinerU v4: compatibility-only unless explicitly assigned

Production release readiness is not claimed by this handoff.

## 2026-05-06 Governance Closure

Repository governance archived historical plans and reviews, removed confirmed obsolete code and dependency drift, aligned UAT with current routes and runtime, and updated the project ledger.

Validation commands recorded as PASS:

```bash
npx pnpm@10.4.1 install --frozen-lockfile
npx pnpm@10.4.1 exec tsc --noEmit
npx pnpm@10.4.1 run build
node server/tests/worker-smoke.mjs
node server/tests/dependency-supervisor-smoke.mjs
BASE_URL=http://localhost:8081 bash uat/smoke-test.sh
DB_BASE_URL=http://localhost:8081/__proxy/db node server/tests/mineru-deep-check.mjs
BASE_URL=http://localhost:8081 npx pnpm@10.4.1 --dir uat exec playwright test tests/pages-smoke.spec.ts
BASE_URL=http://localhost:8081 npx pnpm@10.4.1 --dir uat exec playwright test tests/cms-uat.spec.ts
BASE_URL=http://localhost:8081 npx pnpm@10.4.1 --dir uat exec playwright test tests/pipeline-consistency.spec.ts
```

## Role Boundary

- `Lucia`: product研发总监, Director's senior advisor, PRD and project-documentation owner, task brief author, report reviewer, and project-ledger maintainer.
- `Lucode`: development and testing manager, scoped implementation executor, test executor, completion reporter, and GitHub synchronization owner for assigned repository changes.

## Known Open Boundaries

- MinerU submit-path probing is implemented on `main` and accepted in local rebuilt-runtime Tier 2 Standard validation.
- Production manual-review URL is `http://localhost:8081/cms/`; current follow-up is to restore `luceon-supervisor` and `luceon-sidecar` without restarting MinerU.
- Manual-review failed task `task-1778118934116` is an AI metadata timeout after MinerU completed, not current evidence of MinerU parse failure.
- `server/upload-server.mjs` remains a monolithic server and should not be modularized inside Phase 1 closure.
- Legacy redirects remain for `/cms/source-materials` and `/cms/workspace`.
- Large-PDF soak, concurrent upload, permissions/security, rollback rehearsal, folder upload, and all error-path validation remain outside this governance pass.

## First Commands In A Fresh Checkout

```bash
git status --short --branch
npx pnpm@10.4.1 install --frozen-lockfile
npx pnpm@10.4.1 exec tsc --noEmit
npx pnpm@10.4.1 run build
npx pnpm@10.4.1 run tier2:standard:check
```

Use `docs/codex/PROJECT_STATE.md` as the current ledger. Do not promote historical archive files back into active truth without new validation evidence.

## 2026-05-07 Team Contract Update

The active collaboration team has been reset to the Director, Lucia, and Lucode model.

- `Lucia`: product研发总监 and Director's senior advisor. Lucia owns goal discussion, implementation route analysis, PRD maintenance, project ledger maintenance, task brief writing, report review, and accepted-fact recording.
- `Lucode`: development and testing manager. Lucode executes only Lucia task briefs, performs scoped implementation and testing, reports evidence, and synchronizes repository changes when required.

Historical role files are not active. Current role truth is stored in:

- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/lucia.md`
- `docs/codex/roles/lucode.md`
- `docs/codex/TASK_BRIEF_TEMPLATE.md`

## 2026-05-07 TaskAndReport Handoff Update

Lucia task briefs and Lucode reports are now exchanged through `TaskAndReport/`, not through Director chat relay.

- Task ledger: `TaskAndReport/TASK_TRACKING_LIST.md`
- Task brief naming: `YYYY-MM-DDTHH-MM-SS+0800_<Task-Name>_TASK.md`
- Report naming: `YYYY-MM-DDTHH-MM-SS+0800_<Task-Name>_REPORT.md`
- Controlled statuses: `下达待执行`, `执行中`, `已回报待审`, `退回待修正`, `修正中`, `修正回报待审`, `完成关闭`, `失败关闭`, `取消`, `挂起`
- Required tracking fields: `Next Actor`, `Next Action`, `Required Output`

Current active tasks:

- `TASK-20260509-004345-P0-MinerU-Completed-After-Local-Timeout-Takeover-Code-Fix`: returned to Lucode for correction. Lucode must explicitly set final task metadata `mineruStatus='completed'` in the resumed/takeover completion path and add focused assertions for final task metadata in both new takeover paths. This task must not mutate production task `task-1778249434820`, production DB/MinIO/logs/samples/secrets/override/Docker/services, or create production uploads/retries/reparse. Production recovery requires separate Director authorization after code-level review.

Director shorthand is active:

- `Lucia, check task`: inspect `TaskAndReport/` for rows with `Next Actor=Lucia`.
- `Lucode, check task`: inspect `TaskAndReport/` for rows with `Next Actor=Lucode`.
- If a row names the role as `Next Actor`, execute `Next Action` or write a blocked report; state-only replies are not sufficient.
- If no actionable task/report exists for that role, report no new item and wait.

## 2026-05-08 Director Decision And Heartbeat Autonomy Update

Director decision waits must be recorded in `TaskAndReport/TASK_TRACKING_LIST.md` with `Status=挂起`, `Next Actor=Director`, a specific `Next Action`, and a concrete `Required Output`.

Lucia heartbeat checks must inspect both `Next Actor=Lucia` rows and recorded `Next Actor=Director` decision rows. If a Director decision remains unanswered after two Lucia heartbeat checks, or Lucia detects a task-flow deadlock, Lucia may make the smallest responsible decision needed to continue iteration.

This autonomy cannot be used for production release approval, destructive production operations, secret changes, DB/MinIO/Docker-volume deletion or mutation, broad architecture rewrites, or material product-scope expansion. Those items remain Director-owned.

Any autonomous decision must be recorded in the task row notes and in the relevant review, task, project-state, or handoff document before assigning the next actor.

## 2026-05-08 No-Idle Ledger Update

The task ledger must not have Director, Lucia, and Lucode all idle unless Director explicitly closes the iteration stream and that closure is recorded.

When all executable tasks are closed, Lucia must either create the next bounded Lucode task or record a Director decision row. The current active decision row asks Director to choose the next Phase 1-to-next-iteration route.

At `2026-05-08T10:19:44+0800`, the Director decision row reached two unanswered Lucia heartbeat checks. Lucia applied the conservative default and issued `TASK-20260508-101944-P0-Production-Release-Readiness-Gap-Matrix-And-Validation-Plan` to Lucode.

Lucia accepted that gap matrix at `2026-05-08T10:41:37+0800`. Director-owned release-scope decisions are now recorded in task 19, and non-destructive release-candidate preflight evidence collection is assigned to Lucode in task 20.

Lucia accepted the task 20 evidence pack at `2026-05-08T11:00:44+0800`. Director task 19 remains pending and reached two heartbeat checks; Lucia fallback is limited to non-destructive validation/docs. Task 21 is assigned to Lucode for standard checks and documentation drift inspection.

Lucia accepted task 21 at `2026-05-08T11:20:00+0800`. Standard non-destructive checks passed, including TypeScript, build, dependency-health smoke, Tier 2 Standard, UAT smoke, and read-only runtime health checks. `docs/reviews/PHASE1_ACCEPTANCE_SUMMARY.md` is now explicitly marked as a dated 2026-05-06 snapshot; current status remains in `PROJECT_STATE.md` and `TaskAndReport/`. Production release readiness remains unclaimed.

Director approved the layered release-readiness preparation decision for task 19. Production release readiness remains unclaimed. Production restart/rebuild/deploy/rollback, Docker pull/build/compose, production data mutation, secret changes, and external/multi-user release boundary acceptance remain unauthorized without separate Director approval. Lucia issued task 22 for read-only production workspace override boundary review.

Lucia accepted task 22 at `2026-05-08T12:08:51+0800`. The production override is classified as local runtime configuration with one local-admin exposure boundary: strict AI/model env should be preserved; MinIO console `19001:9001` must be documented or separately changed before release-candidate naming. Task 23 is assigned to document this contract.

Lucia accepted task 23 at `2026-05-08T12:30:45+0800`. `docs/deploy/DEPLOY.md` now records the production-local override contract. Production release readiness remains unclaimed, and production sync/rebuild/restart/rollback, Docker pull/build/compose, data mutation, secret changes, and override mutation remain unauthorized without a separate Director decision and Lucia task.

Director closed task 24 by selecting option 2. Before release-candidate naming, MinIO console exposure must be narrowed to local-only binding; current `19001:9001` exposure is not accepted as-is; complete removal is not required now. Strict AI/model settings remain in production-local `docker-compose.override.yml` for now. Actual production override mutation still requires separate Director approval.

Lucia accepted task 25 at `2026-05-08T12:52:45+0800`. The accepted plan changes MinIO console mapping from `"19001:9001"` to `"127.0.0.1:19001:9001"` while preserving strict AI/model settings unchanged. No production mutation, Docker command, runtime/data/secret mutation, or release-readiness claim occurred.

Director closed task 26 by approving a scoped implementation task. Lucia issued task 27. The approved scope is limited to the MinIO console mapping change, preservation of strict AI/model settings, and non-destructive validation. Production release readiness remains unclaimed.

Lucia accepted task 27 at `2026-05-08T14:05:45+0800`. The production-local MinIO console mapping is now `"127.0.0.1:19001:9001"`, strict AI/model settings remain unchanged, listener inspection shows `127.0.0.1:19001`, local console/CMS/dependency-health checks passed, and no DB/MinIO data/Docker volume/task/artifact/secret mutation or release-readiness claim occurred.

Director closed task 28 by approving the staged runtime-validation wave. Lucia issued task 29 first: large-PDF soak validation. Still forbidden: production release-readiness declaration, DB row deletion, MinIO object deletion, Docker volume deletion/pruning, secret changes, broad deploy/rollback, and external/multi-user release boundary acceptance.

Lucia accepted task 29 as failed evidence at `2026-05-08T14:48:15+0800`. The preferred large PDF `G7_Workbook_ready_to_print.pdf` reached terminal `failed` at AI stage. MinerU and MinIO succeeded; Ollama `qwen3.5:9b` timed out after about `300000ms`; strict no-skeleton fallback was preserved. Task 30 is assigned for non-destructive AI large-input timeout diagnosis and remediation planning.

Lucia accepted task 30 at `2026-05-08T14:59:45+0800`. The accepted diagnosis is that task 29 failed primarily because the first-pass AI metadata input remained on the legacy sampler path and reached about `83k` prompt payload characters. Task 31 is assigned to implement adaptive evidence-pack first-pass selection with thresholds of Markdown length greater than `50000`, source file size greater than `10000000` bytes, or parsed files count greater than `50`. Strict no-skeleton behavior must remain unchanged, and production runtime validation must be assigned separately after code-level acceptance.

Lucia accepted task 31 at `2026-05-08T15:11:45+0800` as code-level implementation. The accepted code selects evidence-pack mode for Markdown length greater than `50000`, source file size greater than `10000000` bytes, or parsed files count greater than `50`; short documents remain on legacy sampling; strict no-skeleton behavior remains unchanged. Lucia independently reran the focused evidence-pack smoke, real-sample smoke, dependency-health smoke, TypeScript check, production build, and diff check. Task 32 records the Director decision required before scoped production deployment/runtime validation.

Task 32 reached two Lucia heartbeat checks without a Director decision at `2026-05-08T15:41:15+0800`. Lucia did not authorize production validation autonomously. To prevent task-flow stalling, Lucia issued task 33 for non-destructive production validation runbook and read-only preflight preparation only.

Lucia accepted task 33 at `2026-05-08T16:02:45+0800`. Accepted preflight facts: production workspace remains at `4cc6d3e` behind `origin/main c882e2b`, production override preserves strict AI/model and `127.0.0.1:19001:9001`, preferred large-PDF sample size/hash match prior evidence, active tasks/jobs were `0`, DB health was OK, and dependency health was non-blocking but Ollama was false. No production mutation or release-readiness claim occurred. Task 32 remains the active Director decision before any scoped production validation.

Director approved task 32 at `2026-05-08T17:31:00+0800`. Lucia issued task 34 for one scoped production validation only. Authorized scope: apply accepted `main` code to production as needed, preserve production-local override boundaries, use minimum necessary Docker/Compose action, run preflight checks, and create at most one controlled large-PDF validation upload if preflight passes. Still forbidden: production release-readiness declaration, DB row deletion, MinIO object deletion, Docker volume deletion/pruning, secret changes, broad rollback, model/timeout changes, skeleton fallback, silent degradation, and external/multi-user release boundary acceptance.

Lucia accepted task 34 at `2026-05-08T18:09:49+0800` as blocked evidence. Production reached `8092965`, upload-server was rebuilt, strict AI/model and MinIO local-only override boundaries were preserved, CMS/DB/MinIO/MinerU submit probe passed, active tasks/jobs were `0`, and the preferred sample size/hash matched. The controlled upload was not created because pre-upload dependency health reported Ollama `qwen3.5:9b` chat-smoke timeout. Task 35 is assigned for non-destructive Ollama readiness diagnosis and recovery planning.

Lucia accepted task 35 at `2026-05-08T18:19:15+0800`. Diagnosis: Ollama `qwen3.5:9b` exists and became ready without mutation; cold probes spent about `8.9s` loading and `9.7s` to `10.6s` total, while warm chat dropped to about `1.35s` and warm dependency health to `793ms`. This supports transient cold-load/readiness behavior under memory pressure rather than model absence. Task 36 is assigned for one scoped validation retry, gated by immediate warm dependency-health pass.

Lucia accepted task 36 at `2026-05-08T18:31:29+0800` as blocked evidence. Immediate pre-upload dependency health failed Ollama readiness again at about `15001ms`, and no controlled upload was created. Direct read-only chat after the stop condition loaded the model in about `6.7s` and succeeded, reinforcing cold-load/model-residency instability. Director decision task 37 is now pending: approve bounded non-mutating Ollama warm-up before a single controlled validation upload, request more diagnosis only, or hold validation.

Director approved task 37 at `2026-05-08T18:38:44+0800`. Approved scope is limited to one bounded non-mutating Ollama warm-up/readiness step before validation, followed by warm dependency-health with `mineruSubmitProbe=true`; if it passes, Lucode may create at most one controlled validation upload. Still forbidden: production release-readiness declaration, deploy/fast-forward/rebuild/restart/rollback/Docker mutation, Ollama restart/kill/start/reload, model/timeout/config/secret/override changes, data/artifact/log deletion, skeleton fallback, silent degradation, or more than one controlled upload. Task 38 is assigned to Lucode.

Lucia accepted task 38 at `2026-05-08T19:10:21+0800` as controlled production validation. The authorized large-PDF sample created task `task-1778237744029`, MinerU completed with `parsedFilesCount=99`, AI reached `review-pending`, and adaptive input selection used `evidence-pack-v0.3` with selected length `16261`. Production release readiness remains unclaimed. Residual risks: cold-load warm-up remains operationally important, first-pass JSON repair was still needed, and MinerU observation was stale/completed-window backfill. Director decision task 39 is pending for the next release-readiness validation track.

Director selected `CONCURRENCY_VALIDATION_FIRST` for task 39 at `2026-05-08T19:17:09+0800`. Lucia issued task 40 for concurrency validation planning and non-destructive preflight only. Lucode may inspect the external sample directory `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/4.XxwlAs2026/sample` as read-only inventory, but must not sync it to GitHub, modify, move, delete, or pollute samples. No production upload is authorized in task 40.

Lucia accepted task 40 at `2026-05-08T19:34:39+0800` as planning/preflight evidence. Lucode reported `PLAN_READY`, active tasks/jobs `0`, MinIO/MinerU OK, initial Ollama timeout at about `14999ms`, one bounded non-mutating warm-up success, and warm dependency-health success with `ollama.durationMs=699`. Lucia initially recorded task 41 for Director approval of a concurrency run.

Director rejected concurrency for task 41 and corrected Lucia's interpretation. The intended model is stage-queued流水, not full end-to-end serial blocking: after one sample completes upload/MinIO intake, the next sample may be accepted; MinerU parsing must queue by stage; Ollama metadata recognition must queue by stage. The true sample directory is `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/4.XxwlAs2026/sample`; it is read-only inventory and must not be synced to GitHub, modified, moved, deleted, normalized, or polluted. Task 42 replaces the concurrency path with stage-queued planning/preflight only; no production upload is authorized yet.

Lucia returned the first task 42 report at `2026-05-08T20:39:35+0800`. The report's preflight evidence is useful, but its proposed plan incorrectly required per-sample terminal state before the next upload. That is full end-to-end serial blocking, not Director's intended stage-queued流水. Lucode must revise the report before Lucia can issue any validation-run task.

Lucia accepted the revised task 42 report at `2026-05-08T21:43:25+0800`. The revised plan now correctly uses upload/storage intake durability as the next-upload handoff and requires MinerU/Ollama heavy-stage active counts to stay `<=1`. Because the next run would create production validation artifacts, Director decision task 43 is pending before Lucode may execute it. If unanswered after two Lucia heartbeat checks, Lucia's allowed fallback is only Option B: first two samples under the same stage-queued boundaries, with no release-readiness claim or destructive/service/config/data mutation.

Director approved Option A for task 43 at `2026-05-08T21:51:38+0800`. Lucia issued task 44 for up to three controlled true-directory uploads under stage-queued rules. Next upload may start after prior upload/storage intake is durable; MinerU active parse-running and Ollama active metadata-running counts must stay `<=1`. Production release readiness, production deploy/rebuild/restart/rollback/Docker mutation, service/config/model/secret/override changes, data deletion, sample mutation/sync, skeleton fallback, and silent degradation remain forbidden.

Lucia accepted task 44 at `2026-05-08T23:44:38+0800` as partial validation evidence. Samples 1 and 2 reached `review-pending`; stage-queued heavy-stage active counts stayed `<=1`; no forbidden mutation or release-readiness claim occurred. Sample 3 `task-1778249434820` remains unresolved: Lucia's read-only refresh showed `running` / `mineru-processing`, local wait timeout, stale MinerU log observation, observed page progress `714/714`, and no AI metadata job. Task 45 is assigned for read-only diagnosis only.

Lucia accepted task 45 at `2026-05-09T00:43:45+0800`. Diagnosis: MinerU API says the underlying MinerU task is `completed` and the result ZIP is available, but Luceon has not ingested the result and still shows the task/material as processing with no AI job. This is a terminal-state propagation / result-ingestion stuck state after local timeout. Task 46 is assigned for code-level correction only; production write-side recovery is not authorized yet.

Lucia returned the first task 46 implementation at `2026-05-09T01:44:51+0800`. Independent checks passed, but the final resumed/takeover completion metadata can still omit `mineruStatus='completed'` on the task record. Lucode must correct that and add focused assertions before Lucia can accept code-level integration. No implementation was merged to main.

Lucia accepted the revised task 46 implementation at `2026-05-09T02:42:47+0800` as `ACCEPTED_CODE_LEVEL`. The accepted code explicitly writes final task metadata `mineruStatus='completed'` in the completed-after-local-timeout takeover path, and focused smokes assert that final task metadata in both new paths. Lucia independently reran diff-check, `mineru-no-resubmit-smoke`, `mineru-timeout-adjudication-smoke`, TypeScript, and build.

Current active task: task 47, Director decision. Director must decide whether to authorize a scoped production recovery for stuck sample 3 task `task-1778249434820` / material `mat-1778249419780`, hold recovery, or request more read-only evidence. Lucia may not autonomously authorize production write-side recovery after heartbeat waits because it can mutate production task/material/AI-job state.

Heartbeat wait evidence for task 47: Lucia check 1 at `2026-05-09T03:42:47+0800` found no Director answer yet. The active next actor remains Director.

Heartbeat wait evidence for task 47: Lucia check 2 at `2026-05-09T04:42:47+0800` also found no Director answer. The two-heartbeat threshold is reached, but Lucia cannot autonomously authorize production write-side recovery because it may mutate production task/material/AI-job state. The active next actor remains Director.

Director approved scoped production recovery for task 47 at `2026-05-09T05:20:30+0800`. Lucia issued task 48 to Lucode. Current active task: task 48, Lucode execution. Scope is limited to recovering only production task `task-1778249434820` / material `mat-1778249419780` using the accepted Task 46 fix and existing MinerU task/result. Production release readiness remains unclaimed, and broad deploy/rebuild/restart/rollback, data deletion, secret/model/config/override changes, unrelated task recovery, new upload creation, or a second MinerU submission remain forbidden.
