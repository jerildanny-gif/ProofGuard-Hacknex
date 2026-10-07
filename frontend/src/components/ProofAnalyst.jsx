import React, { useState, useEffect } from 'react';
import { 
  Sparkles, 
  Send, 
  CheckCircle2, 
  AlertTriangle, 
  Code2, 
  Copy, 
  Check, 
  Clock, 
  Database, 
  Columns3, 
  ShieldAlert, 
  Terminal, 
  Cpu, 
  HelpCircle,
  Flame,
  ArrowRight,
  Shield,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { analyzeQuestion, getAnalysisSuggestions } from '../services/api';
import AnswerGuardian from './AnswerGuardian';

export default function ProofAnalyst({ activeDataset, datasets = [] }) {
  const [question, setQuestion] = useState('');
  const [selectedDatasetId, setSelectedDatasetId] = useState(activeDataset?.id || '');
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState('');
  const [analysisResult, setAnalysisResult] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const [suggestionFilter, setSuggestionFilter] = useState('all'); // 'all', 'valid', 'trap'
  const [copiedCode, setCopiedCode] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [showGuardian, setShowGuardian] = useState(false);

  // Keep selected dataset synced with activeDataset prop
  useEffect(() => {
    if (activeDataset?.id) {
      setSelectedDatasetId(activeDataset.id);
    }
  }, [activeDataset]);

  // Load suggested demo questions
  useEffect(() => {
    loadSuggestions(selectedDatasetId);
  }, [selectedDatasetId]);

  const loadSuggestions = async (dsId) => {
    try {
      const data = await getAnalysisSuggestions(dsId);
      setSuggestions(data);
    } catch (err) {
      console.error('Failed to load suggestions:', err);
    }
  };

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    const query = question.trim();
    if (!query) return;

    setLoading(true);
    setErrorMsg('');
    setAnalysisResult(null);

    // Simulate animated execution pipeline phases for clear transparency
    setLoadingStep('Inspecting schema & Stage 1 anomaly profiles...');
    const stepTimer1 = setTimeout(() => {
      setLoadingStep('Synthesizing verifiable Python/Pandas logic...');
    }, 250);
    const stepTimer2 = setTimeout(() => {
      setLoadingStep('Executing in isolated local sandbox...');
    }, 500);

    try {
      const result = await analyzeQuestion(query, selectedDatasetId || null);
      clearTimeout(stepTimer1);
      clearTimeout(stepTimer2);
      setAnalysisResult(result);
      setShowGuardian(false); // reset guardian on new analysis
    } catch (err) {
      clearTimeout(stepTimer1);
      clearTimeout(stepTimer2);
      setErrorMsg(err.message || 'Analysis failed. Please check backend connection.');
    } finally {
      setLoading(false);
      setLoadingStep('');
    }
  };

  const handleSelectSuggestion = (s) => {
    setQuestion(s.question);
    if (s.dataset_id && s.dataset_id !== selectedDatasetId) {
      setSelectedDatasetId(s.dataset_id);
    }
  };

  const handleCopyCode = () => {
    if (!analysisResult?.generated_code) return;
    navigator.clipboard.writeText(analysisResult.generated_code);
    setCopiedCode(true);
    setTimeout(() => setCopiedCode(false), 2000);
  };

  const filteredSuggestions = suggestions.filter(s => {
    if (suggestionFilter === 'valid') return !s.is_trap;
    if (suggestionFilter === 'trap') return s.is_trap;
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Top Banner / Core Principle */}
      <div className="bg-gradient-to-r from-indigo-950/40 via-slate-900/50 to-slate-900/30 border border-indigo-500/30 rounded-2xl p-5 sm:p-6 backdrop-blur-md relative overflow-hidden">
        <div className="absolute right-0 top-0 w-96 h-96 bg-indigo-500/5 rounded-full blur-3xl pointer-events-none" />
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 relative z-10">
          <div className="space-y-1.5">
            <div className="flex items-center space-x-2">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-indigo-500 text-white shadow-sm shadow-indigo-500/40 tracking-wider uppercase">
                Stage 2 Engine
              </span>
              <span className="text-xs font-semibold text-indigo-300">
                Core Proof-Carrying Data Analyst
              </span>
            </div>
            <h2 className="text-xl font-bold text-white tracking-tight">
              Every numerical answer carries deterministic executable proof.
            </h2>
            <p className="text-xs text-slate-400 max-w-2xl leading-relaxed">
              No black-box hallucinated numbers. Questions are mapped to verifiable Python/Pandas operations, executed in an isolated sandbox against the real data, and validated against Stage 1 anomaly profiles.
            </p>
          </div>

          {/* Verification Pipeline Flow Badge */}
          <div className="flex items-center space-x-1.5 sm:space-x-2 text-[10px] sm:text-xs font-mono bg-slate-950/80 border border-slate-800 rounded-xl px-3 py-2 text-slate-300 self-start lg:self-auto shadow-inner">
            <span className="text-indigo-400 font-semibold">Propose</span>
            <ArrowRight className="w-3 h-3 text-slate-600" />
            <span className="text-amber-400 font-semibold">Execute</span>
            <ArrowRight className="w-3 h-3 text-slate-600" />
            <span className="text-emerald-400 font-semibold">Verify</span>
            <ArrowRight className="w-3 h-3 text-slate-600" />
            <span className="text-white font-semibold">Proof</span>
          </div>
        </div>
      </div>

      {/* Question Input Card */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 backdrop-blur-md space-y-4">
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
            <label className="text-slate-300 font-medium flex items-center space-x-2">
              <Sparkles className="w-4 h-4 text-indigo-400" />
              <span>Ask ProofGuard a Natural Language Question</span>
            </label>

            {/* Target Dataset Selector */}
            <div className="flex items-center space-x-2 text-xs">
              <span className="text-slate-400 text-[11px]">Target:</span>
              <select
                value={selectedDatasetId}
                onChange={(e) => setSelectedDatasetId(e.target.value)}
                className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1 text-xs text-white font-medium focus:outline-none focus:border-indigo-500 cursor-pointer"
              >
                {datasets.map(d => (
                  <option key={d.id} value={d.id}>
                    {d.name} ({d.row_count} rows)
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="relative">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="e.g. How many orders are there? Which product was ordered most? What is the total revenue?"
              disabled={loading}
              className="w-full bg-slate-950 border border-slate-800 focus:border-indigo-500 rounded-xl px-4 py-3.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500/50 pr-28 transition-all"
            />
            <button
              type="submit"
              disabled={loading || !question.trim()}
              className="absolute right-2 top-2 bottom-2 px-4 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-500 text-white rounded-lg text-xs font-semibold flex items-center space-x-2 transition-all shadow-md shadow-indigo-600/20 cursor-pointer disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Verifying...</span>
                </>
              ) : (
                <>
                  <span>Analyze</span>
                  <Send className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          </div>
        </form>

        {/* Loading Animated State */}
        {loading && (
          <div className="p-4 rounded-xl bg-indigo-950/20 border border-indigo-500/20 flex items-center space-x-3 text-xs text-indigo-300 animate-pulse">
            <Cpu className="w-4 h-4 text-indigo-400 animate-spin" />
            <span className="font-mono">{loadingStep || 'Executing analysis pipeline...'}</span>
          </div>
        )}

        {/* Suggested / Trap Questions Chips */}
        <div className="space-y-2 pt-2 border-t border-slate-800/60">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-[11px] text-slate-400 font-medium">
              <HelpCircle className="w-3.5 h-3.5 text-slate-500" />
              <span>Suggested Demo & Trap Questions:</span>
            </div>
            
            {/* Filter buttons */}
            <div className="flex items-center space-x-1">
              <button
                type="button"
                onClick={() => setSuggestionFilter('all')}
                className={`px-2 py-0.5 rounded text-[10px] font-medium transition-colors ${
                  suggestionFilter === 'all'
                    ? 'bg-slate-800 text-white font-semibold'
                    : 'text-slate-500 hover:text-slate-300'
                }`}
              >
                All
              </button>
              <button
                type="button"
                onClick={() => setSuggestionFilter('valid')}
                className={`px-2 py-0.5 rounded text-[10px] font-medium transition-colors ${
                  suggestionFilter === 'valid'
                    ? 'bg-emerald-500/20 text-emerald-300 font-semibold border border-emerald-500/30'
                    : 'text-slate-500 hover:text-slate-300'
                }`}
              >
                Valid Queries
              </button>
              <button
                type="button"
                onClick={() => setSuggestionFilter('trap')}
                className={`px-2 py-0.5 rounded text-[10px] font-medium transition-colors ${
                  suggestionFilter === 'trap'
                    ? 'bg-rose-500/20 text-rose-300 font-semibold border border-rose-500/30'
                    : 'text-slate-500 hover:text-slate-300'
                }`}
              >
                ⚠️ Trap & Refusal Tests
              </button>
            </div>
          </div>

          <div className="flex flex-wrap gap-1.5 max-h-36 overflow-y-auto pr-1">
            {filteredSuggestions.map((s) => (
              <button
                key={s.id}
                type="button"
                onClick={() => handleSelectSuggestion(s)}
                title={s.description}
                className={`text-left text-[11px] px-2.5 py-1.5 rounded-lg border transition-all flex items-center space-x-1.5 cursor-pointer ${
                  s.is_trap
                    ? 'bg-rose-950/20 border-rose-800/40 text-rose-300 hover:bg-rose-900/30 hover:border-rose-600/50'
                    : 'bg-slate-950/50 border-slate-800 text-slate-300 hover:bg-slate-900 hover:text-white hover:border-slate-700'
                }`}
              >
                {s.is_trap && <Flame className="w-3 h-3 text-rose-400 flex-shrink-0" />}
                <span>{s.question}</span>
                <span className={`text-[9px] px-1 py-0.2 rounded font-mono ${
                  s.is_trap ? 'bg-rose-500/20 text-rose-400' : 'bg-slate-800 text-slate-400'
                }`}>
                  {s.category}
                </span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Error Banner */}
      {errorMsg && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800/60 text-xs text-rose-300 flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 text-rose-400 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Analysis Result Card */}
      {analysisResult && (
        <div className="space-y-4 animate-in fade-in duration-300">
          {/* VERIFIED BY EXECUTION RESULT CARD */}
          {analysisResult.status === 'verified' && (
            <div className="bg-slate-900/80 border border-emerald-500/40 rounded-2xl overflow-hidden shadow-xl shadow-emerald-950/20">
              {/* Header Status Bar */}
              <div className="bg-emerald-950/30 border-b border-emerald-500/20 px-5 py-3.5 flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center space-x-2">
                  <div className="p-1 rounded-full bg-emerald-500/20 text-emerald-400">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  </div>
                  <div>
                    <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider">
                      STATUS: VERIFIED BY EXECUTION
                    </span>
                    <p className="text-[10px] text-slate-400">
                      Answer strictly derived from deterministic Python execution against actual data.
                    </p>
                  </div>
                </div>

                <div className="flex items-center space-x-3 text-xs font-mono text-slate-400">
                  {analysisResult.execution_time_ms !== null && (
                    <span className="flex items-center space-x-1 text-slate-400">
                      <Clock className="w-3.5 h-3.5 text-slate-500" />
                      <span>{analysisResult.execution_time_ms} ms</span>
                    </span>
                  )}
                  <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 text-[10px] font-bold">
                    REPRODUCIBLE 100%
                  </span>
                </div>
              </div>

              {/* Body */}
              <div className="p-5 sm:p-6 space-y-6">
                {/* Stage 3 Forensic Gate Success Banner */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between p-3.5 rounded-xl bg-slate-950/80 border border-emerald-500/30 text-xs gap-2">
                  <div className="flex items-center space-x-2 text-emerald-400 font-semibold">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                    <span>Stage 3 Forensic Pre-Inspection: PASSED</span>
                  </div>
                  <span className="text-[11px] text-slate-400 font-mono">
                    Data safe for requested operations • No corrupting columns queried
                  </span>
                </div>

                {/* Final Human Answer Display */}
                <div className="space-y-1">
                  <span className="text-[10px] uppercase tracking-wider font-bold text-slate-400">
                    Calculated Answer
                  </span>
                  <div className="text-lg sm:text-xl font-bold text-white tracking-tight leading-snug">
                    {analysisResult.final_answer}
                  </div>
                </div>


                {/* Metadata Tags: Dataset, Columns, Operation, Execution Result */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                  {/* Dataset */}
                  <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1">
                    <span className="text-[10px] text-slate-400 font-semibold uppercase flex items-center space-x-1">
                      <Database className="w-3 h-3 text-indigo-400" />
                      <span>Dataset Used</span>
                    </span>
                    <p className="text-xs font-medium text-slate-200 truncate">
                      {analysisResult.dataset_name || analysisResult.dataset_used}
                    </p>
                  </div>

                  {/* Columns */}
                  <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1">
                    <span className="text-[10px] text-slate-400 font-semibold uppercase flex items-center space-x-1">
                      <Columns3 className="w-3 h-3 text-indigo-400" />
                      <span>Columns Inspected</span>
                    </span>
                    <p className="text-xs font-medium text-slate-200">
                      {analysisResult.columns_used?.length > 0 
                        ? analysisResult.columns_used.join(', ')
                        : 'Entire Table (Row Index)'}
                    </p>
                  </div>

                  {/* Operation */}
                  <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1">
                    <span className="text-[10px] text-slate-400 font-semibold uppercase flex items-center space-x-1">
                      <Terminal className="w-3 h-3 text-amber-400" />
                      <span>Operation Type</span>
                    </span>
                    <p className="text-xs font-mono font-medium text-amber-300">
                      {analysisResult.operation || 'execution'}
                    </p>
                  </div>

                  {/* Raw Execution Result */}
                  <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1">
                    <span className="text-[10px] text-slate-400 font-semibold uppercase flex items-center space-x-1">
                      <Cpu className="w-3 h-3 text-emerald-400" />
                      <span>Raw Execution Result</span>
                    </span>
                    <p className="text-xs font-mono font-bold text-emerald-400 truncate">
                      {JSON.stringify(analysisResult.execution_result)}
                    </p>
                  </div>
                </div>

                {/* Proof Code Box */}
                {analysisResult.generated_code && (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-300 font-semibold flex items-center space-x-2">
                        <Code2 className="w-4 h-4 text-indigo-400" />
                        <span>Exact Executable Python Proof Code</span>
                      </span>
                      <button
                        onClick={handleCopyCode}
                        className="flex items-center space-x-1 text-slate-400 hover:text-white px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 transition-colors text-[11px] cursor-pointer"
                      >
                        {copiedCode ? (
                          <>
                            <Check className="w-3 h-3 text-emerald-400" />
                            <span className="text-emerald-400">Copied</span>
                          </>
                        ) : (
                          <>
                            <Copy className="w-3 h-3" />
                            <span>Copy Code</span>
                          </>
                        )}
                      </button>
                    </div>

                    <div className="relative rounded-xl bg-slate-950 border border-slate-800 p-4 font-mono text-xs text-slate-200 overflow-x-auto shadow-inner">
                      <pre className="leading-relaxed">
                        <code>{analysisResult.generated_code}</code>
                      </pre>
                    </div>

                    <p className="text-[11px] text-slate-500 font-mono">
                      Isolated Sandbox: Deep-copied dataframe • Restricted builtins • Zero external side effects
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* CANNOT DETERMINE / REFUSAL CARD */}
          {analysisResult.status === 'cannot_determine' && (
            <div className="bg-slate-900/80 border border-amber-500/40 rounded-2xl overflow-hidden shadow-xl shadow-amber-950/20">
              {/* Header Status Bar */}
              <div className="bg-amber-950/30 border-b border-amber-500/20 px-5 py-3.5 flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center space-x-2">
                  <div className="p-1 rounded-full bg-amber-500/20 text-amber-400">
                    <ShieldAlert className="w-4 h-4 text-amber-400" />
                  </div>
                  <div>
                    <span className="text-xs font-bold text-amber-400 uppercase tracking-wider">
                      STATUS: CANNOT DETERMINE (STRICT REFUSAL)
                    </span>
                    <p className="text-[10px] text-slate-400">
                      ProofGuard refusal rule triggered: The question cannot be answered reliably from the available data.
                    </p>
                  </div>
                </div>

                <span className="px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20 text-[10px] font-bold">
                  ZERO HALLUCINATION RULE
                </span>
              </div>

              {/* Body */}
              <div className="p-5 sm:p-6 space-y-4">
                {/* Stage 3 Forensic Gate Refusal Banner */}
                <div className="p-3.5 rounded-xl bg-rose-950/30 border border-rose-500/40 text-xs space-y-1.5">
                  <div className="flex items-center space-x-2 text-rose-400 font-bold uppercase tracking-wider text-[11px]">
                    <AlertTriangle className="w-4 h-4 text-rose-400 flex-shrink-0" />
                    <span>Stage 3 Data Forensics: UNSAFE FOR REQUESTED ANALYSIS</span>
                  </div>
                  <p className="text-slate-300 text-[11px] leading-relaxed">
                    Forensic pre-inspection blocked code execution because the query directly references columns with unresolved currency mismatches, conflicting records, ambiguous dates, or corrupted domain values.
                  </p>
                </div>

                <div className="space-y-1.5">
                  <span className="text-[10px] uppercase tracking-wider font-bold text-amber-400">
                    Refusal Reason & Forensic Evidence
                  </span>
                  <div className="text-base sm:text-lg font-semibold text-white tracking-tight leading-relaxed bg-amber-950/20 border border-amber-800/40 p-4 rounded-xl">
                    {analysisResult.reason}
                  </div>
                </div>


                {/* Warnings / Anomaly Context */}
                {analysisResult.warnings?.length > 0 && (
                  <div className="space-y-2">
                    <span className="text-[11px] font-semibold text-slate-300">
                      Related Stage 1 Guardrail Alerts:
                    </span>
                    <ul className="space-y-1.5">
                      {analysisResult.warnings.map((w, idx) => (
                        <li key={idx} className="text-xs text-slate-300 flex items-start space-x-2">
                          <AlertTriangle className="w-3.5 h-3.5 text-amber-400 mt-0.5 flex-shrink-0" />
                          <span>{w}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Columns / Dataset involved */}
                <div className="flex flex-wrap items-center gap-2 pt-2 text-xs">
                  <span className="text-slate-500">Evaluated on:</span>
                  <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-medium">
                    {analysisResult.dataset_name || analysisResult.dataset_used}
                  </span>
                  {analysisResult.columns_used?.length > 0 && (
                    <>
                      <span className="text-slate-500">Columns checked:</span>
                      {analysisResult.columns_used.map(c => (
                        <span key={c} className="px-2 py-0.5 rounded bg-slate-800 text-amber-300 font-mono text-[11px]">
                          {c}
                        </span>
                      ))}
                    </>
                  )}
                </div>

                <div className="pt-2 border-t border-slate-800/60 text-[11px] text-slate-400">
                  <span className="font-semibold text-slate-300">Core PS08 Requirement:</span> When datasets have mixed currencies, conflicting measurement units, impossible values, or temporal bounds violations, systems must declare <span className="text-amber-400 font-mono">CANNOT DETERMINE</span> instead of providing misleading calculations.
                </div>
              </div>
            </div>
          )}

          {/* EXECUTION FAILED CARD */}
          {analysisResult.status === 'execution_failed' && (
            <div className="bg-slate-900/80 border border-rose-500/40 rounded-2xl overflow-hidden shadow-xl shadow-rose-950/20 p-5 space-y-3">
              <div className="flex items-center space-x-2 text-rose-400">
                <AlertTriangle className="w-5 h-5" />
                <span className="text-xs font-bold uppercase tracking-wider">
                  STATUS: EXECUTION FAILED
                </span>
              </div>
              <p className="text-xs text-rose-200">
                {analysisResult.reason || 'The generated analysis code could not be executed successfully.'}
              </p>
            </div>
          )}

          {/* ─── STAGE 4: ANSWER GUARDIAN PANEL ───────────────────── */}
          <div className="border-t border-slate-800/60 pt-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2">
                <Shield className="w-4 h-4 text-indigo-400" />
                <span className="text-xs font-semibold text-slate-200">Answer Guardian</span>
                <span className="px-1.5 py-0.5 text-[9px] font-bold rounded bg-indigo-500 text-white uppercase tracking-wider">Stage 4</span>
              </div>
              <button
                onClick={() => setShowGuardian(!showGuardian)}
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all border ${
                  showGuardian
                    ? 'bg-indigo-600/20 border-indigo-500/40 text-indigo-300'
                    : 'bg-slate-900 border-slate-700 text-slate-300 hover:bg-slate-800 hover:text-white'
                }`}
              >
                <Shield className="w-3.5 h-3.5" />
                <span>{showGuardian ? 'Hide Guardian' : 'Activate Guardian Evaluation'}</span>
                {showGuardian ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
              </button>
            </div>

            {!showGuardian && (
              <div className="p-3.5 rounded-xl bg-indigo-950/20 border border-indigo-500/20 text-xs text-slate-400 leading-relaxed">
                <span className="text-indigo-300 font-semibold">The AI analyst must NOT be the final authority.</span>{" "}
                The Answer Guardian independently challenges every assumption, inspects proof code logic,
                examines forensic findings, and issues a final Trust Score and Verdict
                (TRUSTED / CONDITIONALLY TRUSTED / DISPUTED / REJECTED).
              </div>
            )}

            {showGuardian && (
              <AnswerGuardian
                analysisResult={analysisResult}
                datasetId={selectedDatasetId || analysisResult?.dataset_used}
              />
            )}
          </div>
        </div>
      )}
    </div>
  );
}
