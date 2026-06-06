#!/usr/bin/env node

/**
 * RawCode2CleanCode P0.1 Pilot
 *
 * 该脚本实现 docs/contracts/RawCode2CleanCode-Protocol-v0.md 中定义的单章节本地闭环。
 * P0.1 将原先的确定性 cleaner 拆为四段式流程：
 *   1. Rule PreCleaner：只删除高置信版面噪音，并生成可审计变更记录。
 *   2. LLM Cleaner Interface：提供 deterministic、llm-dry-run、llm 三种受控模式。
 *   3. Rule PostProcessor：统一 Markdown 标题、空行、图片引用和基础格式。
 *   4. Validator：在本地检查图片、标题、覆盖率、未解决项和生产副作用。
 *
 * 安全边界：不写 DB，不写 MinIO，不触发主 worker，不修改 RawCode 输入目录。
 * 默认 cleaner 为 deterministic，不调用外部 LLM API。
 *
 * 运行方式：
 *   node scripts/rawcode2cleancode-pilot.mjs --fixture
 *   node scripts/rawcode2cleancode-pilot.mjs --fixture --cleaner llm-dry-run
 *   node scripts/rawcode2cleancode-pilot.mjs --input <rawcode-bundle-dir> --chapter-id chapter_001 --out <output-dir>
 *   node scripts/rawcode2cleancode-pilot.mjs --input <rawcode-bundle-dir> --chapter-id chapter_001 --cleaner llm --model <model>
 *
 * 输出内容：
 *   <out>/rawcode/<materialId>/v0/...       # 当使用 --fixture 时生成的样本输入
 *   <out>/cleancode/<materialId>/v0/...     # CleanCode 候选输出
 */

