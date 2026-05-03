# Luceon2026 Project State

Last updated: 2026-05-03

## Current Migration Decision

The project is moving from multi-computer local Codex development to a single primary Codex environment on the Home Mac mini.

Current Windows working copy:

- Path: `D:\Users\moonp\OneDrive\Mac\项目开发\Luceon2026`
- Branch: `main`
- Current local HEAD before this documentation handoff: `d8ef152 fix(uat): add minio fallback evidence check for artifact quality in standard smoke`
- Local branch status before this documentation handoff: ahead of `origin/main` by 10 commits

Target Mac mini mode:

- Codex threads live on the Mac mini.
- Work computers connect by remote desktop.
- GitHub remains the durable source for code and project memory.
- Dev, staging, and production directories are separated on the Mac mini.

Current role model:

- `lucia`: architecture control, task writing, code-delivery review, validation criteria, and final judgment.
- `lucode`: implementation and code revision from Antigravity workspace `/workspace/ops/Luceon2026`, with host/IDE working copy reference `D:\Users\moonp\OneDrive\Mac\项目开发\Luceon2026`, synchronized through GitHub and scoped by lucia-approved task briefs.
- `luplan`: PRD, decision, changelog, project-state, and handoff maintenance.
- `luceonhmm`: UAT deployment, L2/L3 validation, production-like runtime analysis, dependency debugging, rollback support, and evidence capture.
- `cota`: Director-side cross-project Codex collaboration advisor for multi-agent coordination quality, role-boundary review, task-routing advice, Director-voice suggestions to lucia, and XxwlAs2026/cosh setup guidance.
- `lutest`: retired legacy role. Do not route new validation work there.

## Current Engineering Focus

The current active engineering focus is:

- `P1-real-runtime-uat-local-mineru-minio-ollama9b`
- MinerU: local Conda-deployed MinerU, verified through the effective Luceon runtime path.
- MinIO: Docker-deployed MinIO, verified through raw and parsed object evidence.
- Ollama: Ollama-deployed project-required 9B model, verified through effective AI metadata evidence.
- Skeleton fallback: must not be used as proof of real AI recognition.
- Director approved this policy shift on 2026-05-03: stop tracking missing `MINERU_ONLINE_API_TOKEN` as the main blocker and move the current main gate to the real local runtime dependency chain.

Current accepted validation result:

- `P1-latest-ui-metadata-task-detail-interaction-review`: `PASS`
- luceonhmm final status: `PASS_CANDIDATE`
- Lucia final judgment: `PASS`
- Scope: latest UI/code baseline `origin/main@cb6f2376b5146e53c7c83cba62d36bac2236e7e3`, real local runtime stack, review-pending task `task-1777788279069`, material `mat-1777788279055`, `/cms/tasks`, task detail overview, MetadataTab, classification/tag display, and current tag persistence state.
- Validated UI facts:
  - task list and detail use `待复核` consistently.
  - overview answers state, stage, artifact, and next action.
  - MetadataTab four-layer structure is visible: 审核摘要; 当前保存值; AI 建议与证据; 技术详情 (`Technical Details`) default folded.
  - provider/model displayed as `ollama` / `qwen3.5:9b`.
  - `[object Object]` regression not present.
  - `Material.tags=["uat-tag-persistence"]`.
  - `metadata.tags` remains the AI/parse tag source.
  - dependency-health: `blocking=false`.
  - consistency audit: `ok=true`, `findingsCount=0`.
  - browser console error/warn empty.
- Non-blocking polish still pending: task list row repeats `待复核` as both state and consistency diagnosis; overview still shows some AI job/model technical detail after the summary.
- Scope limits: this is not an L3 or production-readiness claim, not a full-site UI review, and does not validate other task states, tag deletion, multi-tag editing, duplicate-tag handling, concurrent edits, or toast stability.

- `P0-metadata-tab-review-architecture-first-pass`: `PASS`
- Scope: MetadataTab information architecture first-pass closure, covering only a real `review-pending` sample.
- Validated HEAD: `372f060450a387da7122064520ecc6a682198dda`
- Later tag persistence HEAD: `cb6f2376b5146e53c7c83cba62d36bac2236e7e3`
- Validated structure:
  - 审核摘要
  - 当前保存值
  - AI 建议与证据
  - 技术详情 (`Technical Details`) 默认折叠
