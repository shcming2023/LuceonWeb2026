import {
  RAW_MATERIAL_2_CLEAN_MATERIAL_INPUT_KIND,
  RAW_MATERIAL_2_CLEAN_MATERIAL_SERVICE_NAME,
  REQUIRED_RAW_MATERIAL_2_CLEAN_MATERIAL_ARTIFACT_ROLES,
  OPTIONAL_RAW_MATERIAL_2_CLEAN_MATERIAL_ARTIFACT_ROLES,
  type RawMaterial2CleanMaterialArtifactRole,
  type RawMaterial2CleanMaterialInputBundle,
  type RawMaterial2CleanMaterialInputBundleObjectRef,
  type RequiredRawMaterial2CleanMaterialArtifactRole,
} from './rawMaterial2CleanMaterialInputBundle';

export const RAW_MATERIAL_2_CLEAN_MATERIAL_REQUEST_KIND = 'raw-material-2-clean-material-request' as const;
export const RAW_MATERIAL_2_CLEAN_MATERIAL_PROTOCOL_VERSION = 'v0.mock' as const;
export const RAW_MATERIAL_2_CLEAN_MATERIAL_MOCK_MODE = 'mock-dry-run' as const;
export const RAW_MATERIAL_2_CLEAN_MATERIAL_DRY_RUN_STATUS = 'MOCK_DRY_RUN_SUCCESS' as const;
export const RAW_MATERIAL_2_CLEAN_MATERIAL_OUTPUT_CATEGORY = 'raw-material-2-clean-material-draft' as const;

export type RawMaterial2CleanMaterialRunnerBlockedCode =
  | 'MISSING_INPUT_BUNDLE'
  | 'UNSUPPORTED_INPUT_KIND'
  | 'UNSUPPORTED_MODE'
  | 'CLEAN_MATERIAL_NOT_ACCEPTED'
  | 'MISSING_REQUIRED_ARTIFACT'
  | 'ARTIFACT_BODY_READ_REQUIRED'
  | 'LIVE_DEPENDENCY_NOT_ALLOWED';

export interface RawMaterial2CleanMaterialRequest {
  kind: typeof RAW_MATERIAL_2_CLEAN_MATERIAL_REQUEST_KIND;
  protocolVersion: typeof RAW_MATERIAL_2_CLEAN_MATERIAL_PROTOCOL_VERSION;
  mode: typeof RAW_MATERIAL_2_CLEAN_MATERIAL_MOCK_MODE;
  materialId: string;
  taskId: string;
  source: {
    cleanServiceName: typeof RAW_MATERIAL_2_CLEAN_MATERIAL_SERVICE_NAME;
    assetVersion: string;
    jobId: string;
    provenanceObjectName: string;
    sourceInput: RawMaterial2CleanMaterialInputBundleObjectRef;
    artifactRefs: Record<RawMaterial2CleanMaterialArtifactRole, RawMaterial2CleanMaterialInputBundleObjectRef>;
    operatorDecision: {
      state: 'accepted';
      decidedAt?: string;
      decidedBy?: string;
    };
  };
}

export interface RawMaterial2CleanMaterialMockDryRunResult {
  ok: true;
  status: typeof RAW_MATERIAL_2_CLEAN_MATERIAL_DRY_RUN_STATUS;
  classification: typeof RAW_MATERIAL_2_CLEAN_MATERIAL_DRY_RUN_STATUS;
  request: RawMaterial2CleanMaterialRequest;
  summary: {
    artifactRolesToReadLater: RawMaterial2CleanMaterialArtifactRole[];
    sourceCleanMaterial: {
      serviceName: typeof RAW_MATERIAL_2_CLEAN_MATERIAL_SERVICE_NAME;
      assetVersion: string;
      jobId: string;
      provenanceObjectName: string;
    };
    output: {
      category: typeof RAW_MATERIAL_2_CLEAN_MATERIAL_OUTPUT_CATEGORY;
      mode: typeof RAW_MATERIAL_2_CLEAN_MATERIAL_MOCK_MODE;
      writePlanned: false;
    };
    boundaries: {
      artifactBodiesRead: false;
      dbAccess: false;
      minioAccess: false;
      runtimePost: false;
      dockerOperation: false;
    };
  };
}

export type RawMaterial2CleanMaterialRunnerResult =
  | RawMaterial2CleanMaterialMockDryRunResult
  | {
      ok: false;
      code: RawMaterial2CleanMaterialRunnerBlockedCode;
      reason: string;
      details?: Record<string, unknown>;
    };

export type RawMaterial2CleanMaterialRequestBuildResult =
  | {
      ok: true;
      request: RawMaterial2CleanMaterialRequest;
    }
  | Extract<RawMaterial2CleanMaterialRunnerResult, { ok: false }>;