import { createHash } from 'node:crypto';
import {
  copyFile,
  mkdir,
  readFile,
  readdir,
  stat,
  writeFile,
} from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { basename, dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const PROTOCOL = 'RawCode2CleanCode/v0';
const DEFAULT_MATERIAL_ID = 'sample-material';
const DEFAULT_VERSION = 'v0';
const PILOT_VERSION = 'p0.1-controlled-llm-interface-2026-06-04';
const DEFAULT_CLEANER = 'deterministic';
const CLEANER_MODES = new Set(['deterministic', 'llm-dry-run', 'llm']);
const REQUIRED_LLM_MODEL = 'deepseek-v4-flash';
const DEFAULT_LLM_MODEL = REQUIRED_LLM_MODEL;
const DEFAULT_OPENAI_BASE = process.env.OPENAI_API_BASE || 'https://api.openai.com/v1';
const DEFAULT_LLM_REQUEST_TIMEOUT_MS = 180000;
const REVIEW_ITEMS_SCHEMA = 'luceon-cleancode-review-items/v1';
const REVIEW_PATCH_CONTRACT_SCHEMA = 'luceon-cleancode-review-patch-contract/v1';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const repoRoot = resolve(__dirname, '..');

function usage() {
  return [
    'Usage:',
    '  node scripts/rawcode2cleancode-pilot.mjs --fixture [--out <dir>] [--force] [--cleaner deterministic|llm-dry-run|llm] [--model <model>]',
    '  node scripts/rawcode2cleancode-pilot.mjs --input <rawcode-bundle-dir> [--chapter-id <id>] [--out <dir>] [--force] [--cleaner deterministic|llm-dry-run|llm] [--model <model>]',
    '',
    'Cleaner modes:',
    '  deterministic  Local deterministic schema-compatible cleaner. Default. No LLM API call.',
    '  llm-dry-run    Build prompt/request/audit files, but do not send API request.',
    '  llm            Send a single controlled chapter request to an OpenAI-compatible chat completions API.',
    '',
    'Boundaries:',
    '  This is a local P0.1 pilot only.',
    '  It does not write DB, does not write MinIO, and does not call runtime workers.',
    '  LLM calls are disabled unless --cleaner llm is explicitly provided.',
    `  LLM cleaner model is locked to ${REQUIRED_LLM_MODEL}; any other --model is rejected.`,
  ].join('\n');
}

function requiresLlmModelGuard(cleanerMode) {
  return cleanerMode === 'llm' || cleanerMode === 'llm-dry-run';
}

function assertAllowedLlmModel({ cleanerMode, model }) {
  if (!requiresLlmModelGuard(cleanerMode)) return;
  if (model !== REQUIRED_LLM_MODEL) {
    throw new Error(`RawCode2CleanCode LLM cleaner model is locked to ${REQUIRED_LLM_MODEL}; received ${model || '<empty>'}`);
  }
}

function parseArgs(argv) {
  const args = {
    input: null,
    chapterId: null,
    out: join(repoRoot, '.tmp', 'rawcode2cleancode-pilot'),
    fixture: false,
    force: false,
    help: false,
    cleaner: DEFAULT_CLEANER,
    model: DEFAULT_LLM_MODEL,
    apiBase: DEFAULT_OPENAI_BASE,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    const next = () => {
      index += 1;
      if (index >= argv.length) throw new Error(`missing value for ${arg}`);
      return argv[index];
    };

    if (arg === '--help' || arg === '-h') {
      args.help = true;
    } else if (arg === '--fixture') {
      args.fixture = true;
    } else if (arg === '--input') {
      args.input = next();
    } else if (arg === '--chapter-id') {
      args.chapterId = next();
    } else if (arg === '--out') {
      args.out = next();
    } else if (arg === '--force') {
      args.force = true;
    } else if (arg === '--cleaner') {
      args.cleaner = next();
    } else if (arg === '--model') {
      args.model = next();
    } else if (arg === '--api-base') {
      args.apiBase = next();
    } else {
      throw new Error(`unknown argument: ${arg}`);
    }
  }

  if (!CLEANER_MODES.has(args.cleaner)) {
    throw new Error(`invalid --cleaner ${args.cleaner}; expected one of ${Array.from(CLEANER_MODES).join(', ')}`);
  }

  assertAllowedLlmModel({ cleanerMode: args.cleaner, model: args.model });

  if (!args.fixture && !args.input) {
    args.fixture = true;
  }

  if (args.fixture && args.input) {
    throw new Error('--fixture and --input cannot be used together');
  }

  return args;
}

function stableJson(value) {
  return `${JSON.stringify(value, null, 2)}\n`;
}

function sha256Buffer(buffer) {
  return createHash('sha256').update(buffer).digest('hex');
}

function sha256Text(text) {
  return createHash('sha256').update(text).digest('hex');
}

function nowIso() {
  return new Date().toISOString();
}

async function ensureDir(path) {
  await mkdir(path, { recursive: true });
}

async function writeJson(path, value) {
  await ensureDir(dirname(path));
  await writeFile(path, stableJson(value), 'utf8');
}

async function writeText(path, text) {
  await ensureDir(dirname(path));
  await writeFile(path, text.endsWith('\n') ? text : `${text}\n`, 'utf8');
}

async function readJson(path) {
  return JSON.parse(await readFile(path, 'utf8'));
}

function normalizeSlashes(path) {
  return String(path || '').replace(/\\/g, '/');
}

function normalizeTextForMetric(text) {
  return String(text || '')
    .replace(/!\[[^\]]*\]\([^)]*\)/g, '')
    .replace(/[`*_#>\-\[\](){}$\\]/g, '')
    .replace(/\s+/g, '')
    .trim();
}

function normalizeHeadingText(text) {
  return normalizeTextForMetric(String(text || '')
    .replace(/^#{1,6}\s+/, '')
    .replace(/^#+\s*$/, '')
    .replace(/^<!--\s*.*?\s*-->\s*$/, ''));
}

function uniqueStrings(values) {
  return Array.from(new Set((values || []).map((value) => String(value || '').trim()).filter(Boolean)));
}

function extractMarkdownImages(markdown) {
  const refs = [];
  const regex = /!\[([^\]]*)\]\(([^)\s]+)(?:\s+"[^"]*")?\)/g;
  let match;
  while ((match = regex.exec(markdown)) !== null) {
    refs.push({
      alt: match[1] || '',
      ref: normalizeSlashes(match[2] || ''),
      raw: match[0],
    });
  }
  return refs;
}

function escapeRegExp(text) {
  return String(text).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function buildImageMapLookup(imageMap) {
  const lookup = new Map();
  for (const image of imageMap.images || []) {
    const rawRef = normalizeSlashes(image.raw_ref);
    const normalizedRef = normalizeSlashes(image.normalized_ref || image.raw_ref);
    if (rawRef) lookup.set(rawRef, normalizedRef);
    if (normalizedRef) lookup.set(normalizedRef, normalizedRef);
  }
  return lookup;
}

function normalizeImageRefs(markdown, imageMap) {
  let output = markdown;
  const lookup = buildImageMapLookup(imageMap);
  const changes = [];
  const imageBySourceBlock = new Map();
  for (const image of imageMap.images || []) {
    const normalizedRef = normalizeSlashes(image.normalized_ref || image.raw_ref);
    if (!normalizedRef) continue;
    for (const sourceBlockId of image.source_block_ids || []) {
      imageBySourceBlock.set(String(sourceBlockId), normalizedRef);
    }
  }

  for (const [rawRef, normalizedRef] of lookup.entries()) {
    if (!rawRef || !normalizedRef || rawRef === normalizedRef) continue;
    const before = output;
    output = output.replace(
      new RegExp(`(!\\[[^\\]]*\\]\\()${escapeRegExp(rawRef)}(\\))`, 'g'),
      `$1${normalizedRef}$2`,
    );
    if (before !== output) {
      changes.push({ type: 'image_ref_normalized', from: rawRef, to: normalizedRef });
    }
  }

  output = output.replace(/!\[([^\]]*)\]\(([^)\s]+)((?:\s+"[^"]*")?)\)/g, (match, alt, ref, titleSuffix) => {
    const sourceBlockMatch = String(alt || '').match(/\bsource_block=([^,\s\]]+)/);
    const sourceBlockId = sourceBlockMatch ? sourceBlockMatch[1] : null;
    const normalizedRef = sourceBlockId ? imageBySourceBlock.get(sourceBlockId) : null;
    const currentRef = normalizeSlashes(ref);
    if (!normalizedRef || currentRef === normalizedRef) return match;
    changes.push({
      type: 'image_ref_restored_from_source_block',
      source_block_id: sourceBlockId,
      from: currentRef,
      to: normalizedRef,
    });
    return `![${alt}](${normalizedRef}${titleSuffix || ''})`;
  });

  return { markdown: output, changes };
}

function summarizeSourceMap(sourceMap) {
  const blocks = sourceMap.source_blocks || [];
  const pages = blocks.map((block) => Number(block.page)).filter((page) => Number.isFinite(page));
  const highRiskBlocks = blocks
    .filter((block) => /formula|table|image|ambiguous|ocr/i.test(`${block.type || ''} ${block.text || ''}`))
    .slice(0, 20)
    .map((block) => ({ block_id: block.block_id, page: block.page, type: block.type, text: String(block.text || '').slice(0, 160) }));

  return {
    page_range: pages.length > 0 ? [Math.min(...pages), Math.max(...pages)] : null,
    block_count: blocks.length,
    high_risk_blocks: highRiskBlocks,
  };
}

function requiredImageRefs(imageMap) {
  return (imageMap.images || [])
    .filter((image) => image.required === true)
    .map((image) => normalizeSlashes(image.normalized_ref || image.raw_ref))
    .filter(Boolean);
}

function markdownCommentValue(value) {
  return String(value ?? '')
    .replace(/-->/g, '-- >')
    .replace(/\r?\n/g, ' ')
    .trim();
}

function visualBlockCommentForImage(image, markdownImage) {
  const ref = normalizeSlashes(image?.normalized_ref || image?.raw_ref || markdownImage?.ref || '');
  const sourceBlockIds = Array.isArray(image?.source_block_ids)
    ? image.source_block_ids.map(String).filter(Boolean)
    : [];
  const linkedSourceBlockIds = Array.isArray(image?.linked_source_block_ids)
    ? image.linked_source_block_ids.map(String).filter(Boolean)
    : [];
  const altText = String(markdownImage?.alt || '').toLowerCase();
  const kindFromImage = String(image?.asset_kind || image?.kind || image?.type || '').toLowerCase();
  const kind = kindFromImage.includes('table') || altText.includes('table') ? 'table' : 'image';
  const sourcePage = image?.source_page ?? image?.page ?? '';
  const bbox = Array.isArray(image?.bbox) ? image.bbox : [];
  const assetHash = image?.asset_hash_name || basename(ref);
  return `<!-- luceon:visual_block type=${kind} source_block_ids=${markdownCommentValue(sourceBlockIds.join(','))} page=${markdownCommentValue(sourcePage)} bbox=${markdownCommentValue(JSON.stringify(bbox))} asset_hash=${markdownCommentValue(assetHash)} linked_source_block_ids=${markdownCommentValue(linkedSourceBlockIds.join(','))} -->`;
}

function restoreVisualBlockComments(markdown, imageMap) {
  const imageByRef = new Map();
  for (const image of imageMap.images || []) {
    const rawRef = normalizeSlashes(image.raw_ref);
    const normalizedRef = normalizeSlashes(image.normalized_ref || image.raw_ref);
    if (rawRef) imageByRef.set(rawRef, image);
    if (normalizedRef) imageByRef.set(normalizedRef, image);
    if (normalizedRef) imageByRef.set(`images/${basename(normalizedRef)}`, image);
  }
  if (imageByRef.size === 0) return { markdown, inserted: 0 };

  const lines = String(markdown || '').replace(/\r\n?/g, '\n').split('\n');
  const output = [];
  let inserted = 0;
  const imageLineRegex = /^(\s*)!\[([^\]]*)\]\(([^)\s]+)(?:\s+"[^"]*")?\)\s*$/;

  for (const line of lines) {
    const match = imageLineRegex.exec(line);
    if (!match) {
      output.push(line);
      continue;
    }
    const markdownImage = {
      alt: match[2] || '',
      ref: normalizeSlashes(match[3] || ''),
      raw: line,
    };
    const image = imageByRef.get(markdownImage.ref);
    if (!image) {
      output.push(line);
      continue;
    }
    const previous = output[output.length - 1] || '';
    const previousHasComment = previous.includes('luceon:visual_block') && previous.includes(image.asset_hash_name || basename(markdownImage.ref));
    if (!previousHasComment) {
      output.push(`${match[1] || ''}${visualBlockCommentForImage(image, markdownImage)}`);
      inserted += 1;
    }
    output.push(line);
  }

  return { markdown: output.join('\n'), inserted };
}

function allowedImageRefs(imageMap) {
  const refs = new Set();
  for (const image of imageMap.images || []) {
    if (image.raw_ref) refs.add(normalizeSlashes(image.raw_ref));
    if (image.normalized_ref) refs.add(normalizeSlashes(image.normalized_ref));
    if (image.normalized_ref) refs.add(`images/${basename(image.normalized_ref)}`);
  }
  return Array.from(refs).filter(Boolean).sort();
}

function stripLuceonMetadataComments(markdown) {
  const removed = [];
  const lines = String(markdown || '').replace(/\r\n?/g, '\n').split('\n');
  const kept = [];
  for (const line of lines) {
    if (/^\s*<!--\s*luceon:/i.test(line)) {
      removed.push(line.trim());
      continue;
    }
    kept.push(line);
  }
  return {
    markdown: kept.join('\n'),
    removed,
  };
}

function normalizeOpeningHeadings(markdown, chapterTitle) {
  const lines = String(markdown || '').replace(/\r\n?/g, '\n').split('\n');
  const output = [];
  const removed = [];
  const seenOpeningTitles = new Set();
  let nonBlankSeen = 0;
  const expectedTitleKey = normalizeHeadingText(chapterTitle || '');

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) {
      output.push(line);
      continue;
    }
    nonBlankSeen += 1;
    const headingMatch = /^(#{1,6})\s+(.+?)\s*$/.exec(trimmed);
    const candidateTitle = headingMatch ? headingMatch[2] : trimmed;
    const candidateKey = normalizeHeadingText(candidateTitle);
    const isOpeningWindow = nonBlankSeen <= 4;
    const isDuplicateOpeningTitle = isOpeningWindow
      && candidateKey
      && (seenOpeningTitles.has(candidateKey) || (expectedTitleKey && candidateKey === expectedTitleKey && seenOpeningTitles.size > 0));
    const isBareTitleAfterHeading = isOpeningWindow && !headingMatch && candidateKey && seenOpeningTitles.has(candidateKey);

    if (isDuplicateOpeningTitle || isBareTitleAfterHeading) {
      removed.push(line);
      continue;
    }

    if (isOpeningWindow && candidateKey) {
      seenOpeningTitles.add(candidateKey);
    }
    output.push(line);
  }

  return {
    markdown: output.join('\n'),
    removed,
  };
}

function rulePreClean(rawMarkdown) {
  const removedNoise = [];
  const changes = [];
  let normalizedMarkdown = String(rawMarkdown || '').replace(/\r\n?/g, '\n');
  const strippedMetadata = stripLuceonMetadataComments(normalizedMarkdown);
  normalizedMarkdown = strippedMetadata.markdown;
  if (strippedMetadata.removed.length > 0) {
    changes.push({ type: 'removed_luceon_trace_metadata_comments', count: strippedMetadata.removed.length });
  }
  if (/<\|txt_split\|>|<\|txt_contd\|>/.test(normalizedMarkdown)) {
    normalizedMarkdown = normalizedMarkdown
      .replace(/<\|txt_split\|>/g, '\n\n')
      .replace(/<\|txt_contd\|>/g, ' ');
    changes.push({ type: 'normalized_popo_text_separators' });
  }
  const lines = normalizedMarkdown.split('\n');
  const kept = [];
  let previousBlank = false;

  for (const originalLine of lines) {
    const line = originalLine.replace(/[ \t]+$/g, '');
    const trimmed = line.trim();

    const isPageNumber = /^第?\s*\d+\s*(页)?$/i.test(trimmed);
    const isPageNoise = /^(page|p\.)\s*\d+$/i.test(trimmed);
    const isHeaderNoise = /^(扫描件页眉|OCR HEADER|页眉)[:：]/i.test(trimmed);
    const isFooterNoise = /^(扫描件页脚|OCR FOOTER|页脚)[:：]/i.test(trimmed);
    const isRuleNoise = /^[-—_]{3,}$/.test(trimmed);

    if (trimmed && (isPageNumber || isPageNoise || isHeaderNoise || isFooterNoise || isRuleNoise)) {
      removedNoise.push({ text: trimmed, reason: 'high-confidence layout noise', confidence: 'high' });
      continue;
    }

    if (!trimmed) {
      if (!previousBlank) kept.push('');
      previousBlank = true;
      continue;
    }

    previousBlank = false;
    const normalizedLine = line.replace(/[ \t]{2,}/g, ' ');
    if (normalizedLine !== line) {
      changes.push({ type: 'collapsed_inline_spaces', before: line, after: normalizedLine });
    }
    kept.push(normalizedLine);
  }

  if (removedNoise.length > 0) changes.push({ type: 'removed_high_confidence_noise_lines', count: removedNoise.length });

  return {
    markdown: `${kept.join('\n').trim()}\n`,
    removedNoise,
    changes,
  };
}

function buildCleanerRequest({ materialId, version, chapterId, chapterTitle, toc, sourceMap, imageMap, chunkManifest, precleanMarkdown, inputMarkdownRole }) {
  const tocNode = (toc.nodes || []).find((node) => node.id === chapterId) || null;
  return {
    protocol: PROTOCOL,
    task: 'clean_structure_locked_markdown_unit',
    chapter_context: {
      material_id: materialId,
      version,
      chapter_id: chapterId,
      title: chapterTitle,
      toc_order: tocNode?.order ?? null,
      toc_level: tocNode?.level ?? null,
      unit_path: tocNode?.unit_path ?? null,
      raw_preview_path: tocNode?.raw_path ?? null,
    },
    input_markdown_role: inputMarkdownRole || 'unit_markdown',
    preclean_markdown: precleanMarkdown,
    image_map: {
      allowed_refs: allowedImageRefs(imageMap),
      required_refs: requiredImageRefs(imageMap),
      declared_images: (imageMap.images || []).map((image) => ({
        asset_hash_name: image.asset_hash_name || basename(image.normalized_ref || image.raw_ref || ''),
        normalized_ref: image.normalized_ref || image.raw_ref || null,
        source_page: image.source_page ?? null,
        source_block_ids: Array.isArray(image.source_block_ids) ? image.source_block_ids : [],
        required: image.required === true,
      })),
      visual_evidence_requirements: Array.isArray(imageMap.visual_evidence_requirements)
        ? imageMap.visual_evidence_requirements
        : [],
    },
    source_map_summary: summarizeSourceMap(sourceMap),
    structure_lock: {
      source: 'upstream canonical_toc and cleaning_unit_pack',
      unit_id: chapterId,
      pack_id: chunkManifest?.pack_id || null,
      title: chapterTitle,
      node: chunkManifest?.node || null,
      boundary: chunkManifest?.boundary || null,
      source_span: chunkManifest?.source_span || null,
      llm_must_not_create_or_delete_book_structure: true,
      llm_must_not_change_heading_hierarchy: true,
      llm_must_not_move_content_outside_this_unit: true,
    },
    constraints: [
      'Return JSON only; do not wrap it in Markdown fences.',
      'Clean, correct, organize, and standardize only the provided structure-locked Markdown unit.',
      'The unit already carries the upstream canonical TOC structure; do not create, delete, promote, demote, or rename book-structure headings.',
      'Do not decide chapter/section/exercise boundaries. Preserve the existing unit boundary.',
      'Do not summarize, expand, translate, or rewrite as new textbook content.',
      'Do not silently remove any possible original content.',
      'Preserve all required image references exactly in Markdown.',
      'For visual evidence requirements, either preserve the linked image reference exactly or report the issue in unresolved_items.',
      'Move uncertain content to unresolved_items instead of deleting it.',
      'Keep educational content, questions, formulas, tables, captions, and examples faithful to the source.',
      'Escape Markdown and LaTeX backslashes as valid JSON string characters; never emit raw invalid JSON escapes such as \\p, \\s, or \\c.',
    ],
    expected_response_schema: {
      clean_markdown: 'string',
      kept_images: ['images/img_001.png'],
      removed_noise: [{ text: 'string', reason: 'string', confidence: 'high|medium|low' }],
      unresolved_items: [{ type: 'string', source_excerpt: 'string', reason: 'string', suggested_action: 'manual_review' }],
      change_summary: ['string'],
      risk_flags: ['contains_formula|contains_table|contains_ambiguous_ocr'],
    },
  };
}

function buildCleanerPrompt(requestPayload) {
  return [
    'You are the RawCode2CleanCode LLM Cleaner for a single structure-locked textbook unit.',
    '',
    'Your task is constrained content cleaning, not content creation and not TOC generation.',
    'The Markdown input is already cut by the upstream canonical table of contents.',
    'Do not change the unit boundary, heading hierarchy, parent path, or source scope.',
    'You must preserve the original meaning, order, examples, formulas, image references, and educational intent.',
    'Do not summarize. Do not add new explanations. Do not remove possible source content silently.',
    'If uncertain, keep the content and add an unresolved item.',
    '',
    'Return JSON only. The JSON must match the expected_response_schema in the request payload.',
    '',
    'REQUEST_PAYLOAD:',
    JSON.stringify(requestPayload, null, 2),
  ].join('\n');
}

function deterministicSchemaCleaner({ precleanMarkdown, chapterTitle, imageMap, mode }) {
  const normalizedImages = normalizeImageRefs(precleanMarkdown, imageMap);
  let markdown = normalizedImages.markdown;
  const changeSummary = [];
  const unresolvedItems = [];
  const riskFlags = [];

  if (!/^#\s+/m.test(markdown) && chapterTitle) {
    markdown = `# ${chapterTitle}\n\n${markdown}`;
    changeSummary.push('inserted chapter heading from chunk_manifest or toc');
  }

  if (normalizedImages.changes.length > 0) {
    changeSummary.push(`normalized ${normalizedImages.changes.length} image reference(s)`);
  }

  if (/\$[^$]+\$|\\\(|\\\[/.test(markdown)) riskFlags.push('contains_formula');
  if (/\|\s*[-:]+\s*\|/.test(markdown)) riskFlags.push('contains_table');
  if (/OCR_UNCERTAIN|无法辨认|[?？]{2,}/i.test(markdown)) {
    riskFlags.push('contains_ambiguous_ocr');
    unresolvedItems.push({
      type: 'ambiguous_ocr',
      source_excerpt: 'detected OCR_UNCERTAIN / repeated question marks / ambiguous marker',
      reason: 'pilot cannot safely resolve ambiguous OCR text',
      suggested_action: 'manual_review',
    });
  }

  if (mode === 'llm-dry-run') {
    riskFlags.push('llm_dry_run_no_model_response');
    changeSummary.push('llm-dry-run generated prompt and request payload without sending API request');
    unresolvedItems.push({
      type: 'llm_not_called',
      source_excerpt: chapterTitle || 'chapter',
      reason: 'llm-dry-run mode does not produce a real model-cleaned response',
      suggested_action: 'run_with_cleaner_llm_or_manual_review',
    });
  } else {
    changeSummary.push('deterministic cleaner simulated LLM output schema');
  }

  return {
    clean_markdown: markdown,
    kept_images: extractMarkdownImages(markdown).map((item) => item.ref),
    removed_noise: [],
    unresolved_items: unresolvedItems,
    change_summary: changeSummary,
    risk_flags: riskFlags,
    _internal_image_ref_changes: normalizedImages.changes,
  };
}

function stripJsonFences(text) {
  const trimmed = String(text || '').trim();
  const fenceMatch = trimmed.match(/^```(?:json)?\s*([\s\S]*?)\s*```$/i);
  return fenceMatch ? fenceMatch[1].trim() : trimmed;
}

function parseLooseJson(text) {
  const stripped = stripJsonFences(text);
  const candidates = [];
  const balanced = extractFirstBalancedJsonObject(stripped);
  if (balanced) candidates.push(balanced);
  candidates.push(stripped);

  const start = stripped.indexOf('{');
  const end = stripped.lastIndexOf('}');
  if (start >= 0 && end > start) candidates.push(stripped.slice(start, end + 1));

  let firstError = null;
  for (const candidate of candidates) {
    try {
      return JSON.parse(candidate);
    } catch (error) {
      if (!firstError) firstError = error;
      try {
        return JSON.parse(repairLooseJsonText(candidate));
      } catch {
        // Try the next candidate. The original error is reported if none work.
      }
    }
  }

  throw firstError || new Error('No JSON object found in model content');
}

function extractFirstBalancedJsonObject(text) {
  const source = String(text || '');
  const start = source.indexOf('{');
  if (start < 0) return null;

  let depth = 0;
  let inString = false;
  let escaped = false;
  for (let index = start; index < source.length; index += 1) {
    const char = source[index];
    if (inString) {
      if (escaped) {
        escaped = false;
      } else if (char === '\\') {
        escaped = true;
      } else if (char === '"') {
        inString = false;
      }
      continue;
    }

    if (char === '"') {
      inString = true;
    } else if (char === '{') {
      depth += 1;
    } else if (char === '}') {
      depth -= 1;
      if (depth === 0) return source.slice(start, index + 1);
    }
  }

  return null;
}

function isRetryableLlmError(error) {
  const message = String(error?.message || error || '');
  return /timed out|terminated|ECONNRESET|ETIMEDOUT|fetch failed|JSON parse failed|Unterminated string|Bad control character|Unexpected non-whitespace|Expected ','|Expected '}'|Expected ']'/i.test(message);
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function repairLooseJsonText(text) {
  return removeInvalidParentheticalAfterStringValues(escapeControlCharactersInJsonStrings(repairJsonStringEscapes(text)));
}

function escapeControlCharactersInJsonStrings(text) {
  const source = String(text || '');
  let output = '';
  let inString = false;
  let escaped = false;

  for (let index = 0; index < source.length; index += 1) {
    const char = source[index];
    if (!inString) {
      output += char;
      if (char === '"') inString = true;
      continue;
    }

    if (escaped) {
      output += char;
      escaped = false;
      continue;
    }

    if (char === '\\') {
      output += char;
      escaped = true;
    } else if (char === '"') {
      output += char;
      inString = false;
    } else if (char === '\n') {
      output += '\\n';
    } else if (char === '\r') {
      output += '\\r';
    } else if (char === '\t') {
      output += '\\t';
    } else {
      const code = char.charCodeAt(0);
      output += code < 0x20 ? `\\u${code.toString(16).padStart(4, '0')}` : char;
    }
  }

  return output;
}

function removeInvalidParentheticalAfterStringValues(text) {
  const source = String(text || '');
  let output = '';
  let index = 0;
  let inString = false;
  let escaped = false;
  let lastSignificant = '';

  while (index < source.length) {
    const char = source[index];
    output += char;

    if (inString) {
      if (escaped) {
        escaped = false;
      } else if (char === '\\') {
        escaped = true;
      } else if (char === '"') {
        inString = false;
        let cursor = index + 1;
        while (/\s/.test(source[cursor] || '')) cursor += 1;
        if (lastSignificant === ':' && source[cursor] === '(') {
          let depth = 0;
          let end = cursor;
          let parenInString = false;
          let parenEscaped = false;
          while (end < source.length) {
            const next = source[end];
            if (parenInString) {
              if (parenEscaped) {
                parenEscaped = false;
              } else if (next === '\\') {
                parenEscaped = true;
              } else if (next === '"') {
                parenInString = false;
              }
              end += 1;
              continue;
            }
            if (next === '"') {
              parenInString = true;
              end += 1;
              continue;
            }
            if (next === '(') depth += 1;
            if (next === ')') {
              depth -= 1;
              if (depth === 0) {
                end += 1;
                break;
              }
            }
            end += 1;
          }
          let after = end;
          while (/\s/.test(source[after] || '')) after += 1;
          if (depth === 0 && /[,}\]]/.test(source[after] || '')) {
            index = end - 1;
          }
        }
      }
      index += 1;
      continue;
    }

    if (char === '"') {
      inString = true;
      escaped = false;
    } else if (!/\s/.test(char)) {
      lastSignificant = char;
    }
    index += 1;
  }

  return output;
}

