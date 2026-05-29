# MinerU-Popo CleanService Adapter Integration Report

Time: `2026-05-30T04-55-53+0800`

Scope: local adapter deployment path and Luceon integration wiring.

## Result

Created a local MinerU-Popo service workspace:

```text
/Users/concm/prod_workspace/MineruPopo
```

The workspace now contains a Luceon CleanService Protocol v1 adapter that exposes:

```text
GET  /health
POST /api/v1/jobs
GET  /api/v1/jobs/{job_id}
```

The Luceon repo now contains an optional compose overlay:

```text
docker-compose.popo.yml
```

and an integration contract note:

```text
docs/contracts/CleanService-MineruPopo-Adapter.md
```

## Adapter Contract

The adapter keeps Luceon's existing `serviceName=toc-rebuild` contract while
using MinerU-Popo as the reconstruction engine.

Input:

- `inputs[]` role `mineru-content`, pointing to `content_list_v2.json`;
- optional `inputs[]` role `source-pdf`;
- otherwise the adapter attempts to discover `eduassets:originals/{materialId}/*.pdf`.

Output:

- `flooded_content.json`;
- `logic_tree.json`;
- `readable_tree.md`;
- `skeleton.json`;
- `unresolved_anchors.json`;
- `metrics.json`;
- `provenance.json`;
- `rebuilt_markdown.md`.

`rebuilt_markdown.md` is the primary operator-facing artifact. The other files
remain technical evidence.

## Validation

Completed:

```text
python3 -m py_compile luceon_service/app.py luceon_service/service.py
git diff --check
MINIO_ACCESS_KEY=dummy MINIO_SECRET_KEY=dummy docker compose -f docker-compose.yml -f docker-compose.popo.yml config --quiet
curl http://127.0.0.1:18080/health
curl -X POST http://127.0.0.1:18080/api/v1/jobs ...
curl http://127.0.0.1:18080/api/v1/jobs/luceon-smoke-missing-model
```

Observed health response:

```json
{"ok":true,"service":"toc-rebuild","engine":"mineru-popo","version":"mineru-popo-adapter.v0.1","protocol_version":"v1","model_configured":false}
```

Observed no-model job response:

```json
{"status":"failed","error":{"code":"popo-model-not-configured","message":"POPO_MODEL_PATH must point to downloaded MinerU-Popo model weights"}}
```

This proves the adapter fails explicitly when the model is absent instead of
pretending to produce clean output.

## Not Completed Yet

Docker image build was attempted with:

```text
docker compose -f docker-compose.yml -f docker-compose.popo.yml build mineru-popo
```

It stalled while loading metadata for `python:3.10-slim`, so the build process
was terminated. No service was deployed, restarted, or connected to the live
Luceon worker.

Real MinerU-Popo inference is still pending because model weights have not been
downloaded/configured:

```text
POPO_MODEL_PATH=/app/models/MinerU-Popo
```

## Boundary

No Luceon DB write, MinIO mutation, CleanService runtime job, production deploy,
service restart, pressure/UAT/readiness/go-live claim, or metadata apply was
performed.

## Next Required Step

Download or mount MinerU-Popo model weights under:

```text
/Users/concm/prod_workspace/MineruPopo/models/MinerU-Popo
```

Then run a single controlled CleanService job against one existing sample with
`CLEANSERVICE_ENABLED=true` and `CLEANSERVICE_ENDPOINT=http://mineru-popo:8000`.

