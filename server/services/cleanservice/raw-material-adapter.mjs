const RAW_BUCKET = 'eduassets-raw';
const DEFAULT_SERVICE_NAME = 'toc-rebuild';
const COMPLETED_STATES = new Set(['completed']);

function hasLegacyParsedEvidence(metadata = {}) {
  const parsedFilesCount = Number(metadata.parsedFilesCount || 0);
  return Boolean(metadata.artifactManifestObjectName) ||
    Boolean(metadata.markdownObjectName) ||
    (Boolean(metadata.parsedPrefix) && parsedFilesCount > 0);
}

function validateContentListV2Source({ task, source, rawMaterialVersion, requireSha256 = false }) {
  const { bucket, object, sha256 } = source || {};

  if (bucket !== RAW_BUCKET) {
    throw new Error('invalid-raw-material: bucket must be eduassets-raw');
  }

  if (!object || typeof object !== 'string') {
    throw new Error('invalid-raw-material: missing object');
  }

  if (!object.endsWith('/content_list_v2.json')) {
    throw new Error('invalid-raw-material: object must end with /content_list_v2.json');
  }

  const materialId = task.materialId;
  const expectedPattern = rawMaterialVersion
    ? new RegExp(`^mineru/${materialId}/${rawMaterialVersion}/content_list_v2\\.json$`)
    : new RegExp(`^mineru/${materialId}/v[^/]+/content_list_v2\\.json$`);

  if (!expectedPattern.test(object)) {
    throw new Error('invalid-raw-material: object path mismatch');
  }

  if (requireSha256 && (!sha256 || typeof sha256 !== 'string')) {
    throw new Error('invalid-raw-material: missing sha256');
  }

  return {
    role: 'mineru-content',
    source: {
      type: 'minio',
      bucket,
      object,
      ...(source.size_bytes !== undefined ? { size_bytes: source.size_bytes } : {}),
      ...(source.sizeBytes !== undefined ? { sizeBytes: source.sizeBytes } : {}),
    },
    ...(sha256 ? { hash: sha256 } : {}),
  };
}

export function buildCanonicalRawMaterialRef(task, { serviceName = DEFAULT_SERVICE_NAME } = {}) {
  const metadata = task?.metadata || {};

  const rawMaterial = metadata.rawMaterial;
  const contentListV2 = rawMaterial?.mineru?.contentListV2;

  if (contentListV2) {
    return validateContentListV2Source({
      task,
      source: contentListV2,
      rawMaterialVersion: rawMaterial.version || 'v1',
    });
  }

  const cleanJob = metadata.cleanServiceJobs?.[serviceName];
  const cleanJobState = cleanJob?.cleanState || cleanJob?.status || cleanJob?.state;
  if (cleanJob?.sourceInput && COMPLETED_STATES.has(cleanJobState)) {
    return validateContentListV2Source({
      task,
      source: cleanJob.sourceInput,
      requireSha256: true,
    });
  }

  if (hasLegacyParsedEvidence(metadata)) {
    const error = new Error('legacy-parsed-evidence-skipped');
    error.code = 'skipped-policy';
    throw error;
  }

  const error = new Error('no-raw-material-evidence');
  error.code = 'not-applicable';
  throw error;
}

export function hasUsableRawMaterialSourceInput(task, { serviceName = DEFAULT_SERVICE_NAME } = {}) {
  try {
    buildCanonicalRawMaterialRef(task, { serviceName });
    return true;
  } catch (err) {
    return false;
  }
}
