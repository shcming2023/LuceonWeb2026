#!/usr/bin/env node
import { readFile, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { resolve } from 'node:path';
import {
  RAW2CLEAN_OPERATOR_RUNNER_DEFAULT_HARD_CAP,
  buildRaw2CleanOperatorRunnerSample,
  runRawMaterial2CleanMaterialOperatorRunner,
} from '../server/services/rawmaterial2cleanmaterial/operator-runner.mjs';

const MAX_OPERATOR_HARD_CAP = 3;

function usage() {
  return [
    'Usage:',
    '  node scripts/raw2clean-operator-runner.mjs --manifest <file> --operator-id <id> [--mode dry-run] [--out <file>]',
    '',
    'Boundaries:',
    '  dry-run is the default mode.',
    '  hard-cap is capped at 3.',
    '  real mode requires --confirm-real.',
    '  processor defaults to fixture; use --processor task288-live only for an explicitly authorized controlled run.',
  ].join('\n');
}

function parseArgs(argv) {
  const args = {
    mode: 'dry-run',
    hardCap: RAW2CLEAN_OPERATOR_RUNNER_DEFAULT_HARD_CAP,
    processor: 'fixture',
    confirmRealRun: false,
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
    } else if (arg === '--processor') {
      args.processor = next();
    } else if (arg === '--confirm-real') {
      args.confirmRealRun = true;
    } else if (arg === '--out') {
      args.out = next();
    } else {
      throw new Error(`unknown argument: ${arg}`);
    }
  }

  return args;
}

function sha256(text) {
  return createHash('sha256').update(text).digest('hex');
}

