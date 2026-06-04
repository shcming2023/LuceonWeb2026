# RawCode2CleanCode UAT Runner 交付与测试指南

作者：Manus AI
状态：P0.1 UAT 可测交付
适用范围：RawCode Bundle 到 CleanCode Bundle 的本地批处理、证据面留存与 UAT 安全门控
最后更新：2026-06-04

## 1. 交付目标

本文档定义 **RawCode2CleanCode UAT Runner** 的交付边界、执行方式、manifest 输入格式、证据面输出格式与测试部门验收建议。该 runner 的目标是把单章节本地 pilot 升级为测试部门可以在 UAT 环境重复执行的批处理入口，同时保持 P0.1 阶段的保守工程边界：runner 只读 RawCode Bundle，只在指定本地输出目录写入 CleanCode 候选与审计文件，不写生产数据库、不写对象存储、不触发 runtime worker。该边界与既有 RawCode2CleanCode Protocol v0 对“本地离线 pilot、允许调用 LLM API、不得写 DB、不得写 MinIO、不得触发主 worker”的规定保持一致。[1]

> **UAT 结论边界：runner 可以证明 CleanCode 候选已按协议生成、质量报告已落盘、零生产副作用已记录；runner 不声明内容已可投产，也不绕过测试部门的人工验收。**

本次交付新增 `scripts/rawcode2cleancode-runner.mjs`，并将其 smoke 测试纳入 `scripts/run-tests.sh` 聚合测试入口。测试部门可以直接使用 runner 对 manifest 中列出的 RawCode 样本进行 dry-run 或受确认的 real 本地运行。real 模式在执行真实阶段前会自动运行 dry-run preflight；若 preflight 失败，真实阶段不会执行。

| 项目 | 当前交付状态 | 说明 |
| --- | --- | --- |
| 单章节 pilot 复用 | 已完成 | `rawcode2cleancode-pilot.mjs` 已导出核心函数，并保留原 CLI 行为。 |
| manifest 批处理 | 已完成 | 支持 1 至 3 个 RawCode 样本的 UAT manifest。 |
| 安全门控 | 已完成 | 缺失操作员、空样本、重复样本、超过硬上限、未确认 real、输入不存在均会被阻断。 |
| 证据面输出 | 已完成 | 每次运行写入 `evidence-surface.json` 与 `runner-result.json`。 |
| 自动化 smoke | 已完成 | `server/tests/rawcode2cleancode-runner-smoke.mjs` 覆盖成功路径与异常门控。 |

## 2. 运行边界与模式

runner 提供两个模式：`dry-run` 与 `real`。`dry-run` 是默认模式，适合测试部门进行 UAT 验证、样本巡检和证据面采集。`real` 模式需要显式传入 `--confirm-real`，并且会先执行 preflight。即使在 real 模式下，当前交付仍然是本地文件处理，不会写 DB、不会写 MinIO、不会向 runtime worker 发送任务。

| 模式 | 触发方式 | 执行行为 | 生产副作用 | 适用场景 |
| --- | --- | --- | --- | --- |
| `dry-run` | `--mode dry-run` 或省略 | 读取 RawCode，生成 CleanCode 候选与证据面；如果请求 `llm` cleaner，会降级为 `llm-dry-run`。 | 固定为 0 | UAT 默认验证、样本回归、门控检查。 |
| `real` | `--mode real --confirm-real` | 先执行 preflight，preflight 通过后再执行真实本地阶段。 | 固定为 0 | 测试部门明确需要验证 real gate 与真实 cleaner 路径时使用。 |
| `llm-dry-run` cleaner | `--cleaner llm-dry-run` | 生成 LLM prompt 与审计文件，但不调用外部 LLM API。 | 固定为 0 | 验证 LLM 输入构造、审计材料和 `NEEDS_REVIEW` 输出。 |

本 runner 的样本硬上限为 3，这是为了避免 UAT 阶段误将局部 pilot 当作整书自动化流水线使用。超过 3 个样本时，即使 manifest 明确列出，runner 也会返回 `ENTRY_HARD_CAP_EXCEEDED` 或 `HARD_CAP_EXCEEDED`，并且不会继续处理。

## 3. manifest 输入格式

测试部门需要准备一个 JSON manifest。manifest 可以使用蛇形命名或驼峰命名；推荐使用蛇形命名，以便与现有文件合约保持一致。`raw_bundle_dir` 可以是 manifest 文件所在目录的相对路径，也可以是绝对路径。

