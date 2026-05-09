# Luceon2026 Project State

Last updated: 2026-05-09

## 1. Current Repository Baseline

- Active workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Branch: `main`
- Remote sync baseline before this governance pass: `origin/main` at `22857e9d83f7598e508f4b2827480c2ec166b96d`
- Package manager: `npx pnpm@10.4.1`
- Root lockfile: `pnpm-lock.yaml`
- Removed lockfile class: root `package-lock.json` and UAT-local `package-lock.json`
- Production release readiness: not claimed by this record.

## 2. Phase 1 Mainline Architecture Snapshot

The current first-phase mainline is the local real runtime path:

1. Operator uploads a document through `/cms/tasks`.
2. `server/upload-server.mjs` stores the raw object in MinIO and creates a `Material` plus a `ParseTask`.
3. `server/services/queue/task-worker.mjs` processes `local-mineru` tasks.
4. Local conda MinerU FastAPI parses PDF inputs; Markdown inputs bypass MinerU and write canonical `full.md`.
5. Parsed artifacts are stored in MinIO under `parsed/{materialId}/`, with `artifact-manifest.json` as the durable large-artifact index.
6. `server/services/ai/metadata-worker.mjs` creates and processes AI metadata jobs through host Ollama `qwen3.5:9b`.
7. High-confidence or accepted results reach `completed`; low-confidence AI results reach `review-pending` and are shown to the operator as `待复核`.

Current runtime dependencies:

| Dependency | Current mainline |
| --- | --- |
| Frontend | React/Vite SPA under `/cms`; `/cms/tasks` is the main workbench |
| Upload/API | Express upload server behind `/__proxy/upload` |
| Data API | Express JSON DB server behind `/__proxy/db` |
| Storage | Docker MinIO with raw and parsed buckets |
| Parser | Local conda MinerU FastAPI, default `http://host.docker.internal:8083` in containers |
| AI | Host Ollama, required model `qwen3.5:9b` |
| Strict AI mode | `DISABLE_AI_SKELETON_FALLBACK=true`, `ALLOW_AI_SKELETON_FALLBACK=false` |
| Online MinerU | Compatibility-only; not part of the current main gate unless explicitly assigned |

## 3. Governance Closure Summary

Completed on 2026-05-06:

- Archived 27 historical `.codebuddy/plans/` files to `archive/phase1-governance-2026-05-06/codebuddy-plans/`.
- Archived 15 historical `docs/reviews/` files to `archive/phase1-governance-2026-05-06/docs-reviews/`.
- Added archive manifest: `archive/phase1-governance-2026-05-06/MANIFEST.md`.
- Replaced active review sprawl with `docs/reviews/README.md` and `docs/reviews/PHASE1_ACCEPTANCE_SUMMARY.md`.
- Removed obsolete online MinerU v4 batch parsing script: `scripts/test-mineru-v4-batch-parsing.mjs`.
- Renamed `src/store/mockData.ts` to `src/store/seedData.ts`.
- Removed dependency-supervisor test-only mock execution path.
- Removed non-`local-mineru` simulated worker-success path from the runtime worker; unsupported parse engines now fail fast.
- Decoupled strict AI skeleton fallback flags from MinerU online mode selection.
- Rewrote Tier 2 Standard configuration toward local MinerU + MinIO + host Ollama `qwen3.5:9b`.
- Removed unused npm dependency groups from `package.json` and regenerated `pnpm-lock.yaml`.
- Added `uat` to the pnpm workspace and removed local lockfile drift.
- Moved deployment documentation to `docs/deploy/DEPLOY.md`.
- Moved long-form historical project notes to `docs/codex/PROJECT_HISTORY.md`.
- Removed unreferenced root theme artifact `default_shadcn_theme.css`.
- Added root-directory policy: `docs/codex/REPOSITORY_STRUCTURE.md`.
- Aligned UAT route semantics: `/cms/tasks` is the main route; `/cms/source-materials` and `/cms/workspace` are legacy redirects.
- Removed explicit skip markers from active UAT suites.
- Repaired stale comments, mojibake text, and misleading pending-comment wording found during governance scans.

Team contract updated on 2026-05-07:

