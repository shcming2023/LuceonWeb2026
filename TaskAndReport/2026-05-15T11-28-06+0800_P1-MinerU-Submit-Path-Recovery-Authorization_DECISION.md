# User Decision Required: P1 MinerU Submit-Path Recovery Authorization

- Decision ID: `TASK-20260515-112806-P1-MinerU-Submit-Path-Recovery-Authorization`
- Created: 2026-05-15T11:28:06+0800
- Created by: Director
- Related task: `TASK-20260515-111251-P1-Production-MinerU-Submit-Path-500-Read-Only-Diagnosis-And-Recovery-Plan`

## Current Fact

Production MinerU `/health` is healthy, but the submit path failed HTTP `500` during the last submit-probe. The admission circuit is open and new non-Markdown/PDF intake is blocked. Active-task diagnostics show no current parse queue or takeover work.

This is a release-boundary blocker. It must be recovered, fixed, or explicitly accepted as an operational risk before release-readiness can progress.

## Options

### Option A: Approve Scoped MinerU-Only Recovery And One Submit-Path Verification

Authorize a narrowly scoped runtime recovery task:

1. Confirm no active parse/AI work.
2. Capture current MinerU process/listener/log state.
3. Restart or relaunch only the host MinerU API session/process.
4. Verify direct MinerU `/health`.
5. Run exactly one authorized dependency-health submit-probe.
6. Do not upload files.
7. Do not mutate DB, MinIO, Docker volumes, Ollama, settings, secrets, models, samples, or production code.
8. Stop and report whether the circuit closes or remains open.

Director recommendation: choose Option A. It is the smallest practical step that can unblock PDF intake while preserving scope and evidence.

### Option B: Keep Production Intake Blocked And Do No Runtime Mutation

Leave the admission circuit open and do not recover MinerU now.

This is safest operationally but blocks further release-boundary progression for PDF/MinerU intake.

### Option C: Code/Tooling Hardening First, No Runtime Recovery

Issue a code-level task to add a no-submit/read-only mode to `ops/runtime-ownership-status.sh` and improve submit-probe/log-channel diagnostics before touching runtime.

This improves future safety but does not unblock the current production submit-path failure by itself.

## Requested User Decision

Please choose one:

- `Option A`: scoped MinerU-only recovery plus exactly one submit-path verification.
- `Option B`: keep blocked, no runtime mutation.
- `Option C`: code/tooling hardening first, no runtime recovery.

Unless the user decides otherwise, Director recommends Option A.

## User Decision Recorded

At 2026-05-15T11:36:28+0800, the user approved Option A.

Director will issue a scoped DevelopmentEngineer task to:

1. Confirm no active parse/AI work.
2. Capture current MinerU process/listener/log state.
3. Restart or relaunch only the host MinerU API session/process.
4. Verify direct MinerU `/health`.
5. Run exactly one authorized dependency-health submit-probe.
6. Stop and report whether the admission circuit closes or remains open.

This approval does not authorize uploads, pressure tests, broad service restart, Docker down/down-v/prune, DB/MinIO restore/import, cleanup/cancel/repair/retry/reparse/re-AI, deploy/rebuild/rollback, Ollama/model/config/secret/sample mutation, or any release-readiness/go-live claim.

## Non-Authorized Boundaries

This decision does not authorize uploads, pressure/batch/soak/fresh serial validation, broad service restart, Docker down/down-v/prune, DB/MinIO restore/import, cleanup/cancel/repair/retry/reparse/re-AI, deploy/rebuild/rollback, Ollama/model/config/secret/sample mutation, automatic retry/requeue, skeleton fallback weakening, pressure PASS, L3, release-readiness, production-readiness, production上线, or go-live readiness.
