import React from 'react';
import { 
  Database, 
  Columns3, 
  Copy, 
  AlertTriangle, 
  HardDrive, 
  ShieldCheck, 
  ShieldAlert, 
  CheckCircle2, 
  HelpCircle,
  TrendingUp
} from 'lucide-react';

export default function DatasetStatsOverview({ meta, health, columns }) {
  if (!meta || !health) return null;

  const score = health.health_score;
  const isHealthy = score >= 80;
  const isModerate = score >= 50 && score < 80;

  const getScoreColor = () => {
    if (isHealthy) return 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10';
    if (isModerate) return 'text-amber-400 border-amber-500/30 bg-amber-500/10';
    return 'text-rose-400 border-rose-500/30 bg-rose-500/10';
  };

  const formatBytes = (bytes) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
  };

  return (
    <div className="space-y-4">
      {/* Top Banner: ProofGuard Health Score & Readiness Assessment */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur-md relative overflow-hidden">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          
          {/* Health Score Gauge */}
          <div className="flex items-center space-x-5">
            <div className={`w-20 h-20 rounded-2xl border flex flex-col items-center justify-center font-mono ${getScoreColor()}`}>
              <span className="text-3xl font-extrabold tracking-tight">{score}</span>
              <span className="text-[10px] uppercase font-semibold tracking-wider">/ 100</span>
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-base font-bold text-white">
                  ProofGuard Data Trust Score
                </h3>
                {isHealthy ? (
                  <span className="flex items-center space-x-1 text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
                    <ShieldCheck className="w-3.5 h-3.5" />
                    <span>Low Risk</span>
                  </span>
                ) : (
                  <span className="flex items-center space-x-1 text-xs px-2 py-0.5 rounded-full bg-rose-500/10 border border-rose-500/30 text-rose-400">
                    <ShieldAlert className="w-3.5 h-3.5" />
                    <span>Unreliable Signals Detected</span>
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400 mt-1 max-w-xl leading-relaxed">
                {isHealthy
                  ? 'Data structure passes primary consistency checks. Ready for Stage 2 query execution.'
                  : 'Standard LLMs will hallucinate or miscalculate on this data due to duplicate records, mixed currencies, or ambiguous formats.'}
              </p>
            </div>
          </div>

          {/* Quick Readiness Notice */}
          <div className="lg:max-w-md bg-slate-950/60 border border-slate-800 rounded-xl p-3.5 text-xs">
            <div className="flex items-center space-x-2 text-indigo-400 font-medium mb-1.5">
              <ShieldCheck className="w-4 h-4" />
              <span>Independent Verification Rule:</span>
            </div>
            <p className="text-slate-300 italic">
              "Never invent a number. If ambiguous units or duplicates distort ground truth, answer:
              <strong className="text-amber-300 not-italic block mt-1 font-mono text-[11px] bg-slate-900 px-2 py-1 rounded border border-slate-800">
                “Cannot determine reliably from the available data.”
              </strong>
            </p>
          </div>

        </div>

        {/* Readiness Bullet Points */}
        {health.readiness_notes && health.readiness_notes.length > 0 && (
          <div className="mt-4 pt-4 border-t border-slate-800/80 flex flex-wrap gap-2">
            {health.readiness_notes.map((note, idx) => (
              <div
                key={idx}
                className="text-xs px-3 py-1.5 rounded-lg bg-indigo-950/30 border border-indigo-800/30 text-indigo-200 flex items-center space-x-2"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 flex-shrink-0" />
                <span>{note}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {/* Total Rows */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 backdrop-blur-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">Total Rows</span>
            <Database className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-xl font-bold text-white font-mono">
            {meta.row_count.toLocaleString()}
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Parsed records</p>
        </div>

        {/* Total Columns */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 backdrop-blur-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">Columns</span>
            <Columns3 className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-xl font-bold text-white font-mono">
            {meta.column_count}
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Attribute fields</p>
        </div>

        {/* Duplicates */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 backdrop-blur-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">Duplicate Rows</span>
            <Copy className={`w-4 h-4 ${health.duplicate_rows > 0 ? 'text-rose-400' : 'text-slate-500'}`} />
          </div>
          <div className="flex items-baseline space-x-2">
            <span className={`text-xl font-bold font-mono ${health.duplicate_rows > 0 ? 'text-rose-400' : 'text-white'}`}>
              {health.duplicate_rows}
            </span>
            <span className={`text-xs px-1.5 py-0.5 rounded font-mono ${
              health.duplicate_rows > 0 ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' : 'text-slate-500'
            }`}>
              {health.duplicate_percentage}%
            </span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1">
            {health.duplicate_rows > 0 ? 'Requires deduplication' : 'No duplicates'}
          </p>
        </div>

        {/* Missing Values */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 backdrop-blur-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">Missing Cells</span>
            <AlertTriangle className={`w-4 h-4 ${health.total_missing_cells > 0 ? 'text-amber-400' : 'text-slate-500'}`} />
          </div>
          <div className="flex items-baseline space-x-2">
            <span className={`text-xl font-bold font-mono ${health.total_missing_cells > 0 ? 'text-amber-400' : 'text-white'}`}>
              {health.total_missing_cells}
            </span>
            <span className={`text-xs px-1.5 py-0.5 rounded font-mono ${
              health.total_missing_cells > 0 ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' : 'text-slate-500'
            }`}>
              {health.missing_cells_percentage}%
            </span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Null / empty values</p>
        </div>

        {/* Memory Footprint */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 backdrop-blur-sm col-span-2 md:col-span-1">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">Memory</span>
            <HardDrive className="w-4 h-4 text-violet-400" />
          </div>
          <div className="text-xl font-bold text-white font-mono">
            {formatBytes(meta.size_bytes)}
          </div>
          <p className="text-[11px] text-slate-500 mt-1">In-memory footprint</p>
        </div>
      </div>
    </div>
  );
}
