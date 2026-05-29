# CleanService MinerU-Popo Adapter

Status: optional integration candidate, not enabled by default.

Local service workspace:

```text
/Users/concm/prod_workspace/MineruPopo
```

## Purpose

MinerU-Popo is a candidate replacement engine for Luceon's current
`toc-rebuild` structure reconstruction stage.

The intended pipeline becomes:

```text
PDF -> MinerU -> MinerU-Popo -> rebuilt_markdown.md -> operator review
```

Luceon keeps the existing CleanService `serviceName=toc-rebuild` contract so
current task/material metadata, artifact verification, and UI lookup remain
compatible.

## Runtime Contract

Endpoint:

```text
GET  /health
POST /api/v1/jobs
GET  /api/v1/jobs/{job_id}
```

Luceon request shape remains CleanService Protocol v1:

- primary input: `inputs[]` role `mineru-content`, pointing to
  `eduassets-raw:mineru/{materialId}/vN/content_list_v2.json`;
- optional input: `inputs[]` role `source-pdf`;
- sink: `eduassets-clean:toc-rebuild/{materialId}/vN/`.

The adapter may discover the source PDF from:

```text
eduassets:originals/{materialId}/*.pdf
```

when `source-pdf` is not supplied.

## Output Contract

Required artifacts:

```text
flooded_content.json
logic_tree.json
readable_tree.md
skeleton.json
unresolved_anchors.json
metrics.json
provenance.json
```

Additional primary product artifact:

```text
rebuilt_markdown.md
```

`rebuilt_markdown.md` is the operator-facing primary artifact. The other files
remain technical evidence.

## Configuration

Optional compose overlay:

```bash
docker compose -f docker-compose.yml -f docker-compose.popo.yml up -d --build mineru-popo
```

Luceon CleanService settings:

```text
CLEANSERVICE_ENABLED=true
CLEANSERVICE_ENDPOINT=http://mineru-popo:8000
CLEANSERVICE_STORAGE_ENDPOINT=minio:9000
POPO_MODEL_PATH=/app/models/MinerU-Popo
```

For host-side smoke without enabling Luceon:

```bash
curl http://127.0.0.1:18080/health
```

## Safety Boundary

- The adapter must fail explicitly when `POPO_MODEL_PATH` is missing.
- The adapter must not produce successful CleanService metadata without
  `provenance.json`.
- The adapter does not mutate Luceon DB records. Luceon still owns metadata
  apply after output verification.
- This document is not a readiness or go-live claim.

