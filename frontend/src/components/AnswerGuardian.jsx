import React, { useState } from 'react';
import {
  Shield,
  ShieldCheck,
  ShieldAlert,
  ShieldX,
  Gavel,
  ChevronDown,
  ChevronRight,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  Database,
  Code2,
  Cpu,
  Search,
  MessageSquare,
  Send,
  Info,
  BarChart3,
  Layers,
  RefreshCw,
} from 'lucide-react';
import { evaluateWithGuardian, submitUserChallenge } from '../services/api';

// ─── VERDICT CONFIG ───────────────────────────────────────────────────────────
const VERDICT_CONFIG = {
  TRUSTED: {
    icon: ShieldCheck,
    color: 'emerald',
    borderColor: 'border-emerald-500/50',
    bgColor: 'bg-emerald-950/30',
    headerBg: 'bg-emerald-950/40',
    textColor: 'text-emerald-400',
    badgeBg: 'bg-emerald-500',
    label: 'TRUSTED',
    emoji: '✅',
  },
  CONDITIONALLY_TRUSTED: {
    icon: Shield,
    color: 'amber',
    borderColor: 'border-amber-500/50',
    bgColor: 'bg-amber-950/20',
    headerBg: 'bg-amber-950/40',
    textColor: 'text-amber-300',
    badgeBg: 'bg-amber-500',
    label: 'CONDITIONALLY TRUSTED',
    emoji: '⚠️',
  },
  DISPUTED: {
    icon: ShieldAlert,
    color: 'orange',
    borderColor: 'border-orange-500/50',
    bgColor: 'bg-orange-950/20',
    headerBg: 'bg-orange-950/40',
    textColor: 'text-orange-300',
    badgeBg: 'bg-orange-500',
    label: 'DISPUTED',
    emoji: '🔴',
  },
  REJECTED: {
    icon: ShieldX,
    color: 'rose',
    borderColor: 'border-rose-600/60',
    bgColor: 'bg-rose-950/30',
    headerBg: 'bg-rose-950/50',
    textColor: 'text-rose-400',
    badgeBg: 'bg-rose-600',
    label: 'REJECTED',
    emoji: '❌',
  },
};

const SEVERITY_CONFIG = {
  CRITICAL: { color: 'text-rose-400', bg: 'bg-rose-950/40 border-rose-500/40', badge: 'bg-rose-500/20 text-rose-300 border border-rose-500/30' },
  HIGH: { color: 'text-orange-400', bg: 'bg-orange-950/30 border-orange-500/30', badge: 'bg-orange-500/20 text-orange-300 border border-orange-500/30' },
  MEDIUM: { color: 'text-amber-400', bg: 'bg-amber-950/20 border-amber-500/30', badge: 'bg-amber-500/20 text-amber-300 border border-amber-500/30' },
  LOW: { color: 'text-slate-300', bg: 'bg-slate-900/60 border-slate-700/40', badge: 'bg-slate-800 text-slate-400' },
};

const LINEAGE_ICONS = {
  database: Database,
  search: Search,
  code: Code2,
  cpu: Cpu,
  shield: Shield,
  gavel: Gavel,
};

const LINEAGE_STATUS_CONFIG = {
  complete: { color: 'text-emerald-400', bg: 'bg-emerald-500/20', dot: 'bg-emerald-400' },
  warning: { color: 'text-amber-400', bg: 'bg-amber-500/20', dot: 'bg-amber-400' },
  failed: { color: 'text-rose-400', bg: 'bg-rose-500/20', dot: 'bg-rose-400' },
  skipped: { color: 'text-slate-400', bg: 'bg-slate-800/50', dot: 'bg-slate-500' },
};

// ─── TRUST SCORE RING ──────────────────────────────────────────────────────────
function TrustScoreRing({ score, grade, verdictColor }) {
  const radius = 36;
  const circumference = 2 * Math.PI * radius;
  const dashOffset = circumference - (score / 100) * circumference;

  const colorMap = {
    emerald: '#10b981',
    amber: '#f59e0b',
    orange: '#f97316',
    rose: '#f43f5e',
  };
  const strokeColor = colorMap[verdictColor] || '#6366f1';

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width="96" height="96" className="-rotate-90">
        <circle cx="48" cy="48" r={radius} fill="none" stroke="#1e293b" strokeWidth="8" />
        <circle
          cx="48" cy="48" r={radius}
          fill="none"
          stroke={strokeColor}
          strokeWidth="8"
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 0.8s ease' }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-xl font-black text-white">{score}</span>
        <span className="text-[10px] font-bold text-slate-400">Grade {grade}</span>
      </div>
    </div>
  );
}

