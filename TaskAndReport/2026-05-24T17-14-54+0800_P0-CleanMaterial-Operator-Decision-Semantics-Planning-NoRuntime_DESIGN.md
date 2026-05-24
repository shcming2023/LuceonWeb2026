# Clean Material Operator Decision Semantics Design

Task:

```text
TASK-20260524-171454-P0-CleanMaterial-Operator-Decision-Semantics-Planning-NoRuntime
```

## 1. State Model

This model is for an operator decision on one Clean Material service/version.
It is not the CleanService execution status, artifact readability status, or a
RawMaterial2CleanMaterial downstream status.

| State | Meaning | Terminal |
| --- | --- | --- |
| `pending-review` | Clean artifacts are available for operator inspection, but no operator decision has been recorded. | No |
| `accepted` | Operator decided this Clean Material version is acceptable as input evidence for the next mainline stage. | Yes for this version |
| `needs-repair` | Operator found issues that may be repairable by a later bounded repair/rebuild task. The version is not accepted for downstream use. | No |
| `rejected` | Operator decided this Clean Material version must not feed downstream stages. Use only for trace/audit. | Yes for this version |
| `superseded` | A newer Clean Material version became the current candidate, so this older version is no longer the active decision target. | Yes for this version |

Default for the current inspected `toc-rebuild v4` metadata:

```text
pending-review
```

The following concepts must remain separate:

- CleanService execution status: `completed`, `failed`, `review-pending-partial`,
  and related service lifecycle states.
- Artifact inspection/readability: whether artifact refs can be opened, parsed,
  and reviewed.
- Operator decision: the human decision state above.
- Downstream cleaning status: future RawMaterial2CleanMaterial or other product
  stage state.

## 2. Metadata Shape Proposal

Decision metadata belongs under the material-level Clean Material summary as the
current product truth for a material/service/version. Task-level clean metadata
may record a mirrored bounded snapshot for traceability in a later task, but the
minimum durable decision source should be:

```text
material.metadata.cleanMaterials[serviceName].operatorDecision
```

Minimum fields:

```json
{
  "state": "pending-review",
  "decidedAt": null,
  "decidedBy": null,
  "reason": null,
  "note": null,
  "artifactSnapshot": {
    "assetVersion": "v4",
    "jobId": "luceon-task-1779085089451-toc-rebuild-v4",
    "provenanceObjectName": "toc-rebuild/1842780526581841/v4/provenance.json",
    "sourceInput": {
      "bucket": "eduassets-raw",
      "object": "mineru/1842780526581841/v1/content_list_v2.json",
      "sha256": "f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db",
      "size_bytes": 31543
    },
    "artifactRefs": {
      "readable_tree": {
        "bucket": "eduassets-clean",
        "object": "toc-rebuild/1842780526581841/v4/readable_tree.md"
      },
      "logic_tree": {
        "bucket": "eduassets-clean",
        "object": "toc-rebuild/1842780526581841/v4/logic_tree.json"
      }
    },
    "tokensTotal": 6266,
    "unresolvedAnchorCount": 0
  },
  "supersededBy": null,
  "updatedAt": "2026-05-24T00:00:00.000Z"
}
```

Example placement for the canonical sample:

```json
{
  "metadata": {
    "cleanMaterials": {
      "toc-rebuild": {
        "latestVersion": "v4",
        "status": "completed",
        "provenanceObjectName": "toc-rebuild/1842780526581841/v4/provenance.json",
        "prefix": null,
        "operatorDecision": {
          "state": "pending-review",
          "decidedAt": null,
          "decidedBy": null,
          "reason": null,
          "note": null,
          "artifactSnapshot": {
            "assetVersion": "v4",
            "jobId": "luceon-task-1779085089451-toc-rebuild-v4",
            "provenanceObjectName": "toc-rebuild/1842780526581841/v4/provenance.json",
            "sourceInput": {
              "bucket": "eduassets-raw",
              "object": "mineru/1842780526581841/v1/content_list_v2.json",
              "sha256": "f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db",
              "size_bytes": 31543
            },
            "artifactRefs": {
              "readable_tree": {
                "bucket": "eduassets-clean",
                "object": "toc-rebuild/1842780526581841/v4/readable_tree.md"
              },
              "logic_tree": {
                "bucket": "eduassets-clean",
                "object": "toc-rebuild/1842780526581841/v4/logic_tree.json"
              },
              "provenance": {
                "bucket": "eduassets-clean",
                "object": "toc-rebuild/1842780526581841/v4/provenance.json"
              }
            },
            "tokensTotal": 6266,
            "unresolvedAnchorCount": 0
          },
          "supersededBy": null,
          "updatedAt": "2026-05-24T00:00:00.000Z"
        }
      }
    }
  }
}
```

This task does not write this example to DB.

## 3. Transition Rules

Allowed transitions:

