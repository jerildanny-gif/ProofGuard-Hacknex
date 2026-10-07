import React, { useState } from 'react';
import { 
  Columns3, 
  Search, 
  Hash, 
  Calendar, 
  Tag, 
  Type, 
  CheckCircle, 
  AlertCircle, 
  BarChart2, 
  ChevronDown, 
  ChevronUp,
  Info
} from 'lucide-react';

const TYPE_ICONS = {
  numeric: Hash,
  datetime: Calendar,
  categorical: Tag,
  boolean: CheckCircle,
  text: Type
};

const TYPE_BADGES = {
  numeric: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
  datetime: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30',
  categorical: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30',
  boolean: 'bg-purple-500/10 text-purple-400 border-purple-500/30',
  text: 'bg-slate-500/10 text-slate-400 border-slate-500/30'
};

export default function ColumnInspector({ columns }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedCol, setExpandedCol] = useState(null);

  if (!columns || columns.length === 0) return null;

  const filteredColumns = columns.filter(col => 
    col.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    col.inferred_type.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const toggleExpand = (name) => {
    setExpandedCol(expandedCol === name ? null : name);
  };

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur-md">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 mb-4 border-b border-slate-800/80 gap-3">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
            <Columns3 className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">Column Profiles & Statistical Inference</h3>
            <p className="text-xs text-slate-400">Inspect data types, distributions, and detected anomalies per column</p>
          </div>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search columns or types..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="bg-slate-950/80 border border-slate-800 rounded-xl pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/30 w-full sm:w-64"
          />
        </div>
      </div>

      <div className="space-y-2.5 max-h-[600px] overflow-y-auto pr-1">
        {filteredColumns.map((col) => {
          const Icon = TYPE_ICONS[col.inferred_type] || Type;
          const badgeClass = TYPE_BADGES[col.inferred_type] || TYPE_BADGES.text;
          const isExpanded = expandedCol === col.name;
          const hasAnomalies = col.anomalies && col.anomalies.length > 0;

          return (
            <div
              key={col.name}
              className={`rounded-xl border transition-all ${
                isExpanded
                  ? 'bg-slate-950/90 border-indigo-500/40 shadow-lg shadow-indigo-950/20'
                  : 'bg-slate-950/40 border-slate-800/70 hover:border-slate-700/80'
              }`}
            >
              {/* Header Row */}
              <div
                onClick={() => toggleExpand(col.name)}
                className="p-3.5 flex items-center justify-between cursor-pointer select-none"
              >
                <div className="flex items-center space-x-3">
                  <div className="w-7 h-7 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-300">
                    <Icon className="w-3.5 h-3.5" />
                  </div>
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-bold text-white font-mono">{col.name}</span>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full border uppercase tracking-wider font-semibold ${badgeClass}`}>
                        {col.inferred_type}
                      </span>
                      {hasAnomalies && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/30 flex items-center space-x-1">
                          <AlertCircle className="w-3 h-3" />
                          <span>{col.anomalies.length} trap{col.anomalies.length > 1 ? 's' : ''}</span>
                        </span>
                      )}
                    </div>
                    <div className="flex items-center space-x-3 text-[11px] text-slate-400 mt-1">
                      <span>Dtype: <code className="text-slate-300">{col.dtype}</code></span>
                      <span>•</span>
                      <span>Unique: <strong className="text-slate-200">{col.unique_count}</strong></span>
                      <span>•</span>
                      <span>Null: <strong className={col.null_count > 0 ? 'text-amber-400' : 'text-slate-400'}>
                        {col.null_count} ({col.null_percentage}%)
                      </strong></span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  {/* Null progress bar */}
                  <div className="hidden md:flex flex-col items-end w-24">
                    <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${col.null_percentage > 20 ? 'bg-rose-500' : col.null_percentage > 0 ? 'bg-amber-500' : 'bg-emerald-500'}`}
                        style={{ width: `${100 - col.null_percentage}%` }}
                      />
                    </div>
                    <span className="text-[10px] text-slate-500 mt-0.5">{(100 - col.null_percentage).toFixed(0)}% valid</span>
                  </div>

                  <button className="text-slate-400 hover:text-white p-1">
                    {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* Expanded details */}
              {isExpanded && (
                <div className="px-4 pb-4 pt-2 border-t border-slate-800/80 bg-slate-900/30 space-y-3">
                  {/* Anomalies alert banner */}
                  {hasAnomalies && (
                    <div className="p-2.5 rounded-lg bg-rose-950/30 border border-rose-500/30 text-xs text-rose-300 space-y-1">
                      <div className="font-semibold flex items-center space-x-1.5 text-rose-400">
                        <AlertCircle className="w-3.5 h-3.5" />
                        <span>Detected Data Trap for Stage 1:</span>
                      </div>
                      {col.anomalies.map((anom, idx) => (
                        <p key={idx} className="pl-5 text-rose-200">• {anom}</p>
                      ))}
                    </div>
                  )}

                  {/* Numeric Stats */}
                  {col.stats && col.inferred_type === 'numeric' && (
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1">
                      <div className="p-2 rounded-lg bg-slate-900/80 border border-slate-800">
                        <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Mean / Std</span>
                        <span className="text-xs font-mono font-medium text-slate-200">
                          {col.stats.mean ?? 'N/A'} <span className="text-slate-500 text-[10px]">±{col.stats.std ?? '0'}</span>
                        </span>
                      </div>
                      <div className="p-2 rounded-lg bg-slate-900/80 border border-slate-800">
                        <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Min</span>
                        <span className="text-xs font-mono font-medium text-slate-200">{col.stats.min ?? 'N/A'}</span>
                      </div>
                      <div className="p-2 rounded-lg bg-slate-900/80 border border-slate-800">
                        <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Median (Q50)</span>
                        <span className="text-xs font-mono font-medium text-indigo-300">{col.stats.median ?? 'N/A'}</span>
                      </div>
                      <div className="p-2 rounded-lg bg-slate-900/80 border border-slate-800">
                        <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Max</span>
                        <span className="text-xs font-mono font-medium text-slate-200">{col.stats.max ?? 'N/A'}</span>
                      </div>
                    </div>
                  )}

                  {/* Categorical Top Values */}
                  {col.stats?.top_values && (
                    <div>
                      <span className="text-[10px] text-slate-400 uppercase tracking-wider block mb-1.5 font-semibold">
                        Frequent Values Distribution
                      </span>
                      <div className="space-y-1.5">
                        {col.stats.top_values.map((item, idx) => (
                          <div key={idx} className="flex items-center space-x-2 text-xs">
                            <span className="w-28 truncate text-slate-300 font-mono text-[11px]">{item.value}</span>
                            <div className="flex-1 bg-slate-800 h-2 rounded-full overflow-hidden">
                              <div
                                className="bg-indigo-500 h-full rounded-full"
                                style={{ width: `${item.percentage}%` }}
                              />
                            </div>
                            <span className="text-[11px] font-mono text-slate-400 w-16 text-right">
                              {item.count} ({item.percentage}%)
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Sample values preview */}
                  <div>
                    <span className="text-[10px] text-slate-400 uppercase tracking-wider block mb-1 font-semibold">
                      Sample Values
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {col.sample_values?.map((val, idx) => (
                        <span
                          key={idx}
                          className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-300"
                        >
                          {val === null || val === undefined ? <em className="text-amber-500">null</em> : String(val)}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}

        {filteredColumns.length === 0 && (
          <div className="text-center py-8 text-xs text-slate-500">
            No columns match "{searchTerm}"
          </div>
        )}
      </div>
    </div>
  );
}