// ─── TRUST DIMENSION BAR ───────────────────────────────────────────────────────
function TrustDimensionBar({ dim }) {
  const getBarColor = (score) => {
    if (score >= 80) return 'bg-emerald-500';
    if (score >= 60) return 'bg-amber-500';
    if (score >= 40) return 'bg-orange-500';
    return 'bg-rose-500';
  };

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-xs">
        <span className="text-slate-300 font-medium">{dim.name}</span>
        <span className={`font-bold ${dim.score >= 80 ? 'text-emerald-400' : dim.score >= 60 ? 'text-amber-400' : dim.score >= 40 ? 'text-orange-400' : 'text-rose-400'}`}>
          {dim.score}/100
        </span>
      </div>
      <div className="relative h-2 bg-slate-800 rounded-full overflow-hidden">
        <div
          className={`absolute left-0 top-0 h-full rounded-full transition-all duration-700 ${getBarColor(dim.score)}`}
          style={{ width: `${dim.score}%` }}
        />
      </div>
      <p className="text-[11px] text-slate-500 leading-relaxed">{dim.reason}</p>
    </div>
  );
}

// ─── CHALLENGE CARD ────────────────────────────────────────────────────────────
function ChallengeCard({ challenge, index }) {
  const [expanded, setExpanded] = useState(false);
  const sev = SEVERITY_CONFIG[challenge.severity] || SEVERITY_CONFIG.LOW;

  return (
    <div className={`rounded-xl border p-3.5 space-y-2 ${sev.bg}`}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-start space-x-2 flex-1">
          {challenge.resolved
            ? <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
            : <AlertTriangle className={`w-4 h-4 ${sev.color} flex-shrink-0 mt-0.5`} />
          }
          <p className="text-xs text-slate-200 leading-relaxed flex-1">{challenge.challenge}</p>
        </div>
        <div className="flex items-center space-x-1.5 flex-shrink-0">
          <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${sev.badge}`}>
            {challenge.severity}
          </span>
          <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${
            challenge.resolved ? 'bg-emerald-500/20 text-emerald-300' : 'bg-slate-800 text-slate-400'
          }`}>
            {challenge.resolved ? 'RESOLVED' : 'UNRESOLVED'}
          </span>
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-slate-500 hover:text-slate-200 p-0.5 transition-colors"
          >
            {expanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {expanded && (
        <div className="pt-2 border-t border-slate-700/40 space-y-2">
          <div>
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Evidence</span>
            <p className="text-[11px] text-slate-300 mt-0.5 leading-relaxed">{challenge.evidence}</p>
          </div>
          {challenge.rebuttal && (
            <div>
              <span className="text-[10px] font-bold text-emerald-500 uppercase tracking-wider">Analyst Rebuttal</span>
              <p className="text-[11px] text-emerald-300/80 mt-0.5 leading-relaxed">{challenge.rebuttal}</p>
            </div>
          )}
          <div className="flex items-center space-x-1.5 text-[10px] text-slate-500">
            <span className="font-mono text-slate-600">ID: {challenge.id}</span>
            <span>•</span>
            <span className="capitalize">{challenge.category}</span>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── PROOF LINEAGE STEPPER ────────────────────────────────────────────────────
function ProofLineage({ lineage }) {
  return (
    <div className="space-y-1">
      {lineage.map((step, idx) => {
        const Icon = LINEAGE_ICONS[step.icon] || Layers;
        const statusCfg = LINEAGE_STATUS_CONFIG[step.status] || LINEAGE_STATUS_CONFIG.skipped;
        const isLast = idx === lineage.length - 1;

        return (
          <div key={step.step} className="flex items-start space-x-3">
            {/* Line + dot */}
            <div className="flex flex-col items-center">
              <div className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 ${statusCfg.bg}`}>
                <Icon className={`w-3.5 h-3.5 ${statusCfg.color}`} />
              </div>
              {!isLast && <div className="w-px h-4 bg-slate-800 mt-0.5" />}
            </div>
            {/* Content */}
            <div className="pb-3 pt-0.5 flex-1 min-w-0">
              <div className="flex items-center space-x-2">
                <span className="text-xs font-semibold text-slate-200">{step.stage}</span>
                <span className={`text-[10px] px-1.5 py-0.2 rounded font-bold uppercase tracking-wide ${
                  step.status === 'complete' ? 'bg-emerald-500/20 text-emerald-400' :
                  step.status === 'warning' ? 'bg-amber-500/20 text-amber-400' :
                  step.status === 'failed' ? 'bg-rose-500/20 text-rose-400' :
                  'bg-slate-800 text-slate-500'
                }`}>
                  {step.status}
                </span>
              </div>
              <p className="text-[11px] text-slate-400 mt-0.5 leading-relaxed">{step.detail}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ─── CHALLENGE THIS ANSWER PANEL ──────────────────────────────────────────────
function UserChallengePanel({ question, datasetId, guardianVerdict, onChallengeResult }) {
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!text.trim()) return;
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const resp = await submitUserChallenge({
        question,
        dataset_id: datasetId,
        challenge_text: text.trim(),
        guardian_response_summary: guardianVerdict?.summary,
      });
      setResult(resp);
      if (onChallengeResult) onChallengeResult(resp);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center space-x-2 text-xs">
        <MessageSquare className="w-4 h-4 text-indigo-400" />
        <span className="text-slate-300 font-medium">Challenge the Guardian's Verdict</span>
      </div>

      <p className="text-[11px] text-slate-400 leading-relaxed">
        Do you believe the Guardian's verdict is wrong? Submit your counter-argument below.
        Reference specific data values, columns, or code logic to have the best chance of overturning it.
      </p>

      <form onSubmit={handleSubmit} className="space-y-2">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="e.g. The Guardian flagged the coerce issue but the dataset column is fully numeric — there are no non-numeric values in the 'quantity' column, so no rows were dropped..."
          disabled={loading}
          rows={3}
          className="w-full bg-slate-950 border border-slate-700 focus:border-indigo-500 rounded-xl px-4 py-3 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500/50 resize-none transition-all"
        />
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={loading || !text.trim()}
            className="flex items-center space-x-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-500 text-white rounded-xl text-xs font-semibold transition-all"
          >
            {loading ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Submitting...</span>
              </>
            ) : (
              <>
                <Send className="w-3.5 h-3.5" />
                <span>Submit Counter-Challenge</span>
              </>
            )}
          </button>
        </div>
      </form>

      {error && (
        <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-800/60 text-xs text-rose-300">
          {error}
        </div>
      )}

      {result && (
        <div className={`p-4 rounded-xl border space-y-2 ${
          result.upheld
            ? 'bg-amber-950/20 border-amber-500/30'
            : 'bg-emerald-950/20 border-emerald-500/30'
        }`}>
          <div className="flex items-center space-x-2">
            {result.upheld
              ? <ShieldAlert className="w-4 h-4 text-amber-400" />
              : <ShieldCheck className="w-4 h-4 text-emerald-400" />
            }
            <span className={`text-xs font-bold uppercase tracking-wider ${result.upheld ? 'text-amber-400' : 'text-emerald-400'}`}>
              {result.upheld ? 'VERDICT UPHELD' : 'VERDICT REVISED'}
            </span>
            {!result.upheld && result.updated_verdict && (
              <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                → {result.updated_verdict}
              </span>
            )}
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">{result.counter_analysis}</p>
          <p className="text-[11px] text-slate-400 leading-relaxed italic">{result.reasoning}</p>
          {!result.upheld && result.updated_trust_score && (
            <div className="text-[11px] text-emerald-400 font-mono">
              Updated Trust Score: {result.updated_trust_score}/100
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ─── MAIN COMPONENT ───────────────────────────────────────────────────────────
export default function AnswerGuardian({ analysisResult, datasetId, onClose }) {
  const [guardianResult, setGuardianResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('overview'); // 'overview', 'challenges', 'lineage', 'challenge-it'
  const [hasRun, setHasRun] = useState(false);

  const runGuardian = async () => {
    if (!analysisResult) return;
    setLoading(true);
    setError('');

    try {
      const payload = {
        question: analysisResult.question,
        dataset_id: datasetId || analysisResult.dataset_used,
        answer_status: analysisResult.status,
        final_answer: analysisResult.final_answer || null,
        generated_code: analysisResult.generated_code || null,
        execution_result: analysisResult.execution_result ?? null,
        columns_used: analysisResult.columns_used || [],
        operation: analysisResult.operation || null,
        forensic_status: analysisResult.forensic_status || null,
        forensic_findings: analysisResult.forensic_findings || [],
        warnings: analysisResult.warnings || [],
      };

      const resp = await evaluateWithGuardian(payload);
      setGuardianResult(resp);
      setHasRun(true);
    } catch (err) {
      setError(err.message || 'Guardian evaluation failed. Check backend connection.');
    } finally {
      setLoading(false);
    }
  };

  const verdict = guardianResult?.verdict;
  const vCfg = verdict ? (VERDICT_CONFIG[verdict.verdict] || VERDICT_CONFIG.DISPUTED) : null;
  const VerdictIcon = vCfg?.icon || Shield;

  const unresolvedCritical = guardianResult?.challenges?.filter(c => !c.resolved && c.severity === 'CRITICAL') || [];
  const unresolvedHigh = guardianResult?.challenges?.filter(c => !c.resolved && c.severity === 'HIGH') || [];
  const unresolvedAll = guardianResult?.challenges?.filter(c => !c.resolved) || [];

  const tabs = [
    { id: 'overview', label: 'Trust Overview', icon: BarChart3 },
    { id: 'challenges', label: `Challenges (${guardianResult?.challenges?.length || 0})`, icon: Gavel },
    { id: 'lineage', label: 'Proof Lineage', icon: Layers },
    { id: 'challenge-it', label: 'Challenge This Answer', icon: MessageSquare },
  ];

  return (
    <div className="bg-slate-900/80 border border-indigo-500/30 rounded-2xl overflow-hidden shadow-2xl shadow-indigo-950/30">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-950/60 via-slate-900/60 to-slate-900/30 border-b border-indigo-500/20 px-5 py-4">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20">
              <Shield className="w-5 h-5 text-indigo-400" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-sm font-bold text-white">Answer Guardian</h3>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-500 text-white tracking-wider uppercase">
                  Stage 4
                </span>
              </div>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Independent adversarial trust evaluator — challenges the analyst's answer
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {hasRun && (
              <button
                onClick={runGuardian}
                disabled={loading}
                title="Re-evaluate"
                className="p-2 rounded-xl border border-slate-700 bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 transition-colors"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              </button>
            )}
          </div>
        </div>

        {/* Pipeline flow badge */}
        <div className="mt-3 flex items-center space-x-1.5 text-[11px] font-mono bg-slate-950/50 border border-slate-800 rounded-xl px-3 py-1.5 text-slate-400 w-fit">
          <span className="text-indigo-400">AI Proposes</span>
          <span className="text-slate-600">→</span>
          <span className="text-amber-400">Forensics Checks</span>
          <span className="text-slate-600">→</span>
          <span className="text-sky-400">Code Executes</span>
          <span className="text-slate-600">→</span>
          <span className="text-rose-400 font-bold">Guardian Challenges</span>
          <span className="text-slate-600">→</span>
          <span className="text-emerald-400">Verifier Decides</span>
        </div>
      </div>

      <div className="p-5 space-y-5">
        {/* Pre-run state */}
        {!hasRun && !loading && (
          <div className="text-center py-8 space-y-4">
            <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mx-auto">
              <Gavel className="w-8 h-8 text-indigo-400" />
            </div>
            <div>
              <h4 className="text-sm font-semibold text-white mb-1">
                Ready to Challenge This Answer
              </h4>
              <p className="text-xs text-slate-400 max-w-md mx-auto leading-relaxed">
                The Answer Guardian will independently evaluate whether the analyst's
                answer should be trusted. It challenges assumptions, inspects code logic,
                examines data quality, and issues a final verdict with a Trust Score.
              </p>
            </div>
            <button
              onClick={runGuardian}
              className="inline-flex items-center space-x-2 px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-sm font-semibold transition-all shadow-lg shadow-indigo-600/20"
            >
              <Shield className="w-4 h-4" />
              <span>Activate Guardian Evaluation</span>
            </button>
            <p className="text-[11px] text-slate-600 font-mono">
              The AI analyst must NOT be the final authority.
            </p>
          </div>
        )}

        {/* Loading state */}
        {loading && (
          <div className="py-8 space-y-4">
            <div className="flex flex-col items-center space-y-3">
              <div className="relative">
                <div className="w-12 h-12 border-2 border-indigo-500/20 rounded-full" />
                <div className="w-12 h-12 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin absolute inset-0" />
                <Shield className="w-5 h-5 text-indigo-400 absolute inset-0 m-auto" />
              </div>
              <div className="text-center">
                <p className="text-sm font-semibold text-white">Guardian is evaluating...</p>
                <p className="text-xs text-slate-400 mt-1">Raising adversarial challenges, scoring trust dimensions, issuing verdict</p>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-2 text-center">
              {['Challenging Assumptions', 'Inspecting Code Logic', 'Scoring Dimensions'].map((step, i) => (
                <div key={i} className="p-2 rounded-lg bg-slate-900/50 border border-slate-800">
                  <div className="w-4 h-4 border border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-1" style={{ animationDelay: `${i * 0.2}s` }} />
                  <p className="text-[10px] text-slate-400">{step}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Error */}
        {error && !loading && (
          <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800/60 text-xs text-rose-300 flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-rose-400 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Results */}
        {guardianResult && !loading && (
          <div className="space-y-4 animate-in fade-in duration-300">

            {/* VERDICT BANNER */}
            <div className={`rounded-xl border p-4 ${vCfg.bgColor} ${vCfg.borderColor}`}>
              <div className="flex flex-col sm:flex-row sm:items-center gap-4">
                {/* Score Ring */}
                <div className="flex-shrink-0 flex flex-col items-center">
                  <TrustScoreRing
                    score={guardianResult.trust_score}
                    grade={guardianResult.trust_grade}
                    verdictColor={vCfg.color}
                  />
                  <span className="text-[10px] text-slate-400 mt-1 text-center font-mono">Trust Score</span>
                </div>

                {/* Verdict info */}
                <div className="flex-1 space-y-2">
                  <div className="flex items-center space-x-2">
                    <VerdictIcon className={`w-5 h-5 ${vCfg.textColor}`} />
                    <span className={`text-sm font-black uppercase tracking-wide ${vCfg.textColor}`}>
                      {vCfg.emoji} {vCfg.label}
                    </span>
                    <span className={`px-2 py-0.5 text-[10px] font-bold rounded text-white ${vCfg.badgeBg}`}>
                      {verdict.can_publish ? 'PUBLISHABLE' : 'DO NOT PUBLISH'}
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed">{verdict.summary}</p>
                  {verdict.conditions?.length > 0 && (
                    <div className="space-y-1">
                      {verdict.conditions.map((cond, idx) => (
                        <div key={idx} className="flex items-start space-x-1.5 text-[11px] text-amber-300">
                          <Info className="w-3.5 h-3.5 text-amber-400 flex-shrink-0 mt-0.5" />
                          <span>{cond}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Challenge summary */}
                <div className="flex-shrink-0 grid grid-cols-2 gap-1.5 text-center sm:w-28">
                  <div className={`p-2 rounded-lg ${unresolvedCritical.length > 0 ? 'bg-rose-950/50 border border-rose-500/30' : 'bg-slate-900/60 border border-slate-800'}`}>
                    <div className={`text-sm font-black ${unresolvedCritical.length > 0 ? 'text-rose-400' : 'text-slate-400'}`}>{unresolvedCritical.length}</div>
                    <div className="text-[9px] text-slate-500 uppercase tracking-wide">Critical</div>
                  </div>
                  <div className={`p-2 rounded-lg ${unresolvedHigh.length > 0 ? 'bg-orange-950/40 border border-orange-500/30' : 'bg-slate-900/60 border border-slate-800'}`}>
                    <div className={`text-sm font-black ${unresolvedHigh.length > 0 ? 'text-orange-400' : 'text-slate-400'}`}>{unresolvedHigh.length}</div>
                    <div className="text-[9px] text-slate-500 uppercase tracking-wide">High</div>
                  </div>
                  <div className="p-2 rounded-lg bg-slate-900/60 border border-slate-800 col-span-2">
                    <div className="text-sm font-black text-slate-300">{guardianResult.challenges?.length || 0}</div>
                    <div className="text-[9px] text-slate-500 uppercase tracking-wide">Total</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Recommendation */}
            <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 text-xs text-slate-300 leading-relaxed font-medium">
              {guardianResult.recommendation}
            </div>

            {/* Tabs */}
            <div className="flex items-center space-x-0.5 border-b border-slate-800 overflow-x-auto">
              {tabs.map(tab => {
                const TabIcon = tab.icon;
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center space-x-1.5 px-3 py-2 text-[11px] font-medium border-b-2 transition-all flex-shrink-0 ${
                      isActive
                        ? 'border-indigo-500 text-indigo-300 bg-indigo-500/5'
                        : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/30'
                    }`}
                  >
                    <TabIcon className="w-3.5 h-3.5" />
                    <span>{tab.label}</span>
                  </button>
                );
              })}
            </div>

            {/* Tab Content */}
            <div className="min-h-[200px]">
              {/* OVERVIEW TAB */}
              {activeTab === 'overview' && (
                <div className="space-y-4">
                  {/* Trust Dimensions */}
                  <div>
                    <h4 className="text-xs font-bold text-slate-300 mb-3 uppercase tracking-wider">
                      Trust Score Breakdown
                    </h4>
                    <div className="space-y-4">
                      {guardianResult.trust_dimensions?.map((dim, idx) => (
                        <TrustDimensionBar key={idx} dim={dim} />
                      ))}
                    </div>
                  </div>

                  {/* Evidence chain */}
                  <div>
                    <h4 className="text-xs font-bold text-slate-300 mb-2 uppercase tracking-wider">
                      Evidence Chain Summary
                    </h4>
                    <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-3.5 space-y-1.5">
                      {guardianResult.evidence_chain?.map((item, idx) => (
                        <div key={idx} className="flex items-start space-x-2 text-[11px]">
                          <span className="text-slate-600 font-mono flex-shrink-0">{String(idx + 1).padStart(2, '0')}.</span>
                          <span className="text-slate-300">{item}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* CHALLENGES TAB */}
              {activeTab === 'challenges' && (
                <div className="space-y-3">
                  {/* Summary bar */}
                  <div className="flex items-center justify-between text-xs text-slate-400">
                    <span>{guardianResult.challenges?.length || 0} total challenges</span>
                    <div className="flex items-center space-x-3">
                      <span className="text-emerald-400">
                        {guardianResult.challenges?.filter(c => c.resolved).length || 0} resolved
                      </span>
                      <span className="text-rose-400">
                        {unresolvedAll.length} unresolved
                      </span>
                    </div>
                  </div>

                  {guardianResult.challenges?.length === 0 ? (
                    <div className="text-center py-6 text-slate-500 text-xs">
                      No adversarial challenges raised by the Guardian.
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {/* Unresolved first */}
                      {guardianResult.challenges
                        ?.slice()
                        .sort((a, b) => {
                          if (a.resolved !== b.resolved) return a.resolved ? 1 : -1;
                          const sevOrder = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 };
                          return (sevOrder[a.severity] || 3) - (sevOrder[b.severity] || 3);
                        })
                        .map((challenge, idx) => (
                          <ChallengeCard key={challenge.id} challenge={challenge} index={idx} />
                        ))
                      }
                    </div>
                  )}
                </div>
              )}

              {/* LINEAGE TAB */}
              {activeTab === 'lineage' && (
                <div>
                  <h4 className="text-xs font-bold text-slate-300 mb-3 uppercase tracking-wider">
                    Proof Lineage Chain
                  </h4>
                  <p className="text-[11px] text-slate-400 mb-4">
                    Every step from data ingestion to Guardian verdict, documented for full auditability.
                  </p>
                  <ProofLineage lineage={guardianResult.proof_lineage || []} />
                </div>
              )}

              {/* CHALLENGE IT TAB */}
              {activeTab === 'challenge-it' && (
                <UserChallengePanel
                  question={guardianResult.question}
                  datasetId={guardianResult.dataset_id}
                  guardianVerdict={verdict}
                  onChallengeResult={(result) => {
                    // optionally reflect updated score
                  }}
                />
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
