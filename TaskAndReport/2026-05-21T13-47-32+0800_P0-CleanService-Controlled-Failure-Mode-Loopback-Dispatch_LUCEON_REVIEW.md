# TASK-231 Luceon Review: Controlled Failure-Mode Loopback Dispatch

## Review Decision

`ACCEPTED_BLOCKED_BEFORE_POST_WITH_EVIDENCE`

Task 231 is accepted as a correct pre-POST block. The requested controlled failure-mode dispatch was not executed because the live Mineru2Table OpenAPI schema gate failed before any real `POST /api/v1/jobs`.

This is not runtime dispatch acceptance, UAT, L3, pressure PASS, release readiness, production readiness, production上线, or go-live.

## Reviewed Evidence

- Report: `TaskAndReport/2026-05-21T13-17-47+0800_P0-CleanService-Controlled-Failure-Mode-Loopback-Dispatch_REPORT.md`
- Remote branch: `origin/lucode/task-231-controlled-failure-dispatch@1ccd21649a9e32dc963423ecc5c5c17a98a245ef`
- `git diff --name-status origin/main..origin/lucode/task-231-controlled-failure-dispatch` showed only:
  - `A TaskAndReport/2026-05-21T13-17-47+0800_P0-CleanService-Controlled-Failure-Mode-Loopback-Dispatch_REPORT.md`
  - `M TaskAndReport/TASK_TRACKING_LIST.md`
- `git diff --check origin/main..origin/lucode/task-231-controlled-failure-dispatch` passed with exit code `0`.

## Luceon Spot Check

Luceon independently rebuilt the same candidate request from current Luceon modules and compared it with live `http://127.0.0.1:8000/openapi.json`.

Observed missing required fields:

- `submitted_at`
- `submitted_by`
- `inputs[0].source.endpoint`
- `inputs[0].source.use_ssl`
- `sink.endpoint`
- `sink.use_ssl`

Luceon also confirmed `/Users/concm/prod_workspace/Mineru2Tables/data/jobs.json` remained `2` bytes with contents `{}`, matching no-job-created/no-POST evidence.

## Evidence Correction

Lucode's report and ledger initially used `be24768e49bfe7ad11d66960d7deec488ca812db` as the exact HEAD, but that SHA is the Luceon main commit that dispatched Task 231. The GitHub-visible Task 231 delivery branch HEAD reviewed and accepted by Luceon is:

```text
1ccd21649a9e32dc963423ecc5c5c17a98a245ef
```

Luceon corrected this control-plane evidence during acceptance.

## Accepted Boundary

Accepted:

- Preflight loopback/dependency/schema-gate execution.
- Correct STOP behavior before malformed POST.
- Final classification `BLOCKED_PAYLOAD_SCHEMA_GAP`.
- Zero real POST and zero job-store mutation.

Not accepted or not performed:

- Real dispatch.
- CleanService payload contract fix.
- MinIO/DB/LLM/Docker/env/secret/model/sample mutation.
- Scheduler activation, upload-server wiring, webhook handling, output ingestion, or real material selection.

## Next Task

Issue Task 232 to align Luceon `JobSubmitRequest` payload generation with live CleanService Protocol v1 required fields. That task remains mock/read-only and must not retry real dispatch.
