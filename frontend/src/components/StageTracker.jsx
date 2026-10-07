import React from 'react';
import { Layers, CheckCircle2, Code2, Lock } from 'lucide-react';

const STAGES = [
  {
    stage: 1,
    name: 'Foundation',
    status: 'complete',
    desc: 'CSV/XLSX ingestion, data statistics, duplicate & anomaly profiling.',
    badge: 'COMPLETE'
  },
  {
    stage: 2,
    name: 'Core Proof-Carrying Analyst',
    status: 'complete',
    desc: 'Natural language queries, sandboxed code execution, proof receipts & refusal rules.',
    badge: 'COMPLETE'
  },
  {
    stage: 3,
    name: 'Data Forensics',
    status: 'complete',
    desc: 'Messy data inspection: currency/unit traps, date ambiguity, duplicates, contradictions & impact assessment.',
    badge: 'COMPLETE'
  },
  {
    stage: 4,
    name: 'ProofGuard Trust Layer',
    status: 'active',
    desc: 'Answer Guardian, adversarial challenges, Trust Score (0-100), proof lineage & Verifier Decides pipeline.',
    badge: 'IN PROGRESS'
  },
  {
    stage: 5,
    name: 'Adversarial Testing & Demo',
    status: 'locked',
    desc: 'Stress testing, adversarial evaluation, and production verification certification.',
    badge: 'LOCKED'
  }
];

export default function StageTracker() {
  return (
    <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-4 sm:p-5 backdrop-blur-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 mb-4 border-b border-slate-800/70 gap-2">
        <div className="flex items-center space-x-2.5">
          <Layers className="w-5 h-5 text-indigo-400" />
          <h2 className="text-sm font-semibold text-slate-200">
            ProofGuard 5-Stage Architecture Roadmap
          </h2>
        </div>
        <div className="flex items-center space-x-2">
          <span className="inline-block w-2 h-2 rounded-full bg-emerald-400" />
          <span className="text-xs text-slate-300 font-medium">Stages 1, 2 & 3 Complete</span>
          <span className="text-slate-600">•</span>
          <span className="inline-block w-2 h-2 rounded-full bg-indigo-500 animate-ping" />
          <span className="text-xs text-indigo-300 font-medium">Stage 4 Active (Trust Layer)</span>
        </div>
      </div>


      <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
        {STAGES.map((s) => {
          const isComplete = s.status === 'complete';
          const isActive = s.status === 'active';
          const isLocked = s.status === 'locked';

          return (
            <div
              key={s.stage}
              className={`relative rounded-xl p-3.5 transition-all border ${
                isActive
                  ? 'bg-gradient-to-b from-indigo-950/60 to-slate-900/90 border-indigo-500/60 shadow-lg shadow-indigo-950/50 ring-1 ring-indigo-500/30'
                  : isComplete
                  ? 'bg-slate-900/60 border-emerald-500/40'
                  : 'bg-slate-950/30 border-slate-800/40 opacity-50'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                  isActive 
                    ? 'bg-indigo-500 text-white shadow-sm shadow-indigo-500/50' 
                    : isComplete
                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                    : 'bg-slate-800 text-slate-400'
                }`}>
                  STAGE {s.stage}
                </span>
                <span className={`text-[10px] font-semibold tracking-wide ${
                  isActive 
                    ? 'text-indigo-300 animate-pulse' 
                    : isComplete 
                    ? 'text-emerald-400' 
                    : 'text-slate-500'
                }`}>
                  {s.badge}
                </span>
              </div>

              <div className="flex items-center space-x-2 mb-1.5">
                {isComplete && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
                {isActive && <Code2 className="w-4 h-4 text-indigo-400" />}
                {isLocked && <Lock className="w-3.5 h-3.5 text-slate-500" />}
                <h3 className={`text-xs font-semibold ${
                  isActive ? 'text-white' : isComplete ? 'text-slate-200' : 'text-slate-400'
                }`}>
                  {s.name}
                </h3>
              </div>

              <p className="text-[11px] text-slate-400 leading-relaxed">
                {s.desc}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
