import React, { useState, useEffect } from 'react';
import { 
  ShieldAlert, 
  Search, 
  AlertTriangle, 
  CheckCircle2, 
  HelpCircle, 
  Coins, 
  Ruler, 
  Calendar, 
  Copy, 
  FileSearch, 
  GitCompare, 
  Flame, 
  ArrowRight,
  Filter,
  RefreshCw,
  Info,
  ChevronDown,
  ChevronRight,
  Sparkles
} from 'lucide-react';
import { getDatasetForensics, assessQuestionForensics } from '../services/api';

export default function DataForensics({ activeDataset, onNavigateToAnalyst }) {
  const [forensicReport, setForensicReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedSeverity, setSelectedSeverity] = useState('ALL');
  const [selectedCategory, setSelectedCategory] = useState('ALL');
  const [expandedFindingId, setExpandedFindingId] = useState(null);

  // Quick Pre-Flight Check state
  const [testQuestion, setTestQuestion] = useState('');
  const [gateLoading, setGateLoading] = useState(false);
  const [gateResult, setGateResult] = useState(null);

  useEffect(() => {
    if (activeDataset?.id) {
      loadForensics(activeDataset.id);
    }
  }, [activeDataset?.id]);

  const loadForensics = async (datasetId) => {
    try {
      setLoading(true);
      setError('');
      setGateResult(null);
      const data = await getDatasetForensics(datasetId);
      setForensicReport(data);
    } catch (err) {
      console.error('Failed to load forensics:', err);
      setError(err.message || 'Failed to inspect dataset forensics.');
    } finally {
      setLoading(false);
    }
  };

  const handleRunGateTest = async (e) => {
    if (e) e.preventDefault();
    const q = testQuestion.trim();
    if (!q || !activeDataset?.id) return;

    setGateLoading(true);
    try {
      const res = await assessQuestionForensics(q, activeDataset.id);
      setGateResult(res);
    } catch (err) {
      console.error('Gate check failed:', err);
    } finally {
      setGateLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    const s = (status || '').toUpperCase();
    if (s === 'CLEAN') {
      return {
        bg: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400',
        icon: <CheckCircle2 className="w-4 h-4 text-emerald-400" />,
        text: 'CLEAN'
      };
    }
    if (s.includes('UNSAFE')) {
      return {
        bg: 'bg-rose-500/15 border-rose-500/40 text-rose-400 shadow-sm shadow-rose-950/40',
        icon: <AlertTriangle className="w-4 h-4 text-rose-400" />,
        text: 'UNSAFE FOR REQUESTED ANALYSIS'
      };
    }
    if (s.includes('CANNOT')) {
      return {
        bg: 'bg-purple-500/15 border-purple-500/40 text-purple-400',
        icon: <HelpCircle className="w-4 h-4 text-purple-400" />,
        text: 'CANNOT DETERMINE'
      };
    }
    return {
      bg: 'bg-amber-500/15 border-amber-500/40 text-amber-300 shadow-sm shadow-amber-950/40',
      icon: <ShieldAlert className="w-4 h-4 text-amber-400" />,
      text: 'NEEDS REVIEW'
    };
  };

  const getSeverityStyle = (severity) => {
    switch (severity?.toUpperCase()) {
      case 'CRITICAL':
        return 'bg-rose-500/20 text-rose-300 border-rose-500/40';
      case 'HIGH':
        return 'bg-orange-500/20 text-orange-300 border-orange-500/40';
      case 'MEDIUM':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/40';
      case 'LOW':
        return 'bg-sky-500/20 text-sky-300 border-sky-500/40';
      default:
        return 'bg-slate-700/30 text-slate-300 border-slate-600/40';
    }
  };

  const findings = forensicReport?.findings || [];
  const counts = forensicReport?.summary_counts || {};

  const filteredFindings = findings.filter(f => {
    if (selectedSeverity !== 'ALL' && f.severity.toUpperCase() !== selectedSeverity) {
      return false;
    }
    if (selectedCategory !== 'ALL' && f.category !== selectedCategory) {
      return false;
    }
    return true;
  });

  const statusBadge = getStatusBadge(forensicReport?.overall_status);

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Top Stage 3 Banner */}
      <div className="bg-gradient-to-r from-amber-950/40 via-slate-900/60 to-slate-900/40 border border-amber-500/30 rounded-2xl p-5 sm:p-6 backdrop-blur-md relative overflow-hidden">
        <div className="absolute right-0 top-0 w-96 h-96 bg-amber-500/5 rounded-full blur-3xl pointer-events-none" />
        
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 relative z-10">
          <div className="space-y-2">
            <div className="flex items-center space-x-2.5">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-500 text-slate-950 shadow-sm shadow-amber-500/30 uppercase tracking-wider">
                Stage 3 Engine
              </span>
              <span className="text-xs font-semibold text-amber-300">
                Data Forensics & Quality Impact Assessment
              </span>
            </div>
            <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight flex items-center space-x-3">
              <span>BEFORE TRUSTING AN ANSWER → FORENSICALLY INSPECT THE DATA</span>
            </h2>
            <p className="text-xs text-slate-300 max-w-3xl leading-relaxed">
              Messy real-world data contains silent traps: mixed currencies, ambiguous dates (DD/MM vs MM/DD), conflicting duplicated entities, and physically impossible outliers. ProofGuard inspects every dataset without altering or auto-cleaning the source records.
            </p>
          </div>

          {/* Overall Forensic Status Pill */}
          <div className="flex flex-col items-start lg:items-end space-y-1.5 flex-shrink-0">
            <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400">
              Overall Forensic Status
            </span>
            <div className={`flex items-center space-x-2 px-3.5 py-2 rounded-xl border text-xs font-bold ${statusBadge.bg}`}>
              {statusBadge.icon}
              <span>{statusBadge.text}</span>
            </div>
          </div>
        </div>

        {/* Forensic Recommendation Banner */}
        {forensicReport?.recommendation && (
          <div className="mt-4 pt-3.5 border-t border-slate-800/80 flex items-start space-x-2.5 text-xs text-amber-200/90 bg-amber-950/20 rounded-xl p-3 border border-amber-500/20">
            <Info className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
            <div className="leading-relaxed">
              <span className="font-semibold text-amber-300">Forensic Recommendation: </span>
              {forensicReport.recommendation}
            </div>
          </div>
        )}
      </div>

      {/* Summary KPI Cards Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {/* Missing Data */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-3.5 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Missing Data</span>
            <HelpCircle className="w-3.5 h-3.5 text-slate-500" />
          </div>
          <div className="text-lg font-bold text-white">
            {counts.missing_percentage || 0}%
          </div>
          <div className="text-[11px] text-slate-400">
            {counts.missing_cells || 0} empty / masked
          </div>
        </div>

        {/* Duplicates */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-3.5 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Duplicates</span>
            <Copy className="w-3.5 h-3.5 text-orange-400" />
          </div>
          <div className="text-lg font-bold text-white">
            {counts.duplicates_count || 0}
          </div>
          <div className="text-[11px] text-slate-400">
            Exact & identifier
          </div>
        </div>

        {/* Date Issues */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-3.5 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Date Traps</span>
            <Calendar className="w-3.5 h-3.5 text-amber-400" />
          </div>
          <div className="text-lg font-bold text-white">
            {counts.date_issues_count || 0}
          </div>
          <div className="text-[11px] text-slate-400">
            DD/MM Ambiguity
          </div>
        </div>

        {/* Currency Mismatch */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-3.5 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Currencies</span>
            <Coins className="w-3.5 h-3.5 text-emerald-400" />
          </div>
          <div className="text-lg font-bold text-white">
            {counts.currency_issues_count || 0}
          </div>
          <div className="text-[11px] text-slate-400">
            Mixed codes/symbols
          </div>
        </div>

        {/* Unit Mismatch */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-3.5 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Unit Issues</span>
            <Ruler className="w-3.5 h-3.5 text-sky-400" />
          </div>
          <div className="text-lg font-bold text-white">
            {counts.unit_issues_count || 0}
          </div>
          <div className="text-[11px] text-slate-400">
            kg, lbs, g conflicts
          </div>
        </div>

        {/* Contradictions & Outliers */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-3.5 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Contradictions</span>
            <GitCompare className="w-3.5 h-3.5 text-rose-400" />
          </div>
          <div className="text-lg font-bold text-white">
            {(counts.contradictions_count || 0) + (counts.impossible_values_count || 0)}
          </div>
          <div className="text-[11px] text-slate-400">
            Conflicting records
          </div>
        </div>
      </div>

      {/* Forensic Pre-Flight Check Card */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 backdrop-blur-md space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <FileSearch className="w-4 h-4 text-indigo-400" />
            <h3 className="text-sm font-semibold text-white">
              Forensic Pre-Execution Check (Analysis Impact Gate)
            </h3>
          </div>
          <span className="text-[11px] text-slate-400">
            Tests whether a specific query is safe before code generation
          </span>
        </div>

        <form onSubmit={handleRunGateTest} className="flex gap-2">
          <input
            type="text"
            value={testQuestion}
            onChange={(e) => setTestQuestion(e.target.value)}
            placeholder="e.g. 'What is the total revenue?' or 'How many orders are there?'"
            className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-mono"
          />
          <button
            type="submit"
            disabled={gateLoading || !testQuestion.trim()}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-colors flex-shrink-0"
          >
            {gateLoading ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <ShieldAlert className="w-3.5 h-3.5" />
            )}
            <span>Inspect Safety</span>
          </button>
        </form>

        {/* Gate Inspection Result Display */}
        {gateResult && (
          <div className={`p-4 rounded-xl border text-xs space-y-2.5 animate-in fade-in duration-150 ${
            gateResult.safe_to_analyze
              ? 'bg-emerald-950/20 border-emerald-500/40 text-emerald-300'
              : 'bg-rose-950/25 border-rose-500/40 text-rose-300'
          }`}>
            <div className="flex items-center justify-between font-semibold">
              <div className="flex items-center space-x-2">
                {gateResult.safe_to_analyze ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-rose-400" />
                )}
                <span>
                  {gateResult.safe_to_analyze 
                    ? 'SAFE TO ANALYZE — Passed Forensic Gate' 
                    : 'BLOCKED BY DATA FORENSICS — Unsafe For Requested Analysis'}
                </span>
              </div>
              <span className="font-mono text-[11px] uppercase tracking-wider px-2 py-0.5 rounded bg-slate-900 border border-slate-800">
                Status: {gateResult.status}
              </span>
            </div>

            <div className="text-slate-300 leading-relaxed">
              <span className="font-semibold text-white">Forensic Reason: </span>
              {gateResult.reason}
            </div>

            {gateResult.affected_columns?.length > 0 && (
              <div className="flex items-center space-x-2 text-[11px]">
                <span className="text-slate-400">Affected Columns:</span>
                {gateResult.affected_columns.map(col => (
                  <span key={col} className="px-2 py-0.5 bg-slate-900 border border-slate-800 rounded font-mono text-white">
                    {col}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Findings Section */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 backdrop-blur-md space-y-4">
        {/* Header & Filter Controls */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800">
          <div className="flex items-center space-x-2">
            <ShieldAlert className="w-4 h-4 text-amber-400" />
            <h3 className="text-sm font-semibold text-white">
              Forensic Findings Registry ({filteredFindings.length} of {findings.length})
            </h3>
          </div>

          {/* Severity Filter Pills */}
          <div className="flex items-center space-x-1 overflow-x-auto text-xs">
            {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map(sev => (
              <button
                key={sev}
                onClick={() => setSelectedSeverity(sev)}
                className={`px-2.5 py-1 rounded-lg border text-[11px] font-semibold transition-colors ${
                  selectedSeverity === sev
                    ? 'bg-indigo-600 text-white border-indigo-500 shadow-sm'
                    : 'bg-slate-950/60 text-slate-400 border-slate-800 hover:text-white'
                }`}
              >
                {sev}
              </button>
            ))}
          </div>
        </div>

        {/* Findings List */}
        {loading ? (
          <div className="p-12 text-center text-slate-400">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-indigo-400" />
            <p className="text-xs">Inspecting dataset for forensic traps and contradictions...</p>
          </div>
        ) : filteredFindings.length === 0 ? (
          <div className="p-8 text-center text-slate-400 text-xs bg-slate-950/40 rounded-xl border border-slate-800">
            No forensic findings match the selected filter.
          </div>
        ) : (
          <div className="space-y-3">
            {filteredFindings.map((finding) => {
              const isExpanded = expandedFindingId === finding.id;
              const sevStyle = getSeverityStyle(finding.severity);

              return (
                <div 
                  key={finding.id}
                  className="bg-slate-950/60 border border-slate-800 rounded-xl p-4 transition-all hover:border-slate-700/80 space-y-3"
                >
                  {/* Finding Header */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-center space-x-2.5">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold border uppercase tracking-wider ${sevStyle}`}>
                        {finding.severity}
                      </span>
                      <span className="text-xs font-semibold text-slate-200">
                        {finding.category.replace(/_/g, ' ').toUpperCase()}
                      </span>
                      {finding.column && (
                        <span className="px-2 py-0.5 bg-slate-900 border border-slate-800 text-[11px] font-mono text-indigo-300 rounded">
                          col: {finding.column}
                        </span>
                      )}
                    </div>

                    <div className="flex items-center space-x-3 text-[11px] text-slate-400">
                      <span>Affected: <strong className="text-white">{finding.affected_count}</strong> records ({finding.affected_percentage}%)</span>
                      <button
                        onClick={() => setExpandedFindingId(isExpanded ? null : finding.id)}
                        className="p-1 rounded bg-slate-900 border border-slate-800 hover:text-white transition-colors"
                      >
                        {isExpanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                      </button>
                    </div>
                  </div>

                  {/* Message */}
                  <div className="text-xs text-slate-300 font-medium leading-relaxed">
                    {finding.message}
                  </div>

                  {/* Expanded Detail Panel */}
                  {isExpanded && (
                    <div className="pt-3 border-t border-slate-800/80 space-y-2.5 text-xs animate-in fade-in duration-150">
                      {/* Examples */}
                      {finding.examples?.length > 0 && (
                        <div className="bg-slate-900/80 rounded-lg p-2.5 border border-slate-800/60">
                          <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400 block mb-1">
                            Example Corrupted / Mismatched Values:
                          </span>
                          <div className="flex flex-wrap gap-1.5 font-mono text-[11px]">
                            {finding.examples.map((ex, i) => (
                              <span key={i} className="px-2 py-0.5 bg-slate-950 border border-slate-800 rounded text-amber-300">
                                {typeof ex === 'object' ? JSON.stringify(ex) : String(ex)}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Impact */}
                      <div className="p-2.5 rounded-lg bg-rose-950/20 border border-rose-500/20 text-rose-300">
                        <strong className="text-rose-400">Analysis Impact: </strong>
                        {finding.impact}
                      </div>

                      {/* Recommendation */}
                      <div className="p-2.5 rounded-lg bg-indigo-950/20 border border-indigo-500/20 text-indigo-300">
                        <strong className="text-indigo-400">Recommendation: </strong>
                        {finding.recommendation}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
