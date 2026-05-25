import { useEffect, useState } from 'react';
import { Boxes, CheckCircle2, ExternalLink, FileJson, Hash, Loader2, TriangleAlert } from 'lucide-react';
import type { RawMaterial2CleanMaterialCandidateView } from '../utils/rawMaterial2CleanMaterialCandidateView';

function mono(value: string | number | null | undefined) {
  return value === null || value === undefined || value === '' ? '-' : String(value);
}

function Field({ label, value }: { label: string; value: string | number | null | undefined }) {
  return (
    <div className="min-w-0">
      <dt className="text-[10px] font-semibold uppercase tracking-wide text-slate-400">{label}</dt>
      <dd className="mt-1 break-all font-mono text-xs text-slate-700">{mono(value)}</dd>
    </div>
  );
}

export function RawMaterial2CleanMaterialCandidateCard({ view }: { view: RawMaterial2CleanMaterialCandidateView }) {
  const [loading, setLoading] = useState(false);
  const [content, setContent] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    if (!view.artifactUrl) {
      setContent('');
      setError('');
      setLoading(false);
      return;
    }

    const controller = new AbortController();
    setLoading(true);
    setContent('');
    setError('');

    (async () => {
      try {
        const response = await fetch(view.artifactUrl!, { cache: 'no-store', signal: controller.signal });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const text = await response.text();
        try {
          setContent(JSON.stringify(JSON.parse(text), null, 2));
        } catch {
          setContent(text);
        }
      } catch (err) {
        if (err instanceof DOMException && err.name === 'AbortError') return;
        setError(err instanceof Error ? err.message : String(err));
      } finally {
        setLoading(false);
      }
    })();

    return () => controller.abort();
  }, [view.artifactUrl]);

  if (!view.present) {
    return (
      <section className="rounded-lg border border-dashed border-slate-200 bg-white p-5">
        <div className="flex items-center gap-2 text-slate-600">
          <Boxes size={16} className="text-slate-400" />
          <h2 className="text-sm font-semibold">Raw2Clean Candidate</h2>
        </div>
        <p className="mt-3 text-sm text-slate-400">暂无 Raw2Clean candidate 元数据</p>
      </section>
    );
  }

  return (
    <section className="rounded-lg border border-cyan-100 bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2 text-slate-800">
            <Boxes size={16} className="text-cyan-600" />
            <h2 className="text-sm font-bold">Raw2Clean Candidate</h2>
          </div>
          <p className="mt-1 break-all font-mono text-xs text-slate-500">{view.serviceName}</p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <span className="rounded-full bg-cyan-50 px-2.5 py-1 text-xs font-semibold text-cyan-700">
            {view.assetVersion || '-'}
          </span>
          <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
            {view.status || 'unknown'}
          </span>
        </div>
      </div>

      {view.conflict && (
        <div className="mb-4 flex items-start gap-2 rounded-md border border-red-100 bg-red-50 px-3 py-2 text-xs text-red-700">
          <TriangleAlert size={14} className="mt-0.5 shrink-0" />
          <span>{view.conflict}</span>
        </div>
      )}

      {view.decision && (
        <div className="mb-4 rounded-md border border-emerald-100 bg-emerald-50 px-3 py-2">
          <div className="flex items-center gap-2 text-xs font-semibold text-emerald-700">
            <CheckCircle2 size={14} />
            <span>Decision: {view.decision.state || 'recorded'}</span>
          </div>
          <div className="mt-2 grid grid-cols-1 gap-2 md:grid-cols-2">
            <Field label="Decided At" value={view.decision.decidedAt} />
            <Field label="Decided By" value={view.decision.decidedBy} />
            <Field label="Final Quality Accepted" value={view.decision.finalQualityAccepted === null ? '-' : String(view.decision.finalQualityAccepted)} />
            <Field label="Decision Reason" value={view.decision.reason} />
          </div>
        </div>
      )}

      <dl className="grid grid-cols-1 gap-3 md:grid-cols-2">
        <Field label="Job ID" value={view.jobId} />
        <Field label="Candidate Object" value={view.artifact?.object} />
        <Field label="Candidate SHA256" value={view.artifact?.sha256} />
        <Field label="Candidate Size" value={view.artifact?.sizeBytes} />
        <Field label="Source Clean Version" value={view.sourceCleanMaterial?.assetVersion} />
        <Field label="Source Input" value={view.sourceInput?.object} />
        <Field label="Sections" value={view.stats.sectionCount} />
        <Field label="Blocks" value={view.stats.blockCount} />
      </dl>

      {view.artifact && (
        <div className="mt-4 rounded-md border border-slate-100 bg-slate-50">
          <div className="flex flex-col gap-2 border-b border-slate-100 p-3 md:flex-row md:items-center md:justify-between">
            <div className="flex min-w-0 items-start gap-2 text-xs text-slate-600">
              <FileJson size={13} className="mt-0.5 shrink-0 text-slate-400" />
              <span className="break-all font-mono">{view.artifact.bucket} / {view.artifact.object}</span>
            </div>
            {view.artifactUrl && (
              <a
                href={view.artifactUrl}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center justify-center gap-1.5 rounded border border-cyan-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-cyan-700 hover:bg-cyan-50"
              >
                <ExternalLink size={12} />
                打开
              </a>
            )}
          </div>
          <div className="min-h-40 max-h-96 overflow-auto bg-white">
            {loading && (
              <div className="flex h-40 items-center justify-center gap-2 text-xs text-slate-400">
                <Loader2 size={14} className="animate-spin" />
                加载 candidate...
              </div>
            )}
            {!loading && error && (
              <div className="flex items-start gap-2 p-4 text-xs text-red-600">
                <TriangleAlert size={14} className="mt-0.5 shrink-0" />
                <span className="break-words">读取失败：{error}</span>
              </div>
            )}
            {!loading && !error && (
              <pre className="whitespace-pre-wrap p-4 font-mono text-[11px] leading-5 text-slate-700">
                {content || '暂无内容'}
              </pre>
            )}
          </div>
          <div className="flex items-start gap-1.5 border-t border-slate-100 px-3 py-2 text-[10px] text-slate-400">
            <Hash size={10} className="mt-0.5 shrink-0" />
            <span className="break-all">{view.preview.candidateArtifactSha256 || '-'}</span>
          </div>
        </div>
      )}

      {view.warnings.length > 0 && (
        <div className="mt-4 rounded-md border border-amber-100 bg-amber-50 px-3 py-2 text-xs text-amber-700">
          {view.warnings.join(', ')}
        </div>
      )}
    </section>
  );
}
