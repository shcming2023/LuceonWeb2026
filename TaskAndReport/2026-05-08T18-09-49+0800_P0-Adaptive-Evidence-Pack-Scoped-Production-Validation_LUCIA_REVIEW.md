# Lucia Review: P0 Adaptive Evidence-Pack Scoped Production Validation

Review target:

- Task: `TASK-20260508-173100-P0-Adaptive-Evidence-Pack-Scoped-Production-Validation`
- Task brief: `TaskAndReport/2026-05-08T17-31-00+0800_P0-Adaptive-Evidence-Pack-Scoped-Production-Validation_TASK.md`
- Lucode report: `TaskAndReport/2026-05-08T17-41-06+0800_P0-Adaptive-Evidence-Pack-Scoped-Production-Validation_REPORT.md`

Decision:

`BLOCKED_ACCEPTED_EVIDENCE`

## Review Summary

Lucode correctly executed the Director-authorized scoped production apply and correctly stopped before creating the controlled large-PDF validation upload when pre-upload dependency health reported Ollama `qwen3.5:9b` not ready.

This is accepted as blocked evidence, not as production validation pass and not as production release readiness.

## Accepted Facts

- Production workspace was fast-forwarded from `4cc6d3e` to accepted `origin/main` at `8092965`.
- Production-local `docker-compose.override.yml` boundary was preserved:
  - `DISABLE_AI_SKELETON_FALLBACK=true`
  - `OLLAMA_TIER2_MODEL=qwen3.5:9b`
  - MinIO console mapping `127.0.0.1:19001:9001`
- Accepted adaptive evidence-pack code is present in production source after apply:
  - `shouldUseEvidencePack`
  - `evidence-pack-v0.3`
- Minimum necessary Docker/Compose apply was limited to `docker compose up -d --build upload-server`, exit `0`.
- Post-apply services were reported healthy: DB, frontend, MinIO, and upload-server.
- CMS reachability passed.
- DB health passed.
- MinerU submit probe passed with status `202` and task id `29cc340e-ea20-402b-9e06-8392e2dd33e2`.
- Active parse/task states were `0`; active AI jobs were `0`.
- Controlled sample size/hash matched:
  - path: `/Users/concm/prod_workspace/Luceon2026/testpdf/G7_Workbook_ready_to_print.pdf`
  - size: `15157403`
  - SHA-256: `672c96f6125ab3afcf0dcd63b858a2584fa4cdd427000df40870f52aa477435b`
- Controlled validation upload was not created because the pre-upload stop condition was met:
  - `ollama.ok=false`
  - `ollama.chatOk=false`
  - `ollama.model=qwen3.5:9b`
  - `ollama.error="Smoke test failed: The operation was aborted due to timeout"`
  - `ollama.durationMs=15006`

## Boundary Judgment

Lucode did not overstep the task:

- No production release-readiness claim.
- No DB rows deleted.
- No MinIO objects deleted.
- No Docker volumes deleted or pruned.
- No secrets changed.
- No model or timeout policy changed.
- No skeleton fallback or silent degradation added.
- No broad rollback.
- No controlled validation upload was created after readiness failed.

## Residual Risk

The accepted adaptive evidence-pack path is now deployed in production source and upload-server was rebuilt, but runtime proof for the large-PDF adaptive input-selection path remains unavailable because no validation task was created.

The immediate blocker is production Ollama readiness for `qwen3.5:9b`, specifically chat-smoke timeout during dependency health.

## Next Action

Issue a narrow, non-destructive Lucode task to diagnose the Ollama readiness timeout and produce a recovery recommendation. The task must not restart or kill services, pull or change models, change timeout policy, change secrets, run Docker mutation, create uploads, or claim production release readiness unless Director separately authorizes a follow-up.
