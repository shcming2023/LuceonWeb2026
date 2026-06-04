# P0 Contents Parser Conservative Chapter Inference And Exercise Reparenting

Task ID: TASK-20260604-141539-P0-Contents-Parser-Conservative-Chapter-Inference-And-Exercise-Reparenting

## Mainline Goal

Fix the deterministic Layer 3 canonical TOC rules so Contents-derived output keeps a stable:

```text
Unit -> Chapter -> Section -> Exercise
```

structure when the book Contents page contains implicit chapter titles or OCR line breaks.

This task must not optimize the whole TOC system broadly. It only addresses the current Math 2022 blocker where:

- Chapter 1 title `Review of number concepts` was present but unnumbered, causing `1.1-1.7` to hang directly under Unit 1.
- Chapter 4 title was split across lines as `Collectingorganisingand` / `displayingdata 107`, causing `4.1-4.3` to hang directly under Unit 1.
- Chapter 9 title was implicit, causing body exercises such as `Exercise 9.13` to risk falling back to the wrong unit/chapter.
- Orphan exercises such as `Exercise 1.8`, `Exercise 4.4`, and `Exercise 9.13` must not fall to the last active Unit.

## Write Boundary

Allowed files:

- `luceon_service/service.py`
- `luceon_service/tests/test_popo_invocation_boundary.py`
- this task/report/ledger entry under `TaskAndReport/`

Forbidden files and actions:

- Do not modify MinerU or MinerU-Popo upstream code.
- Do not rerun MinerU or MinerU-Popo inference for this task.
- Do not call LLM or use LLM to decide whole-book structure.
- Do not rename source assets or image hash names.
- Do not embed full Markdown, raw tree, or artifact body content into DB metadata.
- Do not modify production DB/MinIO in this code-level task.
- Do not touch local private role files such as `AGENTS.md` or `.agents/**`.

## Required Behavior

1. Contents parser must conservatively infer a missing Chapter `N` only when:
   - parsing the Contents-derived outline;
   - a numbered section `N.x` is encountered;
   - Chapter `N` has not already appeared;
   - there is a nearby non-noise heading buffer immediately before `N.x`.
2. Inferred chapters must preserve source trace:
   - title built from the buffered source lines;
   - metadata records `inferred=true`, `inference=following-section-major`, and `source_lines`;
   - warnings include `inferred_chapter_from_following_section`.
3. Explicit chapter entries remain authoritative and must not be overwritten.
4. Body-tree exercise supplementation must continue to attach:
   - to matching section `N.x` when present;
   - otherwise to Chapter `N` when that chapter exists;
   - never to the last unrelated Unit merely because no section match exists.
5. Candidate source binding must not match a chapter to a Unit Project or other incompatible node kind solely because the number matches.

## Positive Acceptance

- Existing Popo invocation boundary tests pass.
- New focused regression proves implicit Chapter 1 and Chapter 4 are recovered.
- New focused regression proves orphan `Exercise 1.8` and `Exercise 4.4` are not attached to Unit 2 or another unrelated fallback.
- Real Math 2022 evidence replay shows:
  - Chapter 1: `1 Review of number concepts`, parent `Unit 1`, children `1.1-1.7`.
  - Chapter 4: `4 Collectingorganisingand displayingdata`, parent `Unit 1`, children `4.1-4.3`.
  - Chapter 9: `9 Sequences,surdsand sets`, parent `Unit 3`, children `9.1-9.4`.
  - `Exercise 1.8` parent is Chapter 1.
  - `Exercise 4.4` parent is Chapter 4.
  - `Exercise 9.13` parent is Chapter 9.
  - sections remain `103/103` against Contents with no missing/extra sections.

## Negative Acceptance

- No MinerU-Popo inference rerun.
- No LLM structure decision.
- No product/DB/MinIO mutation in this implementation task.
- No broad OCR title cleanup; title text defects remain for later CleanLaTeX/cleaning stage.
- No silent inference: every inferred chapter must carry a warning and source-line metadata.
