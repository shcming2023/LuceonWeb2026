#!/usr/bin/env node

/**
 * CleanLaTeX Pack -> RawCode Bundle adapter.
 *
 * Task329 produces source-bound `cleaning_unit_pack` artifacts. The
 * RawCode2CleanCode runner consumes RawCode bundles. This adapter bridges those
 * two local-file contracts without calling MinerU, MinerU-Popo, LLMs, DB,
 * MinIO, or runtime workers.
 */

import { createHash } from 'node:crypto';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { mkdir, readFile, writeFile } from 'node:fs/promises';

const PROTOCOL = 'RawCode2CleanCode/v0';
const PACK_SCHEMA = 'luceon-cleanlatex-cleaning-unit-pack/v1';
const ADAPTER_VERSION = 'cleanlatex-pack-to-rawcode-2026-06-04';
const UAT_MANIFEST_PROTOCOL = 'RawCode2CleanCode-UAT-Manifest/v0';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const repoRoot = resolve(__dirname, '..');

function usage() {
  return [
    'Usage:',
    '  node scripts/cleanlatex-pack-to-rawcode.mjs --packs <cleaning_unit_packs.json> --out <dir> [--operator-id <id>] [--version <vN>] [--limit <n>]',
    '',
    'Output:',
    '  <out>/rawcode/<materialId>/<version>/...',
    '  <out>/rawcode2cleancode-uat-manifest.json',
    '',
    'Boundary:',
    '  Local-file deterministic adapter only; no DB/MinIO/worker/LLM calls.',
  ].join('\n');
}

function parseArgs(argv) {
  const args = {
    packs: null,
    out: join(repoRoot, '.tmp', 'cleanlatex-pack-to-rawcode'),
    operatorId: 'luceon-uat',
    version: null,
    limit: 3,
    help: false,
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
    } else if (arg === '--packs') {
      args.packs = next();
    } else if (arg === '--out') {
      args.out = next();
    } else if (arg === '--operator-id') {
      args.operatorId = next();
    } else if (arg === '--version') {
      args.version = next();
    } else if (arg === '--limit') {
      args.limit = Number(next());
    } else {
      throw new Error(`unknown argument: ${arg}`);
    }
  }

  if (!args.help && !args.packs) throw new Error('--packs is required');
  if (!Number.isFinite(args.limit) || args.limit < 1) throw new Error('--limit must be a positive number');
  return args;
}

function stableJson(value) {
  return `${JSON.stringify(value, null, 2)}\n`;
}

function sha256Text(text) {
  return createHash('sha256').update(text).digest('hex');
}

async function ensureDir(path) {
  await mkdir(path, { recursive: true });
}

async function writeJson(path, value) {
  await ensureDir(dirname(path));
  await writeFile(path, stableJson(value), 'utf8');
}

async function writeText(path, value) {
  await ensureDir(dirname(path));
  await writeFile(path, String(value || '').endsWith('\n') ? String(value || '') : `${value || ''}\n`, 'utf8');
}

function safeSegment(value, fallback = 'unit') {
  const safe = String(value || fallback)
    .replace(/[^a-zA-Z0-9._-]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 96);
  return safe || fallback;
}

function normalizeSlashes(value) {
  return String(value || '').replace(/\\/g, '/');
}

function loadPacksFromPayload(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.packs)) return payload.packs;
  throw new Error('packs file must be an array or an object with packs[]');
}

function normalizePack(pack, index) {
  if (pack?.schema && pack.schema !== PACK_SCHEMA) {
    throw new Error(`unsupported pack schema at index ${index}: ${pack.schema}`);
  }
  const nodeId = String(pack?.node?.node_id || pack?.pack_id || `unit-${index + 1}`);
  const chapterId = safeSegment(nodeId, `unit-${index + 1}`);
  const title = String(pack?.node?.title || pack?.pack_id || chapterId).trim() || chapterId;
  const materialId = String(pack?.material_id || 'unknown-material');
  const assetVersion = String(pack?.asset_version || 'v0');
  const blocks = Array.isArray(pack?.content_blocks) ? pack.content_blocks : [];
  return { pack, chapterId, title, materialId, assetVersion, blocks };
}

