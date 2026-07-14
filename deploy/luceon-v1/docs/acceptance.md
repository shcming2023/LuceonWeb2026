# Zero-GPU acceptance

During the freeze window, do not change code, rebuild images, recreate containers, submit GPU parsing, or use the Popo recovery action.

- Verify host arm64, exact image digests, healthy backend/frontend/worker/Redis/compiler, restart count zero, and no OOM.
- Confirm normal users do not see Popo recovery as a primary or menu action and direct recovery API calls return 403.
- Select at least two existing materials by generic criteria: one short/low-image and one long/high-image, both already frozen through MinerU and Popo and already holding Worker, ZIP, and compare evidence.
- Verify filename, material ID, database row, manifest, status markers, Worker output, and review target identity.
- Render original and compiled PDFs in the browser; reject 404, 502, wrong assets, or persistent timeouts.
- Download the existing LaTeX ZIP, verify its structure and hashes, and independently compile it in the pinned ShareLaTeX container.
- Compare MinIO marker snapshots before and after. There must be no new batch, submitted, running, MinerU, or Popo job marker.
- Confirm PipelineRun, WorkflowJob, and StageRun have no unexplained queued/running records.

Current-Mac evidence is staging only. A production pass requires this checklist on the separate target Mac mini.
