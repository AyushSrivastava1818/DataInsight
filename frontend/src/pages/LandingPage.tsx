import React from 'react';
import { ArrowRight, Wand2, BarChart4, MessageSquare, Download, Sparkles } from 'lucide-react';
import { GlassCard } from '../components/UI/GlassCard';

interface LandingPageProps {
  onStart: () => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onStart }) => {
  return (
    <div className="space-y-16 py-6 fade-in" id="landing-page-root">
      {/* Hero Section */}
      <div className="text-center max-w-4xl mx-auto space-y-6 animate-float">
        <div className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-brand-500/10 text-brand-600 dark:text-brand-400 border border-brand-500/20 text-xs font-bold uppercase tracking-wider">
          <Sparkles className="w-3.5 h-3.5" /> Powered by Advanced Data AI
        </div>
        
        <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight leading-tight">
          Turn Raw CSV Datasets into{' '}
          <span className="bg-clip-text text-transparent bg-gradient-to-r from-brand-600 to-indigo-500 dark:from-brand-400 dark:to-indigo-300">
            Actionable Insights
          </span>{' '}
          in Seconds
        </h1>
        
        <p className="text-lg md:text-xl text-slate-600 dark:text-slate-400 font-medium max-w-2xl mx-auto leading-relaxed">
          The all-in-one data profiling tool. Automatically clean missing entries, cap outliers, inspect descriptive statistics, draw visualizations, and chat with your dataset.
        </p>

        <div className="pt-4 flex items-center justify-center">
          <button
            onClick={onStart}
            className="group flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-brand-600 to-indigo-600 hover:from-brand-700 hover:to-indigo-700 text-white font-bold rounded-2xl shadow-xl shadow-brand-500/20 hover:shadow-brand-500/35 transition-all text-base"
            id="landing-cta-btn"
          >
            Launch Console
            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </button>
        </div>
      </div>

      {/* Feature Showcase Grid */}
      <div className="space-y-6">
        <div className="text-center space-y-2">
          <h2 className="text-3xl font-extrabold">Supercharge Your Analysis</h2>
          <p className="text-slate-500 dark:text-slate-400">Everything you need to go from raw file to a polished analytics deck</p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          <GlassCard hoverEffect className="space-y-4">
            <div className="w-12 h-12 rounded-xl bg-brand-500/10 text-brand-500 flex items-center justify-center border border-brand-500/25">
              <Wand2 className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold">1-Click Cleaning</h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
              Impute null values, drop duplicates, cap outliers via IQR/Z-score, standardize text capitalizations, and rename columns interactively.
            </p>
          </GlassCard>

          <GlassCard hoverEffect className="space-y-4">
            <div className="w-12 h-12 rounded-xl bg-indigo-500/10 text-indigo-500 flex items-center justify-center border border-indigo-500/25">
              <BarChart4 className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold">Automated EDA</h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
              Generate detailed descriptive statistics, frequency tables, correlation matrices, and time series trend plots automatically.
            </p>
          </GlassCard>

          <GlassCard hoverEffect className="space-y-4">
            <div className="w-12 h-12 rounded-xl bg-violet-500/10 text-violet-500 flex items-center justify-center border border-violet-500/25">
              <MessageSquare className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold">Chat Assistant</h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
              Ask natural language questions like "which columns should I remove?" or "explain the correlations" and get immediate, contextual responses.
            </p>
          </GlassCard>

          <GlassCard hoverEffect className="space-y-4">
            <div className="w-12 h-12 rounded-xl bg-purple-500/10 text-purple-500 flex items-center justify-center border border-purple-500/25">
              <Download className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold">PDF/CSV Export</h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
              Download the fully-cleaned dataset or download a structured, publication-quality PDF report complete with your audit trails and charts.
            </p>
          </GlassCard>
        </div>
      </div>

      {/* Aesthetic Callout */}
      <GlassCard className="bg-gradient-to-r from-brand-600/5 to-indigo-600/5 dark:from-brand-500/10 dark:to-indigo-500/10 border border-brand-500/20 dark:border-brand-500/10 p-10 flex flex-col md:flex-row items-center justify-between gap-8">
        <div className="space-y-2 max-w-2xl">
          <h3 className="text-2xl font-bold">Ready to analyze your own data?</h3>
          <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
            Upload any CSV file up to 100 MB. We process everything locally in your SQLite workspace, ensuring total data privacy and rapid profile renders.
          </p>
        </div>
        <button
          onClick={onStart}
          className="px-6 py-3.5 bg-slate-900 hover:bg-slate-800 dark:bg-white dark:hover:bg-slate-100 text-white dark:text-slate-950 font-extrabold rounded-xl transition-all shadow-md shrink-0 text-sm"
        >
          Get Started
        </button>
      </GlassCard>
    </div>
  );
};
