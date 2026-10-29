import React, { useState } from 'react';
import {
  LayoutDashboard,
  Video,
  BarChart3,
  Scale,
  FlaskConical,
  Settings,
  BookOpen,
  Activity,
  Wifi,
  WifiOff,
  ShieldAlert
} from 'lucide-react';

import { useTelemetry } from './hooks/useTelemetry';
import { OverviewPage } from './pages/OverviewPage';
import { LiveMonitoringPage } from './pages/LiveMonitoringPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { ModelComparisonPage } from './pages/ModelComparisonPage';
import { ExperimentCenterPage } from './pages/ExperimentCenterPage';
import { AlertsSettingsPage } from './pages/AlertsSettingsPage';
import { DocumentationPage } from './pages/DocumentationPage';

export function App() {
  const [activeTab, setActiveTab] = useState<string>('overview');
  const { stats, alerts, sessionId, isConnected } = useTelemetry();

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'critical':
        return 'bg-rose-500/20 text-rose-300 border-rose-500/40 animate-pulse';
      case 'high':
        return 'bg-orange-500/20 text-orange-300 border-orange-500/40';
      case 'moderate':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/40';
      default:
        return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40';
    }
  };

  const navItems = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'live', label: 'Live Stream', icon: Video },
    { id: 'analytics', label: 'Crowd Analytics', icon: BarChart3 },
    { id: 'models', label: 'Model Comparison', icon: Scale },
    { id: 'experiments', label: 'Experiment Center', icon: FlaskConical },
    { id: 'alerts', label: 'Alerts & Settings', icon: Settings },
    { id: 'docs', label: 'Methodology & Docs', icon: BookOpen },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-navy-900 text-slate-100">
      {/* Top Navigation Bar */}
      <header className="sticky top-0 z-50 glass-panel border-b border-slate-800/80 px-6 py-3.5 shadow-2xl">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          {/* Logo & Brand Title */}
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 shadow-lg shadow-cyan-500/20 text-white">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <div className="text-base font-bold tracking-tight text-white flex items-center space-x-2">
                <span>CROWD INTEL</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-normal">
                  v1.0 RESEARCH
                </span>
              </div>
              <div className="text-[11px] text-slate-400 font-medium">
                People Counting & Occlusion-Aware Density Estimation
              </div>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="hidden lg:flex items-center space-x-1 bg-slate-900/60 p-1 rounded-xl border border-slate-800">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                    isActive
                      ? 'bg-cyan-500 text-white shadow-md shadow-cyan-500/20'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>

          {/* System Status Indicators */}
          <div className="flex items-center space-x-3">
            {/* Live Crowd Level */}
            <div className={`hidden sm:flex items-center space-x-1.5 px-2.5 py-1 rounded-lg text-xs font-bold uppercase tracking-wider border ${getStatusBadge(stats.crowd_status)}`}>
              <span className="w-2 h-2 rounded-full bg-current" />
              <span>{stats.crowd_status}</span>
            </div>

            {/* Hardware / WS Status */}
            <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-slate-800/60 border border-slate-700/60 text-xs font-mono text-slate-300">
              {isConnected ? (
                <>
                  <Wifi className="w-3.5 h-3.5 text-emerald-400" />
                  <span className="text-emerald-400">ONLINE</span>
                </>
              ) : (
                <>
                  <WifiOff className="w-3.5 h-3.5 text-rose-400" />
                  <span className="text-rose-400">CONNECTING</span>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Mobile Navigation Bar */}
        <div className="lg:hidden flex overflow-x-auto space-x-1 pt-3 pb-1 border-t border-slate-800 mt-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex-shrink-0 flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg text-xs font-semibold ${
                  isActive ? 'bg-cyan-500 text-white' : 'text-slate-400 hover:text-white'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>
      </header>

      {/* Main Page Body */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6">
        {activeTab === 'overview' && <OverviewPage stats={stats} alerts={alerts} sessionId={sessionId} />}
        {activeTab === 'live' && <LiveMonitoringPage stats={stats} />}
        {activeTab === 'analytics' && <AnalyticsPage />}
        {activeTab === 'models' && <ModelComparisonPage />}
        {activeTab === 'experiments' && <ExperimentCenterPage />}
        {activeTab === 'alerts' && <AlertsSettingsPage />}
        {activeTab === 'docs' && <DocumentationPage />}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 py-4 px-6 text-center text-xs text-slate-400 glass-panel">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <div>
            Real-Time People Counting and Crowd Density Estimation System &bull; Research & Industrial Demonstration
          </div>
          <div className="text-[11px] font-mono text-slate-400">
            PyTorch 2.14 &bull; Ultralytics YOLOv8 &bull; ByteTrack &bull; MCNN &bull; FastAPI &bull; React
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
