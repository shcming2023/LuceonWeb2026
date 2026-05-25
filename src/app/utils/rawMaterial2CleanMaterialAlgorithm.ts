import {
  RAW_MATERIAL_2_CLEAN_MATERIAL_MOCK_MODE,
  RAW_MATERIAL_2_CLEAN_MATERIAL_OUTPUT_CATEGORY,
  RAW_MATERIAL_2_CLEAN_MATERIAL_PROTOCOL_VERSION,
  RAW_MATERIAL_2_CLEAN_MATERIAL_REQUEST_KIND,
  type RawMaterial2CleanMaterialRequest,
} from './rawMaterial2CleanMaterialRunner';
import {
  REQUIRED_RAW_MATERIAL_2_CLEAN_MATERIAL_ARTIFACT_ROLES,
  type RawMaterial2CleanMaterialArtifactRole,
  type RawMaterial2CleanMaterialInputBundleObjectRef,
  type RequiredRawMaterial2CleanMaterialArtifactRole,
} from './rawMaterial2CleanMaterialInputBundle';

export const RAW_MATERIAL_2_CLEAN_MATERIAL_DRAFT_KIND = 'raw-material-2-clean-material-draft' as const;
export const RAW_MATERIAL_2_CLEAN_MATERIAL_ALGORITHM_STATUS = 'MOCK_ALGORITHM_DRAFT_READY' as const;

export type RawMaterial2CleanMaterialAlgorithmBlockedCode =
  | 'MISSING_REQUEST'
  | 'UNSUPPORTED_REQUEST_KIND'
  | 'UNSUPPORTED_MODE'
  | 'MISSING_ARTIFACT_BODY'
  | 'INVALID_ARTIFACT_BODY'
  | 'MISSING_SOURCE_REFERENCE'
  | 'LIVE_DEPENDENCY_NOT_ALLOWED';

export type RawMaterial2CleanMaterialArtifactBodyMap = Partial<Record<RawMaterial2CleanMaterialArtifactRole, unknown>>;

export interface RawMaterial2CleanMaterialAlgorithmOptions {
  now?: string | (() => string);
}

export interface RawMaterial2CleanMaterialDraftItem {
  role: RawMaterial2CleanMaterialArtifactRole;
  sourceRef: string;
  title?: string;
  text?: string;
}

export interface RawMaterial2CleanMaterialDraftOutput {
  kind: typeof RAW_MATERIAL_2_CLEAN_MATERIAL_DRAFT_KIND;
  protocolVersion: typeof RAW_MATERIAL_2_CLEAN_MATERIAL_PROTOCOL_VERSION;
  status: typeof RAW_MATERIAL_2_CLEAN_MATERIAL_ALGORITHM_STATUS;
  createdAt: string;
  materialId: string;
  taskId: string;
  source: {
    cleanServiceName: RawMaterial2CleanMaterialRequest['source']['cleanServiceName'];
    assetVersion: string;
    jobId: string;
    provenanceObjectName: string;
    sourceInput: RawMaterial2CleanMaterialInputBundleObjectRef;
    artifactRefs: Record<RawMaterial2CleanMaterialArtifactRole, RawMaterial2CleanMaterialInputBundleObjectRef>;
  };
  extracted: {
    readableTree: {
      sourceRef: string;
      headingCount: number;
      firstHeading?: string;
      textLength: number;
    };
    sections: RawMaterial2CleanMaterialDraftItem[];
    blocks: RawMaterial2CleanMaterialDraftItem[];
  };
  quality: {
    warnings: string[];
  };
  persistencePlan: {
    mode: 'none';
    writesPlanned: false;
  };
  boundaries: {
    artifactBodiesInjected: true;
    dbAccess: false;
    minioAccess: false;
    runtimePost: false;
    dockerOperation: false;
    generatedFinalArtifact: false;
  };
}

