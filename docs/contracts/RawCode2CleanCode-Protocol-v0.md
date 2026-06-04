# RawCode2CleanCode Protocol v0

作者：Manus AI  
状态：P0.1 工程合约草案  
适用范围：单章节本地候选闭环；支持规则预清洗、受控 LLM 清洗接口、规则后处理与本地验证  
最后更新：2026-06-04

## 1. 协议目标

**RawCode2CleanCode Protocol v0** 定义 Luceon2026 中 `RawCode → CleanCode` 阶段的最小工程合约。该阶段接收由 MinerU 解析 PDF 后，再经 MinerU-Popo 与 Luceon 规则处理得到的 **RawCode Bundle**，并输出经过章节切块、噪音清洗、顺序校正、图片引用稳定化和质量验证后的 **CleanCode Bundle**。

本协议的核心目标不是生成 LaTeX，也不是直接生成最终 PDF，而是生成一份可被后续 PDF 重组、LaTeX 转换、HTML 展示或人工审核流程消费的 **Markdown + images 标准内容包**。因此，本阶段应当被理解为内容清洗层，而不是排版层。

> **定义：CleanCode 是忠实于原 PDF、目录顺序正确、内容完整可读、噪音已清除、图片引用可验证的 Markdown + images 文件夹。**

## 2. 阶段边界

RawCode2CleanCode 阶段位于 MinerU-Popo/Luceon 规则处理之后、PDF 重组之前。它不重新解析 PDF，不绕过目录重建结果，也不直接写入生产数据库或对象存储。

| 项目 | v0 规定 |
| --- | --- |
| 输入 | MinerU-Popo + Luceon 规则处理后的 RawCode Bundle。 |
| 输出 | CleanCode Bundle，即清洗后的 Markdown + images + manifest + quality report。 |
| 最小粒度 | 单章节或单小节。 |
| 执行方式 | 本地离线 pilot，允许调用 LLM API，但不得写 DB、不得写 MinIO、不得触发主 worker。 |
| 质量目标 | 完整可读、顺序正确、忠实原文、图片引用稳定、疑难项可审计。 |
| 非目标 | 不生成最终 PDF，不做出版级排版，不承诺整书自动生产，不静默删除不确定内容。 |

## 3. 术语定义

| 术语 | 定义 |
| --- | --- |
| RawCode | 由 MinerU-Popo 与 Luceon 规则处理后的中间内容包，形态为 Markdown + images + metadata。 |
| CleanCode | 经清洗整理后的标准内容包，形态仍为 Markdown + images + metadata。 |
| Chapter Chunk | 依据重建目录切出的章节或小节处理单元。 |
| Source Map | 记录 RawCode 内容块与上游解析块、页码、位置或章节节点之间关系的来源映射。 |
| Image Map | 记录 RawCode 图片引用、原始图片路径、章节内规范路径与保留状态的图片映射。 |
| Unresolved Item | 程序或 LLM 无法高置信判断的内容、公式、图片、表格、章节边界或 OCR 片段。 |
| Quality Report | 自动生成的机器可读质量检查报告，用于判断候选产物是否可进入人工审阅或后续阶段。 |

## 4. RawCode Bundle 输入合约

RawCode Bundle 必须是一个可单独复制、压缩和审计的文件夹。v0 阶段推荐采用如下目录结构。

```text
rawcode/{materialId}/v{N}/
  manifest.json
  toc.json
  full.md
  images/
  chapters/
    chapter_001/
      raw.md
      images/
      source_map.json
      image_map.json
      chunk_manifest.json
```

其中，`full.md` 是全书级 Markdown 视图，`chapters/*/raw.md` 是章节级处理单元。v0 的单章节 pilot 可以只要求一个章节目录存在，但顶层 `manifest.json` 与 `toc.json` 必须存在。

