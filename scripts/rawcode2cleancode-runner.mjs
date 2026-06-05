#!/usr/bin/env node

/**
 * RawCode2CleanCode UAT Runner
 *
 * This CLI promotes the single-chapter P0.1 pilot into a controlled UAT-facing
 * entrypoint. It is intentionally local-file only: it reads RawCode bundles,
 * writes CleanCode candidates under the requested output directory, and records
 * an evidence surface for the testing department. It never writes DB, never
 * writes MinIO, and never posts to runtime workers.
 */

import { createHash } from 'node:crypto';
import { existsSync } from 'node:fs';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { basename, dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  DEFAULT_CLEANER,
  DEFAULT_LLM_MODEL,
  DEFAULT_OPENAI_BASE,
  PROTOCOL,
  REQUIRED_LLM_MODEL,
  runPilot,
  stableJson,
} from './rawcode2cleancode-pilot.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const repoRoot = resolve(__dirname, '..');

const MANIFEST_PROTOCOL = 'RawCode2CleanCode-UAT-Manifest/v0';
const RUNNER_VERSION = 'rawcode2cleancode-uat-runner-2026-06-04';
const DEFAULT_HARD_CAP = 3;
const MAX_OPERATOR_HARD_CAP = 3;
const MAX_FULL_BOOK_HARD_CAP = 500;
const MODES = new Set(['dry-run', 'real']);
const CLEANER_MODES = new Set(['deterministic', 'llm-dry-run', 'llm']);
const ZERO_PRODUCTION_SIDE_EFFECTS = Object.freeze({
  db_writes: 0,
  minio_writes: 0,
  runtime_worker_posts: 0,
});

function usage() {
  return [
    'Usage:',
    '  node scripts/rawcode2cleancode-runner.mjs --manifest <file> --operator-id <id> [--mode dry-run] [--out <dir>] [--cleaner deterministic|llm-dry-run|llm]',
    '  node scripts/rawcode2cleancode-runner.mjs --manifest <file> --operator-id <id> --mode real --confirm-real [--out <dir>] [--cleaner deterministic|llm-dry-run|llm]',
    '',
    'Manifest shape:',
    '  { "protocol": "RawCode2CleanCode-UAT-Manifest/v0", "samples": [{ "sample_id": "chapter-001", "raw_bundle_dir": "...", "chapter_id": "chapter_001" }] }',
    '',
    'Boundaries:',
    '  dry-run is the default mode and does not call external LLM APIs unless --cleaner llm-dry-run is requested for audit generation.',
    '  real mode requires --confirm-real and first runs a dry-run preflight.',
    '  hard-cap is capped at 3 samples for UAT safety unless --allow-full-book is explicitly provided.',
    '  all modes are local-file only: no DB writes, no MinIO writes, no runtime worker posts.',
  ].join('\n');
}

function parseArgs(argv) {
  const args = {
    manifest: null,
    operatorId: null,
    mode: 'dry-run',
    hardCap: DEFAULT_HARD_CAP,
    cleaner: null,
    model: DEFAULT_LLM_MODEL,
    apiBase: DEFAULT_OPENAI_BASE,
    confirmRealRun: false,
    allowFullBook: false,
    out: join(repoRoot, '.tmp', 'rawcode2cleancode-runner'),
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
    } else if (arg === '--manifest') {
      args.manifest = next();
    } else if (arg === '--operator-id') {
      args.operatorId = next();
    } else if (arg === '--mode') {
      args.mode = next();
    } else if (arg === '--hard-cap') {
      args.hardCap = Number(next());
    } else if (arg === '--cleaner') {
      args.cleaner = next();
    } else if (arg === '--model') {
      args.model = next();
    } else if (arg === '--api-base') {
      args.apiBase = next();
    } else if (arg === '--confirm-real') {
      args.confirmRealRun = true;
    } else if (arg === '--allow-full-book') {
      args.allowFullBook = true;
    } else if (arg === '--out') {
      args.out = next();
    } else {
      throw new Error(`unknown argument: ${arg}`);
    }
  }

  if (!MODES.has(args.mode)) {
    throw new Error(`invalid --mode ${args.mode}; expected one of ${Array.from(MODES).join(', ')}`);
  }
  if (!Number.isFinite(args.hardCap) || args.hardCap < 1) {
    throw new Error('--hard-cap must be a positive number');
  }
  if (args.cleaner && !CLEANER_MODES.has(args.cleaner)) {
    throw new Error(`invalid --cleaner ${args.cleaner}; expected one of ${Array.from(CLEANER_MODES).join(', ')}`);
  }

  return args;
}

