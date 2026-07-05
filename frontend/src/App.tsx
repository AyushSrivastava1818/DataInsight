import { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './components/Shared/AuthContext';
import { api } from './services/api';
import type { Dataset, DatasetVersion } from './services/api';
import { Layout } from './components/Shared/Layout';
import { LoginPage } from './pages/LoginPage';
import { LandingPage } from './pages/LandingPage';
import { DashboardPage } from './pages/DashboardPage';
import { CleaningPage } from './pages/CleaningPage';
import { EDAPage } from './pages/EDAPage';
import { ChatPage } from './pages/ChatPage';
import { ReportsPage } from './pages/ReportsPage';

// Inner app — rendered only when auth session is confirmed
function AppContent() {
  const { user, session, loading } = useAuth();
  const [activeTab, setActiveTab] = useState<string>('landing');
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [activeDataset, setActiveDataset] = useState<Dataset | null>(null);
  const [activeVersion, setActiveVersion] = useState<DatasetVersion | null>(null);

  useEffect(() => {
    const supabaseConfigured = !!import.meta.env.VITE_SUPABASE_URL;
    if (session || !supabaseConfigured) {
      refreshDatasets();
    }
  }, [session]);

  const refreshDatasets = async () => {
    try {
      const list = await api.listDatasets();
      setDatasets(list);
      
      if (list.length > 0) {
        if (!activeDataset) {
          const latestDataset = list[0];
          setActiveDataset(latestDataset);
          const latestVersion = latestDataset.versions.reduce((prev, curr) =>
            prev.version_number > curr.version_number ? prev : curr
          );
          setActiveVersion(latestVersion);
        } else {
          const updated = list.find(d => d.id === activeDataset.id);
          if (updated) {
            setActiveDataset(updated);
            const stillExists = updated.versions.find(v => v.version_number === activeVersion?.version_number);
            if (stillExists) {
              setActiveVersion(stillExists);
            } else {
              const latest = updated.versions.reduce((prev, curr) =>
                prev.version_number > curr.version_number ? prev : curr
              );
              setActiveVersion(latest);
            }
          }
        }
      } else {
        setActiveDataset(null);
        setActiveVersion(null);
      }
    } catch (err) {
      console.error('Error fetching datasets:', err);
    }
  };

  // Show centered spinner while Supabase checks existing session
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-4 border-brand-500/20 border-t-brand-500 rounded-full animate-spin" />
          <p className="text-slate-400 text-sm font-medium">Initializing session…</p>
        </div>
      </div>
    );
  }

  // Show LoginPage if no authenticated session exists.
  // When VITE_SUPABASE_URL is not configured, supabase client is null,
  // so we skip auth requirement and load the app directly (dev mode).
  const supabaseConfigured = !!import.meta.env.VITE_SUPABASE_URL;
  if (supabaseConfigured && !user) {
    return <LoginPage />;
  }

  const renderContent = () => {
    switch (activeTab) {
      case 'landing':
        return <LandingPage onStart={() => setActiveTab('dashboard')} />;
      case 'dashboard':
        return (
          <DashboardPage
            activeDataset={activeDataset}
            activeVersion={activeVersion}
            setActiveDataset={setActiveDataset}
            setActiveVersion={setActiveVersion}
            refreshDatasets={refreshDatasets}
            datasets={datasets}
          />
        );
      case 'cleaning':
        return (
          <CleaningPage
            activeDataset={activeDataset}
            activeVersion={activeVersion}
            setActiveDataset={setActiveDataset}
            setActiveVersion={setActiveVersion}
            refreshDatasets={refreshDatasets}
          />
        );
      case 'eda':
        return <EDAPage activeDataset={activeDataset} activeVersion={activeVersion} />;
      case 'chat':
        return <ChatPage activeDataset={activeDataset} activeVersion={activeVersion} />;
      case 'reports':
        return <ReportsPage activeDataset={activeDataset} activeVersion={activeVersion} />;
      default:
        return <LandingPage onStart={() => setActiveTab('dashboard')} />;
    }
  };

  return (
    <Layout
      activeTab={activeTab}
      setActiveTab={setActiveTab}
      activeDataset={activeDataset}
      activeVersion={activeVersion}
    >
      {renderContent()}
    </Layout>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
