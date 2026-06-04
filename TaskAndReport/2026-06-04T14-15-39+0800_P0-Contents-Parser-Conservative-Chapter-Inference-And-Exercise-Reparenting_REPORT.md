# P0 Contents Parser Conservative Chapter Inference And Exercise Reparenting Report

Task ID: TASK-20260604-141539-P0-Contents-Parser-Conservative-Chapter-Inference-And-Exercise-Reparenting

Branch: `codex/task-327-conservative-chapter-inference`

## Summary

Implemented a narrow deterministic Layer 3 fix for Contents-first canonical TOC construction:

- Added a conservative heading buffer in `_parse_contents_outline`.
- When a section `N.x` appears and Chapter `N` is missing, the parser can infer Chapter `N` from the immediately preceding non-noise heading lines.
- Inferred chapters carry explicit warning and source metadata.
- Candidate source binding now requires compatible node kind for chapter/section/exercise matches, preventing chapter entries from binding to Unit Project nodes solely by number.
- Added focused regression coverage for implicit chapter recovery and orphan exercise reparenting.

No MinerU, MinerU-Popo inference, GPU/MPS worker, LLM, DB, or MinIO operation was performed by this implementation task.

## Files Changed

- `luceon_service/service.py`
- `luceon_service/tests/test_popo_invocation_boundary.py`
- `TaskAndReport/2026-06-04T14-15-39+0800_P0-Contents-Parser-Conservative-Chapter-Inference-And-Exercise-Reparenting_TASK.md`
- `TaskAndReport/2026-06-04T14-15-39+0800_P0-Contents-Parser-Conservative-Chapter-Inference-And-Exercise-Reparenting_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

## Real Evidence Replay

Input evidence reused read-only from production evidence:

- Official Popo tree: `TaskAndReport/evidence/2026-06-04_Task324_TOC_View_Filter_UAT/generated/official_popo_tree.json`
- MinerU markdown Contents: `TaskAndReport/evidence/2026-06-04_Task325_Production_Canonical_TOC_UAT/mineru_markdown/cambridge_igcse_0580_math_2022_luceon_fresh_uat.md`

Replay result:

```json
{
  "node_count": 361,
  "kind_counts": {
    "chapter": 29,
    "exercise": 215,
    "glossary": 1,
    "index": 1,
    "past_paper": 6,
    "section": 103,
    "unit": 6
  },
  "contents_outline_count": 146,
  "expected_sections": 103,
  "sections": 103,
  "missing": [],
  "extra": []
}
```

Targeted hierarchy checks:

- Chapter 1: `1 Review of number concepts`, parent `Unit 1`, warning `inferred_chapter_from_following_section`, children `1.1-1.7`.
- Chapter 4: `4 Collectingorganisingand displayingdata`, parent `Unit 1`, warning `inferred_chapter_from_following_section`, children `4.1-4.3`.
- Chapter 9: `9 Sequences,surdsand sets`, parent `Unit 3`, warning `inferred_chapter_from_following_section`, children `9.1-9.4`.
- `Exercise 1.8` parent: `1 Review of number concepts`.
- `Exercise 4.4` parent: `4 Collectingorganisingand displayingdata`.
- `Exercise 9.13` parent: `9 Sequences,surdsand sets`.

## Checks

```bash
PYTHONPATH=. python3 luceon_service/tests/test_popo_invocation_boundary.py
# PASS popo invocation boundary tests

python3 -m py_compile luceon_service/service.py luceon_service/tests/test_popo_invocation_boundary.py
# Exit code 0

git diff --check
# Exit code 0
```

## Boundary

This closes the immediate structural blocker in the Layer 3 rules. It does not claim final title text cleanliness. OCR/title defects such as missing spaces or misspellings remain outside this task and belong to later per-chapter CleanLaTeX/title-cleaning work.