const LIVE_DEPENDENCY_MARKERS = new Set([
  'db',
  'dbClient',
  'database',
  'fetch',
  'httpClient',
  'minio',
  'minioClient',
  'runtimeClient',
  'transport',
  'endpoint',
  'worker',
  'docker',
  'liveDependency',
  'liveDependencies',
]);

function blocked(
  code: RawMaterial2CleanMaterialRunnerBlockedCode,
  reason: string,
  details?: Record<string, unknown>,
): Extract<RawMaterial2CleanMaterialRunnerResult, { ok: false }> {
  return details ? { ok: false, code, reason, details } : { ok: false, code, reason };
}

function asRecord(value: unknown): Record<string, unknown> | null {
  return value && typeof value === 'object' && !Array.isArray(value)
    ? value as Record<string, unknown>
    : null;
}

function hasArtifactBody(value: unknown): boolean {
  const record = asRecord(value);
  return Boolean(
    record
      && ('content' in record || 'body' in record || 'text' in record || 'json' in record || 'data' in record),
  );
}

function containsLiveDependencyMarker(value: unknown, depth = 0): boolean {
  if (depth > 4) return false;
  const record = asRecord(value);
  if (!record) return false;

  for (const [key, child] of Object.entries(record)) {
    if (LIVE_DEPENDENCY_MARKERS.has(key)) return true;
    if (containsLiveDependencyMarker(child, depth + 1)) return true;
  }

  return false;
}

function cloneObjectRef(ref: RawMaterial2CleanMaterialInputBundleObjectRef): RawMaterial2CleanMaterialInputBundleObjectRef {
  return {
    ...(ref.bucket ? { bucket: ref.bucket } : {}),
    object: ref.object,
    ...(ref.sha256 ? { sha256: ref.sha256 } : {}),
    ...(typeof ref.size_bytes === 'number' ? { size_bytes: ref.size_bytes } : {}),
    ...(ref.content_type ? { content_type: ref.content_type } : {}),
  };
}

function isRequiredArtifactRole(role: RawMaterial2CleanMaterialArtifactRole): role is RequiredRawMaterial2CleanMaterialArtifactRole {
  return REQUIRED_RAW_MATERIAL_2_CLEAN_MATERIAL_ARTIFACT_ROLES.includes(
    role as RequiredRawMaterial2CleanMaterialArtifactRole,
  );
}

function validateArtifactRefs(
  artifactRefs: Partial<Record<RawMaterial2CleanMaterialArtifactRole, RawMaterial2CleanMaterialInputBundleObjectRef>>,
): Extract<RawMaterial2CleanMaterialRunnerResult, { ok: false }> | null {
  const roles = [
    ...REQUIRED_RAW_MATERIAL_2_CLEAN_MATERIAL_ARTIFACT_ROLES,
    ...OPTIONAL_RAW_MATERIAL_2_CLEAN_MATERIAL_ARTIFACT_ROLES,
  ] as RawMaterial2CleanMaterialArtifactRole[];

  for (const role of roles) {
    const ref = artifactRefs[role];
    if (!ref) {
      if (isRequiredArtifactRole(role)) {
        return blocked('MISSING_REQUIRED_ARTIFACT', `required artifact ref is missing: ${role}`, { role });
      }
      continue;
    }

    if (!ref.object) {
      if (isRequiredArtifactRole(role)) {
        return blocked('MISSING_REQUIRED_ARTIFACT', `required artifact object is missing: ${role}`, { role });
      }
      continue;
    }

    if (hasArtifactBody(ref)) {
      return blocked('ARTIFACT_BODY_READ_REQUIRED', 'mock boundary accepts artifact object refs only', { role });
    }
  }

  return null;
}

