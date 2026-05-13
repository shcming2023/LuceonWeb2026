# TASK-20260513-195002-P0-Small-Stage-Queued-Validation-After-AI-JSON-Repair Report

- Role: TestAcceptanceEngineer
- Report time: 2026-05-13T19:57:44+0800
- Task brief: `TaskAndReport/2026-05-13T19-50-02+0800_P0-Small-Stage-Queued-Validation-After-AI-JSON-Repair_TASK.md`
- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production workspace: `/Users/concm/prod_workspace/Luceon2026`
- Production entered: yes
- Result: blocked after sample 1 stop condition
- Recommendation: blocked / fail for the small serial validation run; Director decision required.

## Scope

The task authorized a small serial validation from `/Users/concm/prod_workspace/Luceon2026/testpdf`: enumerate all PDFs, validate at most the first 3 by lexicographic filename order, upload one at a time, and stop immediately on dependency blocking, admission open, upload failure, terminal failed state, unresolved active-task drift, or systemic failure evidence.

Selected first 3 candidates by lexicographic filename order:

1. `06第六章 长期股权投资与合营安排.pdf`
2. `2025.pdf`
3. `2025_2026学年春季课程中数G8_提取.pdf`

Only sample 1 was uploaded. Samples 2 and 3 were not uploaded because sample 1 reached terminal failed state.

## Candidate Inventory

| # | Filename | Size bytes | SHA-256 |
| ---: | --- | ---: | --- |
| 1 | `06第六章 长期股权投资与合营安排.pdf` | 10147571 | `3dd5732cecfe8523f8dd78c5332240cb143149a092cea5ba66de3b864ef08133` |
| 2 | `2025.pdf` | 175841 | `642599641f3b15e11b19f383379864081464be1f9c79bdd4f1e9334489c4b1ad` |
| 3 | `2025_2026学年春季课程中数G8_提取.pdf` | 530205 | `71b95d983cdf73507c7334d3682f117f1dfce454286a6bb9f60d437a070b3cfb` |
| 4 | `Cambridge IGCSE(0580)  Core  Mathematics_2023(Hodder Education).pdf` | 63585444 | `cb0e855babcdb39062d8ced78bd9b0b115e09ad9fbbcfffd91e9a01f8052fc2f` |
| 5 | `Cambridge IGCSE(0580)  Core and Extended Mathematics_2018(Cambridge  University Press).pdf` | 39063547 | `a74d612fd10ec0d6f13c06e2ed1cc386d356af2ed81242bc14fa33d9a4bd7022` |
| 6 | `Cambridge IGCSE(0580)  Core and Extended Mathematics_2018(Hodder Education).pdf` | 39891635 | `1d2a6bac4ec39f83f8d815c68354ec13dfda9c0327cd7ea3fef81c6b843e4fd4` |
| 7 | `Cambridge IGCSE(0580)  Core and Extended Mathematics_2022(Cambridge  University Press).pdf` | 102034314 | `2f5b0c0d7d067d5275fa14fd4da96b702801f18616fdff1c8a5d7f2dfc91fd47` |
| 8 | `Cambridge IGCSE(0580)  Core and Extended Mathematics_2023(Hodder Education).pdf` | 55782830 | `85feeb3f19975eb0ced3ee1fee8fee28b9bb778118e35bacbcbf5f4554387092` |
| 9 | `Cambridge IGCSE(0580) Extended Mathematics Practice Book__2023(Cambridge  University Press).pdf` | 103549160 | `cc07915a4c33cee263669d3b963d4e694aa9679cc854eb79f75467748c22193e` |
| 10 | `Cambridge IGCSE(0580) Extended Mathematics Student Book_2018(Oxford University Press).pdf` | 96516982 | `c2e244a2a30b08faf55e45615fe75009137224a8647225c37d0a9301e1bc6b9a` |
| 11 | `Cambridge IGCSE(0606) and O Level(4037) Additional Mathematics Coursebook_2023(Cambridge  University Press).pdf` | 40235936 | `68e17dac3a259e6258d939a3cd879c3703045ee165bdc114afa91f692ceaed9d` |
| 12 | `Cambridge IGCSE(0606) and O Level(4037) Additional Mathematics Coursebook_2023(Hodder Express).pdf` | 43536275 | `03130f2f150b1c7ed7d4f27860c9dde0ba8d167f7965e5a7e693c05ca5b20db4` |
| 13 | `Cambridge IGCSE(0606) and O Level(4037) Additional Mathematics _2018(Haese Mathematics).pdf` | 91501329 | `a5bfdcd16ebdbf59485cecea14ea1a10eb0529fb28edebbf2b7d9265e66edc4e` |
| 14 | `Cambridge IGCSE(0607) International Mathematics  Coursebook Extended_2018(Haese Mathematics).pdf` | 45247007 | `e175170c4b7fff005f8cf227edb422c826e0731879e32c2a702a42f86cc50112` |
| 15 | `Cambridge IGCSE(0607) International Mathematics  Coursebook_2023(Hodder Express).pdf` | 52964792 | `fc261474c028edab34631cbbf2500d4eb39e8f6802a1cf4f1b5dd3d40ad544f5` |
| 16 | `G7_Workbook_ready_to_print.pdf` | 15157403 | `672c96f6125ab3afcf0dcd63b858a2584fa4cdd427000df40870f52aa477435b` |
| 17 | `PDF document-4F18-A8A3-62-0.pdf` | 711046 | `bb491c5782c001a60e9af1c8d531cbf3ce9807f0db341af765c31cc2d75e56f4` |
| 18 | `出国.pdf` | 33814 | `444b2acfa19f23758059cb799848a05e09821b2c6f5a53e64ff39cfbd935444f` |
| 19 | `向树叶学习：人工光合作用.pdf` | 86884 | `2230acbb40524e1de80f1ebe57a13c5f41db353e15c6727f5ebb97383154e16c` |
| 20 | `期末质量分析及建议（曹云童 ）.pdf` | 1041695 | `c2b15ff6cfdd13e7c7cad7ea898bcd0ad98d33b6afde7c3d3e55773916b256e8` |
| 21 | `蓝月、血月、橙月？月亮为啥还会变色？.pdf` | 76797 | `80ece67614c1808a4247496402ceb71b4dd0fdd09ecae9023723c4a530fcb244` |
| 22 | `财务回执(￥50,000.00).pdf.pdf` | 96870 | `40f67c5e5ba41bd4b0c322d128b3274fff4527f93cf75b774f7a67b863038e31` |
| 23 | `走向成功_英语_二模卷16篇.pdf` | 3457503 | `b3e00ad1c7f7afff4bdae1b484abad941af618fd80b9b5f9f22d69848968eaac` |
| 24 | `附件三：考务流程培训-纸笔标准考试.pdf` | 5349060 | `d2e8e9bcd5b59e88a516d2143ece6a03060bf01276481e09d7577a5f82c5ae5a` |

