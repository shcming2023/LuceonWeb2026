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
      tokensTotal: job.stats?.tokens?.total ?? job.stats?.tokensTotal ?? null,
      costCnyEstimated: job.stats?.cost_cny_estimated ?? job.stats?.costCnyEstimated ?? null,
      costCnyActual: job.stats?.cost_cny_actual ?? job.stats?.costCnyActual ?? null,
      unresolvedAnchorCount: verification.unresolvedAnchorCount ?? job.stats?.unresolved_anchor_count ?? null,
    },
    error: job.error ? {
      code: job.error.code || 'protocol_error',
      message: job.error.message || String(job.error),
      retriable: job.error.retriable === true,
    } : null,
    updatedAt: job.finished_at || job.updated_at || new Date().toISOString(),
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
