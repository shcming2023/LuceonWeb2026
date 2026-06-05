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
import { basename, dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { copyFile, mkdir, readFile, writeFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';

const PROTOCOL = 'RawCode2CleanCode/v0';
const PACK_SCHEMA = 'luceon-cleanlatex-cleaning-unit-pack/v1';
const ADAPTER_VERSION = 'cleanlatex-pack-to-rawcode-2026-06-05-inline-visuals';
const UAT_MANIFEST_PROTOCOL = 'RawCode2CleanCode-UAT-Manifest/v0';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const repoRoot = resolve(__dirname, '..');

function usage() {
  return [
    'Usage:',
    '  node scripts/cleanlatex-pack-to-rawcode.mjs --packs <cleaning_unit_packs.json> --out <dir> [--operator-id <id>] [--version <vN>] [--limit <n>|--all] [--asset-root <dir>]',
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
    all: false,
    assetRoot: null,
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
    } else if (arg === '--all') {
      args.all = true;
    } else if (arg === '--asset-root') {
      args.assetRoot = next();
    } else {
      throw new Error(`unknown argument: ${arg}`);
    }
  }

  if (!args.help && !args.packs) throw new Error('--packs is required');
  if (!args.all && (!Number.isFinite(args.limit) || args.limit < 1)) throw new Error('--limit must be a positive number');
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

function markdownBlocksForPack(blocks) {
  const output = [];
  const seenAdjacent = new Set();
  for (const block of blocks || []) {
    const rawText = String(block?.raw_text || '').trim();
    const assetNames = assetHashNamesForBlock(block).join(',');
    const key = `${block?.source_order ?? ''}\u0000${rawText}\u0000${assetNames}`;
    if ((rawText || assetNames) && seenAdjacent.has(key)) continue;
    output.push(block);
    if (rawText || assetNames) seenAdjacent.add(key);
  }
  return output;
}

function sourceBlockIdsForBlock(block, fallback = '') {
  const ids = Array.isArray(block?.source_block_ids) ? block.source_block_ids.map(String).filter(Boolean) : [];
  if (ids.length > 0) return ids;
  const blockId = String(block?.block_id || fallback || '').trim();
  return blockId ? [blockId] : [];
}

function assetHashNamesForBlock(block) {
  const names = new Set();
  for (const name of block?.asset_hash_names || []) {
    if (name) names.add(normalizeSlashes(name));
  }
  for (const ref of block?.asset_refs || []) {
    const name = ref?.asset_hash_name || ref?.hash_name || ref?.name || ref?.raw_ref;
    if (name) names.add(basename(normalizeSlashes(name)));
  }
  return Array.from(names).filter(Boolean).sort();
}

function primaryAssetRefForBlock(block, assetHashName) {
  const refs = Array.isArray(block?.asset_refs) ? block.asset_refs : [];
  return refs.find((ref) => {
    const name = ref?.asset_hash_name || ref?.hash_name || ref?.name || ref?.raw_ref;
    return name && basename(normalizeSlashes(name)) === assetHashName;
  }) || null;
}

function markdownPlaceholderForAssetBlock(block) {
  const names = assetHashNamesForBlock(block);
  if (names.length === 0) return '';
  const kind = String(block?.type || '').toLowerCase().includes('table') ? 'table' : 'image';
  const sourceBlockIds = sourceBlockIdsForBlock(block, block?.block_id);
  const page = block?.page ?? block?.source_page ?? block?.sourcePage ?? null;
  const bbox = Array.isArray(block?.bbox) ? block.bbox : [];
  const lines = [];
  for (const assetHashName of names) {
    const ref = primaryAssetRefForBlock(block, assetHashName);
    const rawRef = normalizeSlashes(ref?.raw_ref || `images/${assetHashName}`);
    const normalizedRef = rawRef.startsWith('images/') ? rawRef : `images/${basename(rawRef)}`;
    const refPage = ref?.source_page ?? page;
    const refBbox = Array.isArray(ref?.bbox) && ref.bbox.length > 0 ? ref.bbox : bbox;
    lines.push(
      `<!-- luceon:visual_block type=${kind} source_block_ids=${markdownCommentValue(sourceBlockIds.join(','))} page=${markdownCommentValue(refPage ?? '')} bbox=${markdownCommentValue(JSON.stringify(refBbox))} asset_hash=${markdownCommentValue(assetHashName)} -->`,
      `![${kind} source_block=${sourceBlockIds[0] || ''} page=${refPage ?? ''}](${normalizedRef})`,
    );
  }
  return lines.join('\n');
}

function markdownForBlock(block) {
  const rawText = String(block?.raw_text || '').trim();
  const visualPlaceholder = markdownPlaceholderForAssetBlock(block);
  return [rawText, visualPlaceholder].filter(Boolean).join('\n\n');
}

function rawMarkdownForPack({ title, blocks }) {
  const blockText = markdownBlocksForPack(blocks)
    .map(markdownForBlock)
    .filter(Boolean)
    .join('\n\n');
  const titlePattern = title.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  if (blockText && new RegExp(`^#*\\s*${titlePattern}\\b`, 'i').test(blockText.trim())) {
    return `${blockText.trim()}\n`;
  }
  return [`# ${title}`, blockText].filter(Boolean).join('\n\n').trim() + '\n';
}

function markdownCommentValue(value) {
  return String(value ?? '')
    .replace(/-->/g, '-- >')
    .replace(/\r?\n/g, ' ')
    .trim();
}

function titleLevelForPack(pack) {
  const level = Number(pack?.pack_boundary?.pack_level ?? pack?.node?.level ?? 1);
  if (!Number.isFinite(level)) return 1;
  return Math.min(6, Math.max(1, Math.round(level)));
}

function ancestorPathForPack(pack, title) {
  const path = Array.isArray(pack?.node?.ancestor_path)
    ? pack.node.ancestor_path
      .map((item) => (typeof item === 'string' ? item : item?.title))
      .filter(Boolean)
    : [];
  return path.length > 0 ? path.map(String) : [String(title || '').trim()].filter(Boolean);
}

function unitMarkdownForPack(item) {
  const { pack, chapterId, title, blocks } = item;
  const sourceBlockIds = Array.isArray(pack?.source_span?.source_block_ids)
    ? pack.source_span.source_block_ids.map(String)
    : blocks.flatMap((block) => (Array.isArray(block?.source_block_ids) ? block.source_block_ids.map(String) : [String(block?.block_id || '')])).filter(Boolean);
  const assetHashNames = new Set();
  for (const block of blocks) {
    for (const name of block?.asset_hash_names || []) assetHashNames.add(String(name));
    for (const ref of block?.asset_refs || []) {
      if (ref?.asset_hash_name) assetHashNames.add(String(ref.asset_hash_name));
    }
  }
  const visualAssets = [
    ...(Array.isArray(pack?.assets?.images) ? pack.assets.images : []),
    ...(Array.isArray(pack?.assets?.tables) ? pack.assets.tables : []),
  ];
  for (const image of visualAssets) {
    const name = image?.asset_hash_name || image?.hash_name || image?.name;
    if (name) assetHashNames.add(String(name));
  }
  const headingLevel = titleLevelForPack(pack);
  const heading = `${'#'.repeat(headingLevel)} ${title}`;
  const body = rawMarkdownForPack(item)
    .trim()
    .replace(/^#{1,6}\s+.+(?:\n+|$)/, '')
    .trim();
  const lines = [
    `<!-- luceon:unit_id=${markdownCommentValue(chapterId)} -->`,
    `<!-- luceon:pack_id=${markdownCommentValue(pack?.pack_id || '')} -->`,
    `<!-- luceon:parent_path=${markdownCommentValue(ancestorPathForPack(pack, title).join(' > '))} -->`,
    `<!-- luceon:pack_level=${markdownCommentValue(headingLevel)} -->`,
    `<!-- luceon:boundary_basis=${markdownCommentValue(pack?.pack_boundary?.boundary_basis || 'structure-level')} -->`,
    `<!-- luceon:source_block_count=${markdownCommentValue(sourceBlockIds.length)} -->`,
    `<!-- luceon:source_order_range=${markdownCommentValue((pack?.source_span?.source_order_range || []).join('-'))} -->`,
    '<!-- luceon:source_blocks_ref=source_map.json -->',
    `<!-- luceon:asset_hashes=${markdownCommentValue(Array.from(assetHashNames).sort().join(','))} -->`,
    '',
    heading,
  ];
  if (body) lines.push('', body);
  lines.push('', '<!-- luceon:end_unit -->', '');
  return lines.join('\n');
}

function sourceBlockFor(block, index) {
  const rawText = String(block?.raw_text || '');
  const assetNames = assetHashNamesForBlock(block);
  const sourceBlockIds = sourceBlockIdsForBlock(block, `block-${index + 1}`);
  const sourceBlock = {
    block_id: String(block?.block_id || `block-${index + 1}`),
    source_block_ids: sourceBlockIds,
    source_order: block?.source_order ?? index + 1,
    page: block?.page ?? null,
    pages: Array.isArray(block?.pages) ? block.pages : [],
    type: block?.type || 'text',
    text: rawText,
    source_hash: block?.source_hash || `sha256:${sha256Text(rawText)}`,
  };
  if (Array.isArray(block?.bbox) && block.bbox.length > 0) {
    sourceBlock.bbox = block.bbox;
  }
  if (assetNames.length > 0) {
    sourceBlock.asset_hash_names = assetNames;
    sourceBlock.markdown_placeholders = assetNames.map((assetHashName) => {
      const ref = primaryAssetRefForBlock(block, assetHashName);
      const rawRef = normalizeSlashes(ref?.raw_ref || `images/${assetHashName}`);
      return {
        asset_hash_name: assetHashName,
        normalized_ref: rawRef.startsWith('images/') ? rawRef : `images/${basename(rawRef)}`,
        source_page: ref?.source_page ?? block?.page ?? null,
        bbox: Array.isArray(ref?.bbox) && ref.bbox.length > 0 ? ref.bbox : (Array.isArray(block?.bbox) ? block.bbox : []),
      };
    });
  }
  if (Array.isArray(block?.asset_refs) && block.asset_refs.length > 0) {
    sourceBlock.asset_refs = block.asset_refs;
  }
  return sourceBlock;
}

function imageMapForPack(pack, rawMarkdown) {
  const images = [];
  const seen = new Set();
  const visualAssets = [
    ...(Array.isArray(pack?.assets?.images) ? pack.assets.images.map((asset) => ({ ...asset, asset_kind: asset?.kind || asset?.type || 'image' })) : []),
    ...(Array.isArray(pack?.assets?.tables) ? pack.assets.tables.map((asset) => ({ ...asset, asset_kind: asset?.kind || asset?.type || 'table' })) : []),
  ];
  for (const image of visualAssets) {
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
      asset_kind: image?.asset_kind || image?.kind || image?.type || (String(image?.role || '').toLowerCase().includes('table') ? 'table' : 'image'),
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

function findAssetSource(assetRoot, image) {
  if (!assetRoot) return null;
  const root = resolve(assetRoot);
  const candidates = [];
  for (const value of [image?.raw_ref, image?.source_path, image?.normalized_ref, image?.asset_hash_name]) {
    const normalized = normalizeSlashes(value);
    if (!normalized) continue;
    candidates.push(join(root, normalized));
    candidates.push(join(root, basename(normalized)));
  }
  for (const candidate of candidates) {
    if (existsSync(candidate)) return candidate;
  }
  return null;
}

async function copyDeclaredImages({ imageMap, rawBundleDir, assetRoot }) {
  const copied = [];
  const missing = [];
  const seen = new Set();
  for (const image of imageMap.images || []) {
    const normalizedRef = normalizeSlashes(image.normalized_ref || image.raw_ref);
    if (!normalizedRef || seen.has(normalizedRef)) continue;
    seen.add(normalizedRef);
    const source = findAssetSource(assetRoot, image);
    if (!source) {
      missing.push({
        normalized_ref: normalizedRef,
        asset_hash_name: image.asset_hash_name || basename(normalizedRef),
      });
      continue;
    }
    const target = join(rawBundleDir, normalizedRef);
    await ensureDir(dirname(target));
    await copyFile(source, target);
    copied.push({
      normalized_ref: normalizedRef,
      source_path: source,
      target_path: target,
    });
  }
  return { copied, missing };
}

async function convertCleanlatexPacksToRawCode({ packsPath, outDir, operatorId = 'luceon-uat', versionOverride = null, limit = 3, assetRoot = null }) {
  const absolutePacksPath = resolve(packsPath);
  const packsRaw = await readFile(absolutePacksPath, 'utf8');
  const allPacks = loadPacksFromPayload(JSON.parse(packsRaw));
  const packs = limit === null ? allPacks : allPacks.slice(0, limit);
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
  const assetCopy = { copied: [], missing: [] };

  for (const [index, item] of normalized.entries()) {
    const chapterDir = join(rawBundleDir, 'chapters', item.chapterId);
    const rawMarkdown = rawMarkdownForPack(item);
    const unitMarkdown = unitMarkdownForPack(item);
    const sourceBlocks = item.blocks.map(sourceBlockFor);
    const imageMap = imageMapForPack(item.pack, unitMarkdown);
    const chapterAssetCopy = await copyDeclaredImages({ imageMap, rawBundleDir, assetRoot });
    assetCopy.copied.push(...chapterAssetCopy.copied.map((entry) => ({ ...entry, chapter_id: item.chapterId })));
    assetCopy.missing.push(...chapterAssetCopy.missing.map((entry) => ({ ...entry, chapter_id: item.chapterId })));

    await writeText(join(chapterDir, 'unit.md'), unitMarkdown);
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
      unit_markdown_path: `chapters/${item.chapterId}/unit.md`,
      raw_preview_path: `chapters/${item.chapterId}/raw.md`,
      llm_input_policy: {
        primary_input: 'unit.md',
        sidecars_for_validation: ['source_map.json', 'image_map.json', 'chunk_manifest.json'],
        structure_boundary_locked: true,
        llm_must_not_generate_book_structure: true,
      },
      risk_flags: item.pack.warnings || [],
    });

    tocNodes.push({
      id: item.chapterId,
      level: item.pack?.pack_boundary?.pack_level ?? item.pack?.node?.level ?? 1,
      title: item.title,
      order: index + 1,
      raw_path: `chapters/${item.chapterId}/raw.md`,
      unit_path: `chapters/${item.chapterId}/unit.md`,
      source_pack_id: item.pack.pack_id || null,
      source_block_ids: item.pack?.source_span?.source_block_ids || [],
    });
    manifestChapters.push({
      chapter_id: item.chapterId,
      title: item.title,
      path: `chapters/${item.chapterId}/unit.md`,
      raw_preview_path: `chapters/${item.chapterId}/raw.md`,
      source_pack_id: item.pack.pack_id || null,
      image_count: imageMap.images.length,
      copied_image_count: chapterAssetCopy.copied.length,
      missing_image_count: chapterAssetCopy.missing.length,
    });
    fullParts.push(unitMarkdown.trim());
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
        asset_root_used: assetRoot ? resolve(assetRoot) : null,
      },
    },
    chapters: manifestChapters,
    asset_copy: {
      copied_count: assetCopy.copied.length,
      missing_count: assetCopy.missing.length,
      copied: assetCopy.copied,
      missing: assetCopy.missing,
    },
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
    inputPackCount: allPacks.length,
    rawBundleDir,
    runnerManifestPath,
    assetCopy: {
      copiedCount: assetCopy.copied.length,
      missingCount: assetCopy.missing.length,
    },
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
    limit: args.all ? null : args.limit,
    assetRoot: args.assetRoot,
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
