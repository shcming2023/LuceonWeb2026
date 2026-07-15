# LuceonWeb2026 runtime control plane closure

Date: 2026-07-15 (Asia/Shanghai)

## Decision

The runtime-control-plane change is production-candidate code. The current Mac mini remains a development deployment, not the formal production host. Its only intentional warning is `backup_disabled`: a same-machine directory is not accepted as proof of an external production backup.

Formal target-host deployment remains gated by a writable external volume, target `.env.production`, private runtime config/secrets, immutable image references, and the release preflight. The production template enables authenticated access, disables public raw downloads, and refuses startup preflight when the external backup volume is absent or not writable.

## Security boundary

- Authentication defaults to enabled (`LUCEON_AUTH_DISABLED=false`).
- Public raw-asset downloads default to disabled.
- Every runtime settings, status, probe, MinIO maintenance, and backup-job endpoint requires `runtime_admin`.
- Runtime and pipeline administrator capability is derived from the explicit email allowlist.
- Public `/settings` without a session redirects to `/login?redirect=/settings`; the settings menu is hidden.
- Authenticated administrator browser evidence: `/settings` rendered the runtime-admin navigation and all six tabs (`系统状态`, `目标环境`, `MinIO 资产`, `GPU 算力`, `模型配置`, `备份与告警`) without console warnings or errors.
- Live API evidence: unauthenticated `/api/runtime/settings` and `/api/materials/1/download_url` returned HTTP 401.
- Unit/API evidence covers unauthenticated HTTP 401 and ordinary-user HTTP 403 for settings and backup-job creation.

## Runtime contract

- Runtime config schema: `2`.
- Development identity: `development-mac-mini`; public app URL is explicit.
- MinIO internal endpoint and public browser endpoint are separate settings.
- Current contract contains nine buckets:
  - `eduassets-input`
  - `eduassets-mineru`
  - `eduassets-minerupopo`
  - `eduassets-raw`
  - `eduassets-clean`
  - `eduassets-standard`
  - `eduassets-parsed`
  - `eduassets-elegantbook`
  - `eduassets-review`
- Historical `eduassets-latex` is optional legacy backup scope, not a current production contract bucket.
- Live MinIO check: connected, 9/9 current buckets present.
- Runtime config mode: `0600`; dead SSH password/service-root, placeholder ASR/TTS/image-generation, fake cloud-provider, auxiliary-filter, and legacy last-backup fields are absent.
- A host:port parsing defect for `host.docker.internal:9000` was reproduced, regression-tested, fixed, rebuilt, and verified against live MinIO.

## Readiness semantics

- GPU is explicitly `on_demand`.
- With zero active GPU tasks, an unavailable GPU is `expected_off` and is not a blocker.
- With queued/running GPU work, Wrapper or staged MinerU/Popo API failure is a blocker.
- GPU probes run in parallel with bounded five-second requests.
- During the user-controlled GPU uptime window, Wrapper health and all four authenticated staged endpoint probes passed; no MinerU or Popo job was submitted.
- Live core dependencies after final deployment: SQLite, Redis, Workflow MySQL, material worker, Workflow V2 worker, backup worker, and Overleaf were 7/7 ready.
- The authenticated settings page showed schema v2, the explicit internal/public MinIO endpoints, all nine current buckets present, on-demand GPU with zero active tasks, the two real model providers only, server-controlled backup paths, and no backup-job false success.
- Saved model probes returned HTTP 200 for DeepSeek `deepseek-v4-flash` and DashScope `qwen3.7-plus`.
- Final local containers: running, OOM false, restart count zero.

## Backup redesign

- The API no longer performs synchronous copy work and the Web process no longer owns a scheduler thread.
- Backup jobs are immutable database records with queued/running/succeeded/failed states, idempotency, leases, heartbeats, retry lineage, frozen target/bucket scope, results, and acknowledgeable critical alerts.
- A dedicated backup worker owns scheduling and execution.
- `manifest` writes a complete inventory only and never claims that assets were copied.
- `copy` streams every object to each enabled server-controlled target, verifies the written size against the MinIO listing, and writes a v2 manifest.
- Missing current buckets, traversal-like object names, an object-limit truncation, or any partial target failure fail the job and record a critical alert; incomplete work cannot be marked succeeded.
- Scope includes all nine current buckets and optionally the historical `eduassets-latex` bucket.
- Paths are fixed by server-side roots; the settings payload cannot inject arbitrary filesystem paths.
- Development backup scheduling remains disabled intentionally. Production example uses full-copy mode, current + legacy scope, snapshot plus external target, and a 500,000-object safety gate.

## Migration and rollback evidence

- Pre-migration consistent SQLite backup: `runtime/backups/mineru-pre-runtime-control-20260715T183829.db`.
- Backup SHA-256: `e299307e019ae09ee3f4032d916964afa1cc281c5bede557c88150dfbeeb509a`.
- A cloned 1.5 GiB database completed upgrade, downgrade, and re-upgrade; every `PRAGMA integrity_check` returned `ok`.
- Development database revision: `20260715_runtime_control_plane`.
- `backup_jobs` exists; the database integrity check after migration returned `ok`.

## Build and regression evidence

- Backend: 609 tests passed.
- Frontend: `vue-tsc -b` and Vite production build passed.
- Compose rendering: local review compose passed `docker compose config --quiet` and includes backend, frontend, Redis, material worker, Workflow V2 worker, and backup worker.
- A no-cache arm64 backend/frontend build completed before the final source-layer rebuild.
- Final local image IDs:
  - backend/worker: `sha256:e8c0392f1ffad97710277fa43dfffd6cc9a4038ac7ea2e3ad1d22b756e18905e`
  - frontend: `sha256:72b9f84457a07ebe33c146faae89d640a8f72c3e750b2c35f69c333b75ec1294`
- Final containers use those exact images; all reported running, OOM false, restart count zero.
- Graphify was updated after code changes.

## Target Mac mini handoff gates

- Supply `.env.production` with mode `0600`.
- Set target identity/public URL, internal MinIO endpoint, public MinIO endpoint, admin allowlist, Workflow MySQL URL, and model/GPU secrets.
- Mount a genuinely external writable volume through `LUCEON_EXTERNAL_BACKUP_PATH`; preflight rejects a missing or non-writable path.
- Render immutable `repository@sha256` image references; do not build on the target.
- Run preflight, image load/pull, migration, start, and verify in order.
- Verify one Workflow V2 worker per Workflow database and confirm all containers have zero OOM/restarts.
- Create and complete one target-host backup job before declaring the external-copy policy operational.

## Residual issues

- Major: none in the implemented control-plane code.
- Operational gate: external production backup cannot be declared ready on this development Mac because no genuine external target volume is mounted/enabled.
- Minor: existing Python/SQLAlchemy `datetime.utcnow()` deprecation warnings remain; they predate this closure and do not affect the current acceptance result.
