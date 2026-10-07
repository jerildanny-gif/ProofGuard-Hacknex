import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import StageTracker from './components/StageTracker';
import DatasetUploader from './components/DatasetUploader';
import SampleDatasetPicker from './components/SampleDatasetPicker';
import DatasetStatsOverview from './components/DatasetStatsOverview';
import ColumnInspector from './components/ColumnInspector';
import DatasetPreviewTable from './components/DatasetPreviewTable';
import AnomalyAlerts from './components/AnomalyAlerts';
import ProofAnalyst from './components/ProofAnalyst';
import DataForensics from './components/DataForensics';
import { 
  checkBackendHealth, 
  getAllDatasets, 
  getSampleDatasets, 
  getDatasetDetails 
} from './services/api';
import { 
  BarChart3, 
  Columns3, 
  Table, 
  ShieldAlert, 
  Upload, 
  Sparkles, 
  RefreshCw,
  FolderOpen,
  Code2,
  FileSearch
} from 'lucide-react';


export default function App() {
  const [backendStatus, setBackendStatus] = useState(null);
  const [datasets, setDatasets] = useState([]);
  const [samples, setSamples] = useState([]);
  const [activeDatasetId, setActiveDatasetId] = useState(null);
  const [datasetDetails, setDatasetDetails] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('analyst');
  const [showUploader, setShowUploader] = useState(false);

  // Poll / check backend health & initial load
  const loadInitialData = async () => {
    try {
      setLoading(true);
      const health = await checkBackendHealth();
      setBackendStatus(health);

      const [sampleList, datasetList] = await Promise.all([
        getSampleDatasets().catch(() => []),
        getAllDatasets().catch(() => [])
      ]);

      setSamples(sampleList);
      setDatasets(datasetList);

      // Default to sample-sales or the first dataset
      if (datasetList && datasetList.length > 0) {
        const defaultId = datasetList.find(d => d.id === 'sample-sales')?.id || datasetList[0].id;
        setActiveDatasetId(defaultId);
        await loadDatasetDetails(defaultId);
      }
    } catch (err) {
      console.error('Initial load failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadDatasetDetails = async (id) => {
    try {
      setLoading(true);
      setActiveDatasetId(id);
      const details = await getDatasetDetails(id);
      setDatasetDetails(details);
    } catch (err) {
      console.error('Failed to load dataset details:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInitialData();
  }, []);

  const handleDatasetLoaded = async (newDatasetId) => {
    // Refresh dataset list and switch to the uploaded one
    const updated = await getAllDatasets();
    setDatasets(updated);
    setActiveDatasetId(newDatasetId);
    await loadDatasetDetails(newDatasetId);
    setShowUploader(false);
    setActiveTab('overview');
  };

  const activeMeta = datasetDetails?.meta;
  const activeHealth = datasetDetails?.health;
  const activeColumns = datasetDetails?.columns;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-indigo-500 selection:text-white">
      {/* Top Navbar */}
      <Navbar backendStatus={backendStatus} activeDataset={activeMeta} />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        
        {/* Stage 1 Foundation Architecture Banner */}
        <StageTracker />

        {/* Action Bar: Active Dataset Switcher & Upload Button */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 backdrop-blur-md">
          {/* Dataset Switcher Dropdown */}
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
              <FolderOpen className="w-5 h-5" />
            </div>
            <div>
              <label className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold block">
                Active Ingested Dataset
              </label>
              <select
                value={activeDatasetId || ''}
                onChange={(e) => loadDatasetDetails(e.target.value)}
                className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-white font-medium focus:outline-none focus:border-indigo-500 mt-0.5 cursor-pointer"
              >
                {datasets.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name} {d.is_sample ? '(Sample Trap)' : '(Custom Upload)'} — {d.row_count} rows
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Upload and Sample Action buttons */}
          <div className="flex items-center space-x-2.5">
            <button
              onClick={() => setShowUploader(!showUploader)}
              className={`flex items-center space-x-2 px-3.5 py-2 rounded-xl text-xs font-semibold transition-all border ${
                showUploader
                  ? 'bg-indigo-600 text-white border-indigo-500 shadow-md shadow-indigo-600/30'
                  : 'bg-slate-900 hover:bg-slate-800 text-slate-200 border-slate-700/80'
              }`}
            >
              <Upload className="w-4 h-4" />
              <span>{showUploader ? 'Close Upload Panel' : 'Upload CSV / XLSX'}</span>
            </button>

            <button
              onClick={loadInitialData}
              title="Refresh datasets"
              className="p-2 rounded-xl border border-slate-800 bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Ingestion & Presets Collapsible Drawer */}
        {showUploader && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 animate-in fade-in duration-200">
            <DatasetUploader onDatasetLoaded={handleDatasetLoaded} />
            <SampleDatasetPicker
              samples={samples}
              activeId={activeDatasetId}
              onSelectSample={loadDatasetDetails}
            />
          </div>
        )}

        {/* Quick Sample Selector if uploader closed */}
        {!showUploader && samples.length > 0 && (
          <div className="flex items-center space-x-2 overflow-x-auto pb-1 text-xs">
            <span className="text-slate-500 text-xs flex items-center space-x-1 flex-shrink-0">
              <Sparkles className="w-3.5 h-3.5 text-amber-400" />
              <span>Quick Presets:</span>
            </span>
            {samples.map((s) => (
              <button
                key={s.id}
                onClick={() => loadDatasetDetails(s.id)}
                className={`flex-shrink-0 px-2.5 py-1 rounded-lg border text-xs font-medium transition-colors ${
                  activeDatasetId === s.id
                    ? 'bg-indigo-500/20 text-indigo-300 border-indigo-500/40 font-semibold'
                    : 'bg-slate-900/50 text-slate-400 border-slate-800 hover:text-slate-200 hover:bg-slate-900'
                }`}
              >
                {s.title}
              </button>
            ))}
          </div>
        )}

        {/* Tab Navigation */}
        <div className="flex items-center space-x-1 border-b border-slate-800 overflow-x-auto">
          <button
            onClick={() => setActiveTab('analyst')}
            className={`flex items-center space-x-2 px-4 py-2.5 text-xs font-medium border-b-2 transition-all flex-shrink-0 ${
              activeTab === 'analyst'
                ? 'border-indigo-500 text-indigo-400 bg-indigo-500/10 font-semibold'
                : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/40'
            }`}
          >
            <Sparkles className="w-4 h-4 text-indigo-400" />
            <span>Proof-Carrying Analyst</span>
            <span className="text-[9px] px-1.5 py-0.2 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-bold uppercase tracking-wider">
              Stage 2 Verified
            </span>
          </button>

          <button
            onClick={() => setActiveTab('forensics')}
            className={`flex items-center space-x-2 px-4 py-2.5 text-xs font-medium border-b-2 transition-all flex-shrink-0 ${
              activeTab === 'forensics'
                ? 'border-amber-500 text-amber-300 bg-amber-500/10 font-semibold'
                : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/40'
            }`}
          >
            <FileSearch className="w-4 h-4 text-amber-400" />
            <span>Data Forensics</span>
            <span className="text-[9px] px-1.5 py-0.2 rounded bg-amber-500 text-slate-950 font-bold uppercase tracking-wider">
              Stage 3 Active
            </span>
          </button>

          <button
            onClick={() => setActiveTab('overview')}
            className={`flex items-center space-x-2 px-4 py-2.5 text-xs font-medium border-b-2 transition-all flex-shrink-0 ${
              activeTab === 'overview'
                ? 'border-indigo-500 text-indigo-400 bg-indigo-500/5 font-semibold'
                : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/40'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            <span>Dataset Overview & Stats</span>
          </button>

          <button
            onClick={() => setActiveTab('columns')}
            className={`flex items-center space-x-2 px-4 py-2.5 text-xs font-medium border-b-2 transition-all flex-shrink-0 ${
              activeTab === 'columns'
                ? 'border-indigo-500 text-indigo-400 bg-indigo-500/5 font-semibold'
                : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/40'
            }`}
          >
            <Columns3 className="w-4 h-4" />
            <span>Column Inspector ({activeColumns ? activeColumns.length : 0})</span>
          </button>

          <button
            onClick={() => setActiveTab('preview')}
            className={`flex items-center space-x-2 px-4 py-2.5 text-xs font-medium border-b-2 transition-all flex-shrink-0 ${
              activeTab === 'preview'
                ? 'border-indigo-500 text-indigo-400 bg-indigo-500/5 font-semibold'
                : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/40'
            }`}
          >
            <Table className="w-4 h-4" />
            <span>Records Explorer (Preview)</span>
          </button>

          <button
            onClick={() => setActiveTab('guardrails')}
            className={`flex items-center space-x-2 px-4 py-2.5 text-xs font-medium border-b-2 transition-all flex-shrink-0 ${
              activeTab === 'guardrails'
                ? 'border-indigo-500 text-indigo-400 bg-indigo-500/5 font-semibold'
                : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/40'
            }`}
          >
            <ShieldAlert className="w-4 h-4" />
            <span>Guardrail & Trap Alerts</span>
            {activeHealth?.detected_issues?.length > 0 && (
              <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-rose-500 text-white font-bold">
                {activeHealth.detected_issues.length}
              </span>
            )}
          </button>
        </div>

        {/* Tab Content Display */}
        {loading && !datasetDetails ? (
          <div className="p-16 text-center">
            <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
            <p className="text-sm text-slate-400">Loading dataset statistics and quality metrics...</p>
          </div>
        ) : (
          <div className="space-y-6">
            {activeTab === 'analyst' && (
              <ProofAnalyst
                activeDataset={activeMeta}
                datasets={datasets}
              />
            )}

            {activeTab === 'forensics' && (
              <DataForensics
                activeDataset={activeMeta}
                onNavigateToAnalyst={() => setActiveTab('analyst')}
              />
            )}

            {activeTab === 'overview' && (
              <div className="space-y-6">
                <DatasetStatsOverview
                  meta={activeMeta}
                  health={activeHealth}
                  columns={activeColumns}
                />
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <AnomalyAlerts health={activeHealth} />
                  <ColumnInspector columns={activeColumns} />
                </div>
              </div>
            )}

            {activeTab === 'columns' && (
              <ColumnInspector columns={activeColumns} />
            )}

            {activeTab === 'preview' && (
              <DatasetPreviewTable
                datasetId={activeDatasetId}
                totalRows={activeMeta?.row_count || 0}
              />
            )}

            {activeTab === 'guardrails' && (
              <AnomalyAlerts health={activeHealth} />
            )}
          </div>
        )}

      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950/80 py-6 mt-12 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center space-x-2">
            <span className="font-bold text-slate-400">PROOFGUARD</span>
            <span>—</span>
            <span>AI Data Analysis with an Independent Trust & Verification Layer</span>
          </div>
          <div className="flex items-center space-x-4 text-slate-500 text-[11px] font-mono">
            <span>Challenge: HNX26PSI08</span>
            <span>•</span>
          <span>Stage 1, 2 & 3 Complete • Stage 4 Active (Trust Layer)</span>
          </div>
        </div>
      </footer>

    </div>
  );
}
