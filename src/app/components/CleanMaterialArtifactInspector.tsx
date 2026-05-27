import { useEffect, useMemo, useState } from 'react';
import { Code, ExternalLink, FileJson, Fingerprint, ListTree, Loader2, TriangleAlert } from 'lucide-react';
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

const PRIMARY_ARTIFACTS = [
  { role: 'readable_tree', label: '可读目录', icon: ListTree },
  { role: 'logic_tree', label: '结构化目录树', icon: FileJson },
  { role: 'skeleton', label: '目录骨架', icon: Code },
  { role: 'provenance', label: '溯源', icon: Fingerprint },
] as const;

interface LoadedArtifact {
  artifact: Artifact;
  loading: boolean;
  content: string;
  error: string;
}

function formatArtifactContent(artifact: Artifact, text: string) {
  if (getKind(artifact) !== 'json') return text;
  try {
    return JSON.stringify(JSON.parse(text), null, 2);
  } catch {
    return text;
  }
}

export function CleanMaterialArtifactInspector({ artifacts }: { artifacts: Artifact[] }) {
  const primaryArtifacts = useMemo(() => (
    PRIMARY_ARTIFACTS
      .map((item) => ({
        ...item,
        artifact: artifacts.find((artifact) => artifact.role === item.role || artifact.object.endsWith(`/${item.role}.${item.role === 'readable_tree' ? 'md' : 'json'}`)) || null,
      }))
      .filter((item): item is typeof item & { artifact: Artifact } => Boolean(item.artifact))
  ), [artifacts]);
  const [loadedByObject, setLoadedByObject] = useState<Record<string, LoadedArtifact>>({});

  useEffect(() => {
    const controller = new AbortController();
    const loadable = primaryArtifacts
      .map((item) => item.artifact)
      .filter((artifact) => getKind(artifact) !== 'unsupported');

    setLoadedByObject(Object.fromEntries(
      loadable.map((artifact) => [artifact.object, { artifact, loading: true, content: '', error: '' }]),
    ));

    (async () => {
      await Promise.all(loadable.map(async (artifact) => {
        try {
          const response = await fetch(getArtifactUrl(artifact), {
            cache: 'no-store',
            signal: controller.signal,
          });
          if (!response.ok) throw new Error(`HTTP ${response.status}`);
          const text = await response.text();
          setLoadedByObject((prev) => ({
            ...prev,
            [artifact.object]: {
              artifact,
              loading: false,
              content: formatArtifactContent(artifact, text),
              error: '',
            },
          }));
        } catch (err) {
          if (err instanceof DOMException && err.name === 'AbortError') return;
          setLoadedByObject((prev) => ({
            ...prev,
            [artifact.object]: {
              artifact,
              loading: false,
              content: '',
              error: err instanceof Error ? err.message : String(err),
            },
          }));
        }
      }));
    })();

    return () => controller.abort();
  }, [primaryArtifacts]);

  if (artifacts.length === 0) {
    return (
      <div className="mt-4 rounded-md border border-dashed border-slate-200 bg-slate-50 p-3 text-xs text-slate-400">
        暂无可检查 artifact refs
      </div>
    );
  }

  return (
    <div className="mt-4 space-y-3">
      <div className="flex items-center gap-2 text-sm font-bold text-slate-800">
        <ListTree size={16} className="text-emerald-600" />
        目录重建结果
      </div>

      {primaryArtifacts.length === 0 && (
        <div className="rounded-md border border-dashed border-slate-200 bg-slate-50 p-3 text-xs text-slate-400">
          未找到 readable_tree / logic_tree / skeleton / provenance artifact。
        </div>
      )}

      {primaryArtifacts.map(({ role, label, icon: Icon, artifact }) => {
        const loaded = loadedByObject[artifact.object];
        const kind = getKind(artifact);
        return (
          <section key={role} className="overflow-hidden rounded-md border border-slate-100 bg-white">
            <div className="flex flex-col gap-2 border-b border-slate-100 bg-slate-50 px-3 py-2 md:flex-row md:items-center md:justify-between">
              <div className="min-w-0">
                <div className="flex items-center gap-1.5 text-xs font-bold text-slate-700">
                  <Icon size={13} className={role === 'readable_tree' ? 'text-emerald-600' : 'text-slate-400'} />
                  {label}
                </div>
                <div className="mt-1 break-all font-mono text-[10px] text-slate-400">
                  {artifact.bucket || 'eduassets-clean'} / {artifact.object}
                </div>
              </div>
              <a
                href={getArtifactUrl(artifact)}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center justify-center gap-1.5 rounded border border-emerald-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-emerald-700 hover:bg-emerald-50"
              >
                <ExternalLink size={12} />
                打开
              </a>
            </div>

            <div className="max-h-96 min-h-20 overflow-auto">
              {loaded?.loading && (
                <div className="flex h-24 items-center justify-center gap-2 text-xs text-slate-400">
                  <Loader2 size={14} className="animate-spin" />
                  加载 {label}...
                </div>
              )}
              {loaded?.error && (
                <div className="flex items-start gap-2 p-4 text-xs text-red-600">
                  <TriangleAlert size={14} className="mt-0.5 shrink-0" />
                  <span className="break-words">读取失败：{loaded.error}</span>
                </div>
              )}
              {!loaded?.loading && !loaded?.error && kind === 'markdown' && (
                <div className="p-4 text-sm leading-6 text-slate-700">
                  <div className="mb-3 rounded border border-emerald-100 bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-700">
                    由目录重建生成的可读目录
                  </div>
                  <div dangerouslySetInnerHTML={{ __html: renderMarkdown(loaded?.content || '') }} />
                </div>
              )}
              {!loaded?.loading && !loaded?.error && (kind === 'json' || kind === 'text') && (
                <pre className="whitespace-pre-wrap p-4 font-mono text-[11px] leading-5 text-slate-700">
                  {loaded?.content || '暂无内容'}
                </pre>
              )}
              {!loaded?.loading && !loaded?.error && kind === 'unsupported' && (
                <div className="flex h-24 items-center justify-center text-xs text-slate-400">
                  当前 artifact 类型暂不支持内嵌预览，请使用“打开”链接查看。
                </div>
              )}
            </div>

            <div className="flex items-start gap-1.5 border-t border-slate-100 px-3 py-2 text-[10px] text-slate-400">
              <Code size={11} className="mt-0.5 shrink-0" />
              <span className="break-all">{artifact.sha256 || 'sha256 unavailable'}</span>
            </div>
          </section>
        );
      })}
    </div>
  );
}
