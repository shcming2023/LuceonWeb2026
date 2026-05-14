# TASK-20260514-093805-P1-MinerU-Live-Progress-Observability-Exactly-One-Controlled-Upload-Validation

Task:
P1 MinerU Live Progress Observability Exactly One Controlled Upload Validation

Assignee:
TestAcceptanceEngineer

Issued by:
Director

Project:
Luceon2026

Development workspace:
`/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`

Production deployment path:
`/Users/concm/prod_workspace/Luceon2026`

Production test sample folder:
`/Users/concm/prod_workspace/Luceon2026/testpdf`

GitHub:
`https://github.com/shcming2023/Luceon2026`

TaskAndReport record:
`TaskAndReport/2026-05-14T09-38-05+0800_P1-MinerU-Live-Progress-Observability-Exactly-One-Controlled-Upload-Validation_TASK.md`

Expected completion report:
`TaskAndReport/2026-05-14T09-38-05+0800_P1-MinerU-Live-Progress-Observability-Exactly-One-Controlled-Upload-Validation_REPORT.md`

## Required Reading Before Execution

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/test-acceptance-engineer.md` if present in the local workspace; if absent, do not block solely on that missing file, and follow `AGENTS.md`, `TEAM_CONTRACT`, and this task brief.
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/prd/Luceon2026-PRD-v0.4.md`
- `docs/codex/TEST_POLICY.md`
- `docs/codex/REPOSITORY_STRUCTURE.md`
- `TaskAndReport/README.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`
- This task brief
- Task 113 report and Director review:
  - `TaskAndReport/2026-05-14T09-15-58+0800_P1-MinerU-Sidecar-Attach-Only-Recovery_REPORT.md`
  - `TaskAndReport/2026-05-14T09-34-12+0800_P1-MinerU-Sidecar-Attach-Only-Recovery_DIRECTOR_REVIEW.md`
- User decision:
  - `TaskAndReport/2026-05-14T09-34-12+0800_P1-MinerU-Live-Progress-Observability-Validation-Decision_DECISION.md`

## Background

Task 113 restored only the MinerU log-observer sidecar transport:

- `luceon-sidecar` is present in tmux.
- `/ops/mineru/log-channel-ownership` reported `sidecar.runningState=observed-recent`.
- Runtime preflight was clean at that time: dependency-health non-blocking, MinerU submit probe accepted, admission circuit closed, and no active/current/queued/takeover parse work.
- Configured production MinerU stdout/stderr logs remained empty.
- `/ops/mineru/global-observation` still saw stale unattributed fallback log content from `uat/scratch/mineru-api.log`.

Director accepted Task 113 only as sidecar-attached idle recovery. It did not prove live MinerU business-progress observability.

The user approved Option A on 2026-05-14: exactly one controlled small/medium PDF upload from `/Users/concm/prod_workspace/Luceon2026/testpdf`, specifically to verify page progress semantics and observability endpoints during real MinerU processing. No pressure test, no second upload, no cleanup, and no上线/readiness claim is authorized.

## Objective

Answer this narrow question with one live production validation:

When one real PDF is uploaded after `luceon-sidecar` attach, does the task page/list/detail surface MinerU progress and final state in a way that is understandable and not misleading, and do the MinerU observability endpoints show live attributable progress, diagnostic-only progress, stale/unattributed signals, or no useful progress?

This is not a throughput, pressure, batch, soak, L3, release-readiness, production-readiness, or go-live test.

## Allowed Operations

In the development workspace:

- run `git status --short --branch`;
- read the task ledger and required documents;
- write this task's completion report;
- update only Task 115 in `TaskAndReport/TASK_TRACKING_LIST.md` to `已回报待 Director 审查` or a blocked/failed status.

In the production deployment path:

- run `git status --short --branch` and `git log -1 --oneline`;
- inspect service state with non-destructive commands such as `docker compose ps`;
- inspect tmux state with non-destructive commands such as `tmux ls`;
- run read-only health/admission/active-task/log-observability checks;
- inventory `/Users/concm/prod_workspace/Luceon2026/testpdf` without modifying sample files;
- select exactly one small/medium PDF from that folder;
- upload exactly one PDF through the existing production upload path;
- observe task list/detail/page semantics until terminal state or clear failure;
- read logs/API surfaces as needed for evidence.

Runtime surfaces to check before upload:

- upload-server health;
- dependency-health with `mineruSubmitProbe=true` and Ollama chat probe if available;
- `/ops/mineru/admission-circuit`;
- `/ops/mineru/active-task`;
- `/ops/mineru/log-channel-ownership`;
- `/ops/mineru/global-observation`;
- Docker service health;
- tmux sidecar presence;
- direct MinerU `/health` if reachable;
- Ollama `/api/ps` or dependency-health residency signal when reachable.