function rawMarkdownForPack({ title, blocks }) {
  const blockText = blocks
    .map((block) => String(block?.raw_text || '').trim())
    .filter(Boolean)
    .join('\n\n');
  const titlePattern = title.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  if (blockText && new RegExp(`^#*\\s*${titlePattern}\\b`, 'i').test(blockText.trim())) {
    return `${blockText.trim()}\n`;
  }
  return [`# ${title}`, blockText].filter(Boolean).join('\n\n').trim() + '\n';
}

function sourceBlockFor(block, index) {
  const rawText = String(block?.raw_text || '');
  const sourceBlock = {
    block_id: String(block?.block_id || `block-${index + 1}`),
    source_block_ids: Array.isArray(block?.source_block_ids) ? block.source_block_ids.map(String) : [String(block?.block_id || `block-${index + 1}`)],
    source_order: block?.source_order ?? index + 1,
    page: block?.page ?? null,
    pages: Array.isArray(block?.pages) ? block.pages : [],
    type: block?.type || 'text',
    text: rawText,
    source_hash: block?.source_hash || `sha256:${sha256Text(rawText)}`,
  };
  if (Array.isArray(block?.asset_hash_names) && block.asset_hash_names.length > 0) {
    sourceBlock.asset_hash_names = block.asset_hash_names.map(String);
  }
  if (Array.isArray(block?.asset_refs) && block.asset_refs.length > 0) {
    sourceBlock.asset_refs = block.asset_refs;
  }
  return sourceBlock;
}

function imageMapForPack(pack, rawMarkdown) {
  const images = [];
  const seen = new Set();
  for (const image of pack?.assets?.images || []) {
    const assetHashName = normalizeSlashes(image?.asset_hash_name || image?.hash_name || image?.name);
    if (!assetHashName || seen.has(assetHashName)) continue;
    seen.add(assetHashName);
    const normalizedRef = `images/${assetHashName}`;
    images.push({
      raw_ref: normalizedRef,
      normalized_ref: normalizedRef,
      source_path: `../../images/${assetHashName}`,
      required: rawMarkdown.includes(assetHashName),
      reason: rawMarkdown.includes(assetHashName) ? 'referenced_by_pack_markdown' : 'declared_by_pack_assets',
      asset_hash_name: assetHashName,
      source_page: image?.source_page ?? null,
      bbox: Array.isArray(image?.bbox) ? image.bbox : [],
      source_block_ids: Array.isArray(image?.source_block_ids) ? image.source_block_ids.map(String) : [],
    });
  }
  return {
    images,
    visual_evidence_requirements: Array.isArray(pack?.visual_evidence_requirements)
      ? pack.visual_evidence_requirements
      : [],
  };
}

