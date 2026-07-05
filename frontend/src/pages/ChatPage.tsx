/* eslint-disable @typescript-eslint/no-unused-vars */
import React, { useState, useEffect, useRef } from 'react';
import { 
  MessageSquare, 
  Send, 
  Sparkles, 
  Bot, 
  User, 
  Trash2,
  TrendingUp,
  AlertTriangle,
  Lightbulb,
  Zap,
  Activity
} from 'lucide-react';
import { api } from '../services/api';
import type { Dataset, DatasetVersion, ChatMessage, Insight } from '../services/api';
import { GlassCard } from '../components/UI/GlassCard';

interface ChatPageProps {
  activeDataset: Dataset | null;
  activeVersion: DatasetVersion | null;
}

export const ChatPage: React.FC<ChatPageProps> = ({ activeDataset, activeVersion }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [input, setInput] = useState<string>('');
  const [sending, setSending] = useState<boolean>(false);
  const [loadingHistory, setLoadingHistory] = useState<boolean>(false);
  const [loadingInsights, setLoadingInsights] = useState<boolean>(false);
  const chatEndRef = useRef<HTMLDivElement | null>(null);

  const presets = [
    "Summarize this dataset.",
    "What are the strongest correlations?",
    "Identify outliers or anomalies.",
    "Which columns should I remove?",
    "Give me data quality improvement suggestions."
  ];

  useEffect(() => {
    if (activeDataset && activeVersion) {
      loadHistory(activeDataset.id);
      loadInsights(activeDataset.id, activeVersion.version_number);
    }
  }, [activeDataset, activeVersion]);

  // Scroll to bottom when messages changes
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadHistory = async (datasetId: number) => {
    setLoadingHistory(true);
    try {
      const history = await api.getChatHistory(datasetId);
      setMessages(history);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingHistory(false);
    }
  };

  const loadInsights = async (datasetId: number, versionNum: number) => {
    setLoadingInsights(true);
    try {
      const ins = await api.getInsights(datasetId, versionNum);
      setInsights(ins);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingInsights(false);
    }
  };

  const handleSend = async (text: string) => {
    if (!activeDataset || !text.trim() || sending) return;
    
    setInput('');
    setSending(true);

    // Optimistically add user message to UI
    const tempUserMsg: ChatMessage = {
      id: Math.random(),
      dataset_id: activeDataset.id,
      sender: 'user',
      message: text,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, tempUserMsg]);

    try {
      const response = await api.sendChatMessage(activeDataset.id, text);
      setMessages(prev => [...prev.filter(m => m.id !== tempUserMsg.id), tempUserMsg, response]);
    } catch (err: any) {
      const errMsg: ChatMessage = {
        id: Math.random(),
        dataset_id: activeDataset.id,
        sender: 'assistant',
        message: `Oops, I failed to process that request: ${err.message || 'Server error.'}`,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errMsg]);
    } finally {
      setSending(false);
    }
  };

  const clearChatHistory = async () => {
    if (!activeDataset) return;
    if (!window.confirm("Are you sure you want to clear chat history for this dataset?")) return;
    try {
      await api.clearChat(activeDataset.id);
      setMessages([]);
    } catch (err) {
      console.error(err);
    }
  };

  const getInsightIcon = (category: string) => {
    switch (category) {
      case 'trend':
        return <TrendingUp className="w-4 h-4 text-emerald-500" />;
      case 'anomaly':
        return <AlertTriangle className="w-4 h-4 text-rose-500" />;
      case 'correlation':
        return <Zap className="w-4 h-4 text-indigo-500" />;
      case 'recommendation':
      default:
        return <Lightbulb className="w-4 h-4 text-amber-500" />;
    }
  };

  const getImportanceBadgeColor = (imp: string) => {
    switch (imp) {
      case 'high':
        return 'bg-rose-500/10 text-rose-500 border-rose-500/20';
      case 'medium':
        return 'bg-amber-500/10 text-amber-500 border-amber-500/20';
      case 'low':
      default:
        return 'bg-slate-200/50 dark:bg-slate-800 text-slate-500 rounded border-slate-300/30';
    }
  };

  if (!activeDataset) {
    return (
      <div className="text-center py-20 text-slate-400 italic">
        Upload a dataset on the Dashboard to chat with AI Analytics.
      </div>
    );
  }

  return (
    <div className="space-y-8 fade-in" id="chat-page-root">
      
      {/* Title */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-extrabold flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-brand-500" /> AI Analytics Console & Insights
          </h2>
          <p className="text-slate-500 dark:text-slate-400">Ask statistical questions, generate correlations, scan trends, or retrieve suggestions.</p>
        </div>

        <button
          onClick={clearChatHistory}
          className="flex items-center gap-2 px-3 py-1.5 text-xs font-semibold rounded-lg text-slate-500 hover:text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/20 transition-all border border-slate-200 dark:border-slate-800"
          title="Clear Chat Logs"
        >
          <Trash2 className="w-4 h-4" /> Clear Logs
        </button>
      </div>

      {/* Main layout grid */}
      <div className="grid lg:grid-cols-3 gap-8 items-start">
        
        {/* Left Side: Chat Console (Span 2) */}
        <div className="lg:col-span-2 space-y-6">
          <GlassCard className="flex flex-col h-[550px] p-0 overflow-hidden relative">
            
            {/* Header bar */}
            <div className="px-6 py-4 border-b border-slate-200/50 dark:border-slate-800/40 bg-slate-50/50 dark:bg-slate-900/30 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Bot className="w-5 h-5 text-brand-500" />
                <div>
                  <span className="font-extrabold text-sm text-slate-800 dark:text-slate-200">DataInsight Analyst</span>
                  <span className="ml-1.5 text-[8px] font-bold px-1.5 py-0.2 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 rounded">
                    ONLINE
                  </span>
                </div>
              </div>
            </div>

            {/* Chat Body messages */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {loadingHistory ? (
                <div className="h-full flex items-center justify-center text-slate-400 text-xs">
                  <Activity className="w-5 h-5 animate-spin mr-2" />
                  Loading chat logs...
                </div>
              ) : messages.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center space-y-4 max-w-md mx-auto">
                  <MessageSquare className="w-12 h-12 text-slate-300 dark:text-slate-700" />
                  <div>
                    <p className="font-extrabold text-slate-700 dark:text-slate-300 text-sm">No Conversations Yet</p>
                    <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                      Ask me questions about columns, missing rates, duplicate records, distributions, skewness, outliers, or type conversions.
                    </p>
                  </div>
                  {/* Preset Quick links */}
                  <div className="flex flex-wrap items-center justify-center gap-2 pt-2">
                    {presets.slice(0, 3).map((p, i) => (
                      <button
                        key={i}
                        onClick={() => handleSend(p)}
                        className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 dark:bg-slate-900 dark:hover:bg-slate-800 border border-slate-200/50 dark:border-slate-800/40 text-[10px] font-bold text-slate-600 dark:text-slate-300 rounded-xl transition-all"
                      >
                        {p}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  {messages.map((msg, idx) => {
                    const isBot = msg.sender === 'assistant';
                    return (
                      <div 
                        key={idx} 
                        className={`flex gap-3 max-w-[85%] ${isBot ? 'mr-auto' : 'ml-auto flex-row-reverse'}`}
                      >
                        {/* Avatar */}
                        <div className={`p-2 rounded-xl h-fit shrink-0 ${isBot ? 'bg-brand-500/10 text-brand-500' : 'bg-slate-100 dark:bg-slate-900 text-slate-600 dark:text-slate-300'}`}>
                          {isBot ? <Bot className="w-4 h-4" /> : <User className="w-4 h-4" />}
                        </div>

                        {/* Speech Bubble */}
                        <div 
                          className={`
                            px-4 py-3 rounded-2xl text-xs leading-relaxed border shadow-sm
                            ${isBot 
                              ? 'bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-200 border-slate-200/60 dark:border-slate-800/50' 
                              : 'bg-brand-500 text-white border-brand-600'
                            }
                          `}
                        >
                          {/* Bot text might contain markdown formatting, rendering linebreaks */}
                          <div className="whitespace-pre-line font-medium">
                            {msg.message}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                  
                  {sending && (
                    <div className="flex gap-3 mr-auto max-w-[80%]">
                      <div className="p-2 rounded-xl bg-brand-500/10 text-brand-500 h-fit shrink-0">
                        <Bot className="w-4 h-4" />
                      </div>
                      <div className="px-4 py-3 rounded-2xl text-xs bg-white dark:bg-slate-900 text-slate-400 border border-slate-200/50 dark:border-slate-800/50 flex items-center gap-2">
                        <Activity className="w-3.5 h-3.5 animate-spin text-brand-500" />
                        AI is compiling statistics...
                      </div>
                    </div>
                  )}
                  
                  <div ref={chatEndRef} />
                </div>
              )}
            </div>

            {/* Chat Footer text input */}
            <div className="p-4 border-t border-slate-200/50 dark:border-slate-800/40 bg-slate-50/50 dark:bg-slate-950/20">
              <form 
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSend(input);
                }}
                className="flex gap-2"
              >
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask a question about your dataset (e.g. What are the anomalies?)..."
                  className="flex-1 glass-input px-4 py-3 text-xs"
                  id="chat-query-input"
                  disabled={sending}
                />
                <button
                  type="submit"
                  disabled={!input.trim() || sending}
                  className="px-4 py-3 bg-brand-500 hover:bg-brand-600 text-white rounded-xl text-xs font-bold transition-all shadow-md disabled:opacity-40 shrink-0"
                >
                  <Send className="w-4.5 h-4.5" />
                </button>
              </form>
            </div>

          </GlassCard>
        </div>

        {/* Right Side: Insights Lists and Presets (Span 1) */}
        <div className="space-y-6">
          
          {/* Quick preset suggestions */}
          <GlassCard className="space-y-3">
            <h3 className="font-extrabold text-sm">Suggested Queries</h3>
            <div className="flex flex-col gap-2">
              {presets.map((p, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSend(p)}
                  className="w-full text-left p-2.5 rounded-lg border border-slate-200/50 dark:border-slate-800/40 hover:bg-slate-50 dark:hover:bg-slate-900/60 text-[11px] font-bold text-slate-600 dark:text-slate-300 transition-all truncate"
                >
                  {p}
                </button>
              ))}
            </div>
          </GlassCard>

          {/* AI Insights Board */}
          <GlassCard className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-extrabold text-sm flex items-center gap-1.5">
                <Sparkles className="w-4 h-4 text-brand-500" /> Automated Insight Deck
              </h3>
              {loadingInsights && <Activity className="w-3.5 h-3.5 animate-spin text-brand-500" />}
            </div>

            <div className="space-y-3 max-h-[310px] overflow-y-auto pr-1 text-xs">
              {insights.length === 0 ? (
                <div className="text-center py-6 text-slate-400 dark:text-slate-600 italic">
                  No automated insights generated
                </div>
              ) : (
                insights.map((ins, idx) => (
                  <div 
                    key={idx}
                    className="p-3 rounded-xl border border-slate-200/50 dark:border-slate-800/40 bg-white/20 dark:bg-slate-950/20 space-y-1.5"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5 font-extrabold">
                        {getInsightIcon(ins.category)}
                        <span className="truncate max-w-[130px]">{ins.title}</span>
                      </div>
                      <span className={`text-[8px] font-bold px-1.5 py-0.2 rounded border uppercase ${getImportanceBadgeColor(ins.importance)}`}>
                        {ins.importance}
                      </span>
                    </div>
                    <p className="text-[10px] text-slate-500 dark:text-slate-400 leading-relaxed font-semibold">
                      {ins.description}
                    </p>
                  </div>
                ))
              )}
            </div>
          </GlassCard>

        </div>

      </div>

    </div>
  );
};
