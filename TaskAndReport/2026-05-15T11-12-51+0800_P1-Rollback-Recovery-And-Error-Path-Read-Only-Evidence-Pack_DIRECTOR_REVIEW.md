# Director Review: P1 Rollback Recovery And Error Path Read-Only Evidence Pack

- Task ID: `TASK-20260515-105951-P1-Rollback-Recovery-And-Error-Path-Read-Only-Evidence-Pack`
- Reviewed at: 2026-05-15T11:12:51+0800
- Reviewer: Director
- Reviewed report: `TaskAndReport/2026-05-15T10-59-51+0800_P1-Rollback-Recovery-And-Error-Path-Read-Only-Evidence-Pack_REPORT.md`
- Result: `ACCEPTED_EVIDENCE_WITH_CRITICAL_BLOCKER`

## Summary

Director accepts the TestAcceptanceEngineer evidence pack. The report materially improves rollback/recovery and error-path evidence, and it correctly identifies the highest-priority current blocker: production MinerU `/health` is healthy, but the submit path returned HTTP `500`, opened the durable admission circuit, and now blocks new non-Markdown intake.

This is no longer only a rollback/evidence-gap issue. It is a live production parse-intake blocker that must be diagnosed and recovered or fixed before any release-boundary progression.

## Director Spot Check

Director performed only non-mutating follow-up checks:

- `GET /__proxy/upload/health`: HTTP 200, `ok=true`.
- `GET /__proxy/upload/ops/dependency-health` without submit probe: HTTP 200, `ok=true`, `blocking=false`; MinerU `/health` OK, MinIO OK, Ollama resident/chat OK.
- The same dependency-health response reports admission circuit `state=open`, `reason=mineru-submit-probe-HTTP 500`, `message=MinerU 当前不可接收新任务，文件未收取，请稍后重试。`
- `GET /__proxy/upload/ops/mineru/admission-circuit`: HTTP 200, `open=true`, last submit probe failed with status `500`.
- `GET /__proxy/upload/ops/mineru/active-task`: HTTP 200, no active task; historical AI failure count remains visible.
- Direct MinerU `/health`: HTTP 200, `status=healthy`, no queued/processing/failed work.

Director did not run submit-probe, upload, restart, repair, cleanup, retry, reparse, re-AI, rollback, failure injection, restore/import, or any production mutation.

## Scope Note

The report notes that `ops/runtime-ownership-status.sh` is documented as a read-only helper but internally calls dependency-health with `mineruSubmitProbe=true`. That behavior is not truly read-only because it attempts a MinerU submit-probe and can change admission-circuit state.

Director accepts the evidence because it surfaced a real production blocker, but this helper/documentation mismatch must be treated as operational debt. Future read-only tasks must not call this helper unless submit-probe side effects are explicitly authorized or the helper is changed to support a no-submit mode.

## Accepted Evidence

Accepted read-only evidence includes:

- DB health and export-shape evidence.
- Selected MinIO raw/parsed/manifest object presence.
- Production-local override preservation evidence.
- Failed/AI residual visibility and task/detail operator semantics.
- Long-running/local-timeout recovery visibility for an existing successful task.
- Current UI dependency-failure surface for the MinerU paused state.
- Gap classification for rollback, service recovery, DB restore, MinIO restore, and live failure-injection paths.

## Decision

The accepted next release-boundary stance is:

`NO_GO_UNTIL_MINERU_SUBMIT_PATH_RECOVERED_OR_FIXED`

This does not declare global no-go for the whole project. It means no release-readiness, production-readiness, pressure PASS, L3, or go-live decision should proceed while production parse intake is blocked by a live MinerU submit-path 500 and an open admission circuit.

## Next Action

Director issues Task 171 to `DevelopmentEngineer`:

`P1 Production MinerU Submit-Path 500 Read-Only Diagnosis And Recovery Plan`

The task is read-only and may inspect logs, code, config, Docker status, process ownership, and existing circuit state. It must not run submit-probe, upload, restart, repair, cleanup, retry, reparse, re-AI, rollback, deploy, or mutate services/data. If recovery requires mutation, the report must recommend an explicit user decision or a separately scoped recovery task.

## Boundaries

This review does not declare pressure PASS, L3, release-readiness, production-readiness, production上线, or go-live readiness.

No rollback, fast-forward, deploy, rebuild, restart, failure injection, upload, pressure/batch/soak/fresh serial validation, cleanup/cancel/repair/retry/reparse/re-AI, destructive mutation, service/config/secret/model/sample mutation, DB/MinIO restore/import, automatic retry/requeue, or skeleton fallback weakening was performed.
