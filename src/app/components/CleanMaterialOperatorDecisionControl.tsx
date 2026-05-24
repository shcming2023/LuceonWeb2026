import { useMemo, useState } from 'react';
import { CheckCircle2, ClipboardCheck, Wrench, XCircle } from 'lucide-react';
import type { Material } from '../../store/types';
import type { CleanMaterialView } from '../utils/cleanMaterialView';
import { buildCleanMaterialDecisionPatch, CleanMaterialDecisionState } from '../utils/cleanMaterialDecision';

const ACTIONS: Array<{ state: CleanMaterialDecisionState; label: string; icon: typeof CheckCircle2; className: string }> = [
  { state: 'accepted', label: 'Accept', icon: CheckCircle2, className: 'border-emerald-200 text-emerald-700 hover:bg-emerald-50' },
  { state: 'needs-repair', label: 'Needs repair', icon: Wrench, className: 'border-amber-200 text-amber-700 hover:bg-amber-50' },
  { state: 'rejected', label: 'Reject', icon: XCircle, className: 'border-red-200 text-red-700 hover:bg-red-50' },
];

function stateLabel(state: string | null) {
  const labels: Record<string, string> = {
    'pending-review': 'pending-review',
    accepted: 'accepted',
    'needs-repair': 'needs-repair',
    rejected: 'rejected',
    superseded: 'superseded',
  };
  return state ? labels[state] || state : '—';
}

export function CleanMaterialOperatorDecisionControl({
  material,
  view,
}: {
  material?: Pick<Material, 'metadata'> | null;
  view: CleanMaterialView;
}) {
  const [selectedState, setSelectedState] = useState<CleanMaterialDecisionState>('accepted');
  const [reason, setReason] = useState('');
  const [note, setNote] = useState('');
  const canBuild = Boolean(material && view.present && view.artifactCount > 0 && !view.operatorDecisionReadOnly);
  const result = useMemo(() => {
    if (!material || !canBuild) return null;
    return buildCleanMaterialDecisionPatch({
      material,
      view,
      state: selectedState,
      reason,
      note,
      decidedBy: 'local-operator',
      decidedAt: 'MOCK_SAFE_PREVIEW_TIMESTAMP',
    });
  }, [material, canBuild, note, reason, selectedState, view]);

  if (!view.present) return null;

  return (
    <div className="mt-4 rounded-md border border-slate-100 bg-slate-50">
      <div className="flex items-start justify-between gap-3 border-b border-slate-100 px-3 py-2">
        <div>
          <p className="flex items-center gap-1.5 text-xs font-semibold text-slate-700">
            <ClipboardCheck size={13} className="text-slate-400" />
            Operator decision
          </p>
          <p className="mt-1 font-mono text-[11px] text-slate-500">
            {stateLabel(view.operatorDecisionState)}
          </p>
        </div>
        {view.operatorDecision?.decidedAt && (
          <span className="rounded bg-white px-2 py-1 font-mono text-[10px] text-slate-400">
            {String(view.operatorDecision.decidedAt)}
          </span>
        )}
      </div>

      {view.operatorDecisionReadOnly ? (
        <div className="space-y-2 p-3 text-xs text-slate-500">
          <p>当前 Clean Material 决策已只读。</p>
          {view.operatorDecision?.decidedBy && (
            <p>Operator: <span className="font-mono text-slate-600">{String(view.operatorDecision.decidedBy)}</span></p>
          )}
          {view.operatorDecision?.reason && (
            <p>Reason: <span className="text-slate-600">{String(view.operatorDecision.reason)}</span></p>
          )}
          {view.operatorDecision?.note && (
            <p>Note: <span className="text-slate-600">{String(view.operatorDecision.note)}</span></p>
          )}
        </div>
      ) : (
        <div className="space-y-3 p-3">
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
            {ACTIONS.map((action) => {
              const Icon = action.icon;
              const active = selectedState === action.state;
              return (
                <button
                  key={action.state}
                  type="button"
                  disabled={!canBuild}
                  onClick={() => setSelectedState(action.state)}
                  className={`flex items-center justify-center gap-1.5 rounded border px-2.5 py-2 text-xs font-semibold disabled:cursor-not-allowed disabled:opacity-40 ${action.className} ${active ? 'bg-white ring-1 ring-slate-200' : 'bg-white/70'}`}
                >
                  <Icon size={13} />
                  {action.label}
                </button>
              );
            })}
          </div>

          {selectedState !== 'accepted' && (
            <input
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              className="w-full rounded border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700 outline-none focus:border-amber-300"
              placeholder="Negative decision reason required"
            />
          )}

          <textarea
            value={note}
            onChange={(event) => setNote(event.target.value)}
            className="min-h-16 w-full rounded border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700 outline-none focus:border-slate-300"
            placeholder="Optional note"
          />

          {!canBuild && (
            <p className="rounded border border-amber-100 bg-amber-50 px-3 py-2 text-xs text-amber-700">
              Decision patch preview is disabled until current artifact refs are available.
            </p>
          )}

          {result && !result.ok && (
            <p className="rounded border border-red-100 bg-red-50 px-3 py-2 text-xs text-red-600">
              {result.error}
            </p>
          )}

          {result?.ok && result.patch && (
            <details className="rounded border border-slate-100 bg-white">
              <summary className="cursor-pointer px-3 py-2 text-xs font-semibold text-slate-600">
                Mock-safe metadata PATCH preview
              </summary>
              <pre className="max-h-64 overflow-auto border-t border-slate-100 p-3 text-[10px] leading-4 text-slate-600">
                {JSON.stringify(result.patch, null, 2)}
              </pre>
            </details>
          )}
        </div>
      )}
    </div>
  );
}
