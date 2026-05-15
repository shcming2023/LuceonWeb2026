# User Decision Required: P1 No-Submit Helper Production Sync Decision

- Task ID: `TASK-20260515-120020-P1-No-Submit-Helper-Production-Sync-Decision`
- Created: 2026-05-15T12:00:20+0800
- Created by: Director
- Next Actor: `User`
- Based on Director review: `TaskAndReport/2026-05-15T12-00-20+0800_P1-Runtime-Ownership-No-Submit-And-MinerU-Recovery-Observability-Hardening_DIRECTOR_REVIEW.md`

## Decision Needed

Task 174 is accepted at code/docs level on the development workspace. It fixes `ops/runtime-ownership-status.sh` so the helper is read-only/no-submit by default and only runs MinerU submit-probe when explicitly opted in.

The remaining question is whether to apply this accepted helper/docs change to the production workspace now.

## Why This Matters

The previous production helper could look read-only while actually calling `dependency-health?mineruSubmitProbe=true`, which creates a synthetic MinerU task and may update the durable admission circuit. That is unsafe for future "read-only" role-thread diagnostics.

## Options

### Option A: Approve Scoped Production Source Sync

Recommended.

Authorize a `DevelopmentEngineer` task to update the production workspace to the accepted GitHub main for this helper/docs change and verify:

- production `ops/runtime-ownership-status.sh` has no-submit default;
- `bash -n ops/runtime-ownership-status.sh` passes;
- `bash ops/runtime-ownership-status.sh --help` shows the submit-probe warning;
- default helper output shows `MinerU submit probe skipped`.

Strict boundaries:

- no `--submit-probe`;
- no `mineruSubmitProbe=true`;
- no upload;
- no Docker Compose;
- no rebuild;
- no service restart;
- no DB/MinIO/Docker volume/data mutation;
- no cleanup, repair, retry, reparse, re-AI, or task mutation;
- no config/secret/model/sample mutation;
- no readiness, L3, pressure PASS, release-readiness, production-readiness, production上线, or go-live claim.

### Option B: Hold Production Workspace Untouched

Do not sync production now. Future runtime checks must avoid production `ops/runtime-ownership-status.sh` unless the caller confirms it is the accepted no-submit version or uses the development workspace helper against production path.

Risk: a future role thread may accidentally use the older production helper and perform a submit-probe during a read-only check.

## Director Recommendation

Choose Option A. It is a small, reversible source sync with no service restart and no runtime mutation beyond reading status. It directly removes a known collaboration hazard before more runtime evidence work.

## User Decision

User approved Option A in-thread at `2026-05-15T12:03:07+0800`:

> 同意Option A：只做生产源码同步和只读验证，不重启服务、不跑 submit-probe、不上传、不做压力测试。

Director will issue a scoped `DevelopmentEngineer` task for production source sync and read-only verification only.
