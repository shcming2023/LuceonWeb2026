# P0 Mineru2Table Standalone Service Fact Audit And CleanService Contract Freeze Report

- **Task ID**: `TASK-20260520-192050-P0-Mineru2Table-Standalone-Service-Fact-Audit-And-CleanService-Contract-Freeze`
- **Executed by**: `Lucode`
- **Date**: `2026-05-20`
- **Final Branch**: `lucode/TASK-20260520-192050-P0-Mineru2Table-Standalone-Service-Fact-Audit-And-CleanService-Contract-Freeze`
- **Final Branch HEAD**: `6461830fe049f2976151223d277af0a4aead9fef` (confirmed by Luceon from `origin/lucode/TASK-20260520-192050-P0-Mineru2Table-Standalone-Service-Fact-Audit-And-CleanService-Contract-Freeze`)

---

## 1. Execution Summary

I have successfully completed the technical fact audit and contract freeze for the `Mineru2Table` standalone service integration, strictly operating under a **docs-only / read-only control-plane restriction**. No runtime modifications were made to the Luceon2026 codebase, and no remote or local mutative actions were executed against the Mineru2Table deployment or external services.

**Key Achievements (Narrow Return Alignment & Corrections):**
1. **Fact Separation Audited**: Clarified that the local running container `mineru2table-api` is built from an older state (HEAD `43754fa`) and does not support Protocol v1 endpoints, while the remote upstream codebase (HEAD `7e9e592`) natively implements over 90% of the CleanService Protocol v1.
2. **Storage Allowlist Code Bug Uncovered**: Identified the exception gap where `minio_backend.py` throws built-in `PermissionError` but the runner catches `StoragePermissionError`, preventing compliant `forbidden_storage_target` HTTP 403 response.
3. **Fact Audit Document Updated**: Generated and corrected [Mineru2Table-Standalone-Service-Fact-Audit.md](file:///workspace/dev/Luceon2026/docs/contracts/Mineru2Table-Standalone-Service-Fact-Audit.md) to split deployed-vs-upstream states, document the allowlist exception mismatch, and freeze all technical facts.
4. **Adaptation Plan Updated**: Revised [CleanService-Mineru2Table-Adaptation-Plan.md](file:///workspace/dev/Luceon2026/docs/contracts/CleanService-Mineru2Table-Adaptation-Plan.md) to downgrade `Option A` to a recommended candidate for Luceon approval, and add `M-4` task to align allowlist exception mapping.

---

## 2. Current-vs-Target Standalone Service Gaps

Our audit has revealed that `Mineru2Table2026` upstream remote codebase already implements over 90% of the CleanService Protocol v1 specification natively. The remaining gaps are narrowed down to **five precise items** (including the exception type and deployment gaps):

1. **Unresolved Anchors (Missing Artifact)**:
   - **Current**: The external runner does not generate or upload the required `unresolved_anchors.json` artifact, violating the Seven-File Target Output Contract.
   - **Target**: Add a parser step to output unresolved anchors list as `unresolved_anchors.json` (even if empty `[]`).
2. **Metrics Naming Alignment (Diverged Name)**:
   - **Current**: The external runner outputs `token_stats.json` (role `token_stats`) instead of `metrics.json`.
   - **Target**: Rename the artifact role to `metrics` and write it as `metrics.json` inside `runner.py`.
3. **Storage Cleanup Hygiene (Disk Saturation Risk)**:
   - **Current**: Temporary directories generated under `/tmp/mineru2table_{job_id}` during run execution are never physically purged.
   - **Target**: Wrap execution inside a `try...finally` block in `runner.py` to call `shutil.rmtree(temp_dir, ignore_errors=True)`.
4. **Allowlist Exception Mismatch (Diverged Error Gap)**:
   - **Current**: `minio_backend.py` raises standard `PermissionError` upon allowlist violation, but `runner.py` catches `StoragePermissionError`. This type mismatch makes the exception fall through to a generic HTTP 500 error instead of the compliant `forbidden_storage_target` HTTP 403 error.
   - **Target**: Align exceptions by having `minio_backend.py` raise `StoragePermissionError` directly.
5. **Local Deployment OpenAPI Endpoints (Deployment Gap)**:
   - **Current**: The local running container (`mineru2table-api`) is on HEAD `43754fa` and lacks all `/api/v1/jobs` endpoints entirely.
   - **Target**: Redeploy the local container using the latest upstream code (`7e9e592` or later) after other code adaptations are ready.

---

## 3. Transition Strategy & Transition Matrix

| Option | Strategy | Feasibility / Recommendation |
| --- | --- | --- |
| **Option A (Lucode Recommended)** | **Direct Protocol Alignment** (Directly fix the gaps in the external Mineru2Table codebase). | **Highly Recommended Candidate for Luceon Approval**. Due to native Protocol v1 support in remote upstream, direct fixes are low-risk. This avoids all proxy overhead and ensures compliant provenance. |
| **Option B (Rejected)** | **Luceon-Side Multipart Adapter** (Keep Mineru2Table as-is, make Luceon wrap and call deprecated multipart HTTP routes). | **Strictly Rejected**. Introduces massive disk/network double-copy overhead and breaks storage security isolation boundaries. |
| **Option C (Deprecated)** | **Hybrid Local Sidecar Adapter** (Deploy a local proxy translating protocol requests). | **Deprecated**. Rendered redundant by native Protocol v1 capability in the latest Mineru2Table codebase. |

---

## 4. Files Changed

A total of 4 control-plane / docs files have been added or updated:

**Documents added/modified:**
- `docs/contracts/Mineru2Table-Standalone-Service-Fact-Audit.md` (New Fact Audit Document)
- `docs/contracts/CleanService-Mineru2Table-Adaptation-Plan.md` (Updated Adaptation Plan)

**Control-plane metadata modified:**
- `TaskAndReport/TASK_TRACKING_LIST.md` (Ledger status promoted to `Lucode 已回报待 Luceon 审查`)
- `TaskAndReport/2026-05-20T19-20-50+0800_P0-Mineru2Table-Standalone-Service-Fact-Audit-And-CleanService-Contract-Freeze_REPORT.md` (This Report)

---

## 5. Mandatory Safety & Security Assertions

- **No Runtime Code/Dependency Mutation**: Checked that `server/**` (except standard docs/reports) and `src/**` remain completely unmodified. No runtime activation or environment mutation has occurred.
- **No Service/Docker Rebuild**: No local dev or production Docker images were built, and no container was restarted.
- **No Data/Storage Mutation**: No database write, MinIO object uploads/deletions, or Ollama/MinerU executions occurred.
- **No Destructive/Release Claims**: No UAT/L3, pressure PASS, go-live, or release-readiness claims are made.

---

## 6. Validation Evidence

**Verification Commands (`git diff` and control-plane verification)**:
```bash
$ git diff --check origin/main..HEAD
(No output)
Exit code: 0

$ git diff --name-status origin/main..HEAD
A       TaskAndReport/2026-05-20T19-20-50+0800_P0-Mineru2Table-Standalone-Service-Fact-Audit-And-CleanService-Contract-Freeze_REPORT.md
M       TaskAndReport/TASK_TRACKING_LIST.md
M       docs/contracts/CleanService-Mineru2Table-Adaptation-Plan.md
A       docs/contracts/Mineru2Table-Standalone-Service-Fact-Audit.md
Exit code: 0
```

All modified files are strictly restricted to documentation and control-plane ledgers.

---

## 7. Ledger and Control-Plane Status

The `TASK_TRACKING_LIST.md` row for Task 224 has been successfully updated:
- **Status**: `Lucode 已回报待 Luceon 审查`
- **Next Actor**: `luceon`
- **Next Action**: Review Mineru2Table standalone audit report, adaptation plan, and contract freeze before initiating Option A Phase 2 integration.
- **Branch/HEAD**: Confirmed by Luceon as `lucode/TASK-20260520-192050-P0-Mineru2Table-Standalone-Service-Fact-Audit-And-CleanService-Contract-Freeze@6461830fe049f2976151223d277af0a4aead9fef`.
