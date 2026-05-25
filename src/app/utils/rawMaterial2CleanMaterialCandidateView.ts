import type { CleanObjectRef, Material } from '../../store/types';

export interface RawMaterial2CleanMaterialCandidateView {
  present: boolean;
  serviceName: string;
  status: string | null;
  assetVersion: string | null;
  jobId: string | null;
  artifact: {
    role: 'candidate';
    object: string;
    bucket: string;
    sha256: string | null;
    sizeBytes: number | null;
  } | null;
  artifactUrl: string | null;
  sourceCleanMaterial: {
    serviceName: string | null;
    assetVersion: string | null;
    jobId: string | null;
    provenanceObjectName: string | null;
  } | null;
  sourceInput: CleanObjectRef | null;
  stats: {
    sectionCount: number | null;
    blockCount: number | null;
    sourceRefCount: number | null;
    candidateArtifactSizeBytes: number | null;
    outputContractSizeBytes: number | null;
  };
  preview: {
    candidateArtifactSha256: string | null;
    outputContractSha256: string | null;
  };
  warnings: string[];
  boundaries: Record<string, unknown>;
  updatedAt: string | null;
  conflict: string | null;
}

function asRecord(value: unknown): Record<string, any> {
  return value && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, any> : {};
}

function cleanString(value: unknown): string | null {
  return typeof value === 'string' && value.trim() ? value.trim() : null;
}

function numberOrNull(value: unknown): number | null {
  if (typeof value === 'number' && Number.isFinite(value)) return value;
  if (typeof value === 'string' && value.trim()) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

function normalizeObjectRef(value: unknown): RawMaterial2CleanMaterialCandidateView['artifact'] {
  const ref = asRecord(value);
  const object = cleanString(ref.object);
  if (!object) return null;
  return {
    role: 'candidate',
    object,
    bucket: cleanString(ref.bucket) || 'eduassets-clean',
    sha256: cleanString(ref.sha256),
    sizeBytes: numberOrNull(ref.size_bytes ?? ref.sizeBytes),
  };
}

function normalizeSourceInput(value: unknown): CleanObjectRef | null {
  const ref = asRecord(value);
  const object = cleanString(ref.object);
  if (!object) return null;
  return {
    bucket: cleanString(ref.bucket) || undefined,
    object,
    sha256: cleanString(ref.sha256) || undefined,
    size_bytes: numberOrNull(ref.size_bytes ?? ref.sizeBytes) ?? undefined,
    content_type: cleanString(ref.content_type) || cleanString(ref.contentType) || undefined,
  };
}

function sameArtifact(left: RawMaterial2CleanMaterialCandidateView['artifact'], right: RawMaterial2CleanMaterialCandidateView['artifact']) {
  if (!left || !right) return Boolean(left) === Boolean(right);
  return left.bucket === right.bucket &&
    left.object === right.object &&
    left.sha256 === right.sha256 &&
    left.sizeBytes === right.sizeBytes;
}

function artifactUrl(artifact: RawMaterial2CleanMaterialCandidateView['artifact']) {
  if (!artifact) return null;
  return `/__proxy/upload/proxy-file?objectName=${encodeURIComponent(artifact.object)}&bucket=${encodeURIComponent(artifact.bucket)}`;
}

function pickCandidateSummary({
  material,
  task,
  serviceName,
}: {
  material?: Pick<Material, 'metadata'> | null;
  task?: { metadata?: Record<string, any> | null } | null;
  serviceName: string;
}) {
  const materialRoot = asRecord(material?.metadata?.rawMaterial2CleanMaterial);
  const materialCurrent = asRecord(materialRoot.currentCandidate);
  const materialCandidates = asRecord(materialRoot.candidates);
  const materialByVersion = asRecord(materialCandidates.v1);
  const taskJobs = asRecord(task?.metadata?.rawMaterial2CleanMaterialJobs);
  const taskSummary = asRecord(taskJobs[serviceName]);

  const materialSummary = Object.keys(materialByVersion).length > 0 ? materialByVersion : materialCurrent;
  return { materialSummary, taskSummary };
}

export function buildRawMaterial2CleanMaterialCandidateView({
  material,
  task,
  serviceName = 'raw-material-2-clean-material',
}: {
  material?: Pick<Material, 'metadata'> | null;
  task?: { metadata?: Record<string, any> | null } | null;
  serviceName?: string;
}): RawMaterial2CleanMaterialCandidateView {
  const { materialSummary, taskSummary } = pickCandidateSummary({ material, task, serviceName });
  const summary = Object.keys(taskSummary).length > 0 ? taskSummary : materialSummary;
  const materialArtifact = normalizeObjectRef(asRecord(materialSummary.artifact).candidate);
  const taskArtifact = normalizeObjectRef(asRecord(taskSummary.artifact).candidate);
  const artifact = taskArtifact || materialArtifact;
  const sourceCleanMaterial = asRecord(summary.sourceCleanMaterial);
  const stats = asRecord(summary.stats);
  const preview = asRecord(summary.preview);
  const candidatePreview = asRecord(preview.candidateArtifact);
  const outputPreview = asRecord(preview.outputContract);
  const present = Boolean(Object.keys(summary).length > 0 || artifact);
  const conflict = taskArtifact && materialArtifact && !sameArtifact(taskArtifact, materialArtifact)
    ? 'task/material candidate ObjectRef mismatch'
    : null;

  return {
    present,
    serviceName,
    status: cleanString(summary.status) || cleanString(summary.cleanState),
    assetVersion: cleanString(summary.assetVersion) || cleanString(materialSummary.assetVersion),
    jobId: cleanString(summary.jobId) || cleanString(materialSummary.jobId),
    artifact,
    artifactUrl: artifactUrl(artifact),
    sourceCleanMaterial: Object.keys(sourceCleanMaterial).length > 0 ? {
      serviceName: cleanString(sourceCleanMaterial.serviceName),
      assetVersion: cleanString(sourceCleanMaterial.assetVersion),
      jobId: cleanString(sourceCleanMaterial.jobId),
      provenanceObjectName: cleanString(sourceCleanMaterial.provenanceObjectName),
    } : null,
    sourceInput: normalizeSourceInput(summary.sourceInput),
    stats: {
      sectionCount: numberOrNull(stats.sectionCount),
      blockCount: numberOrNull(stats.blockCount),
      sourceRefCount: numberOrNull(stats.sourceRefCount),
      candidateArtifactSizeBytes: numberOrNull(stats.candidateArtifactSizeBytes ?? candidatePreview.size_bytes),
      outputContractSizeBytes: numberOrNull(stats.outputContractSizeBytes ?? outputPreview.size_bytes),
    },
    preview: {
      candidateArtifactSha256: cleanString(candidatePreview.sha256) || artifact?.sha256 || null,
      outputContractSha256: cleanString(outputPreview.sha256),
    },
    warnings: Array.isArray(summary.warnings) ? summary.warnings.map(String) : [],
    boundaries: asRecord(summary.boundaries),
    updatedAt: cleanString(summary.updatedAt) || cleanString(materialSummary.updatedAt),
    conflict,
  };
}
