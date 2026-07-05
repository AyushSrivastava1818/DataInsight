// eslint-disable-next-line @typescript-eslint/no-unused-vars
import { Database, ShieldAlert, CheckCircle, BarChart2 } from 'lucide-react';
import { DarkModeToggle } from './DarkModeToggle';
import type { Dataset, DatasetVersion } from '../../services/api';

interface NavbarProps {
  activeDataset: Dataset | null;
  activeVersion: DatasetVersion | null;
}

export const Navbar: React.FC<NavbarProps> = ({ activeDataset, activeVersion }) => {
  const getQualityColor = (score: number) => {
    if (score >= 80) return 'text-emerald-500 bg-emerald-500/10 border-emerald-500/20';
    if (score >= 50) return 'text-amber-500 bg-amber-500/10 border-amber-500/20';
    return 'text-rose-500 bg-rose-500/10 border-rose-500/20';
  };

  return (
    <nav className="glass-nav sticky top-0 z-50 px-6 py-4 flex items-center justify-between" id="app-navbar">
      {/* Brand Logo */}
      <div className="flex items-center gap-3">
        <div className="p-2.5 rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-500 text-white shadow-lg shadow-brand-500/30">
          <BarChart2 className="w-6 h-6" />
        </div>
        <div>
          <span className="font-extrabold text-xl bg-clip-text text-transparent bg-gradient-to-r from-brand-600 to-indigo-500 dark:from-brand-400 dark:to-indigo-300">
            DataInsight AI
          </span>
          <span className="ml-1.5 text-[10px] font-semibold px-1.5 py-0.5 rounded-md bg-brand-500/10 text-brand-600 dark:text-brand-400 border border-brand-500/20">
            PRO
          </span>
        </div>
      </div>

      {/* Dataset Context Bar */}
      {activeDataset && activeVersion && (
        <div className="hidden md:flex items-center gap-4 py-1.5 px-4 rounded-2xl bg-slate-100/80 dark:bg-slate-900/60 border border-slate-200/50 dark:border-slate-800/40 text-sm">
          <div className="flex items-center gap-2">
            <Database className="w-4 h-4 text-brand-500" />
            <span className="font-bold truncate max-w-[200px]" title={activeDataset.name}>
              {activeDataset.name}
            </span>
          </div>

          <div className="h-4 w-px bg-slate-300 dark:bg-slate-800" />

          <div className="flex items-center gap-1.5">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">Version:</span>
            <span className="px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-500 dark:text-indigo-400 font-bold text-xs border border-indigo-500/20">
              v{activeVersion.version_number}
            </span>
          </div>

          <div className="h-4 w-px bg-slate-300 dark:bg-slate-800" />

          <div className={`flex items-center gap-1.5 px-2.5 py-0.5 rounded-full border text-xs font-bold ${getQualityColor(activeVersion.quality_score)}`}>
            {activeVersion.quality_score >= 70 ? (
              <CheckCircle className="w-3.5 h-3.5" />
            ) : (
              <ShieldAlert className="w-3.5 h-3.5" />
            )}
            Health: {activeVersion.quality_score}/100
          </div>
        </div>
      )}

      {/* Action Controls */}
      <div className="flex items-center gap-3">
        <DarkModeToggle />
      </div>
    </nav>
  );
};
