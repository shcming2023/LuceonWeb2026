# P0 Release Readiness Runtime Validation Authorization

Decision ID:
`TASK-20260508-140545-P0-Release-Readiness-Runtime-Validation-Authorization`

Issued by:
Lucia

Issued at:
2026-05-08T14:05:45+0800

Next Actor:
Director

## Background

The MinIO console exposure boundary has been narrowed to local-only and accepted by Lucia. The project still cannot claim production release readiness because several runtime validation categories remain open.

Known remaining categories:

- Large-PDF soak.
- Concurrency validation.
- Error-path matrix.
- Rollback/recovery rehearsal.
- Exact production HEAD and override-boundary confirmation before release-candidate naming.
- Docker frontend base-image preflight before any rebuild.
- Single-operator/no-auth release boundary confirmation.

Some of these checks may create controlled upload tasks, parse tasks, MinIO objects, parsed artifacts, AI metadata records, or controlled failure records. They are not destructive, but they are production runtime mutations and should be explicitly authorized.

## Decision Required

Director should decide whether Lucia may issue scoped Lucode runtime-validation tasks for the next release-readiness evidence wave.

Recommended approval scope:

- Allow controlled production validation tasks that create test upload/parse/AI artifacts only for validation evidence.
- Allow large-PDF soak with specified test files and stop conditions.
- Allow limited concurrency validation with bounded file count, bounded duration, and explicit abort conditions.
- Allow error-path matrix validation using non-destructive or synthetic failure cases where possible.
- Allow rollback/recovery rehearsal planning first; actual rollback/recovery execution should remain separately authorized if it would affect runtime state.
- Require all validation reports to record exact production HEAD, override content, test files, task IDs, artifacts created, commands, pass/fail evidence, and cleanup/non-cleanup decision.

Recommended prohibitions:

- No production release-readiness declaration.
- No DB row deletion or manual repair.
- No MinIO object deletion unless separately approved.
- No Docker volume deletion or pruning.
- No secret changes.
- No broad production rebuild/deploy/rollback outside a specific task.
- No external/multi-user release boundary acceptance.

## Lucia Recommendation

Lucia recommends approving a staged runtime-validation wave, starting with a large-PDF soak task followed by limited concurrency validation and an error-path matrix task. Rollback/recovery should first be planned and then separately authorized if execution is needed.

## Required Output

Director decision:

- Approve staged runtime-validation wave under the recommended scope.
- Approve only a subset of the validation categories.
- Hold and request more planning.
- Cancel release-readiness runtime validation for now.
