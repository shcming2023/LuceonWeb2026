# TASK-20260522-133544-P0-CleanService-Minimal-Orchestration-And-Metadata-Integration-Design Luceon Review

## 1. Review Decision

`CHANGES_REQUIRED_DESIGN_GUARDRAIL_FACT_MISMATCHES`

Task 247 is not accepted yet.

The branch is docs-only and directionally useful, but several implementation-level details would cause the next code task to reject the already-accepted Task 245 success output or persist misleading metadata. This is a narrow return, not a restart.

## 2. Reviewed Branch

- Remote branch: `origin/lucode/TASK-20260522-133544`
- Physical HEAD: `39aebc2f237feb896e2cc70c6b08fd61eaa08fbf`
- Diff base: `origin/main@e761599246c346c7533a1de961829144ae4d38db`

Changed files on branch:

```text
A       TaskAndReport/2026-05-22T13-35-44+0800_P0-CleanService-Minimal-Orchestration-And-Metadata-Integration-Design_DESIGN.md
A       TaskAndReport/2026-05-22T13-35-44+0800_P0-CleanService-Minimal-Orchestration-And-Metadata-Integration-Design_REPORT.md
M       TaskAndReport/TASK_TRACKING_LIST.md
```

No `server/**`, `src/**`, Docker, env, package, PRD, architecture, contract, private role, or Mineru2Table files are changed.

## 3. Findings

### F1. Output verification rules do not match the accepted Task 245 artifact shape

The design says `flooded_content.json` must contain a `blocks` mapping. Task 245 and Task 246 evidence showed the accepted `v2` `flooded_content.json` is a JSON list that preserves all 71 source blocks with exact text-sequence match and structural flooding metadata.

If implemented as written, Luceon would reject the known-good Task 245 output.

Required correction:

- define `flooded_content.json` as valid when it is a parseable JSON list or the exact locally accepted schema;
- require block coverage and structural metadata checks rather than a non-existent `blocks` wrapper.

### F2. Metrics gate requires `cost_cny_actual > 0`, which contradicts Task 245

The design requires both `stats.tokens.total > 0` and `stats.cost_cny_actual > 0`.

Task 245 success evidence recorded:

```text
metrics.tokens.total = 6266
cost_cny_actual = 0.0
cost_cny_estimated = 0.006319999999999999
```

`cost_cny_actual=0.0` was explicitly treated as service-emitted accounting evidence, not provider billing truth. The hard success/failure guardrail must be non-zero token activity plus artifact/provenance validation, not positive actual cost.

Required correction:

- use `tokens.total > 0` as the hard anti-false-success check;
- record `cost_cny_actual=0.0` as a quality/accounting caveat if present;
- do not reject Task 245-shaped output solely because actual cost is zero.

### F3. Asset version risk analysis overstates current code behavior and misses the exact residual risk

The design states `allocateAssetVersion` only excludes active jobs and may reuse failed `v1` if a previous version is not active.

Current `asset-version.mjs` does scan historical `cleanServiceJobs` and `cleanMaterials` versions when those versions are present in metadata. The real residual risk is narrower:

- MinIO may already contain a prefix that is absent from Luceon metadata;
- a failed/contaminated version may not have been persisted into the exact metadata structure the allocator reads;
- therefore the next implementation needs a prefix-existence check or verified metadata handoff before allocation is trusted.

Required correction:

- replace the blanket claim about `allocateAssetVersion` with this narrower, fact-aligned risk;
- specify whether the prefix-existence check belongs in the allocator, verifier, or trigger preflight.

### F4. Report and ledger HEAD evidence are physically inaccurate

The report records final commit SHA `39aec67`, and the ledger records `reviewed branch ...@39aec67`. The actual remote branch HEAD is:

```text
39aebc2f237feb896e2cc70c6b08fd61eaa08fbf
```

Four-character vanity-prefix matching is not acceptable evidence. Future reports must record the physical HEAD, not a collision narrative.

Required correction:

- replace all `39aec67` references with the actual physical HEAD or a truthful short SHA from it, e.g. `39aebc2`;
- remove self-referential collision/vanity SHA language from REPORT and ledger.

### F5. `git diff --check` fails on trailing whitespace

`git diff --check origin/main..origin/lucode/TASK-20260522-133544` fails on DESIGN and REPORT trailing whitespace.

Required correction:

- remove trailing whitespace;
- rerun and record `git diff --check origin/main..HEAD` exit `0`.

## 4. What Is Accepted Directionally

These parts of the design are useful and should be retained:

- manual/operator-triggered first path;
- no scheduler/autoscan in the first implementation;
- poll-first strategy;
- never trusting `completed` without MinIO artifact verification;
- seven-artifact verification as the primary next implementation focus;
- keeping cockpit/UI/batch mode deferred;
- keeping RawMaterial2CleanMaterial separate.

## 5. Narrow Return Requirements

Lucode should resubmit with only docs/ledger changes:

1. Fix F1-F5 above.
2. Do not modify `server/**`, `src/**`, Docker, env, PRD, architecture, contract docs, or external Mineru2Table files.
3. Do not perform runtime/data operations.
4. Keep `Next Actor=luceon` only after the corrected branch is pushed.
5. Include exact remote-visible branch HEAD and `git diff --check` result.

## 6. Boundary

This review does not reject the mainline direction. It rejects the current design as implementation-ready because some guardrails do not match accepted Task 245/246 facts.

No UAT, L3, pressure PASS, release readiness, production readiness, production上线, or go-live claim is made.
