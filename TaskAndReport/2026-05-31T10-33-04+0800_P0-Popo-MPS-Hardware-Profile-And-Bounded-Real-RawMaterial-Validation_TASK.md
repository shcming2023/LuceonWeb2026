# P0 Popo MPS Hardware Profile And Bounded Real RawMaterial Validation

Task ID: `TASK-20260531-103304-P0-Popo-MPS-Hardware-Profile-And-Bounded-Real-RawMaterial-Validation`

Issued at: `2026-05-31T10:33:04+0800`

Issued by: Luceon

Execution owner: Luceon

## Objective

Make MinerU-Popo usable on the actual production hardware profile:

```text
Home Mac mini
Apple MPS
host-mps worker
real MinerU Raw Material
```

This is not a hardware escape task. Do not switch the mainline proof to a different GPU/backend. The current production reality is MPS, so Popo invocation must be bounded to that hardware.

## Scope

Implement and validate a Luceon deployment profile for MPS:

```text
POPO_MPS_CHUNK_SIZE
POPO_MPS_RENDER_SCALE
POPO_MPS_MIN_PIXELS
POPO_MPS_MAX_PIXELS
POPO_MAX_NEW_TOKENS
```

The goal is normal input/output under bounded hardware constraints:

```text
MinerU Raw Material -> Popo -> rebuilt_markdown.md
```

## Constraints

Do not:

- modify source PDF or extracted image hash names;
- delete, migrate, or clean DB/MinIO data;
- claim Popo upstream is broken;
- redesign MinerU-Popo core algorithms;
- switch away from MPS as the production validation target;
- run pressure/release/L3/go-live validation.

Allowed:

- add deployment/profile parameters;
- bound visual processor pixels;
- bound dynamic chunk page span;
- lower render scale if needed;
- keep changes local to Luceon overlay / deployment profile;
- document quality/residual risk honestly.

## Acceptance

Positive pass requires:

1. MPS profile parameters are visible in runtime health/config.
2. Known small sample still produces readable `rebuilt_markdown.md`.
3. Workbook-class real sample `task-1779854322261` no longer fails with MPS buffer explosion and produces readable `rebuilt_markdown.md`, or produces a faster explicit MPS-bounded blocker with exact parameter evidence.
4. Output artifacts preserve source asset hash names.
5. Report states whether the MPS profile is sufficient for current phase or still blocked.

## Required Report

Create:

```text
TaskAndReport/2026-05-31T10-33-04+0800_P0-Popo-MPS-Hardware-Profile-And-Bounded-Real-RawMaterial-Validation_REPORT.md
```

Result wording must be one of:

```text
PASS_MPS_BOUNDED_POPO_REAL_RAWMATERIAL_VALIDATED
BLOCKED_<specific_mps_profile_blocker>
```
