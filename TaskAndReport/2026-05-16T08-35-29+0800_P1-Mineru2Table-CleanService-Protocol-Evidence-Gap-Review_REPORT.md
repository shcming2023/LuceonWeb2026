# Architect Report: P1 Mineru2Table CleanService Protocol Evidence Gap Review

- Task ID: `TASK-20260516-083529-P1-Mineru2Table-CleanService-Protocol-Evidence-Gap-Review`
- Assignee: Architect
- Director task brief: `TaskAndReport/2026-05-16T08-35-29+0800_P1-Mineru2Table-CleanService-Protocol-Evidence-Gap-Review_TASK.md`
- Luceon workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Luceon branch / HEAD during report: `main` / `9bb9c4f`
- External checkout inspected: `/Users/concm/prod_workspace/Mineru2Tables`
- External branch / HEAD during report: `main` / `43754fa`
- Report date: 2026-05-16

## Scope Confirmation

I followed the Director task brief and kept this task read-only except for the required Luceon report and task-ledger update.

I did not implement code, edit the external Mineru2Table repository, mutate Luceon source code, run production/runtime operations, start/stop/restart/build/install/deploy Mineru2Table, mutate Docker/DB/MinIO/MinerU/Ollama/models/secrets/configs/samples, run upload/pressure/submit-probe/retry/reparse/re-AI/cleanup/repair/reset, or claim production acceptance, production readiness, release readiness, L3, pressure PASS, production上线, or go-live.

Files changed by this task:

- `TaskAndReport/2026-05-16T08-35-29+0800_P1-Mineru2Table-CleanService-Protocol-Evidence-Gap-Review_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

## Evidence Sources

Luceon-side sources read:

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/architect.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/prd/Luceon2026-PRD-v0.4.md`
- `docs/prd/Luceon2026-PRD-v0.4-CleanService-Addendum.md`
- `docs/codex/TEST_POLICY.md`
- `docs/codex/REPOSITORY_STRUCTURE.md`
- `TaskAndReport/README.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`
- `docs/architecture/Luceon2026-Asset-Pipeline-Vision.md`
- `docs/contracts/CleanService-Protocol-v1.md`
- `docs/contracts/CleanService-Mineru2Table-Adaptation-Plan.md`
- `TaskAndReport/2026-05-15T20-21-23+0800_P1-CleanServiceWorker-Luceon-Implementation-Plan_REPORT.md`
- `TaskAndReport/2026-05-16T07-46-08+0800_P1-CleanServiceWorker-Luceon-Implementation-Plan_DIRECTOR_REVIEW.md`
- `TaskAndReport/2026-05-16T08-35-29+0800_P1-CleanService-Worker-Eligibility-InputRef-Correction_DIRECTOR_REVIEW.md`

External Mineru2Table sources read:

- `/Users/concm/prod_workspace/Mineru2Tables/api_server.py`
- `/Users/concm/prod_workspace/Mineru2Tables/README.md`
- `/Users/concm/prod_workspace/Mineru2Tables/PRD.md`
- `/Users/concm/prod_workspace/Mineru2Tables/Docs/toc_rebuild_decisions.md`
- `/Users/concm/prod_workspace/Mineru2Tables/Docs/references/output-spec.md`
- Targeted `rg` evidence across `api_server.py`, `README.md`, `PRD.md`, `Docs`, `src`, `tests`, `docker-compose.yml`, and `.env.example`
- Already-running local service health and OpenAPI path reads at `http://127.0.0.1:8000`

Candidate external paths:

| Path | Result |
| --- | --- |
| `/Users/concm/prod_workspace/Mineru2Tables` | found and inspected |
| `/Users/concm/prod_workspace/Mineru2Table2026` | not found |
| `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/Mineru2Table2026` | not found |
| `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/Mineru2Tables` | not found |

## Executive Judgment

Current Mineru2Table is useful as a TOC rebuild engine, but it does not yet implement `CleanService-Protocol-v1`.

Supported evidence exists for:

- a basic `/health` endpoint;
- deprecated-style multipart/file upload routes;
- an in-memory async task API;
- generation of TOC rebuild outputs in local/API result payloads;
- API-key header authentication for current routes;
- token and cost tracking as internal result metadata.

Blocking gaps remain for real Luceon dispatch:

- no `POST /api/v1/jobs` ObjectRef job submission;
- no `GET /api/v1/jobs/{job_id}` persistent CleanService status API;
- no durable job store;
- no idempotency by Luceon-owned `job_id`;
- no MinIO ObjectRef input/output support;
- no protocol `provenance.json`;
- no callback/webhook or signed terminal delivery;
- no CleanService structured error model;
- no `¥8` hard cost stop semantics;
- no timeout/retry contract;
- no protocol identity fields across health/status/provenance.

Therefore Luceon must not enable real Mineru2Table dispatch yet. Luceon can continue mock-protocol foundation work only while disabled by default.

## Protocol Evidence Matrix