- Actual provider/model displayed from result facts: `ollama` / `qwen3.5:9b`
- `[object Object]` controlled-classification leak was fixed and the rerun passed.

- `P1-fix-metadata-current-tags-persistence-contract`: `PASS`
- Scope: `review-pending` task single-tag add + refresh persistence path.
- Validated HEAD: `cb6f2376b5146e53c7c83cba62d36bac2236e7e3`
- Task: `task-1777788279069`
- Material: `mat-1777788279055`
- Test tag: `uat-tag-persistence`
- Backend fact: `Material.tags=["uat-tag-persistence"]`
- `metadata.tags` remains the AI/parse tag source and is not the Operator current-tags fact source.
- Consistency audit: `ok=true`, `findingsCount=0`
- Dependency-health: `blocking=false`

- `P1-uat-verify-disable-ai-skeleton-local9b-after-decouple`: `PASS`
- Lucia final judgment: `PASS`
- Scope: strict no-skeleton local real runtime UAT with local `qwen3.5:9b`; not online MinerU v4 Standard.
- HEAD: `3714590bb2fe351bfc018cd369a08c5491c98628`
- Required local runtime env:
  - `DISABLE_AI_SKELETON_FALLBACK=true`
  - `OLLAMA_TIER2_MODEL=qwen3.5:9b`
- Must not require:
  - `MINERU_ONLINE_API_BASE_URL`
  - `MINERU_ONLINE_API_TOKEN`
- UAT taskId: `task-1777788279069`
- materialId: `mat-1777788279055`
- MinerU taskId: `ebfbd78e-5304-4748-a6e6-c527f3b9b7c6`
- AI job: `ai-job-1777788288960-12c7`
- AI provider/model: `ollama` / `qwen3.5:9b`
- Consistency audit: `ok=true`, `findingsCount=0`
- Director browser verification: pending for this specific run
- Baseline meaning: this is the current valid configuration baseline for the local real runtime stack: strict no-skeleton + local qwen3.5:9b.

- `P1-real-runtime-uat-local-mineru-minio-ollama9b`: `PASS`
- luceonhmm final status: `PASS_CANDIDATE`
- Lucia final judgment: `PASS`
- Scope: local real runtime UAT only, not online MinerU v4 Standard.
- Machine: `concmdeMac-mini.local`
- HEAD: `d0af4837b6d13605cf5245d275031e0a6a13f895`
- Runtime URL: `http://127.0.0.1:8081/cms/`
- Compose files: `docker-compose.yml` + `docker-compose.override.yml`
- Upload task: `task-1777784999485`
- Material: `mat-1777784999468`
- Local MinerU task: `8c8216c8-6f92-45ea-b76a-c719fcb9e326`, completed
- Raw object: `originals/mat-1777784999468/source.pdf`
- Parsed prefix: `parsed/mat-1777784999468/`
- MinIO artifacts: `artifact-manifest.json`, `full.md`, `mineru-result.zip`
- `full.md`: 211 bytes, HTTP 200 via presigned URL
- AI job: `ai-job-1777785048072-dfc0`
- AI provider/model: `ollama` / `qwen3.5:9b`
- Final state: task `review-pending`; material `reviewing` / `completed` / `analyzed`
- Consistency audit: `ok=true`, `findingsCount=0`
- Director browser verification: completed; task details usable
- Remaining risk: container configuration was not explicitly proven to have `ALLOW_AI_SKELETON_FALLBACK=false`; this run did not use skeleton, but luceonhmm still needs a configuration closure check.

Retired / compatibility-only validation target:

- The previous online MinerU v4 Tier 2 Standard target using `MINERU_ONLINE_API_BASE_URL=https://mineru.net/api/v4`, `MINERU_ONLINE_API_TOKEN`, `MINERU_ONLINE_MODEL_VERSION=vlm`, and local Docker Ollama `qwen3.5:0.8b` is no longer the current main blocking gate.
- Historical evidence from that line remains useful context, but it must not be rewritten as passed and missing online token must not block `P1-real-runtime-uat-local-mineru-minio-ollama9b`.

Recent commits leading to current state:

