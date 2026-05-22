# Task 247 Luceon Review v2

## Decision

`ACCEPTED_DESIGN_LEVEL_WITH_LUCEON_EVIDENCE_CORRECTION`

Task 247 is accepted as a docs/design-level artifact. It does not accept any
runtime implementation, database persistence, MinIO mutation, CleanService
worker activation, UAT, L3, pressure-pass, release readiness, or go-live state.

## Reviewed Evidence

- Remote branch: `origin/lucode/TASK-20260522-133544`
- Reviewed remote HEAD: `0619e7674d4e0c06eaf222ade47b9e67ef56722c`
- Diff scope against `origin/main` before Luceon acceptance correction:
  - `TaskAndReport/2026-05-22T13-35-44+0800_P0-CleanService-Minimal-Orchestration-And-Metadata-Integration-Design_DESIGN.md`
  - `TaskAndReport/2026-05-22T13-35-44+0800_P0-CleanService-Minimal-Orchestration-And-Metadata-Integration-Design_REPORT.md`
  - `TaskAndReport/TASK_TRACKING_LIST.md`
- `git diff --check origin/main..origin/lucode/TASK-20260522-133544`: exit 0.
- No `server/**`, `src/**`, Docker, environment, package, PRD, architecture,
  contract, private role, or external Mineru2Table runtime/source files were
  changed by the submitted branch.

## Accepted Corrections From Review v1

The narrow return resolved the review-blocking design facts:

1. `flooded_content.json` is now treated as a JSON array of source blocks, not
   as a `blocks` mapping. This aligns with the accepted Task 245/246 `v2`
   evidence.
2. `metrics.json` no longer requires `cost_cny_actual > 0`; the hard false
   success guard is `stats.tokens.total > 0` plus artifact/provenance checks.
3. The asset-version risk is narrowed to the real residual gap: a MinIO physical
   output prefix may exist even when the Luceon metadata allocator has no record
   of it. The proposed physical-prefix probe and version bump avoids reusing
   polluted prefixes.
4. The submitted DESIGN/REPORT files no longer fail trailing-whitespace checks.

## Luceon Acceptance Corrections

During acceptance, Luceon made two control-plane corrections:

1. Replaced the report's submitted intermediate short SHA `ecd0021` with the
   physical reviewed remote HEAD
   `0619e7674d4e0c06eaf222ade47b9e67ef56722c`.
2. Replaced future-facing `UAT` wording in the design with controlled
   development-verification wording, so this docs-level artifact cannot be read
   as UAT or release readiness evidence.

These corrections are report/design wording corrections only. No business code
or runtime/data state was changed.

## Residual Boundaries

The design is now good enough to guide the next critical-path implementation
task. The next task should stay mainline-first and begin with the verification
guardrail, not broad orchestration polish:

- fetch and validate the seven Mineru2Table output artifacts from MinIO;
- enforce parseable JSON, non-empty markdown, non-zero token metrics, and
  provenance input ObjectRef/hash checks;
- compensate or quarantine the known `input size_bytes=0` upstream provenance
  gap;
- keep the worker disabled by default and avoid real POST dispatch unless a
  later task explicitly authorizes it.

Deferred work remains: broad automation, dashboard polish, batch scheduling,
RawMaterial2CleanMaterial, and readiness/UAT claims.
