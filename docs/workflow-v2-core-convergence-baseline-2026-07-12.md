# Worker V2 Core Convergence Baseline

Date: 2026-07-12

## Scope

This baseline re-evaluates the fixed 10-case golden cohort against the new core
production gates. It does not use Codex Sidecar repairs and does not count the
legacy page-visual result as proof of outline or content fidelity.

The measured inputs are the latest immutable `canonical-clean` artifacts from
the original 10 Worker V2 jobs. The new validators were run read-only against
those artifacts; no legacy artifact or historical output was overwritten.

## Policy State

- Core convergence mode is enabled by default.
- Codex Sidecar enqueue and execution are disabled.
- Post-QA automatic repair is disabled.
- Existing repair attempts and artifacts remain queryable as audit history.
- Existing `worker-v2.0.0-draft1` jobs retain their original stage contracts.
- New jobs use `worker-v2.1.0-core-convergence1` contracts.

## Outline Gate Baseline

| Case | Result | Observed depth | Blocking evidence |
| --- | --- | ---: | --- |
| 1 | review | 1 | outline depth out of range |
| 2 | review | 1 | outline depth out of range |
| 3 | review | 1 | outline depth out of range |
| 4 | review | 3 | source hierarchy contains missing parent links |
| 5 | review | 3 | missing parent links and outline nodes without body units |
| 6 | pass | 2 | none |
| 7 | review | 0 | empty outline and body unit missing from outline |
| 8 | pass | 2 | none |
| 9 | pass | 2 | none |
| 10 | review | 1 | outline depth out of range |

Current result: **3/10 pass**.

The validator does not synthesize headings to satisfy depth. Every accepted
node must retain a source page and heading evidence. Flat or empty outlines
remain blocked until a general source-evidenced reconstruction rule exists.

## Canonical Content Conservation Baseline

| Case | Source blocks | Preserved blocks | Unexplained source blocks | Exact source-to-Clean mappings | Unmapped Clean blocks |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 1724 | 1495 | 12 | 1274 / 1495 | 796 |
| 2 | 1435 | 1265 | 16 | 1097 / 1265 | 672 |
| 3 | 4007 | 3241 | 136 | 2665 / 3241 | 1483 |
| 4 | 18493 | 12756 | 640 | 9720 / 12756 | 7093 |
| 5 | 5398 | 4547 | 278 | 3665 / 4547 | 2162 |
| 6 | 1596 | 1272 | 69 | 1008 / 1272 | 1013 |
| 7 | 149 | 144 | 1 | 122 / 144 | 85 |
| 8 | 3634 | 2655 | 160 | 2136 / 2655 | 1125 |
| 9 | 4483 | 3940 | 151 | 3266 / 3940 | 1504 |
| 10 | 1442 | 965 | 123 | 796 / 965 | 259 |

Current result: **0/10 pass**.

The ledger now gives every source block an explicit disposition. The only
automatic removals are empty blocks, verified out-of-scope pages, repeated
page-edge headers/footers, and typed structural page noise at a page edge.
Selected source headings may be transformed into outline nodes. All other
unassigned blocks remain review blockers.

Exact block mapping is intentionally conservative. Its current misses include
both real fidelity risks and legitimate block split/merge or Markdown structure
changes. The next iteration must add ordered page-level conservation plus
separate formula, table, image, and split/merge ledgers. The gate must not be
weakened merely to improve the pass count.

## Verification

- Targeted backend tests: 49 passed.
- Frontend TypeScript and production build: passed.
- Python compilation: passed.
- `git diff --check`: passed.
- `graphify update .`: not run because the `graphify` executable is not
  available in the current environment.

## Next Work

1. Reconstruct missing two-to-three-level hierarchy using only general,
   source-evidenced heading signals and bounded DeepSeek classification.
2. Add page-level ordered text conservation and explicit split/merge records.
3. Add independent formula, table, image, question, option, and answer-space
   conservation gates.
4. Make Semantic Annotation consume the accepted outline artifact rather than
   rediscovering headings from Markdown.
5. Bind the deterministic ElegantBook project to accepted outline and content
   manifests before any final quality stage can run.
