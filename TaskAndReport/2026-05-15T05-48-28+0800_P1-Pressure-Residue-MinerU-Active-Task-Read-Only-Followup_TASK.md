# P1 Pressure Residue MinerU Active Task Read-Only Followup

Issued at: 2026-05-15T05:48:28+0800

Task ID: `TASK-20260515-054828-P1-Pressure-Residue-MinerU-Active-Task-Read-Only-Followup`

Assigned role: `TestAcceptanceEngineer`

Expected report: `TaskAndReport/2026-05-15T05-48-28+0800_P1-Pressure-Residue-MinerU-Active-Task-Read-Only-Followup_REPORT.md`

## Context

Task 151 accepted the manual pressure-test monitoring report as a failed pressure test. Task 152 accepted the architecture diagnosis that three terminal failures are owned by AI metadata / Ollama timeout semantics.

However, Director spot-check during Task 152 review found one pressure residue task still active:

- Parse task: `task-1778765417422`
- Material: `2274129919986463`
- File: `06第六章 长期股权投资与合营安排.pdf`
- MinerU task: `dcdb27f3-fac6-4ede-b456-a96fe358b0da`
- Current state at Director spot-check: `running`
- Current stage at Director spot-check: `mineru-processing`
- Observed message: MinerU processing continues, but log observation is stale at the container-mounted log source.

This task must be followed up read-only before anyone interprets the pressure test as fully settled.

## Objective

Perform read-only monitoring of the currently active pressure residue MinerU task and report one of these outcomes:

- terminal success path reached;
- terminal failure path reached;
- still running but advancing, with evidence;
- clear hang/stall/observation-stale state, with evidence;
- blocked because the necessary read-only evidence is unavailable.

## Required Reading

Read before acting:

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/test-acceptance-engineer.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/codex/TEST_POLICY.md`
- `TaskAndReport/README.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`
- this task brief
- Task 151 report and Director review
- Task 152 report and Director review

## Allowed Actions

Read-only checks only. You may inspect:

- production UI task list/detail pages;
- upload service read-only health and ops endpoints;
- current parse task/material/AI job state through existing read-only APIs;
- direct MinerU health/status endpoints if available and read-only;
- direct Ollama health/residency endpoints only if needed for context;
- browser console/network evidence if you open UI pages.

Suggested evidence:

- `/__proxy/upload/ops/mineru/active-task`
- `/__proxy/upload/ops/dependency-health`
- relevant task/detail API state for `task-1778765417422`
- material state for `2274129919986463`
- current MinerU task status for `dcdb27f3-fac6-4ede-b456-a96fe358b0da`, if available
- log freshness / observation stale diagnostics
- timestamps showing whether progress or status is advancing between observations

## Forbidden Actions

Do not:

- upload any file;
- stop, cancel, repair, retry, reparse, re-AI, delete, or clean any task/material/object;
- mutate DB, MinIO, Docker volumes, source samples, secrets, settings, models, or local config;
- run `docker compose down`, `docker compose down -v`, destructive cleanup, broad restart/rebuild, or service ownership mutation;
- declare pressure PASS, L3 PASS, release-readiness, production-readiness, or go-live;
- modify repository files except for the required report and task ledger update.

## Execution Guidance

Observe at least two read-only snapshots unless the task has already reached a terminal state on the first snapshot. A 15-30 minute gap is acceptable for this pressure residue follow-up.

If the task remains active with stale logs and no meaningful status movement, classify the evidence carefully as `still-running-observation-stale` or `possible-stall`, not as confirmed failure unless a terminal failure or clear service error is observed.

## Required Report

Write the expected report with:

- snapshot times;
- exact endpoints/pages checked;
- parse task state/stage/message/progress;
- material state and MinerU metadata;
- MinerU task status if visible;
- log freshness and stale/active semantics;
- whether the task terminally completed, failed, remained active, or appears stalled;
- commands/endpoints used with exit codes/status;
- skipped checks and reasons;
- explicit statement that no mutation, cleanup, restart, upload, repair, retry, reparse, or re-AI was performed.

Then update `TaskAndReport/TASK_TRACKING_LIST.md`:

- Status: `已回报待 Director 审查`
- Next Actor: `Director`
- Report / Review: link to your report