export function buildRawMaterial2CleanMaterialRequest(
  bundle?: RawMaterial2CleanMaterialInputBundle | null,
): RawMaterial2CleanMaterialRequestBuildResult {
  if (!bundle) return blocked('MISSING_INPUT_BUNDLE', 'input bundle is required');
  if (containsLiveDependencyMarker(bundle)) {
    return blocked('LIVE_DEPENDENCY_NOT_ALLOWED', 'request construction must not receive live dependency handles');
  }
  if (bundle.kind !== RAW_MATERIAL_2_CLEAN_MATERIAL_INPUT_KIND) {
    return blocked('UNSUPPORTED_INPUT_KIND', 'input bundle kind is not supported', { kind: bundle.kind });
  }
  if (bundle.operatorDecision?.state !== 'accepted') {
    return blocked('CLEAN_MATERIAL_NOT_ACCEPTED', 'accepted operator decision is required');
  }

  const artifactBlock = validateArtifactRefs(bundle.artifactRefs);
  if (artifactBlock) return artifactBlock;

  const artifactRefs = {} as Record<RawMaterial2CleanMaterialArtifactRole, RawMaterial2CleanMaterialInputBundleObjectRef>;
  const roles = [
    ...REQUIRED_RAW_MATERIAL_2_CLEAN_MATERIAL_ARTIFACT_ROLES,
    ...OPTIONAL_RAW_MATERIAL_2_CLEAN_MATERIAL_ARTIFACT_ROLES,
  ] as RawMaterial2CleanMaterialArtifactRole[];

  for (const role of roles) {
    const ref = bundle.artifactRefs[role];
    if (ref) artifactRefs[role] = cloneObjectRef(ref);
  }

  return {
    ok: true,
    request: {
      kind: RAW_MATERIAL_2_CLEAN_MATERIAL_REQUEST_KIND,
      protocolVersion: RAW_MATERIAL_2_CLEAN_MATERIAL_PROTOCOL_VERSION,
      mode: RAW_MATERIAL_2_CLEAN_MATERIAL_MOCK_MODE,
      materialId: bundle.materialId,
      taskId: bundle.taskId,
      source: {
        cleanServiceName: RAW_MATERIAL_2_CLEAN_MATERIAL_SERVICE_NAME,
        assetVersion: bundle.assetVersion,
        jobId: bundle.jobId,
        provenanceObjectName: bundle.provenanceObjectName,
        sourceInput: cloneObjectRef(bundle.sourceInput),
        artifactRefs,
        operatorDecision: {
          state: 'accepted',
          ...(bundle.operatorDecision.decidedAt ? { decidedAt: bundle.operatorDecision.decidedAt } : {}),
          ...(bundle.operatorDecision.decidedBy ? { decidedBy: bundle.operatorDecision.decidedBy } : {}),
        },
      },
    },
  };
}

function isRequest(value: unknown): value is RawMaterial2CleanMaterialRequest {
  return asRecord(value)?.kind === RAW_MATERIAL_2_CLEAN_MATERIAL_REQUEST_KIND;
}

function isInputBundle(value: unknown): value is RawMaterial2CleanMaterialInputBundle {
  return asRecord(value)?.kind === RAW_MATERIAL_2_CLEAN_MATERIAL_INPUT_KIND;
}

export function runRawMaterial2CleanMaterialMockDryRun(
  input?: RawMaterial2CleanMaterialInputBundle | RawMaterial2CleanMaterialRequest | null,
): RawMaterial2CleanMaterialRunnerResult {
  if (!input) return blocked('MISSING_INPUT_BUNDLE', 'input bundle or request is required');
  if (containsLiveDependencyMarker(input)) {
    return blocked('LIVE_DEPENDENCY_NOT_ALLOWED', 'mock dry-run must not receive live dependency handles');
  }

  const requestResult: RawMaterial2CleanMaterialRequestBuildResult = isInputBundle(input)
    ? buildRawMaterial2CleanMaterialRequest(input)
    : isRequest(input)
      ? { ok: true as const, request: input }
      : blocked('UNSUPPORTED_INPUT_KIND', 'input kind is not supported', { kind: asRecord(input)?.kind ?? null });

  if (requestResult.ok === false) return requestResult;

  const { request } = requestResult;
  if (request.mode !== RAW_MATERIAL_2_CLEAN_MATERIAL_MOCK_MODE) {
    return blocked('UNSUPPORTED_MODE', 'only mock-dry-run mode is supported', { mode: request.mode });
  }
  if (request.source.operatorDecision?.state !== 'accepted') {
    return blocked('CLEAN_MATERIAL_NOT_ACCEPTED', 'accepted operator decision is required');
  }

  const artifactBlock = validateArtifactRefs(request.source.artifactRefs);
  if (artifactBlock) return artifactBlock;

  return {
    ok: true,
    status: RAW_MATERIAL_2_CLEAN_MATERIAL_DRY_RUN_STATUS,
    classification: RAW_MATERIAL_2_CLEAN_MATERIAL_DRY_RUN_STATUS,
    request,
    summary: {
      artifactRolesToReadLater: Object.keys(request.source.artifactRefs) as RawMaterial2CleanMaterialArtifactRole[],
      sourceCleanMaterial: {
        serviceName: request.source.cleanServiceName,
        assetVersion: request.source.assetVersion,
        jobId: request.source.jobId,
        provenanceObjectName: request.source.provenanceObjectName,
      },
      output: {
        category: RAW_MATERIAL_2_CLEAN_MATERIAL_OUTPUT_CATEGORY,
        mode: RAW_MATERIAL_2_CLEAN_MATERIAL_MOCK_MODE,
        writePlanned: false,
      },
      boundaries: {
        artifactBodiesRead: false,
        dbAccess: false,
        minioAccess: false,
        runtimePost: false,
        dockerOperation: false,
      },
    },
  };
}
