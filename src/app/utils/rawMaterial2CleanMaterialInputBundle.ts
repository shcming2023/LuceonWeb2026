import type { CleanMaterialSummary, CleanObjectRef, CleanServiceTaskSummary } from '../../store/types';

export const RAW_MATERIAL_2_CLEAN_MATERIAL_INPUT_KIND = 'raw-material-2-clean-material-input' as const;
export const RAW_MATERIAL_2_CLEAN_MATERIAL_SERVICE_NAME = 'toc-rebuild' as const;

export const REQUIRED_RAW_MATERIAL_2_CLEAN_MATERIAL_ARTIFACT_ROLES = [
  'readable_tree',
  'logic_tree',
  'skeleton',
  'flooded_content',
] as const;

export const OPTIONAL_RAW_MATERIAL_2_CLEAN_MATERIAL_ARTIFACT_ROLES = [
  'metrics',
  'provenance',
  'unresolved_anchors',
] as const;

export type RequiredRawMaterial2CleanMaterialArtifactRole =
  typeof REQUIRED_RAW_MATERIAL_2_CLEAN_MATERIAL_ARTIFACT_ROLES[number];

export type OptionalRawMaterial2CleanMaterialArtifactRole =
  typeof OPTIONAL_RAW_MATERIAL_2_CLEAN_MATERIAL_ARTIFACT_ROLES[number];

export type RawMaterial2CleanMaterialArtifactRole =
  | RequiredRawMaterial2CleanMaterialArtifactRole
  | OptionalRawMaterial2CleanMaterialArtifactRole;

export type RawMaterial2CleanMaterialInputBundleBlockedCode =
  | 'MATERIAL_MISSING'
  | 'TASK_MISSING'
  | 'UNSUPPORTED_SERVICE_NAME'
  | 'MISSING_CLEAN_MATERIAL_SUMMARY'
  | 'MISSING_CLEAN_SERVICE_TASK_SUMMARY'
  | 'MATERIAL_TASK_MISMATCH'
  | 'CLEAN_MATERIAL_NOT_ACCEPTED'
  | 'CLEAN_SERVICE_NOT_COMPLETED'
  | 'MISSING_ASSET_VERSION'
  | 'ASSET_VERSION_MISMATCH'
  | 'MISSING_JOB_ID'
  | 'JOB_ID_MISMATCH'
  | 'MISSING_PROVENANCE_OBJECT'
  | 'MISSING_SOURCE_INPUT'
  | 'MISSING_REQUIRED_ARTIFACT'
  | 'ARTIFACT_PREFIX_MISMATCH'
  | 'ARTIFACT_BODY_READ_REQUIRED';

export interface RawMaterial2CleanMaterialInputBundleObjectRef {
  bucket?: string;
  object: string;
  sha256?: string;
  size_bytes?: number;
  content_type?: string;
}

export interface RawMaterial2CleanMaterialSourceInputRef
  extends RawMaterial2CleanMaterialInputBundleObjectRef {
  sha256: string;
}

export interface RawMaterial2CleanMaterialInputBundle {
  kind: typeof RAW_MATERIAL_2_CLEAN_MATERIAL_INPUT_KIND;
  serviceName: typeof RAW_MATERIAL_2_CLEAN_MATERIAL_SERVICE_NAME;
  materialId: string;
  taskId: string;
  assetVersion: string;
  jobId: string;
  provenanceObjectName: string;
  sourceInput: RawMaterial2CleanMaterialSourceInputRef;
  artifactRefs: Record<RawMaterial2CleanMaterialArtifactRole, RawMaterial2CleanMaterialInputBundleObjectRef>;
  operatorDecision: {
    state: 'accepted';
    decidedAt?: string;
    decidedBy?: string;
  };
}

