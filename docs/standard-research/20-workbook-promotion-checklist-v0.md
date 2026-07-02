# Workbook Promotion Checklist V0 - 2026-06-30

Purpose:

```text
Prevent workbook Basic Print candidates from being accidentally promoted to accepted golden or profile-ready status without enough evidence.
```

This checklist applies to `grammar_workbook` / `exercise_workbook` Standard Basic Print research.

Current sample-specific hard stops are summarized in:

```text
docs/standard-research/30-promotion-hard-stop-matrix-v1.md
```

## Status Levels

### Candidate

A workbook run may be registered as a Basic Print candidate when it is useful as a positive comparator, but not yet authoritative.

Required:

- Standard acceptance status is `pass`;
- quality score is at least 90;
- workbook profile contract is `pass`;
- exercise relation contract is `pass`;
- image relation contract is `pass`;
- all review outcomes are closed;
- open blocking outcome count is `0`;
- unresolved blocking issue candidate count is `0`;
- source PDF evidence is available for visual-sensitive images, tables, and formulas;
- all corrections, if any, are recorded in `correction_log.json` with evidence;
- no sample-specific hardcoding by filename, title, material_id, page, or block id;
- candidate record exists under `corpus/golden/candidates/`;
- run manifest exists under `corpus/runs/`.

Candidate status does not mean:

- accepted golden;
- profile-ready;
- layout style is polished;
- source correction rules are generally approved.

### Accepted Golden

A workbook candidate may be promoted to accepted golden only by a separate promotion decision.

Additional requirements beyond candidate:

- promotion document exists and names the accepted closure rule;
- accepted scope is narrow and explicit;
- manual page spot check or equivalent visual review has no blocking findings;
- all non-`accepted_by_rule` outcomes have reviewer, date, notes, and evidence;
- any correction policy used by the candidate is already accepted or explicitly promoted with the sample;
- source annotation policy is resolved or explicitly declared out of scope;
- the sample adds meaningful coverage beyond existing accepted goldens;
- promotion status is written under `corpus/golden/accepted/`;
- README and corpus records are updated.

Hard stops:

- do not promote if any review gate remains `review`;
- do not promote if any correction lacks evidence;
- do not promote if pass depends on sample-specific code;
- do not promote if visual-sensitive structures were closed only by artifact existence without source comparison;
- do not promote if the only evidence is from one workbook family and the claim is broader than that family.

### Profile-Ready

A workbook profile may be called profile-ready only when the project has enough cross-sample evidence to use it as a general Standard compiler contract.

Required evidence:

- at least three accepted or candidate workbook samples;
- at least two different workbook families or publishers;
- at least one sample outside Grammar Friends;
- evidence across exercise grouping, fill blanks, options, tables, figures, helper icons, and correction policy;
- zero unresolved recurring hard blockers;
- known non-blocking caveats are documented as profile rules or explicit non-goals;
- profile rules are not hardcoded to filenames, material ids, headings, pages, or sample-specific block ids;
- failure handling is defined for source-crop gaps, OCR/table mismatches, and ambiguous corrections;
- math/diagram-heavy workbooks are not claimed unless math profile evidence exists.

Current status:

```text
grammar_workbook: profile-ready v0 from GF6/GF4/GIC, candidates not accepted golden
exercise_workbook: one non-Grammar-Friends review pressure run, not candidate-ready
math profile: separate research track, not covered by GF4/GF6
```

## Current Candidate Evaluation

### GF6

Status:

```text
candidate_only_not_promoted
```

Candidate evidence:

- acceptance `pass`;
- quality score `100`;
- 197 review outcomes closed;
- 213 issue candidates dispositioned;
- page spot check has zero blocking findings.

Promotion blockers:

- first positive workbook candidate;
- source annotation / handwritten marks remain a Clean/source-fidelity policy caveat;
- `accepted_by_rule` closures are deterministic evidence, not human visual final approval;
- no second workbook family evidence.

### GF4

Status:

```text
candidate_only_not_promoted
```

Candidate evidence:

- acceptance `pass`;
- quality score `100`;
- 133 review outcomes closed;
- grammar paradigm table rendering validated for three Review 5 failures;
- one source typo correction recorded in `correction_log.json` with source crop evidence.

Promotion blockers:

- same workbook series as GF6;
- source correction policy is newly defined;
- one outcome is manually accepted through correction policy, not `accepted_by_rule`;
- source correction policy needs more samples before broad approval.

## Promotion Review Questions

Before promoting a workbook candidate, answer:

1. What exact status is being promoted: candidate, accepted golden, or profile-ready?
2. What closure rule is being accepted?
3. Which artifacts prove the rule?
4. Which findings are deterministic `accepted_by_rule`, and which are manual `accepted`?
5. Are there corrections? If yes, does each have source crop evidence and a correction-log entry?
6. Are there page spot check notes? If yes, why are they non-blocking?
7. Does the claim generalize beyond one series? If not, how is the scope limited?
8. Is any code hardcoded to a sample?
9. What would cause the next sample to fail under the same rule?

## Required Promotion Artifacts

For accepted golden promotion:

```text
docs/standard-research/<promotion-doc>.md
docs/standard-research/corpus/runs/<run>.json
docs/standard-research/corpus/golden/candidates/<candidate>.json
docs/standard-research/corpus/golden/accepted/<golden>.json
standard_acceptance_report.json
standard_review_outcomes.json
visual_outcome_review.json
basic_print_closure_report.json
correction_log.json, if correction_count > 0
manual/page spot check artifact, if any outcome is manual accepted
```

For profile-ready declaration:

```text
profile readiness document
cross-sample comparison table
known caveats / non-goals
failure-mode handling rules
at least one non-Grammar-Friends workbook run
```

Current non-Grammar-Friends run:

```text
pdf-58860644b15e909c / (7)G7+.pdf
status: review_pressure_sample_not_candidate
profile: exercise_workbook
latest main quality: 94
```

This run helps expose cross-series failure modes, but it does not satisfy candidate or profile-ready evidence because acceptance remains `review` and open blockers are substantial.

## Conclusion

GF6, GF4, and GIC should remain Basic Print candidates, not accepted golden. The grammar_workbook profile is now profile-ready v0; the next promotion work should either promote one sample with a narrow accepted rule or continue the unresolved exercise_workbook/math tracks.
