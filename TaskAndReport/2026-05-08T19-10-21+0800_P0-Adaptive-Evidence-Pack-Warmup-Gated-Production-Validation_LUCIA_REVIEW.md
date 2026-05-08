# Lucia Review: P0 Adaptive Evidence-Pack Warmup-Gated Production Validation

Review target:

- Task: `TASK-20260508-183844-P0-Adaptive-Evidence-Pack-Warmup-Gated-Production-Validation`
- Task brief: `TaskAndReport/2026-05-08T18-38-44+0800_P0-Adaptive-Evidence-Pack-Warmup-Gated-Production-Validation_TASK.md`
- Lucode report: `TaskAndReport/2026-05-08T19-05-34+0800_P0-Adaptive-Evidence-Pack-Warmup-Gated-Production-Validation_REPORT.md`

Decision:

`ACCEPTED_CONTROLLED_PRODUCTION_VALIDATION`

## Review Summary

Lucode stayed inside the Director-approved warm-up-gated validation boundary and produced sufficient evidence that the accepted adaptive evidence-pack path is active in production for the controlled large-PDF sample.

This acceptance is a controlled production validation of the adaptive evidence-pack behavior. It is not production release readiness.

## Accepted Facts

- Production code markers were present:
  - `shouldUseEvidencePack`
  - `evidence-pack-v0.3`
- Production-local override boundary was preserved:
  - `DISABLE_AI_SKELETON_FALLBACK=true`
  - `OLLAMA_TIER2_MODEL=qwen3.5:9b`
  - MinIO console mapping `127.0.0.1:19001:9001`
- No active parse tasks or AI jobs existed before upload.
- The authorized sample matched:
  - path: `/Users/concm/prod_workspace/Luceon2026/testpdf/G7_Workbook_ready_to_print.pdf`
  - size: `15157403`
  - SHA-256: `672c96f6125ab3afcf0dcd63b858a2584fa4cdd427000df40870f52aa477435b`
- Exactly one bounded non-mutating Ollama warm-up was performed.
- Warm-up succeeded with `qwen3.5:9b`, but cold load remained slow:
  - total duration about `29.66s`
  - load duration about `29.19s`
- Warm dependency health with MinerU submit probe passed immediately after warm-up:
  - `ok=true`
  - `blocking=false`
  - `mineru.submitProbe.ok=true`
  - `ollama.ok=true`
  - `ollama.chatOk=true`
  - `ollama.durationMs=1015`
- Exactly one controlled upload was created:
  - task ID `task-1778237744029`
  - material ID `mat-1778237743496`
- MinerU completed:
  - `parsedFilesCount=99`
  - raw/parsed artifacts preserved
  - `artifactIncomplete=false`
- AI metadata reached `review-pending`, not failed:
  - AI job `ai-job-1778237936591-e515`
  - provider/model `ollama` / `qwen3.5:9b`
  - message `AI 识别完成 (240690ms)`
- Adaptive input selection was proven:
  - `aiClassificationSamplingMode=evidence-pack-v0.3`
  - original length `104823`
  - selected length `16261`
  - selected input below `30000`
  - input hash `sha256:021a3d990b63704c2474cbfde855ab2d515fb958dca17939907eb2ad67ae901f`
  - trigger reasons `["markdown-length","source-file-size","parsed-files-count"]`
  - thresholds `{markdownLength:50000,fileSize:10000000,parsedFilesCount:50}`
  - observed `{markdownLength:104823,fileSize:15157403,parsedFilesCount:99}`
- Relevant task event evidence included `ai-content-truncated`, provider request start/success, repair success, and final `review-pending` transition.
- No skeleton fallback was generated or represented as real AI recognition.

## Boundary Judgment

Lucode did not overstep:

- No production release-readiness claim.
- Exactly one controlled validation upload.
- No production deploy, fast-forward, rebuild, restart, rollback, or Docker mutation.
- No Ollama restart/start/stop/kill/reload.
- No model, timeout, config, secret, or override change.
- No DB rows, MinIO objects, Docker volumes, tasks, artifacts, or logs deleted.
- No skeleton fallback or silent degradation.

## Residual Risks

- Ollama cold-load remains slow and requires an explicit warm-up gate for reliable validation.
- First-pass output still hit JSON parse/truncation limits at `numPredict=512`; deterministic repair succeeded, but repair remains part of the successful path.
- MinerU observation was attributed through completed-window backfill and marked stale. This is observability debt, not parse failure.
- Production workspace intentionally remained at `8092965`; this task did not authorize production fast-forward to latest docs-only main commits.

## Next Action

Record a Director decision item for the next release-readiness validation scope. The remaining release-readiness work involves priority and risk-boundary choices, including concurrency validation, error-path matrix, rollback/recovery rehearsal, warm-up strategy, and security boundary decisions.