## Preflight Evidence

Development workspace:

- `git status --short --branch` exit 0.
- Branch: `development-engineer/p0-post-validation-ollama-mineru-blockers`.
- Existing dirty/untracked files were present before this run; unrelated files were not reverted or modified.

Production workspace:

- `git status --short --branch` exit 0: `## main...origin/main`, `M docker-compose.override.yml`.
- `git log -1 --oneline` exit 0: `de2d23f Accept AI JSON repair and dispatch deployment`.
- `docker compose ps` exit 0: `cms-db-server`, `cms-frontend`, `cms-minio`, and `cms-upload-server` were healthy.
- `bash ops/runtime-ownership-status.sh` exit 0: upload-server env truth showed `LOCAL_MINERU_ENDPOINT=http://host.docker.internal:8083`, `OLLAMA_API_URL=http://host.docker.internal:11434`, `OLLAMA_TIER2_MODEL=qwen3.5:9b`, `DISABLE_AI_SKELETON_FALLBACK=true`, `ALLOW_AI_SKELETON_FALLBACK=false`.
- Upload health exit 0: `{"ok":true,"service":"upload-server"}`.
- Dependency health with `mineruSubmitProbe=true` exit 0: `ok=true`, `blocking=false`; MinerU submit probe returned HTTP 202; Ollama `chatOk=true`, `modelResident=true`.
- After the submit-probe transient cleared, MinerU health showed `queued_tasks=0`, `processing_tasks=0`, `failed_tasks=0`.
- Active-task diagnostics before upload: no active task, current task, queued tasks, drift tasks, submit-retryable tasks, or takeover-required tasks; historical AI failures remained unchanged.
- Admission circuit before upload: `open=false`, `state=closed`, counts all zero, `activeTaskClean=true`.
- Ollama `/api/ps` showed `qwen3.5:9b` resident.

## Sample 1 Evidence

Sample:

- File: `/Users/concm/prod_workspace/Luceon2026/testpdf/06第六章 长期股权投资与合营安排.pdf`
- Size: `10147571`
- SHA-256: `3dd5732cecfe8523f8dd78c5332240cb143149a092cea5ba66de3b864ef08133`

