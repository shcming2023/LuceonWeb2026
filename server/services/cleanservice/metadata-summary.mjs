import { getCleanStageLabel, mapCleanStateToTaskIntent } from './states.mjs';

const OBJECT_REF_FIELDS = new Set(['bucket', 'object', 'size_bytes', 'content_type', 'sha256']);

function compactObjectRef(ref) {
  if (!ref || typeof ref !== 'object') return null;
  const compact = {};
  for (const [key, value] of Object.entries(ref)) {
    if (OBJECT_REF_FIELDS.has(key) && value !== undefined && value !== null) {
      compact[key] = value;
    }
  }
  return compact.bucket && compact.object ? compact : null;
}

function compactArtifacts(artifacts = {}) {
  return Object.fromEntries(
    Object.entries(artifacts)
      .map(([key, value]) => [key, compactObjectRef(value)])
      .filter(([, value]) => Boolean(value)),
  );
}

export function buildCleanTaskSummary(job = {}, verification = {}) {
  const cleanState = verification.cleanState || job.cleanState || job.status || 'protocol-failure';
  const stateMapping = mapCleanStateToTaskIntent(cleanState, {
    unresolvedAnchorCount: verification.unresolvedAnchorCount || job.stats?.unresolved_anchor_count,
  });

  return {
    serviceName: job.service_name || job.serviceName || 'toc-rebuild',
    protocolVersion: job.protocol_version || job.protocolVersion || 'v1',
    jobId: job.job_id || job.jobId || null,
    status: cleanState,
    productLabel: getCleanStageLabel(cleanState),
    taskIntent: stateMapping.taskIntent,
    cleanReview: stateMapping.cleanReview,
    materialId: job.material_id || job.materialId || null,
    parseTaskId: job.parse_task_id || job.parseTaskId || null,
    assetVersion: job.asset_version || job.assetVersion || null,
    submittedAt: job.submitted_at || job.submittedAt || null,
    startedAt: job.started_at || job.startedAt || null,
    finishedAt: job.finished_at || job.finishedAt || null,
    artifacts: compactArtifacts(job.artifacts),
    stats: {
      tokensPrompt: job.stats?.tokens?.prompt ?? job.stats?.tokensPrompt ?? verification.tokensPrompt ?? null,
      tokensCompletion: job.stats?.tokens?.completion ?? job.stats?.tokensCompletion ?? verification.tokensCompletion ?? null,
      tokensTotal: job.stats?.tokens?.total ?? job.stats?.tokensTotal ?? verification.tokensTotal ?? null,
      costCnyEstimated: job.stats?.cost_cny_estimated ?? job.stats?.costCnyEstimated ?? verification.costCnyEstimated ?? null,
      costCnyActual: job.stats?.cost_cny_actual ?? job.stats?.costCnyActual ?? verification.costCnyActual ?? null,
      unresolvedAnchorCount: verification.unresolvedAnchorCount ?? job.stats?.unresolved_anchor_count ?? null,
    },
    error: (verification.errors && verification.errors.length > 0)
      ? {
          code: 'verification_failed',
          message: verification.errors.join(', '),
          retriable: false,
        }
      : job.error ? {
          code: job.error.code || 'protocol_error',
          message: job.error.message || String(job.error),
          retriable: job.error.retriable === true,
        } : null,
    warnings: verification.warnings || [],
    updatedAt: verification.updatedAt || job.finished_at || job.updated_at || new Date().toISOString(),
  };
}

export function buildCleanMaterialSummary(job = {}, taskSummary = buildCleanTaskSummary(job)) {
  return {
    serviceName: taskSummary.serviceName,
    latestVersion: taskSummary.assetVersion,
    status: taskSummary.status,
    productLabel: taskSummary.productLabel,
    prefix: job.sink?.prefix || null,
    provenanceObjectName: taskSummary.artifacts?.provenance?.object || null,
    stats: {
      tokensPrompt: taskSummary.stats.tokensPrompt,
      tokensCompletion: taskSummary.stats.tokensCompletion,
      tokensTotal: taskSummary.stats.tokensTotal,
      costCnyActual: taskSummary.stats.costCnyActual,
      unresolvedAnchorCount: taskSummary.stats.unresolvedAnchorCount,
    },
    updatedAt: taskSummary.updatedAt,
  };
}

