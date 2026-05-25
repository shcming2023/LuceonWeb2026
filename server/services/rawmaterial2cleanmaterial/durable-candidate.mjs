export const RAW2CLEAN_DURABLE_SERVICE_NAME = 'raw-material-2-clean-material';
export const RAW2CLEAN_DURABLE_ASSET_VERSION = 'v1';
export const RAW2CLEAN_DURABLE_JOB_ID = 'luceon-task-1779085089451-raw2clean-v1';
export const RAW2CLEAN_DURABLE_BUCKET = 'eduassets-clean';
export const RAW2CLEAN_DURABLE_OBJECT = 'raw-material-2-clean-material/1842780526581841/v1/candidate.json';

const EXPECTED = Object.freeze({
  materialId: '1842780526581841',
  taskId: 'task-1779085089451',
  sourceServiceName: 'toc-rebuild',
  sourceAssetVersion: 'v4',
});

function blocked(code, reason, details = undefined) {
  return details ? { ok: false, code, reason, details } : { ok: false, code, reason };
}

function asRecord(value) {
  return value && typeof value === 'object' && !Array.isArray(value) ? value : null;
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function isSameObjectRef(left, right) {
  return Boolean(left && right) &&
    left.bucket === right.bucket &&
    left.object === right.object &&
    left.sha256 === right.sha256 &&
    Number(left.size_bytes ?? left.sizeBytes ?? 0) === Number(right.size_bytes ?? right.sizeBytes ?? 0);
}

export function hasFullRaw2CleanCandidateContent(value) {
  const serialized = JSON.stringify(value || {});
  if (serialized.includes('"sections"') || serialized.includes('"blocks"') || serialized.includes('"canonicalJson"')) {
    return true;
  }

  const stack = [value];
  while (stack.length > 0) {
    const item = stack.pop();
    if (!item || typeof item !== 'object') continue;
    for (const [key, child] of Object.entries(item)) {
      if (typeof child === 'string' && child.length > 1000) return true;
      if (key === 'candidateJson' || key === 'output') return true;
      if (child && typeof child === 'object') stack.push(child);
    }
  }
  return false;
}

function validateOutput(output) {
  const record = asRecord(output);
  if (!record) return blocked('MISSING_OUTPUT', 'candidate output is required');
  if (record.kind !== 'raw-material-2-clean-material-output-candidate') {
    return blocked('UNSUPPORTED_OUTPUT_KIND', 'output kind is not supported', { kind: record.kind });
  }
  if (record.contractVersion !== 'v0.dry-run') {
    return blocked('UNSUPPORTED_CONTRACT_VERSION', 'output contract version is not supported', { contractVersion: record.contractVersion });
  }
  if (String(record.materialId) !== EXPECTED.materialId || String(record.taskId) !== EXPECTED.taskId) {
    return blocked('SCOPE_MISMATCH', 'output does not match the authorized single-sample target', {
      materialId: record.materialId,
      taskId: record.taskId,
    });
  }

  const sourceCleanMaterial = asRecord(record.sourceCleanMaterial);
  if (
    sourceCleanMaterial?.serviceName !== EXPECTED.sourceServiceName ||
    sourceCleanMaterial?.assetVersion !== EXPECTED.sourceAssetVersion
  ) {
    return blocked('SOURCE_CLEAN_MATERIAL_MISMATCH', 'source clean material is outside the authorized v4 target', {
      sourceCleanMaterial,
    });
  }

  const preview = asRecord(record.preview);
  if (!preview || typeof preview.sha256 !== 'string' || !/^[a-f0-9]{64}$/.test(preview.sha256)) {
    return blocked('MISSING_PREVIEW_SHA', 'output preview sha256 is required');
  }
  if (typeof preview.size_bytes !== 'number' || preview.size_bytes <= 0) {
    return blocked('MISSING_PREVIEW_SIZE', 'output preview size_bytes is required');
  }

  const sections = Array.isArray(record.sections) ? record.sections : [];
  const blocks = Array.isArray(record.blocks) ? record.blocks : [];
  if (sections.some((item) => !item?.sourceRef) || blocks.some((item) => !item?.sourceRef)) {
    return blocked('MISSING_SOURCE_REFERENCE', 'all output sections and blocks must keep source refs');
  }

  return { ok: true };
}

function validateArtifactPreview(preview) {
  const record = asRecord(preview);
  if (!record || typeof record.sha256 !== 'string' || !/^[a-f0-9]{64}$/.test(record.sha256)) {
    return blocked('MISSING_ARTIFACT_SHA', 'candidate artifact sha256 is required');
  }
  if (typeof record.size_bytes !== 'number' || record.size_bytes <= 0) {
    return blocked('MISSING_ARTIFACT_SIZE', 'candidate artifact size_bytes is required');
  }
  return {
    ok: true,
    preview: {
      contentType: record.contentType || record.content_type || 'application/json',
      size_bytes: record.size_bytes,
      sha256: record.sha256,
    },
  };
}

function existingCandidateRefs(existingTask, existingMaterial) {
  const taskJob = existingTask?.metadata?.rawMaterial2CleanMaterialJobs?.[RAW2CLEAN_DURABLE_SERVICE_NAME] || null;
  const materialCandidate =
    existingMaterial?.metadata?.rawMaterial2CleanMaterial?.candidates?.[RAW2CLEAN_DURABLE_ASSET_VERSION] ||
    existingMaterial?.metadata?.rawMaterial2CleanMaterial?.currentCandidate ||
    null;
  return { taskJob, materialCandidate };
}

function validateExistingMetadata(existingTask, existingMaterial, candidateRef) {
  const { taskJob, materialCandidate } = existingCandidateRefs(existingTask, existingMaterial);
  for (const [source, candidate] of [['task', taskJob], ['material', materialCandidate]]) {
    if (!candidate) continue;
    const artifactRef = candidate.artifact?.candidate || candidate.artifactRef || candidate.candidateObjectRef;
    const sameJob = candidate.jobId === RAW2CLEAN_DURABLE_JOB_ID;
    const sameVersion = candidate.assetVersion === RAW2CLEAN_DURABLE_ASSET_VERSION;
    const sameRef = isSameObjectRef(artifactRef, candidateRef);
    if (!(sameJob && sameVersion && sameRef)) {
      return blocked('INCOMPATIBLE_EXISTING_METADATA', `existing ${source} raw2clean metadata is incompatible`, {
        source,
        jobId: candidate.jobId ?? null,
        assetVersion: candidate.assetVersion ?? null,
        artifactRef: artifactRef ?? null,
      });
    }
  }
  return { ok: true };
}

function summarizeOutput(output, candidateRef, artifactPreview, nowValue) {
  const sourceRefs = new Set([
    ...(output.sections || []).map((item) => item.sourceRef),
    ...(output.blocks || []).map((item) => item.sourceRef),
  ]);
  return {
    serviceName: RAW2CLEAN_DURABLE_SERVICE_NAME,
    protocolVersion: output.contractVersion,
    jobId: RAW2CLEAN_DURABLE_JOB_ID,
    status: 'candidate',
    cleanState: 'candidate',
    productLabel: 'Raw2Clean candidate output',
    materialId: String(output.materialId),
    parseTaskId: String(output.taskId),
    assetVersion: RAW2CLEAN_DURABLE_ASSET_VERSION,
    sourceCleanMaterial: clone(output.sourceCleanMaterial),
    sourceInput: clone(output.sourceInput),
    sourceArtifacts: clone(output.sourceArtifacts),
    artifact: {
      candidate: candidateRef,
    },
    stats: {
      sectionCount: output.sections.length,
      blockCount: output.blocks.length,
      sourceRefCount: sourceRefs.size,
      outputContractSizeBytes: output.preview.size_bytes,
      candidateArtifactSizeBytes: artifactPreview.size_bytes,
    },
    preview: {
      candidateArtifact: clone(artifactPreview),
      outputContract: clone(output.preview),
    },
    warnings: Array.isArray(output.warnings) ? [...output.warnings] : [],
    boundaries: {
      durableCandidateArtifactCreated: true,
      dbMetadataPatched: true,
      runtimePost: false,
      serviceExecution: false,
      finalQualityAccepted: false,
      readinessClaimed: false,
    },
    updatedAt: nowValue,
  };
}

export function buildRaw2CleanDurableCandidatePlan({
  output,
  existingTask = null,
  existingMaterial = null,
  candidateArtifactPreview = null,
  now = null,
} = {}) {
  const validation = validateOutput(output);
  if (!validation.ok) return validation;
  const artifactPreviewResult = validateArtifactPreview(candidateArtifactPreview || output.preview);
  if (!artifactPreviewResult.ok) return artifactPreviewResult;
  const artifactPreview = artifactPreviewResult.preview;

  const nowValue = typeof now === 'function' ? now() : typeof now === 'string' ? now : new Date().toISOString();
  const candidateRef = {
    bucket: RAW2CLEAN_DURABLE_BUCKET,
    object: RAW2CLEAN_DURABLE_OBJECT,
    sha256: artifactPreview.sha256,
    size_bytes: artifactPreview.size_bytes,
    content_type: 'application/json',
  };

  const existingValidation = validateExistingMetadata(existingTask, existingMaterial, candidateRef);
  if (!existingValidation.ok) return existingValidation;

  const summary = summarizeOutput(output, candidateRef, artifactPreview, nowValue);
  const taskMetadata = existingTask?.metadata || {};
  const materialMetadata = existingMaterial?.metadata || {};
  const existingRaw2Clean = materialMetadata.rawMaterial2CleanMaterial || {};

  const taskPatch = {
    metadata: {
      ...taskMetadata,
      rawMaterial2CleanMaterialJobs: {
        ...(taskMetadata.rawMaterial2CleanMaterialJobs || {}),
        [RAW2CLEAN_DURABLE_SERVICE_NAME]: summary,
      },
    },
  };

  const materialPatch = {
    metadata: {
      ...materialMetadata,
      rawMaterial2CleanMaterial: {
        ...existingRaw2Clean,
        currentCandidate: {
          serviceName: RAW2CLEAN_DURABLE_SERVICE_NAME,
          jobId: RAW2CLEAN_DURABLE_JOB_ID,
          assetVersion: RAW2CLEAN_DURABLE_ASSET_VERSION,
          artifact: { candidate: candidateRef },
          status: 'candidate',
          updatedAt: nowValue,
        },
        candidates: {
          ...(existingRaw2Clean.candidates || {}),
          [RAW2CLEAN_DURABLE_ASSET_VERSION]: summary,
        },
      },
    },
  };

  if (hasFullRaw2CleanCandidateContent(taskPatch) || hasFullRaw2CleanCandidateContent(materialPatch)) {
    return blocked('FULL_CONTENT_IN_METADATA', 'metadata patch would embed full raw2clean candidate content');
  }

  return {
    ok: true,
    shouldApply: true,
    operationLimit: {
      minioPutObject: 1,
      dbPatch: 2,
    },
    serviceName: RAW2CLEAN_DURABLE_SERVICE_NAME,
    materialId: EXPECTED.materialId,
    taskId: EXPECTED.taskId,
    assetVersion: RAW2CLEAN_DURABLE_ASSET_VERSION,
    jobId: RAW2CLEAN_DURABLE_JOB_ID,
    candidateRef,
    taskPatch,
    materialPatch,
    audit: {
      generatedAt: nowValue,
      sectionCount: summary.stats.sectionCount,
      blockCount: summary.stats.blockCount,
      sourceRefCount: summary.stats.sourceRefCount,
    },
  };
}
