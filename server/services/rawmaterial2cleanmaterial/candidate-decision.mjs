import {
  RAW2CLEAN_DURABLE_ASSET_VERSION,
  RAW2CLEAN_DURABLE_BUCKET,
  RAW2CLEAN_DURABLE_JOB_ID,
  RAW2CLEAN_DURABLE_OBJECT,
  RAW2CLEAN_DURABLE_SERVICE_NAME,
  hasFullRaw2CleanCandidateContent,
} from './durable-candidate.mjs';

export const RAW2CLEAN_DECISION_MATERIAL_ID = '1842780526581841';
export const RAW2CLEAN_DECISION_TASK_ID = 'task-1779085089451';
export const RAW2CLEAN_ACCEPTED_DECISION_SHA = '49a6189e12fe1c65ffdfbdf2e5b73d204c432002dff55812dc8c3be17ac2ce27';
export const RAW2CLEAN_ACCEPTED_DECISION_SIZE = 21767;

function blocked(code, reason, details = undefined) {
  return details ? { ok: false, code, reason, details } : { ok: false, code, reason };
}

function asRecord(value) {
  return value && typeof value === 'object' && !Array.isArray(value) ? value : null;
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function refFromCandidate(candidate) {
  const record = asRecord(candidate);
  return record?.artifact?.candidate || record?.artifactRef || record?.candidateObjectRef || null;
}

function sameCandidateRef(ref) {
  return Boolean(ref) &&
    ref.bucket === RAW2CLEAN_DURABLE_BUCKET &&
    ref.object === RAW2CLEAN_DURABLE_OBJECT &&
    ref.sha256 === RAW2CLEAN_ACCEPTED_DECISION_SHA &&
    Number(ref.size_bytes ?? ref.sizeBytes ?? 0) === RAW2CLEAN_ACCEPTED_DECISION_SIZE;
}

function getTaskCandidate(existingTask) {
  return existingTask?.metadata?.rawMaterial2CleanMaterialJobs?.[RAW2CLEAN_DURABLE_SERVICE_NAME] || null;
}

function getMaterialCandidate(existingMaterial) {
  return existingMaterial?.metadata?.rawMaterial2CleanMaterial?.candidates?.[RAW2CLEAN_DURABLE_ASSET_VERSION] ||
    existingMaterial?.metadata?.rawMaterial2CleanMaterial?.currentCandidate ||
    null;
}

function validateCandidateSummary(source, candidate) {
  const record = asRecord(candidate);
  if (!record) return blocked('MISSING_CANDIDATE_METADATA', `${source} raw2clean candidate metadata is missing`);
  if (record.jobId !== RAW2CLEAN_DURABLE_JOB_ID) {
    return blocked('JOB_ID_MISMATCH', `${source} raw2clean job id does not match`, { jobId: record.jobId ?? null });
  }
  if (record.assetVersion !== RAW2CLEAN_DURABLE_ASSET_VERSION) {
    return blocked('ASSET_VERSION_MISMATCH', `${source} raw2clean asset version does not match`, {
      assetVersion: record.assetVersion ?? null,
    });
  }
  const ref = refFromCandidate(record);
  if (!sameCandidateRef(ref)) {
    return blocked('CANDIDATE_REF_MISMATCH', `${source} candidate ObjectRef does not match authorized target`, {
      ref: ref ?? null,
    });
  }
  return { ok: true, candidate: record, ref };
}

export function buildRaw2CleanAcceptedDecisionPlan({
  existingTask = null,
  existingMaterial = null,
  artifactReadback = null,
  now = null,
  decidedBy = 'Luceon',
} = {}) {
  if (String(existingTask?.id || existingTask?.taskId || RAW2CLEAN_DECISION_TASK_ID) !== RAW2CLEAN_DECISION_TASK_ID) {
    return blocked('TASK_SCOPE_MISMATCH', 'task is outside the authorized single-sample decision scope', {
      taskId: existingTask?.id || existingTask?.taskId || null,
    });
  }
  if (String(existingMaterial?.id || existingMaterial?.materialId || RAW2CLEAN_DECISION_MATERIAL_ID) !== RAW2CLEAN_DECISION_MATERIAL_ID) {
    return blocked('MATERIAL_SCOPE_MISMATCH', 'material is outside the authorized single-sample decision scope', {
      materialId: existingMaterial?.id || existingMaterial?.materialId || null,
    });
  }

  const taskCandidateValidation = validateCandidateSummary('task', getTaskCandidate(existingTask));
  if (!taskCandidateValidation.ok) return taskCandidateValidation;
  const materialCandidateValidation = validateCandidateSummary('material', getMaterialCandidate(existingMaterial));
  if (!materialCandidateValidation.ok) return materialCandidateValidation;

  const artifact = asRecord(artifactReadback);
  if (!artifact) return blocked('MISSING_ARTIFACT_READBACK', 'candidate artifact read-back evidence is required');
  if (artifact.status && Number(artifact.status) !== 200) {
    return blocked('ARTIFACT_READBACK_FAILED', 'candidate artifact proxy GET did not return 200', { status: artifact.status });
  }
  if (
    artifact.sha256 !== RAW2CLEAN_ACCEPTED_DECISION_SHA ||
    Number(artifact.size_bytes ?? artifact.sizeBytes ?? 0) !== RAW2CLEAN_ACCEPTED_DECISION_SIZE
  ) {
    return blocked('ARTIFACT_READBACK_MISMATCH', 'candidate artifact read-back does not match authorized SHA/size', {
      sha256: artifact.sha256 ?? null,
      size_bytes: artifact.size_bytes ?? artifact.sizeBytes ?? null,
    });
  }

  const nowValue = typeof now === 'function' ? now() : typeof now === 'string' ? now : new Date().toISOString();
  const candidateRef = {
    bucket: RAW2CLEAN_DURABLE_BUCKET,
    object: RAW2CLEAN_DURABLE_OBJECT,
    sha256: RAW2CLEAN_ACCEPTED_DECISION_SHA,
    size_bytes: RAW2CLEAN_ACCEPTED_DECISION_SIZE,
    content_type: 'application/json',
  };
  const decision = {
    state: 'accepted',
    decision: 'accepted',
    decidedAt: nowValue,
    decidedBy,
    scope: 'single-sample-durable-boundary',
    materialId: RAW2CLEAN_DECISION_MATERIAL_ID,
    taskId: RAW2CLEAN_DECISION_TASK_ID,
    serviceName: RAW2CLEAN_DURABLE_SERVICE_NAME,
    assetVersion: RAW2CLEAN_DURABLE_ASSET_VERSION,
    jobId: RAW2CLEAN_DURABLE_JOB_ID,
    candidate: clone(candidateRef),
    reason: 'Director-approved single-sample durable accepted decision apply',
    boundaries: {
      finalQualityAccepted: false,
      runtimePost: false,
      serviceExecution: false,
      minioMutation: false,
      batch: false,
      readinessClaimed: false,
    },
  };

  const taskCandidate = {
    ...clone(taskCandidateValidation.candidate),
    status: 'accepted',
    cleanState: 'accepted-candidate',
    decision,
    acceptedDecision: decision,
    updatedAt: nowValue,
  };
  const materialCandidate = {
    ...clone(materialCandidateValidation.candidate),
    status: 'accepted',
    cleanState: 'accepted-candidate',
    decision,
    acceptedDecision: decision,
    updatedAt: nowValue,
  };

  const taskMetadata = existingTask?.metadata || {};
  const materialMetadata = existingMaterial?.metadata || {};
  const existingRaw2Clean = materialMetadata.rawMaterial2CleanMaterial || {};

  const taskPatch = {
    metadata: {
      ...taskMetadata,
      rawMaterial2CleanMaterialJobs: {
        ...(taskMetadata.rawMaterial2CleanMaterialJobs || {}),
        [RAW2CLEAN_DURABLE_SERVICE_NAME]: taskCandidate,
      },
    },
  };

  const materialPatch = {
    metadata: {
      ...materialMetadata,
      rawMaterial2CleanMaterial: {
        ...existingRaw2Clean,
        currentCandidate: {
          ...(existingRaw2Clean.currentCandidate || {}),
          serviceName: RAW2CLEAN_DURABLE_SERVICE_NAME,
          jobId: RAW2CLEAN_DURABLE_JOB_ID,
          assetVersion: RAW2CLEAN_DURABLE_ASSET_VERSION,
          artifact: { candidate: clone(candidateRef) },
          status: 'accepted',
          cleanState: 'accepted-candidate',
          decision,
          acceptedDecision: decision,
          updatedAt: nowValue,
        },
        candidates: {
          ...(existingRaw2Clean.candidates || {}),
          [RAW2CLEAN_DURABLE_ASSET_VERSION]: materialCandidate,
        },
        currentDecision: decision,
      },
    },
  };

  if (hasFullRaw2CleanCandidateContent(taskPatch) || hasFullRaw2CleanCandidateContent(materialPatch)) {
    return blocked('FULL_CONTENT_IN_METADATA', 'decision metadata patch would embed full raw2clean candidate content');
  }

  return {
    ok: true,
    shouldApply: true,
    operationLimit: {
      dbPatch: 2,
      minioPutObject: 0,
    },
    materialId: RAW2CLEAN_DECISION_MATERIAL_ID,
    taskId: RAW2CLEAN_DECISION_TASK_ID,
    serviceName: RAW2CLEAN_DURABLE_SERVICE_NAME,
    assetVersion: RAW2CLEAN_DURABLE_ASSET_VERSION,
    jobId: RAW2CLEAN_DURABLE_JOB_ID,
    candidateRef,
    decision,
    taskPatch,
    materialPatch,
    audit: {
      generatedAt: nowValue,
      artifactSha256: artifact.sha256,
      artifactSizeBytes: Number(artifact.size_bytes ?? artifact.sizeBytes),
    },
  };
}
