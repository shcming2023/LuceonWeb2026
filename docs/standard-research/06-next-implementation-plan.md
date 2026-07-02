# Next Implementation Plan

## Status Update 2026-06-29

Phases 1-3 have reached their first closure target through RE1 review outcome V0:

- review outcome schema and closure artifacts were added;
- source PDF crops were generated as asynchronous review artifacts;
- RE1's 15 table visual review packets were closed by the accepted rule;
- RE1 was promoted to the first official Basic Print golden.

The next active implementation target is Phase 4: use GF6 as the workbook negative regression case and harden `grammar_workbook` / `exercise_workbook` around exercise grouping, blanks, options/tables, and image-text relations.

## Goal

Turn the Standard research track into a verified implementation path, starting with one narrow `basic_print` closure case.

Recommended first target:

```text
Reading Explorer 1 audit MVP
runtime/backend/pipeline-work/audits/re1-clean-master-20260627/standard-final-mvp/
```

Reason at planning time:

- it was the closest candidate;
- score is high;
- source PDF is available;
- issue candidate count is zero;
- remaining blockers are concrete and limited compared with workbook and math cases.

## Phase 1: Gate Hardening

Add gates before broad profile work.

Required checks:

- PDF page count must be non-null.
- Visible machine artifacts must be detected:
  - escaped table tags;
  - HTML comments;
  - source-empty audit comments;
  - prompt/debug artifacts.
- Source PDF availability must be reported before visual review packets are built.
- Unclosed visual review packets must block `basic_print`.
- `standard_done` must not imply `basic_print`.

Expected output:

- updated acceptance report schema or fields;
- tests for markup/comment leakage;
- tests for PDF page count reporting;
- tests for source PDF evidence availability.

## Phase 2: Source Evidence Plumbing

Make source PDF evidence available to Standard runs.

Current problem:

- Clean-to-Standard materialization downloads Clean and Raw prefixes.
- It does not pass source PDF into the Standard script before visual review packets are generated.
- Manifest enrichment adds source metadata after script execution, too late for packet generation.

Expected fix direction:

- materialize source PDF from `eduassets-input` or an archived source object into the Standard work directory;
- pass it to `standard_from_clean.py`;
- record source PDF path/ref in Standard manifest and visual review packets.

## Phase 3: RE1 Basic Print Closure

Use the RE1 audit MVP as the closure case.

Acceptance target:

- no visible leak hits;
- PDF page count readable;
- source PDF available;
- visual review packets closed or explicitly classified non-blocking with evidence;
- tables render as native tables, not leaked markup;
- two-column reading layout remains print-stable;
- package reaches `basic_print`, not merely `review`.

## Phase 4: Workbook Profile V0

Use Grammar Friends 6 after RE1 closure.

Implement minimal workbook profile:

- instruction;
- question group;
- fill blank;
- choice group;
- table question;
- matching two-column;
- figure tied to question/instruction;
- answer area.

Acceptance target:

- zero visible machine artifact leakage;
- source PDF available;
- non-null PDF page count;
- question groups detected above a profile-defined minimum;
- unresolved profile-critical blocks prevent `basic_print`.

## Phase 5: Math Profile Scoping

Use `中学生世界 八上 数学 上册.pdf` only after gate hardening and RE1/workbook lessons.

Initial target should be `review`, not `basic_print`.

Focus:

- formula evidence packets;
- table/formula crop workflow;
- diagram relation;
- worked example and practice set detection.

## Phase 6: Corpus Formalization

After at least one case reaches `basic_print`, add machine-readable corpus manifests:

- case manifests;
- run manifests;
- golden manifests;
- regression command expectations.

Do not create golden entries before a run passes the target quality level.

## Near-Term Checklist

1. Keep this research documentation under review.
2. Add a short `README.md` for `docs/standard-research/` if the directory grows.
3. Implement gate hardening in the Standard script.
4. Create tests from the current failure modes.
5. Re-run RE1 audit MVP or an equivalent controlled RE1 Standard run.
6. Promote only verified `basic_print` output to golden corpus.
