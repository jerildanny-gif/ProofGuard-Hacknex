import React, { useState, useEffect } from 'react';
import { Table, ChevronLeft, ChevronRight, Search, FileDown, Eye, Filter } from 'lucide-react';
import { getDatasetPreview } from '../services/api';

export default function DatasetPreviewTable({ datasetId, totalRows }) {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [previewData, setPreviewData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [filterText, setFilterText] = useState('');

  useEffect(() => {
    setPage(1);
  }, [datasetId]);

  useEffect(() => {
    let isCancelled = false;

    const loadData = async () => {
      if (!datasetId) return;
      try {
        setLoading(true);
        const data = await getDatasetPreview(datasetId, page, pageSize);
        if (!isCancelled) {
          setPreviewData(data);
        }
      } catch (err) {
        console.error('Failed to load preview:', err);
      } finally {
        if (!isCancelled) setLoading(false);
      }
    };

    loadData();
    return () => { isCancelled = true; };
  }, [datasetId, page, pageSize]);

  if (!previewData && loading) {
    return (
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-12 text-center text-slate-400">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        <p className="text-sm">Fetching tabular data preview...</p>
      </div>
    );
  }

  if (!previewData) return null;

  const { columns, rows, total_pages, total_rows } = previewData;

  const filteredRows = rows.filter(row => {
    if (!filterText.trim()) return true;
    return Object.values(row).some(val => 
      String(val).toLowerCase().includes(filterText.toLowerCase())
    );
  });

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur-md">
      {/* Table Controls Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 mb-4 border-b border-slate-800/80 gap-3">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
            <Table className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">Dataset Records Explorer</h3>
            <p className="text-xs text-slate-400">
              Showing page {page} of {total_pages} ({total_rows.toLocaleString()} total rows)
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {/* Row filter search */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Filter current page..."
              value={filterText}
              onChange={(e) => setFilterText(e.target.value)}
              className="bg-slate-950/80 border border-slate-800 rounded-xl pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 w-44 sm:w-56"
            />
          </div>

          {/* Rows per page selector */}
          <select
            value={pageSize}
            onChange={(e) => {
              setPageSize(Number(e.target.value));
              setPage(1);
            }}
            className="bg-slate-950/80 border border-slate-800 rounded-xl px-2.5 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-indigo-500 cursor-pointer"
          >
            <option value={10}>10 rows</option>
            <option value={20}>20 rows</option>
            <option value={50}>50 rows</option>
          </select>
        </div>
      </div>

      {/* Table Container */}
      <div className="relative overflow-x-auto rounded-xl border border-slate-800 bg-slate-950/60 max-h-[520px]">
        {loading && (
          <div className="absolute inset-0 bg-slate-950/50 backdrop-blur-xs flex items-center justify-center z-10">
            <div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        <table className="w-full text-left text-xs border-collapse">
          <thead className="bg-slate-900/90 text-slate-300 uppercase text-[10px] tracking-wider font-mono sticky top-0 z-10 border-b border-slate-800 shadow-sm">
            <tr>
              <th className="py-2.5 px-3 font-semibold text-slate-500 text-center w-12 border-r border-slate-800/60">#</th>
              {columns.map((col) => (
                <th key={col} className="py-2.5 px-3 font-semibold whitespace-nowrap border-r border-slate-800/40 last:border-r-0">
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300 text-[11px]">
            {filteredRows.map((row, idx) => {
              const rowNum = (page - 1) * pageSize + idx + 1;
              return (
                <tr key={idx} className="hover:bg-indigo-950/20 transition-colors">
                  <td className="py-2 px-3 text-center text-slate-500 border-r border-slate-800/60 select-none bg-slate-900/30">
                    {rowNum}
                  </td>
                  {columns.map((col) => {
                    const val = row[col];
                    const isNull = val === null || val === undefined;
                    const isTrap = String(val).startsWith('$') || String(val).startsWith('€') || String(val).startsWith('£') || val === '?' || val === 'TBD' || val === 'N/A' || Number(val) < 0;

                    return (
                      <td key={col} className="py-2 px-3 whitespace-nowrap border-r border-slate-800/30 last:border-r-0">
                        {isNull ? (
                          <span className="px-1.5 py-0.5 rounded text-[10px] bg-amber-500/10 text-amber-400 border border-amber-500/20 italic">
                            null
                          </span>
                        ) : isTrap ? (
                          <span className="text-amber-300 font-medium bg-amber-950/30 px-1 rounded">
                            {String(val)}
                          </span>
                        ) : (
                          <span>{String(val)}</span>
                        )}
                      </td>
                    );
                  })}
                </tr>
              );
            })}

            {filteredRows.length === 0 && (
              <tr>
                <td colSpan={columns.length + 1} className="py-8 text-center text-slate-500 text-xs">
                  No records match current filter
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div className="flex items-center justify-between pt-4 mt-3 border-t border-slate-800/80 text-xs text-slate-400">
        <div>
          Showing <span className="font-semibold text-slate-200">{(page - 1) * pageSize + 1}</span> to{' '}
          <span className="font-semibold text-slate-200">{Math.min(page * pageSize, total_rows)}</span> of{' '}
          <span className="font-semibold text-slate-200">{total_rows.toLocaleString()}</span> entries
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            className="p-1.5 rounded-lg border border-slate-800 bg-slate-950 hover:bg-slate-900 text-slate-300 disabled:opacity-40 disabled:pointer-events-none transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>

          <span className="px-3 py-1 rounded-lg bg-slate-950 border border-slate-800 font-mono text-indigo-300 text-xs">
            {page} / {total_pages}
          </span>

          <button
            onClick={() => setPage(p => Math.min(total_pages, p + 1))}
            disabled={page === total_pages}
            className="p-1.5 rounded-lg border border-slate-800 bg-slate-950 hover:bg-slate-900 text-slate-300 disabled:opacity-40 disabled:pointer-events-none transition-colors"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