function repairJsonStringEscapes(text) {
  const source = String(text || '');
  let output = '';
  let inString = false;

  for (let index = 0; index < source.length; index += 1) {
    const char = source[index];
    if (char === '"') {
      output += char;
      inString = !inString;
      continue;
    }
    if (!inString || char !== '\\') {
      output += char;
      continue;
    }

    let end = index;
    while (source[end] === '\\') end += 1;
    const run = source.slice(index, end);
    const next = source[end] || '';
    const nextIsValidJsonEscape = /["\\/bfnrtu]/.test(next);
    if (!nextIsValidJsonEscape && run.length % 2 === 1) {
      output += `${run}\\`;
      index = end - 1;
    } else if (nextIsValidJsonEscape && run.length % 2 === 1) {
      output += `${run}${next}`;
      index = end;
    } else {
      output += run;
      index = end - 1;
    }
  }

  return output;
}

function normalizeCleanerResponse(value) {
  const response = value || {};
  const cleanMarkdown = typeof response.clean_markdown === 'string'
    ? response.clean_markdown
    : typeof response.cleanMarkdown === 'string'
      ? response.cleanMarkdown
      : null;

  const normalized = {
    clean_markdown: cleanMarkdown,
    kept_images: Array.isArray(response.kept_images) ? response.kept_images.map(normalizeSlashes) : [],
    removed_noise: Array.isArray(response.removed_noise) ? response.removed_noise : [],
    unresolved_items: Array.isArray(response.unresolved_items) ? response.unresolved_items : [],
    change_summary: Array.isArray(response.change_summary) ? response.change_summary.map(String) : [],
    risk_flags: Array.isArray(response.risk_flags) ? response.risk_flags.map(String) : [],
    _internal_image_ref_changes: Array.isArray(response._internal_image_ref_changes) ? response._internal_image_ref_changes : [],
  };

  const errors = [];
  if (typeof normalized.clean_markdown !== 'string' || normalized.clean_markdown.trim().length === 0) {
    errors.push('clean_markdown must be a non-empty string');
  }
  for (const key of ['kept_images', 'removed_noise', 'unresolved_items', 'change_summary', 'risk_flags']) {
    if (!Array.isArray(normalized[key])) errors.push(`${key} must be an array`);
  }

  return { response: normalized, errors };
}

async function callLLMCleaner({ apiBase, model, prompt }) {
  assertAllowedLlmModel({ cleanerMode: 'llm', model });
  if (!process.env.OPENAI_API_KEY) {
    throw new Error('--cleaner llm requires OPENAI_API_KEY in environment');
  }

  const endpoint = `${String(apiBase || DEFAULT_OPENAI_BASE).replace(/\/$/, '')}/chat/completions`;
  const body = {
    model,
    temperature: 0,
    response_format: { type: 'json_object' },
    messages: [
      {
        role: 'system',
        content: 'You are a constrained textbook Markdown cleaning engine. Return valid JSON only.',
      },
      { role: 'user', content: prompt },
    ],
  };

  const timeoutMs = Number(process.env.RAWCODE2CLEANCODE_LLM_TIMEOUT_MS || DEFAULT_LLM_REQUEST_TIMEOUT_MS);
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), Number.isFinite(timeoutMs) && timeoutMs > 0 ? timeoutMs : DEFAULT_LLM_REQUEST_TIMEOUT_MS);
  let response;
  try {
    response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${process.env.OPENAI_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
  } catch (error) {
    if (controller.signal.aborted) {
      throw new Error(`LLM API request timed out after ${timeoutMs}ms`);
    }
    throw error;
  } finally {
    clearTimeout(timeout);
  }

  const responseText = await response.text();
  if (!response.ok) {
    throw new Error(`LLM API request failed with ${response.status}: ${responseText.slice(0, 800)}`);
  }

  const parsed = JSON.parse(responseText);
  const content = parsed.choices?.[0]?.message?.content;
  if (!content) {
    throw new Error('LLM API response missing choices[0].message.content');
  }

  return {
    api_response: parsed,
    content,
    parsed_content: null,
  };
}

