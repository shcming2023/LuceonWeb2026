# Director Review: P1 MinerU Log Source Ownership Remediation Route

- Task ID: `TASK-20260514-100030-P1-MinerU-Log-Source-Ownership-Remediation-Route`
- Review time: 2026-05-14T10:13:43+0800
- Reviewed report: `TaskAndReport/2026-05-14T10-00-30+0800_P1-MinerU-Log-Source-Ownership-Remediation-Route_REPORT.md`
- Result: `ACCEPTED_ANALYSIS_CODE_FIRST_REMEDIATION_REQUIRED`

## Decision

Accepted.

The Architect report is read-only, grounded in current runtime facts, and separates the problem correctly:

- `luceon-sidecar` is alive and observed.
- Configured MinerU stdout/stderr log files remain empty.
- Current MinerU is a healthy unmanaged conda process, not the production `luceon-mineru` wrapper.
- Current MinerU stdout/stderr are pipes, not `/Users/concm/ops/logs/mineru-api*.log`.
- Stale `uat/scratch/mineru-api.log` can still pollute global observation as diagnostic fallback.

Director spot-check matched the core facts: tmux shows only `luceon-sidecar`, the MinerU listener on `8083` is a conda Python process, and `/Users/concm/ops/logs/mineru-api.log` plus `.err.log` remain empty.

## Accepted Interpretation

The remaining observability issue has two layers:

1. Code semantics layer: stale workspace fallback logs must not outrank configured production log channels or surface stale `Predict 99%` as useful current progress.
2. Runtime ownership layer: true live business-progress observability likely requires a later controlled MinerU ownership normalization so MinerU writes to the configured log files.

The code layer is safe to address first without production mutation. Runtime ownership normalization is a process mutation and will require a separate User decision.

## Next Step

Issue Task 117 to DevelopmentEngineer:

`P1 MinerU Stale Fallback Hygiene And Progress Semantics Hardening`

Scope is code/test only. No upload, production mutation, Docker command, MinerU/Ollama/sidecar/supervisor start/stop/restart/kill, log deletion/truncation, sample/config/secret/model mutation, readiness claim, or go-live claim is authorized.

No production readiness, L3, pressure PASS, release-readiness, go-live readiness, or production上线 is claimed.