- Active collaboration roles are Director, Lucia, and Lucode.
- Lucia is the product研发总监 and Director's senior advisor; Lucia owns PRD, project ledger, handoff, role contract, task brief, and report-review responsibilities.
- Lucode is the development and testing manager; Lucode executes only Lucia task briefs and reports completion in a standard copyable format.
- Historical role files are retired and not active project roles.
- Current role truth is stored in `docs/codex/TEAM_CONTRACT.md`, `docs/codex/roles/lucia.md`, `docs/codex/roles/lucode.md`, and `docs/codex/TASK_BRIEF_TEMPLATE.md`.
- Task briefs and reports are stored in `TaskAndReport/` and tracked in `TaskAndReport/TASK_TRACKING_LIST.md`.
- Task tracking rows include `Status`, `Next Actor`, `Next Action`, and `Required Output` to prevent handoff stalls.
- First registered task: `TASK-20260507-063238-P0-MinerU-Submit-Path-Health-Probe`, current status `完成关闭`, no next actor.
- Local test sample library: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/4.XxwlAs2026/sample`. This external directory may be used as a read-only source of validation inputs, may receive additional samples over time, must not be synchronized to GitHub, and must not be deleted, moved, renamed, modified, or polluted during Luceon testing. Reports may record paths, sizes, hashes, and validation evidence.

Collaboration automation updated on 2026-05-08:

- Director decision waits must be recorded in `TaskAndReport/TASK_TRACKING_LIST.md` with `Status=挂起`, `Next Actor=Director`, a specific `Next Action`, and a concrete `Required Output`.
- The `lucia` heartbeat inspects Lucia-owned rows and Director decision rows.
- If a Director decision remains unanswered after two Lucia heartbeat checks, or if Lucia detects task-flow deadlock, Lucia may make the smallest responsible decision needed to continue within documented safety boundaries.
- The task ledger must not leave Director, Lucia, and Lucode all idle unless Director explicitly closes the iteration stream.
- Director decision row `TASK-20260508-095802-P0-Phase-1-Next-Iteration-Route-Decision` reached two unanswered Lucia heartbeat checks on 2026-05-08.
- Lucia applied the conservative default and issued `TASK-20260508-101944-P0-Production-Release-Readiness-Gap-Matrix-And-Validation-Plan`.
- This autonomous action authorizes analysis and planning only. It does not approve production release readiness, destructive production operations, secret changes, DB/MinIO/Docker volume mutation, broad architecture rewrite, or material product-scope expansion.
- Lucia accepted the release-readiness gap matrix on 2026-05-08. Accepted boundary: manual-review readiness has supporting evidence, while production release readiness remains unclaimed.
- Director-owned release-scope decisions are tracked in `TASK-20260508-104137-P0-Director-Release-Readiness-Scope-Decisions`.
- Non-destructive release-candidate preflight evidence collection in `TASK-20260508-104137-P0-Release-Candidate-Non-Destructive-Preflight-And-Evidence-Pack` was accepted on 2026-05-08.
- Accepted evidence: development TypeScript/build/dependency-health-smoke passed; read-only runtime dependency-health with MinerU submit probe and DB health passed; production workspace remains behind `origin/main` with local `docker-compose.override.yml` modification.
- Director task 19 reached two unanswered Lucia heartbeat checks. Lucia fallback remains limited to non-destructive validation/docs and does not authorize production release approval, restart/rebuild/rollback, production mutation, secret changes, or release-scope acceptance.
- Non-destructive standard checks and documentation drift inspection are assigned to `TASK-20260508-110044-P0-Release-Candidate-Standard-Checks-And-Docs-Reconciliation`.
- Lucia accepted task 21 on 2026-05-08. Accepted evidence: TypeScript, build, dependency-health smoke, Tier 2 Standard, UAT smoke, dependency-health with MinerU submit probe, dependency repair status, and DB health passed under non-destructive constraints.
- `docs/reviews/PHASE1_ACCEPTANCE_SUMMARY.md` is marked as a dated 2026-05-06 snapshot; current technical-debt and release-readiness status remain governed by this project state ledger and `TaskAndReport/`.
- Director approved continuing toward production release-readiness preparation, while keeping production release readiness unclaimed.
- Mandatory before any production release-readiness claim: large-PDF soak, concurrency validation, error-path matrix, rollback/recovery rehearsal, production workspace boundary review, `docker-compose.override.yml` boundary review, Docker frontend base-image preflight, and single-operator/no-auth security boundary decision.
- Not authorized without separate Director approval: production release-readiness declaration, production restart/rebuild/deploy/rollback, DB/MinIO/Docker volume/task/artifact/secret mutation, Docker pull/build/compose operations affecting production, and external/multi-user release boundary acceptance.
- Production workspace override boundary review is assigned to `TASK-20260508-113500-P0-Production-Workspace-Override-Boundary-Review`.
- Lucia accepted the production workspace override boundary review on 2026-05-08. Accepted classification: strict AI/model override values are local runtime configuration that should be preserved; MinIO console `19001:9001` is a local-admin exposure boundary that must be documented or separately changed before release-candidate naming.
- Production-local override contract documentation is assigned to `TASK-20260508-120851-P0-Production-Local-Override-Contract-Documentation`.
- Lucia accepted task 23 on 2026-05-08. `docs/deploy/DEPLOY.md` now records the production-local override contract: strict AI/model override values are required runtime semantics, MinIO console `19001:9001` is a local-admin exposure boundary, and release-candidate naming requires exact production HEAD plus override-boundary confirmation. This documentation does not claim production release readiness and does not authorize production sync, rebuild, restart, rollback, Docker operations, data mutation, or override mutation.
- Director closed `TASK-20260508-123045-P0-Production-Override-Release-Boundary-Decision` on 2026-05-08. Decision: before release-candidate naming, MinIO console exposure must be narrowed to local-only binding; current `19001:9001` exposure is not accepted as-is; complete removal is not required at this stage; strict AI/model configuration remains in production-local `docker-compose.override.yml` for now; actual production override mutation still requires separate Director approval.
- Lucia accepted non-destructive local-only binding change planning in `TASK-20260508-123816-P0-MinIO-Console-Local-Only-Binding-Change-Plan`. Accepted proposed mapping: change MinIO console exposure from `"19001:9001"` to `"127.0.0.1:19001:9001"` in production-local override, while preserving strict AI/model settings unchanged.
- Director closed `TASK-20260508-125245-P0-MinIO-Console-Local-Only-Implementation-Authorization` on 2026-05-08 by approving a scoped implementation task. Authorized scope: change production-local MinIO console mapping from `"19001:9001"` to `"127.0.0.1:19001:9001"`, preserve strict AI/model settings unchanged, and run only minimum necessary Docker/Compose operations and non-destructive checks to apply and verify the binding.
- Lucia accepted scoped production-local override implementation in `TASK-20260508-134708-P0-MinIO-Console-Local-Only-Production-Override-Implementation`. Accepted evidence: production-local MinIO console mapping is `"127.0.0.1:19001:9001"`, strict AI/model settings remain unchanged, listener is `127.0.0.1:19001`, local console and CMS are reachable, dependency-health with MinerU submit probe is non-blocking, and no DB/MinIO data/Docker volume/task/artifact/secret mutation or release-readiness claim occurred.
- Director closed `TASK-20260508-140545-P0-Release-Readiness-Runtime-Validation-Authorization` on 2026-05-08 by approving a staged release-readiness runtime-validation wave. Controlled validation artifacts may be created for evidence, but production release-readiness declaration, DB row deletion, MinIO object deletion, Docker volume deletion/pruning, secret changes, broad deploy/rollback, and external/multi-user release boundary acceptance remain forbidden.
- Lucia accepted large-PDF soak validation in `TASK-20260508-142433-P0-Large-PDF-Soak-Validation` as failed evidence. Accepted facts: `G7_Workbook_ready_to_print.pdf` created task `task-1778222027064`, MinerU completed with `parsedFilesCount=99`, MinIO raw/parsed artifacts were preserved, AI failed at stage `ai` because Ollama `qwen3.5:9b` timed out after about `300000ms`, and strict no-skeleton fallback remained enforced. Production release readiness remains unclaimed.
- Lucia accepted AI large-input timeout diagnosis and remediation planning in `TASK-20260508-144815-P0-AI-Large-Input-Timeout-Diagnosis-And-Remediation-Plan`. Accepted diagnosis: the large-PDF timeout is primarily caused by oversized first-pass AI metadata input selection, where the task 29 sample used legacy sampling at about `78084` selected characters because evidence-pack mode did not trigger. The approved first remediation direction is adaptive evidence-pack first-pass selection.
- Lucia accepted code-level adaptive evidence-pack first-pass implementation in `TASK-20260508-145945-P0-Adaptive-Evidence-Pack-First-Pass-For-Large-AI-Metadata-Inputs`. Accepted behavior: evidence-pack mode is selected when Markdown length is greater than `50000`, source file size is greater than `10000000` bytes, or parsed files count is greater than `50`; ordinary short documents remain on the legacy sampler; structured input-selection metadata is recorded; strict no-skeleton behavior remains unchanged.
- Production validation authorization for the accepted adaptive evidence-pack code is recorded in `TASK-20260508-151145-P0-Adaptive-Evidence-Pack-Production-Validation-Authorization`. Production release readiness remains unclaimed.
- Task 32 reached two Lucia heartbeat checks without Director decision on 2026-05-08. Lucia did not authorize production validation autonomously. Non-destructive runbook and read-only preflight preparation is assigned to `TASK-20260508-154115-P0-Adaptive-Evidence-Pack-Production-Validation-Runbook-And-Preflight`.
- Lucia accepted the task 33 runbook and read-only preflight on 2026-05-08. Accepted facts: production workspace remains behind accepted `main`, production override preserves strict AI/model and MinIO console local-only binding, preferred large-PDF sample size/hash match prior evidence, active tasks/jobs were `0`, DB health was OK, and dependency health was non-blocking but Ollama reported false. Actual production validation remains blocked on Director task 32.
- Director approved scoped production validation in `TASK-20260508-151145-P0-Adaptive-Evidence-Pack-Production-Validation-Authorization` on 2026-05-08. Lucia issued `TASK-20260508-173100-P0-Adaptive-Evidence-Pack-Scoped-Production-Validation` to Lucode. The authorization covers only minimum necessary production apply and one controlled large-PDF validation upload if preflight passes; production release readiness remains unclaimed.
- Lucia accepted `TASK-20260508-173100-P0-Adaptive-Evidence-Pack-Scoped-Production-Validation` as blocked evidence on 2026-05-08. Accepted facts: production workspace reached `8092965`, upload-server was rebuilt, strict AI/model and MinIO local-only override boundaries were preserved, CMS/DB/MinIO/MinerU submit probe passed, active tasks/jobs were `0`, and the controlled sample size/hash matched. Controlled upload was not created because pre-upload dependency health reported Ollama `qwen3.5:9b` chat-smoke timeout at about `15006ms`. Production release readiness remains unclaimed.
- Non-destructive Ollama readiness diagnosis is assigned to `TASK-20260508-180949-P0-Ollama-Readiness-Timeout-Diagnosis-And-Recovery-Plan`. This task may inspect but may not restart/kill/start services, mutate Docker, pull/change/delete models, change timeout/config/secrets, create uploads, delete data/artifacts/logs, or claim production release readiness.
- Lucia accepted `TASK-20260508-180949-P0-Ollama-Readiness-Timeout-Diagnosis-And-Recovery-Plan` on 2026-05-08. Accepted diagnosis: Ollama `qwen3.5:9b` exists and became ready without mutation; first direct probes showed cold-load latency around `8.9s` and total `9.7s` to `10.6s`, warm direct chat dropped to about `1.35s`, and warm dependency health reported Ollama OK in `793ms`. This supports a transient cold-load/readiness hypothesis under memory pressure, not model absence. Lucia issued `TASK-20260508-181915-P0-Adaptive-Evidence-Pack-Production-Validation-Retry`.
- Lucia accepted `TASK-20260508-181915-P0-Adaptive-Evidence-Pack-Production-Validation-Retry` as blocked evidence on 2026-05-08. Accepted facts: production code markers and override boundary were present; CMS/DB/MinIO/MinerU submit probe passed; active tasks/jobs were `0`; sample size/hash matched; but immediate pre-upload dependency-health again failed Ollama readiness at `15001ms`. A direct read-only chat after the stop condition loaded `qwen3.5:9b` in about `6.7s` and succeeded, reinforcing cold-load/model-residency instability. Director decision `TASK-20260508-183129-P0-Ollama-Warmup-Before-Validation-Authorization` is now pending before further upload validation.
- Director approved `TASK-20260508-183129-P0-Ollama-Warmup-Before-Validation-Authorization` on 2026-05-08. Approved scope: one bounded non-mutating Ollama warm-up/readiness step before validation; warm dependency-health with `mineruSubmitProbe=true` must pass afterward; at most one controlled validation upload may then be created. Still forbidden: production release-readiness declaration, deploy/fast-forward/rebuild/restart/rollback/Docker mutation, Ollama restart/kill/start/reload, model/timeout/config/secret/override changes, data/artifact/log deletion, skeleton fallback, silent degradation, or more than one upload. Lucia issued `TASK-20260508-183844-P0-Adaptive-Evidence-Pack-Warmup-Gated-Production-Validation`.
- Lucia accepted `TASK-20260508-183844-P0-Adaptive-Evidence-Pack-Warmup-Gated-Production-Validation` on 2026-05-08 as controlled production validation. Accepted facts: one bounded non-mutating Ollama warm-up succeeded; warm dependency-health with MinerU submit probe passed; exactly one controlled upload created task `task-1778237744029` and material `mat-1778237743496`; MinerU completed with `parsedFilesCount=99`; AI reached `review-pending`; adaptive input used `evidence-pack-v0.3`; selected input length was `16261`, below `30000`; trigger reasons, thresholds, observed values, input hash, and related task events were present; no skeleton fallback or forbidden operation occurred. Production release readiness remains unclaimed.
- Director decision `TASK-20260508-191021-P0-Next-Release-Readiness-Validation-Scope` is pending for the next validation track. Lucia recommends `CONCURRENCY_VALIDATION_FIRST`, but the choice remains a Director release-boundary decision.
- Director selected `CONCURRENCY_VALIDATION_FIRST` for `TASK-20260508-191021-P0-Next-Release-Readiness-Validation-Scope` on 2026-05-08. Lucia issued `TASK-20260508-191709-P0-Controlled-Concurrency-Validation-Plan-And-Preflight` as planning/preflight only. No production uploads, production release-readiness claim, destructive operations, Docker/service mutation, model/timeout/config/secret changes, data deletion, or broader release acceptance are authorized by this decision.
- Director corrected the validation model on 2026-05-08: the project must use stage-queued流水 validation, not simultaneous heavy-stage concurrency. After upload/MinIO intake is durable, the next sample may be accepted; MinerU parsing and Ollama metadata recognition must each keep active heavy-stage work `<=1`. The external true sample directory remains `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/4.XxwlAs2026/sample` and remains read-only.
- Lucia accepted `TASK-20260508-215138-P0-Stage-Queued-Sample-Validation-Run` as partial validation evidence on 2026-05-08. Accepted facts: three approved true-directory samples were uploaded under stage-queued rules; samples 1 and 2 reached `review-pending` with Ollama `qwen3.5:9b`; MinerU and Ollama active heavy-stage counts stayed `<=1`; no forbidden mutation, sample sync/modification, signed URL persistence, cleanup, fallback, silent degradation, or production release-readiness claim occurred.
- Sample 3 from that run remains unresolved and is not accepted as terminal pass evidence. Lucia read-only refresh at `2026-05-08T23:44:27+0800` showed task `task-1778249434820` still `running` / `mineru-processing`, message `本地等待超时但 MinerU 仍在 processing，后台将继续观测`, `localTimeoutOccurred=true`, observed page progress `714/714`, `observationStale=true`, and no AI metadata job. Follow-up read-only diagnosis is assigned to `TASK-20260508-234438-P0-Sample3-MinerU-Long-Processing-Read-Only-Diagnosis`.
- Lucia accepted `TASK-20260508-234438-P0-Sample3-MinerU-Long-Processing-Read-Only-Diagnosis` on 2026-05-09. Accepted diagnosis: direct MinerU API reports task `ec9452cc-94e4-4b36-bb64-efba86f38cf6` as `completed`, MinerU health reports `processing_tasks=0`, and the result ZIP is available, but Luceon task `task-1778249434820` remains `running` / `mineru-processing`, material `mat-1778249419780` remains `processing`, and no AI job exists. This is classified as terminal-state propagation / result-ingestion stuck after local timeout. Production recovery is not authorized yet; code-level correction is assigned to `TASK-20260509-004345-P0-MinerU-Completed-After-Local-Timeout-Takeover-Code-Fix`.
- Lucia returned the first task 46 implementation on 2026-05-09. The implementation direction and checks were mostly sound, but the resumed/takeover completion path did not explicitly write final task `metadata.mineruStatus='completed'`, leaving a task-level metadata drift risk too close to the production failure mode. No implementation was integrated into `main`, and production recovery remains unauthorized.

MinerU submit-path probe accepted on 2026-05-07:

- Task: `TASK-20260507-063238-P0-MinerU-Submit-Path-Health-Probe`.
- Implementation commit: `5b21ae3392a4f334b02e0ac2d75f616d4286fdfb`.
- Accepted Lucia review: `TaskAndReport/2026-05-07T08-15-58+0800_P0-MinerU-Submit-Path-Health-Probe_LUCIA_REVIEW.md`.
- Merge commit into `main`: `8201d2e903d5fa524490c17d16258f1764ce98fe`.
- Effective behavior: `/ops/dependency-health` remains lightweight by default; `mineruSubmitProbe=true` or `DEPENDENCY_HEALTH_MINERU_SUBMIT_PROBE=true` enables a bounded synthetic MinerU `/tasks` submit probe. When enabled, MinerU readiness requires both `/health` success and `/tasks` task-id success.

Rebuilt-runtime Tier 2 Standard validation accepted on 2026-05-07:

- Task: `TASK-20260507-092406-P0-Main-Rebuilt-Runtime-Tier2-Standard-Validation`.
- Lucode report: `TaskAndReport/2026-05-07T09-31-59+0800_P0-Main-Rebuilt-Runtime-Tier2-Standard-Validation_REPORT.md`.
- Lucia review: `TaskAndReport/2026-05-07T09-35-39+0800_P0-Main-Rebuilt-Runtime-Tier2-Standard-Validation_LUCIA_REVIEW.md`.
- Runtime: rebuilt local runtime at `http://localhost:8081`.
- Result: Tier 2 Standard PASS with `mineru.healthOk=true`, `mineru.submitProbe.enabled=true`, `mineru.submitProbe.ok=true`, and UAT smoke `12 passed / 0 failed / 0 skipped`.
- Boundary: this is local rebuilt-runtime Tier 2 validation only; production release readiness remains unclaimed.