async function runCleanerStage({
  mode,
  model,
  apiBase,
  materialId,
  version,
  chapterId,
  chapterTitle,
  toc,
  sourceMap,
  imageMap,
  chunkManifest,
  precleanMarkdown,
  inputMarkdownRole,
  auditDir,
}) {
  const requestPayload = buildCleanerRequest({
    materialId,
    version,
    chapterId,
    chapterTitle,
    toc,
    sourceMap,
    imageMap,
    chunkManifest,
    precleanMarkdown,
    inputMarkdownRole,
  });
  const prompt = buildCleanerPrompt(requestPayload);
  const requestJson = stableJson(requestPayload);
  const promptHash = sha256Text(prompt);
  const requestHash = sha256Text(requestJson);
  const audit = {
    prompt_hash: promptHash,
    request_hash: requestHash,
    response_hash: null,
    prompt_path: null,
    request_path: null,
    response_path: null,
    raw_api_response_path: null,
    raw_model_content_path: null,
  };

  if (mode === 'llm-dry-run' || mode === 'llm') {
    await ensureDir(auditDir);
    audit.prompt_path = join(auditDir, 'llm_prompt.txt');
    audit.request_path = join(auditDir, 'llm_request.json');
    await writeText(audit.prompt_path, prompt);
    await writeJson(audit.request_path, requestPayload);
  }

  let rawResponse;
  let llmUsed = false;
  let apiResponse = null;

  if (mode === 'llm') {
    llmUsed = true;
    const maxAttempts = 2;
    const errors = [];
    for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
      try {
        const llmResult = await callLLMCleaner({ apiBase, model, prompt });
        apiResponse = llmResult.api_response;
        audit.raw_api_response_path = join(auditDir, attempt === 1 ? 'llm_raw_api_response.json' : `llm_raw_api_response_attempt_${attempt}.json`);
        audit.raw_model_content_path = join(auditDir, attempt === 1 ? 'llm_raw_model_content.txt' : `llm_raw_model_content_attempt_${attempt}.txt`);
        await writeJson(audit.raw_api_response_path, apiResponse);
        await writeText(audit.raw_model_content_path, llmResult.content);
        rawResponse = llmResult.parsed_content || parseLooseJson(llmResult.content);
        if (attempt > 1) {
          audit.retry_attempts = attempt - 1;
          audit.retry_errors = errors;
        }
        break;
      } catch (error) {
        errors.push(String(error?.message || error));
        if (attempt >= maxAttempts || !isRetryableLlmError(error)) {
          throw new Error(`LLM content JSON parse failed: ${errors.join(' | ')}; raw_model_content_path=${audit.raw_model_content_path}`);
        }
        await sleep(750 * attempt);
      }
    }
  } else {
    rawResponse = deterministicSchemaCleaner({ precleanMarkdown, chapterTitle, imageMap, mode });
  }

  const normalized = normalizeCleanerResponse(rawResponse);
  if (normalized.errors.length > 0) {
    normalized.response.unresolved_items.push({
      type: 'llm_schema_error',
      source_excerpt: chapterTitle || chapterId,
      reason: normalized.errors.join('; '),
      suggested_action: 'fix_prompt_or_manual_review',
    });
    normalized.response.risk_flags.push('llm_schema_error');
  }

  const responseJson = stableJson(normalized.response);
  audit.response_hash = sha256Text(responseJson);

  if (mode === 'llm-dry-run' || mode === 'llm') {
    audit.response_path = join(auditDir, mode === 'llm-dry-run' ? 'llm_dry_run_response.json' : 'llm_response.json');
    await writeJson(audit.response_path, normalized.response);
    if (apiResponse && !audit.raw_api_response_path) {
      audit.raw_api_response_path = join(auditDir, 'llm_raw_api_response.json');
      await writeJson(audit.raw_api_response_path, apiResponse);
    }
  }

  return {
    mode,
    model: mode === 'llm' ? model : null,
    llmUsed,
    requestPayload,
    prompt,
    response: normalized.response,
    schemaErrors: normalized.errors,
    audit,
  };
}