```text
d8ef152 fix(uat): add minio fallback evidence check for artifact quality in standard smoke
bcf3de2 fix(uat): increase smoke poll window to 12m and fix pre-check hang
ee932a4 fix(uat): increase ollama timeout and provide text-rich pdf fixture
4ada517 fix(uat): resolve ollama container network and provide valid pdf for standard smoke test
3e3064f feat(mineru): implement v4 online API adapter for Tier 2 Standard
20d0c90 feat(uat): implement tier 2 standard with real MinerU & Ollama configuration
13610d1 docs(prd): record tier2 standard online mineru decision
76fca4b test(uat): add markdown upload regression smoke test
aa2667d docs(prd): record local tier2 uat baseline
328c975 fix(uat): auto-init minio buckets, fix mineru mock health, and allow primitive JSON payloads
```

## Last Known Tier 2 Evidence

The following evidence is retained as historical background for the retired online MinerU v4 Standard line.

At commit `bcf3de2`, the legacy lutest role reported:

- `npm.cmd run tier2:standard:check`: green exit, exit `0`, about `2.7s`
- `node server/tests/tier2-standard-smoke.mjs`: exit `1`, about `576.69s`
- MinerU v4 returned a real `batch_id`
- `full_zip_url` existed
- MinIO contained `full.md`, `mineru-result.json`, `mineru-result.zip`, `artifact-manifest.json`, and content-list artifacts
- AI completed with provider `ollama`, model `qwen3.5:0.8b`
- `aiClassificationProvider=ollama`, not `skeleton`
- Consistency audit was `ok=true` with one existing orphan-object warning

At commit `d8ef152`, Lucia approved code review for a smoke fallback fix that accepts real parsed artifact evidence from `full.md` when `metadata.artifactQuality` is missing. The final green smoke result for `d8ef152` was still pending in the captured handoff.

## Current Blocker

No current blocker remains for the accepted local real runtime UAT scope of `P1-real-runtime-uat-local-mineru-minio-ollama9b` or the strict no-skeleton local9b configuration baseline `P1-uat-verify-disable-ai-skeleton-local9b-after-decouple`.

Current follow-up:

- Latest UI/Metadata/Task Detail review pending scope: no L3 or production-readiness claim; no full-site UI review; other task states beyond the current `review-pending` sample are not validated.
- Latest UI/Metadata/Task Detail tag pending scope: tag deletion, multi-tag editing, duplicate-tag handling, concurrent edits, and toast stability are not validated.
- Latest UI/Metadata/Task Detail non-blocking polish: task list row repeats `待复核` as both state and consistency diagnosis; overview still shows some AI job/model technical detail after the summary.
- Director browser verification is pending for the specific `P1-uat-verify-disable-ai-skeleton-local9b-after-decouple` run.
- This pending browser verification does not change Lucia's recorded PASS for the strict no-skeleton local9b UAT configuration baseline.
- MetadataTab pending scope: other task states beyond the single `review-pending` sample are not validated.
- MetadataTab pending scope: tag deletion, multi-tag editing, duplicate-tag handling, concurrent edits, and toast stability are not validated.
- PRD wording updates beyond recording these MetadataTab facts remain pending unless Lucia or Director separately assigns PRD revision.

Future repeat evidence for this gate should still include:

- environment identity and Git HEAD
- deployment path and compose/runtime mode
- command list, exit codes, and durations
- local MinerU health/reachability/effective task evidence
- MinIO raw and parsed object evidence
- Ollama provider, 9B model, and duration
- `aiClassificationProvider` is real and not `skeleton`
- consistency audit status
- Director manual browser verification status
- strict no-skeleton configuration state

## Immediate Mac Mini Migration Tasks

1. Push the current branch to GitHub after review.
2. Clone the repository on the Home Mac mini into `~/dev/Luceon2026`.
3. Install and sign in to Codex on the Mac mini.
4. Create or reopen `lucia`, `luplan`, and `luceonhmm` threads on the Mac mini.
5. Read `AGENTS.md` and `docs/codex/roles/*.md` in each thread.
6. Re-run L1 on Mac mini.
7. Keep `P1-real-runtime-uat-local-mineru-minio-ollama9b` as the current local real runtime UAT baseline; rerun it when code or runtime changes affect upload, parse, MinIO, Ollama, AI metadata, task state, or result-library behavior.
8. Keep `lutest` archived; route new UAT, L2, L3, and dependency-debugging tasks to `luceonhmm`.
