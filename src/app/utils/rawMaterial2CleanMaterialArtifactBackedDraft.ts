import {
  buildRawMaterial2CleanMaterialDraftSkeleton,
  type RawMaterial2CleanMaterialAlgorithmOptions,
  type RawMaterial2CleanMaterialAlgorithmResult,
  type RawMaterial2CleanMaterialArtifactBodyMap,
  type RawMaterial2CleanMaterialDraftOutput,
} from './rawMaterial2CleanMaterialAlgorithm';
import {
  buildRawMaterial2CleanMaterialInputBundle,
  REQUIRED_RAW_MATERIAL_2_CLEAN_MATERIAL_ARTIFACT_ROLES,
  type BuildRawMaterial2CleanMaterialInputBundleInput,
  type RawMaterial2CleanMaterialInputBundle,
  type RawMaterial2CleanMaterialInputBundleObjectRef,
  type RequiredRawMaterial2CleanMaterialArtifactRole,
} from './rawMaterial2CleanMaterialInputBundle';
import {
  RAW_MATERIAL_2_CLEAN_MATERIAL_REQUEST_KIND,
  buildRawMaterial2CleanMaterialRequest,
  type RawMaterial2CleanMaterialRequest,
} from './rawMaterial2CleanMaterialRunner';

export type RawMaterial2CleanMaterialArtifactBackedDraftBlockedCode =
  | 'MISSING_INPUT'
  | 'MISSING_ARTIFACT_READER'
  | 'UNSUPPORTED_INPUT_KIND'
  | 'INPUT_BUNDLE_BLOCKED'
  | 'REQUEST_BUILD_BLOCKED'
  | 'ARTIFACT_READ_FAILED'
  | 'DRAFT_BUILD_BLOCKED'
  | 'LIVE_DEPENDENCY_NOT_ALLOWED';

export type RawMaterial2CleanMaterialArtifactBodyReader = (
  ref: RawMaterial2CleanMaterialInputBundleObjectRef,
  role: RequiredRawMaterial2CleanMaterialArtifactRole,
) => unknown | Promise<unknown>;

export interface RawMaterial2CleanMaterialArtifactBackedDraftInput {
  material?: BuildRawMaterial2CleanMaterialInputBundleInput['material'];
  task?: BuildRawMaterial2CleanMaterialInputBundleInput['task'];
  bundle?: RawMaterial2CleanMaterialInputBundle | null;
  request?: RawMaterial2CleanMaterialRequest | null;
  currentAssetVersion?: string | null;
  artifactBodyReader?: RawMaterial2CleanMaterialArtifactBodyReader | null;
  options?: RawMaterial2CleanMaterialAlgorithmOptions;
}

export interface RawMaterial2CleanMaterialArtifactBackedDraftEvidence {
  rolesRead: RequiredRawMaterial2CleanMaterialArtifactRole[];
  artifactRefsRead: Record<RequiredRawMaterial2CleanMaterialArtifactRole, RawMaterial2CleanMaterialInputBundleObjectRef>;
  draftStatus: RawMaterial2CleanMaterialDraftOutput['status'];
  sectionCount: number;
  blockCount: number;
  sampleSourceRefs: string[];
  sourceInput: RawMaterial2CleanMaterialInputBundleObjectRef;
  sourceCleanMaterial: {
    serviceName: RawMaterial2CleanMaterialRequest['source']['cleanServiceName'];
    assetVersion: string;
    jobId: string;
    provenanceObjectName: string;
  };
  boundaries: {
    dbWrites: false;
    minioWrites: false;
    runtimePost: false;
    optionalArtifactsRead: false;
  };
}

export type RawMaterial2CleanMaterialArtifactBackedDraftResult =
  | {
      ok: true;
      request: RawMaterial2CleanMaterialRequest;
      draft: RawMaterial2CleanMaterialDraftOutput;
      evidence: RawMaterial2CleanMaterialArtifactBackedDraftEvidence;
    }
  | {
      ok: false;
      code: RawMaterial2CleanMaterialArtifactBackedDraftBlockedCode;
      reason: string;
      details?: Record<string, unknown>;
    };