function sha256(textOrBuffer) {
  return createHash('sha256').update(textOrBuffer).digest('hex');
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

function blocked(code, reason, details = undefined) {
  return {
    ok: false,
    code,
    reason,
    ...(details ? { details } : {}),
    readinessClaimed: false,
  };
}

function requiresLlmModelGuard(cleanerMode) {
  return cleanerMode === 'llm' || cleanerMode === 'llm-dry-run';
}

function validateAllowedLlmModel({ cleanerMode, model }) {
  if (!requiresLlmModelGuard(cleanerMode)) return null;
  if (model === REQUIRED_LLM_MODEL) return null;
  return blocked('LLM_MODEL_NOT_ALLOWED', `RawCode2CleanCode LLM cleaner model is locked to ${REQUIRED_LLM_MODEL}`, {
    requestedModel: model || null,
    requiredModel: REQUIRED_LLM_MODEL,
    cleanerMode,
  });
}

function safeSegment(value, fallback) {
  const segment = String(value || fallback || 'sample')
    .replace(/[^a-zA-Z0-9._-]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 80);
  return segment || fallback || 'sample';
}

function normalizeSlashes(path) {
  return String(path || '').replace(/\\/g, '/');
}

function redactSensitiveText(value) {
  return String(value || '')
    .replace(/sk-[A-Za-z0-9_*.-]{8,}/g, '[REDACTED_API_KEY]')
    .replace(/Bearer\s+[A-Za-z0-9._~+/=-]{8,}/gi, 'Bearer [REDACTED]');
}

function resolveMaybeRelative(baseDir, value) {
  if (!value) return null;
  const normalized = String(value);
  return resolve(baseDir, normalized);
}

function normalizeSample(sample, index, manifestDir) {
  const rawBundleDirValue = sample.raw_bundle_dir || sample.rawBundleDir || sample.input || sample.input_dir;
  const chapterId = sample.chapter_id || sample.chapterId || null;
  const sampleId = sample.sample_id || sample.sampleId || `${basename(String(rawBundleDirValue || 'rawcode'))}-${chapterId || index + 1}`;
  const cleaner = sample.cleaner || null;

  return {
    ...sample,
    sampleId: String(sampleId),
    rawBundleDir: resolveMaybeRelative(manifestDir, rawBundleDirValue),
    chapterId,
    cleaner,
    title: sample.title || sample.chapter_title || sample.chapterTitle || null,
  };
}

function normalizeManifest(parsed, manifestDir) {
  const samples = Array.isArray(parsed) ? parsed : parsed?.samples;
  const manifestDefaults = Array.isArray(parsed) ? {} : parsed || {};
  return {
    protocol: manifestDefaults.protocol || null,
    operatorId: manifestDefaults.operatorId || manifestDefaults.operator_id || null,
    hardCap: manifestDefaults.hardCap || manifestDefaults.hard_cap || null,
    cleaner: manifestDefaults.cleaner || null,
    samples: Array.isArray(samples)
      ? samples.map((sample, index) => normalizeSample(sample, index, manifestDir))
      : samples,
  };
}

async function readRunnerManifest(path) {
  if (!path) return blocked('MISSING_MANIFEST', 'manifest file is required');
  const absolutePath = resolve(path);
  let raw;
  try {
    raw = await readFile(absolutePath, 'utf8');
  } catch (error) {
    return blocked('MANIFEST_NOT_READABLE', 'manifest file cannot be read', { path: absolutePath, message: error.message });
  }

  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch (error) {
    return blocked('MANIFEST_JSON_INVALID', 'manifest file is not valid JSON', { path: absolutePath, message: error.message });
  }

  return {
    ok: true,
    path: absolutePath,
    sha256: sha256(raw),
    ...normalizeManifest(parsed, dirname(absolutePath)),
  };
}

function validateRunnerInput({ samples, mode, operatorId, hardCap, confirmRealRun, cleaner, model, allowFullBook }) {
  if (!operatorId || !String(operatorId).trim()) {
    return blocked('MISSING_OPERATOR', '--operator-id is required for UAT evidence ownership');
  }
  if (!Array.isArray(samples) || samples.length === 0) {
    return blocked('EMPTY_SAMPLE_LIST', 'manifest must contain at least one RawCode sample');
  }
  const maxHardCap = allowFullBook ? MAX_FULL_BOOK_HARD_CAP : MAX_OPERATOR_HARD_CAP;
  if (hardCap > maxHardCap) {
    return blocked('ENTRY_HARD_CAP_EXCEEDED', `operator entry hard-cap must be <= ${maxHardCap}`, { requestedHardCap: hardCap, maxHardCap, allowFullBook });
  }
  if (samples.length > hardCap) {
    return blocked('HARD_CAP_EXCEEDED', 'sample count exceeds configured hard-cap', { sampleCount: samples.length, hardCap });
  }
  if (mode === 'real' && confirmRealRun !== true) {
    return blocked('REAL_RUN_NOT_CONFIRMED', 'real mode requires --confirm-real');
  }

  const seen = new Set();
  for (const [index, sample] of samples.entries()) {
    if (!sample.rawBundleDir) {
      return blocked('SAMPLE_INPUT_MISSING', 'sample.raw_bundle_dir is required', { index, sampleId: sample.sampleId || null });
    }
    const key = `${normalizeSlashes(sample.rawBundleDir)}::${sample.chapterId || ''}`;
    if (seen.has(key)) {
      return blocked('DUPLICATE_SAMPLE', 'duplicate raw_bundle_dir/chapter_id sample detected', { index, key });
    }
    seen.add(key);
    if (!existsSync(sample.rawBundleDir)) {
      return blocked('RAW_BUNDLE_NOT_FOUND', 'sample raw_bundle_dir does not exist', { index, sampleId: sample.sampleId, rawBundleDir: sample.rawBundleDir });
    }
    if (sample.cleaner && !CLEANER_MODES.has(sample.cleaner)) {
      return blocked('SAMPLE_CLEANER_INVALID', 'sample.cleaner is not supported', { index, sampleId: sample.sampleId, cleaner: sample.cleaner });
    }
    const modelBlock = validateAllowedLlmModel({
      cleanerMode: sample.cleaner || cleaner || DEFAULT_CLEANER,
      model,
    });
    if (modelBlock) {
      return modelBlock;
    }
  }

  return { ok: true, readinessClaimed: false };
}

function buildRunId({ mode, operatorId, manifestSha, startedAt }) {
  const stamp = startedAt.replace(/[^0-9TZ]/g, '').replace(/Z$/, 'Z');
  const safeOperator = safeSegment(operatorId, 'operator').slice(0, 48);
  return `rawcode2cleancode-${mode}-${safeOperator}-${stamp}-${manifestSha.slice(0, 12)}`;
}

function selectCleaner({ sample, defaultCleaner, mode }) {
  const requestedCleaner = sample.cleaner || defaultCleaner || DEFAULT_CLEANER;
  if (mode === 'dry-run' && requestedCleaner === 'llm') {
    return {
      cleanerMode: 'llm-dry-run',
      cleanerDowngradedForDryRun: true,
      requestedCleaner,
    };
  }
  return {
    cleanerMode: requestedCleaner,
    cleanerDowngradedForDryRun: false,
    requestedCleaner,
  };
}

function defaultProcessSample() {
  return async ({ sample, index, mode, phaseLabel, runOutputRoot, defaultCleaner, model, apiBase }) => {
    const cleanerSelection = selectCleaner({ sample, defaultCleaner, mode });
    const sampleOutDir = join(
      runOutputRoot,
      'samples',
      `${String(index + 1).padStart(2, '0')}-${safeSegment(sample.sampleId, `sample-${index + 1}`)}`,
    );

    const result = await runPilot({
      rawBundleDir: sample.rawBundleDir,
      chapterId: sample.chapterId,
      outDir: sampleOutDir,
      cleanerMode: cleanerSelection.cleanerMode,
      model,
      apiBase,
    });

    const productionSideEffects = result.sideEffects || ZERO_PRODUCTION_SIDE_EFFECTS;
    const productionSideEffectTotal = Number(productionSideEffects.db_writes || 0)
      + Number(productionSideEffects.minio_writes || 0)
      + Number(productionSideEffects.runtime_worker_posts || 0);

    return {
      ok: result.ok === true && productionSideEffectTotal === 0,
      stage: productionSideEffectTotal === 0 ? 'rawcode2cleancode-local-clean' : 'production-side-effect-guard',
      status: result.status,
      code: productionSideEffectTotal === 0 ? null : 'PRODUCTION_SIDE_EFFECT_DETECTED',
      reason: productionSideEffectTotal === 0 ? null : 'RawCode2CleanCode runner detected non-zero production side effects',
      evidence: {
        protocol: PROTOCOL,
        phaseLabel,
        cleaner: {
          requested: cleanerSelection.requestedCleaner,
          effective: cleanerSelection.cleanerMode,
          downgradedForDryRun: cleanerSelection.cleanerDowngradedForDryRun,
          llmUsed: result.llmUsed,
        },
        input: {
          rawBundleDir: result.rawBundleDir,
          chapterId: result.chapterId,
        },
        output: {
          cleanBundleDir: result.cleanBundleDir,
          cleanChapterDir: result.cleanChapterDir,
          cleanMd: result.cleanMdPath,
          qualityReport: result.qualityReportPath,
          unresolvedItems: result.unresolvedItemsPath,
          reviewItems: result.reviewItemsPath,
          reviewPatchContract: result.reviewPatchContractPath,
          diff: result.diffPath,
          auditDir: result.auditDir,
        },
        sideEffects: productionSideEffects,
      },
      operationCounts: {
        localRawBundleRead: 1,
        localCleanBundleWrite: 1,
        llmApiCall: result.llmUsed ? 1 : 0,
        dbWrite: Number(productionSideEffects.db_writes || 0),
        minioWrite: Number(productionSideEffects.minio_writes || 0),
        runtimeWorkerPost: Number(productionSideEffects.runtime_worker_posts || 0),
      },
      readinessClaimed: false,
    };
  };
}

function zeroOperationCounts() {
  return {
    localRawBundleRead: 0,
    localCleanBundleWrite: 0,
    llmApiCall: 0,
    dbWrite: 0,
    minioWrite: 0,
    runtimeWorkerPost: 0,
  };
}

function addOperationCounts(target, source = {}) {
  for (const key of Object.keys(target)) {
    target[key] += Number(source[key] || 0);
  }
  return target;
}

async function runSamplePhase({ samples, mode, operatorId, phaseLabel, runOutputRoot, defaultCleaner, model, apiBase, deps }) {
  const processSample = deps?.processSample || defaultProcessSample();
  const operationCounts = zeroOperationCounts();
  const sampleResults = [];
  let stopped = null;

  for (const [index, sample] of samples.entries()) {
    let processed;
    try {
      processed = await processSample({
        sample,
        index,
        mode,
        operatorId,
        phaseLabel,
        runOutputRoot,
        defaultCleaner,
        model,
        apiBase,
      });
    } catch (error) {
      processed = {
        ok: false,
        stage: 'rawcode2cleancode-local-clean',
        code: 'SAMPLE_PROCESSING_ERROR',
        reason: redactSensitiveText(error.message),
        evidence: { stack: redactSensitiveText(error.stack || '') || null },
        operationCounts: {},
        readinessClaimed: false,
      };
    }

    addOperationCounts(operationCounts, processed.operationCounts);
    const sampleResult = {
      order: index + 1,
      sampleId: sample.sampleId,
      chapterId: sample.chapterId || null,
      title: sample.title || null,
      ok: processed.ok === true,
      stage: processed.stage || null,
      status: processed.status || null,
      code: processed.code || null,
      reason: processed.reason || null,
      evidence: processed.evidence || null,
      operationCounts: processed.operationCounts || {},
      readinessClaimed: false,
    };
    sampleResults.push(sampleResult);

    if (processed.ok !== true) {
      stopped = {
        order: index + 1,
        sampleId: sample.sampleId,
        stage: processed.stage || null,
        code: processed.code || 'SAMPLE_FAILED',
        reason: processed.reason || 'sample processing failed',
      };
      break;
    }
  }

  return {
    ok: stopped === null,
    mode,
    phaseLabel,
    attemptedSampleCount: sampleResults.length,
    completedSampleCount: sampleResults.filter((item) => item.ok).length,
    stopped,
    operationCounts,
    samples: sampleResults,
    readinessClaimed: false,
  };
}

async function runRawCode2CleanCodeUatRunner({
  samples,
  mode = 'dry-run',
  operatorId,
  hardCap = DEFAULT_HARD_CAP,
  confirmRealRun = false,
  outDir = join(repoRoot, '.tmp', 'rawcode2cleancode-runner'),
  cleaner = DEFAULT_CLEANER,
  model = DEFAULT_LLM_MODEL,
  apiBase = DEFAULT_OPENAI_BASE,
  allowFullBook = false,
  deps = {},
} = {}) {
  const validation = validateRunnerInput({ samples, mode, operatorId, hardCap, confirmRealRun, cleaner, model, allowFullBook });
  if (!validation.ok) return validation;

  const startedAt = deps.now ? deps.now() : nowIso();
  const manifestSha = deps.manifestSha || sha256(stableJson(samples));
  const runId = buildRunId({ mode, operatorId, manifestSha, startedAt });
  const outputRoot = resolve(outDir, runId);
  await ensureDir(outputRoot);

  if (mode === 'dry-run') {
    const phase = await runSamplePhase({
      samples,
      mode: 'dry-run',
      operatorId,
      phaseLabel: 'dry-run',
      runOutputRoot: join(outputRoot, 'dry-run'),
      defaultCleaner: cleaner,
      model,
      apiBase,
      deps,
    });
    return {
      ...phase,
      ok: phase.ok,
      runId,
      runnerVersion: RUNNER_VERSION,
      startedAt,
      operatorId,
      requestedMode: mode,
      hardCap,
      allowFullBook,
      outputRoot,
      realRunExecuted: false,
      productionSideEffects: ZERO_PRODUCTION_SIDE_EFFECTS,
      readinessClaimed: false,
    };
  }

  const preflight = await runSamplePhase({
    samples,
    mode: 'dry-run',
    operatorId,
    phaseLabel: 'preflight',
    runOutputRoot: join(outputRoot, 'preflight'),
    defaultCleaner: cleaner,
    model,
    apiBase,
    deps,
  });

  if (!preflight.ok) {
    return {
      ok: false,
      code: 'PREFLIGHT_FAILED',
      reason: 'real mode preflight failed; real phase was not executed',
      runId,
      runnerVersion: RUNNER_VERSION,
      startedAt,
      operatorId,
      requestedMode: mode,
      hardCap,
      allowFullBook,
      outputRoot,
      realRunExecuted: false,
      preflight,
      attemptedSampleCount: preflight.attemptedSampleCount,
      completedSampleCount: 0,
      stopped: preflight.stopped,
      operationCounts: preflight.operationCounts,
      samples: preflight.samples,
      productionSideEffects: ZERO_PRODUCTION_SIDE_EFFECTS,
      readinessClaimed: false,
    };
  }

  const realPhase = await runSamplePhase({
    samples,
    mode: 'real',
    operatorId,
    phaseLabel: 'real',
    runOutputRoot: join(outputRoot, 'real'),
    defaultCleaner: cleaner,
    model,
    apiBase,
    deps,
  });

  return {
    ...realPhase,
    ok: realPhase.ok,
    runId,
    runnerVersion: RUNNER_VERSION,
    startedAt,
    operatorId,
    requestedMode: mode,
    hardCap,
    allowFullBook,
    outputRoot,
    realRunExecuted: true,
    preflight,
    productionSideEffects: ZERO_PRODUCTION_SIDE_EFFECTS,
    readinessClaimed: false,
  };
}

function buildEvidenceSurface({ result, runId, manifest, args, startedAt }) {
  return {
    runId,
    startedAt,
    runnerVersion: RUNNER_VERSION,
    protocol: PROTOCOL,
    manifestProtocol: manifest.protocol || MANIFEST_PROTOCOL,
    operatorId: args.operatorId,
    requestedMode: args.mode,
    hardCap: args.hardCap,
    allowFullBook: args.allowFullBook,
    cleaner: args.cleaner,
    liveSideEffectsEnabled: false,
    manifest: {
      path: manifest.path,
      sha256: manifest.sha256,
      sampleCount: Array.isArray(manifest.samples) ? manifest.samples.length : null,
      samples: Array.isArray(manifest.samples)
        ? manifest.samples.map((sample, index) => ({
            order: index + 1,
            sampleId: sample.sampleId,
            rawBundleDir: sample.rawBundleDir,
            chapterId: sample.chapterId || null,
            title: sample.title || null,
          }))
        : null,
    },
    summary: {
      ok: result.ok === true,
      realRunExecuted: result.realRunExecuted === true,
      attemptedSampleCount: result.attemptedSampleCount || 0,
      completedSampleCount: result.completedSampleCount || 0,
      stopped: result.stopped || null,
      operationCounts: result.operationCounts || null,
      productionSideEffects: ZERO_PRODUCTION_SIDE_EFFECTS,
      readinessClaimed: false,
    },
    samples: Array.isArray(result.samples) ? result.samples : [],
    readinessClaimed: false,
  };
}

async function main() {
  let args;
  try {
    args = parseArgs(process.argv.slice(2));
  } catch (error) {
    return blocked('ARGUMENT_ERROR', error.message);
  }

  if (args.help) {
    return { ok: true, help: usage(), readinessClaimed: false };
  }

  const manifest = await readRunnerManifest(args.manifest);
  if (!manifest.ok) return manifest;

  args.operatorId = args.operatorId || manifest.operatorId;
  args.hardCap = Number(args.hardCap || manifest.hardCap || DEFAULT_HARD_CAP);
  args.cleaner = args.cleaner || manifest.cleaner || DEFAULT_CLEANER;

  const maxHardCap = args.allowFullBook ? MAX_FULL_BOOK_HARD_CAP : MAX_OPERATOR_HARD_CAP;
  if (args.hardCap > maxHardCap) {
    return blocked('ENTRY_HARD_CAP_EXCEEDED', `operator entry hard-cap must be <= ${maxHardCap}`, { requestedHardCap: args.hardCap, maxHardCap, allowFullBook: args.allowFullBook });
  }

  const startedAt = nowIso();
  const result = await runRawCode2CleanCodeUatRunner({
    samples: manifest.samples,
    mode: args.mode,
    operatorId: args.operatorId,
    hardCap: args.hardCap,
    confirmRealRun: args.confirmRealRun,
    outDir: args.out,
    cleaner: args.cleaner,
    model: args.model,
    apiBase: args.apiBase,
    allowFullBook: args.allowFullBook,
    deps: {
      now: () => startedAt,
      manifestSha: manifest.sha256,
    },
  });
  const runId = result.runId || buildRunId({ mode: args.mode, operatorId: args.operatorId, manifestSha: manifest.sha256, startedAt });
  const evidenceSurface = buildEvidenceSurface({ result, runId, manifest, args, startedAt });
  const outputRoot = result.outputRoot || resolve(args.out, runId);
  const cliResult = {
    ...result,
    operatorEntry: {
      type: 'cli',
      command: 'scripts/rawcode2cleancode-runner.mjs',
      manifestSha256: manifest.sha256,
      manifestPath: manifest.path,
      localFileOnly: true,
    },
    evidenceSurface,
    evidenceSurfacePath: join(outputRoot, 'evidence-surface.json'),
    runnerResultPath: join(outputRoot, 'runner-result.json'),
    readinessClaimed: false,
  };

  await writeJson(cliResult.evidenceSurfacePath, evidenceSurface);
  await writeJson(cliResult.runnerResultPath, cliResult);
  return cliResult;
}

export {
  MANIFEST_PROTOCOL,
  RUNNER_VERSION,
  DEFAULT_HARD_CAP,
  MAX_OPERATOR_HARD_CAP,
  buildEvidenceSurface,
  normalizeManifest,
  readRunnerManifest,
  runRawCode2CleanCodeUatRunner,
};

if (process.argv[1] && resolve(process.argv[1]) === __filename) {
  main()
    .then((result) => {
      if (result.help) {
        console.log(result.help);
      } else {
        console.log(stableJson(result));
      }
      process.exit(result.ok === false ? 1 : 0);
    })
    .catch((error) => {
      console.error(stableJson(blocked('UNHANDLED_RAWCODE2CLEANCODE_RUNNER_ERROR', error.message)));
      process.exit(1);
    });
}
