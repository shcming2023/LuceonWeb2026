# TASK-20260522-092145-P0-CleanService-Canonical-Raw-Material-Seed-NoPost REPORT

## 1. Scope

Task 240 seeded one canonical Raw Material object for the Director-authorized
candidate:

```text
materialId: 1842780526581841
title: 向树叶学习：人工光合作用
parseTaskId: task-1779085089451
assetVersion: v1
```

This is the Luceon evidence-corrected integration report. Lucode's local Dev
branch was:

```text
lucode/TASK-20260522-092145@a1caa1eea2c3a76208c86d410a525bd74590a38f
```

The branch was not visible through `git ls-remote` during Luceon review, and
the local report had mechanical evidence issues. Luceon independently verified
the host MinIO/runtime state before closing this task.

## 2. Director Authorization

The Director authorized exactly one controlled MinIO write for this task:

```text
eduassets-raw/mineru/1842780526581841/v1/content_list_v2.json
```

Still forbidden:

- `POST /api/v1/jobs`;
- LLM/API call;
- Luceon DB write;
- source code change;
- Docker mutation;
- cleanup or wider migration.

## 3. Source Evidence

Legacy MinerU ZIP:

```text
bucket: eduassets-parsed
object: parsed/1842780526581841/mineru-result.zip
size: 79737 bytes
sha256: 1530a1cfba2ae39068d21b7d8ee82e8af3ba6596da6400eed19a7d73b358d012
```

Copied ZIP entry:

```text
向树叶学习：人工光合作用/auto/向树叶学习：人工光合作用_content_list_v2.json
```

Extracted entry:

```text
size: 31543 bytes
sha256: f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db
top-level count: 4
block count: 71
block types:
  title: 1
  paragraph: 70
```

## 4. Canonical Raw Material Object

The canonical Raw Material bucket now exists:

```text
eduassets-raw
```

Uploaded object:

```text
bucket: eduassets-raw
object: mineru/1842780526581841/v1/content_list_v2.json
stat size: 31543 bytes
readback size: 31543 bytes
sha256: f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db
matches ZIP entry: true
```

At review time, `eduassets-raw` contained only:

```text
mineru/1842780526581841/v1/content_list_v2.json
```

## 5. Negative Checks

No `eduassets-clean` output exists for the target prefix. In fact, the
`eduassets-clean` bucket is still absent in the reviewed host state.

Mineru2Table job store remains unchanged:

```text
path: /Users/concm/prod_workspace/Mineru2Tables/data/jobs.json
size: 718 bytes
sha256: 29d5621bcca3d626b8f27289caabd13ba6cd835913a76b9e2cbd8fd8d4577413
key count: 1
```

Read-only log scan after the Task 240 authorization window found no new
`/api/v1/jobs` POST evidence in `mineru2table-api` logs.

## 6. Safety Assertions

- Any `POST /api/v1/jobs` sent: `no`
- Any LLM/API call accepted: `no`
- Any Luceon DB write accepted: `no`
- Any business source code change: `no`
- Any Docker service/image/network/volume mutation accepted: `no`
- Any write to `eduassets-clean`: `no`
- Any legacy object delete/rename/overwrite accepted: `no`
- Any cleanup or wider migration accepted: `no`
- UAT/L3/readiness/pressure PASS/go-live claim: `no`

## 7. Final Classification

```text
CANONICAL_RAW_MATERIAL_SEEDED_NO_POST
```