export interface BuildRawMaterial2CleanMaterialInputBundleInput {
  material?: {
    id?: string | number | null;
    metadata?: Record<string, unknown> | null;
  } | null;
  task?: {
    id?: string | number | null;
    materialId?: string | number | null;
    metadata?: Record<string, unknown> | null;
  } | null;
  serviceName?: string;
  currentAssetVersion?: string | null;
}

export type BuildRawMaterial2CleanMaterialInputBundleResult =
  | {
      ok: true;
      bundle: RawMaterial2CleanMaterialInputBundle;
    }
  | {
      ok: false;
      code: RawMaterial2CleanMaterialInputBundleBlockedCode;
      reason: string;
      details?: Record<string, unknown>;
    };

function blocked(
  code: RawMaterial2CleanMaterialInputBundleBlockedCode,
  reason: string,
  details?: Record<string, unknown>,
): BuildRawMaterial2CleanMaterialInputBundleResult {
  return details ? { ok: false, code, reason, details } : { ok: false, code, reason };
}

function asRecord(value: unknown): Record<string, unknown> | null {
  return value && typeof value === 'object' && !Array.isArray(value)
    ? value as Record<string, unknown>
    : null;
}

function compactString(value: unknown): string | null {
  if (typeof value === 'string' && value.trim()) return value.trim();
  if (typeof value === 'number' && Number.isFinite(value)) return String(value);
  return null;
}

function pickString(...values: unknown[]): string | null {
  for (const value of values) {
    const clean = compactString(value);
    if (clean) return clean;
  }
  return null;
}

function normalizeObjectRef(value: unknown): RawMaterial2CleanMaterialInputBundleObjectRef | null {
  const record = asRecord(value);
  const object = compactString(record?.object);
  if (!record || !object) return null;

  const ref: RawMaterial2CleanMaterialInputBundleObjectRef = { object };
  const bucket = compactString(record.bucket);
  const sha256 = compactString(record.sha256);
  const contentType = pickString(record.content_type, record.contentType);
  const sizeBytes = typeof record.size_bytes === 'number'
    ? record.size_bytes
    : typeof record.sizeBytes === 'number'
      ? record.sizeBytes
      : null;

  if (bucket) ref.bucket = bucket;
  if (sha256) ref.sha256 = sha256;
  if (typeof sizeBytes === 'number' && Number.isFinite(sizeBytes)) ref.size_bytes = sizeBytes;
  if (contentType) ref.content_type = contentType;

  return ref;
}

function normalizeSourceInput(value: unknown): RawMaterial2CleanMaterialSourceInputRef | null {
  const ref = normalizeObjectRef(value);
  if (!ref?.sha256) return null;
  return {
    ...ref,
    sha256: ref.sha256,
  };
}

function hasArtifactBody(value: unknown): boolean {
  const record = asRecord(value);
  return Boolean(
    record
      && ('content' in record || 'body' in record || 'text' in record || 'json' in record || 'data' in record),
  );
}

function getServiceSummary<T>(metadata: Record<string, unknown> | null | undefined, mapName: string, serviceName: string): T | null {
  const map = asRecord(metadata?.[mapName]);
  return asRecord(map?.[serviceName]) as T | null;
}

function artifactRefsFromSnapshot(operatorDecision: Record<string, unknown> | null): Record<string, unknown> | null {
  const snapshot = asRecord(operatorDecision?.artifactSnapshot);
  return asRecord(snapshot?.artifactRefs);
}

function expectedArtifactPrefix(serviceName: string, materialId: string, assetVersion: string): string {
  return `${serviceName}/${materialId}/${assetVersion}/`;
}

