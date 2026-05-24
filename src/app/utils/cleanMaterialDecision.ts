import type { CleanMaterialView } from './cleanMaterialView';
import type { Material } from '../../store/types';

export type CleanMaterialDecisionState = 'accepted' | 'needs-repair' | 'rejected';

export interface BuildCleanMaterialDecisionPatchInput {
  material: Pick<Material, 'metadata'>;
  view: CleanMaterialView;
  state: CleanMaterialDecisionState;
  reason?: string;
  note?: string;
  decidedBy?: string;
  decidedAt?: string;
}

export interface CleanMaterialDecisionPatchResult {
  ok: boolean;
  error?: string;
  patch?: {
    metadata: Record<string, any>;
  };
}

const NEGATIVE_STATES = new Set<CleanMaterialDecisionState>(['needs-repair', 'rejected']);

function compactText(value: unknown) {
  return typeof value === 'string' && value.trim() ? value.trim() : null;
}

function cloneRecord<T>(value: T): T {
  return JSON.parse(JSON.stringify(value ?? {}));
}

export function buildCleanMaterialArtifactSnapshot(view: CleanMaterialView) {
  return {
    assetVersion: view.latestVersion,
    jobId: view.jobId,
    provenanceObjectName: view.provenanceObjectName,
    sourceInput: view.sourceInput ? cloneRecord(view.sourceInput) : null,
    artifactRefs: Object.fromEntries(view.artifacts.map((artifact) => [
      artifact.role,
      {
        bucket: artifact.bucket || 'eduassets-clean',
        object: artifact.object,
        ...(artifact.sha256 ? { sha256: artifact.sha256 } : {}),
        ...(artifact.sizeBytes != null ? { size_bytes: artifact.sizeBytes } : {}),
      },
    ])),
    tokensTotal: view.tokensTotal,
    unresolvedAnchorCount: view.unresolvedAnchorCount,
  };
}

export function buildCleanMaterialDecisionPatch({
  material,
  view,
  state,
  reason = '',
  note = '',
  decidedBy = 'local-operator',
  decidedAt = new Date().toISOString(),
}: BuildCleanMaterialDecisionPatchInput): CleanMaterialDecisionPatchResult {
  if (!view.present) return { ok: false, error: 'clean-material-missing' };
  if (view.operatorDecisionReadOnly) return { ok: false, error: 'clean-material-decision-read-only' };
  if (!view.latestVersion) return { ok: false, error: 'clean-material-version-missing' };
  if (view.artifacts.length === 0) return { ok: false, error: 'clean-material-artifacts-missing' };

  const cleanReason = compactText(reason);
  if (NEGATIVE_STATES.has(state) && !cleanReason) {
    return { ok: false, error: 'decision-reason-required' };
  }

  const metadata = cloneRecord(material.metadata || {});
  const cleanMaterials = cloneRecord(metadata.cleanMaterials || {});
  const existingSummary = cloneRecord(cleanMaterials[view.serviceName] || {});

  cleanMaterials[view.serviceName] = {
    ...existingSummary,
    operatorDecision: {
      state,
      decidedAt,
      decidedBy,
      reason: cleanReason,
      note: compactText(note),
      artifactSnapshot: buildCleanMaterialArtifactSnapshot(view),
      supersededBy: null,
      updatedAt: decidedAt,
    },
  };

  return {
    ok: true,
    patch: {
      metadata: {
        ...metadata,
        cleanMaterials,
      },
    },
  };
}