Production manual-review deployment accepted with follow-up on 2026-05-07:

- Task: `TASK-20260507-094405-P0-Production-Deployment-For-Manual-Review`.
- Lucode report: `TaskAndReport/2026-05-07T09-52-08+0800_P0-Production-Deployment-For-Manual-Review_REPORT.md`.
- Lucia review: `TaskAndReport/2026-05-07T10-13-05+0800_P0-Production-Deployment-For-Manual-Review_LUCIA_REVIEW.md`.
- Production URL for Director manual review: `http://localhost:8081/cms/`.
- Deployed production HEAD: `f02684c3aee392fdc0e6a9e8fd8da911c17db892`.
- Deployment evidence: containers healthy, dependency-health `blocking=false`, `mineru.submitProbe.ok=true`, `ollama.ok=true`, and smoke `12 passed / 0 failed / 0 skipped`.
- Boundary: this is manual-review deployment only, not production release readiness.
- Follow-up task issued: `TASK-20260507-101305-P0-Production-Ops-Sidecar-Supervisor-Recovery`.

Manual-review incident facts recorded on 2026-05-07:

- Task `task-1778118934116`, file `G7_Workbook_ready_to_print.pdf`, reached `stage=ai`, `state=failed`.
- MinerU completed and produced parsed artifacts including `full.md`, `artifact-manifest.json`, `mineru-result.zip`; parsed files count was reported as `99`.
- Failure cause observed in upload-server logs: Ollama provider timeout in AI metadata recognition, model `qwen3.5:9b`, duration about `299998ms`, timeout `300000ms`.
- Strict no-skeleton behavior is preserved: the failed AI metadata stage did not silently generate skeleton metadata.
- Ops observation gap: `luceon-supervisor` and `luceon-sidecar` / `mineru-log-observer` were not running; `/ops/dependency-repair/status` returned `SUPERVISOR_UNAVAILABLE`; `/ops/mineru/global-observation` returned `{"observation":null}`.

Production ops recovery accepted on 2026-05-07:

- Task: `TASK-20260507-101305-P0-Production-Ops-Sidecar-Supervisor-Recovery`.
- Lucode reports: `TaskAndReport/2026-05-07T10-23-55+0800_P0-Production-Ops-Sidecar-Supervisor-Recovery_REPORT.md` and `TaskAndReport/2026-05-07T10-34-23+0800_P0-Production-Ops-Sidecar-Supervisor-Recovery_SUPPLEMENTAL_REPORT.md`.
- Lucia review: `TaskAndReport/2026-05-07T10-41-51+0800_P0-Production-Ops-Sidecar-Supervisor-Recovery_LUCIA_REVIEW.md`.
- Result: `luceon-supervisor` and `luceon-sidecar` were started without restarting MinerU/Ollama or mutating failed tasks.
- Follow-up tasks issued:
  - `TASK-20260507-104151-P0-Production-AI-JSON-Repair-Ollama-Timeout-Diagnosis`.
  - `TASK-20260507-104151-P1-MinerU-Sidecar-Task-Level-Log-Attribution`.

Supplemental manual-review facts recorded on 2026-05-07:

- New task `task-1778120784621`, file `走向成功_英语_二模卷16篇.pdf`, reached `stage=ai`, `state=ai-running`, message `AI: 正在进行 JSON Repair...`.
- Associated AI job `ai-job-1778120889758-8cab` was running with `currentPhase=repair-pass-running`.
- MinerU completed for that task and produced `25` parsed files.
- Host MinerU logs contained valid business progress for the file, but task-level `mineruObservedProgress` remained low-signal.
- Current likely split: AI/Ollama JSON Repair blockage is separate from MinerU sidecar attribution/backfill gap.

AI repair and sidecar attribution diagnoses accepted on 2026-05-07:

- AI timeout diagnosis task: `TASK-20260507-104151-P0-Production-AI-JSON-Repair-Ollama-Timeout-Diagnosis`.
- Lucia review: `TaskAndReport/2026-05-07T10-56-16+0800_P0-Production-AI-JSON-Repair-Ollama-Timeout-Diagnosis_LUCIA_REVIEW.md`.
- Accepted conclusion: the observed failures are in AI metadata / JSON Repair execution against Ollama `qwen3.5:9b`, after MinerU parse completion. Strict no-skeleton behavior remains intact.
- Follow-up implementation task issued: `TASK-20260507-105616-P0-AI-Metadata-Repair-Prompt-And-Timeout-Hardening`.
- MinerU sidecar attribution task: `TASK-20260507-104151-P1-MinerU-Sidecar-Task-Level-Log-Attribution`.
- Lucia review: `TaskAndReport/2026-05-07T10-56-16+0800_P1-MinerU-Sidecar-Task-Level-Log-Attribution_LUCIA_REVIEW.md`.
- Accepted conclusion: host MinerU logs exist, while task-level progress can remain low-signal for fast-completing tasks because attribution currently depends on an exact-one-active-task window.
- Follow-up implementation task issued: `TASK-20260507-105616-P1-MinerU-Sidecar-Completed-Window-Log-Backfill`.

AI repair and completed-window sidecar implementations accepted on 2026-05-07:

- AI repair implementation task: `TASK-20260507-105616-P0-AI-Metadata-Repair-Prompt-And-Timeout-Hardening`.
- Lucia review: `TaskAndReport/2026-05-07T12-13-24+0800_P0-AI-Metadata-Repair-Prompt-And-Timeout-Hardening_LUCIA_REVIEW.md`.
- Accepted behavior: AI JSON Repair now uses bounded repair input, deterministic draft normalization where safe, and expanded raw trace metadata while preserving strict no-skeleton failure semantics.
- MinerU sidecar implementation task: `TASK-20260507-105616-P1-MinerU-Sidecar-Completed-Window-Log-Backfill`.
- Lucia review: `TaskAndReport/2026-05-07T12-13-24+0800_P1-MinerU-Sidecar-Completed-Window-Log-Backfill_LUCIA_REVIEW.md`.
- Accepted behavior: sidecar observations can be backfilled to exactly one recently completed local-MinerU task within a bounded window; ambiguous observations remain unattributed and parse state is not changed.
- Residual test-truth task issued: `TASK-20260507-121324-P0-MinerU-Log-Progress-Smoke-Truth-Alignment`.

MinerU log progress smoke truth alignment accepted on 2026-05-07:

- Task: `TASK-20260507-121324-P0-MinerU-Log-Progress-Smoke-Truth-Alignment`.
- Lucia review: `TaskAndReport/2026-05-07T12-38-25+0800_P0-MinerU-Log-Progress-Smoke-Truth-Alignment_LUCIA_REVIEW.md`.
- Accepted behavior: confirmed MinerU execution errors now map to `failed-confirmed`; stale-log handling preserves confirmed failures.
- Boundary: bare `Error:` style low-confidence signals remain outside confirmed-failure adjudication; no production runtime mutation or release-readiness claim is made.

Current-main production deployment task issued on 2026-05-07:

- Task: `TASK-20260507-125133-P0-Current-Main-Production-Deployment-And-Manual-Runtime-Regression`.
- Target main HEAD: `5ffa31d109b2133fdc31645bba25dfe26d36e136`.
- Objective: deploy current `main` to `/Users/concm/prod_workspace/Luceon2026` and prepare `http://localhost:8081/cms/` for Director manual review with non-destructive runtime regression evidence.
- Boundary: this task can establish manual-review readiness; it must not claim production release readiness.

Current-main production deployment accepted on 2026-05-07:

- Task: `TASK-20260507-125133-P0-Current-Main-Production-Deployment-And-Manual-Runtime-Regression`.
- Lucia review: `TaskAndReport/2026-05-07T13-14-26+0800_P0-Current-Main-Production-Deployment-And-Manual-Runtime-Regression_LUCIA_REVIEW.md`.
- Accepted status: `READY_WITH_KNOWN_LIMITATIONS`.
- Deployed production HEAD: `a4fcb05a95d59847b6218cb7a8d2f590097fb4e0`.
- Runtime result: `http://localhost:8081/cms/` is reachable; dependency health is non-blocking with MinerU submit probe and Ollama passing; Tier 2 Standard and UAT smoke passed; controlled sample upload reached `review-pending`.
- Boundary: manual review can continue, but production release readiness remains unclaimed.
- Follow-up tasks issued:
  - `TASK-20260507-131426-P0-MinerU-Log-Observation-Transport-And-Attribution-Robustness`.
  - `TASK-20260507-131426-P1-AI-Deterministic-Repair-UI-And-Ops-Status-Semantics`.

Follow-up runtime-semantics fixes accepted at code level on 2026-05-07:

- MinerU log observation task: `TASK-20260507-131426-P0-MinerU-Log-Observation-Transport-And-Attribution-Robustness`.
- Lucia review: `TaskAndReport/2026-05-07T13-39-17+0800_P0-MinerU-Log-Observation-Transport-And-Attribution-Robustness_LUCIA_REVIEW.md`.
- Accepted implementation commit: `b98be38c8269a99a09cd86c18733315d4adfa345`; integrated main commit: `da83520`.
- Accepted behavior: the observer source is explicit as `host-filesystem`, host log paths are passed into the sidecar, log freshness diagnostics are source-aware, and task attribution uses a bounded 1000 ms timestamp tolerance while keeping ambiguous observations unattributed.
- AI UI and ops status semantics task: `TASK-20260507-131426-P1-AI-Deterministic-Repair-UI-And-Ops-Status-Semantics`.
- Lucia review: `TaskAndReport/2026-05-07T13-39-17+0800_P1-AI-Deterministic-Repair-UI-And-Ops-Status-Semantics_LUCIA_REVIEW.md`.
- Accepted implementation commit: `4a1d42c4db7cec942b5f05d263171f50aa001a24`; integrated main commit: `da83520`.
- Accepted behavior: deterministic repair success in `review-pending` is shown as completed and review-needed, actual AI failure and skeleton fallback remain distinct, and reachable Ollama without tmux management is treated as an ops-session warning rather than an AI outage.
- Boundary: these are code-level acceptances only. Production deployment and manual-runtime validation are assigned to `TASK-20260507-133917-P0-Deploy-Followup-Fixes-And-Manual-Validation`.

Follow-up fixes production deployment accepted for manual review on 2026-05-07:

- Task: `TASK-20260507-133917-P0-Deploy-Followup-Fixes-And-Manual-Validation`.
- Lucode report: `TaskAndReport/2026-05-07T13-59-14+0800_P0-Deploy-Followup-Fixes-And-Manual-Validation_REPORT.md`.
- Lucia review: `TaskAndReport/2026-05-07T14-29-07+0800_P0-Deploy-Followup-Fixes-And-Manual-Validation_LUCIA_REVIEW.md`.
- Production deployed code HEAD: `10a4151d3503586191b6216342a47187159ae61e`.
- Runtime result: `http://localhost:8081/cms/` is reachable; dependency health with MinerU submit probe is non-blocking; controlled sample `task-1778133327274` reached `review-pending`.
- Controlled sample facts: MinerU completed with `8` parsed files; AI job `ai-job-1778133335165-eee5` used `ollama` / `qwen3.5:9b`; deterministic repair succeeded; skeleton fallback was not observed.
- Browser-visible semantics reported by Lucode: deterministic repair success is displayed as completed/review-needed and not as AI dependency blocked; reachable non-tmux Ollama is displayed as an ops-session warning.
- Lucia read-only verification confirmed the runtime health and controlled-sample DB facts.
- Boundary: manual review is ready with known residual observability debt. Production release readiness, staging readiness, L3 readiness, and full-site acceptance remain unclaimed.
- Follow-up task issued: `TASK-20260507-142907-P1-Completed-Task-Observation-And-Ops-Session-Semantics`.

Completed-task observation and ops-session semantics accepted at code level on 2026-05-08:

- Task: `TASK-20260507-142907-P1-Completed-Task-Observation-And-Ops-Session-Semantics`.
- Lucode report: `TaskAndReport/2026-05-07T14-54-09+0800_P1-Completed-Task-Observation-And-Ops-Session-Semantics_REPORT.md`.
- Lucia review: `TaskAndReport/2026-05-08T06-20-00+0800_P1-Completed-Task-Observation-And-Ops-Session-Semantics_LUCIA_REVIEW.md`.
- Accepted implementation commit: `5b8d6f391a988b712416721622137c1fb151429d`; integrated main commit: `a3078b019f1abb4fc71777bc31f5b950e7ebee65`.
- Accepted behavior: terminal local-MinerU tasks with an existing observation do not persist later completed-window backfill observations; later observations are exposed as non-mutating global diagnostics.
- Accepted behavior: terminal stale observation wording is diagnostic and does not imply that a completed task is still processing.
- Accepted behavior: dependency supervisor status separates managed tmux ownership from service reachability and can surface unmanaged MinerU/Ollama sessions.
- Boundary: this is code-level acceptance only. Production deployment and runtime validation are assigned to `TASK-20260508-062000-P1-Deploy-Completed-Observation-Semantics-Validation`.

Completed-task observation and ops-session semantics accepted in production runtime on 2026-05-08:

- Task: `TASK-20260508-062000-P1-Deploy-Completed-Observation-Semantics-Validation`.
- Lucode report: `TaskAndReport/2026-05-08T08-11-39+0800_P1-Deploy-Completed-Observation-Semantics-Validation_REPORT.md`.
- Lucia review: `TaskAndReport/2026-05-08T08-14-14+0800_P1-Deploy-Completed-Observation-Semantics-Validation_LUCIA_REVIEW.md`.
- Production deployed code HEAD: `4cc6d3e4d2e3ca5251cba59ffbdbb0546f1e9bdb`.
- Runtime result: `http://localhost:8081/cms/` is reachable; dependency health with MinerU submit probe is non-blocking; controlled sample `task-1778199039640` reached `review-pending`.
- Controlled sample facts: MinerU completed with `8` parsed files; AI job `ai-job-1778199042959-d2bf` used `ollama` / `qwen3.5:9b`; deterministic repair succeeded.
- Production validation confirmed terminal observation non-mutation: synthetic completed-window observation returned `mutated=false` and preserved the task's existing observation.
- Production validation confirmed dependency status separation: service reachability fields are distinct from tmux ownership fields, and unmanaged MinerU/Ollama sessions are represented without treating reachable services as outages.
- Boundary: this is scoped production runtime validation only. Production release readiness, staging readiness, L3 readiness, and full-site acceptance remain unclaimed.
- Residual deployment reliability debt: `docker compose up -d --build` repeatedly hung while loading frontend `nginx:1.27-alpine` metadata. Follow-up task issued: `TASK-20260508-081414-P2-Docker-Frontend-Build-Metadata-Hang-Diagnosis`.

Docker frontend build metadata diagnosis accepted on 2026-05-08:

- Task: `TASK-20260508-081414-P2-Docker-Frontend-Build-Metadata-Hang-Diagnosis`.
- Lucode report: `TaskAndReport/2026-05-08T08-22-40+0800_P2-Docker-Frontend-Build-Metadata-Hang-Diagnosis_REPORT.md`.
- Lucia review: `TaskAndReport/2026-05-08T08-24-14+0800_P2-Docker-Frontend-Build-Metadata-Hang-Diagnosis_LUCIA_REVIEW.md`.
- Accepted conclusion: the hang is bounded to Docker Desktop / buildx metadata resolution for missing local image `nginx:1.27-alpine`, not invalid compose config or a failing Vite frontend build.
- Evidence summary: `docker compose config`, `docker compose build --dry-run`, and `npx pnpm@10.4.1 run build` passed; direct metadata inspection and frontend build hung while loading `nginx:1.27-alpine` metadata.
- Operator boundary: no repository change was made. Before any deployment that must rebuild the frontend image, preflight exact base-image metadata resolution and pre-pull `nginx:1.27-alpine` when Docker Desktop / registry access is healthy.
- Boundary: this is a bounded deployment-reliability diagnosis only. Production release readiness remains unclaimed.

## 4. Validation Ledger

Commands run in this governance pass:

| Check | Result |
| --- | --- |
| `npx pnpm@10.4.1 install --frozen-lockfile` | PASS |
| `npx pnpm@10.4.1 exec tsc --noEmit` | PASS |
| `npx pnpm@10.4.1 run build` | PASS; Vite reported only the existing chunk-size warning |
| `node server/tests/dependency-health-smoke.mjs` after MinerU submit-path probe | PASS, 31 passed / 0 failed |
| `node server/tests/ai-metadata-repair-hardening-smoke.mjs` after AI repair hardening | PASS |
| `node server/tests/mineru-sidecar-completed-window-smoke.mjs` after sidecar backfill | PASS |
| `node server/tests/ai-metadata-real-sample-smoke.mjs` after AI repair hardening | PASS |
| `node server/tests/worker-smoke.mjs` after AI repair hardening | PASS; strict AI mode fails fast without skeleton fallback |
| `node server/tests/mineru-sidecar-smoke.mjs` after sidecar backfill | PASS |
| `node server/tests/mineru-log-source-live-smoke.mjs` after sidecar backfill | PASS |
| `node server/tests/mineru-log-progress-smoke.mjs` during Lucia pre-fix review | FAIL; existing Test 4 expectation drift: expected `failed-confirmed`, actual `log-error-signal`; parser/test files were not changed by the accepted branch |
| `node server/tests/mineru-log-progress-smoke.mjs` after truth alignment | PASS, 118 passed / 0 failed |
| `node server/tests/mineru-artifact-empty-retry-smoke.mjs` after truth alignment | PASS, 62 passed / 0 failed |
| `node server/tests/mineru-log-observation-transport-smoke.mjs` after runtime-semantics follow-up integration | PASS |
| `node server/tests/mineru-sidecar-completed-window-smoke.mjs` after runtime-semantics follow-up integration | PASS |
| `node server/tests/mineru-log-progress-smoke.mjs` after runtime-semantics follow-up integration | PASS, 118 passed / 0 failed |
| `node server/tests/mineru-log-source-live-smoke.mjs` after runtime-semantics follow-up integration | PASS, 21 passed / 0 failed |
| `npx pnpm@10.4.1 exec tsc --noEmit` after runtime-semantics follow-up integration | PASS |
| `npx pnpm@10.4.1 run build` after runtime-semantics follow-up integration | PASS; Vite reported only the existing chunk-size warning |
| `BASE_URL=http://localhost:8081 bash uat/smoke-test.sh` after runtime-semantics follow-up integration | PASS, 12 passed / 0 failed / 0 skipped |
| `curl -fsS 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true'` during Lucia review of task 13 | PASS; `ok=true`, `blocking=false`, `mineru.submitProbe.ok=true`, `ollama.ok=true` |
| `curl -fsS http://localhost:8081/__proxy/upload/ops/dependency-repair/status` during Lucia review of task 13 | PASS; `ok=true`, `sidecar=true`, `ollamaReachable=true`; MinerU tmux ownership residual remains |
| `curl -fsS http://localhost:8081/__proxy/db/tasks/task-1778133327274` during Lucia review of task 13 | PASS; task remained `review-pending`, MinerU `completed`, parsed files `8` |
| `curl -fsS 'http://localhost:8081/__proxy/db/ai-metadata-jobs?parseTaskId=task-1778133327274'` during Lucia review of task 13 | PASS; job remained `review-pending`, provider `ollama`, phase `repair-deterministic-succeeded` |
| `node server/tests/mineru-completed-observation-semantics-smoke.mjs` during Lucia review of task 14 | PASS, 4 cases passed |
| `node server/tests/dependency-supervisor-smoke.mjs` during Lucia review of task 14 | PASS |
| `node server/tests/mineru-log-observation-transport-smoke.mjs` during Lucia review of task 14 | PASS, 3 cases passed |
| `node server/tests/mineru-sidecar-completed-window-smoke.mjs` during Lucia review of task 14 | PASS, 8 cases passed |
| `node server/tests/mineru-log-progress-smoke.mjs` during Lucia review of task 14 | PASS, 118 passed / 0 failed |
| `node server/tests/mineru-log-source-live-smoke.mjs` during Lucia review of task 14 | PASS, 21 passed / 0 failed |
| `npx pnpm@10.4.1 exec tsc --noEmit` during Lucia review of task 14 | PASS |
| `npx pnpm@10.4.1 run build` during Lucia review of task 14 | PASS; Vite reported only the existing chunk-size warning |
| `BASE_URL=http://localhost:8081 bash uat/smoke-test.sh` during Lucia review of task 14 | PASS, 12 passed / 0 failed / 0 skipped |
| `curl -fsS 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true'` during Lucia review of task 15 | PASS; `ok=true`, `blocking=false`, `mineru.submitProbe.ok=true`, `ollama.ok=true` |
| `curl -fsS http://localhost:8081/__proxy/upload/ops/dependency-repair/status` during Lucia review of task 15 | PASS; reachability and ownership fields are separated |
| `curl -fsS http://localhost:8081/__proxy/db/tasks/task-1778199039640` during Lucia review of task 15 | PASS; task remained `review-pending`, MinerU `completed`, parsed files `8` |
| `curl -fsS 'http://localhost:8081/__proxy/db/ai-metadata-jobs?parseTaskId=task-1778199039640'` during Lucia review of task 15 | PASS; job remained `review-pending`, provider `ollama`, phase `repair-deterministic-succeeded` |
| `BASE_URL=http://localhost:8081 npx pnpm@10.4.1 run tier2:standard:check` after rebuilt runtime | PASS; `mineru.healthOk=true`, `mineru.submitProbe.ok=true` |
| `BASE_URL=http://localhost:8081 bash uat/smoke-test.sh` after rebuilt runtime | PASS, 12 passed / 0 failed / 0 skipped |
| `node server/tests/worker-smoke.mjs` | PASS; strict AI mode fails fast without skeleton fallback |
| `node server/tests/dependency-supervisor-smoke.mjs` | PASS |
| `BASE_URL=http://localhost:8081 LOCAL_MINERU_ENDPOINT=http://127.0.0.1:8083 OLLAMA_API_URL=http://127.0.0.1:11434 OLLAMA_TIER2_MODEL=qwen3.5:9b npx pnpm@10.4.1 run tier2:standard:check` | PASS |
| `BASE_URL=http://localhost:8081 bash uat/smoke-test.sh` | PASS, 12 passed / 0 failed / 0 skipped |
| `DB_BASE_URL=http://localhost:8081/__proxy/db node server/tests/mineru-deep-check.mjs` | PASS |
| `BASE_URL=http://localhost:8081 npx pnpm@10.4.1 --dir uat exec playwright test tests/pages-smoke.spec.ts` | PASS, 8 passed |
| `BASE_URL=http://localhost:8081 npx pnpm@10.4.1 --dir uat exec playwright test tests/cms-uat.spec.ts` | PASS, 18 passed |
| `BASE_URL=http://localhost:8081 npx pnpm@10.4.1 --dir uat exec playwright test tests/pipeline-consistency.spec.ts` | PASS, 2 passed |

