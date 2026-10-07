import React from 'react';
import { Sparkles, DollarSign, Calendar, HeartPulse, Boxes, ChevronRight, AlertTriangle } from 'lucide-react';

const ICONS_MAP = {
  'sample-sales': DollarSign,
  'sample-employees': Calendar,
  'sample-clinical': HeartPulse,
  'sample-inventory': Boxes
};

export default function SampleDatasetPicker({ samples, activeId, onSelectSample }) {
  if (!samples || samples.length === 0) return null;

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur-md">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">Curated Messy Datasets</h3>
            <p className="text-xs text-slate-400">Benchmark ProofGuard against known real-world data traps</p>
          </div>
        </div>
        <span className="text-[11px] text-amber-400 font-medium bg-amber-500/10 px-2 py-0.5 rounded-full border border-amber-500/20">
          4 Presets Ready
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {samples.map((sample) => {
          const isSelected = activeId === sample.id;
          const Icon = ICONS_MAP[sample.id] || Sparkles;

          return (
            <button
              key={sample.id}
              onClick={() => onSelectSample(sample.id)}
              className={`text-left p-3.5 rounded-xl border transition-all flex flex-col justify-between group ${
                isSelected
                  ? 'bg-indigo-950/50 border-indigo-500 ring-1 ring-indigo-500/30 shadow-md shadow-indigo-950/50'
                  : 'bg-slate-950/40 border-slate-800/80 hover:border-slate-700 hover:bg-slate-900/50'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <div className={`w-7 h-7 rounded-lg flex items-center justify-center ${
                      isSelected ? 'bg-indigo-500 text-white' : 'bg-slate-800 text-slate-400 group-hover:text-slate-200'
                    }`}>
                      <Icon className="w-4 h-4" />
                    </div>
                    <span className="text-xs font-semibold text-white group-hover:text-indigo-300 transition-colors">
                      {sample.title}
                    </span>
                  </div>
                  <ChevronRight className={`w-3.5 h-3.5 transition-transform ${
                    isSelected ? 'text-indigo-400 translate-x-0.5' : 'text-slate-600 group-hover:text-slate-400'
                  }`} />
                </div>

                <p className="text-[11px] text-slate-400 leading-relaxed mb-3">
                  {sample.description}
                </p>
              </div>

              <div className="flex flex-wrap gap-1.5 pt-2 border-t border-slate-800/60">
                {sample.tags.map((tag) => (
                  <span
                    key={tag}
                    className="text-[10px] px-2 py-0.5 rounded-md bg-slate-800/80 text-slate-300 border border-slate-700/50"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