```json
{
  "protocol": "RawCode2CleanCode-UAT-Manifest/v0",
  "operatorId": "uat-operator-001",
  "cleaner": "deterministic",
  "samples": [
    {
      "sample_id": "sample-chapter-001",
      "raw_bundle_dir": "./rawcode/sample-material/v0",
      "chapter_id": "chapter_001",
      "title": "第一章 数与式"
    }
  ]
}
```

| 字段 | 必需性 | 类型 | 说明 |
| --- | --- | --- | --- |
| `protocol` | 推荐 | string | 推荐值为 `RawCode2CleanCode-UAT-Manifest/v0`。 |
| `operatorId` / `operator_id` | 必需，可由 CLI 覆盖 | string | 记录 UAT 操作员或执行主体，用于证据面归属。 |
| `cleaner` | 可选 | string | 可取 `deterministic`、`llm-dry-run` 或 `llm`。未提供时默认为 `deterministic`。 |
| `samples` | 必需 | array | 样本数组，数量必须为 1 至 3。 |
| `samples[].sample_id` | 推荐 | string | 证据面中的样本标识。 |
| `samples[].raw_bundle_dir` | 必需 | string | RawCode Bundle 路径，应包含 `manifest.json`、`toc.json` 与 `chapters/*/raw.md` 等协议文件。[1] |
| `samples[].chapter_id` | 推荐 | string | 单章节处理目标；省略时由 pilot 自动选择第一章节。 |
| `samples[].title` | 可选 | string | 测试报告中展示的人类可读标题。 |

## 4. CLI 使用方式

在仓库根目录执行以下命令即可运行默认 dry-run。`--out` 指向 runner 的输出根目录，runner 会在其中创建带时间戳和 manifest hash 的 run 目录。

```bash
node scripts/rawcode2cleancode-runner.mjs \
  --manifest /path/to/rawcode2cleancode-uat-manifest.json \
  --operator-id uat-operator-001 \
  --mode dry-run \
  --out .tmp/rawcode2cleancode-uat
```

如果测试部门需要验证 real mode 的安全门控，应使用以下命令。该命令只有在 `--confirm-real` 存在时才会进入 real 流程，而且 real 前置 preflight 失败时不会执行真实阶段。

```bash
node scripts/rawcode2cleancode-runner.mjs \
  --manifest /path/to/rawcode2cleancode-uat-manifest.json \
  --operator-id uat-operator-001 \
  --mode real \
  --confirm-real \
  --out .tmp/rawcode2cleancode-uat
```

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--manifest` | 无 | 必需，指向 UAT manifest JSON。 |
| `--operator-id` | manifest 中的 `operatorId` | 推荐显式提供，用于证据面归属。 |
| `--mode` | `dry-run` | 可取 `dry-run` 或 `real`。 |
| `--confirm-real` | false | real 模式必需；缺失时返回 `REAL_RUN_NOT_CONFIRMED`。 |
| `--hard-cap` | 3 | UAT 样本硬上限；当前最大允许值为 3。 |
| `--cleaner` | manifest 或 `deterministic` | 覆盖 manifest 的 cleaner。 |
| `--model` | pilot 默认模型 | 仅真实 LLM cleaner 使用。 |
| `--api-base` | pilot 默认 API base | 仅真实 LLM cleaner 使用。 |
| `--out` | `.tmp/rawcode2cleancode-runner` | 输出根目录。 |

## 5. 输出目录与证据面

一次成功或被阻断的 CLI 运行都会尝试写入证据面。正常进入 runner 的 run 会生成如下结构，其中 `evidence-surface.json` 是测试部门最重要的验收入口，`runner-result.json` 则保留完整 CLI 结果。

```text
<out>/rawcode2cleancode-<mode>-<operator>-<timestamp>-<manifestHash>/
  evidence-surface.json
  runner-result.json
  dry-run/
    samples/
      01-<sampleId>/
        cleancode/<materialId>/v<N>/...
  preflight/              # 仅 real 模式存在
  real/                   # 仅 real 模式且 preflight 通过后存在
