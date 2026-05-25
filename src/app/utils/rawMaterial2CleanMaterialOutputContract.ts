import {
  RAW_MATERIAL_2_CLEAN_MATERIAL_ALGORITHM_STATUS,
  RAW_MATERIAL_2_CLEAN_MATERIAL_DRAFT_KIND,
  type RawMaterial2CleanMaterialDraftItem,
  type RawMaterial2CleanMaterialDraftOutput,
} from './rawMaterial2CleanMaterialAlgorithm';
import type {
  RawMaterial2CleanMaterialArtifactRole,
  RawMaterial2CleanMaterialInputBundleObjectRef,
} from './rawMaterial2CleanMaterialInputBundle';

export const RAW_MATERIAL_2_CLEAN_MATERIAL_OUTPUT_KIND = 'raw-material-2-clean-material-output-candidate' as const;
export const RAW_MATERIAL_2_CLEAN_MATERIAL_OUTPUT_CONTRACT_VERSION = 'v0.dry-run' as const;

export type RawMaterial2CleanMaterialOutputContractBlockedCode =
  | 'MISSING_DRAFT'
  | 'UNSUPPORTED_DRAFT_KIND'
  | 'DRAFT_NOT_READY'
  | 'MISSING_SOURCE_REFERENCE'
  | 'LIVE_DEPENDENCY_NOT_ALLOWED';

export interface RawMaterial2CleanMaterialOutputContractOptions {
  now?: string | (() => string);
}

export interface RawMaterial2CleanMaterialOutputContractItem {
  sourceRef: string;
  sourceRole: RawMaterial2CleanMaterialArtifactRole;
  title?: string;
  text?: string;
}

export interface RawMaterial2CleanMaterialOutputContractPreview {
  contentType: 'application/json';
  size_bytes: number;
  sha256: string;
}

export interface RawMaterial2CleanMaterialOutputContract {
  kind: typeof RAW_MATERIAL_2_CLEAN_MATERIAL_OUTPUT_KIND;
  contractVersion: typeof RAW_MATERIAL_2_CLEAN_MATERIAL_OUTPUT_CONTRACT_VERSION;
  createdAt: string;
  materialId: string;
  taskId: string;
  sourceCleanMaterial: {
    serviceName: RawMaterial2CleanMaterialDraftOutput['source']['cleanServiceName'];
    assetVersion: string;
    jobId: string;
    provenanceObjectName: string;
  };
  sourceInput: RawMaterial2CleanMaterialInputBundleObjectRef;
  sourceArtifacts: Record<RawMaterial2CleanMaterialArtifactRole, RawMaterial2CleanMaterialInputBundleObjectRef>;
  sections: RawMaterial2CleanMaterialOutputContractItem[];
  blocks: RawMaterial2CleanMaterialOutputContractItem[];
  provenance: {
    draftKind: typeof RAW_MATERIAL_2_CLEAN_MATERIAL_DRAFT_KIND;
    draftStatus: typeof RAW_MATERIAL_2_CLEAN_MATERIAL_ALGORITHM_STATUS;
    draftCreatedAt: string;
    sourceRefCount: number;
    readableTree: RawMaterial2CleanMaterialDraftOutput['extracted']['readableTree'];
  };
  warnings: string[];
  preview: RawMaterial2CleanMaterialOutputContractPreview;
  persistencePlan: {
    mode: 'none';
    writesPlanned: false;
  };
  boundaries: {
    dbAccess: false;
    dbWrites: false;
    minioAccess: false;
    minioWrites: false;
    runtimePost: false;
    dockerOperation: false;
    durableArtifactCreated: false;
  };
}

