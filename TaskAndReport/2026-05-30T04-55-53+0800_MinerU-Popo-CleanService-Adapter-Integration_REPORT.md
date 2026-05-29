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

Additional deployment validation completed after model download:

```text
Hugging Face model snapshot downloaded to:
/Users/concm/prod_workspace/MineruPopo/models/MinerU-Popo

Model directory size:
17G

Container start:
POPO_PORT=18082 POPO_MODEL_PATH=/app/models/MinerU-Popo docker compose -f docker-compose.yml -f docker-compose.popo.yml up -d --no-deps --force-recreate mineru-popo

Health:
curl http://127.0.0.1:18082/health
```

Observed health response:

```text
{"ok":true,"service":"toc-rebuild","engine":"mineru-popo","version":"mineru-popo-adapter.v0.1","protocol_version":"v1","model_configured":true,"job_dir":"/app/runtime/jobs"}
```

Runtime dependency import check inside `mineru-popo` passed for:

```text
fastapi
boto3
tqdm
fitz
PIL
bs4
transformers
torch
torchvision
qwen_vl_utils
AutoProcessor
Qwen3VLForConditionalGeneration
```

Container status:

```text
mineru-popo   Up (healthy)   127.0.0.1:18082->8000/tcp
```

Additional integration wiring completed:

```text
server/lib/task-actions-routes.mjs
```

The task-detail `POST /tasks/:id/toc-rebuild` route now switches behavior by
`CLEANSERVICE_ENABLED`:

- `false`: preserve the previous local/manual Markdown-based toc-rebuild path;
- `true`: submit a CleanService Protocol v1 job to `CLEANSERVICE_ENDPOINT`.

For the current Luceon MinerU output shape, the enabled route sends
`inputs[]` role `mineru-result-zip` pointing at the existing
`eduassets-parsed:parsed/{materialId}/mineru-result.zip`. The MinerU-Popo
adapter extracts `*_content_list_v2.json` and `*_origin.pdf` from that zip,
runs Popo, verifies the returned seven required artifacts through MinIO, and
applies only the CleanService metadata summary to the task/material records.

Runtime deployment completed:

```text
cms-upload-server:
  CLEANSERVICE_ENABLED=true
  CLEANSERVICE_ENDPOINT=http://mineru-popo:8000

mineru-popo:
  model_configured=true
  127.0.0.1:18082->8000/tcp
```

Verified from inside `cms-upload-server`:

```text
wget -qO- http://mineru-popo:8000/health
```

Observed:

```json
{"ok":true,"service":"toc-rebuild","engine":"mineru-popo","version":"mineru-popo-adapter.v0.1","protocol_version":"v1","model_configured":true}
```

## Boundary

No CleanService real sample job, pressure/UAT/readiness/go-live claim, or
manual sample metadata apply was performed during validation.

The Popo adapter container was built and started on `127.0.0.1:18082`, and the
main Luceon upload worker was reconfigured to use it as the active CleanService
endpoint. A future operator click on an eligible task's `目录重建` action will
perform the real CleanService job and metadata apply.

## Next Required Step

Run one explicitly authorized single-sample CleanService job through the
task-detail `目录重建` button:

```text
CLEANSERVICE_ENABLED=true
CLEANSERVICE_ENDPOINT=http://mineru-popo:8000
```

The job should use one existing task/material sample, mutate only the configured
CleanService output bucket, and then verify that Luceon can surface
`rebuilt_markdown.md` as the primary operator-facing artifact.
