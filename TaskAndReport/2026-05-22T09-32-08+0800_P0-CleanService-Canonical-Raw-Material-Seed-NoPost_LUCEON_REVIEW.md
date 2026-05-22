# TASK-20260522-092145-P0-CleanService-Canonical-Raw-Material-Seed-NoPost LUCEON REVIEW

## Decision

`ACCEPTED_DATA_SEED_LEVEL_WITH_LUCEON_EVIDENCE_CORRECTION`

Task 240 is accepted at the canonical Raw Material seed level.

Acceptance means only that one selected existing MinerU result has been copied
into canonical Raw Material object storage for a future one-shot Mineru2Table
dispatch.

Acceptance does not mean Mineru2Table dispatch has happened, CleanService is
active, Raw Material migration/backfill is complete, Luceon DB metadata
references the new object, Clean Material artifacts exist, UAT/L3/pressure
PASS/release readiness/production readiness/go-live.

## Review Inputs

Luceon reviewed:

- local Dev branch:
  `lucode/TASK-20260522-092145@a1caa1eea2c3a76208c86d410a525bd74590a38f`;
- host MinIO state through `cms-upload-server`;
- Mineru2Table job store at
  `/Users/concm/prod_workspace/Mineru2Tables/data/jobs.json`;
- current Luceon `main` baseline:
  `43c53fcd80c896284759c3d56514afaa8a243dd7`.

The reported branch was not visible through `git ls-remote`, and the submitted
local report/ledger had mechanical evidence errors. Because the actual
authorized MinIO seed was correct and bounded, Luceon corrected the
control-plane evidence during integration instead of returning the task.

## Corrections Applied By Luceon

- Corrected the implementation reference to the local Dev branch HEAD
  `a1caa1eea2c3a76208c86d410a525bd74590a38f`.
- Replaced the local report's failed whitespace state with a clean integration
  report.
- Corrected the legacy ZIP SHA256 to
  `1530a1cfba2ae39068d21b7d8ee82e8af3ba6596da6400eed19a7d73b358d012`.
- Preserved the submitted canonical entry SHA256:
  `f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db`.

## Data Findings

Canonical bucket state:

```text
bucket: eduassets-raw
object: mineru/1842780526581841/v1/content_list_v2.json
```

The uploaded object matches the source ZIP entry byte-for-byte:

```text
size: 31543 bytes
sha256: f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db
matches ZIP entry: true
```

Parsed structure:

```text
top-level count: 4
block count: 71
title: 1
paragraph: 70
```

Negative checks:

```text
eduassets-clean target output: absent
jobs.json size: 718 bytes
jobs.json sha256: 29d5621bcca3d626b8f27289caabd13ba6cd835913a76b9e2cbd8fd8d4577413
jobs.json key count: 1
```

Luceon also performed a read-only log scan after the Task 240 authorization
window and found no new `/api/v1/jobs` POST evidence in `mineru2table-api`
logs.

## Boundary

No CleanService dispatch POST, LLM/API call, Luceon DB write, source code
change, Docker service/image/network/volume mutation, write to
`eduassets-clean`, legacy object delete/rename/overwrite, cleanup, wider
migration, UAT/L3/readiness/pressure PASS/go-live claim is accepted by this
review.
