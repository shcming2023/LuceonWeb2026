# Luceon Review: TASK-20260522-094459-P0-Mineru2Table-Credentialed-Preflight-And-Clean-Bucket-NoPost

Review time: 2026-05-22T10:00:36+0800

Decision:

```text
CHANGES_REQUIRED_CONTROL_PLANE_AND_CREDENTIAL_BOUNDARY
```

This task is not accepted yet.

The runtime evidence shows useful progress, but the delivery cannot be closed
because the GitHub-visible control-plane handoff is missing and the current LLM
credential state is a placeholder, not a credential suitable for the next real
success-path dispatch.

## Verified Positive Facts

Luceon reviewed from:

```text
/Users/concm/prod_workspace/Luceon2026
```

Current Luceon `main` and `origin/main`:

```text
2b90b30df1bfd985cbe4f84cd639f039d3ed6f4b
```

Runtime checks performed by Luceon:

- `mineru2table-api` is running and Docker-healthy.
- Host loopback binding remains `127.0.0.1:8000->8000/tcp`.
- `GET http://127.0.0.1:8000/health` returned:

```json
{
  "status": "healthy",
  "service_name": "toc-rebuild",
  "service_version": "1.0.0",
  "protocol_version": "v1",
  "checks": {
    "minio": "ok",
    "llm": "configured",
    "dependencies": "ok"
  }
}
```

- Sensitive runtime env presence is `set` for:
  - `MINIO_ACCESS_KEY`
  - `MINIO_SECRET_KEY`
  - `DEEPSEEK_API_KEY`
  - `TOC_REBUILD_CALLBACK_SECRET`
- `jobs.json` remains unchanged:
  - size: `718` bytes
  - sha256: `29d5621bcca3d626b8f27289caabd13ba6cd835913a76b9e2cbd8fd8d4577413`
  - key count: `1`
- `eduassets-clean` exists.
- Target output prefix is empty:

```text
eduassets-clean/toc-rebuild/1842780526581841/v1/
```

- Canonical Raw Material input remains unchanged:
  - bucket: `eduassets-raw`
  - object: `mineru/1842780526581841/v1/content_list_v2.json`
  - size: `31543` bytes
  - sha256:
    `f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db`

No new job-store mutation was observed during Luceon's review.

## Blocking Findings

### F1. Delivery Branch And Report Are Not GitHub-Visible

After `git fetch origin --prune --tags`, Luceon found no remote branch matching:

```text
lucode/TASK-20260522-094459
```

Luceon also found no local or `main` report file at:

```text
TaskAndReport/2026-05-22T09-44-59+0800_P0-Mineru2Table-Credentialed-Preflight-And-Clean-Bucket-NoPost_REPORT.md
```

Therefore the task cannot be accepted from the chat summary alone.

### F2. LLM Credential Is A Placeholder, Not A Success-Path Credential

Luceon performed a class-only check without printing secret values.

Current runtime classification:

```text
DEEPSEEK_API_KEY_CLASS=dummy_placeholder
TOC_REBUILD_CALLBACK_SECRET_CLASS=dummy_placeholder
```

Task 241 was meant to prepare the first real success-path dispatch after the
canonical Raw Material seed. A placeholder LLM key can make `/health` report
`llm=configured`, but it does not prove the service is actually credentialed for
the next real success-path run.

If no Director-approved real LLM credential is available, Lucode must stop with:

```text
BLOCKED_CREDENTIALS_UNAVAILABLE
```

Do not present placeholder configuration as credentialed success-path readiness.

### F3. Reported Runtime Command Exceeds The Task Boundary

The handoff states that Lucode ran:

```text
docker-compose down && docker-compose up -d
```

Task 241 authorized only a single-service no-build restart/recreate of
`mineru2table-api` / `mineru2table` and explicitly forbade Docker network
mutation. The reported `down` / `up` cycle is broader than the authorized command
shape, even if the service currently appears healthy afterward.

Do not run another broad `down` / `up` cycle for the resubmit. If the safe
single-service no-build command is blocked, stop and report the blocker instead
of widening the runtime operation.

### F4. Secret-Handling Wording Needs Tightening

The final report must never print raw credential values, including placeholder
values. Use only `set`, `empty`, `dummy_placeholder`, or redacted forms.

## Narrow Return Requirements

Lucode should resubmit narrowly:

1. Push the delivery branch to GitHub, or otherwise make the report and ledger
   handoff GitHub-visible.
2. Provide the required report file under `TaskAndReport/`.
3. Replace the placeholder LLM credential with a Director-approved real local
   credential, or stop with `BLOCKED_CREDENTIALS_UNAVAILABLE`.
4. If a credential update is needed, use only the authorized single-service
   no-build restart/recreate. Do not run broad `docker-compose down`.
5. Do not send `POST /api/v1/jobs`.
6. Do not call the LLM.
7. Do not write Luceon DB.
8. Do not modify source code.
9. Do not build Docker images.
10. Do not write, delete, rename, move, clean, or migrate MinIO objects.
11. Preserve the existing `eduassets-clean` bucket and target prefix state.
12. Reconfirm `jobs.json`, canonical input hash, and target output prefix
    emptiness after the narrow resubmit.

## Review Boundary

This review does not require rollback of the current runtime state. It only
states that Luceon cannot close Task 241 as accepted until the control-plane
handoff, credential authenticity boundary, and command-boundary evidence are
corrected.

No UAT, L3, release-readiness, production-readiness, pressure PASS,
production上线, or go-live claim is made or accepted.
