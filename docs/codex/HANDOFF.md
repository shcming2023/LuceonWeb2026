# Codex Thread Handoff

Last updated: 2026-05-03

This file is the short entry point for moving Luceon2026 work from the current Windows Codex environment to the Home Mac mini Codex environment.

## Source Environment

- Current active folder: `D:\Users\moonp\OneDrive\Mac\项目开发\Luceon2026`
- Current repository branch: `main`
- Current local state before this handoff: `main` was ahead of `origin/main` by 10 commits
- Codex thread state on this Windows machine is local to `C:\Users\moonp\.codex`

Do not rely on OneDrive or local Codex thread history as the durable project memory. Use GitHub and repository docs.

## Target Environment

Home Mac mini will become the main Codex host.

Suggested directories:

```text
~/dev/Luceon2026
~/staging/Luceon2026
/opt/luceon2026
```

Suggested container/project naming:

```text
luceon-dev
luceon-staging
luceon-prod
```

## Threads To Recreate Or Continue

### cota

Read:

- `AGENTS.md`
- `docs/codex/roles/cota.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`

Use cota as Director's cross-project Codex collaboration advisor. cota helps Director optimize role boundaries, task routing, task brief quality, report discipline, and cross-agent communication for Luceon2026 and for transferred collaboration models such as XxwlAs2026/cosh. cota does not replace lucia or shana, does not assign work directly to execution agents, and does not make implementation, validation, PRD, release, or deployment judgments.

### lucia

Read:

- `AGENTS.md`
- `docs/codex/roles/lucia.md`
- `docs/codex/PROJECT_STATE.md`

Use lucia for architecture control, task writing, review, and final judgment. Lucia must not take over code implementation, PRD maintenance, or Tier 2 execution.

### lucode

Read:

- `AGENTS.md`
- `docs/codex/roles/lucode.md`
- `docs/codex/TASK_BRIEF_TEMPLATE.md`

Use lucode for implementation and code revision only. lucode runs Antigravity in `/workspace/ops/Luceon2026` with host/IDE working copy reference `D:\Users\moonp\OneDrive\Mac\项目开发\Luceon2026`, synchronizes through GitHub, and must follow lucia-approved task briefs.

### luplan

Read:

- `AGENTS.md`
- `docs/codex/roles/luplan.md`
- `docs/prd/README.md`
- `docs/prd/luplan-prd-maintenance.md`
- `docs/prd/Luceon2026-PRD-v0.4.md`

Use luplan for PRD, changelog, decision, and project-state maintenance only.

### luceonhmm

Read:

- `AGENTS.md`
- `docs/codex/roles/luceonhmm.md`
- `docs/codex/TEST_POLICY.md`
- `docs/codex/PROJECT_STATE.md`

Use luceonhmm for UAT deployment, L2/L3 validation, production-like runtime analysis, dependency debugging, rollback support, and evidence capture.

Current accepted UAT fact:

- `P1-ui-clarity-polish-after-review-pass`: `PASS`
- luceonhmm reported `PASS_CANDIDATE`; Lucia accepted final status as `PASS`.
- Validated HEAD: `87543399673308f2b8ff2febf145c85b3e342f75`.
- Scope: `/cms/tasks`, review-pending task detail overview, internal diagnostics folded area, task `task-1777788279069`, material `mat-1777788279055`.
- Validated behavior: task list main status remains `待复核`; same-row diagnostics badge now shows `状态一致` with no duplicate second `待复核`; overview shows current state, current stage, generated artifact, and next action; AI Job / model technical info no longer appears in the main summary by default; AI metadata job/model remains available after expanding internal diagnostics; dependency-health `blocking=false`; consistency audit `ok=true findingsCount=0`; browser console error/warn empty.
- Pending: no MetadataTab full revalidation claim, no products/library/settings review claim, no multi-task-state UI validation claim, and no L3/production-readiness claim.
- Non-blocking polish: internal diagnostics title currently says `内部诊断信息 (状态一致性、MinerU 画像、日志观测)`; because AI job info now also lives there, the title can later be clarified to include `AI 任务`.

- `P1-latest-ui-metadata-task-detail-interaction-review`: `PASS`
- luceonhmm reported `PASS_CANDIDATE`; Lucia accepted final status as `PASS`.
- Scope: latest UI/code baseline `origin/main@cb6f2376b5146e53c7c83cba62d36bac2236e7e3`, real local runtime stack, review-pending task `task-1777788279069`, material `mat-1777788279055`, `/cms/tasks`, task detail overview, MetadataTab, classification/tag display, and current tag persistence state.
- Validated facts: task list and detail consistently use `待复核`; overview answers state, stage, artifact, and next action; MetadataTab shows 审核摘要, 当前保存值, AI 建议与证据, and folded 技术详情 (`Technical Details`); provider/model is `ollama/qwen3.5:9b`; `[object Object]` regression is absent; `Material.tags=["uat-tag-persistence"]`; `metadata.tags` remains AI/parse tag source; dependency-health `blocking=false`; consistency audit `ok=true findingsCount=0`; browser console error/warn empty.
- Pending: no L3 or production-readiness claim, no full-site UI review, no validation for other task states, tag deletion, multi-tag editing, duplicate-tag handling, concurrent edits, or toast stability.
- Follow-up polish status: duplicate `待复核` in the task-list row and default main-summary AI job/model exposure were later resolved by `P1-ui-clarity-polish-after-review-pass`.

