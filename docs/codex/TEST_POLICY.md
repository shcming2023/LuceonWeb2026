# Luceon2026 Validation Policy

Last updated: 2026-05-03

## Validation Levels

### L1: Fast Code Gate

Owner in the target model: `lucia`

Purpose: determine whether the code is obviously broken before deeper environment validation.

Typical commands:

```bash
npx tsc --noEmit
npm run build
npm run local:check
npm run test:smoke
```

L1 must not be reported as L2, UAT, or production validation.

### L2: Tier 2 Near-Production Validation

Current owner: `luceonhmm`

Legacy owner: `lutest` is retired and must not receive new validation work.

Purpose: validate real integration behavior in a near-production local or staging environment.

Current main L2/UAT target:

- task name: `P1-real-runtime-uat-local-mineru-minio-ollama9b`
- local Conda-deployed MinerU
- Docker-deployed MinIO
- Ollama-deployed project-required 9B model
- real Luceon upload, parse, object-storage, AI metadata, task-state, and result-library behavior
- `aiClassificationProvider` must not be `skeleton`
- parsed artifact evidence must be non-empty

Current accepted result:

- `P2-operator-main-workflow-polish-bundle`: `PASS`
- Lucia final judgment: `PASS`
- Evidence source: luceonhmm reported `PASS_CANDIDATE`, then Lucia accepted it as `PASS`.
- Validated implementation HEAD: `c60152d72fe8dae545a2c18c3f425b6f0620ecf4`
- Scope: local real runtime UAT, task `task-1777849339744`, material `mat-1777849339732`, focused Operator polish checks for MetadataTab tags, completed actions, completed list wording, and overview next-action label.
- Confirmed behavior:
  - MetadataTab tag save immediate sync passed.
  - read-only chip updates immediately after save without refresh.
  - re-entering edit mode preserves the saved draft tags.
  - delete tag -> save -> read-only chip disappears immediately without refresh.
  - refresh UI matches API `Material.tags`.
  - `metadata.tags` was not polluted.
  - completed task detail no longer shows misleading `审核通过` main button.
  - completed task list row no longer shows review action.
  - completed list row no longer shows `需审计`; it shows `待同步` where relevant.
  - overview label now shows `下一步动作`.
  - browser console error/warn empty.
  - consistency audit `findingsCount=0`, `blockingFindings=0`.
- Pending scope: no L3/production-readiness claim, no full-site UI review, no all-task-state validation, no all-error-path validation, and no upload file-picker / upload modal validation.
- Non-blocking polish: `待同步` is clearer than `需审计`, but may still benefit from a tooltip explaining it is a task/material/AI job/artifact status mapping hint, not a failure or audit rejection. Potential follow-up: `P3-task-list-pending-sync-tooltip-polish`.

- `P1-operator-main-workflow-usability-review`: `PASS`
- Lucia final judgment: `PASS`
- Evidence source: luceonhmm reported `PASS_CANDIDATE`, then Lucia accepted it as `PASS`.
- Validated HEAD: `1849beacef6d755859c45e7704ddd467dc3b03aa`
- Scope: local real runtime UAT, task `task-1777849339744`, material `mat-1777849339732`, Operator main workflow: upload real PDF, task list, task detail, MetadataTab, tag save, review approval, ZIP download, and event log.
- Confirmed behavior:
  - real PDF upload created the task successfully.
  - local MinerU completed.
  - MinIO raw and parsed artifacts were available.
  - Ollama provider/model: `ollama` / `qwen3.5:9b`.
  - `review-pending` -> `completed` / `done` can complete.
  - `Material.tags` saved successfully.
  - `metadata.tags` was not polluted.
  - ZIP download succeeded.
  - event log explains MinerU, MinIO, AI, and review stages.
  - dependency-health `blocking=false`.
  - consistency audit `findingsCount=0`, `blockingFindings=0`.
  - browser console error/warn empty.
- Pending scope: no L3/production-readiness claim, no full-site UI review, no complete browser file-picker / upload modal validation, no all-task-state validation, and no all-error-path validation.
- Follow-up polish status: MetadataTab tag save immediate chip/draft sync, completed `审核通过` action visibility, completed-list `需审计` wording, and completed overview next-action label were later resolved by `P2-operator-main-workflow-polish-bundle`.