## Forbidden Operations

- Do not upload more than one PDF.
- Do not run pressure, batch-concurrent, soak, broad stress, or long-run tests.
- Do not repair, reparse, re-AI, retry failed historical work, clean up, delete, rename, or mutate historical tasks/materials/artifacts.
- Do not mutate DB/MinIO/Docker volumes/data except for the single authorized upload's normal application-created records/artifacts.
- Do not modify, delete, rename, copy into the repository, or pollute sample files.
- Do not run `docker compose down`, `docker compose down -v`, volume deletion, DB reset, MinIO cleanup, model pull/delete/replace, broad restart, rebuild, rollback, or config/secret/env mutation.
- Do not restart, kill, normalize, or take ownership of MinerU.
- Do not mutate Ollama or attach/restart supervisor.
- Do not change source code, PRD truth, role contracts, release docs, GitHub settings, secrets, model settings, or unrelated files.
- Do not declare L3, pressure PASS, production readiness, release readiness, go-live readiness, or production上线.
- Do not push to GitHub. Director owns GitHub synchronization for this workflow.

## Pre-Upload Stop Conditions

Stop and write a blocked report before uploading if any of these are true:

- active parse or AI work exists;
- admission circuit is open;
- dependency-health is blocking;
- core Docker services are unhealthy;
- `luceon-sidecar` is absent or `/ops/mineru/log-channel-ownership` does not report the sidecar as recently observed;
- production upload-server is not reachable;
- production HEAD cannot be identified;
- sample folder `/Users/concm/prod_workspace/Luceon2026/testpdf` is missing or contains no suitable PDF;
- the validation would require a restart/rebuild, destructive cleanup, repair, reparse, re-AI, model/config change, or ownership normalization.

## Validation Requirements

For the single selected PDF, record:

- sample path, filename, size, and SHA-256 hash;
- why it qualifies as a small/medium sample;
- upload command or UI path used;
- created task id, material id, MinerU task id, and AI job id if available;
- task list/detail/page status transitions visible to the operator;
- whether page/list/detail text clearly communicates MinerU progress, diagnostic-only observation, stale/unattributed logs, failure, or completion;
- `/ops/mineru/log-channel-ownership` snapshots before, during if possible, and after processing;
- `/ops/mineru/global-observation` snapshots before, during if possible, and after processing;
- whether any `log-observation-unreadable`, stale-log, unattributed-log, or MinerU observation warning appears;
- whether any such warning remains diagnostic-only while MinerU API is queued/pending/processing/running;
- whether any transient false failed/self-corrected event appears to the operator;
- parsed artifact count or parsed-file evidence if MinerU completes;
- AI metadata terminal state if the task reaches AI stage;
- final admission-circuit and active-task state.

If the task reaches `review-pending`, record that as a bounded pass for this one controlled upload only. If it fails, record exact stage, reason, visible UI semantics, raw diagnostic evidence, and stop without a second upload.

## Required Checks

At minimum, run and record exit codes for:

- `git status --short --branch` in the development workspace;
- `git status --short --branch` and `git log -1 --oneline` in the production workspace;
- sample inventory, `stat`, and `shasum -a 256`;
- production health/API checks listed above;
- per-sample task/material/AI/admission/active-task/API checks;
- browser-visible page/list/detail checks if browser access is available.

No source-code build, lint, or typecheck is required unless you unexpectedly modify repository code, which is forbidden by this task.

## Completion Report Requirements

Write the report to:

`TaskAndReport/2026-05-14T09-38-05+0800_P1-MinerU-Live-Progress-Observability-Exactly-One-Controlled-Upload-Validation_REPORT.md`

Then update only Task 115 in `TaskAndReport/TASK_TRACKING_LIST.md`:

- if completed: `Status=已回报待 Director 审查`, `Next Actor=Director`;
- if blocked: `Status=挂起`, `Next Actor=Director`;
- include report path, production HEAD, selected sample path/hash, task/material/MinerU/AI ids, terminal state, and concise observability finding.

Do not update project state docs, PRD, role contracts, release docs, or GitHub.

## Acceptance Criteria

Director can accept this task if:

- exactly one PDF was uploaded, or a valid pre-upload blocked report explains why upload was unsafe;
- all preflight evidence is recorded;
- sample identity is recorded with path, size, and hash;
- task/material/MinerU/AI identifiers are recorded where available;
- operator-visible MinerU progress semantics are explicitly assessed;
- log-channel ownership and global observation endpoint behavior are explicitly assessed;
- final task state and final runtime surfaces are recorded;
- no forbidden operation or readiness claim is performed.
