import { Brain, Boxes, CheckCircle2, FileText, GitBranch, Layers3, Sparkles } from 'lucide-react';
import type { MainlinePipelineView } from '../utils/mainlinePipeline';

const ICONS = {
  pdf: FileText,
  mineru: Layers3,
  ai: Brain,
  toc: GitBranch,
  raw: Boxes,
  clean: Sparkles,
};

const STATE_STYLE = {
  done: 'border-emerald-200 bg-emerald-50 text-emerald-800',
  current: 'border-blue-200 bg-blue-50 text-blue-800',
  pending: 'border-slate-200 bg-white text-slate-600',
  blocked: 'border-amber-200 bg-amber-50 text-amber-800',
};

const DOT_STYLE = {
  done: 'bg-emerald-600 text-white',
  current: 'bg-blue-600 text-white',
  pending: 'bg-slate-200 text-slate-500',
  blocked: 'bg-amber-500 text-white',
};

export function MainlinePipelinePanel({
  view,
  compact = false,
  stepLinks = {},
}: {
  view: MainlinePipelineView;
  compact?: boolean;
  stepLinks?: Partial<Record<string, string>>;
}) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <GitBranch size={16} className="text-blue-600" />
            <h2 className="text-sm font-bold text-slate-900">资产处理主线</h2>
          </div>
          <p className="mt-1 text-xs text-slate-500">PDF → MinerU → AI → 目录重建 → Raw Material → Clean Material</p>
        </div>
        <div className="shrink-0 rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-700">
          {view.completedCount}/{view.steps.length} · {view.currentLabel}
        </div>
      </div>

      <div className={compact ? 'grid grid-cols-1 gap-2 sm:grid-cols-2 xl:grid-cols-3' : 'grid grid-cols-1 gap-2 md:grid-cols-2 xl:grid-cols-6'}>
        {view.steps.map((item, index) => {
          const Icon = ICONS[item.key as keyof typeof ICONS] || Boxes;
          const href = stepLinks[item.key];
          const content = (
            <>
              <div className="flex items-start gap-2">
                <span className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[10px] font-bold ${DOT_STYLE[item.state]}`}>
                  {item.state === 'done' ? <CheckCircle2 size={13} /> : index + 1}
                </span>
                <div className="min-w-0">
                  <div className="flex items-center gap-1.5">
                    <Icon size={13} className="shrink-0" />
                    <p className="truncate text-xs font-bold">{item.label}</p>
                  </div>
                  <p className="mt-1 text-xs leading-snug opacity-90">{item.detail}</p>
                  {item.meta && (
                    <p className="mt-1 truncate font-mono text-[10px] opacity-70" title={item.meta}>
                      {item.meta}
                    </p>
                  )}
                </div>
              </div>
              {href && (
                <span className="mt-2 inline-flex text-[10px] font-semibold opacity-80">
                  查看产物
                </span>
              )}
            </>
          );

          if (href) {
            return (
              <a
                key={item.key}
                href={href}
                className={`block min-w-0 rounded-lg border p-3 transition hover:-translate-y-0.5 hover:shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-300 ${STATE_STYLE[item.state]}`}
                aria-label={`查看${item.label}产物`}
              >
                {content}
              </a>
            );
          }

          return (
            <div key={item.key} className={`min-w-0 rounded-lg border p-3 ${STATE_STYLE[item.state]}`}>
              {content}
            </div>
          );
        })}
      </div>
    </section>
  );
}
