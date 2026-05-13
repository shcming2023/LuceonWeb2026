# Director Review: P1 MinerU Progress Diagnostic And Log Source Ownership Review

Review time:
2026-05-13T15:34:48+0800

Reviewed task:
`TASK-20260513-151715-P1-MinerU-Progress-Diagnostic-And-Log-Source-Ownership-Review`

Reviewed report:
`TaskAndReport/2026-05-13T15-17-15+0800_P1-MinerU-Progress-Diagnostic-And-Log-Source-Ownership-Review_REPORT.md`

Decision:
`ACCEPTED_ANALYSIS_CODE_FIRST_IMPLEMENTATION_REQUIRED`

## Summary

Director accepts the Architect report.

The report correctly separates the MinerU progress-observability issue from the P0 AI terminal failure. Task 90 proved that MinerU parsing and artifact ingestion can succeed while the task page still shows an operator-facing diagnostic that sounds like processing is still ongoing. The next step should be code-first: make terminal MinerU completion diagnostics authoritative for display/API semantics without fabricating page, batch, phase, or percent progress.

No production log ownership change is authorized by this review.

## Evidence Reviewed

Architect reported:

- task metadata showed `log-observation-unreadable`;
- material metadata showed `fast-complete-no-business-signal`;
- production log source was reported as `/host/mineru-logs/mineru-api.err.log`, existing but unreadable or empty;
- task page showed `MinerU 已提交/正在处理，但暂无可归因业务日志`;
- MinerU completed and stored artifacts;
- AI failure remains separate.

Director independently inspected the relevant code paths:

- `server/lib/ops-mineru-log-parser.mjs` already has `createFastCompleteMineruObservation()`;
- `server/services/mineru/local-adapter.mjs` builds a completion observation on terminal completion;
- `src/app/utils/taskView.ts` currently formats only the task-level `metadata.mineruObservedProgress`;
- task-page/detail code derives operator lines from task-level observations.

The accepted diagnosis is that terminal completion diagnostics must take precedence over stale/unreadable in-flight diagnostics once MinerU completion is confirmed.

## Boundary

Accepted:

- code-first approach;
- preserve log-unreadable evidence as diagnostics;
- do not fabricate progress details;
- keep AI failure visible and separate from MinerU completion.

Not authorized:

- production config or log mount changes;
- service restart;
- upload validation;
- cleanup/repair/reparse/re-AI of historical tasks;
- DB/MinIO/Docker/model/sample mutation;
- L3, pressure PASS, release-readiness claim.

## Follow-Up

Director issued:

`TASK-20260513-153448-P1-Terminal-MinerU-Diagnostic-Precedence`

Assigned to:

`DevelopmentEngineer`

The optional read-only log-source ownership check is deferred. It can be issued later if the code-first fix still leaves the task page ambiguous or if production validation needs to prove the log mount separately.
