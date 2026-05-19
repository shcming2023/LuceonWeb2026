export function buildCanonicalRawMaterialRef(task) {
  const metadata = task?.metadata || {};

  const parsedFilesCount = Number(metadata.parsedFilesCount || 0);
  const hasLegacy = Boolean(metadata.artifactManifestObjectName) ||
    Boolean(metadata.markdownObjectName) ||
    (Boolean(metadata.parsedPrefix) && parsedFilesCount > 0);

  const rawMaterial = metadata.rawMaterial;
  const contentListV2 = rawMaterial?.mineru?.contentListV2;

  if (!contentListV2) {
    if (hasLegacy) {
      const error = new Error('legacy-parsed-evidence-skipped');
      error.code = 'skipped-policy';
      throw error;
    }
    const error = new Error('no-raw-material-evidence');
    error.code = 'not-applicable';
    throw error;
  }

  const { bucket, object, sha256 } = contentListV2;

  if (bucket !== 'eduassets-raw') {
    throw new Error('invalid-raw-material: bucket must be eduassets-raw');
  }

  if (!object || typeof object !== 'string') {
    throw new Error('invalid-raw-material: missing object');
  }

  if (!object.endsWith('/content_list_v2.json')) {
    throw new Error('invalid-raw-material: object must end with /content_list_v2.json');
  }

  const materialId = task.materialId;
  const assetVersion = rawMaterial.version || 'v1';

  if (!object.startsWith(`mineru/${materialId}/${assetVersion}/`)) {
    throw new Error('invalid-raw-material: object path mismatch');
  }

  return {
    role: 'mineru-content',
    source: {
      type: 'minio',
      bucket,
      object,
    },
    ...(sha256 ? { hash: sha256 } : {}),
  };
}
