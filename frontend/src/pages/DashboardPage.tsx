/* eslint-disable @typescript-eslint/no-unused-vars */
import React, { useState, useEffect } from 'react';
import { Upload, Database, FileSpreadsheet, ArrowRightLeft, Trash2, CheckCircle2, ChevronRight, Activity, Clock } from 'lucide-react';
import { api } from '../services/api';
import type { Dataset, DatasetVersion, PreviewData } from '../services/api';
import { GlassCard } from '../components/UI/GlassCard';
import confetti from 'canvas-confetti';

interface DashboardPageProps {
  activeDataset: Dataset | null;
  activeVersion: DatasetVersion | null;
  setActiveDataset: (d: Dataset | null) => void;
  setActiveVersion: (v: DatasetVersion | null) => void;
  refreshDatasets: () => Promise<void>;
  datasets: Dataset[];
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  activeDataset,
  activeVersion,
  setActiveDataset,
  setActiveVersion,
  refreshDatasets,
  datasets
}) => {
  const [dragActive, setDragActive] = useState<boolean>(false);
  const [uploading, setUploading] = useState<boolean>(false);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [preview, setPreview] = useState<PreviewData | null>(null);
  const [loadingPreview, setLoadingPreview] = useState<boolean>(false);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const rowsPerPage = 10;

  // Trigger preview fetch when dataset/version changes
  useEffect(() => {
    if (activeDataset && activeVersion) {
      fetchPreview(activeDataset.id, activeVersion.version_number);
    } else {
      setPreview(null);
    }
    setCurrentPage(1);
  }, [activeDataset, activeVersion]);

  const fetchPreview = async (datasetId: number, versionNum: number) => {
    setLoadingPreview(true);
    try {
      const data = await api.getPreview(datasetId, versionNum);
      setPreview(data);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoadingPreview(false);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      await uploadFile(file);
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      await uploadFile(file);
    }
  };

  const uploadFile = async (file: File) => {
    // Basic checks
    if (!file.name.toLowerCase().endsWith('.csv')) {
      setUploadError('Only CSV files are supported.');
      return;
    }
    
    if (file.size > 100 * 1024 * 1024) {
      setUploadError('File size exceeds the 100 MB limit.');
      return;
    }

    setUploadError(null);
    setUploading(true);
    setUploadProgress(10);
    
    // Simulate upload progress
    const interval = setInterval(() => {
      setUploadProgress(prev => {
        if (prev >= 90) {
          clearInterval(interval);
          return 90;
        }
        return prev + 15;
      });
    }, 150);

    try {
      const version = await api.uploadDataset(file);
      setUploadProgress(100);
      clearInterval(interval);
      
      // Load datasets list again
      await refreshDatasets();
      
      // Retrieve full dataset to get complete relations
      const updatedList = await api.listDatasets();
      const loadedDataset = updatedList.find(d => d.id === version.dataset_id);
      
      if (loadedDataset) {
        setActiveDataset(loadedDataset);
        const activeVer = loadedDataset.versions.find(v => v.version_number === version.version_number);
        setActiveVersion(activeVer || version);
      }
      
      // Fun Confetti trigger
      confetti({
        particleCount: 80,
        spread: 60,
        origin: { y: 0.8 }
      });
      
    } catch (err: any) {
      clearInterval(interval);
      setUploadError(err.message || 'Failed to upload dataset.');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (datasetId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm("Are you sure you want to delete this dataset and all its version files?")) return;
    
    try {
      await api.deleteDataset(datasetId);
      if (activeDataset?.id === datasetId) {
        setActiveDataset(null);
        setActiveVersion(null);
      }
      await refreshDatasets();
    } catch (err: any) {
      alert(err.message || 'Failed to delete dataset.');
    }
  };

  const selectDataset = (d: Dataset) => {
    setActiveDataset(d);
    // Auto-select latest version
    const latest = d.versions.reduce((prev, curr) => prev.version_number > curr.version_number ? prev : curr);
    setActiveVersion(latest);
  };

  const handleVersionChange = (versionNum: number) => {
    if (!activeDataset) return;
    const selected = activeDataset.versions.find(v => v.version_number === versionNum);
    if (selected) {
      setActiveVersion(selected);
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getScoreColorClass = (score: number) => {
    if (score >= 80) return 'text-emerald-500 stroke-emerald-500';
    if (score >= 50) return 'text-amber-500 stroke-amber-500';
    return 'text-rose-500 stroke-rose-500';
  };

  // Preview Paginated Rows
  const paginatedData = React.useMemo(() => {
    if (!preview) return [];
    const startIndex = (currentPage - 1) * rowsPerPage;
    return preview.data.slice(startIndex, startIndex + rowsPerPage);
  }, [preview, currentPage]);

  const totalPages = preview ? Math.ceil(preview.data.length / rowsPerPage) : 0;

  return (
    <div className="space-y-8 fade-in" id="dashboard-page-root">
      
      {/* Upload and Selection Panels */}
      <div className="grid lg:grid-cols-3 gap-6">
        
        {/* Upload System (Colspan 2) */}
        <div className="lg:col-span-2">
          <GlassCard className="h-full flex flex-col justify-between space-y-4">
            <div>
              <h2 className="text-xl font-bold">Upload CSV Dataset</h2>
              <p className="text-sm text-slate-500 dark:text-slate-400">Stream clean analysis directly into SQLite local repository (Limit: 100 MB)</p>
            </div>
            
            {/* Dropzone */}
            <div 
              onDragEnter={handleDrag}
              onDragOver={handleDrag}
              onDragLeave={handleDrag}
              onDrop={handleDrop}
              className={`
                relative border-2 border-dashed rounded-xl p-8 flex flex-col items-center justify-center text-center transition-all cursor-pointer min-h-[180px]
                ${dragActive 
                  ? 'border-brand-500 bg-brand-500/5' 
                  : 'border-slate-300 dark:border-slate-800 hover:border-brand-400 hover:bg-slate-50/50 dark:hover:bg-slate-900/30'
                }
              `}
              onClick={() => document.getElementById('csv-file-input')?.click()}
            >
              <input 
                id="csv-file-input"
                type="file" 
                accept=".csv"
                className="hidden" 
                onChange={handleFileChange}
              />
              
              {uploading ? (
                <div className="space-y-3 w-full max-w-[280px]">
                  <Activity className="w-10 h-10 text-brand-500 animate-pulse mx-auto" />
                  <p className="font-semibold text-sm">Processing dataset structure...</p>
                  <div className="w-full bg-slate-200 dark:bg-slate-800 rounded-full h-2">
                    <div 
                      className="bg-brand-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                  <span className="text-xs text-slate-400 font-bold">{uploadProgress}%</span>
                </div>
              ) : (
                <div className="space-y-2">
                  <div className="p-3.5 bg-slate-100 dark:bg-slate-900 rounded-2xl w-fit mx-auto border border-slate-200/50 dark:border-slate-800/50">
                    <Upload className="w-6 h-6 text-slate-500 dark:text-slate-400" />
                  </div>
                  <p className="font-bold text-sm">Drag and drop your CSV file here, or <span className="text-brand-500 dark:text-brand-400 hover:underline">browse</span></p>
                  <p className="text-xs text-slate-400 dark:text-slate-500">Supports standard comma-separated fields with headers</p>
                </div>
              )}
            </div>

            {uploadError && (
              <p className="text-xs font-semibold text-rose-500 px-1.5">{uploadError}</p>
            )}
          </GlassCard>
        </div>

        {/* Dataset History Selection */}
        <div>
          <GlassCard className="h-full flex flex-col justify-between space-y-4">
            <div>
              <h2 className="text-xl font-bold flex items-center gap-2">
                <Database className="w-5 h-5 text-brand-500" /> Analysis History
              </h2>
              <p className="text-sm text-slate-500 dark:text-slate-400">Select or switch active datasets</p>
            </div>

            {/* List */}
            <div className="flex-1 overflow-y-auto max-h-[180px] space-y-2 pr-1">
              {datasets.length === 0 ? (
                <div className="text-center py-6 text-slate-400 dark:text-slate-600 text-xs font-semibold italic">
                  No datasets uploaded yet
                </div>
              ) : (
                datasets.map((d) => {
                  const isActive = activeDataset?.id === d.id;
                  const latestVer = d.versions.reduce((prev, curr) => prev.version_number > curr.version_number ? prev : curr);
                  
                  return (
                    <div
                      key={d.id}
                      onClick={() => selectDataset(d)}
                      className={`
                        flex items-center justify-between p-2.5 rounded-xl border transition-all cursor-pointer text-xs
                        ${isActive 
                          ? 'bg-brand-500/10 border-brand-500/30 text-brand-700 dark:text-brand-400 font-bold shadow-sm' 
                          : 'border-slate-200/50 dark:border-slate-800/40 hover:bg-slate-50 dark:hover:bg-slate-900/60'
                        }
                      `}
                    >
                      <div className="flex items-center gap-2.5 min-w-0">
                        <FileSpreadsheet className={`w-4 h-4 shrink-0 ${isActive ? 'text-brand-500' : 'text-slate-400'}`} />
                        <div className="min-w-0">
                          <p className="truncate font-semibold text-slate-700 dark:text-slate-200" title={d.name}>{d.name}</p>
                          <p className="text-[10px] text-slate-400 mt-0.5">{latestVer.row_count} rows • v{latestVer.version_number}</p>
                        </div>
                      </div>

                      <button
                        onClick={(e) => handleDelete(d.id, e)}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/20 transition-all shrink-0"
                        title="Delete Dataset"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  );
                })
              )}
            </div>
          </GlassCard>
        </div>

      </div>

      {/* Dataset Statistics and Details Grid */}
      {activeDataset && activeVersion && (
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6 fade-in" id="dataset-overview-grid">
          
          {/* Row Count */}
          <GlassCard className="flex items-center justify-between">
            <div className="space-y-1.5">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Total Rows</span>
              <p className="text-3xl font-extrabold text-slate-800 dark:text-white">{activeVersion.row_count.toLocaleString()}</p>
            </div>
            <div className="p-3 bg-brand-500/10 rounded-2xl text-brand-500 border border-brand-500/20">
              <FileSpreadsheet className="w-6 h-6" />
            </div>
          </GlassCard>

          {/* Column Count */}
          <GlassCard className="flex items-center justify-between">
            <div className="space-y-1.5">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Columns count</span>
              <p className="text-3xl font-extrabold text-slate-800 dark:text-white">{activeVersion.col_count}</p>
            </div>
            <div className="p-3 bg-indigo-500/10 rounded-2xl text-indigo-500 border border-indigo-500/20">
              <Clock className="w-6 h-6" />
            </div>
          </GlassCard>

          {/* File Size */}
          <GlassCard className="flex items-center justify-between">
            <div className="space-y-1.5">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">File Storage</span>
              <p className="text-3xl font-extrabold text-slate-800 dark:text-white">{formatBytes(activeVersion.file_size)}</p>
            </div>
            <div className="p-3 bg-violet-500/10 rounded-2xl text-violet-500 border border-violet-500/20">
              <Database className="w-6 h-6" />
            </div>
          </GlassCard>

          {/* Quality Score gauge */}
          <GlassCard className="flex items-center gap-4 py-4 justify-between">
            <div className="space-y-1">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Health Index</span>
              <p className="text-2xl font-extrabold text-slate-800 dark:text-white">{activeVersion.quality_score}/100</p>
              <span className="text-[10px] text-slate-400 leading-none">Overall data completeness</span>
            </div>
            
            {/* Circular Gauge */}
            <div className="relative w-16 h-16 shrink-0">
              <svg className="w-full h-full transform -rotate-90">
                <circle
                  cx="32"
                  cy="32"
                  r="26"
                  className="stroke-slate-200 dark:stroke-slate-800 fill-none"
                  strokeWidth="5.5"
                />
                <circle
                  cx="32"
                  cy="32"
                  r="26"
                  className={`fill-none ${getScoreColorClass(activeVersion.quality_score)}`}
                  strokeWidth="5.5"
                  strokeDasharray={163.3}
                  strokeDashoffset={163.3 - (163.3 * activeVersion.quality_score) / 100}
                  strokeLinecap="round"
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center text-xs font-extrabold">
                {Math.round(activeVersion.quality_score)}%
              </div>
            </div>
          </GlassCard>

        </div>
      )}

      {/* Dataset Versioning and Preview */}
      {activeDataset && activeVersion && (
        <div className="grid lg:grid-cols-4 gap-6 items-start fade-in">
          
          {/* Version Checklist (Left Sidebar, col 1) */}
          <div>
            <GlassCard className="space-y-4">
              <h3 className="font-bold text-sm flex items-center gap-2">
                <Clock className="w-4 h-4 text-brand-500" /> Version History
              </h3>
              
              <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1">
                {activeDataset.versions.map((v) => {
                  const isCurrent = v.version_number === activeVersion.version_number;
                  return (
                    <div
                      key={v.id}
                      onClick={() => handleVersionChange(v.version_number)}
                      className={`
                        w-full text-left p-3 rounded-xl border transition-all cursor-pointer flex flex-col gap-1
                        ${isCurrent 
                          ? 'border-brand-500/40 bg-brand-500/5 text-brand-700 dark:text-brand-400 font-bold' 
                          : 'border-slate-200/50 dark:border-slate-800/40 hover:bg-slate-50 dark:hover:bg-slate-900/60'
                        }
                      `}
                    >
                      <div className="flex justify-between items-center text-xs">
                        <span className="font-extrabold">Version v{v.version_number}</span>
                        <span className="text-[10px] text-slate-400 font-medium">
                          {new Date(v.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      <p className="text-[10px] text-slate-500 dark:text-slate-400 truncate leading-relaxed">
                        {v.change_summary}
                      </p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-[9px] px-1.5 py-0.2 bg-slate-200 dark:bg-slate-800 text-slate-500 rounded-md font-semibold">
                          {v.row_count} rows
                        </span>
                        <span className="text-[9px] px-1.5 py-0.2 bg-slate-200 dark:bg-slate-800 text-slate-500 rounded-md font-semibold">
                          Health: {v.quality_score}%
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </GlassCard>
          </div>

          {/* Large Dataset Table (Right, col 3) */}
          <div className="lg:col-span-3">
            <GlassCard className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-bold text-base flex items-center gap-2">
                    <FileSpreadsheet className="w-5 h-5 text-indigo-500" /> Interactive Profile Table Preview
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400">Displaying first {preview?.data.length || 0} loaded records. Inspect formats and data types.</p>
                </div>
              </div>

              {loadingPreview ? (
                <div className="h-64 flex flex-col items-center justify-center text-slate-400 text-sm">
                  <Activity className="w-8 h-8 text-brand-500 animate-spin mb-2" />
                  Generating profile preview...
                </div>
              ) : preview ? (
                <div className="space-y-4">
                  {/* Table Wrapper */}
                  <div className="overflow-x-auto border border-slate-200 dark:border-slate-800/80 rounded-xl">
                    <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-800/80 text-xs">
                      <thead className="bg-slate-100/50 dark:bg-slate-900/60">
                        <tr>
                          {preview.headers.map((header) => {
                            const dtype = preview.types[header] || 'text';
                            const nullCount = preview.null_counts[header] ?? 0;
                            const totalRows = preview.row_count;
                            const missingPct = totalRows > 0 ? (nullCount / totalRows) * 100 : 0;
                            
                            return (
                              <th 
                                key={header} 
                                className="px-4 py-3.5 text-left font-bold text-slate-700 dark:text-slate-300 border-r border-slate-200 dark:border-slate-800 last:border-0"
                              >
                                <div className="space-y-1">
                                  <div className="truncate text-sm font-extrabold" title={header}>{header}</div>
                                  <div className="flex items-center justify-between gap-2 text-[9px] font-semibold tracking-wider uppercase text-slate-400">
                                    <span className="bg-slate-200 dark:bg-slate-800 px-1.5 py-0.2 rounded-md font-bold text-[8px] text-brand-600 dark:text-brand-400">
                                      {dtype.includes('float') || dtype.includes('int') || dtype === 'numeric' ? 'NUM' : dtype.includes('datetime') ? 'DATE' : 'STR'}
                                    </span>
                                    {nullCount > 0 ? (
                                      <span className="text-rose-500" title={`${nullCount} missing rows`}>
                                        {missingPct.toFixed(0)}% Null
                                      </span>
                                    ) : (
                                      <span className="text-emerald-500">100% Clean</span>
                                    )}
                                  </div>
                                </div>
                              </th>
                            );
                          })}
                        </tr>
                      </thead>
                      
                      <tbody className="divide-y divide-slate-100 dark:divide-slate-800/40 bg-white/30 dark:bg-transparent">
                        {paginatedData.map((row, idx) => (
                          <tr key={idx} className="hover:bg-slate-50/50 dark:hover:bg-slate-900/20">
                            {preview.headers.map((header) => (
                              <td 
                                key={header} 
                                className="px-4 py-2.5 truncate max-w-[150px] border-r border-slate-100 dark:border-slate-900/60 last:border-0 text-slate-600 dark:text-slate-300"
                              >
                                {row[header] === null || row[header] === undefined ? (
                                  <span className="text-rose-500 font-semibold italic text-[10px] px-1 py-0.5 rounded bg-rose-500/10">NULL</span>
                                ) : (
                                  String(row[header])
                                )}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* Pagination footer */}
                  <div className="flex items-center justify-between text-xs px-2">
                    <span className="text-slate-400 font-semibold">
                      Showing {((currentPage - 1) * rowsPerPage) + 1} to {Math.min(currentPage * rowsPerPage, preview.data.length)} of {preview.data.length} preview rows
                    </span>

                    <div className="flex gap-2">
                      <button
                        onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                        disabled={currentPage === 1}
                        className="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-900 font-semibold disabled:opacity-40"
                      >
                        Prev
                      </button>
                      <button
                        onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                        disabled={currentPage === totalPages}
                        className="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-900 font-semibold disabled:opacity-40"
                      >
                        Next
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="h-64 flex items-center justify-center text-slate-400 text-xs italic">
                  Upload a dataset to generate visual previews
                </div>
              )}
            </GlassCard>
          </div>

        </div>
      )}
    </div>
  );
};