Upload:

- Endpoint: `POST http://localhost:8081/__proxy/upload/tasks`
- Request ID: `tae-task100-s1-1778673388500`
- Material ID: `stage100-01-1778673388500`
- HTTP status: `200`
- Task ID: `task-1778673389375`
- Object: `originals/stage100-01-1778673388500/source.pdf`
- MinerU task ID: `87b58566-c24e-4b34-8313-61e2b9dc2c09`

Observed task timeline:

- `2026-05-13T11:56:34.568Z`: worker picked the task.
- `2026-05-13T11:56:34.835Z`: submitted to MinerU, internal ID `87b58566-c24e-4b34-8313-61e2b9dc2c09`.
- `2026-05-13T11:56:34.892Z`: progress message `MinerU 已提交/正在处理，但暂无可归因业务日志`.
- `2026-05-13T11:56:34.920Z`: `worker-failed`, `log-observation-unreadable`, MinerU still processing.
- `2026-05-13T11:56:44.674Z`: misjudged failed corrected, MinerU still processing.
- `2026-05-13T11:56:44.734Z`: resumed task failed again with `log-observation-unreadable`.
- Additional read-only follow-up showed the same correction/failure loop repeating through `2026-05-13T11:57:14.872Z`.

Final Luceon DB/API state observed for sample 1:

- Task: `state=failed`, `stage=mineru-processing`, `progress=50`.
- Task message: `[resume] 执行失败: MinerU 日志活性异常判定卡死(接管): activityLevel=log-observation-unreadable, logAgeMs=Infinityms, mineruStatus=processing. MinerU API 仍显示 processing 但日志长期无业务进展，提前终止轮询。`
- Material: `status=failed`, `mineruStatus=failed`, `aiStatus=failed`.
- AI job: none created.
- Parsed artifacts: none recorded.
- Direct MinerU API after stop: `/tasks/87b58566-c24e-4b34-8313-61e2b9dc2c09` returned `status=processing`, `queued_ahead=0`, `completed_at=null`, `error=null`.
- MinerU `/health` after stop: `processing_tasks=1`.
- Upload-server active-task diagnostics after stop: no active/current/queued/drift/takeover tasks, only historical AI failures.
- Admission circuit after stop: `open=false`, `state=closed`, counts all zero.

UI evidence:

- Task detail page `/cms/tasks/task-1778673389375`: `当前状态=失败`, `当前阶段=mineru-processing`, `已产物=原始文件就绪`, `下一步动作=需排查或重试`, error text matches `log-observation-unreadable`.
- Task list page `/cms/tasks`: top row for this file showed `已终止`, `MinerU 已提交/正在处理，但暂无可归因业务日志`, and the same MinerU log-observation error; counters showed `已失败 4`.
- Screenshots were saved as temporary local evidence under `/tmp/luceon-task100-s1-detail.png` and `/tmp/luceon-task100-s1-list.png`.

## Stop Decision

The run stopped after sample 1 because the task reached terminal `failed` state. This matches the task brief stop condition:

> Stop immediately if any validation task reaches terminal `failed`.

Samples 2 and 3 were not uploaded.

## Findings

1. The small serial validation did not reproduce Task 98's successful full path on the first lexicographic sample.
2. The failure occurred before AI: no AI job was created and no AI JSON repair/finalization evidence exists for sample 1.
3. The dominant failure evidence is MinerU progress/log observability and failed-state adjudication: Luceon repeatedly marked the task failed because log observation was unreadable while direct MinerU still reported the internal task as `processing`.
4. There is a state visibility gap after the stop: direct MinerU reports `processing_tasks=1`, but Luceon active-task diagnostics report no active/current/queued/drift/takeover task and admission remains closed with counts zero.
5. No evidence was found that strict AI fallback weakened or skeleton metadata was produced; the pipeline never reached AI.

## Not Executed

- Samples 2 and 3 were not uploaded because sample 1 reached terminal failed state.
- No pressure, batch-concurrent, soak, broad stress, long-run test, repair, reparse, re-AI, cleanup, restart, rebuild, model operation, data deletion, DB/MinIO/Docker volume mutation, sample mutation, GitHub push, L3 validation, production-readiness, release-readiness, or go-live claim was performed.

## Recommendation

Blocked / fail recommendation for Task 100's small serial validation boundary.

Director should review whether the next action is a DevelopmentEngineer or Architect task around MinerU log-observation failure adjudication and active-task diagnostics drift. The current evidence should not be used as production readiness, release readiness, L3, pressure PASS, batch PASS, or go-live evidence.