Runtime evidence from the final pipeline run:

- PDF chain reached `review-pending`.
- Markdown chain reached an accepted AI-after-parse terminal state.
- Parsed artifacts included `full.md`, `artifact-manifest.json`, and MinerU result carriers.
- Parsed ZIP export included the manifest and canonical Markdown.
- Strict AI worker smoke proved provider failure does not produce skeleton output in current strict mode.

## 5. Known Technical Debts

| ID | Status | Description | Boundary |
| --- | --- | --- | --- |
| TD-001 | Closed | MinerU `/health` and `/tasks` readiness are now separated through an explicit submit-path dependency probe. | Default dependency health remains lightweight; Tier 2 Standard now requests `mineruSubmitProbe=true`. Production release readiness still requires rebuilt-runtime validation. |
| TD-002 | Open | `server/upload-server.mjs` remains a large mixed server containing upload, storage, parser, AI, and ops routes. | Keep unchanged for Phase 1 stability; modular refactor belongs to a later phase. |
| TD-003 | Open | Legacy compatibility routes remain for `/cms/source-materials` and `/cms/workspace`. | Keep redirect tests; do not use them as the main operator entry point. |
| TD-004 | Open | Online MinerU v4 adapter remains in the codebase for explicit compatibility-only validation. | It must not be selected by no-skeleton flags or treated as the current Standard gate. |
| TD-005 | Open | Vite production build emits a chunk-size warning for the main bundle. | Non-blocking for Phase 1; consider route-level code splitting later. |
| TD-006 | Open | Full concurrency, large-PDF soak, permissions/security, rollback rehearsal, folder upload, and all error-path coverage are not closed by this governance run. | These are Phase 2 or release-readiness validation items. |
| TD-007 | Open | `scripts/tier2-standard-check.mjs` can still show an unhelpful JSON parse error when `BASE_URL` points to a frontend-only route returning HTML. | Validation ergonomics debt; does not affect MinerU submit-path probe behavior. |
| TD-008 | Mitigated | Production ops observer and dependency supervisor were missing after deployment; `luceon-supervisor` and `luceon-sidecar` have been started. | Long-term guarantee that these sessions survive deployment/restart remains open for a later ops automation task. |
| TD-009 | Mitigated | AI metadata recognition / JSON Repair can block or time out through Ollama `qwen3.5:9b` after MinerU succeeds. | Implementation accepted on `main`: bounded repair input, deterministic draft normalization, and strict no-skeleton failure semantics. Production runtime revalidation remains a release-readiness concern. |
| TD-010 | Mitigated | MinerU host logs can contain valid progress while fast-completing tasks fail to receive useful task-level `mineruObservedProgress`. | Implementation accepted on `main`: bounded completed-window backfill with ambiguous observations remaining unattributed. Production runtime revalidation remains a release-readiness concern. |
| TD-011 | Closed | `server/tests/mineru-log-progress-smoke.mjs` Test 4 expected `failed-confirmed`, while the parser returned `log-error-signal`. | Closed by `TASK-20260507-121324-P0-MinerU-Log-Progress-Smoke-Truth-Alignment`; confirmed execution errors now produce `failed-confirmed`, and the smoke test passes without `.skip` or weakened assertions. |
| TD-012 | Mitigated | MinerU task-level live log observation can still be unreliable in production manual review even when MinerU parse succeeds and host logs contain business progress. | Production validation in `TASK-20260507-133917-P0-Deploy-Followup-Fixes-And-Manual-Validation` showed improved attribution and explicit `host-filesystem` source context for the controlled sample. Residual post-completion observation mutation is tracked as TD-014. |
| TD-013 | Closed | UI/diagnostic wording can describe deterministic AI repair success or reachable-but-unmanaged Ollama status as AI blocked. | Closed by task 13 validation: deterministic repair success is displayed as completed/review-needed, and reachable non-tmux Ollama is displayed as an ops-session warning rather than a dependency outage. |
| TD-014 | Closed | Terminal ParseTasks can still receive misleading post-completion MinerU observation changes through completed-window backfill. | Closed by task 15 production validation: synthetic completed-window observation returned `mutated=false` and did not mutate the terminal task's existing observation. |
| TD-015 | Closed | Dependency repair status still reports missing expected tmux ownership for a reachable MinerU service. | Closed by task 15 production validation: service reachability and tmux ownership are reported separately, including unmanaged session details. |
| TD-016 | Documented | `docker compose up -d --build` can hang while loading frontend `nginx:1.27-alpine` metadata. | Diagnosis accepted in task 16. Treat as Docker Desktop / buildx metadata resolution for a missing local base image; preflight and pre-pull the exact base image before frontend rebuilds in release-readiness work. |
| TD-017 | Mitigated | Medium-large parsed documents could enter AI metadata first pass through the legacy sampler with timeout-prone input size. | Code-level mitigation accepted in task 31 and controlled production validation accepted in task 38: selected input used `evidence-pack-v0.3` and was reduced from `104823` to `16261`. Broader release-readiness validation remains separate. |
| TD-018 | Mitigated | Production Ollama `qwen3.5:9b` dependency-health chat smoke timed out before the adaptive evidence-pack controlled upload could be created. | Task 38 validated a bounded non-mutating warm-up gate: warm dependency-health passed after warm-up and the controlled upload completed to `review-pending`. Cold-load remains a release-readiness operational concern, not closed globally. |
| TD-019 | Superseded | Controlled production concurrency validation was considered but rejected by Director. | Director clarified local MinerU, MinIO, and Ollama deployment should use stage-queued流水 validation: upload intake can accept the next sample after MinIO intake, while MinerU and Ollama heavy work queue by stage. Task 42 replaces the concurrency route with stage-queued planning/preflight from the true sample directory. |
| TD-020 | Mitigated | Stage-queued validation over real samples initially left sample 3 unresolved in production state. | Task 48 recovered sample 3 to `review-pending` / `reviewing` using the existing MinerU result. This closes the sample 3 validation gap for manual review, but does not imply production release readiness. |
| TD-021 | Mitigated | A MinerU result that completes after Luceon local timeout can remain un-ingested, leaving task/material stuck in processing with no AI job. | Task 46 accepted a code-level fix, and Task 48 recovered the known stuck production target `task-1778249434820` without a new upload or second target MinerU submission. Broader historical residuals are tracked separately. |
| TD-022 | Split | Post-recovery runtime diagnostics found Ollama dependency-health warm/cold timeout behavior and three historical terminal AI failures mislabeled as takeover-required. | Ollama readiness remains residual release-readiness debt. The historical AI-failure diagnostic misclassification is assigned to Task 50 for code-level correction only. |
| TD-023 | Open | `/ops/mineru/active-task` can label historical terminal AI failures as `takeoverRequiredTasks`, which confuses active MinerU recovery/readiness reporting. | Task 50 is assigned to correct diagnostic classification while preserving actionable MinerU takeover visibility and strict no-skeleton semantics. |

## 6. Core Asset Directory Index

| Path | Role |
| --- | --- |
| `src/app/` | React SPA routes, pages, and reusable UI components |
| `src/store/` | Frontend application state and seed data |
| `server/upload-server.mjs` | Upload, MinIO, parse task, AI trigger, operational proxy entrypoints |
| `server/db-server.mjs` | JSON-backed data API for materials, tasks, settings, secrets, and AI metadata jobs |
| `server/services/mineru/` | Local and compatibility MinerU adapters |
| `server/services/queue/` | Parse task worker and task processing orchestration |
| `server/services/ai/` | AI metadata worker, provider adapters, taxonomy, and v0.2 schema helpers |
| `server/tests/` | Service-level smoke and regression checks |
| `ops/` | Local dependency supervisor and operator tooling |
| `scripts/` | Local checks, test runner wrappers, and Tier 2 pre-check scripts |
| `uat/` | Playwright UAT suites and shell smoke test |
| `docs/prd/` | Active PRD source |
| `docs/codex/` | Team contract, project state, handoff, role, validation policy, repository structure, and historical project records |
| `docs/codex/roles/` | Active Lucia and Lucode role contracts only |
| `docs/deploy/` | Deployment documentation and environment migration notes |
| `docs/reviews/` | Current review index and phase acceptance summary only |
| `TaskAndReport/` | Lucia-issued task briefs, Lucode reports, and task tracking ledger |
| `archive/phase1-governance-2026-05-06/` | Historical plan and review archive for traceability |

