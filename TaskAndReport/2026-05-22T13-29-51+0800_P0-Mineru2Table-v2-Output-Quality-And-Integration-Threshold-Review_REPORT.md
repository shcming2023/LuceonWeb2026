# TASK-20260522-132951-P0-Mineru2Table-v2-Output-Quality-And-Integration-Threshold-Review Report

## 1. Final Classification

`PROCEED_TO_MINIMAL_ORCHESTRATION_DESIGN_WITH_GUARDRAILS`

The Task 245 `v2` output is sufficient to justify moving into Luceon-side minimal orchestration and metadata integration planning.

This is not product-final structural acceptance. The sample is structurally shallow, and the service still has guardrail/provenance debt that must be handled before unattended or broad automation.

## 2. Read-Only Boundary

- Luceon HEAD reviewed: `c187c890374f972ddd4126bc28c3a81df9b4e860`
- Luceon workspace: `/Users/concm/prod_workspace/Luceon2026`
- Mineru2Table workspace: `/Users/concm/prod_workspace/Mineru2Tables`

Performed read-only operations only:

- read canonical Raw Material object from MinIO;
- read Task 245 `v2` output objects from MinIO;
- read Task 242 `v1` prefix object inventory;
- read `jobs.json`;
- inspected recent logs for absence of new POST/LLM/upload activity during this review window.

No runtime/data mutation was performed:

- no `POST /api/v1/jobs`;
- no `chat/completions`;
- no MinIO object write/delete/cleanup/move/rename;
- no DB write;
- no Docker build/recreate/restart/down;
- no source-code edit;
- no manual job-store edit;
- no cleanup or reuse of the contaminated `v1` prefix.

## 3. Source Object Inventory

Canonical input:

- Bucket: `eduassets-raw`
- Object: `mineru/1842780526581841/v1/content_list_v2.json`
- Size: `31543` bytes
- SHA256: `f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db`
- Top-level type: `list`
- Top-level length: `4`
- Flattened blocks: `71`
- Block types:
  - `title`: `1`
  - `paragraph`: `70`

The input is a single-title article-like sample. Therefore a shallow one-section tree is plausible for this specific sample and should not be treated as equivalent to an empty or failed result.

## 4. Output Object Inventory

Task 245 output prefix:

```text
eduassets-clean/toc-rebuild/1842780526581841/v2/
```

The prefix contains exactly seven required artifacts:

| File | Size | SHA256 | Parse/Content |
| --- | ---: | --- | --- |
| `flooded_content.json` | `20054` | `e1a8355a80a5014b5a616ed441a4d0851c47d6a3d6092711ce765ffe11eea7b7` | JSON list parses |
| `logic_tree.json` | `375` | `b61ee669b63bccb597f9ff31e5773ac1cc53a7bf6d6ef7a5ba73d467c7267665` | JSON object parses |
| `readable_tree.md` | `106` | `bba5cf360fa7c0d92a9489ce84dfc40458de6072f812d7ab5d381b8e828946d7` | non-empty Markdown |
| `skeleton.json` | `21160` | `c004915e79dde976f68cbb460ae3e6bf34e81be6b7cc8bdc28d5252d5ec15f9e` | JSON object parses |
| `unresolved_anchors.json` | `2` | `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945` | JSON list parses |
| `metrics.json` | `129` | `add72cb0a0c0dcb2fe051961795da8c151181022df79770583d5fb75c7ed9718` | JSON object parses |
| `provenance.json` | `2108` | `4762b30f5ab344b1eec0a46b4541b9fa1df314ca756eb837b4622b43169104eb` | JSON object parses |

No `token_stats.json` exists under `v2`.

## 5. Structure Assessment

### `logic_tree.json`

Observed structure:

- node count: `2`
- max depth: `1`
- root node:
  - `node_id=root`
  - `title=文档根节点`
  - `status=pending_anchor`
  - children: `1`
- child node:
  - `node_id=p0_80_77_359_96_title`
  - `title=向树叶学习：人工光合作用`
  - `status=anchored`
  - `level=1`
  - children: `0`

Assessment:

- Positive: the output is not the Task 242 skeletal failure shape. It contains an anchored L1 title and is consistent with a source that has only one title block.
- Limitation: it does not infer any additional substructure from the bilingual paragraphs. This is acceptable for minimal integration evidence but not enough to claim product-grade structure quality.

### `readable_tree.md`

Observed:

- non-empty;
- 3 lines;
- presents the single detected L1 title with the source-derived node id.

Assessment:

- Positive: useful as a minimal operator-visible outline.
- Limitation: too shallow to validate complex TOC reconstruction behavior.

## 6. Block Coverage And Content Preservation

### `flooded_content.json`

Coverage:

- flattened blocks: `71`
- block types:
  - `title`: `1`
  - `paragraph`: `70`
