# P0 Mineru2Table Integration Pre-Implementation Design - Luceon Review

- Task ID: `TASK-20260519-152658-P0-Mineru2Table-Integration-PreImplementation-Design`
- Reviewed at: `2026-05-19T15:39:19+0800`
- Reviewed by: `Luceon`
- Reviewed branch: `origin/lucode/task-221-mineru2table-design`
- Reviewed branch HEAD: `b98965548367db8aebef035b105bce694ae909d0`
- Decision: `CHANGES_REQUIRED_DESIGN_GAPS`

## 1. Judgment

Not accepted yet.

The branch stays inside the allowed file boundary: it adds a design artifact, adds a report, and updates the task ledger only. It does not modify `server/**`, `src/**`, runtime config, Docker files, private role files, production data, DB, MinIO, model files, sample files, or the external Mineru2Table repository.

However, the design is too thin to become the basis for Task A implementation. Task 221 required a concrete implementation-level blueprint with exact state/data contracts, complete future-task gates, data-governance red lines, and exact report evidence. Several required sections are missing or semantically wrong.

Do not merge this branch into `main` as accepted design evidence.

## 2. Blocking Findings

### F1. Data and state contract is incomplete

Task 221 required exact bounded shapes for task metadata, material metadata, job request records, provenance/output summaries, and clean-stage event payloads. The submitted design only provides abbreviated task/material snippets and a note that large artifacts stay in MinIO.

Evidence:

- Required by task brief: `job request records`, `provenance and output summaries`, and `clean-stage event payloads`.
- Submitted design lines 63-91 only cover partial `task.metadata.cleanServiceJobs.toc-rebuild` and `material.metadata.cleanMaterials.toc-rebuild`.

Required correction:

- Add exact JSON-like bounded shapes for:
  - CleanService job request record, including `job_id`, `material_id`, `parse_task_id`, `asset_version`, `inputs`, `sink`, `callback_url`, `callback_secret_ref`, and `options`.
  - Task metadata summary.
  - Material metadata summary.
  - Output/provenance summary, including ObjectRefs and hashes.
  - Clean-stage task-event payloads.
- Explicitly state which fields are persisted in DB and which remain MinIO ObjectRefs only.

### F2. Mandatory data-governance red lines are missing

Task 221 required the design to preserve three red lines: ID-only extraction, asset hash locking, and pure layout/code-generation boundaries. The submitted design does not mention these controls.

Evidence:

- Required by task brief lines 222-228.
- Submitted design ends at open decisions and contains no red-line section.

Required correction:

- Add a dedicated governance section that preserves:
  - ID-only extraction: service/model choices must cite stable block IDs or source references, not invented source text.
  - Asset hash locking: original resource hash names must not be renamed by convenience.
  - Pure layout/code-generation boundary: later LaTeX/TikZ/code-like clean output must use standard packages and avoid custom macros unless separately authorized.
- Tie these rules to the future task sequence and acceptance checks.

### F3. Future implementation tasks do not include the required gates

Task 221 required each future task to include purpose, write boundary, feature flag/default-disabled posture, positive and negative acceptance criteria, minimum tests, and explicit out-of-scope items. The submitted Task A-F list is useful but too sparse.

Evidence:

- Required by task brief lines 150-161.
- Submitted design lines 34-61 provide purpose/boundary/acceptance for some tasks, but not feature-flag posture, negative acceptance, minimum tests, or out-of-scope items per task.

Required correction:

- Expand Task A-F into a dispatchable sequence where every task has:
  - purpose;
  - exact file write boundary;
  - default-disabled or mock-only gate;
  - positive acceptance criteria;
  - negative acceptance criteria;
  - minimum tests and exact smoke/test names where possible;
  - explicit non-goals.

### F4. Soft-limit and hard-limit cost semantics are conflated

The design and report refer to a `cost-decision` state after a hard cost limit, but the accepted contract separates these semantics:

- Luceon soft limit `¥5`: pause for decision.
- Service hard limit `¥8`: stop explicitly with non-retriable `quota_exceeded` or terminal failed state.

Evidence:

- Submitted design line 106 says hard cost failure may enter terminal failure or `cost-decision`.
- Submitted report lines 55-58 ask for hard cost limit authorization flow using `cost-decision`.

Required correction:

- Rewrite cost states so `cost-decision` is reserved for soft-limit policy.
- Treat hard-limit crossing as explicit failed/non-retriable protocol outcome, not an override flow.
- If Lucode wants an override concept, it must be listed as a future Director/User product decision and must not imply bypassing the `¥8` hard stop.

### F5. Raw Material ObjectRef decision overstates a recommendation as contract

Rejecting legacy `eduassets-parsed` compatibility may be a reasonable Lucode recommendation, but the design phrases it as a pipeline mandate before Luceon acceptance. It also says old assets must be re-parsed through an updated pipeline, which could be misread as authorizing reparse or migration.

Evidence:

- Submitted design lines 95-97 say the pipeline must exclusively use canonical layout and legacy parsed layouts must not be bridged.
- Submitted design line 119 later labels this as a Lucode recommendation.

Required correction:

- Keep "no legacy bridge" as a Lucode recommendation pending Luceon acceptance.
- State explicitly that no existing asset reparse, migration, backfill, deletion, or pseudo-provenance creation is authorized by this design.
- Define the safe behavior for legacy assets before a future raw-layout implementation exists, such as `not-applicable`, `skipped-policy`, or "requires separate migration/reparse task".

### F6. Report evidence is not complete enough

The report does not include the final full HEAD and does not record the exact `git diff --name-status` output. It also treats `git diff origin/main --name-status` exit code `0` as proof that only expected files changed; that command's exit code only proves the command ran successfully.

Evidence:

- Submitted report line 7 lists branch but no HEAD.
- Submitted report lines 44-45 list two commands and exit codes but omit exact output.
- Submitted report line 53 says Branch/HEAD was updated but does not record `b98965548367db8aebef035b105bce694ae909d0`.

Required correction:

- Add final full branch HEAD.
- Include exact `git diff origin/main --name-status` output and exit code.
- Include exact `git diff origin/main --check` exit code.
- State that the path audit conclusion is based on the name-status output, not the command exit code alone.

## 3. Review Evidence

Commands run from `/Users/concm/prod_workspace/Luceon2026`:

```bash
git fetch origin --prune --tags
git pull --ff-only origin main
git rev-parse origin/main origin/lucode/task-221-mineru2table-design
git log -1 --oneline origin/lucode/task-221-mineru2table-design
git diff --name-status origin/main..origin/lucode/task-221-mineru2table-design
git diff --check origin/main..origin/lucode/task-221-mineru2table-design
git merge-base --is-ancestor origin/main origin/lucode/task-221-mineru2table-design; echo main_ancestor_exit=$?
```

Observed:

- `origin/main`: `35768e1560c68d2abe4be1acf4ce982160463489`
- reviewed branch HEAD: `b98965548367db8aebef035b105bce694ae909d0`
- latest branch commit: `b989655 TASK-221: Complete Mineru2Table Pre-Implementation Design`
- `main_ancestor_exit=0`
- `git diff --check` exit code `0`
- changed paths:

```text
A	TaskAndReport/2026-05-19T15-26-58+0800_P0-Mineru2Table-Integration-PreImplementation-Design_DESIGN.md
A	TaskAndReport/2026-05-19T15-26-58+0800_P0-Mineru2Table-Integration-PreImplementation-Design_REPORT.md
M	TaskAndReport/TASK_TRACKING_LIST.md
```

After the user clarified that `/Users/concm/prod_workspace/Mineru2Tables` is an accessible Mineru2Table analysis workspace, Luceon also performed a read-only spot-check there:

- workspace status: `main...origin/main`
- HEAD: `43754fa0f3d18051b2d9a3ab4b3cf769a0d47239`
- keyword scan found `content_list_v2.json` support, but no evidence of `/api/v1/jobs`, MinIO ObjectRef job submission, protocol callback/HMAC, `quota_exceeded`, or `max_cost_cny` support.

No external repository mutation or runtime action was performed.

## 4. Required Resubmission

Lucode should revise the same scoped branch or a clean follow-up branch and resubmit:

1. Updated `*_DESIGN.md` addressing F1-F6.
2. Updated `*_REPORT.md` with full HEAD and exact validation output/exit codes.
3. Updated Task 221 ledger row with final branch/HEAD and `Ready for luceon Review`.

No source code, runtime config, production deployment, external repository mutation, upload, submit-probe, pressure, retry, reparse, re-AI, data mutation, AGENTS/.agents edit, readiness/L3/pressure PASS/go-live claim, or legacy asset migration is authorized by this return review.
