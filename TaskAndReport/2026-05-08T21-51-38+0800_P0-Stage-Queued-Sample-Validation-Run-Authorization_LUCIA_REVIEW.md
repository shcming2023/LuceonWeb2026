# Lucia Review: P0 Stage-Queued Sample Validation Run Authorization

Review ID:
`2026-05-08T21-51-38+0800_P0-Stage-Queued-Sample-Validation-Run-Authorization_LUCIA_REVIEW`

Reviewed decision:
`TASK-20260508-214325-P0-Stage-Queued-Sample-Validation-Run-Authorization`

Reviewer:
Lucia

Review time:
2026-05-08T21:51:38+0800

## Director Decision Recorded

Director approved Option A:

`批准最多 3 个样本`

## Scope Authorized

Lucia is authorized to issue a scoped Lucode task for a controlled stage-queued production validation run.

Authorized sample order:

1. `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/4.XxwlAs2026/sample/期末质量分析及建议（曹云童 ）.pdf`
2. `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/4.XxwlAs2026/sample/走向成功_英语_二模卷16篇.pdf`
3. `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/4.XxwlAs2026/sample/Cambridge IGCSE(0580)  Core and Extended Mathematics_2018(Cambridge  University Press).pdf`, only if samples 1 and 2 pass the stage-queued gates

Authorized validation model:

- next upload may start after prior sample upload/storage intake is durable;
- durable intake requires upload success, task ID, material ID, objectName, provider, DB task visibility, DB material visibility, and trackable task state/stage;
- MinerU active parse-running count must stay `<=1`;
- Ollama active metadata/Ollama-running count must stay `<=1`.

## Still Forbidden

- Production release-readiness declaration.
- Production deploy, fast-forward, rebuild, restart, rollback, or Docker mutation unless explicitly needed for pre-approved validation gates. This task does not authorize such mutation.
- Ollama restart, start, stop, kill, or reload.
- Model, timeout, config, secret, or production-local override changes.
- DB row deletion, MinIO object deletion, Docker volume deletion/pruning, task/artifact/log deletion or cleanup.
- External sample copy, move, rename, edit, delete, normalization, pollution, or GitHub sync.
- Skeleton fallback or silent degradation.
- Signed MinIO URL or secret persistence in reports.
- More than three controlled uploads.

## Next Action

Lucia issued:

`TASK-20260508-215138-P0-Stage-Queued-Sample-Validation-Run`

This is a controlled validation artifact task, not production release readiness.
