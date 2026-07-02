# Current State Audit

Audit date: 2026-06-29

## Update 2026-06-29

This audit is the pre-closure baseline for the Standard Basic Print research track. It remains useful as evidence of the initial failure state, but its `0` Basic Print count has been superseded.

Current accepted state:

- verified `basic_print` samples: `1`
- first official Basic Print golden: RE1 review outcome V0
- golden manifest: `corpus/golden/accepted/pdf-e71fe159994b50f3.re1-review-outcome-v0-20260629.golden.json`
- promotion record: `12-re1-basic-print-promotion.md`

## Pre-Closure Summary

At the time of this audit, there were no verified `basic_print` Standard samples in this project.

The then-current Standard outputs proved that the node could emit artifacts, but they did not prove that the outputs were printable textbook editions. The live evidence showed all known Standard acceptance reports were `review`, not `pass`.

## Evidence Sources

Commands used from `/Users/concm/prod_workspace/luceonWeb2026`:

```bash
find runtime -path '*/standard_acceptance_report.json' -print | sort | wc -l
find runtime -path '*/standard_acceptance_report.json' -print0 | xargs -0 jq -r '.status' | sort | uniq -c
sqlite3 -header -column runtime/backend/mineru.db \
  "select material_id, title, count(*) as rows, min(standard_quality_score) as min_score, max(standard_quality_score) as max_score
   from materials
   where standard_manifest_object is not null and standard_manifest_object <> ''
   group by material_id, title
   order by material_id;"
```

Observed output:

```text
standard_acceptance_report.json files: 9
statuses: 9 review

pdf-aadfa33fb0485c1a  中学生世界 八上 数学 上册.pdf                                     rows=2  score=84
pdf-e71fe159994b50f3  Reading Explorer 1 Students Book.pdf                              rows=2  score=86
pdf-ff4c7f59964ad54f  Grammar Friends 6 (Students Book) (Flannigan E.) (Z-Library).pdf  rows=2  score=85
```

## Audited Material Set

| Material | Material ID | Current Role | Current Status |
| --- | --- | --- | --- |
| Reading Explorer 1 Students Book.pdf | `pdf-e71fe159994b50f3` | reading textbook candidate | review at audit time; later promoted in review outcome V0 |
| Grammar Friends 6 (Students Book) (Flannigan E.) (Z-Library).pdf | `pdf-ff4c7f59964ad54f` | workbook / grammar exercises counterexample | review |
| 中学生世界 八上 数学 上册.pdf | `pdf-aadfa33fb0485c1a` | math / formula-heavy counterexample | review |

## Known Run Classes

### Published Clean-to-Standard Runs

The published DB-facing Standard runs are under:

```text
runtime/backend/pipeline-work/clean2standard/*/standard-final/
```

These runs are useful as failure and regression evidence. They are not golden samples.

Observed common blockers:

- `standard_acceptance_report.json` is `review`.
- `print_qa_report.json` often has `pdf_page_count: null`.
- `standard_visual_review_packets.json` has `source_pdf_available: false` in the published runs.
- HTML/print output can leak raw markup or audit comments.
- Complex tables and formulas are not source-verified.

### RE1 Audit MVP

Path:

```text
runtime/backend/pipeline-work/audits/re1-clean-master-20260627/standard-final-mvp/
```

At audit time, this was the closest candidate:

- score: `97`
- status: `review`
- PDF page count: `141`
- source PDF available: `true`
- issue candidates: `0`
- visual review packets: `15`

At audit time, it was not `basic_print` because it had unresolved visual review packets and visible leak hits. RE1 review outcome V0 later closed those packets and was promoted as the first Basic Print golden.

## Failure Taxonomy

Current Standard failures group into five classes.

### 1. Artifact Success Mistaken For Quality

Chrome can generate a PDF while the visible content is not acceptable. `pdf_ok=true` is necessary but insufficient.

Examples:

- `standard.pdf` exists but `pdf_page_count` is `null`.
- PDF renders while escaped table row tags appear in the visible page.

### 2. Source Evidence Missing

Standard needs the original PDF or page crops to verify tables, formulas, images, and layout-sensitive relations.

Published clean-to-standard runs currently do not make source PDF evidence available to the Standard script, so review packets cannot be closed.

### 3. Markup And Audit Leakage

Visible output must not contain implementation artifacts.

Examples:

- escaped HTML table rows such as `&lt;tr&gt;&lt;td&gt;...`;
- source-empty audit comments such as `<!-- source_empty_chunk ... -->`.

### 4. Profile Gap

General line-by-line block classification is not enough for workbooks or formula-heavy materials.

Observed gaps:

- question groups not recovered;
- options and answer areas not represented as child structures;
- matching, table questions, and fill-blank exercises need profile-aware layout intent.

### 5. Visual-Semantic Layout Gap

Basic print usability depends on layout when layout carries meaning.

Examples:

- images must remain with the relevant explanation, caption, or question;
- option lists may need inline, grid, or multi-line layout depending on length;
- matching questions require left/right columns;
- formulas and tables need evidence-backed reconstruction or explicit review.

## Pre-Closure Count

```text
pre-closure basic_print compliant samples: 0
pre-closure pass samples by acceptance reports: 0
pre-closure review Standard reports: 9
pre-closure published Standard materials, deduplicated: 3
closest candidate at audit time: Reading Explorer 1 audit MVP, still review
```

## Audit Conclusion

At audit time, the observed outputs should be classified as Standard attempts, not accepted Standard samples.

The next phase created a research corpus from source cases and run records, then drove RE1 review outcome V0 to `basic_print` under explicit gates. GF6 remains the workbook negative regression target.