- `P1-metadatatab-expanded-tag-interaction-validation`: `PASS`
- Lucia final judgment: `PASS`
- Evidence source: luceonhmm reported `PASS_CANDIDATE`, then Lucia accepted it as `PASS`.
- Validated HEAD: `8601eab2dd784f7d808f4bc9257b3b5c47909f9a`
- Scope: real local runtime stack, task `task-1777788279069`, material `mat-1777788279055`, MetadataTab current-tags expanded interaction.
- Confirmed behavior:
  - multi-tag add passed.
  - tag deletion passed.
  - duplicate tag handling passed.
  - refresh persistence passed.
  - toast success was observed.
  - `Material.tags` remains the Operator current tags fact source.
  - `metadata.tags` remains the AI/parse tag source and was not polluted.
  - internal diagnostics title includes `AI 任务`.
  - dependency-health `blocking=false`.
  - consistency audit `findingsCount=0`, `blockingFindings=0`.
  - browser console error/warn empty.
- Final `Material.tags`: `["uat-tag-persistence","uat-tag-multi-a","uat-tag-multi-b"]`
- `metadata.tags` remained: `["PDF","OCR","Pipeline","表格识别","公式识别","含解析产物"]`
- Pending scope: no L3/production-readiness claim, no full-site UI review, no validation for other task states, concurrent editing, or failure-toast/error-path behavior.
- Non-blocking polish: after save success, current-page chips may not immediately sync to the final state, but refresh stabilizes the state. Potential follow-up: `P2-metadatatab-tags-immediate-chip-sync-polish`.

- `P1-ui-clarity-polish-after-review-pass`: `PASS`
- Lucia final judgment: `PASS`
- Evidence source: luceonhmm reported `PASS_CANDIDATE`, then Lucia accepted it as `PASS`.
- Validated HEAD: `87543399673308f2b8ff2febf145c85b3e342f75`
- Scope: `/cms/tasks`, review-pending task detail overview, internal diagnostics folded area, task `task-1777788279069`, material `mat-1777788279055`.
- Validated behavior:
  - task list main status remains `待复核`.
  - same-row diagnostics badge now shows `状态一致`, with no duplicate second `待复核`.
  - overview shows current state, current stage, generated artifact, and next action.
  - AI Job / model technical info no longer appears in the main summary by default.
  - AI metadata job/model remains available after expanding internal diagnostics.
  - dependency-health `blocking=false`.
  - consistency audit `ok=true`, `findingsCount=0`.
  - browser console error/warn empty.
- Pending scope: no MetadataTab full revalidation claim, no products/library/settings review claim, no multi-task-state UI validation claim, and no L3/production-readiness claim.
- Follow-up polish status: internal diagnostics title clarity was later resolved by `P1-metadatatab-expanded-tag-interaction-validation`; the title now includes `AI 任务`.

- `P1-latest-ui-metadata-task-detail-interaction-review`: `PASS`
- Lucia final judgment: `PASS`
- Evidence source: luceonhmm reported `PASS_CANDIDATE`, then Lucia accepted it as `PASS`.
- Scope: latest UI/code baseline `origin/main@cb6f2376b5146e53c7c83cba62d36bac2236e7e3`, real local runtime stack, review-pending task `task-1777788279069`, material `mat-1777788279055`, `/cms/tasks`, task detail overview, MetadataTab, classification/tag display, and current tag persistence state.
- Validated facts:
  - task list and detail use `待复核` consistently.
  - overview answers state, stage, artifact, and next action.
  - MetadataTab four-layer structure is visible: 审核摘要; 当前保存值; AI 建议与证据; 技术详情 (`Technical Details`) default folded.
  - provider/model displayed as `ollama` / `qwen3.5:9b`.
  - `[object Object]` regression not present.
  - `Material.tags=["uat-tag-persistence"]`.
  - `metadata.tags` remains the AI/parse tag source.
  - dependency-health `blocking=false`.
  - consistency audit `ok=true`, `findingsCount=0`.
  - browser console error/warn empty.
- Pending scope: no L3/production-readiness claim, no full-site UI review, no validation for other task states, concurrent editing, or failure-toast/error-path behavior. Tag deletion, multi-tag editing, duplicate-tag handling, refresh persistence, and success toast observation were later covered by `P1-metadatatab-expanded-tag-interaction-validation`.
- Follow-up polish status: duplicate `待复核` in the task-list row and default main-summary AI job/model exposure were later resolved by `P1-ui-clarity-polish-after-review-pass`.

