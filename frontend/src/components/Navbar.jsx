import React from 'react';
import { ShieldCheck, ShieldAlert, Activity, Sparkles, Database, Layers } from 'lucide-react';

export default function Navbar({ backendStatus, activeDataset }) {
  const isOnline = backendStatus?.status === 'online';

  return (
    <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        
        {/* Brand & Identity */}
        <div className="flex items-center space-x-3">
          <div className="relative">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center shadow-lg shadow-indigo-500/25 border border-indigo-400/30">
              <ShieldCheck className="w-6 h-6 text-white" />
            </div>
            <span className="absolute -top-1 -right-1 flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
            </span>
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-extrabold text-xl tracking-tight bg-gradient-to-r from-white via-slate-100 to-indigo-200 bg-clip-text text-transparent">
                PROOFGUARD
              </span>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 tracking-wider">
                STAGE 1 FOUNDATION
              </span>
            </div>
            <p className="text-xs text-slate-400 hidden sm:block">
              AI Data Analysis with an Independent Trust & Verification Layer
            </p>
          </div>
        </div>

        {/* Right Info Badges */}
        <div className="flex items-center space-x-3">
          {activeDataset && (
            <div className="hidden md:flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-800/60 border border-slate-700/60 text-xs text-slate-300">
              <Database className="w-3.5 h-3.5 text-indigo-400" />
              <span className="text-slate-400">Active:</span>
              <span className="font-semibold text-white truncate max-w-[150px]">{activeDataset.name}</span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-700 text-slate-300">
                {activeDataset.row_count.toLocaleString()} rows
              </span>
            </div>
          )}

          {/* Backend Status indicator */}
          <div className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg border text-xs font-medium transition-all ${
            isOnline 
              ? 'bg-emerald-950/30 border-emerald-500/30 text-emerald-400' 
              : 'bg-rose-950/30 border-rose-500/30 text-rose-400'
          }`}>
            <span className={`w-2 h-2 rounded-full ${isOnline ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'}`} />
            <span>FastAPI: {isOnline ? 'Engine Online' : 'Connecting...'}</span>
          </div>

          <div className="hidden lg:flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-indigo-950/40 border border-indigo-800/40 text-[11px] text-indigo-300">
            <span className="font-mono text-indigo-200">HNX26PSI08</span>
          </div>
        </div>

      </div>
    </header>
  );
}
