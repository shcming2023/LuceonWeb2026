# Lucode Task: P0 Parsed ZIP Manual Sample Layout Production Revalidation

- Task ID: `TASK-20260509-164028-P0-Parsed-Zip-Manual-Sample-Layout-Production-Revalidation`
- Created At: `2026-05-09T16:40:28+0800`
- Created By: Lucia
- Next Actor: Lucode
- Priority: P0
- Status: 待执行
- Related Review: `TaskAndReport/2026-05-09T16-40-28+0800_P0-Parsed-Zip-Manual-Sample-Layout-Alignment_LUCIA_REVIEW.md`
- Expected Sample: `/Users/concm/Downloads/Cambridge IGCSE(0580)  Core and Extended Mathematics_2018(Cambridge  University Press).zip`

## Objective

Deploy or verify the latest main code containing the parsed-ZIP manual-sample layout correction, then revalidate the production "下载 MinerU 解析输出物" behavior against the Director-provided expected sample structure.

## Scope

Allowed:

- sync production runtime to the accepted main commit for this task;
- restart only the minimum necessary application service if required to apply code;
- download the default parsed ZIP for the relevant Cambridge material if available;
- compare normalized ZIP manifests against the Director-provided expected sample;
- inspect raw/diagnostic export modes only if needed to prove default-user boundary.

Forbidden:

- no DB, MinIO, Docker volume, task, material, artifact, log, sample, or secret deletion;
- no mutation of `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/4.XxwlAs2026/sample`;
- no model/timeout/provider/production override change;
- no new validation upload unless Lucia issues a separate task;
- no production release-readiness declaration.

## Required Validation

1. Confirm production code HEAD and deployed upload-server code include the manual-sample layout correction.
2. Download default parsed ZIP through the same endpoint/UI path used by "下载 MinerU 解析输出物".
3. Produce a normalized manifest for the downloaded ZIP:
   - ignore `__MACOSX/**`;
   - ignore `.DS_Store`;
   - record top-level folders, file count, extension counts, and sample paths.
4. Produce a normalized manifest for Director sample ZIP:
   - `/Users/concm/Downloads/Cambridge IGCSE(0580)  Core and Extended Mathematics_2018(Cambridge  University Press).zip`;
   - ignore `__MACOSX/**`;
   - ignore `.DS_Store`.
5. Verify default production ZIP has:
   - exactly one user-facing top-level material folder;
   - `<material-folder>/full.md`;
   - OCR contents directly under `<material-folder>/...`;
   - no `<material-folder>/ocr/...`;
   - no root `full.md`;
   - no root `mineru-result.zip`;
   - no root `artifact-manifest.json`;
   - no non-OCR legacy expanded files;
   - no app-generated `__MACOSX` or `.DS_Store`.
6. Verify `mineru-raw` and `diagnostic` modes still retain raw/debug access if checked.

## Required Checks

- `git diff --check`
- focused parsed ZIP export smoke if runnable in production or dev
- normalized ZIP manifest comparison between production download and Director sample

## Required Report

Create `TaskAndReport/2026-05-09T16-40-28+0800_P0-Parsed-Zip-Manual-Sample-Layout-Production-Revalidation_REPORT.md` with:

- production path, branch, and HEAD;
- deployed code HEAD;
- downloaded ZIP path;
- normalized manifest summary for production download;
- normalized manifest summary for Director sample;
- pass/fail result for each required validation item;
- exact residual risk;
- explicit statement that production release readiness is not claimed.

