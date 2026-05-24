import { useEffect, useMemo, useState } from 'react';
import { Code, ExternalLink, FileText, Loader2, TriangleAlert } from 'lucide-react';
import type { CleanMaterialView } from '../utils/cleanMaterialView';
import { renderMarkdown } from '../utils/markdown';

type Artifact = CleanMaterialView['artifacts'][number];

function getArtifactUrl(artifact: Artifact) {
  const bucket = artifact.bucket || 'eduassets-clean';
  return `/__proxy/upload/proxy-file?objectName=${encodeURIComponent(artifact.object)}&bucket=${encodeURIComponent(bucket)}`;
}

function getKind(artifact: Artifact) {
  if (artifact.object.endsWith('.md')) return 'markdown';
  if (artifact.object.endsWith('.json')) return 'json';
  if (artifact.object.endsWith('.txt')) return 'text';
  return 'unsupported';
}

function pickInitialArtifact(artifacts: Artifact[]) {
  return artifacts.find((artifact) => artifact.object.endsWith('/readable_tree.md') || artifact.role === 'readable_tree') ||
    artifacts.find((artifact) => artifact.object.endsWith('.json')) ||
    artifacts[0] ||
    null;
}

export function CleanMaterialArtifactInspector({ artifacts }: { artifacts: Artifact[] }) {
  const initialArtifact = useMemo(() => pickInitialArtifact(artifacts), [artifacts]);
  const [selectedObject, setSelectedObject] = useState(initialArtifact?.object || '');
  const selectedArtifact = artifacts.find((artifact) => artifact.object === selectedObject) || initialArtifact;
  const [loading, setLoading] = useState(false);
  const [content, setContent] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    setSelectedObject(initialArtifact?.object || '');
  }, [initialArtifact?.object]);

  useEffect(() => {
    if (!selectedArtifact) {
      setContent('');
      setError('');
      setLoading(false);
      return;
    }

    const kind = getKind(selectedArtifact);
    if (kind === 'unsupported') {
      setContent('');
      setError('');
      setLoading(false);
      return;
    }

    const controller = new AbortController();
    setLoading(true);
    setError('');
    setContent('');

    (async () => {
      try {
        const response = await fetch(getArtifactUrl(selectedArtifact), {
          cache: 'no-store',
          signal: controller.signal,
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const text = await response.text();
        if (kind === 'json') {
          try {
            setContent(JSON.stringify(JSON.parse(text), null, 2));
          } catch {
            setContent(text);
          }
        } else {
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
  }, [selectedArtifact?.object, selectedArtifact?.bucket]);

  if (artifacts.length === 0) {
    return (
      <div className="mt-4 rounded-md border border-dashed border-slate-200 bg-slate-50 p-3 text-xs text-slate-400">
        暂无可检查 artifact refs
      </div>
    );
  }

  const kind = selectedArtifact ? getKind(selectedArtifact) : 'unsupported';
  const artifactUrl = selectedArtifact ? getArtifactUrl(selectedArtifact) : '';

  return (
    <div className="mt-4 rounded-md border border-slate-100 bg-slate-50">
      <div className="border-b border-slate-100 p-3">
        <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <label className="flex min-w-0 flex-1 items-center gap-2 text-xs font-semibold text-slate-600">
            <FileText size={13} className="shrink-0 text-slate-400" />
            <select
              value={selectedArtifact?.object || ''}
              onChange={(event) => setSelectedObject(event.target.value)}
              className="min-w-0 flex-1 rounded border border-slate-200 bg-white px-2 py-1.5 font-mono text-[11px] text-slate-700 outline-none focus:border-emerald-300"
            >
              {artifacts.map((artifact) => (
                <option key={artifact.object} value={artifact.object}>
                  {artifact.role} · {artifact.object.split('/').pop()}
                </option>
              ))}
            </select>
          </label>
          {selectedArtifact && (
            <a
              href={artifactUrl}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center justify-center gap-1.5 rounded border border-emerald-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-emerald-700 hover:bg-emerald-50"
            >
              <ExternalLink size={12} />
              打开
            </a>
          )}
        </div>
      </div>

      <div className="min-h-40 max-h-96 overflow-auto bg-white">
        {loading && (
          <div className="flex h-40 items-center justify-center gap-2 text-xs text-slate-400">
            <Loader2 size={14} className="animate-spin" />
            加载 artifact...
          </div>
        )}
        {!loading && error && (
          <div className="flex items-start gap-2 p-4 text-xs text-red-600">
            <TriangleAlert size={14} className="mt-0.5 shrink-0" />
            <span className="break-words">读取失败：{error}</span>
          </div>
        )}
        {!loading && !error && kind === 'unsupported' && (
          <div className="flex h-40 items-center justify-center text-xs text-slate-400">
            当前 artifact 类型暂不支持内嵌预览，请使用“打开”链接查看。
          </div>
        )}
        {!loading && !error && kind === 'markdown' && (
          <div className="p-4 text-sm leading-6 text-slate-700" dangerouslySetInnerHTML={{ __html: renderMarkdown(content) }} />
        )}
        {!loading && !error && (kind === 'json' || kind === 'text') && (
          <pre className="whitespace-pre-wrap p-4 font-mono text-[11px] leading-5 text-slate-700">
            {content || '暂无内容'}
          </pre>
        )}
      </div>

      {selectedArtifact && (
        <div className="flex items-start gap-1.5 border-t border-slate-100 px-3 py-2 text-[10px] text-slate-400">
          <Code size={11} className="mt-0.5 shrink-0" />
          <span className="break-all">{selectedArtifact.bucket || 'eduassets-clean'} / {selectedArtifact.object}</span>
        </div>
      )}
    </div>
  );
}
