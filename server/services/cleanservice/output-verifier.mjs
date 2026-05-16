import { CLEAN_STAGE_STATES } from './states.mjs';

export const REQUIRED_CLEAN_ARTIFACTS = Object.freeze([
  'flooded_content',
  'logic_tree',
  'readable_tree',
  'skeleton',
  'provenance',
]);

function isObjectRef(value) {
  return Boolean(value) &&
    typeof value === 'object' &&
    typeof value.bucket === 'string' &&
    value.bucket.length > 0 &&
    typeof value.object === 'string' &&
    value.object.length > 0;
}

function verifyProvenanceShape(provenance, expected = {}) {
  if (!provenance || typeof provenance !== 'object') {
    return ['missing-provenance-shape'];
  }

  const errors = [];
  if (provenance.schema !== 'luceon-provenance/v1') errors.push('invalid-provenance-schema');
  if (expected.serviceName && provenance.service?.name !== expected.serviceName) errors.push('service-name-mismatch');
  if (expected.protocolVersion && provenance.service?.protocol_version !== expected.protocolVersion) errors.push('protocol-version-mismatch');
  if (expected.materialId && provenance.asset?.material_id !== expected.materialId) errors.push('material-id-mismatch');
  if (expected.assetVersion && provenance.asset?.asset_version !== expected.assetVersion) errors.push('asset-version-mismatch');
  if (expected.jobId && provenance.job?.job_id !== expected.jobId) errors.push('job-id-mismatch');
  return errors;
}

export function verifyCleanServiceOutput(job = {}, options = {}) {
  const artifacts = job.artifacts || {};
  const errors = [];

  for (const key of REQUIRED_CLEAN_ARTIFACTS) {
    if (!isObjectRef(artifacts[key])) errors.push(`missing-artifact:${key}`);
  }

  if (artifacts.raw_mineru || artifacts.rawMineru || job.rawMineruOutput === true) {
    errors.push('raw-mineru-output-not-clean-success');
  }
  if (job.placeholderOutput === true || job.skeletonOnly === true) {
    errors.push('placeholder-or-skeleton-output-not-clean-success');
  }

  errors.push(...verifyProvenanceShape(job.provenance, {
    serviceName: options.serviceName || job.service_name,
    protocolVersion: options.protocolVersion || job.protocol_version,
    materialId: job.material_id,
    assetVersion: job.asset_version,
    jobId: job.job_id,
  }));

  const unresolvedAnchorCount = Number(job.stats?.unresolved_anchor_count || 0);
  if (errors.length > 0) {
    return {
      ok: false,
      cleanState: CLEAN_STAGE_STATES.PROTOCOL_FAILURE,
      errors,
      unresolvedAnchorCount,
    };
  }

  if (unresolvedAnchorCount > 0) {
    return {
      ok: true,
      cleanState: CLEAN_STAGE_STATES.REVIEW_PENDING_PARTIAL,
      errors: [],
      unresolvedAnchorCount,
    };
  }

  return {
    ok: true,
    cleanState: CLEAN_STAGE_STATES.COMPLETED,
    errors: [],
    unresolvedAnchorCount,
  };
}
