# P0 Asset Pipeline PRD Iteration PDF Raw Clean Traceability - Luceon Review

- Task ID: `TASK-20260519-143047-P0-Asset-Pipeline-PRD-Iteration-PDF-Raw-Clean-Traceability`
- Review time: `2026-05-19T15:05:00+0800`
- Reviewed by: `Luceon`
- Reviewed branch: `origin/lucode/task-220-asset-pipeline-prd-iteration`
- Reviewed HEAD: `bf82b6ee57cbf19859461a442a236a9dc412c532`
- Decision: `CHANGES_REQUIRED`

## 1. Summary

The PRD and architecture documentation edits mostly move in the intended direction: they promote the Director-confirmed `PDF -> Raw Material -> Clean Material` asset chain, preserve Raw Material as a durable prerequisite layer, position Mineru2Table as the first structure-rebuild/preparation step, and keep `RawMaterial2CleanMaterial` as a later distinct cleaning stage.

However, the submission cannot be accepted because it includes an unauthorized repository-level always-on agent/rule file and the report does not provide the exact validation exit-code evidence required by the task brief.

No production deployment, runtime validation, upload, submit-probe, data migration, DB/MinIO/Docker mutation, CleanServiceWorker implementation, Mineru2Table dispatch, or readiness/go-live claim was performed during this review.

## 2. Blocking Findings

### F1 - Unauthorized always-on role/rule file committed

- File: `.agents/rules/luceon2026rules.md`
- Lines observed: `1-39`
- Severity: blocking

Task 220's write boundary allowed only PRD/docs/contracts/project-state/handoff/report/ledger files. It did not allow `.agents/**`. The task also explicitly forbade role-file edits and the Director previously required role settings to remain local/private and not be synchronized into the repository.

The added file is an always-on rule file:

- `trigger: always_on`
- defines `luceon` / `lucode` physical topology;
- defines check-task SOP;
- instructs broad `git add .` behavior.

This violates the isolation boundary and risks making local role/runtime rules visible to the other side through GitHub. It must be removed from the branch. Do not replace it with another committed role/rule/config file.

### F2 - Report omits exact validation exit codes required by the task brief

- File: `TaskAndReport/2026-05-19T14-30-47+0800_P0-Asset-Pipeline-PRD-Iteration-PDF-Raw-Clean-Traceability_REPORT.md`
- Severity: blocking

The task brief required the report to include "validation commands and exact exit codes." The submitted report says `git diff --check` passed and Markdown syntax is valid, but it does not record exact commands with exit codes. The correction report must include the exact validation commands and exit codes, at minimum:

- `git diff --check` with exit code;
- a read-only changed-file/path audit showing no forbidden areas remain changed;
- any Markdown/document validation command actually run, with exit code.

## 3. Non-Blocking Content Notes

The product/architecture text is directionally acceptable after the blocking issues are removed. In the next correction, keep the documentation changes narrow; do not rework the PRD beyond fixing the two review findings unless Luceon explicitly requests it.

## 4. Required Correction

Lucode should resubmit the same task branch with only these corrections:

1. Remove `.agents/rules/luceon2026rules.md` from the branch.
2. Ensure the changed-file set is limited to the Task 220 allowed write boundary.
3. Update the report with exact validation commands and exit codes.
4. Update the ledger row with the corrected branch/HEAD.
5. Do not implement code/runtime changes, production deployment, data migration, or any CleanService/Mineru2Table dispatch.

## 5. Review Evidence

Commands run from `/Users/concm/prod_workspace/Luceon2026`:

```bash
git fetch origin --prune --tags
git rev-parse origin/lucode/task-220-asset-pipeline-prd-iteration
git log -1 --oneline origin/lucode/task-220-asset-pipeline-prd-iteration
git diff --name-status origin/main..origin/lucode/task-220-asset-pipeline-prd-iteration
git show origin/lucode/task-220-asset-pipeline-prd-iteration:TaskAndReport/2026-05-19T14-30-47+0800_P0-Asset-Pipeline-PRD-Iteration-PDF-Raw-Clean-Traceability_REPORT.md
git show origin/lucode/task-220-asset-pipeline-prd-iteration:.agents/rules/luceon2026rules.md
git diff --check origin/main..origin/lucode/task-220-asset-pipeline-prd-iteration
```

Observed:

- Remote branch exists at `bf82b6ee57cbf19859461a442a236a9dc412c532`.
- `git diff --check origin/main..origin/lucode/task-220-asset-pipeline-prd-iteration` produced no whitespace errors.
- Changed-file set included unauthorized `.agents/rules/luceon2026rules.md`.

