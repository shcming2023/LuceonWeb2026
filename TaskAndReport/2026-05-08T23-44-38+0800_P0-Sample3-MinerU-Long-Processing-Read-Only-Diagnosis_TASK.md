# Task: P0 Sample 3 MinerU Long-Processing Read-Only Diagnosis

- Task ID: `TASK-20260508-234438-P0-Sample3-MinerU-Long-Processing-Read-Only-Diagnosis`
- Issued At: `2026-05-08T23:44:38+0800`
- Issued By: Lucia
- Next Actor: Lucode
- Priority: P0
- Status: `下达待执行`

## Background

Task 44 validated stage-queued production sample intake with three Director-approved true-directory samples.

Samples 1 and 2 reached `review-pending`. Sample 3 remains unresolved:

- File: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/4.XxwlAs2026/sample/Cambridge IGCSE(0580)  Core and Extended Mathematics_2018(Cambridge  University Press).pdf`
- SHA256: `a74d612fd10ec0d6f13c06e2ed1cc386d356af2ed81242bc14fa33d9a4bd7022`
- Task: `task-1778249434820`
- Material: `mat-1778249419780`
- MinerU task id: `ec9452cc-94e4-4b36-bb64-efba86f38cf6`

Lucia read-only refresh at `2026-05-08T23:44:27+0800` showed:

- task state/stage: `running` / `mineru-processing`
- message: `本地等待超时但 MinerU 仍在 processing，后台将继续观测`
- `localTimeoutOccurred=true`
- `mineruStatus=processing`
- observed page progress `714/714`, `100%`
- `observationStale=true`
- no AI metadata job yet for `parseTaskId=task-1778249434820`
- DB health `ok=true`

## Objective

Determine, with read-only evidence, whether sample 3 is:

1. still legitimately processing in MinerU,
2. stuck after MinerU page processing completed,
3. blocked by stale log observation or host MinerU API state mismatch,
4. failed in a way not yet reflected as terminal task state.

## Scope

Allowed:

- Read-only HTTP/curl checks against production CMS/API/DB/ops endpoints.
- Read-only inspection of existing production logs, task records, material records, AI metadata job records, and MinerU API status for `ec9452cc-94e4-4b36-bb64-efba86f38cf6`.
- Read-only process/listener/container inspection.
- Read-only checks of active task/job counts.
- A bounded observation window if needed.
- Report a recommended next action and whether Director authorization would be required.

Forbidden:

- Do not restart, stop, kill, reload, rebuild, redeploy, or mutate production services, Docker containers, Compose state, MinerU, MinIO, Ollama, or upload/db servers.
- Do not change model, timeout, config, secrets, production override, code, DB rows, MinIO objects, Docker volumes, tasks, artifacts, logs, or samples.
- Do not delete, prune, normalize, move, rename, or copy the external sample directory into GitHub.
- Do not trigger a reparse, retry, cleanup, or new upload.
- Do not claim production release readiness.
- Do not persist signed URLs, secrets, local credentials, or private tokens in the report.

## Required Checks

Run only read-only checks:

1. `git status --short --branch` in the production workspace.
2. Read-only task refresh for `task-1778249434820`.
3. Read-only material refresh for `mat-1778249419780`.
4. Read-only AI metadata job lookup for `task-1778249434820` / `mat-1778249419780`.
5. Read-only active parse-task and AI-job counts.
6. Read-only MinerU API/task-status check for `ec9452cc-94e4-4b36-bb64-efba86f38cf6`, if available without mutation.
7. Read-only existing log freshness and latest relevant business/error signals.
8. DB health and dependency-health only if they are read-only and non-mutating.

## Required Output

Create a report in `TaskAndReport/` with:

- Final status: `DIAGNOSIS_ACCEPTED_EVIDENCE`, `STILL_PROCESSING_WITH_EVIDENCE`, `STUCK_REQUIRES_DIRECTOR_DECISION`, or `BLOCKED`.
- Exact commands and timestamps.
- Current state/stage/progress/message for task `task-1778249434820`.
- Current material status.
- MinerU API/task status evidence.
- Log freshness evidence.
- AI job evidence.
- Active task/job counts.
- Whether the issue is runtime throughput, stale observability, terminal-state propagation, or unknown.
- Recommended next action with safety boundary.
- Explicit statement that no forbidden mutation, cleanup, retry, upload, sample modification, signed URL persistence, or release-readiness claim occurred.
