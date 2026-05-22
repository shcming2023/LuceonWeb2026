const REQUIRED_TRACE_ARTIFACTS = Object.freeze([
  'flooded_content',
  'logic_tree',
  'readable_tree',
  'skeleton',
  'unresolved_anchors',
  'metrics',
  'provenance',
]);

function isObjectRef(ref) {
  return Boolean(ref) &&
    typeof ref === 'object' &&
    typeof ref.bucket === 'string' &&
    ref.bucket.trim().length > 0 &&
    typeof ref.object === 'string' &&
    ref.object.trim().length > 0;
}

/**
 * Builds the dry-run metadata persistence plan for CleanService.
 *
 * @param {Object} params
 * @param {Object} params.candidate The verified candidate object built by buildVerifiedCleanOutputMetadataCandidate.
 * @param {Object} [params.existingTask] The existing task record from the DB (if any).
 * @param {Object} [params.existingMaterial] The existing material record from the DB (if any).
 * @param {Function} [params.now] Timestamp generator function.
 * @returns {Object} Persistence plan.
 */
export function buildCleanMetadataPersistencePlan({
  candidate,
  existingTask = null,
  existingMaterial = null,
  now = null,
}) {
  const getNow = typeof now === 'function' ? now : () => new Date().toISOString();

  // 1. Check if candidate is valid/persistable
  if (!candidate || candidate.ok !== true || candidate.shouldPersist !== true) {
    return {
      ok: false,
      shouldApply: false,
      dryRun: true,
      taskPatch: null,
      materialPatch: null,
      reason: 'candidate-not-persistable',
      errors: candidate?.verificationSummary?.errors || [],
    };
  }

  const serviceName = candidate.serviceName || 'toc-rebuild';
  const materialId = candidate.materialId;
  const parseTaskId = candidate.parseTaskId;

  // 2. Gate Check: Task Summary existence
  const taskSummary = candidate.metadataPatch?.taskMetadata?.cleanServiceJobs?.[serviceName];
  if (!taskSummary) {
    return {
      ok: false,
      shouldApply: false,
      dryRun: true,
      taskPatch: null,
      materialPatch: null,
      reason: 'missing-task-summary',
    };
  }

  // 3. Gate Check: Material Summary existence
  const materialSummary = candidate.metadataPatch?.materialMetadata?.cleanMaterials?.[serviceName];
  if (!materialSummary) {
    return {
      ok: false,
      shouldApply: false,
      dryRun: true,
      taskPatch: null,
      materialPatch: null,
      reason: 'missing-material-summary',
    };
  }

  // 4. Gate Check: Traceability - Source Input
  const sourceInput = candidate.verificationSummary?.sourceInput || {};
  if (!sourceInput.bucket || !sourceInput.object || !sourceInput.sha256) {
    return {
      ok: false,
      shouldApply: false,
      dryRun: true,
      taskPatch: null,
      materialPatch: null,
      reason: 'missing-source-input',
    };
  }

  // 5. Gate Check: Traceability - Seven Artifact Refs
  const artifacts = taskSummary.artifacts || {};
  for (const role of REQUIRED_TRACE_ARTIFACTS) {
    if (!isObjectRef(artifacts[role])) {
      return {
        ok: false,
        shouldApply: false,
        dryRun: true,
        taskPatch: null,
        materialPatch: null,
        reason: `missing-artifact-ref:${role}`,
      };
    }
  }

  // 6. Gate Check: Traceability - Token Total
  const tokensTotal = taskSummary.stats?.tokensTotal;
  if (typeof tokensTotal !== 'number' || tokensTotal <= 0) {
    return {
      ok: false,
      shouldApply: false,
      dryRun: true,
      taskPatch: null,
      materialPatch: null,
      reason: 'missing-token-total',
    };
  }

  // 7. Safe Shallow-Merge Pre-Merge
  const existingTaskMetadata = existingTask?.metadata || {};
  const existingJobs = existingTaskMetadata.cleanServiceJobs || {};

  const existingMaterialMetadata = existingMaterial?.metadata || {};
  const existingMaterials = existingMaterialMetadata.cleanMaterials || {};

  // Build safe patches without mutating input arguments
  const taskPatch = {
    metadata: {
      ...existingTaskMetadata,
      cleanServiceJobs: {
        ...existingJobs,
        [serviceName]: {
          ...taskSummary,
        },
      },
    },
  };

  const materialPatch = {
    metadata: {
      ...existingMaterialMetadata,
      cleanMaterials: {
        ...existingMaterials,
        [serviceName]: {
          ...materialSummary,
        },
      },
    },
  };

  // 8. Cost Source Classification & Audit Summary
  const costSource = candidate.verificationSummary?.costSource || 'unavailable';

  return {
    ok: true,
    shouldApply: true,
    dryRun: true,
    serviceName,
    materialId,
    parseTaskId,
    taskPatch,
    materialPatch,
    audit: {
      costSource,
      tokensTotal,
      cleanState: taskSummary.status,
      timestamp: getNow(),
    },
  };
}
