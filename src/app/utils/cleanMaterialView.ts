import type { CleanMaterialSummary, CleanObjectRef, CleanServiceTaskSummary, Material } from '../../store/types';

export interface CleanMaterialView {
  serviceName: string;
  present: boolean;
  status: string | null;
  latestVersion: string | null;
  jobId: string | null;
  provenanceObjectName: string | null;
  prefix: string | null;
  sourceInput: CleanObjectRef | null;
  tokensTotal: number | null;
  unresolvedAnchorCount: number | null;
  artifacts: Array<{ role: string; object: string; bucket: string | null; sha256: string | null; sizeBytes: number | null }>;
  artifactCount: number;
  warnings: string[];
  operatorDecision: Record<string, any> | null;
  operatorDecisionState: string | null;
  operatorDecisionReadOnly: boolean;
  updatedAt: string | null;
  hasPrefixGap: boolean;
}

function asRecord(value: unknown): Record<string, any> {
  return value && typeof value === 'object' ? value as Record<string, any> : {};
}

function cleanString(value: unknown): string | null {
  return typeof value === 'string' && value.trim() ? value.trim() : null;
}

function numberOrNull(value: unknown): number | null {
  if (typeof value === 'number' && Number.isFinite(value)) return value;
  if (typeof value === 'string' && value.trim() !== '') {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

function normalizeSourceInput(...candidates: unknown[]): CleanObjectRef | null {
  for (const candidate of candidates) {
    const ref = asRecord(candidate);
    const object = cleanString(ref.object);
    if (!object) continue;
    return {
      bucket: cleanString(ref.bucket) || undefined,
      object,
      sha256: cleanString(ref.sha256) || cleanString(ref.sha256_hex) || undefined,
      size_bytes: numberOrNull(ref.size_bytes ?? ref.sizeBytes) ?? undefined,
      content_type: cleanString(ref.content_type) || cleanString(ref.contentType) || undefined,
    };
  }
  return null;
}

function normalizeArtifacts(artifacts: unknown): CleanMaterialView['artifacts'] {
  return Object.entries(asRecord(artifacts))
    .map(([role, rawRef]) => {
      const ref = asRecord(rawRef);
      const object = cleanString(ref.object);
      if (!object) return null;
      return {
        role,
        object,
        bucket: cleanString(ref.bucket),
        sha256: cleanString(ref.sha256) || cleanString(ref.sha256_hex),
        sizeBytes: numberOrNull(ref.size_bytes ?? ref.sizeBytes),
      };
    })
    .filter((item): item is CleanMaterialView['artifacts'][number] => Boolean(item));
}

function getServiceSummary<T>(container: unknown, serviceName: string): T | null {
  const services = asRecord(container);
  const summary = services[serviceName];
  return summary && typeof summary === 'object' ? summary as T : null;
}

export function buildCleanMaterialView({
  material,
  task,
  serviceName = 'toc-rebuild',
}: {
  material?: Pick<Material, 'metadata'> | null;
  task?: { metadata?: Record<string, any> | null } | null;
  serviceName?: string;
}): CleanMaterialView {
  const materialSummary = getServiceSummary<CleanMaterialSummary>(material?.metadata?.cleanMaterials, serviceName);
  const taskSummary = getServiceSummary<CleanServiceTaskSummary>(task?.metadata?.cleanServiceJobs, serviceName);
  const materialStats = asRecord(materialSummary?.stats);
  const taskStats = asRecord(taskSummary?.stats);
  const artifacts = normalizeArtifacts(taskSummary?.artifacts);
  const provenanceObjectName =
    cleanString(materialSummary?.provenanceObjectName) ||
    cleanString(taskSummary?.artifacts?.provenance?.object);
  const latestVersion =
    cleanString(materialSummary?.latestVersion) ||
    cleanString(materialSummary?.assetVersion) ||
    cleanString(taskSummary?.assetVersion);
  const status =
    cleanString(materialSummary?.status) ||
    cleanString(materialSummary?.cleanState) ||
    cleanString(taskSummary?.status) ||
    cleanString(taskSummary?.cleanState);
  const sourceInput = normalizeSourceInput(
    materialSummary?.sourceInput,
    taskSummary?.sourceInput,
    taskSummary?.verificationSummary?.sourceInput,
  );
  const tokensTotal = numberOrNull(
    materialStats.tokensTotal ??
    materialStats.tokens_total ??
    taskStats.tokensTotal ??
    taskStats.tokens_total ??
    taskStats.tokens?.total,
  );
  const unresolvedAnchorCount = numberOrNull(
    materialStats.unresolvedAnchorCount ??
    materialStats.unresolved_anchor_count ??
    taskStats.unresolvedAnchorCount ??
    taskStats.unresolved_anchor_count,
  );
  const prefix = cleanString(materialSummary?.prefix);
  const present = Boolean(materialSummary || taskSummary || latestVersion || provenanceObjectName || artifacts.length > 0);
  const operatorDecision = asRecord(materialSummary?.operatorDecision);
  const operatorDecisionState = cleanString(operatorDecision.state) || (present ? 'pending-review' : null);

  return {
    serviceName,
    present,
    status,
    latestVersion,
    jobId: cleanString(taskSummary?.jobId),
    provenanceObjectName,
    prefix,
    sourceInput,
    tokensTotal,
    unresolvedAnchorCount,
    artifacts,
    artifactCount: artifacts.length,
    warnings: [
      ...((Array.isArray(materialSummary?.warnings) ? materialSummary?.warnings : []) || []),
      ...((Array.isArray(taskSummary?.warnings) ? taskSummary?.warnings : []) || []),
    ],
    operatorDecision: Object.keys(operatorDecision).length > 0 ? operatorDecision : null,
    operatorDecisionState,
    operatorDecisionReadOnly: Boolean(operatorDecisionState && operatorDecisionState !== 'pending-review'),
    updatedAt: cleanString(materialSummary?.updatedAt) || cleanString(taskSummary?.updatedAt),
    hasPrefixGap: !prefix && Boolean(latestVersion || provenanceObjectName || artifacts.length > 0),
  };
}
