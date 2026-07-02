# Grammar Paradigm Table Rebuild Audit V0 - 2026-07-01

Purpose:

```text
Verify, from current artifacts, how the three GF4 V2 table reconstruction blockers were resolved in GF4 V3, and keep this track separate from paired-vocabulary blank-box reconstruction.
```

## Audit

Command:

```text
python3 backend/scripts/audit_standard_grammar_paradigm_table_rebuild.py --v2-standard-dir runtime/backend/pipeline-work/audits/gf4-workbook-second-sample-v2-rerun-20260630/standard-final --v3-standard-dir runtime/backend/pipeline-work/audits/gf4-workbook-second-sample-v3-rerun-20260630/standard-final --out-dir runtime/backend/pipeline-work/audits/gf4-grammar-paradigm-table-rebuild-audit-20260701
```

Artifacts:

```text
runtime/backend/pipeline-work/audits/gf4-grammar-paradigm-table-rebuild-audit-20260701/grammar_paradigm_table_rebuild_audit.json
runtime/backend/pipeline-work/audits/gf4-grammar-paradigm-table-rebuild-audit-20260701/grammar_paradigm_table_rebuild_audit.html
```

## Result

| Metric | Count / status |
| --- | ---: |
| GF4 V2 reconstruction records | `3` |
| reflowed by grammar paradigm renderer | `3` |
| collapsed fragments removed | `3` |
| GF4 V3 decisions for those outcomes | `accepted: 3` |
| GF4 V3 closure | `basic_print_candidate` |
| GF4 V3 acceptance | `pass` |
| GF4 V3 quality score | `100` |
| source-fidelity correction count | `1` |

Rule boundary:

```text
Header-driven grammar paradigm tables with one body row are rendered as aligned multi-row tables only when every body cell splits into the same row count and the common row count is at least 3.
```

Decision:

```text
The grammar paradigm table renderer is validated for the GF4 failure mode and is already part of the GF4 candidate evidence. It is not a broad table rebuild rule and must not be used to solve paired-vocabulary blank-box blockers. The GF4 candidate still depends on the explicit evidence-backed b-01544 source typo correction, so this is candidate evidence, not accepted golden or profile-ready proof.
```

## Separation From Blank-Box Track

```text
GF4 V2 failures: line/row structure flattened inside grammar paradigm tables.
G7+ paired-vocabulary failures: source blank boxes missing inside definition cells.
```

These are separate reconstruction subtracks:

| Track | Current status |
| --- | --- |
| `grammar_paradigm_table_rebuild` | validated for GF4 failure mode |
| `paired_vocabulary_blank_box_preservation` | prototype only, not compiler-ready |

Next safe step:

```text
Do not merge the two reconstruction tracks. Use GF4 as a validated candidate rule for grammar_workbook, and keep G7+ blank-box preservation on a separate source-fidelity/visual-regression path.
```
