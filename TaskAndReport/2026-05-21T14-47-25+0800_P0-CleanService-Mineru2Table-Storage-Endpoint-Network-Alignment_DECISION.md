# TASK-20260521-144725-P0-CleanService-Mineru2Table-Storage-Endpoint-Network-Alignment Decision

## Decision Needed

Task 233 proved that the next blocker is storage endpoint/network/allowlist alignment:

```text
Luceon generated payload endpoint: minio:9000
Mineru2Table allowlist: localhost:9000
Mineru2Table network: mineru2tables_default
Luceon MinIO network: cms-network
cms-minio aliases on cms-network: cms-minio, minio
```

Director must choose how to align the runtime boundary before any further real dispatch attempt.

## Option A: Correct Target Runtime Alignment (Luceon Recommended)

Authorize a narrow runtime/config task to align Mineru2Table with Luceon's MinIO service boundary:

- attach or configure `mineru2table-api` so it can resolve/reach Luceon's `cms-network` MinIO alias `minio:9000`;
- update Mineru2Table allowlist to include `minio:9000`;
- keep Mineru2Table MinIO credentials empty for the immediate Option B failure-mode retry unless Director separately authorizes credentials;
- rerun read-only health/openapi/allowlist checks;
- then retry the one-POST Option B dispatch only if all gates pass.

Tradeoff: touches Docker/network/env configuration, so it needs explicit Director authorization. It is the cleanest path toward the eventual success-path architecture.

## Option B: Temporary Failure-Mode Shortcut

Authorize a one-off retry using payload endpoint `localhost:9000` only to pass the current allowlist, while keeping credentials empty.

Tradeoff: lower configuration work, but misleading for the future success path because `localhost` inside `mineru2table-api` is not the Luceon MinIO service boundary.

## Option C: Pause Real Dispatch

Do not mutate runtime config and do not retry POST. Continue mock-only or docs-only planning.

Tradeoff: safest operationally, but stops the mainline from crossing the real service boundary.

## Luceon Recommendation

Choose Option A. It is a true prerequisite, not side work, because future Raw Material to Clean Material processing must use the same storage endpoint semantics that real jobs will use.

## Still Not Authorized Unless Director Chooses It

- Docker/network/env changes.
- MinIO credential injection.
- MinIO object reads/writes.
- DB metadata patching.
- LLM calls.
- Scheduler activation.
- Any readiness, UAT, L3, pressure PASS, production上线, or go-live claim.