## 7. Boundary For Future Work

- GitHub `main`, this local workspace, and the PRD remain the three project truth sources.
- Current Phase 1 status is local real-runtime PASS for the upload -> MinerU -> MinIO -> Ollama metadata -> review path.
- This record does not promote staging readiness, production release readiness, or full-site acceptance.
- Future changes must preserve full-text reasoning as the chapter-preprocessing direction if chapter preprocessing is reintroduced or extended; heuristic chapter preprocessing such as `chapterPreprocessV2.ts` must not be restored as a main path.

## 2026-05-08 Controlled Concurrency Validation Planning

Lucia accepted Task 40 as `ACCEPTED_PLANNING_AND_PREFLIGHT_WITH_DIRECTOR_DECISION_REQUIRED`.

Confirmed planning/preflight facts from Lucode report:

- Result classification: `PLAN_READY`.
- No production upload was created.
- No production release-readiness claim occurred.
- No production deploy, fast-forward, rebuild, restart, rollback, Docker mutation, Ollama restart/start/stop/kill/reload, model/timeout/config/secret/override change, DB row deletion, MinIO object deletion, Docker volume deletion, sample mutation, GitHub sample sync, skeleton fallback, or silent degradation was reported.
- Production override boundary was reported present: `DISABLE_AI_SKELETON_FALLBACK=true`, `OLLAMA_TIER2_MODEL=qwen3.5:9b`, and MinIO console mapping `127.0.0.1:19001:9001`.
- Active parse/task states and active AI metadata jobs were `0`.
- Initial dependency-health with MinerU submit probe passed MinIO/MinerU but timed out Ollama at about `14999ms`; one bounded non-mutating Ollama warm-up succeeded; warm dependency-health passed with `ollama.durationMs=699`.

The technically accepted first concurrency shape is concurrency `2`, maximum uploads `2`, using:

- `/Users/concm/prod_workspace/Luceon2026/testpdf/G7_Workbook_ready_to_print.pdf`
- `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/4.XxwlAs2026/sample/走向成功_英语_二模卷16篇.pdf`

The external sample directory remains read-only input inventory and must not be synchronized to GitHub, modified, moved, renamed, deleted, normalized, or polluted.

Director rejected concurrency after this planning step. Concurrency must not be used as the validation route for this local deployment.

## 2026-05-08 Director Correction: Stage-Queued Validation Only

Director clarified that local MinerU, MinIO, and Ollama deployment constraints require a stage-queued流水 validation model, not full end-to-end serial blocking.

The accepted validation shape is:

1. A sample enters upload and is stored in MinIO.
2. After upload/MinIO intake is complete, the intake may accept the next sample.
3. MinerU parsing queues by stage; do not run multiple heavy MinerU parse jobs simultaneously for this local deployment validation.
4. Ollama metadata recognition queues by stage; do not run multiple heavy Ollama metadata jobs simultaneously for this local deployment validation.
5. Evidence must record each sample's stage transition and queue behavior.

The real sample source for future validation is:

`/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/4.XxwlAs2026/sample`

The sample directory may be inspected as read-only inventory only. It must not be synchronized to GitHub, modified, moved, renamed, deleted, normalized, or polluted.

Task 42 is assigned to Lucode for stage-queued planning/preflight only. No production upload is authorized by Task 42.

Lucia reviewed the first Task 42 report at `2026-05-08T20:39:35+0800` and returned it for correction. Accepted preflight facts: true sample inventory was read-only, active parse/task states and active AI jobs were `0`, dependency-health with MinerU submit probe passed, and Ollama was OK but slow at `12740ms`. Blocking issue: the proposed plan required each sample to reach terminal state before the next upload, which contradicts Director's stage-queued model. Lucode must revise the plan so the next upload may start after prior upload/storage intake is durable, while MinerU and Ollama heavy stages remain queued/single-worker.

Lucia accepted the revised Task 42 report at `2026-05-08T21:43:25+0800`. Accepted revised planning facts:

- Next upload may start after prior upload/storage intake is durable, not after terminal completion.
- Durable intake requires upload success, task ID, material ID, objectName, provider, DB task visibility, DB material visibility, and trackable task state/stage.
- MinerU active parse-running count must stay `<=1`.
- Ollama active metadata/Ollama-running count must stay `<=1`.
- The true sample directory remains read-only and must not be synchronized to GitHub, modified, moved, renamed, deleted, normalized, or polluted.
- Actual production validation is not authorized by Task 42. Director decision task 43 is pending.

Director approved Option A for task 43 at `2026-05-08T21:51:38+0800`: up to three controlled true-directory samples may be used for a stage-queued production validation artifact run. Lucia issued task 44. This authorization does not include production release readiness, production deploy/rebuild/restart/rollback/Docker mutation, service/config/model/secret/override changes, data deletion, sample mutation/sync, skeleton fallback, or silent degradation.

## 2026-05-09 MinerU Completed-After-Timeout Takeover Fix

Task 45 confirmed a production stuck state for sample 3: MinerU API reported underlying task `ec9452cc-94e4-4b36-bb64-efba86f38cf6` as `completed` with result available, while Luceon task `task-1778249434820` and material `mat-1778249419780` remained processing and no AI metadata job existed.

Task 46 is accepted at code level. The accepted implementation handles completed-after-local-timeout takeover without creating a second MinerU task and explicitly writes final task metadata `mineruStatus='completed'`. Lucia independently verified the focused no-resubmit smoke, timeout-adjudication smoke, TypeScript, build, and diff check.

This did not by itself authorize production recovery for the existing stuck task and did not declare production release readiness. Director later approved scoped production recovery for only `task-1778249434820` / `mat-1778249419780` at `2026-05-09T05:20:30+0800`; Lucia issued Task 48 to Lucode. The authorization remains target-only and does not include production release readiness, broad deploy/rebuild/restart/rollback, data deletion, secret/model/config/override changes, unrelated task recovery, new upload creation, or a second MinerU submission if the existing result is available.

Lucia accepted Task 48 at `2026-05-09T06:24:41+0800`. Confirmed production facts: target task `task-1778249434820` is `review-pending`, material `mat-1778249419780` is `reviewing`, AI job `ai-job-1778278172782-303b` is `review-pending`, and parsed artifacts exist under `parsed/mat-1778249419780/`. The recovery used existing MinerU task `ec9452cc-94e4-4b36-bb64-efba86f38cf6`; no new upload, second target MinerU submission, manual DB edit, cleanup, or release-readiness claim occurred. Residual diagnostics remain for Ollama dependency-health timeout and three unrelated historical takeover-required tasks.

Lucia accepted Task 49 at `2026-05-09T06:37:09+0800` as read-only diagnostic evidence. The three takeover-required tasks are historical terminal AI failures, not active MinerU ingestion work. Task 50 is assigned to correct the diagnostic classification so these historical AI failures are no longer surfaced as `takeoverRequiredTasks`. Ollama dependency-health warm/cold timeout behavior remains release-readiness debt; no production mutation is authorized by Task 50.

Lucia accepted Task 50 at `2026-05-09T07:47:37+0800` as `ACCEPTED_CODE_LEVEL` and integrated the diagnostic classification fix into `main`. Accepted behavior: `/ops/mineru/active-task` and `/ops/mineru/diagnostics` share `classifyMineruActiveTasks()`, historical terminal AI failures with completed MinerU status and parsed artifacts are surfaced in `historicalAiFailureTasks`, and actionable completed-but-not-ingested or running-completed MinerU cases remain in `takeoverRequiredTasks`. Lucia independently reran focused classification smoke, MinerU diagnostics smoke, MinerU no-resubmit smoke, TypeScript, build, and diff-check; Lucia also restored diagnostics smoke coverage for the richer log observation structure. This remains code-level acceptance only. Production deployment/validation requires Director decision task 51, and production release readiness remains unclaimed.

Director closed Task 51 at `2026-05-09T08:28:54+0800` by instructing Lucia to continue accelerated production-candidate validation under a maximum two-validation-pass and two-revision-cycle timebox. Lucia issued Task 52 for production-candidate validation pass 1. This timebox is a decision discipline, not a lowered launch standard: if blocking issues remain after two validation passes and two revision cycles, Lucia must return a go/no-go recommendation to Director. Production release readiness remains unclaimed until Lucia reviews sufficient production evidence.

Lucia accepted Task 52 at `2026-05-09T08:46:29+0800` as blocked production-candidate evidence, not release readiness. Confirmed facts: production and development were reported at `4ff4791`; production-local strict AI/model settings and MinIO console local-only binding were preserved; CMS/DB/MinIO/MinerU and Task 50 diagnostic classification passed; no controlled upload was created because actual pass-1 dependency-health failed Ollama `qwen3.5:9b` readiness on the cold check and again after one bounded warm-up. Lucia independently observed that current later dependency-health can pass in warm state: default dependency-health returned Ollama `ok=true` with duration `11212ms`, and `dependency-health?mineruSubmitProbe=true` returned MinerU probe task `2aac6910-0c32-42e8-b09a-3a4937393ee6` plus Ollama `ok=true` with duration `552ms`. This narrows the blocker to readiness-smoke / cold-load stability, but it does not erase pass-1 failure or validate production release readiness. Lucia issued Task 53 for the smallest code-level dependency-health Ollama smoke alignment before validation pass 2.

