# P1 CleanService External Protocol Pause And MinerU Validation Refocus

Decision record timestamp: 2026-05-16T08:48:28+0800

Task ID: TASK-20260516-084828-P1-CleanService-External-Protocol-Pause-And-MinerU-Validation-Refocus

Recorded by: Director

## Decision

User approved the Director correction to pause the external Mineru2Table CleanService protocol implementation decision and return the active project focus to MinerU progress semantics and long-run pressure validation.

## Background

Task 203 accepted that the external `/Users/concm/prod_workspace/Mineru2Tables` service is not yet compatible with the proposed CleanService Protocol v1, and Task 204 asked whether to authorize external Mineru2Table protocol implementation.

The user corrected the sequencing: the project is not yet ready to prioritize independent Mineru2Table service integration while these core Phase 1 questions remain unresolved:

- Is the current task-page progress semantics display actually normal after the `progressSnapshot` deployment?
- Has a long-running pressure validation passed after that deployment?
- Has MinerU log/progress integration been proven under real active MinerU processing?

Director agrees with the correction. CleanService/Mineru2Table protocol work remains recorded as useful future direction, but it must not drive the current next action.

## Current Evidence Boundary

- Task 193 implemented normalized `progressSnapshot`, active-task direct MinerU/DB reconciliation, `db-behind-direct-mineru` lag semantics, terminal/idle stale-log distinction, readiness-only dependency-health boundary, and task-event log cleanup.
- Task 197 deployed and read-only validated that `progressSnapshot.version=progress-snapshot-v0.1` is visible in production.
- Task 190 accepted a 24-PDF terminal monitoring run only as evidence with residuals: 24 MinerU parses completed, 23 reached review-pending/review, 1 failed in AI, and progress semantics lag/log-channel stale issues remained.
- There is not yet a fresh long-run pressure validation proving that the new progress semantics are reliable during active MinerU processing.

## Scope Correction

Task 204 is paused. No external Mineru2Table repository mutation, protocol implementation, service deployment, or Luceon real dispatch wiring is authorized by this decision.

The next scoped action is Task 205 for TestAcceptanceEngineer: validate current MinerU progress semantics during a fresh controlled, user-started pressure run, or record a blocked baseline if no user-started run is available.

## Forbidden By This Decision

- Do not implement or mutate external Mineru2Table.
- Do not wire real CleanService dispatch in Luceon.
- Do not deploy, restart, or mutate production services for this decision.
- Do not upload or clear data automatically.
- Do not run manual submit-probe.
- Do not retry, reparse, re-AI, repair, cancel, or reset tasks.
- Do not mutate DB, MinIO data/volumes, Docker volumes, model files, secrets, config, or sample files.
- Do not claim pressure PASS, L3, production readiness, release readiness, production上线, or go-live.

## Follow-up

Director issued Task 205 to TestAcceptanceEngineer.