| From | To | Requirement |
| --- | --- | --- |
| none | `pending-review` | A completed Clean Material version becomes visible/inspectable. |
| `pending-review` | `accepted` | Operator identity and timestamp are recorded. |
| `pending-review` | `needs-repair` | Operator identity, timestamp, and reason are recorded. |
| `pending-review` | `rejected` | Operator identity, timestamp, and reason are recorded. |
| `needs-repair` | `accepted` | A later implementation explicitly allows re-review after repair evidence. |
| `needs-repair` | `rejected` | Operator decides repair is not worth pursuing. |
| `accepted` | `superseded` | A newer asset version becomes current. |
| `needs-repair` | `superseded` | A newer version replaces the repair candidate. |
| `rejected` | `superseded` | A newer version replaces the rejected candidate. |

Forbidden transitions:

- `rejected -> accepted` without a new version or explicit future re-review task.
- `superseded -> accepted`, `superseded -> needs-repair`, or
  `superseded -> rejected`.
- Any transition that changes CleanService execution status.
- Any transition that implies RawMaterial2CleanMaterial has run.
- Any transition without recording operator identity, timestamp, and evidence
  snapshot.

When a newer asset version is created, the previous version may be marked
`superseded` with:

```json
{
  "supersededBy": {
    "assetVersion": "v5",
    "jobId": "luceon-task-1779085089451-toc-rebuild-v5"
  }
}
```

`needs-repair` differs from `rejected`:

- `needs-repair` means the artifact may be salvageable and should block
  downstream use until a repair/rebuild task is authorized.
- `rejected` means the version should not be repaired in-place or used
  downstream; a new version or new upstream evidence is required.

## 4. Evidence Requirements

Every operator decision except the initial default must record:

- `decidedBy`: stable operator/user id or local operator label.
- `decidedAt`: ISO timestamp.
- `state`: target decision state.
- `artifactSnapshot.assetVersion`.
- `artifactSnapshot.jobId`.
- `artifactSnapshot.provenanceObjectName`.
- `artifactSnapshot.sourceInput.object`, `sha256`, and size when available.
- `artifactSnapshot.artifactRefs` for at least `readable_tree` and one JSON
  artifact; preferably all seven refs when present.
- `reason`: required for `needs-repair` and `rejected`; optional but allowed for
  `accepted`.
- `note`: optional operator comment.

Content hashes can reference existing ObjectRef hashes when available. The
future implementation should not fetch and hash artifact bodies merely to make a
decision unless a separate task authorizes that heavier verification.

## 5. Product Behavior Boundary

Minimum future UI behavior:

- Show current operator decision state in the existing Clean Material card.
- If no decision exists, show `pending-review`.
- Provide small decision actions only for the current Clean Material version:
  `Accept`, `Needs repair`, `Reject`.
- Require reason text for negative decisions.
- Show the artifact snapshot that will be recorded before submit.
- Keep action disabled when there are no artifact refs to inspect.
- Show read-only state for superseded versions.

Forbidden UI behavior for the next implementation:

- No broad approval workflow dashboard.
- No multi-step assignment/escalation system.
- No role/permission redesign.
- No RawMaterial2CleanMaterial launch button.
- No artifact editing.
- No automatic repair/rebuild.
- No batch decision UI.

## 6. Next Implementation Task Boundary

Proposed next task name:

```text
P0 CleanMaterial Operator Decision Minimal UI And Metadata Patch NoRuntime
```

Allowed files:

- `src/app/utils/cleanMaterialView.ts`
- `src/app/components/CleanMaterialSummaryCard.tsx`
- one focused decision component under `src/app/components/`
- `src/app/pages/AssetDetailPage.tsx` and `src/app/pages/TaskDetailPage.tsx`
  only if needed to pass operator identity or refresh after apply
- a small server/db route only if the existing metadata update path cannot
  safely express the exact material metadata patch
- focused tests or smoke helpers
- TaskAndReport task/report/ledger files

Forbidden operations:

- CleanService runtime, Mineru2Table POST/query/probe, MinIO write/delete,
  Docker/production operations, upload/retry/reparse/Re-AI, RawMaterial2CleanMaterial,
  broad workflow/permission system, batch decisions, readiness/go-live claims.

Acceptance criteria:

- Existing v4 defaults to `pending-review` when no decision exists.
- Operator can record `accepted`, `needs-repair`, or `rejected` for current v4.
- Negative states require reason.
- Patch is limited to material Clean Material decision metadata.
- Decision snapshot includes version/job/provenance/sourceInput/artifact refs.
- Superseded/non-current version is read-only.
- No source artifact content is modified.

Checks:

- `git diff --check origin/main...HEAD`
- `npx pnpm@10.4.1 exec tsc --noEmit`
- `npx pnpm@10.4.1 run build`
- focused smoke/unit check for decision metadata construction
- server syntax check if any server route changes

## 7. Deferred Items

- RawMaterial2CleanMaterial execution or launch.
- Batch Clean Material decisions.
- Multi-user permission and governance policy.
- Audit export/reporting.
- Production validation and readiness.
- Decision analytics.
- Version comparison UI.
- Artifact annotation or content editing.