export function buildRawMaterial2CleanMaterialInputBundle({
  material,
  task,
  serviceName = RAW_MATERIAL_2_CLEAN_MATERIAL_SERVICE_NAME,
  currentAssetVersion,
}: BuildRawMaterial2CleanMaterialInputBundleInput): BuildRawMaterial2CleanMaterialInputBundleResult {
  if (!material) return blocked('MATERIAL_MISSING', 'material is required');
  if (!task) return blocked('TASK_MISSING', 'task is required');
  if (serviceName !== RAW_MATERIAL_2_CLEAN_MATERIAL_SERVICE_NAME) {
    return blocked('UNSUPPORTED_SERVICE_NAME', 'only toc-rebuild can feed the current bundle builder', { serviceName });
  }

  const materialMetadata = asRecord(material.metadata);
  const taskMetadata = asRecord(task.metadata);
  const cleanMaterialSummary = getServiceSummary<CleanMaterialSummary>(materialMetadata, 'cleanMaterials', serviceName);
  if (!cleanMaterialSummary) {
    return blocked('MISSING_CLEAN_MATERIAL_SUMMARY', 'material.metadata.cleanMaterials[serviceName] is required', { serviceName });
  }

  const cleanServiceTaskSummary = getServiceSummary<CleanServiceTaskSummary>(taskMetadata, 'cleanServiceJobs', serviceName);
  if (!cleanServiceTaskSummary) {
    return blocked('MISSING_CLEAN_SERVICE_TASK_SUMMARY', 'task.metadata.cleanServiceJobs[serviceName] is required', { serviceName });
  }

  const materialId = pickString(material.id, cleanMaterialSummary.materialId, cleanServiceTaskSummary.materialId, task.materialId);
  const taskMaterialId = pickString(task.materialId, cleanServiceTaskSummary.materialId, cleanMaterialSummary.materialId, material.id);
  const taskId = pickString(task.id, cleanServiceTaskSummary.parseTaskId);
  if (!materialId) return blocked('MATERIAL_MISSING', 'material id is required');
  if (!taskId) return blocked('TASK_MISSING', 'task id is required');
  if (taskMaterialId && taskMaterialId !== materialId) {
    return blocked('MATERIAL_TASK_MISMATCH', 'task and material point at different material ids', {
      materialId,
      taskMaterialId,
    });
  }

  const operatorDecision = asRecord(cleanMaterialSummary.operatorDecision);
  if (operatorDecision?.state !== 'accepted') {
    return blocked('CLEAN_MATERIAL_NOT_ACCEPTED', 'operatorDecision.state must be accepted', {
      state: operatorDecision?.state ?? null,
    });
  }

  const status = pickString(
    cleanMaterialSummary.status,
    cleanMaterialSummary.cleanState,
    cleanServiceTaskSummary.status,
    cleanServiceTaskSummary.cleanState,
  );
  if (status !== 'completed') {
    return blocked('CLEAN_SERVICE_NOT_COMPLETED', 'clean material service status must be completed', { status });
  }

  const snapshot = asRecord(operatorDecision.artifactSnapshot);
  const discoveredAssetVersion = pickString(
    cleanMaterialSummary.latestVersion,
    cleanMaterialSummary.assetVersion,
    cleanServiceTaskSummary.assetVersion,
    snapshot?.assetVersion,
  );
  if (!discoveredAssetVersion) {
    return blocked('MISSING_ASSET_VERSION', 'current Clean Material asset version is required');
  }

  const expectedAssetVersion = compactString(currentAssetVersion) || discoveredAssetVersion;
  if (discoveredAssetVersion !== expectedAssetVersion) {
    return blocked('ASSET_VERSION_MISMATCH', 'Clean Material asset version does not match the requested current version', {
      assetVersion: discoveredAssetVersion,
      currentAssetVersion: expectedAssetVersion,
    });
  }

  const jobId = pickString(cleanServiceTaskSummary.jobId, snapshot?.jobId);
  if (!jobId) return blocked('MISSING_JOB_ID', 'clean service jobId is required');
  const snapshotJobId = compactString(snapshot?.jobId);
  if (snapshotJobId && snapshotJobId !== jobId) {
    return blocked('JOB_ID_MISMATCH', 'task jobId and operatorDecision snapshot jobId do not match', {
      jobId,
      snapshotJobId,
    });
  }

  const provenanceObjectName = pickString(
    cleanMaterialSummary.provenanceObjectName,
    snapshot?.provenanceObjectName,
    asRecord(cleanServiceTaskSummary.artifacts?.provenance)?.object,
  );
  if (!provenanceObjectName) {
    return blocked('MISSING_PROVENANCE_OBJECT', 'provenanceObjectName is required');
  }

  const sourceInput = normalizeSourceInput(
    cleanMaterialSummary.sourceInput
      || cleanServiceTaskSummary.sourceInput
      || snapshot?.sourceInput,
  );
  if (!sourceInput) {
    return blocked('MISSING_SOURCE_INPUT', 'sourceInput with object and sha256 is required');
  }

  const artifactSource = asRecord(cleanServiceTaskSummary.artifacts) || artifactRefsFromSnapshot(operatorDecision);
  if (!artifactSource) {
    return blocked('MISSING_REQUIRED_ARTIFACT', 'artifact refs are required');
  }

  const prefix = expectedArtifactPrefix(serviceName, materialId, discoveredAssetVersion);
  const artifactRefs = {} as Record<RawMaterial2CleanMaterialArtifactRole, RawMaterial2CleanMaterialInputBundleObjectRef>;
  const roles: RawMaterial2CleanMaterialArtifactRole[] = [
    ...REQUIRED_RAW_MATERIAL_2_CLEAN_MATERIAL_ARTIFACT_ROLES,
    ...OPTIONAL_RAW_MATERIAL_2_CLEAN_MATERIAL_ARTIFACT_ROLES,
  ];

  for (const role of roles) {
    const rawRef = artifactSource[role];
    if (!rawRef) {
      if (REQUIRED_RAW_MATERIAL_2_CLEAN_MATERIAL_ARTIFACT_ROLES.includes(role as RequiredRawMaterial2CleanMaterialArtifactRole)) {
        return blocked('MISSING_REQUIRED_ARTIFACT', `required artifact ref is missing: ${role}`, { role });
      }
      continue;
    }

    if (hasArtifactBody(rawRef)) {
      return blocked('ARTIFACT_BODY_READ_REQUIRED', 'bundle construction must use object refs only, not artifact bodies', { role });
    }

    const ref = normalizeObjectRef(rawRef);
    if (!ref) {
      if (REQUIRED_RAW_MATERIAL_2_CLEAN_MATERIAL_ARTIFACT_ROLES.includes(role as RequiredRawMaterial2CleanMaterialArtifactRole)) {
        return blocked('MISSING_REQUIRED_ARTIFACT', `required artifact object ref is invalid: ${role}`, { role });
      }
      continue;
    }

    if (!ref.object.startsWith(prefix)) {
      return blocked('ARTIFACT_PREFIX_MISMATCH', 'artifact ref points outside the expected Clean Material prefix', {
        role,
        object: ref.object,
        expectedPrefix: prefix,
      });
    }

    artifactRefs[role] = ref;
  }

  if (!provenanceObjectName.startsWith(prefix)) {
    return blocked('ARTIFACT_PREFIX_MISMATCH', 'provenance object points outside the expected Clean Material prefix', {
      object: provenanceObjectName,
      expectedPrefix: prefix,
    });
  }

  return {
    ok: true,
    bundle: {
      kind: RAW_MATERIAL_2_CLEAN_MATERIAL_INPUT_KIND,
      serviceName: RAW_MATERIAL_2_CLEAN_MATERIAL_SERVICE_NAME,
      materialId,
      taskId,
      assetVersion: discoveredAssetVersion,
      jobId,
      provenanceObjectName,
      sourceInput,
      artifactRefs,
      operatorDecision: {
        state: 'accepted',
        ...(compactString(operatorDecision.decidedAt) ? { decidedAt: compactString(operatorDecision.decidedAt) as string } : {}),
        ...(compactString(operatorDecision.decidedBy) ? { decidedBy: compactString(operatorDecision.decidedBy) as string } : {}),
      },
    },
  };
}
