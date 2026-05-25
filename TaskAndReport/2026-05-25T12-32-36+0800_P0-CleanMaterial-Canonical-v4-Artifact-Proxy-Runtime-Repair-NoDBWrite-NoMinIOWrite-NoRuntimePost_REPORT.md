# TASK-20260525-123236 Luceon Report

Report time: 2026-05-25T12:32:36+0800

Decision:

```text
SUCCESS_PROXY_RUNTIME_REPAIRED_CLEAN_BUCKET_ARTIFACT_READS
```

## Root Cause

Task 278 originally classified the blocker as stale/missing clean ObjectRefs
because product proxy reads returned key-not-found.

Further diagnosis found the clean objects were present in the actual `cms-minio`
bucket:

```text
eduassets-clean/toc-rebuild/1842780526581841/v1/*
eduassets-clean/toc-rebuild/1842780526581841/v2/*
eduassets-clean/toc-rebuild/1842780526581841/v3/*
eduassets-clean/toc-rebuild/1842780526581841/v4/*
```

The running `cms-upload-server` image was stale. Its container-local
`server/upload-server.mjs` had:

```text
if (bucketParam === rawBucket || bucketParam === parsedBucket) return bucketParam;
```

and did not include current `main` support for:

```text
bucketParam === 'clean'
bucketParam === cleanBucket
```

Runtime logs confirmed proxy requests with `bucket=eduassets-clean` were still
resolved to `eduassets`:

```text
[upload-server] proxy-file: eduassets/toc-rebuild/1842780526581841/v4/readable_tree.md
```

So the actual problem was not missing MinIO objects. It was a stale upload-server
runtime image that did not honor the clean bucket query parameter.

## Repair Action

Luceon rebuilt and recreated only the upload-server service:

```text
docker compose build upload-server
docker compose up -d --no-deps upload-server
```

No DB service, MinIO service, frontend service, Docker volume, Docker network,
job store, source asset, model, env, secret, or sample file was mutated.

Post-recreate checks:

```text
cms-upload-server Up healthy
GET /__proxy/upload/health -> 200 {"ok":true,"service":"upload-server"}
```

Container-local code now includes:

```text
bucketParam === 'clean'
bucketParam === rawBucket || bucketParam === parsedBucket || bucketParam === cleanBucket
```

## Artifact Verification

After the repair, all seven canonical v4 clean artifact ObjectRefs are
retrievable through the product proxy and match recorded metadata size/SHA:

| Role | Status | Size | SHA256 |
| --- | ---: | ---: | --- |
| `flooded_content` | 200 | 20054 | `e1a8355a80a5014b5a616ed441a4d0851c47d6a3d6092711ce765ffe11eea7b7` |
| `logic_tree` | 200 | 375 | `b61ee669b63bccb597f9ff31e5773ac1cc53a7bf6d6ef7a5ba73d467c7267665` |
| `metrics` | 200 | 129 | `add72cb0a0c0dcb2fe051961795da8c151181022df79770583d5fb75c7ed9718` |
| `provenance` | 200 | 2066 | `394b87a89375e0f403df8660de304ab9541b3276d25ba7b424f8369e5b1234c5` |
| `readable_tree` | 200 | 106 | `bba5cf360fa7c0d92a9489ce84dfc40458de6072f812d7ab5d381b8e828946d7` |
| `skeleton` | 200 | 21160 | `c004915e79dde976f68cbb460ae3e6bf34e81be6b7cc8bdc28d5252d5ec15f9e` |
| `unresolved_anchors` | 200 | 2 | `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945` |

This resolves the specific blocker:

```text
DB says v4 clean artifacts exist, but product proxy cannot read them.
```

## RawMaterial2CleanMaterial Follow-Up Probe

After proxy repair, Luceon ran a read-only artifact-backed draft probe. Artifact
reads succeeded, but the draft did not complete because the current Task 276
algorithm skeleton does not support the real `logic_tree.json` object shape:

```text
DRAFT_BUILD_BLOCKED
INVALID_ARTIFACT_BODY
artifact body has no supported item array: logic_tree
```

This is a new downstream code-shape compatibility blocker, not the original
MinIO/proxy readability blocker.

## Boundary Confirmation

No DB POST/PATCH/PUT/DELETE/apply, MinIO put/copy/move/delete/write/delete-marker
or cleanup, runtime POST, submit-probe, Mineru2Table query/probe, raw2clean
service execution, broad Docker/Compose restart, volume/network/prune,
job-store edit, upload/retry/reparse/Re-AI/rollback, source asset mutation,
model/env/secret mutation, UAT, L3, pressure PASS, release readiness,
production readiness, production online, or go-live claim was performed or made.

## Next Mainline Step

Issue a narrow Lucode task:

```text
P0 RawMaterial2CleanMaterial Real-Artifact Shape Compatibility
MockSafe ReadOnly NoDBWrite NoMinIOWrite NoRuntimePost
```

The task should adapt the draft skeleton to accept the real canonical
`logic_tree.json`, `skeleton.json`, and `flooded_content.json` shapes without
inventing source truth and without expanding into final cleaning quality.