- `P0-metadata-tab-review-architecture-first-pass`: `PASS`
- Scope: MetadataTab 信息架构首轮收口，仅覆盖真实 `review-pending` 样本。
- Validated HEAD: `372f060450a387da7122064520ecc6a682198dda`; later tag persistence HEAD: `cb6f2376b5146e53c7c83cba62d36bac2236e7e3`.
- Validated structure: 审核摘要; 当前保存值; AI 建议与证据; 技术详情 (`Technical Details`) 默认折叠.
- Actual provider/model displayed from result facts: `ollama` / `qwen3.5:9b`.
- `[object Object]` controlled-classification leak fixed and rerun passed.

- `P1-fix-metadata-current-tags-persistence-contract`: `PASS`
- Scope: `review-pending` task single-tag add + refresh persistence path.
- Validated HEAD: `cb6f2376b5146e53c7c83cba62d36bac2236e7e3`.
- Evidence: task `task-1777788279069`, material `mat-1777788279055`, test tag `uat-tag-persistence`, backend `Material.tags=["uat-tag-persistence"]`, consistency audit `ok=true findingsCount=0`, dependency-health `blocking=false`.
- Contract: `metadata.tags` remains the AI/parse tag source and is not the Operator current-tags fact source.
- Pending: other task states, tag deletion, multi-tag editing, duplicate-tag handling, concurrent edits, and toast stability are not validated.

- `P1-uat-verify-disable-ai-skeleton-local9b-after-decouple`: `PASS`
- Lucia accepted final status as `PASS`.
- Scope: strict no-skeleton local real runtime UAT with local `qwen3.5:9b`, not the retired online MinerU v4 Standard.
- HEAD: `3714590bb2fe351bfc018cd369a08c5491c98628`
- Required local runtime env: `DISABLE_AI_SKELETON_FALLBACK=true`, `OLLAMA_TIER2_MODEL=qwen3.5:9b`
- Must not require: `MINERU_ONLINE_API_BASE_URL`, `MINERU_ONLINE_API_TOKEN`
- Key evidence: task `task-1777788279069`, material `mat-1777788279055`, MinerU task `ebfbd78e-5304-4748-a6e6-c527f3b9b7c6`, AI job `ai-job-1777788288960-12c7`, AI `ollama/qwen3.5:9b`, consistency audit `ok=true findingsCount=0`.
- Director browser verification: pending for this specific run.

- `P1-real-runtime-uat-local-mineru-minio-ollama9b`: `PASS`
- luceonhmm reported `PASS_CANDIDATE`; Lucia accepted final status as `PASS`.
- Scope: local real runtime UAT only, not the retired online MinerU v4 Standard.
- Key evidence: `concmdeMac-mini.local`, HEAD `d0af4837b6d13605cf5245d275031e0a6a13f895`, runtime `http://127.0.0.1:8081/cms/`, compose `docker-compose.yml` + `docker-compose.override.yml`, task `task-1777784999485`, material `mat-1777784999468`, local MinerU task `8c8216c8-6f92-45ea-b76a-c719fcb9e326`, MinIO artifacts `artifact-manifest.json`, `full.md`, `mineru-result.zip`, AI `ollama/qwen3.5:9b`, consistency audit `ok=true findingsCount=0`, Director browser verification completed.

### lutest

lutest is retired. Do not recreate or route new work to the lutest thread unless Director explicitly asks to inspect historical Tier 2 evidence.

## Before Leaving The Windows Machine

1. Check status:

```bash
git status --short --branch
```

2. Commit handoff docs.
3. Push all local commits to GitHub after Director approves.
4. Do not copy `C:\Users\moonp\.codex` as a multi-machine sync mechanism.
5. Rotate any exposed MinerU token before production use.

## First Commands On Mac Mini

```bash
mkdir -p ~/dev ~/staging
cd ~/dev
git clone <github-repo-url> Luceon2026
cd Luceon2026
git status --short --branch
npm install
npx tsc --noEmit
npm run build
npm run local:check
```

Then read `docs/codex/TEST_POLICY.md`. The current local real runtime UAT baseline `P1-real-runtime-uat-local-mineru-minio-ollama9b` is recorded as `PASS`, and the strict no-skeleton local9b configuration baseline `P1-uat-verify-disable-ai-skeleton-local9b-after-decouple` is recorded as `PASS`. New threads should preserve those facts and rerun the baseline only when assigned or when relevant code/runtime changes require it. Do not start by chasing the retired online MinerU v4 token gate unless Lucia or Director explicitly assigns a compatibility-only online validation task.
