# Source Fidelity Correction Policy V0 - 2026-06-30

Decision:

```text
Basic Print may accept a minimal source typo correction only when it is explicit, evidence-backed, and recorded in correction_log.json.
```

## Why

GF4 V3 fixed the grammar paradigm table rendering problem, but exposed one source-fidelity mismatch:

```text
visual:table_visual_review:b-01544
```

The source crop shows:

```text
Yes, they aren’t.
```

Clean/Standard renders:

```text
Yes, they are.
```

The source PDF text is internally inconsistent with the present continuous short-answer paradigm:

```text
Are they playing?  Yes, they aren’t.  No, they aren’t.
```

For Basic Print, silently changing this would violate source fidelity. Reverting it would preserve the source typo but produce a less usable grammar table. The acceptable closure is to keep the corrected Clean/Standard text and record the source typo correction explicitly.

## Allowed Correction Boundary

A source correction may be accepted in Basic Print only when all checks hold:

- the source PDF evidence is available as a page/bbox crop;
- the source text and corrected text are both explicit;
- the correction is local and minimal;
- the correction fixes an obvious typo, OCR error, or internally inconsistent source cell;
- the correction is pedagogically necessary for direct-print usability;
- the correction is recorded in `correction_log.json` with evidence;
- the review outcome is closed as `accepted`, not `accepted_by_rule`.

This policy does not allow:

- rewriting explanations for style;
- filling missing answers or inventing content;
- changing ambiguous source text;
- broad normalization without per-item evidence;
- silently correcting source content.

## GF4 Application

Correction log entry:

```text
runtime/backend/pipeline-work/audits/gf4-workbook-second-sample-v3-rerun-20260630/standard-final/correction_log.json
```

Evidence:

```text
visual_source_crops/0026-b-01544-image.png
manual_visual_review/standard-page-98.png
standard.pdf#page=98
```

Outcome closure:

```text
visual:table_visual_review:b-01544
decision: accepted
reviewer: codex:manual_source_fidelity_review
reason: accepted_as_evidence_backed_source_typo_correction
```

## Gate Behavior

`correction_evidence` remains `pass` only when every correction has an `evidence` field.

If a correction has no evidence, the gate must fail. A correction count greater than zero is acceptable only because the correction is auditable.

## Conclusion

GF4 can be treated as a Basic Print candidate after this closure, but not an accepted golden. The project has validated one narrow workbook source-correction rule, not a general license to rewrite source PDFs.
