# Third Workbook Pressure Sample Selection V0 - 2026-06-30

Purpose:

```text
Choose the next non-Grammar-Friends workbook pressure sample without misclassifying math-heavy evidence as grammar_workbook profile readiness.
```

## Candidate Search Result

Local Popo2Raw records show these relevant non-Grammar-Friends candidates:

```text
pdf-01ae095f5a0f2dc7  Grammar in Context Baisic (Seventh).pdf
pdf-58860644b15e909c  (7)G7+.pdf
pdf-6872e8c10a25df23  Cambridge Primary Mathematics Learners Book 5_2nd Edition .pdf
pdf-ef278d5a1ffd9c1d  Cambridge Primary Mathematics Learners Book 1_2nd Edition .pdf
```

Only `pdf-58860644b15e909c` currently has a passing Clean package in `raw2clean`.

## Preferred Candidate

```text
pdf-01ae095f5a0f2dc7 / Grammar in Context Baisic (Seventh).pdf
```

Why it is preferred:

- closest to the current `grammar_workbook` / `exercise_workbook` validation target;
- outside Grammar Friends;
- has grammar tables, review sections, exercises, options, and writing practice;
- Popo2Raw exists with source evidence.

Current evidence:

- raw artifact: `runtime/backend/pipeline-work/popo2raw/run-8-pdf-01ae095f5a0f2dc7-popo-20260617014256-staged_popo_20260617_batch07_sma-1369cfec--005-popo_01ae095f5a0f2dc7_005/body-final`
- source PDF object: `eduassets-input / Grammar in Context Baisic (Seventh).pdf`
- source SHA256: `01ae095f5a0f2dc76b6407fc7908c89b4429d18b5145487a3da1ac72b5e291bd`
- raw QA: included page range `16-317`, assigned blocks `4921`, unassigned blocks `0`, source image refs `396`, markdown image refs `152`, table source images `244`

Current blocker:

```text
Clean review gates remain open after successful v3 Clean generation and Standard v8 gate pass.
```

Clean attempt evidence:

- run record: `docs/standard-research/corpus/runs/pdf-01ae095f5a0f2dc7.gic-clean-blocked-v0-20260630.run.json`
- attempt `gic-clean-v0-20260630`: raw input materialized, no Clean reports, manually interrupted after `>10m` while waiting in `llm_polish_markdown` / `deepseek_chat`
- attempt `gic-clean-v1-20260630`: retried with `DEEPSEEK_MODEL=deepseek-v4-flash`, raw input materialized, no Clean reports, manually interrupted after `>3m` at the same response-stream wait
- run record: `docs/standard-research/corpus/runs/pdf-01ae095f5a0f2dc7.gic-clean-review-v3-20260630.run.json`
- attempt `gic-clean-v3-20260630`: full Clean artifacts generated with `clean.pdf`, `review.html`, `acceptance_report.json`, and `llm_usage.json`; Clean acceptance is `review`, hard failures `0`
- v3 review blockers: `media_review_threshold` with `128` retained media-review images; `llm_structure_revert_threshold` with `7` protected-structure rollbacks
- Standard pressure run: `docs/standard-research/corpus/runs/pdf-01ae095f5a0f2dc7.gic-standard-upstream-limited-v0-20260630.run.json`
- Standard artifact: `runtime/backend/pipeline-work/audits/gic-standard-upstream-limited-v0-rerun-20260630/standard-final`
- Standard status: `review`, quality score `85`, PDF render `pass`, `307` pages
- Standard review blockers: `125` unresolved blocking issue candidates, `377` open blocking review outcomes, source PDF missing
- After source PDF backfill, table/formula closure, and 4 source-crop image reconstructions in the upstream-limited v0 run: Standard gates `pass`, quality score `100`, PDF render `pass`, `308` pages, `377/377` review outcomes closed as `accepted_by_rule`
- After generic workbook relation hardening in the v8 run: `exercise_relation_contract` is `pass`, `real_profile_gap_count` is `0`, question groups increased from `40` to `415`, and orphan table questions dropped from `105` to `0`
- After v8 source crop closure and 4 source-crop-backed image replacements: Standard gates `pass`, quality score `100`, PDF render `pass`, `303` pages, workbook profile `pass`, `377/377` review outcomes closed as `accepted_by_rule`, `125` image source crops and `252` visual table/formula source crops generated
- Clean review closure policy v3 passes after media purpose ledger and LLM fallback ledger; GIC is now a Basic Print candidate
- Clean review scope report: `runtime/backend/pipeline-work/audits/gic-standard-workbook-relation-rule-v8-20260630/standard-final/clean_review_scope_report.json`
- Clean review scope command: `python3 backend/scripts/scope_clean_review_for_standard.py --clean-dir runtime/backend/pipeline-work/audits/gic-clean-v3-20260630/clean-final --standard-dir runtime/backend/pipeline-work/audits/gic-standard-workbook-relation-rule-v8-20260630/standard-final --update-manifest`
- Clean review closure conclusion: reusable media and LLM fallback ledgers close the two Clean review gates for candidate eligibility; Clean `acceptance_report.json` remains unmutated

Decision:

- register as corpus case and Basic Print candidate;
- do not run Standard from Popo2Raw `body-final` as if it were Clean;
- do not treat the v3 Clean review candidate or Standard gate pass as an accepted golden;
- next execution must use a separate accepted-golden review before promoting GIC beyond candidate.

## Fallback Pressure Run

```text
pdf-58860644b15e909c / (7)G7+.pdf
```

Why it is useful:

- outside Grammar Friends;
- Clean package exists and passes Clean acceptance;
- image-heavy and table-heavy;
- can pressure `exercise_workbook`/math-heavy Standard behavior without touching Clean.

Evidence:

- clean package: `runtime/backend/pipeline-work/raw2clean/run-32-pdf-58860644b15e909c-popo-20260618020631-staged_popo_20260618_batch13-97b1f8e5--002-popo_58860644b15e909c_002/clean-final`
- clean status: `pass`
- cleaning units: `127`
- image refs: `2662`
- review items: `17`
- source PDF object: `eduassets-input / (7)G7+.pdf`

Standard review run:

- run: `docs/standard-research/corpus/runs/pdf-58860644b15e909c.g7plus-non-gf-workbook-pressure-v0-20260630.run.json`
- artifact: `runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final`
- profile: `exercise_workbook`
- acceptance: `review`
- quality score: `94`
- PDF render: `pass`, `747` pages, `64,136,385` bytes
- review outcomes: `664` open blocking after image source evidence closed `1477` image outcomes, exact table/formula source evidence closed `2198` outcomes, and one near-match table was manually accepted
- issue candidates: `2661`, unresolved blocking `0` after image issue candidates were covered by visual outcomes
- source crop evidence: `1477/1477` image crops and `2200/2863` table/formula crops generated; `663` table/formula outcomes still need page/bbox and `1` near-match table needs reconstruction
- main blockers: exercise relation contract, `663` table/formula page-bbox gaps, `1` table reconstruction blocker, and source PDF lineage evidence

Limit:

- math-heavy evidence cannot make `grammar_workbook` profile-ready;
- use as pressure/review evidence only.

## Next Execution Choice

Recommended:

1. Use GIC as the first non-Grammar-Friends Basic Print candidate and as part of grammar_workbook profile-ready v0 evidence.
2. Use the `(7)G7+.pdf` Standard review run only for math-heavy `exercise_workbook` failure-mode discovery.

Stop condition:

- do not promote GIC beyond candidate without a separate accepted-golden decision;
- do not force a Standard run from a Raw package;
- do not count a math-heavy fallback as proof of grammar_workbook profile readiness.
