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

function allowedImageRefs(imageMap) {
  const refs = new Set();
  for (const image of imageMap.images || []) {
    if (image.raw_ref) refs.add(normalizeSlashes(image.raw_ref));
    if (image.normalized_ref) refs.add(normalizeSlashes(image.normalized_ref));
    if (image.normalized_ref) refs.add(`images/${basename(image.normalized_ref)}`);
  }
  return Array.from(refs).filter(Boolean).sort();
}

function rulePreClean(rawMarkdown) {
  const removedNoise = [];
  const changes = [];
  const lines = String(rawMarkdown || '').replace(/\r\n?/g, '\n').split('\n');
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

function buildCleanerRequest({ materialId, version, chapterId, chapterTitle, toc, sourceMap, imageMap, precleanMarkdown }) {
  const tocNode = (toc.nodes || []).find((node) => node.id === chapterId) || null;
  return {
    protocol: PROTOCOL,
    task: 'clean_single_chapter_markdown',
    chapter_context: {
      material_id: materialId,
      version,
      chapter_id: chapterId,
      title: chapterTitle,
      toc_order: tocNode?.order ?? null,
      toc_level: tocNode?.level ?? null,
    },
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
    constraints: [
      'Return JSON only; do not wrap it in Markdown fences.',
      'Clean, correct, organize, and standardize Markdown only.',
      'Do not summarize, expand, translate, or rewrite as new textbook content.',
      'Do not silently remove any possible original content.',
      'Preserve all required image references exactly in Markdown.',
      'For visual evidence requirements, either preserve the linked image reference exactly or report the issue in unresolved_items.',
      'Move uncertain content to unresolved_items instead of deleting it.',
      'Keep educational content, questions, formulas, tables, captions, and examples faithful to the source.',
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
    'You are the RawCode2CleanCode LLM Cleaner for a single textbook chapter.',
    '',
    'Your task is constrained content cleaning, not content creation.',
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
  try {
    return JSON.parse(stripped);
  } catch (firstError) {
    const start = stripped.indexOf('{');
    const end = stripped.lastIndexOf('}');
    if (start >= 0 && end > start) {
      return JSON.parse(stripped.slice(start, end + 1));
    }
    throw firstError;
  }
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

  const response = await fetch(endpoint, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${process.env.OPENAI_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });

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
    parsed_content: parseLooseJson(content),
  };
}

async function runCleanerStage({ mode, model, apiBase, materialId, version, chapterId, chapterTitle, toc, sourceMap, imageMap, precleanMarkdown, auditDir }) {
  const requestPayload = buildCleanerRequest({ materialId, version, chapterId, chapterTitle, toc, sourceMap, imageMap, precleanMarkdown });
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
    const llmResult = await callLLMCleaner({ apiBase, model, prompt });
    llmUsed = true;
    apiResponse = llmResult.api_response;
    rawResponse = llmResult.parsed_content;
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
    if (apiResponse) {
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
  const normalizedImages = normalizeImageRefs(clean, imageMap);
  clean = normalizedImages.markdown;

  const changeSummary = [...(llmResponse.change_summary || [])];
  const riskFlags = new Set(llmResponse.risk_flags || []);
  const unresolvedItems = [...(llmResponse.unresolved_items || [])];

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
    keptImages: Array.from(new Set([...(llmResponse.kept_images || []), ...extractMarkdownImages(clean).map((item) => item.ref)])),
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
  const gaps = [];
  if (referencedTerms.length > 0 && cleanRefs.length === 0 && !hasUnresolvedItems) {
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

  checks.push(...validateCleanerResponseAgainstImageMap({ llmResponse, imageMap }));
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
  const rawMdPath = join(rawChapterDir, 'raw.md');
  const sourceMapPath = join(rawChapterDir, 'source_map.json');
  const imageMapPath = join(rawChapterDir, 'image_map.json');
  const chunkManifestPath = join(rawChapterDir, 'chunk_manifest.json');

  const rawMarkdown = await readFile(rawMdPath, 'utf8');
  const sourceMap = await readJson(sourceMapPath);
  const imageMap = await readJson(imageMapPath);
  const chunkManifest = await readJson(chunkManifestPath);

  return {
    rawBundleDir,
    manifest,
    toc,
    chapterId,
    rawChapterDir,
    rawMdPath,
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

  await writeText(join(rawChapterDir, 'raw.md'), rawMarkdown);
  await writeText(join(rawBundleDir, 'full.md'), rawMarkdown);

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
      { chapter_id: chapterId, title: chapterTitle, path: `chapters/${chapterId}/raw.md` },
    ],
  });

  await writeJson(join(rawBundleDir, 'toc.json'), {
    toc_version: 'v0',
    material_id: DEFAULT_MATERIAL_ID,
    nodes: [
      { id: chapterId, level: 1, title: chapterTitle, order: 1, raw_path: `chapters/${chapterId}/raw.md` },
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
    precleanMarkdown: precleanResult.markdown,
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
    rawMarkdown: loaded.rawMarkdown,
    cleanerMode,
    llmResponse: cleanerStage.response,
  });

  const rawMdBuffer = await readFile(loaded.rawMdPath);
  const cleanMdPath = join(cleanChapterDir, 'clean.md');
  await writeText(cleanMdPath, postProcessResult.cleanMarkdown);
  const cleanMdBuffer = await readFile(cleanMdPath);

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
      raw_md: loaded.rawMdPath,
      source_map: loaded.sourceMapPath,
      image_map: loaded.imageMapPath,
      chunk_manifest: loaded.chunkManifestPath,
    },
    output: {
      clean_md: cleanMdPath,
      images_dir: imageCopyResult.cleanImagesDir,
      quality_report: join(cleanChapterDir, 'quality_report.json'),
      unresolved_items: join(cleanChapterDir, 'unresolved_items.json'),
      diff: join(cleanChapterDir, 'diff.md'),
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
      },
    },
    cleaner: cleanerManifest,
    hashes: {
      raw_md_sha256: sha256Buffer(rawMdBuffer),
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
  await writeJson(join(cleanChapterDir, 'quality_report.json'), qualityReport);
  await writeJson(join(cleanChapterDir, 'unresolved_items.json'), unresolvedPayload);
  await writeText(join(cleanChapterDir, 'diff.md'), buildDiffMarkdown({
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
    qualityReportPath: join(cleanChapterDir, 'quality_report.json'),
    unresolvedItemsPath: join(cleanChapterDir, 'unresolved_items.json'),
    diffPath: join(cleanChapterDir, 'diff.md'),
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
  assertAllowedLlmModel,
  buildFixtureRawCode,
  loadRawBundle,
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