export type RawMaterial2CleanMaterialOutputContractResult =
  | {
      ok: true;
      output: RawMaterial2CleanMaterialOutputContract;
      canonicalJson: string;
    }
  | {
      ok: false;
      code: RawMaterial2CleanMaterialOutputContractBlockedCode;
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
  code: RawMaterial2CleanMaterialOutputContractBlockedCode,
  reason: string,
  details?: Record<string, unknown>,
): RawMaterial2CleanMaterialOutputContractResult {
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

function nowValue(options?: RawMaterial2CleanMaterialOutputContractOptions): string {
  if (typeof options?.now === 'function') return options.now();
  if (typeof options?.now === 'string') return options.now;
  return new Date().toISOString();
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

function normalizeItem(item: RawMaterial2CleanMaterialDraftItem): RawMaterial2CleanMaterialOutputContractItem | null {
  if (!item.sourceRef) return null;
  return {
    sourceRef: item.sourceRef,
    sourceRole: item.role,
    ...(item.title ? { title: item.title } : {}),
    ...(item.text ? { text: item.text } : {}),
  };
}

function stableJson(value: unknown): string {
  return JSON.stringify(sortStable(value));
}

function sortStable(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(sortStable);
  const record = asRecord(value);
  if (!record) return value;

  return Object.keys(record)
    .sort()
    .reduce<Record<string, unknown>>((sorted, key) => {
      sorted[key] = sortStable(record[key]);
      return sorted;
    }, {});
}

const SHA256_K = [
  0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5,
  0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
  0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
  0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
  0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc,
  0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
  0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
  0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
  0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
  0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
  0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3,
  0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
  0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5,
  0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
  0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
  0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
];

function rightRotate(value: number, amount: number): number {
  return (value >>> amount) | (value << (32 - amount));
}

function utf8Bytes(value: string): Uint8Array {
  return new TextEncoder().encode(value);
}

function sha256Hex(value: string): string {
  const bytes = utf8Bytes(value);
  const bitLength = bytes.length * 8;
  const paddedLength = Math.ceil((bytes.length + 9) / 64) * 64;
  const padded = new Uint8Array(paddedLength);
  padded.set(bytes);
  padded[bytes.length] = 0x80;

  const view = new DataView(padded.buffer);
  view.setUint32(paddedLength - 8, Math.floor(bitLength / 0x100000000));
  view.setUint32(paddedLength - 4, bitLength >>> 0);

  const hash = [
    0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
    0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19,
  ];
  const words = new Array<number>(64);

  for (let offset = 0; offset < paddedLength; offset += 64) {
    for (let index = 0; index < 16; index += 1) {
      words[index] = view.getUint32(offset + index * 4);
    }
    for (let index = 16; index < 64; index += 1) {
      const s0 = rightRotate(words[index - 15], 7) ^ rightRotate(words[index - 15], 18) ^ (words[index - 15] >>> 3);
      const s1 = rightRotate(words[index - 2], 17) ^ rightRotate(words[index - 2], 19) ^ (words[index - 2] >>> 10);
      words[index] = (words[index - 16] + s0 + words[index - 7] + s1) >>> 0;
    }

    let [a, b, c, d, e, f, g, h] = hash;
    for (let index = 0; index < 64; index += 1) {
      const s1 = rightRotate(e, 6) ^ rightRotate(e, 11) ^ rightRotate(e, 25);
      const ch = (e & f) ^ (~e & g);
      const temp1 = (h + s1 + ch + SHA256_K[index] + words[index]) >>> 0;
      const s0 = rightRotate(a, 2) ^ rightRotate(a, 13) ^ rightRotate(a, 22);
      const maj = (a & b) ^ (a & c) ^ (b & c);
      const temp2 = (s0 + maj) >>> 0;
      h = g;
      g = f;
      f = e;
      e = (d + temp1) >>> 0;
      d = c;
      c = b;
      b = a;
      a = (temp1 + temp2) >>> 0;
    }

    hash[0] = (hash[0] + a) >>> 0;
    hash[1] = (hash[1] + b) >>> 0;
    hash[2] = (hash[2] + c) >>> 0;
    hash[3] = (hash[3] + d) >>> 0;
    hash[4] = (hash[4] + e) >>> 0;
    hash[5] = (hash[5] + f) >>> 0;
    hash[6] = (hash[6] + g) >>> 0;
    hash[7] = (hash[7] + h) >>> 0;
  }

  return hash.map((part) => part.toString(16).padStart(8, '0')).join('');
}

function withPreview(
  outputWithoutPreview: Omit<RawMaterial2CleanMaterialOutputContract, 'preview'>,
): { output: RawMaterial2CleanMaterialOutputContract; canonicalJson: string } {
  const previewPlaceholder: RawMaterial2CleanMaterialOutputContractPreview = {
    contentType: 'application/json',
    size_bytes: 0,
    sha256: 'pending',
  };
  const outputWithPlaceholder: RawMaterial2CleanMaterialOutputContract = {
    ...outputWithoutPreview,
    preview: previewPlaceholder,
  };
  const canonicalJsonWithoutPreview = stableJson({
    ...outputWithPlaceholder,
    preview: previewPlaceholder,
  });
  const preview: RawMaterial2CleanMaterialOutputContractPreview = {
    contentType: 'application/json',
    size_bytes: utf8Bytes(canonicalJsonWithoutPreview).length,
    sha256: sha256Hex(canonicalJsonWithoutPreview),
  };
  const output = {
    ...outputWithoutPreview,
    preview,
  };
  return {
    output,
    canonicalJson: stableJson(output),
  };
}

export function buildRawMaterial2CleanMaterialOutputContract({
  draft,
  options,
}: {
  draft?: RawMaterial2CleanMaterialDraftOutput | null;
  options?: RawMaterial2CleanMaterialOutputContractOptions;
}): RawMaterial2CleanMaterialOutputContractResult {
  if (!draft) return blocked('MISSING_DRAFT', 'draft is required');
  if (containsLiveDependencyMarker({ draft, options })) {
    return blocked('LIVE_DEPENDENCY_NOT_ALLOWED', 'output contract accepts injected draft data only');
  }
  if (draft.kind !== RAW_MATERIAL_2_CLEAN_MATERIAL_DRAFT_KIND) {
    return blocked('UNSUPPORTED_DRAFT_KIND', 'draft kind is not supported', { kind: draft.kind });
  }
  if (draft.status !== RAW_MATERIAL_2_CLEAN_MATERIAL_ALGORITHM_STATUS) {
    return blocked('DRAFT_NOT_READY', 'draft status must be ready', { status: draft.status });
  }

  const sections = draft.extracted.sections.map(normalizeItem).filter((item): item is RawMaterial2CleanMaterialOutputContractItem => Boolean(item));
  const blocks = draft.extracted.blocks.map(normalizeItem).filter((item): item is RawMaterial2CleanMaterialOutputContractItem => Boolean(item));
  if (sections.length !== draft.extracted.sections.length || blocks.length !== draft.extracted.blocks.length) {
    return blocked('MISSING_SOURCE_REFERENCE', 'all draft sections and blocks must keep source refs');
  }

  const sourceArtifacts = {} as Record<RawMaterial2CleanMaterialArtifactRole, RawMaterial2CleanMaterialInputBundleObjectRef>;
  for (const [role, ref] of Object.entries(draft.source.artifactRefs)) {
    sourceArtifacts[role as RawMaterial2CleanMaterialArtifactRole] = cloneObjectRef(ref);
  }

  const sourceRefs = new Set([
    ...sections.map((item) => item.sourceRef),
    ...blocks.map((item) => item.sourceRef),
  ]);

  const outputWithoutPreview: Omit<RawMaterial2CleanMaterialOutputContract, 'preview'> = {
    kind: RAW_MATERIAL_2_CLEAN_MATERIAL_OUTPUT_KIND,
    contractVersion: RAW_MATERIAL_2_CLEAN_MATERIAL_OUTPUT_CONTRACT_VERSION,
    createdAt: nowValue(options),
    materialId: draft.materialId,
    taskId: draft.taskId,
    sourceCleanMaterial: {
      serviceName: draft.source.cleanServiceName,
      assetVersion: draft.source.assetVersion,
      jobId: draft.source.jobId,
      provenanceObjectName: draft.source.provenanceObjectName,
    },
    sourceInput: cloneObjectRef(draft.source.sourceInput),
    sourceArtifacts,
    sections,
    blocks,
    provenance: {
      draftKind: draft.kind,
      draftStatus: draft.status,
      draftCreatedAt: draft.createdAt,
      sourceRefCount: sourceRefs.size,
      readableTree: draft.extracted.readableTree,
    },
    warnings: [...draft.quality.warnings],
    persistencePlan: {
      mode: 'none',
      writesPlanned: false,
    },
    boundaries: {
      dbAccess: false,
      dbWrites: false,
      minioAccess: false,
      minioWrites: false,
      runtimePost: false,
      dockerOperation: false,
      durableArtifactCreated: false,
    },
  };

  const { output, canonicalJson } = withPreview(outputWithoutPreview);
  return { ok: true, output, canonicalJson };
}
