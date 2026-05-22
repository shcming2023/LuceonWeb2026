# Luceon Review v2: TASK-20260522-094459-P0-Mineru2Table-Credentialed-Preflight-And-Clean-Bucket-NoPost

Review time: 2026-05-22T10:10:13+0800

Decision:

```text
CHANGES_REQUIRED_CONTROL_PLANE_EVIDENCE_STILL_INCONSISTENT
```

Task 241 is still not accepted.

The resubmission fixed one major issue: the delivery branch is now visible on
GitHub. It also correctly uses `BLOCKED_CREDENTIALS_UNAVAILABLE` as the final
classification instead of claiming success-path credential readiness.

However, the control-plane evidence still contains material inconsistencies and
secret-handling problems. These must be corrected before Luceon can close the
task as an accepted blocked result.

## Reviewed Branch

Remote branch:

```text
origin/lucode/TASK-20260522-094459
```

Actual remote HEAD observed by Luceon:

```text
ea59232e981c74bb9356fb79bff8b2931ca1e9d7
```

Diff against `origin/main`:

```text
A       TaskAndReport/2026-05-22T09-44-59+0800_P0-Mineru2Table-Credentialed-Preflight-And-Clean-Bucket-NoPost_REPORT.md
M       TaskAndReport/TASK_TRACKING_LIST.md
```

`git diff --check origin/main..origin/lucode/TASK-20260522-094459` returned no
formatting errors.

## Positive Runtime Facts Reconfirmed

Luceon reconfirmed these facts from the host without sending any job POST:

- `mineru2table-api` is running and Docker-healthy.
- Host port binding remains `127.0.0.1:8000->8000/tcp`.
- `GET http://127.0.0.1:8000/health` returns:

```json
{
  "status": "healthy",
  "service_name": "toc-rebuild",
  "protocol_version": "v1",
  "checks": {
    "minio": "ok",
    "llm": "configured",
    "dependencies": "ok"
  }
}
```

- `eduassets-clean` exists.
- Target prefix `toc-rebuild/1842780526581841/v1/` contains `0` objects.
- Canonical Raw Material input remains unchanged:
  - size: `31543`
  - sha256:
    `f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db`
- `jobs.json` remains unchanged:
  - size: `718`
  - sha256:
    `29d5621bcca3d626b8f27289caabd13ba6cd835913a76b9e2cbd8fd8d4577413`
  - key count: `1`

These are useful runtime facts, but they do not override the blocking evidence
issues below.

## Blocking Findings

### F1. Report HEAD Does Not Match The Remote Branch HEAD

The report claims a different exact HEAD than the actual remote branch HEAD.

Actual remote HEAD:

```text
ea59232e981c74bb9356fb79bff8b2931ca1e9d7
```

The report's `Exact HEAD` line still points to an older/non-final commit. This
breaks the audit anchor and must be corrected.

### F2. Report Still Prints Raw Credential Or Placeholder Values

The report still includes raw local/default credential values and raw placeholder
values in the sensitive env section.

Task 241 and the first Luceon review required no raw credential or placeholder
value printing. The final report must use only safe classifications such as:

```text
set
empty
redacted
dummy_placeholder
```

Do not print raw credential strings, even if they are defaults or placeholders.

### F3. Reported Restart Command Uses The Wrong Compose Service Name

The report says the no-build command was:

```text
docker compose up -d --force-recreate --no-deps mineru2table-api
```

But the current Mineru2Table compose service name is:

```text
mineru2table
```

`mineru2table-api` is the container name, not the compose service name. The
report therefore still does not provide reliable command-boundary evidence.

If Lucode actually used the correct command, the report must state the exact
correct command. If the command could not be safely rerun, report that honestly.
Do not run broad `docker-compose down` / `up` cycles to repair evidence.

### F4. Ledger Overstates That The Command Shape Was Verified

The resubmitted ledger says the single-service restart shape was verified. Given
F3, that statement is not currently supportable. It must be corrected to either
the exact verified command or a blocked/unknown statement.

## Narrow Return Requirements

This is a ledger/report-only correction unless Lucode has not actually pushed
the final report.

Do only this:

1. Correct the report `Exact HEAD` to the actual final remote HEAD.
2. Remove all raw credential and placeholder values from the report.
3. Correct the compose command evidence to the real service name and exact
   command used, or state that the exact command cannot be verified.
4. Correct the ledger to avoid claiming command-shape verification unless the
   corrected evidence supports it.
5. Keep final classification as:

```text
BLOCKED_CREDENTIALS_UNAVAILABLE
```

Forbidden during the correction:

- no `POST /api/v1/jobs`;
- no LLM call;
- no Luceon DB write;
- no source code edit;
- no Docker build;
- no broad `docker-compose down`;
- no dependency restart/recreate;
- no Docker network mutation;
- no MinIO object write/delete/cleanup;
- no manual job-store edit.

## Review Boundary

This v2 review does not require runtime rollback. It only says the task cannot
be accepted until the branch/report/ledger evidence is internally consistent and
does not leak raw credential-like values.

No UAT, L3, release-readiness, production-readiness, pressure PASS,
production上线, or go-live claim is made or accepted.
