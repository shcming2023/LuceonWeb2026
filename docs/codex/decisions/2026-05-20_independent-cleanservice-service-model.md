# Architectural Decision Record (ADR): Independent CleanService Service Model

- **Status**: Accepted
- **Task ID**: `TASK-20260520-143129-P0-Independent-CleanService-Service-Model-PRD-And-Architecture-Alignment`
- **Date**: 2026-05-20
- **Authors**: Lucode (Development Engineer & Product Manager)
- **Approved By**: Luceon (Architect & Director)

---

## 1. Context & Problem Statement

In Luceon2026, parsing and cleaning educational materials are heavy processing workloads. The Phase 1 mainline relies on local MinerU parsing and Ollama metadata generation. As we transition to Phase 2, we introduce two critical structural and text cleaning stages:
1. **Mineru2Table (`toc-rebuild`)**: Reconstructing structural table-of-contents, logical hierarchy, and anchor mappings.
2. **RawMaterial2CleanMaterial**: Performing block-level cleaning, normalization, and generating final high-fidelity learning assets.

The initial design considered embedding these stages directly within the Luceon main project worker pool. However, this raises severe architectural issues:
* **Resource Contention**: Heavy PDF structure analysis and local LLM/deep learning inferences block Luceon's lightweight web server and task cockpit processes.
* **Release Dependency**: Coupling Mineru2Table's rapid algorithm iterations with Luceon's core CMS business logic leads to high release risks and deployment friction.
* **Technology & Container mismatch**: Heavy document parsing engines and LaTeX/TikZ renderers require massive, complex Docker base images that do not belong in a streamlined Node.js web application.

---

## 2. Decision & Architectural Direction

We formally adopt the **Independent CleanService Service Model**:

1. **Physical and Repository Boundary**:
   * **Luceon Main Project**: Exclusively owns the asset registry (database), task orchestration, operator review workflow, permission audit, cost monitoring, and strict provenance enforcement.
   * **Mineru2Table (`toc-rebuild`)**: Decoupled into an independent, separately developed repository (`shcming2023/Mineru2Table2026`) and independently deployed as a Docker container (`mineru2table-api`).
   * **RawMaterial2CleanMaterial**: Established as a separate, distinct post-processing service in a different repository and container boundary, preventing it from being collapsed into Mineru2Table.
2. **API-Based Collaboration (CleanService Protocol v1)**:
   * Decouple all runtime linkages. Luceon and CleanServices collaborate exclusively via standard asynchronous HTTP API calls.
   * No direct file sharing through local mounts. Input and output assets are transferred exclusively via MinIO ObjectRefs.
3. **Control Plane Supremacy**:
   * Luceon remains the absolute authority for resource identity (`materialId`), processing tasks (`parseTaskId`), monotonic version allocation (`assetVersion`), and job idempotency keys (`job_id`).
   * CleanServices act as pure stateless workers: they consume Luceon-provided inputs and write verified structural or cleaned objects to Luceon-assigned prefixes under `eduassets-clean`.

---

## 3. Detailed Responsibility Division

| Area of Concern | Luceon Control Plane | Independent CleanService (e.g. Mineru2Table) |
| --- | --- | --- |
| **Material/Task Identity** | Owns `materialId`, `parseTaskId`, `job_id`. | Strictly consumes identities; must never mutate or reassign them. |
| **Asset Versioning** | Monotonically allocates and dictates `assetVersion`. | Accepts `assetVersion`; cannot independently decide asset lifecycle versions. |
| **Storage & Object Authority** | Dictates exact input MinIO ObjectRefs and allowed output prefixes. | Reads allowed input refs; writes completed artifacts to assigned prefixes. |
| **State Machine** | Orchestrates tasks, admits jobs, records events, exposes operator review, and issues final acceptance. | Tracks internal job states (`queued`, `processing`, `completed`, `failed`); writes internal service logs. |
| **Cost & Quota Governance** | Sets and audits soft cost limit (`¥5`). Stops or restarts based on user decision. | Enforces hard cost limit (`¥8`) via `options.max_cost_cny`. Shuts down with `quota_exceeded` on overrun. |
| **Failure Adjudication** | Maps service errors to operator-facing states; handles fallback/recovery paths. | Exposes highly structured JSON errors; guarantees explicit terminal failure (no-silent-fallback). |

---

## 4. Consequences & Benefits

* **Strong Isolation**: CleanService crashes, LLM timeouts, or Out-Of-Memory errors in the heavy python-based `Mineru2Table` container do not degrade Luceon's task cockpit or block database transactions.
* **Surgical Iterability**: Mineru2Table and RawMaterial2CleanMaterial can be updated, redeployed, and patched independently without restarting Luceon.
* **Flexible Scalability**: Heavy CleanService Docker containers can be scaled out to specialized GPU instances while Luceon remains on a lightweight host.
* **Immutable Provenance**: By enforcing MinIO ObjectRefs and strict `provenance.json` handoffs, we guarantee a tamper-proof and fully auditable pipeline of derived learning assets.
* **Mainline Safety**: Since CleanServices run strictly post-mainline, our Phase 1 production evidence remains completely safe, isolated, and operational.
