import React, { useState, useEffect } from 'react';
import {
  BarChart3,
  Download,
  Calendar,
  Layers,
  TrendingUp,
  Clock,
  Users,
  Filter,
  FileSpreadsheet,
  FileCode
} from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend
} from 'recharts';
import { apiService } from '../services/api';
import { SessionItem, AnalyticsSnapshot } from '../types';

export const AnalyticsPage: React.FC = () => {
  const [sessions, setSessions] = useState<SessionItem[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string>('');
  const [snapshots, setSnapshots] = useState<AnalyticsSnapshot[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [sessRes, sumRes] = await Promise.all([
          apiService.getSessions(30),
          apiService.getReportsSummary()
        ]);
        if (sessRes.data && sessRes.data.sessions) {
          setSessions(sessRes.data.sessions);
          if (sessRes.data.sessions.length > 0 && !selectedSessionId) {
            setSelectedSessionId(sessRes.data.sessions[0].session_id);
          }
        }
        if (sumRes.data) {
          setSummary(sumRes.data);
        }
      } catch (e) {
        console.error('Error loading analytics:', e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  useEffect(() => {
    const loadSnapshots = async () => {
      try {
        const res = await apiService.getAnalyticsHistory(selectedSessionId || undefined, 150);
        if (res.data && res.data.snapshots) {
          setSnapshots(res.data.snapshots);
        }
      } catch (e) {
        console.error('Error fetching snapshots:', e);
      }
    };
    loadSnapshots();
  }, [selectedSessionId]);

  const chartData = snapshots.map((s) => ({
    time: new Date(s.timestamp * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    tracked: s.active_tracked_count,
    detected: s.detection_count,
    density: s.density_estimate,
    hybrid: s.hybrid_estimate,
    occlusion: (s.occlusion_index * 100).toFixed(0),
    fps: s.processing_fps
  }));

  return (
    <div className="space-y-6">
      {/* Header & Export Actions */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center space-x-2">
            <BarChart3 className="w-6 h-6 text-cyan-400" />
            <span>Crowd Analytics & Historical Reporting</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Historical crowd telemetry, peak periods, occupancy aggregations, and scientific exports.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <a
            href={apiService.getExportCsvUrl(selectedSessionId)}
            download
            className="flex items-center space-x-1.5 px-3.5 py-2 text-xs font-semibold rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-all shadow-md"
          >
            <FileSpreadsheet className="w-4 h-4 text-emerald-400" />
            <span>Export CSV</span>
          </a>

          <a
            href={apiService.getExportJsonUrl(selectedSessionId)}
            download
            className="flex items-center space-x-1.5 px-3.5 py-2 text-xs font-semibold rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-all shadow-md"
          >
            <FileCode className="w-4 h-4 text-cyan-400" />
            <span>Export JSON</span>
          </a>
        </div>
      </div>

      {/* Summary KPI Cards */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="glass-panel p-4 rounded-xl border border-slate-700/60">
            <div className="text-xs font-medium text-slate-400 uppercase">Total Sessions</div>
            <div className="text-2xl font-bold text-white mt-1">{summary.total_sessions}</div>
          </div>
          <div className="glass-panel p-4 rounded-xl border border-slate-700/60">
            <div className="text-xs font-medium text-slate-400 uppercase">Peak Recorded Crowd</div>
            <div className="text-2xl font-bold text-cyan-400 mt-1">{summary.peak_crowd_count} people</div>
          </div>
          <div className="glass-panel p-4 rounded-xl border border-slate-700/60">
            <div className="text-xs font-medium text-slate-400 uppercase">Average Occupancy</div>
            <div className="text-2xl font-bold text-emerald-400 mt-1">{summary.average_crowd_count} people</div>
          </div>
          <div className="glass-panel p-4 rounded-xl border border-slate-700/60">
            <div className="text-xs font-medium text-slate-400 uppercase">Total Alerts Raised</div>
            <div className="text-2xl font-bold text-amber-400 mt-1">{summary.total_alerts}</div>
          </div>
        </div>
      )}

      {/* Session Filter Bar */}
      <div className="glass-panel p-4 rounded-xl border border-slate-700/60 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Filter className="w-4 h-4 text-cyan-400" />
          <span className="text-xs font-semibold text-slate-300">Filter by Session:</span>
          <select
            value={selectedSessionId}
            onChange={(e) => setSelectedSessionId(e.target.value)}
            className="px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500 font-mono"
          >
            <option value="">-- All Recent Snapshots --</option>
            {sessions.map((s) => (
              <option key={s.session_id} value={s.session_id}>
                {s.session_id} ({s.source_type} | {new Date(s.start_time * 1000).toLocaleTimeString()})
              </option>
            ))}
          </select>
        </div>

        <div className="text-xs text-slate-400 font-mono">
          Showing {snapshots.length} recorded data points
        </div>
      </div>

      {/* Main Analytical Chart */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-700/60 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-white flex items-center space-x-2">
            <TrendingUp className="w-4 h-4 text-emerald-400" />
            <span>Timeline Crowd Occupancy & Occlusion Correlation</span>
          </h3>
          <div className="text-xs text-slate-400">Chronological telemetry interval</div>
        </div>

        <div className="h-72 w-full">
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                <XAxis dataKey="time" stroke="#64748B" fontSize={11} />
                <YAxis stroke="#64748B" fontSize={11} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0F172A',
                    borderColor: '#334155',
                    borderRadius: '8px',
                    fontSize: '12px',
                    color: '#F8FAFC'
                  }}
                />
                <Legend />
                <Line type="monotone" dataKey="tracked" stroke="#10B981" strokeWidth={2} name="Active Tracked" dot={false} />
                <Line type="monotone" dataKey="detected" stroke="#06B6D4" strokeWidth={2} name="Detections" dot={false} />
                <Line type="monotone" dataKey="hybrid" stroke="#6366F1" strokeWidth={1.5} name="Hybrid Fused" dot={false} />
                <Line type="monotone" dataKey="occlusion" stroke="#F59E0B" strokeWidth={1.5} strokeDasharray="4 4" name="Occlusion Index %" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex items-center justify-center text-slate-500 text-xs">
              No snapshot data recorded for selected session.
            </div>
          )}
        </div>
      </div>

      {/* Session History Table */}
      <div className="glass-panel p-5 rounded-2xl border border-slate-700/60 shadow-xl">
        <h3 className="text-sm font-semibold text-white mb-4 flex items-center space-x-2">
          <Clock className="w-4 h-4 text-cyan-400" />
          <span>Session Processing Log</span>
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/80 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Session ID</th>
                <th className="py-3 px-4">Source</th>
                <th className="py-3 px-4">Model & Tracker</th>
                <th className="py-3 px-4">Started At</th>
                <th className="py-3 px-4 text-center">Peak Count</th>
                <th className="py-3 px-4 text-center">Avg Count</th>
                <th className="py-3 px-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {sessions.map((s) => (
                <tr key={s.session_id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="py-3 px-4 font-mono font-medium text-cyan-300">{s.session_id}</td>
                  <td className="py-3 px-4 text-slate-300">{s.source_type} ({s.source_path})</td>
                  <td className="py-3 px-4 text-slate-400 font-mono">{s.model_name} / {s.tracker_type}</td>
                  <td className="py-3 px-4 text-slate-400">{new Date(s.start_time * 1000).toLocaleString()}</td>
                  <td className="py-3 px-4 text-center font-bold text-white">{s.peak_count}</td>
                  <td className="py-3 px-4 text-center text-emerald-400 font-bold">{s.avg_count.toFixed(1)}</td>
                  <td className="py-3 px-4">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                      s.status === 'active' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40' : 'bg-slate-800 text-slate-400'
                    }`}>
                      {s.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
