# User Decision: P1 Next Validation Scope After Task Detail Progress Pass

- Decision ID: `TASK-20260514-125436-P1-Next-Validation-Scope-After-Task-Detail-Progress-Pass`
- Created: 2026-05-14T12:54:36+0800
- Created by: Director
- Current status: `PENDING_USER_DECISION`
- Based on Director review: `TaskAndReport/2026-05-14T12-54-36+0800_P1-Task-Detail-Progress-Hardening-Exactly-One-Controlled-Upload-Validation_DIRECTOR_REVIEW.md`

## Current Facts

Task 126 passed its exact scope:

- one authorized production UI upload only;
- sample `走向成功_英语_二模卷16篇.pdf`, size `3457503`, SHA-256 `b3e00ad1c7f7afff4bdae1b484abad941af618fd80b9b5f9f22d69848968eaac`;
- task `task-1778733717808`;
- material `2820074763593700`;
- MinerU task `9d5a39b1-d098-40d4-a277-a853433bd006`;
- AI job `ai-job-1778733759504-ed73`;
- final state `review-pending`, material `reviewing`, MinerU completed, AI analyzed, parsed files `25`;
- task detail `当前进展` appeared in all observations;
- task detail/list both showed fine-grained MinerU progress during real processing;
- dependency-repair status polling produced no HTTP 503 and browser console warning/error count was 0;
- final runtime surfaces were clean: active task idle, admission closed, direct MinerU healthy.

Remaining truth:

- This is still a one-sample validation, not pressure/batch/soak/L3/readiness evidence.
- Some early/late diagnostic wording remains, but it did not block operator understanding or terminal correctness in Task 126.
- The project still needs broader evidence before any release-readiness or long-run claims.

## Decision Needed

Choose the next validation scope.

## Option A: Small Serial Validation, Up To 3 PDFs (Director Recommended)

Authorize TestAcceptanceEngineer to run up to 3 additional PDFs from:

`/Users/concm/prod_workspace/Luceon2026/testpdf`

Boundary:

- one upload at a time;
- wait for terminal state before next upload;
- stop immediately on systemic failure;
- record task/detail progress semantics, console noise, queue/admission health, final task/material/AI states, sample hashes, and residual diagnostic wording;
- no pressure, no concurrent batch, no soak, no readiness claim.

Why recommended:

- Task 126 fixed the most immediate UX evidence gap on one sample.
- A small serial pass is the next conservative way to see whether the improvement holds across varied documents without stressing the system.
- It keeps resource collision risk low while building evidence toward later release-readiness planning.

## Option B: Hold Validation And Polish Residual Diagnostic Wording

Assign DevelopmentEngineer to reduce remaining early/late diagnostic wording such as `MinerU 已完成，但本次未捕获可归因业务进度日志` after a task has captured real business progress during processing.

This may improve operator clarity, but it is less urgent than proving the stabilized path on a few more files.

## Option C: Pause Here

Pause the validation line and keep Task 126 as the current best bounded production evidence.

This avoids new production uploads but leaves broader stability untested.

## Director Recommendation

Choose Option A.

Do not move to pressure testing yet. Pressure or long-duration validation should wait until a small serial run passes with clean task-level evidence.
