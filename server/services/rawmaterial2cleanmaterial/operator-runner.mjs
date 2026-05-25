export const RAW2CLEAN_OPERATOR_RUNNER_DEFAULT_HARD_CAP = 3;

const ZERO_OPERATION_COUNTS = Object.freeze({
  rawSeedPutObject: 0,
  cleanServicePost: 0,
  raw2cleanCandidatePutObject: 0,
  dbPatch: 0,
  minioDelete: 0,
  runtimePostOtherThanCleanService: 0,
  dockerOperation: 0,
  batch: 0,
});

function blocked(code, reason, details = undefined) {
  return details ? { ok: false, code, reason, details } : { ok: false, code, reason };
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

function sampleKey(sample) {
  return `${String(sample?.materialId || '')}::${String(sample?.taskId || '')}`;
}

function normalizeOperationCounts(counts = {}) {
  return {
    ...ZERO_OPERATION_COUNTS,
    ...Object.fromEntries(
      Object.entries(counts || {}).map(([key, value]) => [key, Number(value || 0)]),
    ),
  };
}

function addOperationCounts(left, right) {
  const result = normalizeOperationCounts(left);
  const normalizedRight = normalizeOperationCounts(right);
  for (const [key, value] of Object.entries(normalizedRight)) {
    result[key] = Number(result[key] || 0) + Number(value || 0);
  }
  return result;
}

function validateSamples(samples, hardCap) {
  if (!Array.isArray(samples)) return blocked('SAMPLES_NOT_ARRAY', 'operator sample list must be an array');
  if (samples.length === 0) return blocked('EMPTY_SAMPLE_LIST', 'operator sample list must not be empty');
  if (samples.length > hardCap) {
    return blocked('HARD_CAP_EXCEEDED', 'operator sample list exceeds hard cap', {
      sampleCount: samples.length,
      hardCap,
    });
  }

  const seen = new Set();
  for (const [index, sample] of samples.entries()) {
    if (!sample || typeof sample !== 'object') {
      return blocked('INVALID_SAMPLE', 'operator sample must be an object', { index });
    }
    if (!sample.materialId || !sample.taskId) {
      return blocked('MISSING_SAMPLE_ID', 'operator sample must include materialId and taskId', { index, sample });
    }
    const key = sampleKey(sample);
    if (seen.has(key)) {
      return blocked('DUPLICATE_SAMPLE', 'operator sample list contains duplicate material/task pair', {
        index,
        materialId: String(sample.materialId),
        taskId: String(sample.taskId),
      });
    }
    seen.add(key);
  }

  return { ok: true };
}

function validateMode(mode) {
  if (mode === 'dry-run' || mode === 'real') return { ok: true };
  return blocked('UNSUPPORTED_MODE', 'operator runner mode must be dry-run or real', { mode });
}

function validateRunnerRequest({ samples, mode, hardCap, operatorId, confirmRealRun }) {
  const modeValidation = validateMode(mode);
  if (!modeValidation.ok) return modeValidation;
  const sampleValidation = validateSamples(samples, hardCap);
  if (!sampleValidation.ok) return sampleValidation;
  if (!operatorId) return blocked('MISSING_OPERATOR', 'operatorId is required for operator-triggered runner');
  if (mode === 'real' && confirmRealRun !== true) {
    return blocked('REAL_RUN_NOT_CONFIRMED', 'real mode requires explicit operator confirmation');
  }
  return { ok: true };
}

function summarizeResults(results, mode, stopped = null) {
  const totals = results.reduce((acc, result) => addOperationCounts(acc, result.operationCounts), ZERO_OPERATION_COUNTS);
  return {
    ok: !stopped,
    mode,
    attemptedSampleCount: results.length,
    completedSampleCount: results.filter((result) => result.ok).length,
    stopped,
    operationCounts: totals,
    readinessClaimed: false,
    samples: results,
  };
}

function normalizeSampleResult({ sample, index, mode, result }) {
  const evidence = result?.evidence || {};
  return {
    ok: result?.ok === true,
    mode,
    order: index + 1,
    materialId: String(sample.materialId),
    taskId: String(sample.taskId),
    title: sample.title || null,
    stage: result?.stage || null,
    code: result?.code || null,
    reason: result?.reason || null,
    rawSeed: evidence.rawSeed || null,
    cleanService: evidence.cleanService || null,
    candidate: evidence.candidate || null,
    dbPatchCount: Number(evidence.dbPatchCount || 0),
    productSurface: evidence.productSurface || null,
    operationCounts: normalizeOperationCounts(result?.operationCounts),
    readinessClaimed: false,
  };
}

async function runPhase({ samples, mode, deps, phaseLabel }) {
  const results = [];
  for (const [index, sample] of samples.entries()) {
    const result = await deps.processSample({
      sample: clone(sample),
      index,
      mode,
      phaseLabel,
    });
    const normalized = normalizeSampleResult({ sample, index, mode, result });
    results.push(normalized);
    if (!normalized.ok) {
      return summarizeResults(results, mode, {
        order: index + 1,
        materialId: String(sample.materialId),
        taskId: String(sample.taskId),
        stage: normalized.stage,
        code: normalized.code || 'SAMPLE_FAILED',
        reason: normalized.reason || 'sample failed',
      });
    }
  }
  return summarizeResults(results, mode);
}

export async function runRawMaterial2CleanMaterialOperatorRunner({
  samples,
  mode = 'dry-run',
  hardCap = RAW2CLEAN_OPERATOR_RUNNER_DEFAULT_HARD_CAP,
  operatorId,
  confirmRealRun = false,
  deps = {},
} = {}) {
  const normalizedHardCap = Number(hardCap || RAW2CLEAN_OPERATOR_RUNNER_DEFAULT_HARD_CAP);
  const validation = validateRunnerRequest({
    samples,
    mode,
    hardCap: normalizedHardCap,
    operatorId,
    confirmRealRun,
  });
  if (!validation.ok) return validation;
  if (typeof deps.processSample !== 'function') {
    return blocked('MISSING_PROCESS_SAMPLE_DEP', 'operator runner requires injected processSample dependency');
  }

  const sampleList = asArray(samples).map((sample) => clone(sample));
  const startedAt = typeof deps.now === 'function' ? deps.now() : new Date().toISOString();
  const dryRun = await runPhase({ samples: sampleList, mode: 'dry-run', deps, phaseLabel: 'preflight' });

  if (mode === 'dry-run') {
    return {
      ...dryRun,
      requestedMode: mode,
      hardCap: normalizedHardCap,
      operatorId,
      startedAt,
      realRunExecuted: false,
      preflight: dryRun,
      readinessClaimed: false,
    };
  }

  if (!dryRun.ok) {
    return {
      ok: false,
      requestedMode: mode,
      hardCap: normalizedHardCap,
      operatorId,
      startedAt,
      realRunExecuted: false,
      preflight: dryRun,
      stopped: dryRun.stopped,
      code: 'PREFLIGHT_FAILED',
      reason: 'real run blocked because dry-run preflight failed',
      readinessClaimed: false,
    };
  }

  const realRun = await runPhase({ samples: sampleList, mode: 'real', deps, phaseLabel: 'real' });
  return {
    ...realRun,
    requestedMode: mode,
    hardCap: normalizedHardCap,
    operatorId,
    startedAt,
    realRunExecuted: true,
    preflight: dryRun,
    realRun,
    readinessClaimed: false,
  };
}

export function buildRaw2CleanOperatorRunnerSample({
  materialId,
  taskId,
  title = null,
  rawSeed = null,
  candidateObject = null,
} = {}) {
  return {
    materialId: String(materialId || ''),
    taskId: String(taskId || ''),
    title,
    rawSeed: rawSeed ? clone(rawSeed) : null,
    candidateObject: candidateObject || (materialId
      ? `raw-material-2-clean-material/${materialId}/v1/candidate.json`
      : null),
  };
}