```

| 文件 | 责任 | 测试关注点 |
| --- | --- | --- |
| `evidence-surface.json` | UAT 证据面 | `summary.ok`、`operationCounts`、`productionSideEffects`、`samples[].evidence.output`。 |
| `runner-result.json` | 完整执行结果 | CLI 参数、manifest hash、runId、preflight 与真实阶段细节。 |
| `clean.md` | CleanCode 主产物 | 内容是否忠实、是否存在明显噪音、图片引用是否可读。 |
| `quality_report.json` | 机器质量报告 | `status`、阻断原因、图片检查、覆盖率和风险项。 |
| `unresolved_items.json` | 未决项清单 | 是否保留所有不确定问题，是否未静默删除。 |
| `diff.md` | 差异摘要 | 清洗动作是否可解释、可审计。 |

证据面中的生产副作用字段应始终保持为 0。测试部门应把任何非零值视为阻断缺陷，并停止后续验收。

```json
{
  "summary": {
    "operationCounts": {
      "localRawBundleRead": 1,
      "localCleanBundleWrite": 1,
      "llmApiCall": 0,
      "dbWrite": 0,
      "minioWrite": 0,
      "runtimeWorkerPost": 0
    },
    "productionSideEffects": {
      "db_writes": 0,
      "minio_writes": 0,
      "runtime_worker_posts": 0
    },
    "readinessClaimed": false
  }
}
```

## 6. 建议验收标准

测试部门在 UAT 环境下应至少执行一次 `dry-run`，并建议补充一次未确认 real 的负向测试，以确认 runner 不会绕过安全门控。对于 `llm-dry-run` cleaner，应检查 audit 目录中是否存在 prompt 与 dry-run 响应；该模式的章节状态通常为 `NEEDS_REVIEW`，这属于预期行为。

| 编号 | 验收项 | 期望结果 |
| --- | --- | --- |
| AC-01 | manifest 可被读取并解析 | runner 输出 `ok: true` 或明确的阻断错误码，不出现未捕获异常。 |
| AC-02 | dry-run 本地产物生成 | 每个样本均生成 CleanCode Bundle、`clean.md`、`quality_report.json`、`unresolved_items.json` 与 `diff.md`。 |
| AC-03 | 证据面完整 | `evidence-surface.json` 存在，包含 runId、manifest hash、operatorId、summary 和 samples。 |
| AC-04 | 生产副作用为零 | `dbWrite`、`minioWrite`、`runtimeWorkerPost` 以及 `productionSideEffects` 全部为 0。 |
| AC-05 | 硬上限生效 | 样本数超过 3 或 `--hard-cap` 大于 3 时，runner 应阻断。 |
| AC-06 | real 模式确认生效 | 缺少 `--confirm-real` 时返回 `REAL_RUN_NOT_CONFIRMED`。 |
| AC-07 | preflight gate 生效 | real 模式中 preflight 失败时，真实阶段不应执行。 |
| AC-08 | 不声明投产就绪 | runner 与样本结果中的 `readinessClaimed` 应保持 `false`。 |

## 7. 自动化回归入口

本交付新增的 smoke 测试可以单独运行，也可以通过聚合测试入口运行。单独运行适合开发者或测试部门快速确认 runner；聚合入口适合 release gate。

```bash
node server/tests/rawcode2cleancode-runner-smoke.mjs
```

聚合测试入口中已新增 RawCode2CleanCode runner smoke 阶段。若 UAT 环境具备前端服务与 Playwright 条件，可以执行完整聚合测试。

```bash
bash scripts/run-tests.sh
```

| 测试入口 | 覆盖范围 | 是否需要 Web 服务 |
| --- | --- | --- |
| `node server/tests/rawcode2cleancode-runner-smoke.mjs` | runner 成功路径、`llm-dry-run`、异常门控、real preflight gate。 | 不需要。 |
| `bash scripts/run-tests.sh` | 既有 smoke、服务端 smoke、RawCode2CleanCode runner smoke、Playwright E2E。 | 需要满足既有 UAT 环境条件。 |

## 8. 已知限制与后续建议

当前 runner 仍属于 P0.1 UAT 可测交付，而不是整书级生产流水线。它继承协议中“单章节或单小节”的最小粒度设计，并以本地候选包形式输出 CleanCode。[1] 在测试部门完成 UAT 后，后续可以把多章节 assemble、真实 LLM 质量评估、人工审核 UI、PDF 重组和版本化入库作为独立阶段推进。

| 限制 | 当前处理 | 后续建议 |
| --- | --- | --- |
| 整书处理 | 暂不支持，样本硬上限 3。 | P1 引入章节队列与 assemble gate。 |
| 真实 LLM cleaner | 已保留 `llm` 接口；`llm-dry-run` 可先验证 prompt 与审计。 | UAT 环境配置 API key 后再执行受控真实 LLM 验证。 |
| 生产入库 | 当前明确禁止。 | 待 CleanCode 合约稳定后，通过独立 review gate 接入 DB/MinIO。 |
| 内容质量 | runner 只输出质量报告，不代替人工验收。 | 测试部门按抽样内容和协议逐条审查。 |

## References

[1]: ./RawCode2CleanCode-Protocol-v0.md "RawCode2CleanCode Protocol v0"