export type RawMaterial2CleanMaterialAlgorithmResult =
  | {
      ok: true;
      draft: RawMaterial2CleanMaterialDraftOutput;
    }
  | {
      ok: false;
      code: RawMaterial2CleanMaterialAlgorithmBlockedCode;
      reason: string;
      details?: Record<string, unknown>;
    };

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
  code: RawMaterial2CleanMaterialAlgorithmBlockedCode,
  reason: string,
  details?: Record<string, unknown>,
): RawMaterial2CleanMaterialAlgorithmResult {
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

function compactString(value: unknown): string | null {
  return typeof value === 'string' && value.trim() ? value.trim() : null;
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

function nowValue(options?: RawMaterial2CleanMaterialAlgorithmOptions): string {
  if (typeof options?.now === 'function') return options.now();
  if (typeof options?.now === 'string') return options.now;
  return new Date().toISOString();
}

function bodyToJson(value: unknown, role: RawMaterial2CleanMaterialArtifactRole): unknown {
  if (typeof value !== 'string') return value;
  try {
    return JSON.parse(value);
  } catch {
    return { __invalidJsonRole: role };
  }
}

function invalidJson(value: unknown): boolean {
  return Boolean(asRecord(value)?.__invalidJsonRole);
}

function arrayFromStructuredBody(value: unknown, keys: string[]): unknown[] | null {
  if (Array.isArray(value)) return value;
  const record = asRecord(value);
  if (!record) return null;

  for (const key of keys) {
    const child = record[key];
    if (Array.isArray(child)) return child;
  }

  return null;
}

function sourceRefFromRecord(record: Record<string, unknown>): string | null {
  return compactString(record.sourceRef)
    || compactString(record.source_ref)
    || compactString(record.blockId)
    || compactString(record.block_id)
    || compactString(record.nodeId)
    || compactString(record.node_id)
    || compactString(record.id);
}

function textFromRecord(record: Record<string, unknown>): string | undefined {
  return compactString(record.text)
    || compactString(record.content)
    || compactString(record.markdown)
    || undefined;
}

function titleFromRecord(record: Record<string, unknown>): string | undefined {
  return compactString(record.title)
    || compactString(record.heading)
    || compactString(record.label)
    || undefined;
}

function extractItemsFromBody(
  role: RawMaterial2CleanMaterialArtifactRole,
  body: unknown,
  keys: string[],
): RawMaterial2CleanMaterialDraftItem[] | RawMaterial2CleanMaterialAlgorithmResult {
  const parsed = bodyToJson(body, role);
  if (invalidJson(parsed)) {
    return blocked('INVALID_ARTIFACT_BODY', `artifact body is not valid JSON: ${role}`, { role });
  }

  const items = arrayFromStructuredBody(parsed, keys);
  if (!items) {
    return blocked('INVALID_ARTIFACT_BODY', `artifact body has no supported item array: ${role}`, { role });
  }

  const extracted: RawMaterial2CleanMaterialDraftItem[] = [];
  for (const item of items) {
    const record = asRecord(item);
    if (!record) continue;

    const sourceRef = sourceRefFromRecord(record);
    const text = textFromRecord(record);
    const title = titleFromRecord(record);
    if (!sourceRef && (text || title)) {
      return blocked('MISSING_SOURCE_REFERENCE', `source-derived item is missing a source reference: ${role}`, {
        role,
        item,
      });
    }

    if (sourceRef) {
      extracted.push({
        role,
        sourceRef,
        ...(title ? { title } : {}),
        ...(text ? { text } : {}),
      });
    }
  }

  return extracted;
}

function summarizeReadableTree(body: unknown): RawMaterial2CleanMaterialDraftOutput['extracted']['readableTree'] | RawMaterial2CleanMaterialAlgorithmResult {
  if (typeof body !== 'string') {
    return blocked('INVALID_ARTIFACT_BODY', 'readable_tree body must be an injected string');
  }

  const headings = body
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => /^#{1,6}\s+\S/.test(line));

  return {
    sourceRef: 'artifact:readable_tree',
    headingCount: headings.length,
    ...(headings[0] ? { firstHeading: headings[0].replace(/^#{1,6}\s+/, '') } : {}),
    textLength: body.length,
  };
}

function missingRequiredBodies(
  artifactBodies: RawMaterial2CleanMaterialArtifactBodyMap,
): RequiredRawMaterial2CleanMaterialArtifactRole | null {
  for (const role of REQUIRED_RAW_MATERIAL_2_CLEAN_MATERIAL_ARTIFACT_ROLES) {
    if (artifactBodies[role] == null) return role;
  }
  return null;
}

export function buildRawMaterial2CleanMaterialDraftSkeleton({
  request,
  artifactBodies,
  options,
}: {
  request?: RawMaterial2CleanMaterialRequest | null;
  artifactBodies?: RawMaterial2CleanMaterialArtifactBodyMap | null;
  options?: RawMaterial2CleanMaterialAlgorithmOptions;
}): RawMaterial2CleanMaterialAlgorithmResult {
  if (!request) return blocked('MISSING_REQUEST', 'request is required');
  if (containsLiveDependencyMarker({ request, artifactBodies })) {
    return blocked('LIVE_DEPENDENCY_NOT_ALLOWED', 'algorithm skeleton accepts injected data only, not live dependencies');
  }
  if (request.kind !== RAW_MATERIAL_2_CLEAN_MATERIAL_REQUEST_KIND) {
    return blocked('UNSUPPORTED_REQUEST_KIND', 'request kind is not supported', { kind: request.kind });
  }
  if (request.mode !== RAW_MATERIAL_2_CLEAN_MATERIAL_MOCK_MODE) {
    return blocked('UNSUPPORTED_MODE', 'only mock-dry-run requests are supported', { mode: request.mode });
  }
  if (!artifactBodies) {
    return blocked('MISSING_ARTIFACT_BODY', 'injected artifact body map is required');
  }

  const missingRole = missingRequiredBodies(artifactBodies);
  if (missingRole) {
    return blocked('MISSING_ARTIFACT_BODY', `required injected artifact body is missing: ${missingRole}`, { role: missingRole });
  }

  const readableTree = summarizeReadableTree(artifactBodies.readable_tree);
  if ('ok' in readableTree) return readableTree;

  const logicItems = extractItemsFromBody('logic_tree', artifactBodies.logic_tree, ['sections', 'nodes', 'items']);
  if (!Array.isArray(logicItems)) return logicItems;

  const skeletonItems = extractItemsFromBody('skeleton', artifactBodies.skeleton, ['nodes', 'sections', 'items']);
  if (!Array.isArray(skeletonItems)) return skeletonItems;

  const floodedItems = extractItemsFromBody('flooded_content', artifactBodies.flooded_content, ['blocks', 'items', 'content']);
  if (!Array.isArray(floodedItems)) return floodedItems;

  const artifactRefs = {} as Record<RawMaterial2CleanMaterialArtifactRole, RawMaterial2CleanMaterialInputBundleObjectRef>;
  for (const [role, ref] of Object.entries(request.source.artifactRefs)) {
    artifactRefs[role as RawMaterial2CleanMaterialArtifactRole] = cloneObjectRef(ref);
  }

  return {
    ok: true,
    draft: {
      kind: RAW_MATERIAL_2_CLEAN_MATERIAL_DRAFT_KIND,
      protocolVersion: RAW_MATERIAL_2_CLEAN_MATERIAL_PROTOCOL_VERSION,
      status: RAW_MATERIAL_2_CLEAN_MATERIAL_ALGORITHM_STATUS,
      createdAt: nowValue(options),
      materialId: request.materialId,
      taskId: request.taskId,
      source: {
        cleanServiceName: request.source.cleanServiceName,
        assetVersion: request.source.assetVersion,
        jobId: request.source.jobId,
        provenanceObjectName: request.source.provenanceObjectName,
        sourceInput: cloneObjectRef(request.source.sourceInput),
        artifactRefs,
      },
      extracted: {
        readableTree,
        sections: [...logicItems, ...skeletonItems],
        blocks: floodedItems,
      },
      quality: {
        warnings: [
          'mock-algorithm-skeleton-only',
          ...(floodedItems.length === 0 ? ['no-flooded-content-blocks'] : []),
        ],
      },
      persistencePlan: {
        mode: 'none',
        writesPlanned: false,
      },
      boundaries: {
        artifactBodiesInjected: true,
        dbAccess: false,
        minioAccess: false,
        runtimePost: false,
        dockerOperation: false,
        generatedFinalArtifact: false,
      },
    },
  };
}