- `P0-metadata-tab-review-architecture-first-pass`: `PASS`
- Scope: MetadataTab information architecture first-pass closure, covering only a real `review-pending` sample.
- Validated HEAD: `372f060450a387da7122064520ecc6a682198dda`
- Later tag persistence HEAD: `cb6f2376b5146e53c7c83cba62d36bac2236e7e3`
- Validated structure: 审核摘要; 当前保存值; AI 建议与证据; 技术详情 (`Technical Details`) 默认折叠.
- Actual provider/model displayed from result facts: `ollama` / `qwen3.5:9b`
- `[object Object]` controlled-classification leak fixed and rerun passed.

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
- Pending scope: other task states, concurrent editing, and failure-toast/error-path behavior are not validated.

- `P1-uat-verify-disable-ai-skeleton-local9b-after-decouple`: `PASS`
- Lucia final judgment: `PASS`
- Scope: strict no-skeleton local real runtime UAT with local `qwen3.5:9b`; this does not prove the retired online MinerU v4 Standard path.
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
- Baseline meaning: current valid configuration baseline is strict no-skeleton + local `qwen3.5:9b` for the local real runtime stack.

- `P1-real-runtime-uat-local-mineru-minio-ollama9b`: `PASS`
- Lucia final judgment: `PASS`
- Scope: local real runtime UAT only; this does not prove the retired online MinerU v4 Standard path.
- Evidence source: luceonhmm reported `PASS_CANDIDATE`, then Lucia accepted it as `PASS`.

The previous online MinerU v4 Standard target is retired from the current main validation path and is retained only as legacy / compatibility-only context:

- retired target: MinerU online v4 + `MINERU_ONLINE_API_TOKEN` + `MINERU_ONLINE_MODEL_VERSION=vlm` + local Docker Ollama `qwen3.5:0.8b`
- missing `MINERU_ONLINE_API_TOKEN` no longer blocks the current main UAT.
- do not report the retired online target as passed unless a future compatibility task explicitly requires and proves it.

Current UAT command set is task-specific. luceonhmm must start from the real runtime path, confirm the effective dependency chain, then run the task's assigned checks without destructive cleanup.

Required report fields:

- machine and OS
- commit hash
- command list and exit codes
- Docker/compose status
- dependency-health result
- local Conda MinerU process/reachability/effective runtime evidence
- Docker MinIO health and object-storage evidence
- Ollama health and effective 9B model evidence
- parsed artifact evidence, including Markdown, JSON, ZIP, or content-list evidence when applicable
- AI job id
- AI provider and model
- AI duration
- `aiClassificationProvider`
- whether skeleton fallback was used
- consistency audit result
- Director browser verification state

Accepted local real runtime UAT evidence for the 2026-05-03 PASS:

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

Accepted strict no-skeleton local9b evidence for the 2026-05-03 PASS:

- HEAD: `3714590bb2fe351bfc018cd369a08c5491c98628`
- Required local runtime env: `DISABLE_AI_SKELETON_FALLBACK=true`, `OLLAMA_TIER2_MODEL=qwen3.5:9b`
- Online MinerU env not required: `MINERU_ONLINE_API_BASE_URL`, `MINERU_ONLINE_API_TOKEN`
- UAT taskId: `task-1777788279069`
- materialId: `mat-1777788279055`
- MinerU taskId: `ebfbd78e-5304-4748-a6e6-c527f3b9b7c6`
- AI job: `ai-job-1777788288960-12c7`
- AI provider/model: `ollama` / `qwen3.5:9b`
- Consistency audit: `ok=true`, `findingsCount=0`
- Director browser verification: pending for this specific run

### L3: Home Mac Mini Production Truth

Target owner: `luceonhmm`

Purpose: validate the actual staging or production environment on the Home Mac mini.

Only L3 can be treated as production truth. L1 and L2 can support a release decision, but they do not replace L3.

## Result Vocabulary

Use these words exactly in reports:

- `PASS`: command or validation target completed and met the stated criteria.
- `FAIL`: command or validation target ran and violated the criteria.
- `BLOCKED`: required environment, credential, service, or input was missing.
- `SKIPPED`: intentionally not run, with reason.
- `PENDING`: started but not completed by the handoff point.

Do not use "passed" for a check that did not return a green exit code.

## Secret Handling

MinerU, AI provider, and other secrets must only be injected through local process environment or local uncommitted secret management.

Reports may say:

```text
MINERU_OR_AI_TOKEN=<present, redacted>
```

Reports must not include any full token or secret value.

## Destructive Operations

These require explicit Director approval:

- `docker compose down -v`
- deleting Docker volumes
- clearing MinIO buckets
- clearing DB data
- deleting production or staging deployment data
- changing production secrets

Rebuilding containers with `up -d --build --force-recreate` is allowed for L2 when the task explicitly asks for it, as long as volumes are not wiped.