async function convertCleanlatexPacksToRawCode({ packsPath, outDir, operatorId = 'luceon-uat', versionOverride = null, limit = 3 }) {
  const absolutePacksPath = resolve(packsPath);
  const packsRaw = await readFile(absolutePacksPath, 'utf8');
  const packs = loadPacksFromPayload(JSON.parse(packsRaw)).slice(0, limit);
  if (packs.length === 0) throw new Error('no cleaning unit packs found');

  const normalized = packs.map(normalizePack);
  const materialId = normalized[0].materialId;
  const version = versionOverride || `rawcode-from-${normalized[0].assetVersion}`;
  const rawBundleDir = join(resolve(outDir), 'rawcode', safeSegment(materialId, 'material'), safeSegment(version, 'v0'));
  const createdAt = new Date().toISOString();

  await ensureDir(join(rawBundleDir, 'chapters'));
  await ensureDir(join(rawBundleDir, 'images'));

  const tocNodes = [];
  const manifestChapters = [];
  const fullParts = [];

  for (const [index, item] of normalized.entries()) {
    const chapterDir = join(rawBundleDir, 'chapters', item.chapterId);
    const rawMarkdown = rawMarkdownForPack(item);
    const sourceBlocks = item.blocks.map(sourceBlockFor);
    const imageMap = imageMapForPack(item.pack, rawMarkdown);

    await writeText(join(chapterDir, 'raw.md'), rawMarkdown);
    await writeJson(join(chapterDir, 'source_map.json'), {
      protocol: PROTOCOL,
      source: {
        adapter: ADAPTER_VERSION,
        cleaning_unit_pack_id: item.pack.pack_id || null,
        cleaning_unit_pack_sha256: `sha256:${sha256Text(stableJson(item.pack))}`,
      },
      chapter_id: item.chapterId,
      source_blocks: sourceBlocks,
    });
    await writeJson(join(chapterDir, 'image_map.json'), {
      protocol: PROTOCOL,
      chapter_id: item.chapterId,
      ...imageMap,
    });
    await writeJson(join(chapterDir, 'chunk_manifest.json'), {
      protocol: PROTOCOL,
      material_id: materialId,
      version,
      chapter_id: item.chapterId,
      title: item.title,
      order: index + 1,
      source: 'cleanlatex-cleaning-unit-pack',
      pack_id: item.pack.pack_id || null,
      node: item.pack.node || null,
      boundary: item.pack.pack_boundary || null,
      source_span: item.pack.source_span || null,
      risk_flags: item.pack.warnings || [],
    });

    tocNodes.push({
      id: item.chapterId,
      level: item.pack?.pack_boundary?.pack_level ?? item.pack?.node?.level ?? 1,
      title: item.title,
      order: index + 1,
      raw_path: `chapters/${item.chapterId}/raw.md`,
      source_pack_id: item.pack.pack_id || null,
      source_block_ids: item.pack?.source_span?.source_block_ids || [],
    });
    manifestChapters.push({
      chapter_id: item.chapterId,
      title: item.title,
      path: `chapters/${item.chapterId}/raw.md`,
      source_pack_id: item.pack.pack_id || null,
    });
    fullParts.push(rawMarkdown.trim());
  }

  await writeText(join(rawBundleDir, 'full.md'), `${fullParts.join('\n\n')}\n`);
  await writeJson(join(rawBundleDir, 'toc.json'), {
    protocol: PROTOCOL,
    toc_version: 'v0',
    material_id: materialId,
    nodes: tocNodes,
  });
  await writeJson(join(rawBundleDir, 'manifest.json'), {
    protocol: PROTOCOL,
    bundle_type: 'rawcode',
    material_id: materialId,
    version,
    created_at: createdAt,
    source_pipeline: {
      mineru: { available: true, inherited: true },
      minerupopo: { available: true, inherited: true },
      luceon_rules: { available: true, inherited: true },
      cleanlatex_pack_adapter: {
        available: true,
        version: ADAPTER_VERSION,
        input_packs_sha256: `sha256:${sha256Text(packsRaw)}`,
      },
    },
    chapters: manifestChapters,
  });

  const runnerManifestPath = join(resolve(outDir), 'rawcode2cleancode-uat-manifest.json');
  await writeJson(runnerManifestPath, {
    protocol: UAT_MANIFEST_PROTOCOL,
    operatorId,
    cleaner: 'deterministic',
    samples: manifestChapters.map((chapter) => ({
      sample_id: `${safeSegment(materialId)}-${chapter.chapter_id}`,
      raw_bundle_dir: rawBundleDir,
      chapter_id: chapter.chapter_id,
      title: chapter.title,
    })),
  });

  return {
    ok: true,
    adapterVersion: ADAPTER_VERSION,
    materialId,
    version,
    packCount: packs.length,
    rawBundleDir,
    runnerManifestPath,
    zeroProductionSideEffects: {
      db_writes: 0,
      minio_writes: 0,
      runtime_worker_posts: 0,
    },
  };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    console.log(usage());
    return;
  }
  const result = await convertCleanlatexPacksToRawCode({
    packsPath: args.packs,
    outDir: args.out,
    operatorId: args.operatorId,
    versionOverride: args.version,
    limit: args.limit,
  });
  console.log(stableJson(result));
}

export {
  ADAPTER_VERSION,
  PACK_SCHEMA,
  convertCleanlatexPacksToRawCode,
  stableJson,
};

if (process.argv[1] && resolve(process.argv[1]) === __filename) {
  main().catch((error) => {
    console.error(`[cleanlatex-pack-to-rawcode] ${error.stack || error.message}`);
    process.exitCode = 1;
  });
}
