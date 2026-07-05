import React from 'react';
import { 
  Download, 
  FileSpreadsheet, 
  FileText, 
  BarChart, 
  HelpCircle,
  TrendingUp,
  Award
} from 'lucide-react';
import { api } from '../services/api';
import type { Dataset, DatasetVersion } from '../services/api';
import { GlassCard } from '../components/UI/GlassCard';

interface ReportsPageProps {
  activeDataset: Dataset | null;
  activeVersion: DatasetVersion | null;
}

export const ReportsPage: React.FC<ReportsPageProps> = ({ activeDataset, activeVersion }) => {
  
  if (!activeDataset || !activeVersion) {
    return (
      <div className="text-center py-20 text-slate-400 italic">
        Upload a dataset on the Dashboard to export reports.
      </div>
    );
  }

  const handleCsvDownload = () => {
    const url = api.getCSVDownloadUrl(activeDataset.id, activeVersion.version_number);
    window.open(url, '_blank');
  };

  const handlePdfDownload = () => {
    const url = api.getPDFDownloadUrl(activeDataset.id, activeVersion.version_number);
    window.open(url, '_blank');
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="space-y-8 fade-in" id="reports-page-root">
      
      {/* Title */}
      <div>
        <h2 className="text-2xl font-extrabold flex items-center gap-2">
          <Download className="w-6 h-6 text-brand-500" /> Export Reports & Data
        </h2>
        <p className="text-slate-500 dark:text-slate-400">Download the active dataset version or compile a publication-grade PDF report.</p>
      </div>

      {/* Grid of Report Formats */}
      <div className="grid md:grid-cols-2 gap-8">
        
        {/* Cleaned CSV Card */}
        <GlassCard className="flex flex-col justify-between space-y-6 p-8 border-brand-500/10 hover:border-brand-500/25">
          <div className="space-y-4">
            <div className="p-4 bg-brand-500/10 text-brand-500 rounded-2xl w-fit border border-brand-500/20">
              <FileSpreadsheet className="w-8 h-8" />
            </div>

            <div className="space-y-1">
              <h3 className="text-xl font-bold">Cleaned CSV Dataset</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                Download the fully parsed comma-separated file representing the active version. All duplicate rows, missing entries, and outlier adjustments will be baked directly into the cells.
              </p>
            </div>

            <div className="pt-2 grid grid-cols-2 gap-4 text-xs font-semibold text-slate-500 dark:text-slate-400">
              <div className="bg-slate-100/50 dark:bg-slate-900/40 p-2.5 rounded-xl border border-slate-200/50 dark:border-slate-800/30">
                <p className="text-[10px] text-slate-400 uppercase">Version</p>
                <p className="font-extrabold text-slate-700 dark:text-slate-200 mt-0.5">v{activeVersion.version_number}</p>
              </div>
              <div className="bg-slate-100/50 dark:bg-slate-900/40 p-2.5 rounded-xl border border-slate-200/50 dark:border-slate-800/30">
                <p className="text-[10px] text-slate-400 uppercase">Storage Size</p>
                <p className="font-extrabold text-slate-700 dark:text-slate-200 mt-0.5">{formatBytes(activeVersion.file_size)}</p>
              </div>
            </div>
          </div>

          <button
            onClick={handleCsvDownload}
            className="w-full py-4 bg-brand-500 hover:bg-brand-600 text-white rounded-xl font-bold text-sm transition-all flex items-center justify-center gap-2 shadow-lg shadow-brand-500/10 hover:shadow-brand-500/25"
            id="download-csv-btn"
          >
            <Download className="w-4 h-4" /> Download Cleaned CSV
          </button>
        </GlassCard>

        {/* Complete Analytics PDF Card */}
        <GlassCard className="flex flex-col justify-between space-y-6 p-8 border-indigo-500/10 hover:border-indigo-500/25">
          <div className="space-y-4">
            <div className="p-4 bg-indigo-500/10 text-indigo-500 rounded-2xl w-fit border border-indigo-500/20">
              <FileText className="w-8 h-8" />
            </div>

            <div className="space-y-1">
              <h3 className="text-xl font-bold">Comprehensive PDF Analytics Report</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                Compile a detailed document listing the dataset's executive business insights, full transformation logs audit-trail, descriptive tables, and generated distribution/correlation plots.
              </p>
            </div>

            <div className="pt-2 grid grid-cols-2 gap-4 text-xs font-semibold text-slate-500 dark:text-slate-400">
              <div className="bg-slate-100/50 dark:bg-slate-900/40 p-2.5 rounded-xl border border-slate-200/50 dark:border-slate-800/30">
                <p className="text-[10px] text-slate-400 uppercase">Health Rating</p>
                <p className="font-extrabold text-slate-700 dark:text-slate-200 mt-0.5">{activeVersion.quality_score}/100</p>
              </div>
              <div className="bg-slate-100/50 dark:bg-slate-900/40 p-2.5 rounded-xl border border-slate-200/50 dark:border-slate-800/30">
                <p className="text-[10px] text-slate-400 uppercase">Page Layout</p>
                <p className="font-extrabold text-slate-700 dark:text-slate-200 mt-0.5">Letter (Portrait)</p>
              </div>
            </div>
          </div>

          <button
            onClick={handlePdfDownload}
            className="w-full py-4 bg-indigo-500 hover:bg-indigo-600 text-white rounded-xl font-bold text-sm transition-all flex items-center justify-center gap-2 shadow-lg shadow-indigo-500/10 hover:shadow-indigo-500/25"
            id="download-pdf-btn"
          >
            <FileText className="w-4 h-4" /> Download Complete Report (PDF)
          </button>
        </GlassCard>

      </div>

      {/* Integration Guide */}
      <GlassCard className="p-8 space-y-4">
        <h3 className="text-lg font-bold flex items-center gap-2">
          <Award className="w-5 h-5 text-brand-500" /> BI Integration & Downstream Analytics Guide
        </h3>
        
        <div className="grid md:grid-cols-3 gap-6 text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
          <div className="space-y-2">
            <h4 className="font-bold text-slate-700 dark:text-slate-200 flex items-center gap-1.5">
              <span className="w-5 h-5 rounded-full bg-slate-100 dark:bg-slate-900 flex items-center justify-center border border-slate-200 dark:border-slate-800 text-[10px] font-extrabold">1</span>
              Tableau / Power BI
            </h4>
            <p>
              Import the downloaded **Cleaned CSV** directly as a Text File source. Because column data types are clean and missing null cells are imputed, relationships will resolve automatically without manual mapping errors.
            </p>
          </div>

          <div className="space-y-2">
            <h4 className="font-bold text-slate-700 dark:text-slate-200 flex items-center gap-1.5">
              <span className="w-5 h-5 rounded-full bg-slate-100 dark:bg-slate-900 flex items-center justify-center border border-slate-200 dark:border-slate-800 text-[10px] font-extrabold">2</span>
              Python / Jupyter Models
            </h4>
            <p>
              Use `pandas.read_csv('cleaned_dataset_v{activeVersion.version_number}.csv')` in your modeling scripts. Features are normalized, skewed values are flagged, and outlines capped, reducing training convergence times.
            </p>
          </div>

          <div className="space-y-2">
            <h4 className="font-bold text-slate-700 dark:text-slate-200 flex items-center gap-1.5">
              <span className="w-5 h-5 rounded-full bg-slate-100 dark:bg-slate-900 flex items-center justify-center border border-slate-200 dark:border-slate-800 text-[10px] font-extrabold">3</span>
              Audit Trails
            </h4>
            <p>
              Keep the downloaded **PDF Report** as a data governance artifact. It contains a chronological log showing every single cleaning step applied to the dataset, making your analytics pipelines fully explainable.
            </p>
          </div>
        </div>
      </GlassCard>
    </div>
  );
};
