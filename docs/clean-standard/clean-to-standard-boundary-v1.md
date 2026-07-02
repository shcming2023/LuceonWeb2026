# Clean To Standard Boundary V1

Purpose:

```text
Make the stage boundary explicit after introducing Luceon Clean Standard Document v1.
```

## Boundary Summary

Clean produces a canonical semantic/evidence document.

Standard compiles that document into Basic Print artifacts and review outcomes.

Neither stage should take over the other stage's job.

## Clean Responsibilities

Clean must:

- preserve source-faithful text and reading order;
- remove extraction noise and prompt artifacts;
- emit `clean.md` for human review;
- emit `clean_standard.json` for compiler consumption;
- classify blocks into the finite v1 vocabulary;
- create outline paths;
- create relation edges for instructional structure;
- record asset roles;
- preserve source refs when Raw/PDF evidence is available;
- record uncertainty as `review_flags`;
- record hard blockers as `blockers`;
- produce `clean_contract_report.json`.

Clean may:

- mark profile candidates with evidence;
- mark decorative/helper media decisions;
- mark Clean review risks that Standard might scope later.

Clean must not:

- decide Basic Print Candidate or Accepted status;
- close Standard visual review outcomes;
- hide uncertain relations by forcing a confident relation;
- invent content to satisfy a profile;
- encode sample names, filenames, page numbers, or material ids into schema behavior.

## Standard Responsibilities

Standard must:

- consume `clean_standard.json` as the primary contract;
- use `clean.md` as readable/renderable text evidence, not as the only structure source;
- compile `standard.md`, `standard.html`, and `standard.pdf`;
- preserve outline and source fidelity;
- apply profile contracts;
- generate review outcomes for unresolved visual/relation/source evidence issues;
- generate product status such as `profile_certified_output`, `standard_review_draft`, or `blocked_needs_reconstruction`;
- keep source evidence and review packets auditable;
- write corpus/golden regression evidence.

Standard may:

- generate source crops;
- backfill source evidence from Raw/PDF under conservative rules;
- apply deterministic closure rules when evidence satisfies the profile contract.

Standard must not:

- mutate Clean acceptance history;
- promote a sample to candidate or accepted without corpus/golden records;
- treat source crop existence as visual acceptance;
- broaden `exercise_workbook` to absorb math-heavy relation families;
- lower thresholds to make reports green.

## Contract Failure Behavior

| Clean Standard condition | Standard behavior |
| --- | --- |
| `contract.status = pass` | compile with applicable profile contract |
| `contract.status = review` | compile conservative Standard Review Draft if hard gates are intact |
| `contract.status = fail` | stop before Basic Print compilation |
| missing `clean_standard.json` | legacy fallback allowed only as Review Draft during migration |
| missing source refs for visual-sensitive blocks | emit review outcomes, do not close by rule |
| unresolved relation blockers | emit blocked/review product status |

## Migration From Current State

Current Standard code still infers much of the structure from `clean.md`.

The migration should be staged:

1. Define v1 contract and schema.
2. Add a Clean-side exporter that emits `clean_standard.json` beside existing Clean artifacts.
3. Add a validator that writes `clean_contract_report.json`.
4. Teach Standard to prefer `clean_standard.json`.
5. Keep Markdown inference only as a legacy fallback that yields `standard_review_draft`.
6. Move existing research rules into profile contracts and validators.

## Acceptance For The Boundary

The boundary is satisfied when:

- RE1 can compile from Clean Standard into the existing accepted reading path;
- GF6/GF4/GIC can compile into candidate/profile-ready grammar workbook evidence;
- G7+ remains review pressure with explicit exercise/math-heavy blockers;
- Math 8A remains blocked/review with explicit formula/source evidence blockers;
- no stage has to infer status from filenames or sample ids.
