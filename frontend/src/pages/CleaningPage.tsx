/* eslint-disable @typescript-eslint/no-unused-vars */
import React, { useState, useEffect } from 'react';
import { 
  Wand2, 
  HelpCircle, 
  Trash2, 
  RefreshCw, 
  Hash, 
  Type, 
  Calendar, 
  Check, 
  RotateCcw,
  CheckCircle,
  AlertCircle
} from 'lucide-react';
import { api } from '../services/api';
import type { Dataset, DatasetVersion } from '../services/api';
import { GlassCard } from '../components/UI/GlassCard';

interface CleaningPageProps {
  activeDataset: Dataset | null;
  activeVersion: DatasetVersion | null;
  setActiveDataset: (d: Dataset | null) => void;
  setActiveVersion: (v: DatasetVersion | null) => void;
  refreshDatasets: () => Promise<void>;
}

export const CleaningPage: React.FC<CleaningPageProps> = ({
  activeDataset,
  activeVersion,
  setActiveDataset,
  setActiveVersion,
  refreshDatasets
}) => {
  const [columns, setColumns] = useState<string[]>([]);
  const [cleaningStatus, setCleaningStatus] = useState<{ type: 'success' | 'error' | null; message: string }>({ type: null, message: '' });
  const [applying, setApplying] = useState<boolean>(false);

  // States for forms
  const [imputeCol, setImputeCol] = useState<string>('');
  const [imputeStrategy, setImputeStrategy] = useState<string>('mean');

  const [castCol, setCastCol] = useState<string>('');
  const [castType, setCastType] = useState<string>('numeric');
  const [dateFormat, setDateFormat] = useState<string>('%Y-%m-%d');

  const [outlierCol, setOutlierCol] = useState<string>('');
  const [outlierMethod, setOutlierMethod] = useState<string>('iqr');
  const [outlierStrategy, setOutlierStrategy] = useState<string>('cap');
  const [outlierThresh, setOutlierThresh] = useState<number>(3.0);

  const [textCol, setTextCol] = useState<string>('');
  const [textCasing, setTextCasing] = useState<string>('lower');
  const [textSpaces, setTextSpaces] = useState<boolean>(true);
  const [textSpecial, setTextSpecial] = useState<boolean>(false);

  const [colOpAction, setColOpAction] = useState<'rename' | 'delete' | 'create'>('rename');
  const [colOpTarget, setColOpTarget] = useState<string>('');
  const [colOpNewName, setColOpNewName] = useState<string>('');
  const [colOpFormula, setColOpFormula] = useState<string>('');

  useEffect(() => {
    if (activeDataset && activeVersion) {
      loadColumns();
    }
  }, [activeDataset, activeVersion]);

  const loadColumns = async () => {
    if (!activeDataset || !activeVersion) return;
    try {
      const preview = await api.getPreview(activeDataset.id, activeVersion.version_number);
      setColumns(preview.headers);
      if (preview.headers.length > 0) {
        setImputeCol(preview.headers[0]);
        setCastCol(preview.headers[0]);
        setOutlierCol(preview.headers[0]);
        setTextCol(preview.headers[0]);
        setColOpTarget(preview.headers[0]);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleCleanResponse = async (newVersion: DatasetVersion, actionSummary: string) => {
    setCleaningStatus({
      type: 'success',
      message: `Operation succeeded! New version v${newVersion.version_number} saved: ${actionSummary}`
    });
    
    // Refresh parent state
    await refreshDatasets();
    
    // Re-fetch parent datasets structure
    const updatedList = await api.listDatasets();
    const updatedDataset = updatedList.find(d => d.id === activeDataset?.id);
    if (updatedDataset) {
      setActiveDataset(updatedDataset);
      const versionObj = updatedDataset.versions.find(v => v.version_number === newVersion.version_number);
      setActiveVersion(versionObj || newVersion);
    }
  };

  const handleCleanError = (err: any) => {
    setCleaningStatus({
      type: 'error',
      message: err.message || 'Operation failed. Verify column data types and inputs.'
    });
  };

  const applyImputation = async () => {
    if (!activeDataset || !imputeCol) return;
    setApplying(true);
    setCleaningStatus({ type: null, message: '' });
    try {
      const res = await api.imputeMissing(activeDataset.id, imputeCol, imputeStrategy);
      await handleCleanResponse(res, `Imputed missing values in ${imputeCol} via ${imputeStrategy}`);
    } catch (err: any) {
      handleCleanError(err);
    } finally {
      setApplying(false);
    }
  };

  const applyRemoveDuplicates = async () => {
    if (!activeDataset) return;
    setApplying(true);
    setCleaningStatus({ type: null, message: '' });
    try {
      const res = await api.removeDuplicates(activeDataset.id);
      await handleCleanResponse(res, `Dropped duplicate rows`);
    } catch (err: any) {
      handleCleanError(err);
    } finally {
      setApplying(false);
    }
  };

  const applyTypeCast = async () => {
    if (!activeDataset || !castCol) return;
    setApplying(true);
    setCleaningStatus({ type: null, message: '' });
    try {
      const res = await api.typeCorrection(activeDataset.id, castCol, castType, castType === 'datetime' ? dateFormat : undefined);
      await handleCleanResponse(res, `Casted datatype of ${castCol} to ${castType}`);
    } catch (err: any) {
      handleCleanError(err);
    } finally {
      setApplying(false);
    }
  };

  const applyOutlierHandling = async () => {
    if (!activeDataset || !outlierCol) return;
    setApplying(true);
    setCleaningStatus({ type: null, message: '' });
    try {
      const res = await api.handleOutliers(activeDataset.id, outlierCol, outlierMethod, outlierStrategy, outlierThresh);
      await handleCleanResponse(res, `Applied outlier limits on ${outlierCol} (${outlierStrategy})`);
    } catch (err: any) {
      handleCleanError(err);
    } finally {
      setApplying(false);
    }
  };

  const applyTextCleaning = async () => {
    if (!activeDataset || !textCol) return;
    setApplying(true);
    setCleaningStatus({ type: null, message: '' });
    try {
      const res = await api.cleanText(activeDataset.id, textCol, {
        remove_extra_spaces: textSpaces,
        casing: textCasing || undefined,
        remove_special_chars: textSpecial
      });
      await handleCleanResponse(res, `Sanitized text columns in ${textCol}`);
    } catch (err: any) {
      handleCleanError(err);
    } finally {
      setApplying(false);
    }
  };

  const applyColumnOp = async () => {
    if (!activeDataset) return;
    setApplying(true);
    setCleaningStatus({ type: null, message: '' });
    try {
      const res = await api.columnOp(
        activeDataset.id,
        colOpAction,
        colOpAction === 'create' ? colOpNewName : colOpTarget,
        colOpAction === 'rename' ? colOpNewName : undefined,
        colOpAction === 'create' ? colOpFormula : undefined
      );
      await handleCleanResponse(res, `${colOpAction.toUpperCase()} column action completed`);
      setColOpNewName('');
      setColOpFormula('');
    } catch (err: any) {
      handleCleanError(err);
    } finally {
      setApplying(false);
    }
  };

  if (!activeDataset || !activeVersion) {
    return (
      <div className="text-center py-20 text-slate-400 italic">
        Upload a dataset on the Dashboard to access the Interactive Cleaning Workstation.
      </div>
    );
  }

  return (
    <div className="space-y-8 fade-in" id="cleaning-page-root">
      
      {/* Page Title & Active Status */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-extrabold flex items-center gap-2">
            <Wand2 className="w-6 h-6 text-brand-500" /> Interactive Cleaning Workstation
          </h2>
          <p className="text-slate-500 dark:text-slate-400">Perform mathematical and statistical transformations on the active dataset version.</p>
        </div>
      </div>

      {/* Cleaning Operation Status Alerts */}
      {cleaningStatus.type && (
        <div 
          className={`
            p-4 rounded-xl flex items-start gap-3 border text-xs font-semibold
            ${cleaningStatus.type === 'success' 
              ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/25' 
              : 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/25'
            }
          `}
          id="cleaning-status-alert"
        >
          {cleaningStatus.type === 'success' ? <CheckCircle className="w-5 h-5 shrink-0" /> : <AlertCircle className="w-5 h-5 shrink-0" />}
          <div>
            <p className="font-extrabold uppercase tracking-wider">{cleaningStatus.type === 'success' ? 'Success' : 'Error Occurred'}</p>
            <p className="mt-1 leading-relaxed">{cleaningStatus.message}</p>
          </div>
        </div>
      )}

      {/* Workstation Grid layout */}
      <div className="grid lg:grid-cols-3 gap-8">
        
        {/* Cleaning Forms (Left & Center columns, span 2) */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Form Rows grouped as small cards */}
          <div className="grid md:grid-cols-2 gap-6">
            
            {/* Missing values imputation */}
            <GlassCard className="flex flex-col justify-between space-y-4">
              <div className="space-y-1">
                <h4 className="font-extrabold text-sm text-slate-800 dark:text-slate-200">A. Handle Missing Values</h4>
                <p className="text-[10px] text-slate-400">Fill blank cells using statistical indicators or drop values.</p>
              </div>

              <div className="space-y-3">
                <div className="flex flex-col gap-1">
                  <label className="text-[10px] font-bold text-slate-400 uppercase">Select Column</label>
                  <select 
                    value={imputeCol} 
                    onChange={(e) => setImputeCol(e.target.value)}
                    className="glass-input px-3 py-2 text-xs"
                  >
                    {columns.map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                </div>

                <div className="flex flex-col gap-1">
                  <label className="text-[10px] font-bold text-slate-400 uppercase">Imputation Strategy</label>
                  <select 
                    value={imputeStrategy} 
                    onChange={(e) => setImputeStrategy(e.target.value)}
                    className="glass-input px-3 py-2 text-xs"
                  >
                    <option value="mean">Mean Imputation (Numerical only)</option>
                    <option value="median">Median Imputation (Numerical only)</option>
                    <option value="mode">Mode Imputation (Frequent value)</option>
                    <option value="ffill">Forward Fill (Carry forward)</option>
                    <option value="bfill">Backward Fill (Carry backward)</option>
                    <option value="drop_rows">Drop Null Rows</option>
                    <option value="drop_col">Drop Null Column</option>
                  </select>
                </div>
              </div>

              <button
                onClick={applyImputation}
                disabled={applying}
                className="w-full mt-2 py-2 bg-brand-500 hover:bg-brand-600 text-white rounded-xl text-xs font-bold transition-all disabled:opacity-40"
              >
                Apply Imputation
              </button>
            </GlassCard>

            {/* Outlier Detection Form */}
            <GlassCard className="flex flex-col justify-between space-y-4">
              <div className="space-y-1">
                <h4 className="font-extrabold text-sm text-slate-800 dark:text-slate-200">B. Outlier Management</h4>
                <p className="text-[10px] text-slate-400">Detect anomalies using IQR or Z-score boundaries.</p>
              </div>

              <div className="space-y-3">
                <div className="flex flex-col gap-1">
                  <label className="text-[10px] font-bold text-slate-400 uppercase">Select Column</label>
                  <select 
                    value={outlierCol} 
                    onChange={(e) => setOutlierCol(e.target.value)}
                    className="glass-input px-3 py-2 text-xs"
                  >
                    {columns.map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="flex flex-col gap-1">
                    <label className="text-[10px] font-bold text-slate-400 uppercase">Method</label>
                    <select 
                      value={outlierMethod} 
                      onChange={(e) => setOutlierMethod(e.target.value)}
                      className="glass-input px-3 py-2 text-xs"
                    >
                      <option value="iqr">IQR Bounds</option>
                      <option value="zscore">Z-Score</option>
                    </select>
                  </div>
                  <div className="flex flex-col gap-1">
                    <label className="text-[10px] font-bold text-slate-400 uppercase">Action</label>
                    <select 
                      value={outlierStrategy} 
                      onChange={(e) => setOutlierStrategy(e.target.value)}
                      className="glass-input px-3 py-2 text-xs"
                    >
                      <option value="cap">Cap Outliers</option>
                      <option value="remove">Remove Rows</option>
                    </select>
                  </div>
                </div>

                <div className="flex flex-col gap-1">
                  <div className="flex justify-between items-center text-[10px] font-bold text-slate-400 uppercase">
                    <span>Threshold Limit</span>
                    <span>{outlierThresh.toFixed(1)}</span>
                  </div>
                  <input
                    type="range"
                    min="1.0"
                    max="5.0"
                    step="0.5"
                    value={outlierThresh}
                    onChange={(e) => setOutlierThresh(parseFloat(e.target.value))}
                    className="h-1 bg-slate-200 dark:bg-slate-800 rounded-lg appearance-none cursor-pointer accent-brand-500"
                  />
                </div>
              </div>

              <button
                onClick={applyOutlierHandling}
                disabled={applying}
                className="w-full mt-2 py-2 bg-brand-500 hover:bg-brand-600 text-white rounded-xl text-xs font-bold transition-all disabled:opacity-40"
              >
                Restrict Outliers
              </button>
            </GlassCard>

            {/* Data Type Conversions */}
            <GlassCard className="flex flex-col justify-between space-y-4">
              <div className="space-y-1">
                <h4 className="font-extrabold text-sm text-slate-800 dark:text-slate-200">C. Data Type Cast</h4>
                <p className="text-[10px] text-slate-400">Reformat standard columns into mathematical equivalents.</p>
              </div>

              <div className="space-y-3">
                <div className="flex flex-col gap-1">
                  <label className="text-[10px] font-bold text-slate-400 uppercase">Select Column</label>
                  <select 
                    value={castCol} 
                    onChange={(e) => setCastCol(e.target.value)}
                    className="glass-input px-3 py-2 text-xs"
                  >
                    {columns.map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                </div>

                <div className="flex flex-col gap-1">
                  <label className="text-[10px] font-bold text-slate-400 uppercase">Convert Type To</label>
                  <select 
                    value={castType} 
                    onChange={(e) => setCastType(e.target.value)}
                    className="glass-input px-3 py-2 text-xs"
                  >
                    <option value="numeric">Numerical (Float/Int)</option>
                    <option value="datetime">Datetime (Time stamp)</option>
                    <option value="categorical">Categorical (Enum/Group)</option>
                    <option value="text">Text (String)</option>
                  </select>
                </div>

                {castType === 'datetime' && (
                  <div className="flex flex-col gap-1">
                    <label className="text-[10px] font-bold text-slate-400 uppercase">Date Format Parser</label>
                    <input 
                      type="text" 
                      value={dateFormat}
                      onChange={(e) => setDateFormat(e.target.value)}
                      placeholder="%Y-%m-%d"
                      className="glass-input px-3 py-2 text-xs font-mono"
                    />
                  </div>
                )}
              </div>

              <button
                onClick={applyTypeCast}
                disabled={applying}
                className="w-full mt-2 py-2 bg-brand-500 hover:bg-brand-600 text-white rounded-xl text-xs font-bold transition-all disabled:opacity-40"
              >
                Convert Type
              </button>
            </GlassCard>

            {/* Text Sanitisers */}
            <GlassCard className="flex flex-col justify-between space-y-4">
              <div className="space-y-1">
                <h4 className="font-extrabold text-sm text-slate-800 dark:text-slate-200">D. Text Standardisation</h4>
                <p className="text-[10px] text-slate-400">Trim extra spaces, format casings, clean signs.</p>
              </div>

              <div className="space-y-3">
                <div className="flex flex-col gap-1">
                  <label className="text-[10px] font-bold text-slate-400 uppercase">Select Column</label>
                  <select 
                    value={textCol} 
                    onChange={(e) => setTextCol(e.target.value)}
                    className="glass-input px-3 py-2 text-xs"
                  >
                    {columns.map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                </div>

                <div className="flex flex-col gap-1">
                  <label className="text-[10px] font-bold text-slate-400 uppercase">Apply Capitalisation</label>
                  <select 
                    value={textCasing} 
                    onChange={(e) => setTextCasing(e.target.value)}
                    className="glass-input px-3 py-2 text-xs"
                  >
                    <option value="none">No casing modification</option>
                    <option value="lower">lower case (lowercase)</option>
                    <option value="upper">UPPER CASE (UPPERCASE)</option>
                    <option value="title">Title Case (Titlecase)</option>
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-4 pt-1">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input 
                      type="checkbox" 
                      checked={textSpaces} 
                      onChange={(e) => setTextSpaces(e.target.checked)}
                      className="rounded border-slate-300 text-brand-500 focus:ring-brand-500" 
                    />
                    <span className="text-[10px] font-bold text-slate-500">Trim spaces</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input 
                      type="checkbox" 
                      checked={textSpecial} 
                      onChange={(e) => setTextSpecial(e.target.checked)}
                      className="rounded border-slate-300 text-brand-500 focus:ring-brand-500" 
                    />
                    <span className="text-[10px] font-bold text-slate-500">Strip Special</span>
                  </label>
                </div>
              </div>

              <button
                onClick={applyTextCleaning}
                disabled={applying}
                className="w-full mt-2 py-2 bg-brand-500 hover:bg-brand-600 text-white rounded-xl text-xs font-bold transition-all disabled:opacity-40"
              >
                Clean Text
              </button>
            </GlassCard>

          </div>

          {/* Duplicates & Column Operations (Wide layout card) */}
          <div className="grid md:grid-cols-3 gap-6">
            
            {/* Duplicates Removal (col 1) */}
            <GlassCard className="flex flex-col justify-between space-y-4">
              <div className="space-y-1">
                <h4 className="font-extrabold text-sm text-slate-800 dark:text-slate-200">E. Duplicate Handlers</h4>
                <p className="text-[10px] text-slate-400">Scan database rows for identical fields and drop redundancies.</p>
              </div>

              <button
                onClick={applyRemoveDuplicates}
                disabled={applying}
                className="w-full py-4 bg-brand-500/10 hover:bg-brand-500/20 border border-brand-500/20 text-brand-700 dark:text-brand-400 rounded-xl text-xs font-extrabold transition-all disabled:opacity-40 flex items-center justify-center gap-2"
              >
                <Trash2 className="w-4 h-4" /> Drop Duplicate Rows
              </button>
            </GlassCard>

            {/* Column Operations (col 2-3) */}
            <GlassCard className="md:col-span-2 flex flex-col justify-between space-y-4">
              <div className="space-y-1">
                <h4 className="font-extrabold text-sm text-slate-800 dark:text-slate-200">F. Column operations & Custom Equations</h4>
                <p className="text-[10px] text-slate-400">Rename variables, delete unneeded parameters, or define math relationships.</p>
              </div>

              <div className="grid sm:grid-cols-2 gap-4">
                
                <div className="space-y-3">
                  <div className="flex flex-col gap-1">
                    <label className="text-[10px] font-bold text-slate-400 uppercase">Operation</label>
                    <select 
                      value={colOpAction} 
                      onChange={(e) => setColOpAction(e.target.value as any)}
                      className="glass-input px-3 py-2 text-xs"
                    >
                      <option value="rename">Rename Column</option>
                      <option value="delete">Delete Column</option>
                      <option value="create">Create Calculated Column</option>
                    </select>
                  </div>

                  {colOpAction !== 'create' && (
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-slate-400 uppercase">Target Column</label>
                      <select 
                        value={colOpTarget} 
                        onChange={(e) => setColOpTarget(e.target.value)}
                        className="glass-input px-3 py-2 text-xs"
                      >
                        {columns.map(c => <option key={c} value={c}>{c}</option>)}
                      </select>
                    </div>
                  )}
                </div>

                <div className="space-y-3">
                  {colOpAction !== 'delete' && (
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-slate-400 uppercase">
                        {colOpAction === 'rename' ? 'New Column Name' : 'New Calculated Column Name'}
                      </label>
                      <input 
                        type="text" 
                        value={colOpNewName}
                        onChange={(e) => setColOpNewName(e.target.value)}
                        placeholder="e.g. Sales_Adjusted"
                        className="glass-input px-3 py-2 text-xs"
                      />
                    </div>
                  )}

                  {colOpAction === 'create' && (
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-slate-400 uppercase">Math Formula Expression</label>
                      <input 
                        type="text" 
                        value={colOpFormula}
                        onChange={(e) => setColOpFormula(e.target.value)}
                        placeholder="e.g. Units_Sold * Unit_Price"
                        className="glass-input px-3 py-2 text-xs font-semibold"
                      />
                    </div>
                  )}
                </div>

              </div>

              <button
                onClick={applyColumnOp}
                disabled={applying || (colOpAction === 'rename' && !colOpNewName) || (colOpAction === 'create' && (!colOpNewName || !colOpFormula))}
                className="w-full py-2 bg-brand-500 hover:bg-brand-600 text-white rounded-xl text-xs font-bold transition-all disabled:opacity-40"
              >
                Execute Column Operation
              </button>
            </GlassCard>

          </div>

        </div>

        {/* Change / Transformation Audit Logs (Right Sidebar column, span 1) */}
        <div>
          <GlassCard className="h-full flex flex-col justify-between space-y-4">
            <div>
              <h3 className="font-extrabold text-sm flex items-center gap-2">
                <RotateCcw className="w-4 h-4 text-brand-500" /> Transformation Audit Timeline
              </h3>
              <p className="text-[10px] text-slate-400">Step-by-step history of transformations applied on this dataset.</p>
            </div>

            {/* Timeline element */}
            <div className="flex-1 overflow-y-auto max-h-[460px] space-y-4 pr-1 mt-4 text-xs">
              {!activeVersion?.cleaning_logs || activeVersion.cleaning_logs.length === 0 ? (
                <div className="text-center py-10 text-slate-400 dark:text-slate-600 italic">
                  No transformations applied
                </div>
              ) : (
                <div className="relative border-l border-slate-200 dark:border-slate-800 ml-2 space-y-5">
                  {activeVersion.cleaning_logs.map((log, idx) => (
                    <div key={idx} className="relative pl-6">
                      {/* Timeline dot */}
                      <span className="absolute -left-1.5 top-1.5 w-3 h-3 bg-brand-500 border-2 border-white dark:border-slate-950 rounded-full" />
                      
                      <div className="space-y-1">
                        <div className="flex justify-between items-center font-bold">
                          <span className="text-slate-800 dark:text-slate-200 bg-brand-500/10 px-2 py-0.5 rounded-md text-[9px] text-brand-600 dark:text-brand-400">
                            {log.action_type}
                          </span>
                          <span className="text-[9px] text-slate-400 font-semibold">
                            {new Date(log.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>
                        <p className="text-[10px] text-slate-600 dark:text-slate-400 leading-relaxed font-semibold">
                          {log.column_name && <span>Col: <b>{log.column_name}</b> • </span>}
                          {log.details}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </GlassCard>
        </div>

      </div>
    </div>
  );
};
