# Luceon Review: TASK-20260522-102956-P0-Mineru2Table-Single-Sample-Real-Success-Path-Validation

Review time: 2026-05-22T11:06:41+0800

Decision:

```text
CHANGES_REQUIRED_CONTROL_PLANE_MISSING_AND_FALSE_SUCCESS_ON_LLM_FAILURE
```

Task 242 is not accepted.

The runtime produced valuable mainline evidence, but it is failed evidence:
Mineru2Table submitted exactly one job and uploaded the seven expected artifact
filenames, yet the service logged an LLM authentication failure and still marked
the job `completed` with zero-token metrics and skeletal/empty structural
outputs.

## Control-Plane Blocker

After `git fetch origin --prune --tags`, Luceon found no GitHub-visible branch
matching:

```text
lucode/TASK-20260522-102956
```

No Task 242 report file is visible on `main` at:

```text
TaskAndReport/2026-05-22T10-29-56+0800_P0-Mineru2Table-Single-Sample-Real-Success-Path-Validation_REPORT.md
```

Therefore the submitted chat summary cannot be accepted as the formal delivery
record.

## Runtime Facts Independently Verified By Luceon

Luceon performed read-only host/runtime checks. No cleanup, retry, DB write, or
additional POST was performed by Luceon.

### Job Store

`/app/data/jobs.json` in `mineru2table-api`:

```text
size: 3581 bytes
sha256: 683bbbb94a13c84e62e6ed2dd6a13c87fb7042efa4e03c9d16920046e80cf330
key_count: 2
```

Keys:

```text
luceon-optionb-mock-job-1779399902295
luceon-task242-toc-rebuild-1842780526581841-v1-20260522025136
```

The Task 242 job record reports:

```text
status: completed
material_id: 1842780526581841
asset_version: v1
```

Artifact keys in the job record:

```text
flooded_content
logic_tree
metrics
provenance
readable_tree
skeleton
unresolved_anchors
```

### Target Prefix Objects

Target prefix:

```text
eduassets-clean/toc-rebuild/1842780526581841/v1/
```

Object count: `7`

Objects:

| File | Size | SHA256 |
| --- | ---: | --- |
| `flooded_content.json` | 14090 | `9cda588e28c65085a4928895a6091ab520e2a7d7381766ac2d538f6505567db6` |
| `logic_tree.json` | 138 | `135e32777cd03442827110e179a7c95868c600a3b919d0b3b4aa2830ea2fb2ef` |
| `metrics.json` | 105 | `798fe58889e401d53721ed6014a268bd8183c74567f7719057594d6ee55c56d8` |
| `provenance.json` | 2050 | `b6d938419466cd11de4ce59982508311ef0212e06a0c7e9bce1fbb5afbfa4bd9` |
| `readable_tree.md` | 39 | `4dce26d3b9c196b3b7003502eebadbc64ffae62a1bb942c5aacb85960d0f0b60` |
| `skeleton.json` | 21160 | `c004915e79dde976f68cbb460ae3e6bf34e81be6b7cc8bdc28d5252d5ec15f9e` |
| `unresolved_anchors.json` | 2 | `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945` |

There are no extra objects and no `token_stats.json`.

### LLM Failure And False Success

Container logs for the Task 242 job show:

```text
HTTP 401 Authorization Required from DeepSeek chat completions
LLM authentication failure
```

The raw API key value is not reproduced in this review.

Despite that LLM failure, the job was marked `completed`.

`metrics.json` contains:

```json
{
  "tokens": {
    "prompt": 0,
    "completion": 0,
    "total": 0
  },
  "cost_cny_estimated": 0.0,
  "cost_cny_actual": 0.0
}
```

The job record contains the same zero-token/zero-cost stats.

`logic_tree.json` is only a skeletal root node:

```json
{
  "node_id": "root",
  "title": "文档根节点",
  "level": 0,
  "status": "pending_anchor",
  "confidence": 0.0,
  "evidence": [],
  "children": []
}
```

`readable_tree.md` is only a heading.

`unresolved_anchors.json` is `[]`.

### Provenance Concerns

`provenance.json` does point to the expected input ObjectRef and SHA256:

```text
eduassets-raw/mineru/1842780526581841/v1/content_list_v2.json
f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db
```

However, Luceon also observed:

```text
implementation_commit: unknown
input size_bytes: 0
```

These are provenance quality gaps for later correction, but the immediate P0 is
the false-success semantics on LLM failure.

## Findings

### F1. Delivery Branch And Report Are Missing

Task 242 cannot be accepted until the GitHub-visible branch and report are
present.

### F2. The Claimed Success Is Actually An LLM Authentication Failure

The task was intended to prove a real LLM success path. The actual evidence is
that DeepSeek returned authentication failure.

This should have been reported as:

```text
BLOCKED_LLM_RUNTIME_FAILURE
```

not as a completed success-path validation.

### F3. Mineru2Table Incorrectly Converts LLM Failure Into Completed Artifacts

The service produced seven artifact filenames and marked the job `completed`,
but the structural output is skeletal and metrics are zero. Empty/skeleton
artifacts must not be represented as clean success.

This is a mainline defect and should be fixed before another success-path run is
attempted.

### F4. The Current Target Prefix Is Now Contaminated With Failed-Run Artifacts

The authorized target prefix now contains artifacts from the failed LLM run.

Do not rerun Task 242 into the same prefix unless the Director explicitly
authorizes either:

- cleanup/replacement of that prefix, or
- use of a new asset version/prefix such as `v2`.

No cleanup is authorized by this review.

## Narrow Return Requirements

Lucode should do only the following unless Director separately authorizes a new
runtime attempt:

1. Push the Task 242 delivery branch and report to GitHub.
2. Correct the report classification to:

   ```text
   BLOCKED_LLM_RUNTIME_FAILURE
   ```

3. Record the LLM 401/authentication failure without printing raw key material.
4. Record that the job was incorrectly marked `completed` despite LLM failure.
5. Record the seven object names and hashes already present in the target
   prefix as failed-run artifacts.
6. Record that the target prefix must not be reused for another run without
   Director authorization for cleanup/replacement or a new asset version.
7. Keep the ledger at `Ready for luceon Review` only after the corrected branch
   and report are visible.

Do not perform another POST, another LLM call, cleanup, delete, overwrite,
rename, move, DB write, Docker build, broad compose down, dependency restart,
network mutation, source-code edit, or manual job-store edit as part of this
return.

## Review Boundary

This review accepts only that the run produced useful failed evidence. It does
not accept Task 242 as a successful validation.

No UAT, L3, release-readiness, production-readiness, pressure PASS,
production上线, or go-live claim is made or accepted.