function stableJson(value) {
  return `${JSON.stringify(value, null, 2)}\n`;
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

function normalizeManifest(parsed) {
  const samples = Array.isArray(parsed) ? parsed : parsed?.samples;
  const manifestDefaults = Array.isArray(parsed) ? {} : parsed || {};
  return {
    operatorId: manifestDefaults.operatorId || null,
    hardCap: manifestDefaults.hardCap || null,
    samples: Array.isArray(samples)
      ? samples.map((sample) => ({
          ...sample,
          ...buildRaw2CleanOperatorRunnerSample(sample),
        }))
      : samples,
  };
}

async function readManifest(path) {
  if (!path) return blocked('MISSING_MANIFEST', 'manifest file is required');
  const absolutePath = resolve(path);
  const raw = await readFile(absolutePath, 'utf8');
  const parsed = JSON.parse(raw);
  return {
    ok: true,
    path: absolutePath,
    sha256: sha256(raw),
    ...normalizeManifest(parsed),
  };
}

function buildRunId({ mode, operatorId, manifestSha, now }) {
  const stamp = now.replace(/[^0-9TZ]/g, '').replace(/Z$/, 'Z');
  const safeOperator = String(operatorId || 'operator').replace(/[^a-zA-Z0-9_-]/g, '-').slice(0, 48);
  return `raw2clean-${mode}-${safeOperator}-${stamp}-${manifestSha.slice(0, 12)}`;
}

function fixtureProcessSample() {
  return async ({ sample, index, mode, phaseLabel }) => {
    const candidateObject = sample.candidateObject
      || `raw-material-2-clean-material/${sample.materialId}/v1/candidate.json`;
    return {
      ok: true,
      stage: 'operator-entry-fixture',
      evidence: {
        rawSeed: sample.rawSeed || null,
        cleanService: {
          jobId: `fixture-${sample.taskId}-toc-rebuild-v1`,
          assetVersion: 'v1',
          submitted: false,
          simulated: true,
          phaseLabel,
        },
        candidate: {
          bucket: 'eduassets-clean',
          object: candidateObject,
          sha256: sha256(`${sample.materialId}:${sample.taskId}:${mode}:${index}`),
          size_bytes: stableJson(sample).length,
          simulated: true,
        },
        dbPatchCount: 0,
        productSurface: {
          discoverable: mode === 'dry-run' ? false : 'simulated',
          simulated: true,
        },
      },
      operationCounts: {},
    };
  };
}

function normalizeLiveSampleResult(result, mode) {
  return {
    ok: result?.ok === true,
    stage: result?.mode || mode,
    evidence: {
      rawSeed: result?.rawSeed
        ? {
            bucket: 'eduassets-raw',
            object: result.sample?.rawObject || null,
            action: result.rawSeed.action,
            sha256: result.rawSeed.sha256,
            size_bytes: result.rawSeed.size_bytes,
          }
        : null,
      cleanService: result?.cleanService
        ? {
            endpoint: result.cleanService.endpoint,
            jobId: result.cleanService.jobId,
            assetVersion: result.cleanService.assetVersion,
            status: result.cleanService.status,
            classification: result.cleanService.classification,
            submitted: Number(result.cleanService.submitCalls || 0) > 0,
            submitCalls: Number(result.cleanService.submitCalls || 0),
            reconciledExistingJob: result.cleanService.reconciledExistingJob === true,
            sectionCount: result.cleanService.sectionCount,
            blockCount: result.cleanService.blockCount,
            artifacts: result.cleanService.artifacts || null,
          }
        : null,
      candidate: result?.candidate?.ref
        ? {
            ...result.candidate.ref,
            action: result.candidate.write?.action || null,
            outputContractPreview: result.candidate.outputContractPreview || null,
          }
        : null,
      dbPatchCount: Number(result?.patchResult?.operationCount || 0),
      productSurface: result?.post
        ? {
            cleanJobId: result.post.cleanJobId || null,
            cleanDecision: result.post.cleanDecision || null,
            raw2cleanTaskStatus: result.post.raw2cleanTaskStatus || null,
            raw2cleanDecision: result.post.raw2cleanDecision || null,
          }
        : null,
    },
    operationCounts: {
      rawSeedPutObject: Number(result?.boundaries?.rawSeedPutObject || 0),
      cleanServicePost: Number(result?.boundaries?.cleanServicePost || 0),
      raw2cleanCandidatePutObject: Number(result?.boundaries?.raw2cleanCandidatePutObject || 0),
      dbPatch: Number(result?.boundaries?.dbPatch || 0),
      minioDelete: Number(result?.boundaries?.minioDelete || 0),
      runtimePostOtherThanCleanService: Number(result?.boundaries?.runtimePostOtherThanCleanService || 0),
      dockerOperation: Number(result?.boundaries?.dockerOperation || 0),
      batch: Number(result?.boundaries?.batch || 0),
    },
  };
}

async function buildLiveTask288Deps() {
  const { processMiniBatchPilotSample } = await import('../server/tests/rawmaterial2cleanmaterial-bounded-mini-batch-pilot.mjs');
  return {
    processor: {
      kind: 'task288-live',
      liveSideEffectsEnabled: true,
      source: 'server/tests/rawmaterial2cleanmaterial-bounded-mini-batch-pilot.mjs',
    },
    deps: {
      processSample: async ({ sample, index, mode }) => {
        const result = await processMiniBatchPilotSample(sample, index, { realApply: mode === 'real' });
        return normalizeLiveSampleResult(result, mode);
      },
    },
  };
}

async function buildDeps(processor) {
  if (processor === 'fixture') {
    return {
      processor: {
        kind: 'fixture',
        liveSideEffectsEnabled: false,
      },
      deps: {
        processSample: fixtureProcessSample(),
      },
    };
  }

  if (processor === 'task288-live') {
    return buildLiveTask288Deps();
  }

  return {
    error: blocked('UNSUPPORTED_PROCESSOR', 'operator entry processor is not supported', {
      processor,
    }),
  };
}

function buildEvidenceSurface({ result, runId, manifest, args, startedAt, processor }) {
  return {
    runId,
    startedAt,
    operatorId: args.operatorId,
    requestedMode: args.mode,
    hardCap: args.hardCap,
    processor: args.processor,
    liveSideEffectsEnabled: processor?.liveSideEffectsEnabled === true,
    manifest: {
      path: manifest.path,
      sha256: manifest.sha256,
      sampleCount: Array.isArray(manifest.samples) ? manifest.samples.length : null,
      samples: Array.isArray(manifest.samples)
        ? manifest.samples.map((sample, index) => ({
            order: index + 1,
            materialId: sample.materialId,
            taskId: sample.taskId,
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
      readinessClaimed: false,
    },
    samples: Array.isArray(result.samples) ? result.samples : [],
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

  const manifest = await readManifest(args.manifest);
  if (!manifest.ok) return manifest;

  args.operatorId = args.operatorId || manifest.operatorId;
  args.hardCap = Number(args.hardCap || manifest.hardCap || RAW2CLEAN_OPERATOR_RUNNER_DEFAULT_HARD_CAP);
  if (args.hardCap > MAX_OPERATOR_HARD_CAP) {
    return blocked('ENTRY_HARD_CAP_EXCEEDED', 'operator entry hard-cap must be <= 3', {
      requestedHardCap: args.hardCap,
      maxHardCap: MAX_OPERATOR_HARD_CAP,
    });
  }

  const processorBundle = await buildDeps(args.processor);
  if (processorBundle.error) return processorBundle.error;

  const startedAt = new Date().toISOString();
  const runId = buildRunId({
    mode: args.mode,
    operatorId: args.operatorId,
    manifestSha: manifest.sha256,
    now: startedAt,
  });
  const runnerResult = await runRawMaterial2CleanMaterialOperatorRunner({
    samples: manifest.samples,
    mode: args.mode,
    hardCap: args.hardCap,
    operatorId: args.operatorId,
    confirmRealRun: args.confirmRealRun,
    deps: {
      ...processorBundle.deps,
      now: () => startedAt,
    },
  });
  const result = {
    ...runnerResult,
    runId,
    operatorEntry: {
      type: 'cli',
      command: 'scripts/raw2clean-operator-runner.mjs',
      processor: processorBundle.processor,
      manifestSha256: manifest.sha256,
      manifestPath: manifest.path,
    },
    evidenceSurface: buildEvidenceSurface({
      result: runnerResult,
      runId,
      manifest,
      args,
      startedAt,
      processor: processorBundle.processor,
    }),
    readinessClaimed: false,
  };

  if (args.out) {
    await writeFile(resolve(args.out), stableJson(result));
  }
  return result;
}

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
    console.error(stableJson(blocked('UNHANDLED_OPERATOR_ENTRY_ERROR', error.message)));
    process.exit(1);
  });