| 文件 | 必需性 | 说明 |
| --- | --- | --- |
| `manifest.json` | 必需 | 记录材料 ID、版本、上游任务、生成时间、规则版本和输入来源。 |
| `toc.json` | 必需 | 记录重建后的目录树、章节顺序、章节 ID 与标题。 |
| `full.md` | 推荐 | 全书 Markdown 汇总视图，可由章节拼装生成。 |
| `images/` | 必需 | 全局图片池，保存从上游解析产物继承或规范化后的图片。 |
| `chapters/*/raw.md` | 必需 | 单章节待清洗 Markdown。 |
| `chapters/*/source_map.json` | 必需 | 章节内容块与上游来源的映射。 |
| `chapters/*/image_map.json` | 必需 | 章节内图片引用与真实文件路径的映射。 |
| `chapters/*/chunk_manifest.json` | 必需 | 章节切块元数据，包括章节边界、标题、顺序和风险标记。 |

### 4.1 `manifest.json` 最小 schema

```json
{
  "protocol": "RawCode2CleanCode/v0",
  "bundle_type": "rawcode",
  "material_id": "sample-material",
  "version": "v0",
  "created_at": "2026-06-04T00:00:00.000Z",
  "source_pipeline": {
    "mineru": { "available": true },
    "minerupopo": { "available": true },
    "luceon_rules": { "available": true }
  },
  "chapters": [
    { "chapter_id": "chapter_001", "title": "Chapter 1", "path": "chapters/chapter_001/raw.md" }
  ]
}
```

### 4.2 `toc.json` 最小 schema

```json
{
  "toc_version": "v0",
  "material_id": "sample-material",
  "nodes": [
    {
      "id": "chapter_001",
      "level": 1,
      "title": "Chapter 1",
      "order": 1,
      "raw_path": "chapters/chapter_001/raw.md"
    }
  ]
}
```

### 4.3 `image_map.json` 最小 schema

```json
{
  "chapter_id": "chapter_001",
  "images": [
    {
      "raw_ref": "../images/img_001.png",
      "normalized_ref": "images/img_001.png",
      "source_path": "../../images/img_001.png",
      "required": true,
      "reason": "referenced_by_markdown"
    }
  ]
}
```

## 5. CleanCode Bundle 输出合约

CleanCode Bundle 与 RawCode Bundle 一样，必须是可审计、可打包、可复现的文件夹。v0 阶段推荐目录结构如下。

```text
cleancode/{materialId}/v{N}/
  manifest.json
  toc.json
  full.md
  images/
  chapters/
    chapter_001/
      clean.md
      images/
      clean_manifest.json
      quality_report.json
      unresolved_items.json
      diff.md
```

| 文件 | 必需性 | 说明 |
| --- | --- | --- |
| `manifest.json` | 必需 | 记录 CleanCode Bundle 全局元数据、输入来源、规则版本、模型信息和验证状态。 |
| `toc.json` | 必需 | 从 RawCode 继承并可追加清洗状态的目录树。 |
| `full.md` | 推荐 | 由所有章节 `clean.md` 拼装而成的全书 Markdown。 |
| `images/` | 推荐 | 全局 CleanCode 图片池。P0 可由章节图片复制得到。 |
| `chapters/*/clean.md` | 必需 | 清洗后的章节 Markdown，是后续 PDF 重组的主要输入。 |
| `chapters/*/images/` | 必需 | 本章节实际引用的图片。 |
| `chapters/*/clean_manifest.json` | 必需 | 记录单章节输入、输出、hash、规则版本、模型信息和文件路径。 |
| `chapters/*/quality_report.json` | 必需 | 记录验证结果、指标、风险项和阻断原因。 |
| `chapters/*/unresolved_items.json` | 必需 | 记录所有未解决问题，不允许静默丢弃。 |
| `chapters/*/diff.md` | 必需 | 人类可读的 raw 与 clean 差异摘要。 |

### 5.1 `clean_manifest.json` 最小 schema

```json
{
  "protocol": "RawCode2CleanCode/v0",
  "bundle_type": "cleancode_chapter",
  "material_id": "sample-material",
  "chapter_id": "chapter_001",
  "status": "PASS",
  "input": {
    "raw_md": "rawcode/sample-material/v0/chapters/chapter_001/raw.md",
    "source_map": "rawcode/sample-material/v0/chapters/chapter_001/source_map.json",
    "image_map": "rawcode/sample-material/v0/chapters/chapter_001/image_map.json"
  },
  "output": {
    "clean_md": "cleancode/sample-material/v0/chapters/chapter_001/clean.md",
    "images_dir": "cleancode/sample-material/v0/chapters/chapter_001/images"
  },
  "cleaner": {
    "mode": "deterministic-pilot",
    "llm_used": false,
    "model": null
  },
  "hashes": {
    "raw_md_sha256": "...",
    "clean_md_sha256": "..."
  }
}
```

