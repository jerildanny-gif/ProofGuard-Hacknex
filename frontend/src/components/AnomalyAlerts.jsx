import React from 'react';
import { 
  ShieldAlert, 
  AlertTriangle, 
  Info, 
  CheckCircle2, 
  Lock, 
  Ban, 
  HelpCircle,
  AlertOctagon
} from 'lucide-react';

export default function AnomalyAlerts({ health }) {
  if (!health) return null;

  const { detected_issues, health_score, duplicate_rows, total_missing_cells } = health;

  const criticalIssues = detected_issues.filter(i => i.severity === 'critical');
  const warningIssues = detected_issues.filter(i => i.severity === 'warning');
  const infoIssues = detected_issues.filter(i => i.severity === 'info');

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur-md space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800/80 gap-3">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-400">
            <ShieldAlert className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">
              Data Reliability & Guardrail Profiler
            </h3>
            <p className="text-xs text-slate-400">
              Trap detection layer protecting against hallucinated analytics & unverified claims
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-[11px] font-mono px-2.5 py-1 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 font-semibold">
            {detected_issues.length} Flagged Situation{detected_issues.length === 1 ? '' : 's'}
          </span>
        </div>
      </div>

      {/* ProofGuard Golden Rule Card */}
      <div className="bg-gradient-to-r from-indigo-950/40 via-slate-900/60 to-purple-950/40 border border-indigo-500/30 rounded-xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-start space-x-3">
          <div className="p-2 rounded-lg bg-indigo-500/20 text-indigo-400 mt-0.5">
            <Lock className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-xs font-bold text-white uppercase tracking-wider">
              ProofGuard Non-Hallucination Invariant
            </h4>
            <p className="text-xs text-slate-300 mt-0.5">
              Whenever any query encounters ambiguous dates, mixed currency symbols, or contradictory rows without explicit harmonization:
            </p>
          </div>
        </div>
        <div className="sm:flex-shrink-0 bg-slate-950 px-3.5 py-2 rounded-lg border border-amber-500/30 font-mono text-xs text-amber-300 font-bold shadow-inner">
          “Cannot determine reliably from the available data.”
        </div>
      </div>

      {/* Issues Listing */}
      <div className="space-y-2.5">
        {detected_issues.length === 0 ? (
          <div className="p-8 text-center bg-slate-950/40 rounded-xl border border-slate-800">
            <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
            <p className="text-sm font-medium text-white">No severe data reliability traps detected</p>
            <p className="text-xs text-slate-400 mt-1">This dataset meets structural baseline requirements for numerical verification.</p>
          </div>
        ) : (
          detected_issues.map((issue, idx) => {
            const isCrit = issue.severity === 'critical';
            const isWarn = issue.severity === 'warning';

            return (
              <div
                key={idx}
                className={`p-3.5 rounded-xl border flex items-start space-x-3 transition-colors ${
                  isCrit
                    ? 'bg-rose-950/20 border-rose-500/30 text-rose-200'
                    : isWarn
                    ? 'bg-amber-950/20 border-amber-500/30 text-amber-200'
                    : 'bg-slate-950/40 border-slate-800/80 text-slate-300'
                }`}
              >
                <div className={`p-1.5 rounded-lg mt-0.5 flex-shrink-0 ${
                  isCrit ? 'bg-rose-500/20 text-rose-400' : isWarn ? 'bg-amber-500/20 text-amber-400' : 'bg-slate-800 text-slate-400'
                }`}>
                  {isCrit ? <AlertOctagon className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-semibold text-white font-mono">
                      {issue.category}
                    </span>
                    <span className={`text-[10px] font-bold px-1.5 py-0.2 rounded uppercase ${
                      isCrit ? 'bg-rose-500/20 text-rose-300' : isWarn ? 'bg-amber-500/20 text-amber-300' : 'bg-slate-800 text-slate-400'
                    }`}>
                      {issue.severity}
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                    {issue.message}
                  </p>
                </div>

                <div className="hidden sm:block text-right">
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-400">
                    Guardrail Active
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Summary Matrix for the Hackathon Requirements */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-slate-800/60 text-xs">
        <div className="p-2.5 rounded-xl bg-slate-950/40 border border-slate-800">
          <span className="text-[10px] text-slate-500 block mb-1">Duplicate Traps</span>
          <span className={`font-mono font-semibold ${duplicate_rows > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
            {duplicate_rows > 0 ? `${duplicate_rows} Rows Flagged` : 'Clean (0)'}
          </span>
        </div>
        <div className="p-2.5 rounded-xl bg-slate-950/40 border border-slate-800">
          <span className="text-[10px] text-slate-500 block mb-1">Missing Cells</span>
          <span className={`font-mono font-semibold ${total_missing_cells > 0 ? 'text-amber-400' : 'text-emerald-400'}`}>
            {total_missing_cells > 0 ? `${total_missing_cells} Empty Cells` : 'Complete'}
          </span>
        </div>
        <div className="p-2.5 rounded-xl bg-slate-950/40 border border-slate-800">
          <span className="text-[10px] text-slate-500 block mb-1">Currency / Units</span>
          <span className="font-mono font-semibold text-indigo-300">
            Auto-Scanned
          </span>
        </div>
        <div className="p-2.5 rounded-xl bg-slate-950/40 border border-slate-800">
          <span className="text-[10px] text-slate-500 block mb-1">Fallback Guardrail</span>
          <span className="font-mono font-semibold text-amber-300">
            Enforced
          </span>
        </div>
      </div>
    </div>
  );
}
