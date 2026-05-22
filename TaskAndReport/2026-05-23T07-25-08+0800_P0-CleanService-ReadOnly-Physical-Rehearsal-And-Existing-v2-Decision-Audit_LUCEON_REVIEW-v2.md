# Luceon Review v2: TASK-20260522-212810-P0-CleanService-ReadOnly-Physical-Rehearsal-And-Existing-v2-Decision-Audit

## Verdict

Status: Accepted and Closed

Classification: ACCEPTED_READONLY_REHEARSAL_EVIDENCE_WITH_LUCEON_HEAD_CORRECTION

Task 253 is accepted as read-only physical rehearsal evidence. The rehearsal
proved the current runner decision against the existing real `toc-rebuild v2`
metadata without dispatch, DB writes, MinIO writes, or runtime mutation.

## Review Basis

Luceon reviewed the GitHub-visible branch:

```text
origin/lucode/TASK-20260522-212810-P0-CleanService-ReadOnly-Physical-Rehearsal-And-Existing-v2-Decision-Audit@bbd5e9b7cb430eab8e8d9e5f829bc1f012295d3e
```

Baseline:

```text
origin/main@36b7bd558a16bdace92fa06b32b7c069471a2076
```

Diff scope:

```text
A       TaskAndReport/2026-05-22T21-28-10+0800_P0-CleanService-ReadOnly-Physical-Rehearsal-And-Existing-v2-Decision-Audit_REPORT.md
M       TaskAndReport/TASK_TRACKING_LIST.md
```

`git diff --check origin/main..origin/lucode/...` passed with no output.

The submitted report and ledger recorded an intermediate HEAD
`c6eca44eb5520e54366cb45c0f209cc5b1d40131`. Luceon corrected both to the true
remote delivery HEAD `bbd5e9b7cb430eab8e8d9e5f829bc1f012295d3e` during
acceptance. No business code or runtime data was changed.

## Evidence Reviewed

The report states that:

- DB GET observed task `task-1779085089451` in `review-pending`;
- task metadata contains completed `cleanServiceJobs['toc-rebuild']` with
  `assetVersion=v2` and jobId
  `luceon-task245-toc-rebuild-1842780526581841-v2-20260522052230`;
- material `1842780526581841` contains completed
  `cleanMaterials['toc-rebuild']` with `latestVersion=v2`;
- raw object
  `eduassets-raw/mineru/1842780526581841/v1/content_list_v2.json` exists with
  size `31543` and expected SHA256;
- the seven `v2` output artifacts under
  `eduassets-clean/toc-rebuild/1842780526581841/v2/` exist with recorded sizes
  and SHA256 values;
- the runner returned `BLOCKED_EXISTING_TOC_REBUILD_METADATA`;
- tripwire call matrix was `[]`.

Luceon performed an independent GET-only DB spot check from the existing Docker
network and confirmed the relevant task/material `toc-rebuild` metadata.

Luceon also ran a local runner rehearsal using the fetched task/material and
tripwire dependencies. The result matched the report:

```json
{
  "result": {
    "ok": false,
    "status": "BLOCKED_EXISTING_TOC_REBUILD_METADATA",
    "classification": "BLOCKED_EXISTING_TOC_REBUILD_METADATA",
    "reason": "Incompatible existing toc-rebuild metadata exists in task or material records"
  },
  "calls": []
}
```

## Interpretation

This outcome is acceptable for Task 253. The task brief explicitly did not make
`ALREADY_APPLIED_NOOP` the only passing result.

The important mainline evidence is:

1. The current successful `v2` sample is visible in DB metadata and reported
   MinIO evidence.
2. The runner stays pre-dispatch and pre-verify for the existing real metadata.
3. The current runner does not treat the historical completed `v2` metadata as
   already-applied noop. Because completed `v2` is not an active duplicate,
   `allocateAssetVersion` advances toward `v3`; the existing `v2` metadata then
   triggers `BLOCKED_EXISTING_TOC_REBUILD_METADATA`.

This is a useful design decision point before Task 254. We should decide
whether the next step is:

- add a narrow policy for “use current applied clean material as noop/current
  state” when the operator wants no rerun; or
- proceed with a separately authorized new assetVersion run that intentionally
  creates the next version.

## Boundary

Accepted only:

- read-only DB observation;
- read-only MinIO evidence as recorded in the report;
- mock-safe runner decision rehearsal;
- explanation of the existing `v2` decision behavior.

Not accepted or claimed:

- real Mineru2Table dispatch;
- real Mineru2Table job status query;
- DB writes;
- MinIO writes, deletes, cleanup, or replacement;
- Docker/Compose mutation;
- LLM calls;
- source-code changes;
- worker activation;
- UAT, L3, production readiness, pressure PASS, release readiness, or go-live.