## 6. 清洗原则

CleanCode 清洗必须遵循 **忠实、保守、可审计、可回退** 四个原则。程序和 LLM 都不得把 CleanCode 当作创作任务。

| 原则 | 要求 |
| --- | --- |
| 忠实 | 不新增原文不存在的知识点、解释、题目、答案或结论。 |
| 保守 | 不确定内容必须保留或进入 unresolved，不得静默删除。 |
| 可审计 | 每次删除、合并、移动或规范化都应在差异摘要或质量报告中可解释。 |
| 可回退 | CleanCode 必须保留 RawCode 输入路径和 hash，便于重新生成和比较。 |

## 7. 推荐处理流程

v0 处理流程采用“规则骨架 + LLM 清洗 + 程序验证”的混合架构。P0 pilot 可以先使用确定性清洗器模拟 LLM Cleaner 的输出合约；P0.1 在不改变本地、单章节、只读输入和不写生产存储边界的前提下，引入受控 LLM Cleaner 接口。

| 步骤 | 输入 | 输出 | 责任边界 |
| --- | --- | --- | --- |
| RawCode Builder | Popo/Luceon 产物 | RawCode Bundle | 只归一化结构，不做语义清洗。 |
| Chapter Chunker | `toc.json`、`full.md` 或 Popo 结构 | `chapters/*/raw.md` | 依据重建目录切块，并记录边界。 |
| Rule PreCleaner | `raw.md` | preclean Markdown | 只删除高置信噪音。 |
| LLM Cleaner | preclean Markdown、目录上下文、图片清单 | 结构化清洗结果 | 忠实整理，不允许创造内容。 |
| Rule PostProcessor | LLM 输出 | `clean.md` | 统一 Markdown 风格和图片路径。 |
| Validator | CleanCode 章节包 | `quality_report.json` | 检查图片、标题、覆盖率、疑似删除和风险。 |
| Assembler | 多章节 CleanCode | `full.md` | P1 后使用，P0 可只处理单章节。 |

## 8. LLM Cleaner 输出 schema

真实 LLM Cleaner 必须返回结构化 JSON，而不是自由 Markdown 文本。程序应校验 JSON 后再落盘。

```json
{
  "clean_markdown": "# Chapter 1\n\nClean content...",
  "kept_images": ["images/img_001.png"],
  "removed_noise": [
    {
      "text": "12",
      "reason": "isolated page number",
      "confidence": "high"
    }
  ],
  "unresolved_items": [
    {
      "type": "formula_or_ocr",
      "source_excerpt": "x = ?",
      "reason": "ambiguous OCR symbol",
      "suggested_action": "manual_review"
    }
  ],
  "change_summary": [
    "normalized heading levels",
    "fixed hard line breaks"
  ],
  "risk_flags": ["contains_formula", "contains_table"]
}
```

Prompt 中必须明确：LLM 只能清洗、纠错、整理和标准化 Markdown；不得总结、扩写、替换教材表达、删除可能属于正文的内容；遇到不确定内容必须写入 `unresolved_items`。

### 8.1 P0.1 受控 LLM 接口

P0.1 的核心变化是把原先的单体确定性 cleaner 拆成 **Rule PreCleaner → LLM Cleaner → Rule PostProcessor → Validator** 四段式流程。LLM Cleaner 只允许处理已经由 Rule PreCleaner 去除高置信版面噪音后的单章节 Markdown，并且必须返回第 8 节定义的结构化 JSON。程序不得直接把 LLM 返回文本当作最终 `clean.md`，而必须经过 JSON 校验、图片引用校验、后处理和本地验证后才能落盘。

