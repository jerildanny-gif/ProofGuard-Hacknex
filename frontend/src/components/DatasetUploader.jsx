import React, { useState, useRef } from 'react';
import { UploadCloud, FileSpreadsheet, AlertCircle, CheckCircle2, Loader2, ArrowUpRight } from 'lucide-react';
import { uploadDatasetFile } from '../services/api';

export default function DatasetUploader({ onDatasetLoaded }) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileProcess = async (file) => {
    if (!file) return;

    const ext = file.name.split('.').pop().toLowerCase();
    if (!['csv', 'xlsx', 'xls'].includes(ext)) {
      setError('Please upload a valid CSV or Excel (.xlsx, .xls) file.');
      return;
    }

    if (file.size > 25 * 1024 * 1024) {
      setError('File size exceeds the 25MB maximum limit.');
      return;
    }

    try {
      setUploading(true);
      setError(null);
      setSuccessMsg(null);

      const result = await uploadDatasetFile(file);
      setSuccessMsg(`Successfully ingested "${result.meta.name}" (${result.meta.row_count.toLocaleString()} rows)`);
      if (onDatasetLoaded) {
        onDatasetLoaded(result.meta.id);
      }
    } catch (err) {
      setError(err.message || 'Error uploading file');
    } finally {
      setUploading(false);
    }
  };

  const onDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const onDragLeave = () => {
    setIsDragging(false);
  };

  const onDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileProcess(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 relative overflow-hidden backdrop-blur-md">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
            <UploadCloud className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">Upload Custom Dataset</h3>
            <p className="text-xs text-slate-400">Ingest CSV or Excel sheets for verification profiling</p>
          </div>
        </div>
        <span className="text-[11px] font-mono text-slate-500 bg-slate-950 px-2 py-1 rounded border border-slate-800">
          CSV, XLSX &lt; 25MB
        </span>
      </div>

      {/* Drag & Drop Area */}
      <div
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all flex flex-col items-center justify-center relative ${
          isDragging
            ? 'border-indigo-500 bg-indigo-500/10 shadow-inner'
            : 'border-slate-800 hover:border-slate-700 bg-slate-950/40 hover:bg-slate-950/70'
        }`}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={(e) => {
            if (e.target.files?.[0]) handleFileProcess(e.target.files[0]);
          }}
          accept=".csv,.xlsx,.xls"
          className="hidden"
        />

        {uploading ? (
          <div className="flex flex-col items-center py-4">
            <Loader2 className="w-8 h-8 text-indigo-400 animate-spin mb-3" />
            <p className="text-sm font-medium text-white">Analyzing & computing dataset statistics...</p>
            <p className="text-xs text-slate-400 mt-1">Scanning duplicates, inferring column dtypes & quality flags</p>
          </div>
        ) : (
          <>
            <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mb-3 text-indigo-400 group-hover:scale-105 transition-transform">
              <FileSpreadsheet className="w-6 h-6" />
            </div>
            <p className="text-sm font-medium text-slate-200">
              <span className="text-indigo-400 font-semibold underline decoration-indigo-400/40 underline-offset-4">Click to browse</span> or drag and drop
            </p>
            <p className="text-xs text-slate-500 mt-1.5">
              Supports real-world messy CSV & XLSX tables
            </p>
          </>
        )}
      </div>

      {/* Status alerts */}
      {error && (
        <div className="mt-4 p-3 rounded-xl bg-rose-950/40 border border-rose-500/30 flex items-center space-x-2.5 text-xs text-rose-300">
          <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {successMsg && (
        <div className="mt-4 p-3 rounded-xl bg-emerald-950/40 border border-emerald-500/30 flex items-center space-x-2.5 text-xs text-emerald-300">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}
    </div>
  );
}