function rulePostProcess({ llmResponse, chapterTitle, imageMap }) {
  let clean = llmResponse.clean_markdown || '';
  const strippedMetadata = stripLuceonMetadataComments(clean);
  clean = strippedMetadata.markdown;
  const normalizedImages = normalizeImageRefs(clean, imageMap);
  clean = normalizedImages.markdown;

  const changeSummary = [...(llmResponse.change_summary || [])];
  const riskFlags = new Set(llmResponse.risk_flags || []);
  const unresolvedItems = [...(llmResponse.unresolved_items || [])];
  if (strippedMetadata.removed.length > 0) {
    changeSummary.push(`postprocessor removed ${strippedMetadata.removed.length} Luceon trace metadata comment(s) from reader-facing CleanCode`);
  }

  if (!/^#\s+/m.test(clean) && chapterTitle) {
    clean = `# ${chapterTitle}\n\n${clean}`;
    changeSummary.push('postprocessor inserted chapter heading from chunk_manifest or toc');
  }

  clean = clean
    .replace(/\r\n?/g, '\n')
    .replace(/[ \t]+$/gm, '')
    .replace(/\n{3,}/g, '\n\n')
    .replace(/([^\n])\n(#{1,6}\s+)/g, '$1\n\n$2')
    .replace(/^(#{1,6}\s+[^\n]+)\n(?!\n)/gm, '$1\n\n')
    .replace(/\[\s*\]/g, '[ ]')
    .trim();

  const cleanRefs = new Set(extractMarkdownImages(clean).map((item) => normalizeSlashes(item.ref)));
  const missingRequiredImages = requiredImageRefs(imageMap).filter((ref) => !cleanRefs.has(ref));
  if (missingRequiredImages.length > 0) {
    const reviewLines = [
      '',
      '## Visual evidence requiring placement review',
      '',
      ...missingRequiredImages.map((ref) => `![Required visual evidence](${ref})`),
    ];
    clean = `${clean}\n${reviewLines.join('\n')}`;
    unresolvedItems.push(...missingRequiredImages.map((ref) => ({
      type: 'required_image_placement',
      source_excerpt: ref,
      reason: 'Required image was declared in the source image map but omitted by the cleaner; postprocessor preserved the asset hash and requires placement review.',
      suggested_action: 'manual_review',
    })));
    changeSummary.push(`postprocessor restored ${missingRequiredImages.length} required image reference(s) for placement review`);
    riskFlags.add('required_image_placement_review');
  }
  const normalizedHeadings = normalizeOpeningHeadings(clean, chapterTitle);
  clean = normalizedHeadings.markdown;
  if (normalizedHeadings.removed.length > 0) {
    changeSummary.push(`postprocessor removed ${normalizedHeadings.removed.length} duplicate opening heading/title line(s)`);
  }
  clean = `${clean}\n`;

  if (normalizedImages.changes.length > 0) {
    changeSummary.push(`postprocessor normalized ${normalizedImages.changes.length} image reference(s)`);
  }
  if (/\$[^$]+\$|\\\(|\\\[/.test(clean)) riskFlags.add('contains_formula');
  if (/\|\s*[-:]+\s*\|/.test(clean)) riskFlags.add('contains_table');
  if (/OCR_UNCERTAIN|无法辨认|[?？]{2,}/i.test(clean)) riskFlags.add('contains_ambiguous_ocr');

  return {
    cleanMarkdown: clean,
    imageRefChanges: [...(llmResponse._internal_image_ref_changes || []), ...normalizedImages.changes],
    unresolvedItems,
    changeSummary,
    riskFlags: Array.from(riskFlags),
    keptImages: Array.from(new Set(extractMarkdownImages(clean).map((item) => item.ref))),
  };
}

async function pathExists(path) {
  try {
    await stat(path);
    return true;
  } catch {
    return false;
  }
}

async function copyReferencedImages({ rawChapterDir, rawBundleDir, cleanChapterDir, imageMap, cleanMarkdown }) {
  const cleanImagesDir = join(cleanChapterDir, 'images');
  await ensureDir(cleanImagesDir);

  const referenced = extractMarkdownImages(cleanMarkdown).map((item) => item.ref);
  const copied = [];
  const missing = [];

  for (const image of imageMap.images || []) {
    const normalizedRef = normalizeSlashes(image.normalized_ref || image.raw_ref);
    const shouldCopy = image.required === true || referenced.includes(normalizedRef);
    if (!shouldCopy) continue;

    const fileName = basename(normalizedRef);
    const targetPath = join(cleanImagesDir, fileName);
    const candidates = [
      image.source_path ? resolve(rawChapterDir, image.source_path) : null,
      image.raw_ref ? resolve(rawChapterDir, image.raw_ref) : null,
      image.raw_ref ? resolve(rawBundleDir, image.raw_ref) : null,
      image.raw_ref ? resolve(rawBundleDir, 'images', basename(image.raw_ref)) : null,
      resolve(rawChapterDir, 'images', fileName),
      resolve(rawBundleDir, 'images', fileName),
    ].filter(Boolean);

    const sourcePath = candidates.find((candidate) => existsSync(candidate));
    if (!sourcePath) {
      missing.push({ normalized_ref: normalizedRef, candidates });
      continue;
    }

    await copyFile(sourcePath, targetPath);
    copied.push({
      normalized_ref: `images/${fileName}`,
      source_path: sourcePath,
      target_path: targetPath,
    });
  }

  return { cleanImagesDir, copied, missing };
}

function validateCleanerResponseAgainstImageMap({ llmResponse, imageMap }) {
  const checks = [];
  const allowed = new Set(allowedImageRefs(imageMap));
  const required = new Set(requiredImageRefs(imageMap));
  const cleanRefs = extractMarkdownImages(llmResponse.clean_markdown || '').map((item) => item.ref);
  const keptImages = new Set((llmResponse.kept_images || []).map(normalizeSlashes));
  const outsideAllowed = [...new Set([...cleanRefs, ...keptImages])].filter((ref) => ref && !allowed.has(ref));
  const missingRequired = [...required].filter((ref) => !cleanRefs.includes(ref) && !keptImages.has(ref));

  checks.push({
    id: 'llm_json_schema',
    status: typeof llmResponse.clean_markdown === 'string' && llmResponse.clean_markdown.trim() ? 'PASS' : 'BLOCKED',
    detail: { hasCleanMarkdown: typeof llmResponse.clean_markdown === 'string' },
  });
  checks.push({
    id: 'llm_image_refs_allowed',
    status: outsideAllowed.length === 0 ? 'PASS' : 'BLOCKED',
    detail: { outsideAllowed },
  });
  checks.push({
    id: 'llm_required_images_preserved_or_reported',
    status: missingRequired.length === 0 ? 'PASS' : 'NEEDS_REVIEW',
    detail: { missingRequired },
  });

  return checks;
}

function repeatedLargeTextSegments(markdown) {
  const counts = new Map();
  const repeated = [];
  const segments = String(markdown || '')
    .split(/\n{2,}|<\|txt_split\|>/g)
    .map((segment) => normalizeTextForMetric(segment))
    .filter((segment) => segment.length >= 80);

  for (const segment of segments) {
    const count = (counts.get(segment) || 0) + 1;
    counts.set(segment, count);
    if (count === 2) {
      repeated.push({
        preview: segment.slice(0, 120),
        normalized_chars: segment.length,
      });
    }
  }

  return repeated.slice(0, 20);
}

function duplicateOpeningHeadingLines(markdown, chapterTitle) {
  const duplicates = [];
  const seen = new Set();
  const expectedKey = normalizeHeadingText(chapterTitle || '');
  const lines = String(markdown || '').replace(/\r\n?/g, '\n').split('\n');
  let nonBlankSeen = 0;
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    nonBlankSeen += 1;
    if (nonBlankSeen > 5) break;
    const match = /^(#{1,6})\s+(.+?)\s*$/.exec(trimmed);
    const key = normalizeHeadingText(match ? match[2] : trimmed);
    if (!key) continue;
    if (seen.has(key) || (expectedKey && key === expectedKey && seen.size > 0)) {
      duplicates.push(trimmed);
    }
    seen.add(key);
  }
  return duplicates;
}

function deduplicatedNormalizedTextForMetric(markdown) {
  const seen = new Set();
  const uniqueSegments = [];
  const segments = String(markdown || '')
    .split(/\n{2,}|<\|txt_split\|>/g)
    .map((segment) => normalizeTextForMetric(segment))
    .filter(Boolean);

  for (const segment of segments) {
    if (seen.has(segment)) continue;
    seen.add(segment);
    uniqueSegments.push(segment);
  }

  return uniqueSegments.join('');
}

function referencedVisualEvidenceGaps({ cleanMarkdown, cleanRefs, unresolvedItems, imageMap }) {
  const text = String(cleanMarkdown || '');
  const terms = [
    'flow diagram',
    'diagram',
    'figure',
    'chart',
    'graph',
    'illustration',
    'image',
    'picture',
  ];
  const referencedTerms = terms.filter((term) => new RegExp(`\\b${term.replace(/\s+/g, '\\s+')}\\b`, 'i').test(text));
  const hasUnresolvedItems = Array.isArray(unresolvedItems) && unresolvedItems.length > 0;
  const hasVisualContract = (imageMap?.images || []).length > 0 || (imageMap?.visual_evidence_requirements || []).length > 0;
  const gaps = [];
  if (hasVisualContract && referencedTerms.length > 0 && cleanRefs.length === 0 && !hasUnresolvedItems) {
    gaps.push(...referencedTerms.map((term) => ({
      term,
      reason: 'clean markdown references visual evidence but has no image reference or unresolved item',
    })));
  }

  for (const requirement of imageMap?.visual_evidence_requirements || []) {
    const status = String(requirement?.status || '');
    const linkedAssetNames = Array.isArray(requirement?.linked_asset_hash_names)
      ? requirement.linked_asset_hash_names.map(String).filter(Boolean)
      : [];
    if (status !== 'asset-linked' && status !== 'asset-missing') continue;
    const linkedRefsPresent = linkedAssetNames.some((name) => cleanRefs.some((ref) => basename(ref) === name));
    if (linkedRefsPresent || hasUnresolvedItems) continue;
    gaps.push({
      term: (requirement?.terms || []).join(', ') || 'visual_evidence_requirement',
      linked_asset_hash_names: linkedAssetNames,
      reason: 'visual evidence requirement was neither preserved as an image reference nor reported unresolved',
    });
  }
  return gaps;
}

function validateCleanCode({ cleanMarkdown, chapterTitle, imageMap, cleanChapterDir, copiedImages, missingImages, unresolvedItems, rawMarkdown, cleanerMode, llmResponse }) {
  const checks = [];
  const risks = [];
  const cleanRefs = extractMarkdownImages(cleanMarkdown).map((item) => item.ref);
  const copiedNames = new Set(copiedImages.map((item) => basename(item.normalized_ref)));
  const requiredImages = (imageMap.images || []).filter((item) => item.required === true);
  const missingRefs = [];
  const requiredMissingFromMarkdown = [];

  for (const ref of cleanRefs) {
    const fileName = basename(ref);
    const physicalPath = join(cleanChapterDir, ref);
    if (!existsSync(physicalPath) && !copiedNames.has(fileName)) {
      missingRefs.push(ref);
    }
  }

  for (const image of requiredImages) {
    const normalizedRef = normalizeSlashes(image.normalized_ref || image.raw_ref);
    if (!cleanRefs.includes(normalizedRef)) {
      requiredMissingFromMarkdown.push(normalizedRef);
    }
  }

  const rawNormalized = normalizeTextForMetric(rawMarkdown);
  const cleanNormalized = normalizeTextForMetric(cleanMarkdown);
  const coverageRatio = rawNormalized.length === 0 ? 0 : cleanNormalized.length / rawNormalized.length;
  const rawDeduplicatedNormalized = deduplicatedNormalizedTextForMetric(rawMarkdown);
  const deduplicatedCoverageRatio = rawDeduplicatedNormalized.length === 0
    ? coverageRatio
    : cleanNormalized.length / rawDeduplicatedNormalized.length;
  const coverageAcceptable = coverageRatio >= 0.55 || deduplicatedCoverageRatio >= 0.85;
  const hasHeading = chapterTitle
    ? cleanMarkdown.includes(chapterTitle) || /^#\s+/m.test(cleanMarkdown)
    : /^#\s+/m.test(cleanMarkdown);
  const splitMarkerCount = (cleanMarkdown.match(/<\|txt_split\|>/g) || []).length;
  const repeatedSegments = repeatedLargeTextSegments(cleanMarkdown);
  const visualEvidenceGaps = referencedVisualEvidenceGaps({ cleanMarkdown, cleanRefs, unresolvedItems, imageMap });
  const luceonMetadataCommentCount = (cleanMarkdown.match(/<!--\s*luceon:/gi) || []).length;
  const duplicateOpeningHeadings = duplicateOpeningHeadingLines(cleanMarkdown, chapterTitle);

  checks.push(...validateCleanerResponseAgainstImageMap({
    llmResponse: {
      ...llmResponse,
      clean_markdown: cleanMarkdown,
      kept_images: cleanRefs,
    },
    imageMap,
  }));
  checks.push({
    id: 'clean_markdown_exists',
    status: cleanMarkdown.trim().length > 0 ? 'PASS' : 'BLOCKED',
    detail: `clean markdown chars=${cleanMarkdown.length}`,
  });
  checks.push({
    id: 'heading_present',
    status: hasHeading ? 'PASS' : 'NEEDS_REVIEW',
    detail: chapterTitle ? `expected title=${chapterTitle}` : 'no expected title provided',
  });
  checks.push({
    id: 'image_refs_exist',
    status: missingRefs.length === 0 && missingImages.length === 0 ? 'PASS' : 'BLOCKED',
    detail: { missingRefs, missingImages },
  });
  checks.push({
    id: 'required_images_preserved',
    status: requiredMissingFromMarkdown.length === 0 ? 'PASS' : 'NEEDS_REVIEW',
    detail: { requiredMissingFromMarkdown },
  });
  checks.push({
    id: 'content_coverage_ratio',
    status: coverageAcceptable ? 'PASS' : 'NEEDS_REVIEW',
    detail: {
      rawNormalizedChars: rawNormalized.length,
      rawDeduplicatedNormalizedChars: rawDeduplicatedNormalized.length,
      cleanNormalizedChars: cleanNormalized.length,
      ratio: Number(coverageRatio.toFixed(4)),
      deduplicatedRatio: Number(deduplicatedCoverageRatio.toFixed(4)),
      duplicateAwarePass: coverageRatio < 0.55 && deduplicatedCoverageRatio >= 0.85,
    },
  });
  checks.push({
    id: 'raw_split_markers_resolved',
    status: splitMarkerCount === 0 ? 'PASS' : 'NEEDS_REVIEW',
    detail: { splitMarkerCount },
  });
  checks.push({
    id: 'duplicate_large_text_segments_absent',
    status: repeatedSegments.length === 0 ? 'PASS' : 'NEEDS_REVIEW',
    detail: { repeatedSegments },
  });
  checks.push({
    id: 'reader_surface_luceon_metadata_hidden',
    status: luceonMetadataCommentCount === 0 ? 'PASS' : 'NEEDS_REVIEW',
    detail: { luceonMetadataCommentCount },
  });
  checks.push({
    id: 'reader_surface_duplicate_opening_headings_absent',
    status: duplicateOpeningHeadings.length === 0 ? 'PASS' : 'NEEDS_REVIEW',
    detail: { duplicateOpeningHeadings },
  });
  checks.push({
    id: 'unresolved_items_landed',
    status: Array.isArray(unresolvedItems) ? 'PASS' : 'BLOCKED',
    detail: { unresolvedCount: Array.isArray(unresolvedItems) ? unresolvedItems.length : null },
  });
  checks.push({
    id: 'visual_references_have_assets_or_review_items',
    status: visualEvidenceGaps.length === 0 ? 'PASS' : 'NEEDS_REVIEW',
    detail: { visualEvidenceGaps },
  });
  checks.push({
    id: 'production_side_effects_absent',
    status: 'PASS',
    detail: { db_writes: 0, minio_writes: 0, runtime_worker_posts: 0 },
  });

  if (requiredMissingFromMarkdown.length > 0) risks.push('required_image_missing_from_markdown');
  if (missingRefs.length > 0 || missingImages.length > 0) risks.push('missing_image_file');
  if (!coverageAcceptable) risks.push('low_content_coverage_ratio');
  if (splitMarkerCount > 0) risks.push('raw_split_markers_remaining');
  if (repeatedSegments.length > 0) risks.push('duplicate_large_text_segments');
  if (luceonMetadataCommentCount > 0) risks.push('reader_surface_luceon_metadata_visible');
  if (duplicateOpeningHeadings.length > 0) risks.push('reader_surface_duplicate_opening_headings');
  if (visualEvidenceGaps.length > 0) risks.push('visual_reference_without_asset_or_review_item');
  if (cleanerMode === 'llm-dry-run') risks.push('llm_dry_run_requires_review');

  const hasBlocked = checks.some((check) => check.status === 'BLOCKED');
  const hasReview = checks.some((check) => check.status === 'NEEDS_REVIEW');
  const status = hasBlocked ? 'BLOCKED' : hasReview || unresolvedItems.length > 0 ? 'NEEDS_REVIEW' : 'PASS';

  return {
    protocol: PROTOCOL,
    status,
    cleaner_mode: cleanerMode,
    checks,
    metrics: {
      raw_chars: rawMarkdown.length,
      clean_chars: cleanMarkdown.length,
      raw_normalized_chars: rawNormalized.length,
      raw_deduplicated_normalized_chars: rawDeduplicatedNormalized.length,
      clean_normalized_chars: cleanNormalized.length,
      content_coverage_ratio: Number(coverageRatio.toFixed(4)),
      deduplicated_content_coverage_ratio: Number(deduplicatedCoverageRatio.toFixed(4)),
      clean_image_ref_count: cleanRefs.length,
      required_image_count: requiredImages.length,
      copied_image_count: copiedImages.length,
      unresolved_item_count: unresolvedItems.length,
    },
    risks,
  };
}

function sourceBlockIdsFromValue(value) {
  if (Array.isArray(value)) return uniqueStrings(value);
  if (typeof value === 'string') return uniqueStrings(value.split(/[,，\s]+/g));
  return [];
}

function sourceBlockText(block) {
  return String(block?.text || block?.raw_text || block?.markdown || block?.content || '');
}

function sourceBlockPage(block) {
  if (block?.page !== undefined && block?.page !== null) return block.page;
  if (Array.isArray(block?.pages) && block.pages.length > 0) return block.pages[0];
  return null;
}

function sourceBlockIdentitySet(block) {
  return uniqueStrings([
    block?.block_id,
    ...(Array.isArray(block?.source_block_ids) ? block.source_block_ids : []),
  ]);
}

function normalizeExcerptForSearch(text) {
  return normalizeTextForMetric(String(text || '').slice(0, 600));
}

function findSourceBlocksForReviewItem({ unresolvedItem, sourceMap }) {
  const blocks = Array.isArray(sourceMap?.source_blocks) ? sourceMap.source_blocks : [];
  const explicitIds = uniqueStrings([
    ...sourceBlockIdsFromValue(unresolvedItem?.source_block_ids),
    ...sourceBlockIdsFromValue(unresolvedItem?.linked_source_block_ids),
    ...sourceBlockIdsFromValue(unresolvedItem?.block_ids),
  ]);
  if (explicitIds.length > 0) {
    const matched = blocks.filter((block) => sourceBlockIdentitySet(block).some((id) => explicitIds.includes(id)));
    return {
      blocks: matched,
      source_block_ids: explicitIds,
      match_method: matched.length > 0 ? 'explicit_source_block_ids' : 'explicit_source_block_ids_unmatched',
      warnings: matched.length > 0 ? [] : ['explicit_source_block_ids_not_found_in_source_map'],
    };
  }

  const needle = normalizeExcerptForSearch(unresolvedItem?.source_excerpt);
  if (!needle || needle.length < 4) {
    return {
      blocks: [],
      source_block_ids: [],
      match_method: 'no_source_excerpt',
      warnings: ['source_block_match_not_attempted'],
    };
  }

  const matched = blocks
    .filter((block) => normalizeExcerptForSearch(sourceBlockText(block)).includes(needle))
    .slice(0, 5);
  return {
    blocks: matched,
    source_block_ids: uniqueStrings(matched.flatMap((block) => sourceBlockIdentitySet(block))),
    match_method: matched.length > 0 ? 'source_excerpt_direct_substring' : 'source_excerpt_unmatched',
    warnings: matched.length > 0 ? [] : ['source_excerpt_not_found_in_source_map'],
  };
}

function buildSourceRefs(blocks) {
  return blocks.map((block) => ({
    block_id: block?.block_id || null,
    source_block_ids: Array.isArray(block?.source_block_ids) ? block.source_block_ids : [],
    page: sourceBlockPage(block),
    pages: Array.isArray(block?.pages) ? block.pages : [],
    bbox: Array.isArray(block?.bbox) ? block.bbox : null,
    type: block?.type || null,
    source_order: block?.source_order ?? null,
    text_excerpt: sourceBlockText(block).slice(0, 400),
  }));
}

function assetRefsForSourceBlocks({ imageMap, sourceBlockIds, unresolvedItem }) {
  const ids = new Set(uniqueStrings(sourceBlockIds));
  const itemText = `${unresolvedItem?.source_excerpt || ''} ${unresolvedItem?.clean_excerpt || ''} ${unresolvedItem?.reason || ''}`;
  const itemAssetNames = new Set([
    ...sourceBlockIdsFromValue(unresolvedItem?.asset_hashes),
    ...sourceBlockIdsFromValue(unresolvedItem?.asset_hash_names),
  ]);
  const images = Array.isArray(imageMap?.images) ? imageMap.images : [];
  return images
    .filter((image) => {
      const imageIds = uniqueStrings([
        ...(Array.isArray(image?.source_block_ids) ? image.source_block_ids : []),
        ...(Array.isArray(image?.linked_source_block_ids) ? image.linked_source_block_ids : []),
      ]);
      const assetHash = image?.asset_hash_name || basename(normalizeSlashes(image?.normalized_ref || image?.raw_ref || ''));
      return imageIds.some((id) => ids.has(id))
        || itemAssetNames.has(assetHash)
        || (assetHash && itemText.includes(assetHash));
    })
    .slice(0, 20)
    .map((image) => ({
      asset_hash_name: image?.asset_hash_name || basename(normalizeSlashes(image?.normalized_ref || image?.raw_ref || '')),
      normalized_ref: normalizeSlashes(image?.normalized_ref || image?.raw_ref || ''),
      raw_ref: normalizeSlashes(image?.raw_ref || ''),
      source_page: image?.source_page ?? image?.page ?? null,
      bbox: Array.isArray(image?.bbox) ? image.bbox : null,
      required: image?.required === true,
      asset_kind: image?.asset_kind || image?.kind || image?.type || 'image',
      source_block_ids: Array.isArray(image?.source_block_ids) ? image.source_block_ids : [],
      linked_source_block_ids: Array.isArray(image?.linked_source_block_ids) ? image.linked_source_block_ids : [],
    }));
}

function assetRefsForAssetHashes({ imageMap, assetHashes }) {
  const hashes = new Set(uniqueStrings(assetHashes));
  if (hashes.size === 0) return [];
  return (Array.isArray(imageMap?.images) ? imageMap.images : [])
    .filter((image) => hashes.has(image?.asset_hash_name || basename(normalizeSlashes(image?.normalized_ref || image?.raw_ref || ''))))
    .map((image) => ({
      asset_hash_name: image?.asset_hash_name || basename(normalizeSlashes(image?.normalized_ref || image?.raw_ref || '')),
      normalized_ref: normalizeSlashes(image?.normalized_ref || image?.raw_ref || ''),
      raw_ref: normalizeSlashes(image?.raw_ref || ''),
      source_page: image?.source_page ?? image?.page ?? null,
      bbox: Array.isArray(image?.bbox) ? image.bbox : null,
      required: image?.required === true,
      asset_kind: image?.asset_kind || image?.kind || image?.type || 'image',
      source_block_ids: Array.isArray(image?.source_block_ids) ? image.source_block_ids : [],
      linked_source_block_ids: Array.isArray(image?.linked_source_block_ids) ? image.linked_source_block_ids : [],
    }));
}

function validatorAssetHashes(check) {
  const detail = check?.detail || {};
  return uniqueStrings([
    ...(Array.isArray(detail.missingRequired) ? detail.missingRequired.map((ref) => basename(normalizeSlashes(ref))) : []),
    ...(Array.isArray(detail.requiredMissingFromMarkdown) ? detail.requiredMissingFromMarkdown.map((ref) => basename(normalizeSlashes(ref))) : []),
    ...(Array.isArray(detail.visualEvidenceGaps)
      ? detail.visualEvidenceGaps.flatMap((gap) => Array.isArray(gap?.linked_asset_hash_names) ? gap.linked_asset_hash_names : [])
      : []),
  ]);
}

function excerptAroundNeedle(markdown, needle) {
  const source = String(markdown || '');
  const normalizedNeedle = String(needle || '').trim();
  if (!normalizedNeedle) return '';
  const index = source.indexOf(normalizedNeedle);
  if (index < 0) return '';
  const start = Math.max(0, index - 160);
  const end = Math.min(source.length, index + normalizedNeedle.length + 160);
  return source.slice(start, end).trim();
}

function itemPatchContract() {
  return {
    allowed_actions: [
      'accept_clean_excerpt',
      'edit_clean_excerpt',
      'mark_source_ocr_issue_accepted',
      'keep_unresolved',
      'request_reparse',
    ],
    selected_action: null,
    manual_clean_excerpt: null,
    reviewer: null,
    reviewed_at: null,
    notes: null,
  };
}

function buildReviewItems({ materialId, version, chapterId, chapterTitle, unresolvedItems, qualityReport, sourceMap, imageMap, rawMarkdown, cleanMarkdown, createdAt }) {
  const items = [];
  const addItem = (item) => {
    const reviewItemId = `review-${chapterId}-${String(items.length + 1).padStart(4, '0')}`;
    items.push({
      review_item_id: reviewItemId,
      unit_id: chapterId,
      unit_title: chapterTitle,
      status: 'open',
      ...item,
      patch_contract: itemPatchContract(),
    });
  };

  for (const unresolvedItem of unresolvedItems || []) {
    const sourceMatch = findSourceBlocksForReviewItem({ unresolvedItem, sourceMap });
    const sourceRefs = buildSourceRefs(sourceMatch.blocks);
    const assetRefs = assetRefsForSourceBlocks({ imageMap, sourceBlockIds: sourceMatch.source_block_ids, unresolvedItem });
    const sourceExcerpt = String(unresolvedItem?.source_excerpt || '').slice(0, 800);
    const cleanExcerpt = String(unresolvedItem?.clean_excerpt || '').slice(0, 800) || excerptAroundNeedle(cleanMarkdown, sourceExcerpt);
    addItem({
      origin: 'llm_unresolved_item',
      type: unresolvedItem?.type || 'unresolved',
      severity: 'review',
      source_block_ids: sourceMatch.source_block_ids,
      source_match_method: sourceMatch.match_method,
      source_match_warnings: sourceMatch.warnings,
      source_refs: sourceRefs,
      source_excerpt: sourceExcerpt,
      clean_excerpt: cleanExcerpt,
      reason: String(unresolvedItem?.reason || '').slice(0, 1000),
      suggested_action: unresolvedItem?.suggested_action || 'manual_review',
      asset_hashes: uniqueStrings(assetRefs.map((asset) => asset.asset_hash_name)),
      asset_refs: assetRefs,
      raw_context_excerpt: sourceExcerpt ? excerptAroundNeedle(rawMarkdown, sourceExcerpt) : '',
    });
  }

  for (const check of qualityReport?.checks || []) {
    if (check.status === 'PASS') continue;
    const assetHashes = validatorAssetHashes(check);
    const assetRefs = assetRefsForAssetHashes({ imageMap, assetHashes });
    addItem({
      origin: 'validator_check',
      type: `validator:${check.id}`,
      severity: check.status === 'BLOCKED' ? 'blocked' : 'review',
      source_block_ids: [],
      source_match_method: 'validator_check_only',
      source_match_warnings: [],
      source_refs: [],
      source_excerpt: '',
      clean_excerpt: '',
      reason: `Validator check ${check.id} returned ${check.status}.`,
      suggested_action: check.status === 'BLOCKED' ? 'fix_before_acceptance' : 'manual_review',
      asset_hashes: uniqueStrings([...assetHashes, ...assetRefs.map((asset) => asset.asset_hash_name)]),
      asset_refs: assetRefs,
      validator_check_id: check.id,
      validator_status: check.status,
      validator_detail: check.detail,
    });
  }

  return {
    schema: REVIEW_ITEMS_SCHEMA,
    protocol: PROTOCOL,
    material_id: materialId,
    version,
    unit_id: chapterId,
    title: chapterTitle,
    created_at: createdAt,
    status: items.length > 0 ? 'open' : 'no_review_required',
    item_count: items.length,
    source_policy: {
      source_truth_must_reference_source_blocks: true,
      llm_must_not_decide_book_structure: true,
      asset_hash_names_must_be_preserved: true,
    },
    items,
  };
}

function buildReviewPatchContract({ materialId, version, chapterId, chapterTitle, reviewItemsPath, cleanMdPath }) {
  return {
    schema: REVIEW_PATCH_CONTRACT_SCHEMA,
    protocol: PROTOCOL,
    material_id: materialId,
    version,
    unit_id: chapterId,
    title: chapterTitle,
    inputs: {
      clean_md: cleanMdPath,
      review_items: reviewItemsPath,
    },
    allowed_item_actions: [
      {
        action: 'accept_clean_excerpt',
        effect: 'mark the current CleanCode wording as accepted for this item',
        required_fields: ['review_item_id', 'reviewer', 'reviewed_at'],
      },
      {
        action: 'edit_clean_excerpt',
        effect: 'replace only the cited CleanCode excerpt without changing the cleaning unit boundary',
        required_fields: ['review_item_id', 'manual_clean_excerpt', 'reviewer', 'reviewed_at'],
      },
      {
        action: 'mark_source_ocr_issue_accepted',
        effect: 'accept the CleanCode wording while recording that the source OCR remained ambiguous',
        required_fields: ['review_item_id', 'reviewer', 'reviewed_at', 'notes'],
      },
      {
        action: 'keep_unresolved',
        effect: 'leave the item open and block final unit acceptance',
        required_fields: ['review_item_id', 'reviewer', 'reviewed_at', 'notes'],
      },
      {
        action: 'request_reparse',
        effect: 'route the cited source blocks back to upstream parsing review',
        required_fields: ['review_item_id', 'reviewer', 'reviewed_at', 'notes'],
      },
    ],
    output_policy: {
      patched_clean_md: 'patched_clean.md',
      review_decision_log: 'review_decision_log.json',
      all_review_items_must_be_closed_for_final_acceptance: true,
      patch_must_not_change_unit_boundary: true,
      patch_must_not_rename_assets: true,
      patch_must_preserve_source_block_refs: true,
    },
  };
}

function buildDiffMarkdown({ chapterId, rawMarkdown, precleanResult, cleanerStage, postProcessResult, qualityReport }) {
  return `# RawCode2CleanCode P0.1 Diff: ${chapterId}\n\n` +
    `## Summary\n\n` +
    `| Item | Value |\n` +
    `| --- | --- |\n` +
    `| Status | ${qualityReport.status} |\n` +
    `| Cleaner mode | ${cleanerStage.mode} |\n` +
    `| Raw chars | ${rawMarkdown.length} |\n` +
    `| Preclean chars | ${precleanResult.markdown.length} |\n` +
    `| Clean chars | ${postProcessResult.cleanMarkdown.length} |\n` +
    `| Removed noise lines | ${precleanResult.removedNoise.length + cleanerStage.response.removed_noise.length} |\n` +
    `| Image ref changes | ${postProcessResult.imageRefChanges.length} |\n` +
    `| Unresolved items | ${postProcessResult.unresolvedItems.length} |\n` +
    `| Prompt hash | ${cleanerStage.audit.prompt_hash || 'null'} |\n` +
    `| Request hash | ${cleanerStage.audit.request_hash || 'null'} |\n` +
    `| Response hash | ${cleanerStage.audit.response_hash || 'null'} |\n\n` +
    `## Stage Changes\n\n` +
    `### Rule PreCleaner\n\n` +
    `${precleanResult.changes.length > 0 ? precleanResult.changes.map((item) => `- ${JSON.stringify(item)}`).join('\n') : '- No preclean changes.'}\n\n` +
    `### LLM Cleaner Interface\n\n` +
    `${cleanerStage.response.change_summary.length > 0 ? cleanerStage.response.change_summary.map((item) => `- ${item}`).join('\n') : '- No LLM-stage change summary.'}\n\n` +
    `### Rule PostProcessor\n\n` +
    `${postProcessResult.changeSummary.length > 0 ? postProcessResult.changeSummary.map((item) => `- ${item}`).join('\n') : '- No postprocess changes.'}\n\n` +
    `## Removed Noise\n\n` +
    `${[...precleanResult.removedNoise, ...cleanerStage.response.removed_noise].length > 0 ? [...precleanResult.removedNoise, ...cleanerStage.response.removed_noise].map((item) => `- ${item.text} (${item.reason}, ${item.confidence || 'unknown'})`).join('\n') : '- None.'}\n\n` +
    `## Validation Checks\n\n` +
    `| Check | Status | Detail |\n` +
    `| --- | --- | --- |\n` +
    `${qualityReport.checks.map((check) => `| ${check.id} | ${check.status} | ${JSON.stringify(check.detail).replace(/\|/g, '\\|')} |`).join('\n')}\n`;
}

async function listChapterDirs(rawBundleDir) {
  const chaptersDir = join(rawBundleDir, 'chapters');
  const entries = await readdir(chaptersDir, { withFileTypes: true });
  return entries.filter((entry) => entry.isDirectory()).map((entry) => entry.name).sort();
}

async function loadRawBundle(rawBundleDir, requestedChapterId) {
  const manifestPath = join(rawBundleDir, 'manifest.json');
  const tocPath = join(rawBundleDir, 'toc.json');
  const manifest = await readJson(manifestPath);
  const toc = await readJson(tocPath);
  const chapterIds = await listChapterDirs(rawBundleDir);
  const chapterId = requestedChapterId || manifest.chapters?.[0]?.chapter_id || chapterIds[0];
  if (!chapterId) throw new Error(`no chapter found in ${rawBundleDir}`);
  if (!chapterIds.includes(chapterId)) throw new Error(`chapter ${chapterId} not found in ${join(rawBundleDir, 'chapters')}`);

  const rawChapterDir = join(rawBundleDir, 'chapters', chapterId);
  const unitMdPath = join(rawChapterDir, 'unit.md');
  const rawMdPath = join(rawChapterDir, 'raw.md');
  const sourceMapPath = join(rawChapterDir, 'source_map.json');
  const imageMapPath = join(rawChapterDir, 'image_map.json');
  const chunkManifestPath = join(rawChapterDir, 'chunk_manifest.json');

  const rawMarkdownInputPath = existsSync(unitMdPath) ? unitMdPath : rawMdPath;
  const rawMarkdown = await readFile(rawMarkdownInputPath, 'utf8');
  const sourceMap = await readJson(sourceMapPath);
  const imageMap = await readJson(imageMapPath);
  const chunkManifest = await readJson(chunkManifestPath);

  return {
    rawBundleDir,
    manifest,
    toc,
    chapterId,
    rawChapterDir,
    unitMdPath,
    rawMdPath,
    rawMarkdownInputPath,
    inputMarkdownRole: existsSync(unitMdPath) ? 'structure_locked_unit_markdown' : 'legacy_raw_markdown',
    sourceMapPath,
    imageMapPath,
    chunkManifestPath,
    rawMarkdown,
    sourceMap,
    imageMap,
    chunkManifest,
  };
}

async function writeTinyPng(path) {
  // 1x1 transparent PNG. It is sufficient for file existence and path validation in P0.1.
  const pngBase64 = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII=';
  await ensureDir(dirname(path));
  await writeFile(path, Buffer.from(pngBase64, 'base64'));
}

async function buildFixtureRawCode(outDir) {
  const rawBundleDir = join(outDir, 'rawcode', DEFAULT_MATERIAL_ID, DEFAULT_VERSION);
  const chapterId = 'chapter_001';
  const chapterTitle = '第一章 数与式';
  const rawChapterDir = join(rawBundleDir, 'chapters', chapterId);
  const globalImage = join(rawBundleDir, 'images', 'img_001.png');
  const chapterImage = join(rawChapterDir, 'images', 'img_001.png');
  const createdAt = nowIso();

  const rawMarkdown = [
    '扫描件页眉：Luceon OCR Draft',
    '',
    '# 第一章 数与式',
    '',
    '本章介绍有理数、整式以及基础运算。',
    '这些内容是后续学习方程和函数的基础。',
    '',
    '12',
    '',
    '## 1.1 有理数',
    '',
    '有理数可以表示为两个整数的比。',
    '例如 $\\frac{1}{2}$、$-3$ 都是有理数。',
    '',
    '![数轴示意图](../images/img_001.png)',
    '',
    '例 1：在数轴上表示 $-2$、$0$、$3$。',
    '',
    '---',
    '',
    '页脚：第 12 页',
  ].join('\n');

  await ensureDir(rawChapterDir);
  await ensureDir(join(rawBundleDir, 'images'));
  await ensureDir(join(rawChapterDir, 'images'));
  await writeTinyPng(globalImage);
  await copyFile(globalImage, chapterImage);

  const unitMarkdown = [
    '<!-- luceon:unit_id=chapter_001 -->',
    '<!-- luceon:parent_path=第一章 数与式 -->',
    '<!-- luceon:pack_level=1 -->',
    '<!-- luceon:boundary_basis=structure-level -->',
    '<!-- luceon:source_blocks=b001,b002,b003,b004 -->',
    '<!-- luceon:asset_hashes=img_001.png -->',
    '',
    rawMarkdown,
    '',
    '<!-- luceon:end_unit -->',
  ].join('\n');

  await writeText(join(rawChapterDir, 'unit.md'), unitMarkdown);
  await writeText(join(rawChapterDir, 'raw.md'), rawMarkdown);
  await writeText(join(rawBundleDir, 'full.md'), unitMarkdown);

  await writeJson(join(rawBundleDir, 'manifest.json'), {
    protocol: PROTOCOL,
    bundle_type: 'rawcode',
    material_id: DEFAULT_MATERIAL_ID,
    version: DEFAULT_VERSION,
    created_at: createdAt,
    source_pipeline: {
      mineru: { available: true, mode: 'fixture' },
      minerupopo: { available: true, mode: 'fixture' },
      luceon_rules: { available: true, mode: 'fixture' },
    },
    chapters: [
      {
        chapter_id: chapterId,
        title: chapterTitle,
        path: `chapters/${chapterId}/unit.md`,
        raw_preview_path: `chapters/${chapterId}/raw.md`,
      },
    ],
  });

  await writeJson(join(rawBundleDir, 'toc.json'), {
    toc_version: 'v0',
    material_id: DEFAULT_MATERIAL_ID,
    nodes: [
      {
        id: chapterId,
        level: 1,
        title: chapterTitle,
        order: 1,
        unit_path: `chapters/${chapterId}/unit.md`,
        raw_path: `chapters/${chapterId}/raw.md`,
      },
    ],
  });

  await writeJson(join(rawChapterDir, 'source_map.json'), {
    chapter_id: chapterId,
    source_blocks: [
      { block_id: 'b001', page: 12, type: 'heading', text: chapterTitle },
      { block_id: 'b002', page: 12, type: 'paragraph', text: '本章介绍有理数、整式以及基础运算。' },
      { block_id: 'b003', page: 12, type: 'formula', text: '$\\frac{1}{2}$、$-3$' },
      { block_id: 'b004', page: 12, type: 'image', image_ref: '../images/img_001.png' },
    ],
  });

  await writeJson(join(rawChapterDir, 'image_map.json'), {
    chapter_id: chapterId,
    images: [
      {
        raw_ref: '../images/img_001.png',
        normalized_ref: 'images/img_001.png',
        source_path: 'images/img_001.png',
        required: true,
        reason: 'referenced_by_markdown',
      },
    ],
  });

  await writeJson(join(rawChapterDir, 'chunk_manifest.json'), {
    protocol: PROTOCOL,
    material_id: DEFAULT_MATERIAL_ID,
    chapter_id: chapterId,
    title: chapterTitle,
    order: 1,
    source: 'fixture',
    boundary: { start: 1, end: rawMarkdown.split('\n').length },
    unit_markdown_path: `chapters/${chapterId}/unit.md`,
    raw_preview_path: `chapters/${chapterId}/raw.md`,
    llm_input_policy: {
      primary_input: 'unit.md',
      sidecars_for_validation: ['source_map.json', 'image_map.json', 'chunk_manifest.json'],
      structure_boundary_locked: true,
      llm_must_not_generate_book_structure: true,
    },
    risk_flags: [],
  });

  return rawBundleDir;
}

async function runPilot({ rawBundleDir, chapterId, outDir, cleanerMode, model, apiBase }) {
  const loaded = await loadRawBundle(rawBundleDir, chapterId);
  const materialId = loaded.manifest.material_id || DEFAULT_MATERIAL_ID;
  const version = loaded.manifest.version || DEFAULT_VERSION;
  const cleanBundleDir = join(outDir, 'cleancode', materialId, version);
  const cleanChapterDir = join(cleanBundleDir, 'chapters', loaded.chapterId);
  const auditDir = join(cleanChapterDir, 'audit');
  const chapterTitle = loaded.chunkManifest.title
    || loaded.toc.nodes?.find((node) => node.id === loaded.chapterId)?.title
    || loaded.chapterId;
  const createdAt = nowIso();

  await ensureDir(cleanChapterDir);

  const precleanResult = rulePreClean(loaded.rawMarkdown);
  const cleanerStage = await runCleanerStage({
    mode: cleanerMode,
    model,
    apiBase,
    materialId,
    version,
    chapterId: loaded.chapterId,
    chapterTitle,
    toc: loaded.toc,
    sourceMap: loaded.sourceMap,
    imageMap: loaded.imageMap,
    chunkManifest: loaded.chunkManifest,
    precleanMarkdown: precleanResult.markdown,
    inputMarkdownRole: loaded.inputMarkdownRole,
    auditDir,
  });
  const postProcessResult = rulePostProcess({
    llmResponse: cleanerStage.response,
    chapterTitle,
    imageMap: loaded.imageMap,
  });

  const imageCopyResult = await copyReferencedImages({
    rawChapterDir: loaded.rawChapterDir,
    rawBundleDir: loaded.rawBundleDir,
    cleanChapterDir,
    imageMap: loaded.imageMap,
    cleanMarkdown: postProcessResult.cleanMarkdown,
  });

  const qualityReport = validateCleanCode({
    cleanMarkdown: postProcessResult.cleanMarkdown,
    chapterTitle,
    imageMap: loaded.imageMap,
    cleanChapterDir,
    copiedImages: imageCopyResult.copied,
    missingImages: imageCopyResult.missing,
    unresolvedItems: postProcessResult.unresolvedItems,
    rawMarkdown: precleanResult.markdown,
    cleanerMode,
    llmResponse: cleanerStage.response,
  });

  const rawMdBuffer = await readFile(loaded.rawMdPath);
  const inputMarkdownBuffer = await readFile(loaded.rawMarkdownInputPath);
  const cleanMdPath = join(cleanChapterDir, 'clean.md');
  const cleanSourceMapPath = join(cleanChapterDir, 'source_map.json');
  const cleanImageMapPath = join(cleanChapterDir, 'image_map.json');
  const cleanChunkManifestPath = join(cleanChapterDir, 'chunk_manifest.json');
  const qualityReportPath = join(cleanChapterDir, 'quality_report.json');
  const unresolvedItemsPath = join(cleanChapterDir, 'unresolved_items.json');
  const reviewItemsPath = join(cleanChapterDir, 'review_items.json');
  const reviewPatchContractPath = join(cleanChapterDir, 'review_patch_contract.json');
  const diffPath = join(cleanChapterDir, 'diff.md');
  await writeText(cleanMdPath, postProcessResult.cleanMarkdown);
  await copyFile(loaded.sourceMapPath, cleanSourceMapPath);
  await copyFile(loaded.imageMapPath, cleanImageMapPath);
  await copyFile(loaded.chunkManifestPath, cleanChunkManifestPath);
  const cleanMdBuffer = await readFile(cleanMdPath);

  const reviewItemsPayload = buildReviewItems({
    materialId,
    version,
    chapterId: loaded.chapterId,
    chapterTitle,
    unresolvedItems: postProcessResult.unresolvedItems,
    qualityReport,
    sourceMap: loaded.sourceMap,
    imageMap: loaded.imageMap,
    rawMarkdown: loaded.rawMarkdown,
    cleanMarkdown: postProcessResult.cleanMarkdown,
    createdAt,
  });
  const reviewPatchContract = buildReviewPatchContract({
    materialId,
    version,
    chapterId: loaded.chapterId,
    chapterTitle,
    reviewItemsPath,
    cleanMdPath,
  });

  const cleanerManifest = {
    mode: cleanerMode,
    pilot_version: PILOT_VERSION,
    llm_used: cleanerStage.llmUsed,
    model: cleanerStage.llmUsed ? model : null,
    api_base_host: cleanerStage.llmUsed ? new URL(String(apiBase).replace(/\/$/, '')).host : null,
    prompt_hash: cleanerStage.audit.prompt_hash,
    request_hash: cleanerStage.audit.request_hash,
    response_hash: cleanerStage.audit.response_hash,
    prompt_path: cleanerStage.audit.prompt_path,
    request_path: cleanerStage.audit.request_path,
    response_path: cleanerStage.audit.response_path,
    raw_api_response_path: cleanerStage.audit.raw_api_response_path,
    schema_errors: cleanerStage.schemaErrors,
  };

  const cleanManifest = {
    protocol: PROTOCOL,
    bundle_type: 'cleancode_chapter',
    material_id: materialId,
    version,
    chapter_id: loaded.chapterId,
    title: chapterTitle,
    status: qualityReport.status,
    created_at: createdAt,
    input: {
      raw_bundle_dir: loaded.rawBundleDir,
      input_markdown: loaded.rawMarkdownInputPath,
      input_markdown_role: loaded.inputMarkdownRole,
      unit_md: loaded.unitMdPath,
      raw_md: loaded.rawMdPath,
      source_map: loaded.sourceMapPath,
      image_map: loaded.imageMapPath,
      chunk_manifest: loaded.chunkManifestPath,
    },
    output: {
      clean_md: cleanMdPath,
      source_map: cleanSourceMapPath,
      image_map: cleanImageMapPath,
      chunk_manifest: cleanChunkManifestPath,
      images_dir: imageCopyResult.cleanImagesDir,
      quality_report: qualityReportPath,
      unresolved_items: unresolvedItemsPath,
      review_items: reviewItemsPath,
      review_patch_contract: reviewPatchContractPath,
      diff: diffPath,
      audit_dir: cleanerMode === 'deterministic' ? null : auditDir,
    },
    stages: {
      rule_precleaner: {
        removed_noise_count: precleanResult.removedNoise.length,
        changes_count: precleanResult.changes.length,
        preclean_markdown_sha256: sha256Text(precleanResult.markdown),
      },
      llm_cleaner: cleanerManifest,
      rule_postprocessor: {
        image_ref_changes_count: postProcessResult.imageRefChanges.length,
        kept_images: postProcessResult.keptImages,
        risk_flags: postProcessResult.riskFlags,
      },
      validator: {
        status: qualityReport.status,
        checks_count: qualityReport.checks.length,
        review_item_count: reviewItemsPayload.item_count,
      },
      review_surface: {
        schema: REVIEW_ITEMS_SCHEMA,
        status: reviewItemsPayload.status,
        item_count: reviewItemsPayload.item_count,
      },
    },
    cleaner: cleanerManifest,
    hashes: {
      raw_md_sha256: sha256Buffer(rawMdBuffer),
      input_markdown_sha256: sha256Buffer(inputMarkdownBuffer),
      clean_md_sha256: sha256Buffer(cleanMdBuffer),
    },
    side_effects: {
      db_writes: 0,
      minio_writes: 0,
      runtime_worker_posts: 0,
    },
  };

  const unresolvedPayload = {
    protocol: PROTOCOL,
    material_id: materialId,
    chapter_id: loaded.chapterId,
    status: postProcessResult.unresolvedItems.length > 0 ? 'NEEDS_REVIEW' : 'PASS',
    items: postProcessResult.unresolvedItems,
  };

  await writeJson(join(cleanChapterDir, 'clean_manifest.json'), cleanManifest);
  await writeJson(qualityReportPath, qualityReport);
  await writeJson(unresolvedItemsPath, unresolvedPayload);
  await writeJson(reviewItemsPath, reviewItemsPayload);
  await writeJson(reviewPatchContractPath, reviewPatchContract);
  await writeText(diffPath, buildDiffMarkdown({
    chapterId: loaded.chapterId,
    rawMarkdown: loaded.rawMarkdown,
    precleanResult,
    cleanerStage,
    postProcessResult,
    qualityReport,
  }));

  await ensureDir(join(cleanBundleDir, 'images'));
  for (const copied of imageCopyResult.copied) {
    await copyFile(copied.target_path, join(cleanBundleDir, 'images', basename(copied.normalized_ref)));
  }

  await writeJson(join(cleanBundleDir, 'toc.json'), {
    ...loaded.toc,
    protocol: PROTOCOL,
    bundle_type: 'cleancode_toc',
    cleaned_at: createdAt,
    nodes: (loaded.toc.nodes || []).map((node) => ({
      ...node,
      clean_path: node.id === loaded.chapterId ? `chapters/${loaded.chapterId}/clean.md` : node.clean_path || null,
      clean_status: node.id === loaded.chapterId ? qualityReport.status : node.clean_status || 'NOT_PROCESSED',
    })),
  });

  await writeText(join(cleanBundleDir, 'full.md'), postProcessResult.cleanMarkdown);
  await writeJson(join(cleanBundleDir, 'manifest.json'), {
    protocol: PROTOCOL,
    bundle_type: 'cleancode',
    material_id: materialId,
    version,
    created_at: createdAt,
    input_rawcode: {
      path: loaded.rawBundleDir,
      manifest_sha256: sha256Text(stableJson(loaded.manifest)),
    },
    chapters: [
      { chapter_id: loaded.chapterId, title: chapterTitle, path: `chapters/${loaded.chapterId}/clean.md`, status: qualityReport.status },
    ],
    cleaner: cleanerManifest,
    validation: {
      status: qualityReport.status,
      quality_report: `chapters/${loaded.chapterId}/quality_report.json`,
      review_items: `chapters/${loaded.chapterId}/review_items.json`,
      review_patch_contract: `chapters/${loaded.chapterId}/review_patch_contract.json`,
      review_item_count: reviewItemsPayload.item_count,
    },
    side_effects: {
      db_writes: 0,
      minio_writes: 0,
      runtime_worker_posts: 0,
    },
  });

  return {
    ok: qualityReport.status !== 'BLOCKED',
    status: qualityReport.status,
    cleanerMode,
    llmUsed: cleanerStage.llmUsed,
    materialId,
    version,
    chapterId: loaded.chapterId,
    rawBundleDir: loaded.rawBundleDir,
    cleanBundleDir,
    cleanChapterDir,
    cleanMdPath,
    qualityReportPath,
    unresolvedItemsPath,
    reviewItemsPath,
    reviewPatchContractPath,
    diffPath,
    auditDir: cleanerMode === 'deterministic' ? null : auditDir,
    sideEffects: cleanManifest.side_effects,
  };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    console.log(usage());
    return;
  }

  const outDir = resolve(args.out);
  if (existsSync(outDir) && !args.force) {
    throw new Error(`output directory already exists: ${outDir}; pass --force to reuse it`);
  }
  await ensureDir(outDir);

  const rawBundleDir = args.fixture
    ? await buildFixtureRawCode(outDir)
    : resolve(args.input);

  const result = await runPilot({
    rawBundleDir,
    chapterId: args.chapterId,
    outDir,
    cleanerMode: args.cleaner,
    model: args.model,
    apiBase: args.apiBase,
  });

  console.log(stableJson({
    ok: result.ok,
    status: result.status,
    protocol: PROTOCOL,
    cleaner_mode: result.cleanerMode,
    llm_used: result.llmUsed,
    material_id: result.materialId,
    version: result.version,
    chapter_id: result.chapterId,
    raw_bundle_dir: result.rawBundleDir,
    clean_bundle_dir: result.cleanBundleDir,
    clean_md: result.cleanMdPath,
    quality_report: result.qualityReportPath,
    unresolved_items: result.unresolvedItemsPath,
    review_items: result.reviewItemsPath,
    review_patch_contract: result.reviewPatchContractPath,
    diff: result.diffPath,
    audit_dir: result.auditDir,
    side_effects: result.sideEffects,
  }));

  if (!result.ok) {
    process.exitCode = 2;
  }
}

export {
  PROTOCOL,
  DEFAULT_CLEANER,
  DEFAULT_LLM_MODEL,
  DEFAULT_OPENAI_BASE,
  REQUIRED_LLM_MODEL,
  PILOT_VERSION,
  REVIEW_ITEMS_SCHEMA,
  REVIEW_PATCH_CONTRACT_SCHEMA,
  assertAllowedLlmModel,
  buildReviewItems,
  buildReviewPatchContract,
  buildFixtureRawCode,
  loadRawBundle,
  normalizeImageRefs,
  parseLooseJson,
  runPilot,
  sha256Text,
  stableJson,
  validateCleanCode,
};

if (process.argv[1] && resolve(process.argv[1]) === __filename) {
  main().catch((error) => {
    console.error(`[rawcode2cleancode-pilot] ${error.stack || error.message}`);
    process.exitCode = 1;
  });
}
