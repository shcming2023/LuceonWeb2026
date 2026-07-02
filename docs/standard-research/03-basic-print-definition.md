# Basic Print Definition

## Definition

`basic_print` is the lowest Standard quality level that can be printed and used as a textbook without consulting the original PDF for normal reading, teaching, and exercises.

It is not a decorative edition, not a source PDF replica, and not a polished publication. It is a neutral printable edition where source content and learning context remain intact.

## Core Standard

A `basic_print` package must be:

- source faithful;
- structurally aligned to Clean and Raw;
- complete enough for student and teacher use;
- evidence-backed when repairs or visual decisions are made;
- semantically laid out so learning tasks remain understandable;
- printable as stable HTML/PDF.

## Hard Gates

Any failure below prevents `basic_print`.

### Output Completeness

Required files must exist:

- `standard.md`
- `standard.html`
- `standard.pdf`
- `images/`
- `manifest.json`
- `standard_document.json`
- `correction_log.json`
- `standard_issue_candidates.json`
- `layout_report.json`
- `print_qa_report.json`
- `standard_acceptance_report.json`
- `standard_quality_score.json`
- `standard_visual_review_packets.json`
- `review.html`

### PDF Render Quality

`print_qa_report.json` must show:

- `pdf_ok=true`;
- non-zero `pdf_bytes`;
- readable non-null `pdf_page_count`;
- no severe blank-page, clipping, or unreadable-render evidence.

### No Machine Artifact Leakage

Visible HTML/PDF must not contain:

- escaped HTML table or row tags;
- raw XML/JSON fragments;
- Markdown or HTML comments used for audit;
- prompt artifacts;
- internal debug markers;
- unresolved placeholders.

### Source Fidelity

The package must not add, delete, rewrite, summarize, or invent content except through explicit evidence-backed corrections recorded in `correction_log.json`.

### Evidence Availability

The Standard run must have access to:

- Clean manifest and Clean source lines;
- Raw manifest and source evidence;
- source PDF reference or local source PDF;
- image semantics or equivalent media evidence;
- page candidates or review packets for visual-sensitive structures.

If source PDF evidence is unavailable for a case that has tables, formulas, diagrams, or layout-sensitive images, the output must stay `review`.

### Media Integrity

Referenced images must exist. Educational media must not be dropped without evidence.

Low-quality educational images require one of:

- retained with review note;
- replaced/repaired from source evidence;
- explicitly marked `needs_review`.

They must not be silently removed for visual neatness.

### Semantic Context Integrity

The StandardDocument must preserve learning relations:

- heading and section hierarchy;
- instruction and question group;
- question stem and options;
- answer area and fill blanks;
- figure and caption;
- image and related explanation/question;
- table and its surrounding instruction;
- formula and its explanatory text;
- matching left/right columns;
- reading passage and associated comprehension tasks.

### Profile-Critical Coverage

For the selected profile, required structures must be detected or explicitly marked `needs_review`.

Examples:

- workbook: instruction, question group, question, option, answer blank, matching, table question, answer area;
- reading textbook: unit, lesson, passage, captioned figure, vocabulary box, comprehension section;
- math textbook: concept, worked example, formula, diagram, practice set, solution/answer area.

### Layout Intent

Blocks must carry layout intent where print usability depends on it.

Examples:

- `keep_with_next`
- `keep_together`
- `choice_inline`
- `choice_grid`
- `matching_two_column`
- `table_question`
- `answer_area`
- `figure_with_caption`
- `two_column_passage`

### Formula And Table Integrity

Tables and formulas must be either:

- rendered clearly and source-verified;
- or recorded as unresolved review packets.

Unresolved packets prevent `basic_print` unless they are explicitly classified as non-blocking decorative or low-risk by a reviewed rule.

For simple reading-textbook text tables, a table visual packet may be closed as `accepted_by_rule` when the Standard table exactly matches the Raw `content_list` table after normalized comparison, source PDF page/bbox exists, and a source PDF crop was generated or reused. This rule does not apply to math/formula-heavy, chart-hybrid, nested, or cross-page tables.

## Review Gates

These do not always block `review`, but they block `basic_print` when profile-critical or widespread:

- high issue candidate count;
- many isolated short blocks;
- many unknown or needs-review blocks;
- loose captions;
- split question groups;
- unresolved visual review packets;
- weak evidence traceability;
- rough but non-fatal layout issues.

## Theme Boundary

The following are outside `basic_print`:

- brand colors;
- decorative headers;
- cover design;
- publication-grade typography;
- style matching the original PDF;
- rich page design.

They belong to `polished`, not `basic_print`.