| # | Requirement | Classification | Evidence | Notes |
| ---: | --- | --- | --- | --- |
| 1 | `/health` shape and service identity/version/protocol fields | partial | `api_server.py` defines `GET /health`; live `curl http://127.0.0.1:8000/health` returned `{"status":"healthy","version":"1.0.0","timestamp":"...","llm_status":"not_configured"}` | Health exists, but lacks `service_name`, `service_version`, `protocol_version`, and `checks.minio/llm/dependencies` required by CleanService v1. |
| 2 | `POST /api/v1/jobs` ObjectRef job submission | missing | OpenAPI path list: `/api/v1/extract`, `/api/v1/tasks`, `/api/v1/tasks/{task_id}`, `/health`; `rg` found no `/api/v1/jobs` | Current APIs are multipart/file upload routes. |
| 3 | `GET /api/v1/jobs/{job_id}` persistent job status | missing | No `/api/v1/jobs/{job_id}` route; current status route is `GET /api/v1/tasks/{task_id}` | Current status model uses `task_id`, not Luceon-owned `job_id`. |
| 4 | Persistent job state across process restart | missing | `api_server.py` declares `_task_store: Dict[str, Dict[str, Any]] = {}` with comment saying memory-level storage and restart loss | Restart durability is explicitly absent. |
| 5 | Idempotency by `job_id` | missing | `create_task()` generates `task_id = str(uuid.uuid4())[:8]`; no request-owned `job_id` is accepted | Repeated submissions create new task IDs. |
| 6 | MinIO ObjectRef input support | missing | Current `extract_sync()` and `create_task()` accept `UploadFile`; `_extract_zip_and_find_json()` reads local temp/zip contents | No MinIO endpoint/bucket/object request schema or allowlist. |
| 7 | MinIO ObjectRef output support | missing | Current API returns JSON response/result; README describes local `Output/` files for CLI | No sink ObjectRef or MinIO writer for `eduassets-clean`. |
| 8 | Required artifacts: `flooded_content`, `logic_tree`, `readable_tree`, `skeleton`, `provenance` | partial | README documents `debug_skeleton.json`, `output_logic_tree.json`, `output_readable_tree.md`, `output_flooded_content.json`; API returns `markdown_tree`, `logic_tree`, `flooded_data`, `token_stats` | Core content artifacts exist conceptually, but names differ and `provenance` is absent. |
| 9 | Provenance fields for service/protocol/material/version/input/output/cost | missing | `rg` found no `provenance.json`, `service_name`, or `protocol_version` implementation evidence | Token/cost stats exist but are not protocol provenance. |
| 10 | Callback/webhook or clear polling-only contract | partial | Current `GET /api/v1/tasks/{task_id}` provides polling; no webhook/callback evidence | Polling exists for old task route, but no CleanService polling contract and no terminal callback. |
| 11 | Structured errors matching CleanService v1 | partial | FastAPI raises `HTTPException` with string `detail`; task status stores `error: str(e)` | Not the required `{error:{code,message,details,retriable}}` model. |
| 12 | Cost limit support: Luceon soft `¥5`, service hard `¥8` | partial | `token_stats` includes estimated and actual cost; UI shows token cost; no `max_cost_cny` or `quota_exceeded` found | Cost measurement exists, enforcement does not. |
| 13 | Timeout and retry semantics | unknown | No CleanService timeout/retry contract found; background thread handles exceptions as failed | There may be library/network timeouts inside LLM client, but no protocol-visible timeout/retry semantics. |
| 14 | Security/auth: API key and callback signature | partial | `API_KEY_NAME = "X-API-Key"` and FastAPI dependency protect routes when `API_KEY` env exists | API key exists; callback HMAC/signature does not. |
| 15 | Current gaps blocking Luceon real dispatch | supported as blockers | Evidence above plus Luceon `CleanService-Protocol-v1.md` and adaptation plan | Real dispatch is blocked until external service implements/proves protocol features. |

## External Architecture Findings

Current external API shape:

- `GET /health`
- `POST /api/v1/extract`
- `POST /api/v1/tasks`
- `GET /api/v1/tasks/{task_id}`
- `GET /api/v1/tasks`
- `DELETE /api/v1/tasks/{task_id}`

Current async model:

- file upload writes to a temp file;
- `task_id` is server-generated from UUID;
- task state is held in process memory;
- background thread runs `_run_pipeline()`;
- terminal result is stored under `_task_store[task_id]["result"]`;
- temp files and extracted directories are removed after processing.

This is a reasonable standalone service/API prototype, but it is not yet an orchestrated durable CleanService.

## Blockers Before Luceon Real Dispatch

Luceon real dispatch must remain blocked until Mineru2Table provides evidence for these items:

1. `GET /health` returns `service_name="toc-rebuild"`, `service_version`, `protocol_version="v1"`, dependency checks, and unhealthy `503` behavior.
2. `POST /api/v1/jobs` accepts Luceon-owned `job_id`, `material_id`, `parse_task_id`, `asset_version`, MinIO `inputs[]`, MinIO `sink`, callback fields, and hard limits.
3. `GET /api/v1/jobs/{job_id}` returns persistent protocol job state after process restart.
4. Repeated `POST /api/v1/jobs` with the same `job_id` returns an idempotency hit without duplicate work.
5. Service reads MinIO input ObjectRefs from allowlisted endpoints/buckets without credentials in request bodies.
6. Service writes required artifacts to the Luceon-provided sink prefix.
7. `provenance.json` includes service identity, implementation repo/commit, material/task/version/job IDs, input/output hashes, options, token/cost stats.
8. Terminal delivery is either signed webhook or an explicitly accepted polling-only contract.
9. Errors use CleanService v1 codes and retriable semantics.
10. `options.max_cost_cny=8.0` and/or token ceilings stop explicitly with `quota_exceeded` / `retriable=false`.
11. API key and callback HMAC configuration are documented and tested.
12. Old multipart routes are retained but deprecated, not used as Luceon's long-term production path.

## Recommended Next Tasks

External-service work:

1. Director should issue a Mineru2Table-side implementation task for CleanService Protocol v1 foundations: health identity, `/api/v1/jobs`, persistent job store, idempotency, MinIO storage adapter, output/provenance writer, structured errors, cost hard-limit, and API/auth configuration.
2. Add Mineru2Table tests for ObjectRef submit/status, idempotency, restart persistence, MinIO fixture output, provenance schema, `quota_exceeded`, and old-route compatibility/deprecation.
3. Add a byte-identical copy/sync check for `CleanService-Protocol-v1.md` between Luceon2026 and Mineru2Table2026 once the external repo has an approved protocol location.

Luceon work:

1. Continue Luceon CleanService mock/protocol work only behind disabled-by-default configuration.
2. Do not wire real Mineru2Table endpoint into runtime startup, callback, polling, or production deployment until external protocol evidence is reviewed.
3. After external evidence exists, dispatch a Luceon mock-to-real adapter task using one controlled MinIO fixture and no production readiness claim.
4. Keep UI/product states separate from current Phase 1 AI metadata path until Director accepts protocol and ProductManager acceptance wording.

## Commands Run

All commands were read-only except report and ledger editing at the end.

| Command | CWD | Exit |
| --- | --- | ---: |
| `git status --short --branch` | Luceon workspace | 0 |
| `rg -n "\\| Architect \\|" TaskAndReport/TASK_TRACKING_LIST.md` | Luceon workspace | 0 |
| `sed -n ...` required Luceon task/docs/reports | Luceon workspace | 0 |
| `test -d` loop for four candidate Mineru2Table paths | Luceon workspace | 0 |
| `git status --short --branch` | `/Users/concm/prod_workspace/Mineru2Tables` | 0 |
| `find . -maxdepth 3 -type f ...` | `/Users/concm/prod_workspace/Mineru2Tables` | 0 |
| `rg -n "health|/api/v1|extract|tasks|jobs|job_id|..." .` | `/Users/concm/prod_workspace/Mineru2Tables` | 0 |
| `sed -n ... api_server.py README.md PRD.md Docs/...` | `/Users/concm/prod_workspace/Mineru2Tables` | 0 |
| `lsof -nP -iTCP:8000 -sTCP:LISTEN || true` | `/Users/concm/prod_workspace/Mineru2Tables` | 0 |
| `curl -sS --max-time 3 http://127.0.0.1:8000/health` | `/Users/concm/prod_workspace/Mineru2Tables` | 0 |
| `curl -sS --max-time 3 http://127.0.0.1:8000/openapi.json \| jq -r '.paths \| keys[]'` | `/Users/concm/prod_workspace/Mineru2Tables` | 0 |
| `git rev-parse --abbrev-ref HEAD && git rev-parse --short HEAD && git log -1 --oneline` | Luceon workspace | 0 |
| `git rev-parse --abbrev-ref HEAD && git rev-parse --short HEAD && git log -1 --oneline` | `/Users/concm/prod_workspace/Mineru2Tables` | 0 |

## Skipped Checks

- No clone of `shcming2023/Mineru2Table2026`: task forbids cloning/installing/building unless later authorized.
- No build/test/install in Mineru2Table: task is read-only evidence review and forbids build/install.
- No service start/stop/restart: task forbids runtime mutation. The health/OpenAPI checks were run only because an already-running listener on port 8000 was discovered.
- No Luceon runtime, production, upload, pressure, submit-probe, retry, reparse, re-AI, cleanup, repair, or reset checks: explicitly outside task scope.
- No secret/config reads from `.env`: file names were observed but secret contents were not needed and were not reported.

## Non-Readiness Boundary

This report is architecture evidence only. It does not accept Mineru2Table as CleanService-ready, does not authorize Luceon real dispatch, does not authorize production/runtime wiring, and does not claim production acceptance, production readiness, release readiness, L3, pressure PASS, production上线, or go-live.

## Required Director Review

Director review is required.

Recommended Director action: accept this evidence-gap review, keep real Mineru2Table dispatch blocked, and dispatch external-service protocol implementation/evidence work before any Luceon real callback/polling/runtime wiring task.
