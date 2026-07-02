# Grammar Workbook Profile Ready V0 - 2026-07-01

Purpose:

```text
Decide whether the grammar_workbook Standard Basic Print profile has enough candidate evidence to be called profile-ready v0.
```

This is not an accepted-golden promotion and not a release-readiness claim.

## Audit

Command:

```text
python3 backend/scripts/audit_standard_workbook_profile_promotion.py --out-dir runtime/backend/pipeline-work/audits/grammar-workbook-profile-promotion-20260701
```

Artifact:

```text
runtime/backend/pipeline-work/audits/grammar-workbook-profile-promotion-20260701/workbook_profile_promotion_audit.json
```

## Verdict

```text
verdict = grammar_workbook_profile_ready_v0
profile_ready = true
```

Scope:

```text
grammar_workbook Basic Print compiler/profile contract only
```

Explicit exclusions:

- `exercise_workbook`;
- `math_textbook`;
- math-heavy workbooks;
- accepted-golden promotion;
- style / polish / cover design;
- engineering release readiness.

## Candidate Set

| Candidate | Family | Status | Quality | Open blockers |
| --- | --- | --- | ---: | ---: |
| GF6 | Grammar Friends | `basic_print_candidate` | `100` | `0` |
| GF4 | Grammar Friends | `basic_print_candidate` | `100` | `0` |
| GIC | Grammar in Context | `basic_print_candidate` | `100` | `0` |

Criteria:

| Criterion | Result |
| --- | --- |
| at least three candidate workbook samples | `true` |
| at least two workbook families | `true` |
| at least one non-Grammar-Friends candidate | `true` |
| all candidates Standard pass | `true` |
| exercise grouping evidence | `true` |
| fill blank / option / table / figure / helper icon evidence | `true` |
| correction policy evidence recorded | `true` |
| Clean review closure policy evidence | `true` |

## Decision

```text
grammar_workbook profile-ready v0
```

Meaning:

- the `grammar_workbook` profile contract is ready to be used as a Standard Basic Print compiler/profile baseline;
- future grammar workbook samples should be judged against this contract rather than treated as first-principles research every time;
- failures should be recorded as regressions, profile gaps, or out-of-scope sample classes.

Non-meaning:

- no workbook sample is accepted golden by this document;
- GF6/GF4/GIC remain candidate-only;
- G7+ remains `exercise_workbook` review pressure;
- math profile remains blocked/review;
- Standard Basic Print as a whole is not release-ready.

## Caveats

- GF4 uses one evidence-backed correction; correction policy remains evidence-gated.
- GF6 page spot check has non-blocking notes and is not a style/polish sign-off.
- GIC Clean acceptance remains `review` on disk but is candidate-eligible through separate closure ledgers.
- G7+ and math samples remain outside this profile-ready claim.