const LIVE_DEPENDENCY_MARKERS = new Set([
  'db',
  'dbClient',
  'database',
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
  code: RawMaterial2CleanMaterialArtifactBackedDraftBlockedCode,
  reason: string,
  details?: Record<string, unknown>,
): RawMaterial2CleanMaterialArtifactBackedDraftResult {
  return details ? { ok: false, code, reason, details } : { ok: false, code, reason };
}

function asRecord(value: unknown): Record<string, unknown> | null {
  return value && typeof value === 'object' && !Array.isArray(value)
    ? value as Record<string, unknown>
    : null;
}

function containsLiveDependencyMarker(value: unknown, depth = 0): boolean {
  if (depth > 5) return false;
  const record = asRecord(value);
  if (!record) return false;

  for (const [key, child] of Object.entries(record)) {
    if (LIVE_DEPENDENCY_MARKERS.has(key)) return true;
    if (containsLiveDependencyMarker(child, depth + 1)) return true;
  }

  return false;
}

function isRequest(value: unknown): value is RawMaterial2CleanMaterialRequest {
  return asRecord(value)?.kind === RAW_MATERIAL_2_CLEAN_MATERIAL_REQUEST_KIND;
}

function resolveRequest(
  input: RawMaterial2CleanMaterialArtifactBackedDraftInput,
): RawMaterial2CleanMaterialArtifactBackedDraftResult | { ok: true; request: RawMaterial2CleanMaterialRequest } {
  if (input.request) {
    if (!isRequest(input.request)) {
      return blocked('UNSUPPORTED_INPUT_KIND', 'request kind is not supported', { kind: asRecord(input.request)?.kind ?? null });
    }
    return { ok: true, request: input.request };
  }

  const bundle = input.bundle ?? null;
  if (bundle) {
    const requestResult = buildRawMaterial2CleanMaterialRequest(bundle);
    if (!requestResult.ok) {
      return blocked('REQUEST_BUILD_BLOCKED', 'request builder blocked the input bundle', { result: requestResult });
    }
    return { ok: true, request: requestResult.request };
  }

  if (!input.material || !input.task) {
    return blocked('MISSING_INPUT', 'material/task, bundle, or request is required');
  }

  const bundleResult = buildRawMaterial2CleanMaterialInputBundle({
    material: input.material,
    task: input.task,
    currentAssetVersion: input.currentAssetVersion,
  });
  if (!bundleResult.ok) {
    return blocked('INPUT_BUNDLE_BLOCKED', 'input bundle builder blocked material/task metadata', { result: bundleResult });
  }

  const requestResult = buildRawMaterial2CleanMaterialRequest(bundleResult.bundle);
  if (!requestResult.ok) {
    return blocked('REQUEST_BUILD_BLOCKED', 'request builder blocked the built input bundle', { result: requestResult });
  }

  return { ok: true, request: requestResult.request };
}

function sampleSourceRefs(draft: RawMaterial2CleanMaterialDraftOutput): string[] {
  return [
    ...draft.extracted.sections.map((item) => item.sourceRef),
    ...draft.extracted.blocks.map((item) => item.sourceRef),
  ].slice(0, 8);
}

export async function buildRawMaterial2CleanMaterialArtifactBackedDraftDryRun(
  input: RawMaterial2CleanMaterialArtifactBackedDraftInput,
): Promise<RawMaterial2CleanMaterialArtifactBackedDraftResult> {
  if (containsLiveDependencyMarker({
    material: input.material,
    task: input.task,
    bundle: input.bundle,
    request: input.request,
    options: input.options,
  })) {
    return blocked('LIVE_DEPENDENCY_NOT_ALLOWED', 'artifact-backed dry-run accepts data and injected readers only');
  }
  if (!input.artifactBodyReader) {
    return blocked('MISSING_ARTIFACT_READER', 'injected read-only artifact body reader is required');
  }

  const requestResult = resolveRequest(input);
  if (requestResult.ok === false) return requestResult;

  const { request } = requestResult;
  const artifactBodies: RawMaterial2CleanMaterialArtifactBodyMap = {};
  const artifactRefsRead = {} as Record<RequiredRawMaterial2CleanMaterialArtifactRole, RawMaterial2CleanMaterialInputBundleObjectRef>;
  const rolesRead: RequiredRawMaterial2CleanMaterialArtifactRole[] = [];

  for (const role of REQUIRED_RAW_MATERIAL_2_CLEAN_MATERIAL_ARTIFACT_ROLES) {
    const ref = request.source.artifactRefs[role];
    if (!ref?.object) {
      return blocked('REQUEST_BUILD_BLOCKED', `required artifact ref is missing from request: ${role}`, { role });
    }

    try {
      artifactBodies[role] = await input.artifactBodyReader(ref, role);
      artifactRefsRead[role] = ref;
      rolesRead.push(role);
    } catch (error) {
      return blocked('ARTIFACT_READ_FAILED', `read-only artifact body reader failed for ${role}`, {
        role,
        object: ref.object,
        error: error instanceof Error ? error.message : String(error),
      });
    }
  }

  const draftResult: RawMaterial2CleanMaterialAlgorithmResult = buildRawMaterial2CleanMaterialDraftSkeleton({
    request,
    artifactBodies,
    options: input.options,
  });
  if (!draftResult.ok) {
    return blocked('DRAFT_BUILD_BLOCKED', 'artifact-backed draft skeleton blocked the injected bodies', { result: draftResult });
  }

  const { draft } = draftResult;
  return {
    ok: true,
    request,
    draft,
    evidence: {
      rolesRead,
      artifactRefsRead,
      draftStatus: draft.status,
      sectionCount: draft.extracted.sections.length,
      blockCount: draft.extracted.blocks.length,
      sampleSourceRefs: sampleSourceRefs(draft),
      sourceInput: draft.source.sourceInput,
      sourceCleanMaterial: {
        serviceName: request.source.cleanServiceName,
        assetVersion: request.source.assetVersion,
        jobId: request.source.jobId,
        provenanceObjectName: request.source.provenanceObjectName,
      },
      boundaries: {
        dbWrites: false,
        minioWrites: false,
        runtimePost: false,
        optionalArtifactsRead: false,
      },
    },
  };
}