export function buildCleanMetadataPatch(job = {}, verification = {}) {
  const taskSummary = buildCleanTaskSummary(job, verification);
  const materialSummary = buildCleanMaterialSummary(job, taskSummary);
  const serviceName = taskSummary.serviceName;
  return {
    taskMetadata: {
      cleanServiceJobs: {
        [serviceName]: taskSummary,
      },
    },
    materialMetadata: {
      cleanMaterials: {
        [serviceName]: materialSummary,
      },
    },
  };
}

export function buildVerifiedCleanOutputMetadataCandidate({ job = {}, verification = {}, now = null }) {
  const getNow = typeof now === 'function' ? now : () => new Date().toISOString();

  // 1. Source input 提取与溯源补偿逻辑
  const vSourceInput = verification.sourceInput || {};
  const provenanceObj = job.provenance || {};
  const provInput = (provenanceObj.inputs && Array.isArray(provenanceObj.inputs) && provenanceObj.inputs[0])
    || provenanceObj.input
    || {};

  const bucket = vSourceInput.bucket || provInput.bucket || null;
  const object = vSourceInput.object || provInput.object || null;
  const sha256 = vSourceInput.sha256 || vSourceInput.sha256_hex || provInput.sha256 || provInput.sha256_hex || null;
  const inputSizeBytes = verification.inputSizeBytes ?? vSourceInput.sizeBytes ?? vSourceInput.size_bytes ?? provInput.size_bytes ?? provInput.sizeBytes ?? null;

  const sourceInput = {
    bucket,
    object,
    sha256,
    sizeBytes: inputSizeBytes,
  };

  const serviceName = job.service_name || job.serviceName || 'toc-rebuild';
  const materialId = job.material_id || job.materialId || null;
  const parseTaskId = job.parse_task_id || job.parseTaskId || null;
  const assetVersion = job.asset_version || job.assetVersion || null;
  const jobId = job.job_id || job.jobId || null;

  // 2. 溯源契约缺口检查（当验证结果 ok 时，如果核心数据缺失，则执行 stop-rule 阻断）
  let isBlocked = false;
  const errors = [...(verification.errors || [])];
  if (verification.ok === true && (!bucket || !object || !sha256)) {
    isBlocked = true;
    errors.push('BLOCKED_VERIFIER_CONTRACT_GAP');
  }

  const isOk = verification.ok === true && !isBlocked;

  let costSource = 'unavailable';
  const hasJobStatsCost = job.stats && (
    (job.stats.cost_cny_estimated !== undefined && job.stats.cost_cny_estimated !== null) ||
    (job.stats.costCnyEstimated !== undefined && job.stats.costCnyEstimated !== null) ||
    (job.stats.cost_cny_actual !== undefined && job.stats.cost_cny_actual !== null) ||
    (job.stats.costCnyActual !== undefined && job.stats.costCnyActual !== null)
  );

  const hasVerificationCost = verification && (
    (verification.costCnyEstimated !== undefined && verification.costCnyEstimated !== null) ||
    (verification.costCnyActual !== undefined && verification.costCnyActual !== null)
  );

  if (hasJobStatsCost) {
    costSource = 'job-stats';
  } else if (hasVerificationCost) {
    costSource = 'verification/candidate';
  }

  const verificationSummary = {
    ok: isOk,
    cleanState: isOk ? (verification.cleanState || 'completed') : 'protocol-failure',
    errors,
    warnings: verification.warnings || [],
    unresolvedAnchorCount: verification.unresolvedAnchorCount || 0,
    inputSizeBytes,
    sourceInput,
    costSource,
  };

  if (!isOk) {
    return {
      ok: false,
      shouldPersist: false,
      serviceName,
      materialId,
      parseTaskId,
      assetVersion,
      jobId,
      cleanState: isOk ? (verification.cleanState || 'completed') : 'protocol-failure',
      metadataPatch: null,
      verificationSummary,
    };
  }

  const targetTime = getNow();
  const enhancedVerification = {
    ...verification,
    updatedAt: targetTime,
  };

  const metadataPatch = buildCleanMetadataPatch(job, enhancedVerification);

  return {
    ok: true,
    shouldPersist: true,
    serviceName,
    materialId,
    parseTaskId,
    assetVersion,
    jobId,
    cleanState: verification.cleanState || 'completed',
    metadataPatch,
    verificationSummary,
  };
}