- structural metadata key: `__meta_flooding__`
- all `71/71` blocks have an L1 assignment;
- unique L1 title assignment: `向树叶学习：人工光合作用`.

Text sequence comparison:

- source text count: `71`
- flooded text count: `71`
- source/flooded exact sequence match: `true`
- mismatch count: `0`

Assessment:

- Positive: content preservation and structural flooding are good enough for Luceon to store as a traceable `toc-rebuild` asset.
- Limitation: all blocks belong to one L1, so this sample does not validate multi-level section assignment.

### `skeleton.json`

Coverage:

- block count: `71`
- source/skeleton exact text sequence match: `true`
- block types preserved:
  - `title`: `1`
  - `paragraph`: `70`

Assessment:

- Positive: source block coverage is preserved.

## 7. Unresolved Anchors

`unresolved_anchors.json`:

- type: JSON list;
- count: `0`;
- size: `2` bytes.

Assessment:

- Positive: file exists and is valid JSON.
- Positive: no free-text invented source claims were observed.
- Limitation: this sample does not stress unresolved-anchor behavior.

## 8. Metrics

`metrics.json`:

```json
{
  "tokens": {
    "prompt": 6212,
    "completion": 54,
    "total": 6266
  },
  "cost_cny_estimated": 0.006319999999999999,
  "cost_cny_actual": 0.0
}
```

Assessment:

- Positive: non-zero token evidence distinguishes Task 245 from Task 242's false-success/zero-token failed run.
- Limitation: `cost_cny_actual=0.0` should be treated as service-emitted accounting evidence, not as provider billing truth.

## 9. Provenance

`provenance.json` contains:

- schema/service/job/options/stats sections;
- one input entry;
- six output entries;
- job id: `luceon-task245-toc-rebuild-1842780526581841-v2-20260522052230`;
- input bucket: `eduassets-raw`;
- input object: `mineru/1842780526581841/v1/content_list_v2.json`;
- input SHA256: `f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db`.

Known gaps:

- `input size_bytes=0`, while the actual input size is `31543`;
- `provenance.outputs` contains six content/metric outputs and does not self-reference `provenance.json`.

Assessment:

- Positive: enough ObjectRef/hash traceability exists for Luceon to record an initial CleanService output reference set.
- Must guard: Luceon should not treat provenance quality as complete until `input size_bytes` is fixed or compensated in Luceon-side verification.

## 10. No-Mutation Verification

After this read-only review:

- `jobs.json` size remains `6469` bytes;
- `jobs.json` SHA256 remains `882471ce941d20182c83237df9dc65969bc7c9b47a6c13d717d2c0c53cedf6f0`;
- `jobs.json` key count remains `3`;
- no new `POST /api/v1/jobs`, `chat/completions`, or MinIO upload log lines were observed during the Task 246 review window;
- `v1` object count remains `7`;
- `v2` object count remains `7`.

## 11. Integration Threshold Decision

Decision:

```text
Proceed to Luceon minimal orchestration design with guardrails.
```

Reasoning:

- The service produced the required seven-file contract under `v2`.
- The output is materially different from Task 242's failed-run artifacts.
- Source block coverage is preserved.
- Every source block is assigned structural metadata.
- Metrics show real LLM activity.
- Provenance includes the critical input ObjectRef and hash.

Guardrail requirement:

Luceon minimal integration must independently verify, before accepting a clean output record:

- job terminal state is `completed`;
- all seven artifacts exist;
- `metrics.tokens.total > 0`;
- JSON artifacts parse;
- Markdown is non-empty;
- source ObjectRef and SHA match the Raw Material input;
- output prefix is a new Luceon-assigned asset version;
- failed or stale prefixes are not reused.

## 12. Must-Fix Before Broad Automation

These should be assigned as narrow follow-ups before unattended/batch CleanService automation:

1. Mineru2Table false-success guard: LLM/API failures must not produce terminal `completed`.
2. Provenance input size: record the actual input object size, not `0`.
3. Decide and document whether `provenance.outputs` should include `provenance.json` itself.

## 13. Deferrable Side Work

These are useful but should not block minimal orchestration design:

- multi-document and multi-level TOC quality evaluation;
- operator UI presentation;
- unresolved-anchor cockpit;
- cost overrun desk;
- RawMaterial2CleanMaterial;
- cleanup/migration policy for failed `v1` artifacts.

## 14. Review Boundary

Acceptance of Task 246 means only:

```text
Luceon has a grounded quality/threshold decision for the Task 245 v2 output.
```

It does not mean:

- Luceon orchestration is implemented;
- database persistence is implemented;
- output quality is product-final;
- RawMaterial2CleanMaterial has run;
- UAT, L3, pressure PASS, release readiness, production readiness, production上线, or go-live.