| 接口项 | P0.1 规定 |
| --- | --- |
| 默认模式 | `dry-run` 或 `deterministic`，不调用外部模型。 |
| 显式 LLM 模式 | 只有在调用方显式传入 `--cleaner llm` 时才允许调用 LLM API。 |
| 输入粒度 | 单章节或单小节，不允许整本书一次性提交给 LLM。 |
| 输入内容 | `preclean_markdown`、`chapter_context`、`image_map`、`source_map_summary`、`constraints`。 |
| 输出格式 | 严格 JSON，字段必须符合第 8 节 schema。 |
| 失败处理 | JSON 不可解析、必要字段缺失、图片引用丢失或覆盖率异常时，状态必须降级为 `BLOCKED` 或 `NEEDS_REVIEW`。 |
| 审计要求 | `clean_manifest.json` 必须记录 cleaner mode、model、prompt hash、request hash、response hash、是否使用 LLM。 |
| 安全边界 | 仍然不写 DB、不写 MinIO、不触发主 worker、不修改 RawCode 输入目录。 |

LLM 请求载荷推荐采用如下机器可读结构。该结构应被嵌入 prompt 或作为 API message 的内容传递，以保证模型理解完整约束。

```json
{
  "protocol": "RawCode2CleanCode/v0",
  "task": "clean_single_chapter_markdown",
  "chapter_context": {
    "material_id": "sample-material",
    "chapter_id": "chapter_001",
    "title": "第一章 数与式",
    "toc_order": 1
  },
  "preclean_markdown": "# 第一章 数与式\n\n...",
  "image_map": {
    "allowed_refs": ["images/img_001.png"],
    "required_refs": ["images/img_001.png"]
  },
  "source_map_summary": {
    "page_range": [12, 13],
    "block_count": 20,
    "high_risk_blocks": []
  },
  "constraints": [
    "Do not summarize or rewrite as new textbook content.",
    "Do not remove any possible original content silently.",
    "Preserve all required image references.",
    "Return JSON only."
  ]
}
```

P0.1 的实现应支持三种 cleaner mode，以便在不同环境下稳定调试和回归测试。

| Cleaner mode | 是否调用 LLM | 用途 | 输出要求 |
| --- | --- | --- | --- |
| `deterministic` | 否 | 默认回归测试与无密钥环境验证。 | 使用规则模拟 LLM 输出 schema。 |
| `llm-dry-run` | 否 | 生成 prompt、request payload 和审计 hash，但不发送 API 请求。 | 产物状态可为 `NEEDS_REVIEW`，并保留 prompt 文件。 |
| `llm` | 是 | 单章节真实清洗实验。 | 必须通过 JSON schema、图片、覆盖率与质量验证。 |

在 P0.1 阶段，LLM 输出不应被默认信任。程序必须执行以下防护：第一，解析 JSON 并校验必需字段；第二，检查 `kept_images` 与 Markdown 图片引用是否均属于 `image_map` 的允许集合；第三，确认 required 图片未被静默删除；第四，对 raw 与 clean 的规范化文本长度、公式标记、题号和表格线索做粗粒度比较；第五，把所有不确定项写入 `unresolved_items.json`；第六，在 `diff.md` 中展示规则预清洗、LLM 清洗和规则后处理各自的变更摘要。

## 9. 验证规则

Validator 必须在本地执行，并生成 `quality_report.json`。v0 至少包含以下验证项。

| 验证项 | 方法 | 阻断条件 |
| --- | --- | --- |
| 文件存在性 | 检查 `clean.md`、`images/`、manifest、报告文件 | 必需文件缺失。 |
| Markdown 基础结构 | 检查标题、图片语法、空内容、异常控制字符 | `clean.md` 为空或明显不可解析。 |
| 图片引用完整 | 扫描 `![](...)` 并检查目标文件存在 | 任一图片引用不存在。 |
| 图片未被静默吞掉 | 比较 `image_map.json` 中 required 图片与 `clean.md` 引用 | required 图片消失且未进入 unresolved。 |
| 标题一致性 | 对照 `toc.json` 或 `chunk_manifest.json` | 章节主标题缺失或明显错位。 |
| 内容覆盖异常 | 比较 raw 与 clean 的规范化文本长度、题号和公式标记数量 | 大幅减少且未记录为噪音或 unresolved。 |
| 未解决项落盘 | 检查 LLM/规则报告的疑难项是否写入文件 | 风险项存在但 `unresolved_items.json` 缺失。 |

