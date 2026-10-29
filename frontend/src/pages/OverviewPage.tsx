import React, { useEffect, useState } from 'react';
import {
  Users,
  Eye,
  Footprints,
  Activity,
  Flame,
  ShieldAlert,
  ArrowRightLeft,
  MapPin,
  TrendingUp,
  Cpu
} from 'lucide-react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

import { TelemetryStats, AlertItem, AnalyticsSnapshot } from '../types';
import { KPICard } from '../components/KPICard';
import { AlertBanner } from '../components/AlertBanner';
import { VideoPlayer } from '../components/VideoPlayer';
import { apiService } from '../services/api';

interface OverviewPageProps {
  stats: TelemetryStats;
  alerts: AlertItem[];
  sessionId: string;
}

export const OverviewPage: React.FC<OverviewPageProps> = ({ stats, alerts, sessionId }) => {
  const [historyData, setHistoryData] = useState<any[]>([]);

  // Fetch trend history for charts
  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await apiService.getAnalyticsHistory(sessionId, 40);
        if (res.data && res.data.snapshots) {
          const formatted = res.data.snapshots.map((s, idx) => ({
            time: new Date(s.timestamp * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
            tracked: s.active_tracked_count,
            detected: s.detection_count,
            density: s.density_estimate,
            hybrid: s.hybrid_estimate
          }));
          setHistoryData(formatted);
        }
      } catch (e) {
        // quiet
      }
    };

    fetchHistory();
    const interval = setInterval(fetchHistory, 3000);
    return () => clearInterval(interval);
  }, [sessionId]);

  const totalIn = Object.values(stats.lines || {}).reduce((acc, curr) => acc + curr.count_in, 0);
  const totalOut = Object.values(stats.lines || {}).reduce((acc, curr) => acc + curr.count_out, 0);

  return (
    <div className="space-y-6">
      {/* Alert Banner */}
      <AlertBanner alerts={alerts} />

      {/* KPI Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <KPICard
          title="Frame Detections"
          value={stats.frame_detection_count}
          subtitle="Instantaneous count"
          icon={Eye}
          colorScheme="cyan"
          badge="YOLO"
        />

        <KPICard
          title="Active Tracked"
          value={stats.active_tracked_count}
          subtitle="Persistent identities"
          icon={Users}
          colorScheme="emerald"
          badge="ByteTrack"
        />

        <KPICard
          title="Cumulative Unique"
          value={stats.cumulative_unique_count}
          subtitle="Total visitors"
          icon={Footprints}
          colorScheme="indigo"
          badge="Session"
        />

        <KPICard
          title="Density Estimate"
          value={stats.density_count > 0 ? stats.density_count.toFixed(1) : (stats.density_weights_ready ? '0.0' : 'No Weights')}
          subtitle={stats.density_weights_ready ? 'MCNN Regression' : 'Untrained Mode'}
          icon={Flame}
          colorScheme="amber"
          badge="Spatial"
        />

        <KPICard
          title="Throughput"
          value={`${stats.processing_fps.toFixed(1)} FPS`}
          subtitle={`${stats.latency_ms.toFixed(1)} ms latency`}
          icon={Activity}
          colorScheme="cyan"
          badge="Real-time"
        />

        <KPICard
          title="Occlusion Index"
          value={`${(stats.occlusion_index * 100).toFixed(0)}%`}
          subtitle={`Crowd: ${stats.difficulty_category.toUpperCase()}`}
          icon={ShieldAlert}
          colorScheme={stats.difficulty_category === 'severe' ? 'rose' : (stats.difficulty_category === 'high' ? 'amber' : 'emerald')}
          badge="Proxy"
        />
      </div>

      {/* Main View Area: Video Player & Real-Time Monitoring Panels */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Live Video Stream */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-white flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400"></span>
              <span>Live Visual Inference Stream</span>
            </h2>
            <div className="text-xs text-slate-400">
              Source: <span className="font-mono text-cyan-300">{stats.source || 'None'}</span>
            </div>
          </div>

          <VideoPlayer stats={stats} />
        </div>

        {/* Real-time Spatial & Tripwire Stats Sidebar */}
        <div className="space-y-6">
          {/* Tripwire Line Crossing Summary */}
          <div className="glass-panel p-5 rounded-2xl border border-slate-700/60 shadow-xl">
            <h3 className="text-sm font-semibold text-white mb-3 flex items-center space-x-2">
              <ArrowRightLeft className="w-4 h-4 text-purple-400" />
              <span>Tripwire Flow Analytics</span>
            </h3>

            <div className="grid grid-cols-3 gap-2 p-3 bg-slate-900/60 rounded-xl border border-slate-800 text-center mb-4">
              <div>
                <div className="text-xs text-slate-400 font-medium">IN</div>
                <div className="text-lg font-bold text-emerald-400">+{totalIn}</div>
              </div>
              <div className="border-x border-slate-800">
                <div className="text-xs text-slate-400 font-medium">OUT</div>
                <div className="text-lg font-bold text-rose-400">-{totalOut}</div>
              </div>
              <div>
                <div className="text-xs text-slate-400 font-medium">NET</div>
                <div className="text-lg font-bold text-cyan-400">{totalIn - totalOut}</div>
              </div>
            </div>

            {Object.keys(stats.lines || {}).length > 0 ? (
              <div className="space-y-2">
                {Object.values(stats.lines).map(line => (
                  <div key={line.line_id} className="p-2.5 rounded-lg bg-slate-800/40 border border-slate-700/40 flex items-center justify-between text-xs">
                    <span className="font-medium text-slate-300">{line.name}</span>
                    <div className="space-x-2 font-mono">
                      <span className="text-emerald-400">In: {line.count_in}</span>
                      <span className="text-rose-400">Out: {line.count_out}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-xs text-slate-400 text-center py-2">No tripwire lines configured.</div>
            )}
          </div>

          {/* Region of Interest Occupancy */}
          <div className="glass-panel p-5 rounded-2xl border border-slate-700/60 shadow-xl">
            <h3 className="text-sm font-semibold text-white mb-3 flex items-center space-x-2">
              <MapPin className="w-4 h-4 text-teal-400" />
              <span>Polygonal Region Occupancy</span>
            </h3>

            {Object.keys(stats.regions || {}).length > 0 ? (
              <div className="space-y-3">
                {Object.values(stats.regions).map(reg => (
                  <div key={reg.region_id} className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-xs font-semibold text-white">{reg.name}</span>
                      <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded ${
                        reg.status === 'critical' ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40' :
                        reg.status === 'high' ? 'bg-orange-500/20 text-orange-300 border border-orange-500/40' :
                        reg.status === 'moderate' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40' :
                        'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                      }`}>
                        {reg.status}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
                      <span>Occupants: <strong className="text-slate-100">{reg.count}</strong></span>
                      <span>Density: {reg.density_per_10k_px.toFixed(2)}/10k px</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-xs text-slate-400 text-center py-4">No regions configured.</div>
            )}
          </div>
        </div>
      </div>

      {/* Real-time Trend Charts */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-700/60 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-base font-semibold text-white flex items-center space-x-2">
              <TrendingUp className="w-4 h-4 text-cyan-400" />
              <span>Real-Time People Counting & Density Trends</span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Comparative visualization of Active Tracked People vs Frame Detections vs Continuous Density Regression
            </p>
          </div>
          <div className="flex items-center space-x-4 text-xs font-medium">
            <span className="flex items-center space-x-1.5 text-emerald-400">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
              <span>Active Tracked</span>
            </span>
            <span className="flex items-center space-x-1.5 text-cyan-400">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400"></span>
              <span>Detections</span>
            </span>
            <span className="flex items-center space-x-1.5 text-amber-400">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-400"></span>
              <span>Density Map Count</span>
            </span>
          </div>
        </div>

        <div className="h-64 w-full">
          {historyData.length > 1 ? (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={historyData}>
                <defs>
                  <linearGradient id="colorTracked" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10B981" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#10B981" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="colorDetected" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#06B6D4" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#06B6D4" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                <XAxis dataKey="time" stroke="#64748B" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748B" fontSize={11} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0F172A',
                    borderColor: '#334155',
                    borderRadius: '8px',
                    fontSize: '12px',
                    color: '#F8FAFC'
                  }}
                />
                <Area type="monotone" dataKey="tracked" stroke="#10B981" strokeWidth={2} fillOpacity={1} fill="url(#colorTracked)" name="Active Tracked" />
                <Area type="monotone" dataKey="detected" stroke="#06B6D4" strokeWidth={2} fillOpacity={1} fill="url(#colorDetected)" name="Frame Detections" />
                <Area type="monotone" dataKey="density" stroke="#F59E0B" strokeWidth={1.5} fillOpacity={0} name="Density Regression" />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex items-center justify-center text-slate-500 text-xs">
              Waiting for telemetry frames to record trend curve...
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
