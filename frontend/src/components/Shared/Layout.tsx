import React from 'react';
// eslint-disable-next-line @typescript-eslint/no-unused-vars
import { 
  LayoutDashboard, 
  Wand2, 
  BarChart4, 
  MessageSquare, 
  Download, 
  Home,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import { Navbar } from './Navbar';
import type { Dataset, DatasetVersion } from '../../services/api';

interface LayoutProps {
  children: React.ReactNode;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  activeDataset: Dataset | null;
  activeVersion: DatasetVersion | null;
}

export const Layout: React.FC<LayoutProps> = ({
  children,
  activeTab,
  setActiveTab,
  activeDataset,
  activeVersion,
}) => {
  const [collapsed, setCollapsed] = React.useState<boolean>(false);

  const menuItems = [
    { id: 'landing', label: 'Home', icon: Home, requiresDataset: false },
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, requiresDataset: false },
    { id: 'cleaning', label: 'Data Cleaning', icon: Wand2, requiresDataset: true },
    { id: 'eda', label: 'Exploratory EDA', icon: BarChart4, requiresDataset: true },
    { id: 'chat', label: 'AI Chat Assistant', icon: MessageSquare, requiresDataset: true },
    { id: 'reports', label: 'Export Reports', icon: Download, requiresDataset: true },
  ];

  const handleTabClick = (itemId: string) => {
    setActiveTab(itemId);
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* Top Header Navbar */}
      <Navbar activeDataset={activeDataset} activeVersion={activeVersion} />

      {/* Main Layout Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <aside 
          className={`
            glass-card border-y-0 border-l-0 rounded-none z-10 flex flex-col justify-between transition-all duration-300
            ${collapsed ? 'w-20' : 'w-64'}
          `}
          id="app-sidebar"
        >
          <div className="py-6 px-4">
            <div className="flex flex-col gap-2">
              {menuItems.map((item) => {
                const Icon = item.icon;
                const isActive = activeTab === item.id;
                const needsDataset = item.requiresDataset && !activeDataset;
                
                return (
                  <button
                    key={item.id}
                    onClick={() => handleTabClick(item.id)}
                    className={`
                      w-full flex items-center gap-3 py-3 px-3.5 rounded-xl text-sm font-semibold transition-all group relative
                      ${isActive 
                        ? 'bg-brand-500 text-white shadow-md shadow-brand-500/20' 
                        : needsDataset
                          ? 'text-slate-400 dark:text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-900 hover:text-slate-600 dark:hover:text-slate-300'
                          : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-900'
                      }
                    `}
                    id={`sidebar-link-${item.id}`}
                  >
                    <Icon className={`w-5 h-5 shrink-0 ${isActive ? 'text-white' : needsDataset ? 'text-slate-400 dark:text-slate-500' : 'text-slate-500 dark:text-slate-400'}`} />
                    
                    {!collapsed && (
                      <span className="truncate">{item.label}</span>
                    )}

                    {/* Tooltip when collapsed */}
                    {collapsed && (
                      <span className="absolute left-full ml-3 px-2 py-1 rounded bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900 text-xs font-semibold opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-50 whitespace-nowrap shadow-lg">
                        {item.label}{needsDataset ? ' (Upload CSV first)' : ''}
                      </span>
                    )}

                    {/* "needs dataset" dot indicator when not collapsed */}
                    {!collapsed && needsDataset && !isActive && (
                      <span className="ml-auto text-[10px] text-slate-400 dark:text-slate-600 font-normal italic">No CSV</span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Sidebar Collapse Action */}
          <div className="p-4 border-t border-slate-200/50 dark:border-slate-800/40">
            <button
              onClick={() => setCollapsed(!collapsed)}
              className="w-full flex items-center justify-center p-2 rounded-xl text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-900 border border-slate-200/30 dark:border-slate-800/30 transition-all"
            >
              {collapsed ? <ChevronRight className="w-5 h-5" /> : <ChevronLeft className="w-5 h-5" />}
            </button>
          </div>
        </aside>

        {/* Content Panel */}
        <main className="flex-1 overflow-y-auto p-8 relative">
          <div className="max-w-7xl mx-auto space-y-8 fade-in">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};