`quality_report.json` 的 `status` 字段只能取 `PASS`、`NEEDS_REVIEW` 或 `BLOCKED`。其中，`PASS` 表示可以进入下一步候选消费；`NEEDS_REVIEW` 表示可人工审阅但不应自动进入后续生产；`BLOCKED` 表示必须修正后重跑。

## 10. P0 Pilot 约束

P0 pilot 的目标是证明单章节闭环成立，而不是证明整书生产质量。它必须符合下列约束。

| 约束 | 说明 |
| --- | --- |
| 本地运行 | 只读入仓库 fixture 或本地输入，输出到本地目录。 |
| 不写生产依赖 | 不写 DB，不写 MinIO，不调用主 worker，不触发生产任务。 |
| 可重复 | 同一输入在 `deterministic` 和 `llm-dry-run` 模式下应产生稳定文件结构和可比较结果。 |
| 可审计 | 所有输出都应包含输入路径、hash、规则版本、cleaner mode、模型信息、prompt hash 和验证状态。 |
| 可扩展 | P0 的文件夹合约应能扩展到多章节和整书。 |

## 11. 推荐工程落点

v0 推荐先落地在 `scripts/rawcode2cleancode-pilot.mjs`，并在未来根据复杂度拆分到独立服务目录。

```text
scripts/rawcode2cleancode-pilot.mjs
server/services/rawcode2cleancode/
  contracts.mjs
  rawcode-builder.mjs
  chapter-chunker.mjs
  rule-precleaner.mjs
  llm-cleaner.mjs
  postprocessor.mjs
  validator.mjs
  assembler.mjs
```

P0 可以只实现脚本与内置 fixture 生成，P1 再将模块拆分到 `server/services/rawcode2cleancode/`。这样既能快速验证合约，又避免过早服务化带来的重构成本。

## 12. P0 成功标准

P0 通过的标准不是“内容已经出版级完美”，而是单章节闭环可以稳定产出符合协议的候选文件夹。

| 成功标准 | 验收方式 |
| --- | --- |
| 能生成 RawCode 章节样本 | `rawcode/{materialId}/v0/chapters/chapter_001/raw.md` 存在。 |
| 能生成 CleanCode 章节样本 | `cleancode/{materialId}/v0/chapters/chapter_001/clean.md` 存在。 |
| 图片引用完整 | `clean.md` 中所有图片路径存在。 |
| 质量报告完整 | `quality_report.json` 存在并包含 status、checks、metrics、risks。 |
| 未解决项透明 | `unresolved_items.json` 存在，即使为空也必须落盘。 |
| 差异可读 | `diff.md` 能说明主要清洗变化。 |
| 不触碰生产系统 | 执行过程不需要 DB、MinIO 或主 worker。 |

## 13. 后续版本演进

v0 聚焦单章节本地闭环；v1 可以引入真实 LLM API、更多输入适配器和更严格的内容覆盖校验；v2 再考虑多章节整书组装、人工审核界面和 CleanService/RawMaterial2CleanMaterial 的平台接入。

| 版本 | 范围 | 关键新增 |
| --- | --- | --- |
| v0 | 单章节本地 pilot | 文件夹合约、确定性清洗器、验证器、报告。 |
| P0.1 | 单章节受控 LLM pilot | 规则预清洗、LLM cleaner 接口、LLM dry-run、prompt/request/response 审计、规则后处理。 |
| v1 | 单材料多章节 | 批量 LLM API、章节间一致性、全书 `full.md`。 |
| v2 | 平台集成 | 服务化、对象存储、DB metadata、审核界面、回滚机制。 |

## 14. 与现有项目契约的关系

本协议不替代现有 CleanService 协议，而是为 RawMaterial2CleanMaterial 的内容清洗阶段提供更明确的 Markdown + images 中间层。现阶段应保持低耦合：RawCode2CleanCode 只消费上游已落盘产物，输出本地 CleanCode Bundle，不改变现有 CleanService worker、数据库结构或上传服务行为。

在 P0 成功后，可以再讨论是否将该阶段正式纳入 `server/services/rawmaterial2cleanmaterial/` 或独立为 `server/services/rawcode2cleancode/`。