Lucia accepted Task 53 at `2026-05-09T09:01:38+0800` as `ACCEPTED_CODE_LEVEL` and integrated branch `lucode/p0-ollama-dependency-health-smoke-alignment-revision-1` at `9063a14`. Accepted behavior: dependency-health Ollama smoke now mirrors the production provider no-thinking request shape with `stream:false`, top-level `think:false`, `options.think:false`, and `num_predict:1`, while preserving strict missing-model and chat-failure behavior. Lucia independently reran `git diff --check`, `node server/tests/dependency-health-smoke.mjs` (`40 passed / 0 failed`), TypeScript, and build. Production release readiness remains unclaimed; Task 54 is assigned for production-candidate validation pass 2.

Lucia accepted Task 54 at `2026-05-09T09:12:21+0800` as `BLOCKED_AFTER_PASS_2_NO_GO_FOR_RELEASE_READY`. Both validation passes in the Director timebox are now used. Accepted pass-2 facts: production/development synced to `f720685`, production-local override boundary was preserved, CMS/DB/MinIO/MinerU submit path and diagnostic classification passed, but the upload-server container-to-host Ollama `/api/chat` path still timed out. Host direct no-think chat succeeded, and container `/api/tags` could see `qwen3.5:9b`, but container-side no-think `/api/chat` timed out. Lucia independently confirmed dependency-health with MinerU submit probe still fails on Ollama chat timeout while MinIO/MinerU pass. Production release readiness remains unclaimed. Lucia issued Task 55 as revision cycle 2 of 2 for a narrow container-to-host Ollama chat timeout diagnosis/fix or final no-go decision.

Lucia accepted Task 55 at `2026-05-09T09:29:35+0800` as `ACCEPTED_NO_CODE_RUNTIME_DECISION_REQUIRED`. Both validation passes and both revision cycles in the Director timebox are exhausted. Accepted facts: host `localhost:11434` reaches Ollama `0.23.1` and can complete no-think chat; the upload-server container reaches `host.docker.internal:11434` / `192.168.65.254:11434`, sees Ollama `0.22.1`, and can list tags, but `/api/chat` times out before response headers; two host `ollama serve` listeners are present on `127.0.0.1:11434` and `*:11434`. Lucia independently rechecked the dependency-health submit probe failure, the dual listeners, host-local version `0.23.1`, and container-visible version `0.22.1`. Production release readiness is `NO_GO` until the local Ollama runtime ownership/listener split is resolved and a new Director-approved validation route passes. Director decision Task 56 is now pending for whether to authorize scoped local Ollama runtime standardization, hold validation, or request more read-only evidence.

Director selected Option A for Task 56 at `2026-05-09T09:43:56+0800` and clarified that the intended local state is one Ollama server. Lucia issued Task 57 for scoped local Ollama runtime/listener ownership standardization. The authorization is limited to reconciling host-local and container-facing Ollama endpoints to the same intended effective runtime and verifying version/tags/no-think chat/dependency-health. It does not authorize production release readiness, validation pass 3, validation uploads, model pull/delete/reload, model-selection or timeout-policy changes, production override changes, DB/MinIO/Docker volume/task/artifact/log/sample deletion, or broad production deploy/rebuild/restart/rollback.

Lucia accepted Task 57 at `2026-05-09T10:12:45+0800` as `ACCEPTED_RUNTIME_STANDARDIZED_READY_FOR_VALIDATION_DECISION`. Confirmed facts: duplicate host-only Ollama listener PID `665` was terminated with `kill -TERM 665`; one wildcard listener PID `59391` remains on `*:11434`; host-local and container-facing endpoints now report Ollama `0.23.1`; `qwen3.5:9b` is present; host-local and container-facing no-think `/api/chat` pass; dependency-health with MinerU submit probe passes. Lucia independently rechecked the one-listener state, host/container version/tags/chat, and dependency-health. No source code, model, timeout policy, secret, production override, DB/MinIO/Docker volume/task/artifact/log/sample data, validation upload, or production release-readiness claim occurred. Because the previous two-pass/two-revision timebox is exhausted, Director decision Task 58 is pending before any post-standardization production-candidate validation pass.

Director authorized Option A for Task 58 at `2026-05-09T10:16:33+0800`. Lucia issued Task 59 for one bounded post-standardization production-candidate validation pass. The task may run preflight, warm dependency-health with MinerU submit probe, and at most one controlled validation upload if gates pass. It does not authorize Lucode to declare production release readiness, create more than one upload, change source code, change model/timeout/secret/production override settings, perform model operations, delete or mutate DB/MinIO/Docker volume/task/artifact/log/sample data, or run broad production deploy/rebuild/restart/rollback.

Lucia accepted Task 59 at `2026-05-09T10:40:53+0800` as `ACCEPTED_PRODUCTION_CANDIDATE_KEY_PATH_READY_FOR_DIRECTOR_RELEASE_DECISION`. Accepted facts: one bounded post-standardization validation upload used the external read-only sample `走向成功_英语_二模卷16篇.pdf` with SHA-256 `b3e00ad1c7f7afff4bdae1b484abad941af618fd80b9b5f9f22d69848968eaac`; task `task-1778293431502` and material `validation-post-ollama-1778293431` completed the critical path to operator review; MinerU task `9457643f-06c1-44a5-b41a-1eb9e7d65d24` completed with parsed prefix `parsed/validation-post-ollama-1778293431/`; `full.md`, `artifact-manifest.json`, and `mineru-result.zip` were available; AI job `ai-job-1778293625705-fb6c` reached `review-pending` with provider/model `ollama` / `qwen3.5:9b`; final task state was `review-pending`, final material status was `reviewing`, `mineruStatus=completed`, and `aiStatus=analyzed`; strict no-skeleton fallback was preserved; post diagnostics were idle with no takeover-required tasks; post dependency-health with MinerU submit probe passed. Lucia independently rechecked health, diagnostics, task/material state, and verified only docs/TaskAndReport files changed since the deployed production code baseline. Production release readiness remains pending Director final decision in Task 60.

Director later found a manual parsed-ZIP download defect before release approval. The downloaded ZIP for material manifest id `409615937854928` contained default-user export overreach: outer `mineru-result.zip`, outer `artifact-manifest.json`, root `full.md`, and the expanded MinerU tree were all present in the default package. Director clarified the expected package boundary: root `full.md` plus the extracted MinerU `ocr/` directory. Lucia accepted a code-level correction in `server/upload-server.mjs`: default `mode=user` now exports root `full.md` plus `ocr/` contents, while `mineru-raw` and `diagnostic` modes remain available for raw/full diagnostic export. Verified at code level with parsed ZIP export smoke, TypeScript, build, and diff-check. Production deployment and real download revalidation are pending Task 61; production release readiness remains unclaimed.

Task 61 production revalidation is accepted. Confirmed production facts: production ran the accepted code `86a0d0e`, the originally observed material `409615937854928` was unavailable in current parsed storage, and fallback material `417987242893597` verified the default user ZIP boundary. The default ZIP contains root `full.md` plus all `194` OCR files, has `0` non-root/non-`ocr` files, and excludes root `mineru-result.zip` and root `artifact-manifest.json`; `mineru-raw` still returns the raw OCR ZIP, and `diagnostic` still includes root `mineru-result.zip`, `artifact-manifest.json`, and `full.md`. Lucia independently confirmed the default/raw/diagnostic ZIP structure. Production release readiness remains pending Director task 60.

Director later provided the manually prepared expected ZIP `/Users/concm/Downloads/Cambridge IGCSE(0580)  Core and Extended Mathematics_2018(Cambridge  University Press).zip`, which supersedes the Task 61 user-facing layout boundary. Confirmed code-level correction: default `mode=user` parsed ZIP exports exactly one top-level material folder, writes `full.md` inside that folder, and lifts the contents of MinerU `ocr/` directly under that folder without preserving the `ocr` segment. The default user ZIP still excludes root `mineru-result.zip`, root `artifact-manifest.json`, non-OCR legacy expanded files, and app-generated macOS ZIP artifacts. `mineru-raw` and `diagnostic` modes remain available for raw/debug export. Code-level smoke passed; production deployment/download revalidation is pending Task 62. Production release readiness remains pending Director task 60 and is blocked by Task 62 evidence.

Task 62 production revalidation is accepted with exact-sample gap recorded. Production was synced to `cd1812a` for the parsed-ZIP layout correction, only `upload-server` was rebuilt, and health returned OK. The exact Cambridge material was unavailable in current production parsed storage, so no same-material production comparison was performed and no new upload was created. Existing real production material `417987242893597` validated the corrected default export layout: one top-level material folder, `<folder>/full.md`, OCR contents lifted directly under that folder, no `<folder>/ocr/...`, no root `full.md`, no root `mineru-result.zip`, no root `artifact-manifest.json`, and no app-generated macOS artifacts. Raw and diagnostic modes still retain raw/debug access. Production release readiness remains pending Director task 60.
