import { Boxes, ChevronDown, FileJson, Hash, Link2 } from 'lucide-react';
import type { CleanMaterialView } from '../utils/cleanMaterialView';
import type { Material } from '../../store/types';
import { CleanMaterialArtifactInspector } from './CleanMaterialArtifactInspector';
import { CleanMaterialOperatorDecisionControl } from './CleanMaterialOperatorDecisionControl';

function mono(value: string | number | null | undefined) {
  return value === null || value === undefined || value === '' ? '—' : String(value);
}

function Field({ label, value, title }: { label: string; value: string | number | null | undefined; title?: string }) {
  return (
    <div className="min-w-0">
      <dt className="text-[10px] font-semibold uppercase tracking-wide text-slate-400">{label}</dt>
      <dd className="mt-1 break-all font-mono text-xs text-slate-700" title={title || mono(value)}>
        {mono(value)}
      </dd>
    </div>
  );
}

export function CleanMaterialSummaryCard({ material, view }: { material?: Pick<Material, 'metadata'> | null; view: CleanMaterialView }) {
  if (!view.present) {
    return (
      <section className="rounded-lg border border-dashed border-slate-200 bg-white p-5">
        <div className="flex items-center gap-2 text-slate-600">
          <Boxes size={16} className="text-slate-400" />
          <h2 className="text-sm font-semibold">Clean Material</h2>
        </div>
        <p className="mt-3 text-sm text-slate-400">暂无 Clean Material 元数据</p>
      </section>
    );
  }

  return (
    <section className="rounded-lg border border-emerald-100 bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2 text-slate-800">
            <Boxes size={16} className="text-emerald-600" />
            <h2 className="text-sm font-bold">Clean Material</h2>
          </div>
          <p className="mt-1 break-all font-mono text-xs text-slate-500">{view.serviceName}</p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <span className="rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700">
            {view.latestVersion || '—'}
          </span>
          <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
            {view.status || 'unknown'}
          </span>
        </div>
      </div>

      {view.hasPrefixGap && (
        <div className="mb-4 rounded-md border border-amber-100 bg-amber-50 px-3 py-2 text-xs text-amber-700">
          prefix 为空；当前摘要使用 task artifact refs 与 material provenance ref 展示，不隐藏已接受版本。
        </div>
      )}

      <dl className="grid grid-cols-1 gap-3 md:grid-cols-2">
        <Field label="Job ID" value={view.jobId} />
        <Field label="Provenance" value={view.provenanceObjectName} />
        <Field label="Source Object" value={view.sourceInput?.object} />
        <Field label="Source SHA256" value={view.sourceInput?.sha256} />
        <Field label="Source Size" value={view.sourceInput?.size_bytes ?? view.sourceInput?.sizeBytes} />
        <Field label="Tokens Total" value={view.tokensTotal} />
        <Field label="Unresolved Anchors" value={view.unresolvedAnchorCount} />
        <Field label="Artifact Count" value={view.artifactCount} />
      </dl>

      {view.artifacts.length > 0 && (
        <details className="group mt-4 rounded-md border border-slate-100 bg-slate-50">
          <summary className="flex cursor-pointer list-none items-center justify-between gap-2 px-3 py-2 text-xs font-semibold text-slate-600">
            <span className="flex items-center gap-1.5">
              <FileJson size={13} className="text-slate-400" />
              Artifact refs
            </span>
            <ChevronDown size={14} className="text-slate-400 transition-transform group-open:rotate-180" />
          </summary>
          <div className="space-y-2 border-t border-slate-100 p-3">
            {view.artifacts.map((artifact) => (
              <div key={artifact.role} className="rounded border border-slate-100 bg-white p-2">
                <div className="mb-1 flex items-center justify-between gap-2">
                  <span className="text-xs font-semibold text-slate-700">{artifact.role}</span>
                  {artifact.sizeBytes != null && <span className="text-[10px] text-slate-400">{artifact.sizeBytes} bytes</span>}
                </div>
                <p className="flex items-start gap-1.5 break-all font-mono text-[11px] text-slate-600">
                  <Link2 size={11} className="mt-0.5 shrink-0 text-slate-400" />
                  {artifact.object}
                </p>
                {artifact.sha256 && (
                  <p className="mt-1 flex items-start gap-1.5 break-all font-mono text-[10px] text-slate-400">
                    <Hash size={10} className="mt-0.5 shrink-0" />
                    {artifact.sha256}
                  </p>
                )}
              </div>
            ))}
          </div>
        </details>
      )}

      <CleanMaterialArtifactInspector artifacts={view.artifacts} />
      <CleanMaterialOperatorDecisionControl material={material} view={view} />
    </section>
  );
}
