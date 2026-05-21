# TASK-230 Luceon Review: CleanService Real Loopback Dispatch Preflight And Authorization Dossier

## Review Decision

`ACCEPTED_READ_ONLY_PREFLIGHT_DOSSIER_WITH_LUCEON_BOUNDARY_CLARIFICATIONS`

Task 230 is accepted as a read-only authorization dossier for a future single real loopback dispatch. It is not an acceptance of real dispatch, Luceon orchestrator runtime wiring, MinIO/LLM configuration, DB metadata mutation, UAT, L3, release readiness, production readiness, pressure PASS, or go-live.

## Reviewed Evidence

- Report: `TaskAndReport/2026-05-21T12-44-30+0800_P0-CleanService-Real-Loopback-Dispatch-Preflight-And-Authorization-Dossier_REPORT.md`
- Reported branch reviewed from GitHub-visible remote state: `origin/lucode/task-230-dispatch-preflight-dossier@2cf824b9bbaee328133ec13f7f0bd917e87137fd`
- `git diff --name-status origin/main..origin/lucode/task-230-dispatch-preflight-dossier` showed only:
  - `A TaskAndReport/2026-05-21T12-44-30+0800_P0-CleanService-Real-Loopback-Dispatch-Preflight-And-Authorization-Dossier_REPORT.md`
  - `M TaskAndReport/TASK_TRACKING_LIST.md`
- `git diff --check origin/main..origin/lucode/task-230-dispatch-preflight-dossier` passed with exit code `0`.

## Luceon Spot Checks

- Luceon workspace was clean before merge: `## main...origin/main`.
- Mineru2Table deployment workspace HEAD: `af80ced635755384a2c878110013c3e2d8f9cb9a`.
- Mineru2Table deployment workspace had existing untracked runtime data: `?? data/`; Luceon did not modify it.
- `docker inspect mineru2table-api --format '{{json .NetworkSettings.Ports}}'` returned `127.0.0.1:8000` host binding for container port `8000/tcp`.
- `GET http://127.0.0.1:8000/health` returned HTTP success with honest service status `unhealthy`, `minio=unconfigured`, `llm=not_configured`, and `dependencies=ok`.
- `GET http://127.0.0.1:8000/openapi.json` exposed:
  - `/api/v1/jobs`
  - `/api/v1/jobs/{job_id}`
  - `/api/v1/jobs:from-storage`
  - legacy `/api/v1/extract` and `/api/v1/tasks` paths
- Masked environment presence check confirmed `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `DEEPSEEK_API_KEY`, and `TOC_REBUILD_CALLBACK_SECRET` are empty in the current `mineru2table-api` container.

## Boundary Clarifications

1. The chat handoff named commit `76cd7ba`, but the GitHub-visible remote branch reviewed by Luceon is `2cf824b9bbaee328133ec13f7f0bd917e87137fd`. Luceon acceptance is anchored to the latter.
2. Option B is a recommended next decision path, not an accepted or executed test result. Its claims about `202`, eventual failed job status, retriable behavior, polling behavior, and Luceon-side failure semantics remain hypotheses until Director explicitly authorizes a real single dispatch and the result is observed.
3. A real `POST /api/v1/jobs` is not read-only. Even in failure-mode, it is expected to mutate Mineru2Table job state at `JOB_STORE_PATH` and may create runtime evidence. That mutation is still pending Director authorization.
4. The dossier is sufficient to support a Director decision between Option A, Option B, and Option C, but it does not itself authorize any of them.

## Accepted Boundary

Accepted:

- Read-only runtime/config/API-route snapshot.
- Masked dependency presence matrix.
- Candidate input requirements and mutation/cost map.
- Director decision options and stop-rule framing.
- Confirmation that current dependency state is intentionally unconfigured for MinIO/LLM.

Not accepted or not performed:

- Any real `POST /api/v1/jobs`.
- Any CleanService worker tick against the real endpoint.
- Any MinIO, DB, Docker volume, model, sample, secret, or LLM mutation.
- Any MinIO credential injection or DeepSeek key configuration.
- Any Luceon orchestrator production wiring.
- Any UAT, L3, release-readiness, production-readiness, pressure PASS, or go-live claim.

## Next Decision

Luceon recommends Option B as the next mainline-first learning step, but only after explicit Director authorization.

Recommended authorization wording:

> Authorize one controlled failure-mode real loopback dispatch only. Keep Mineru2Table MinIO/LLM credentials unconfigured. Permit exactly one `POST /api/v1/jobs` and read-only follow-up status checks. Permit only the expected Mineru2Table job-store mutation. Do not configure credentials, do not write MinIO, do not patch Luceon DB, do not run scheduler-wide activation, and stop after first conclusive result or stop-rule breach.
