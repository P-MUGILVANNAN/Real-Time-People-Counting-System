import React, { useState, useEffect } from 'react';
import {
  Bell,
  Settings,
  ShieldAlert,
  AlertTriangle,
  AlertCircle,
  CheckCircle2,
  Save,
  MapPin,
  CircleDot,
  Cpu,
  RefreshCw
} from 'lucide-react';
import { apiService } from '../services/api';
import { AlertItem, ModelsStatus } from '../types';

export const AlertsSettingsPage: React.FC = () => {
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [moderateThresh, setModerateThresh] = useState<number>(10);
  const [highThresh, setHighThresh] = useState<number>(25);
  const [criticalThresh, setCriticalThresh] = useState<number>(50);
  const [cooldown, setCooldown] = useState<number>(15);
  const [saveMsg, setSaveMsg] = useState<string>('');
  const [modelsStatus, setModelsStatus] = useState<ModelsStatus | null>(null);

  // New region form
  const [regName, setRegName] = useState<string>('West Lobby');
  const [regPolyStr, setRegPolyStr] = useState<string>('[[50, 50], [550, 50], [550, 400], [50, 400]]');

  // New line form
  const [lineName, setLineName] = useState<string>('Corridor Tripwire');
  const [lineStart, setLineStart] = useState<string>('50, 240');
  const [lineEnd, setLineEnd] = useState<string>('590, 240');

  const fetchAlerts = async () => {
    try {
      const res = await apiService.getAlerts(50);
      if (res.data && res.data.alerts) {
        setAlerts(res.data.alerts);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchStatus = async () => {
    try {
      const res = await apiService.getModelsStatus();
      if (res.data) setModelsStatus(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchAlerts();
    fetchStatus();
  }, []);

  const handleAck = async (id: string) => {
    try {
      await apiService.acknowledgeAlert(id);
      fetchAlerts();
    } catch (e) {
      console.error(e);
    }
  };

  const handleSaveThresholds = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiService.updateThresholds({
        moderate_crowd_threshold: moderateThresh,
        high_crowd_threshold: highThresh,
        critical_crowd_threshold: criticalThresh,
        alert_cooldown_seconds: cooldown
      });
      setSaveMsg('Crowd alert thresholds successfully updated in system memory.');
      setTimeout(() => setSaveMsg(''), 4000);
    } catch (e) {
      setSaveMsg('Error saving thresholds.');
      setTimeout(() => setSaveMsg(''), 4000);
    }
  };

  const handleAddRegion = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const polygon = JSON.parse(regPolyStr);
      const regId = `roi_${Date.now()}`;
      await apiService.createRegion({
        region_id: regId,
        name: regName,
        polygon,
        moderate_thresh: moderateThresh,
        high_thresh: highThresh,
        critical_thresh: criticalThresh
      });
      setSaveMsg(`Region '${regName}' created successfully.`);
      setTimeout(() => setSaveMsg(''), 4000);
    } catch (e) {
      alert('Invalid polygon JSON. Expected array of [x, y] coordinates: [[x1, y1], [x2, y2], ...]');
    }
  };

  const handleAddLine = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const startPt = lineStart.split(',').map((v) => parseInt(v.trim()));
      const endPt = lineEnd.split(',').map((v) => parseInt(v.trim()));
      const lineId = `line_${Date.now()}`;
      await apiService.createLine({
        line_id: lineId,
        name: lineName,
        start_pt: startPt,
        end_pt: endPt
      });
      setSaveMsg(`Tripwire '${lineName}' configured successfully.`);
      setTimeout(() => setSaveMsg(''), 4000);
    } catch (e) {
      alert('Invalid coordinates. Use format "x, y" (e.g. "50, 240")');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-white flex items-center space-x-2">
          <Settings className="w-6 h-6 text-cyan-400" />
          <span>System Alerts & Spatial Configuration</span>
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Adjust multi-tier crowd density alert triggers, acknowledge active incidents, and configure spatial regions of interest.
        </p>
      </div>

      {saveMsg && (
        <div className="p-3 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 text-xs flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
          <span>{saveMsg}</span>
        </div>
      )}

      {/* Grid: Alert Log and Configuration */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Alerts History Table */}
        <div className="lg:col-span-2 glass-panel p-5 rounded-2xl border border-slate-700/60 shadow-xl space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white flex items-center space-x-2">
              <Bell className="w-4 h-4 text-amber-400" />
              <span>Historical Crowd Incident Logs ({alerts.length})</span>
            </h3>
            <button onClick={fetchAlerts} className="text-slate-400 hover:text-cyan-400 text-xs flex items-center space-x-1">
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Refresh</span>
            </button>
          </div>

          <div className="overflow-x-auto max-h-96">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900/80 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800 sticky top-0">
                <tr>
                  <th className="py-2.5 px-3">Severity</th>
                  <th className="py-2.5 px-3">Incident Message</th>
                  <th className="py-2.5 px-3 text-center">Value / Threshold</th>
                  <th className="py-2.5 px-3">Timestamp</th>
                  <th className="py-2.5 px-3 text-center">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {alerts.length > 0 ? (
                  alerts.map((a) => (
                    <tr key={a.alert_id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="py-2.5 px-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                          a.severity === 'critical'
                            ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                            : a.severity === 'high'
                            ? 'bg-orange-500/20 text-orange-300 border border-orange-500/40'
                            : 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                        }`}>
                          {a.severity}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-slate-200 font-medium">{a.message}</td>
                      <td className="py-2.5 px-3 text-center font-mono text-cyan-400">
                        {a.metric_value} / {a.threshold_value}
                      </td>
                      <td className="py-2.5 px-3 text-slate-400">
                        {new Date(a.timestamp * 1000).toLocaleTimeString()}
                      </td>
                      <td className="py-2.5 px-3 text-center">
                        {a.acknowledged ? (
                          <span className="text-emerald-400 font-medium text-[11px] flex items-center justify-center space-x-1">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span>Ack'd</span>
                          </span>
                        ) : (
                          <button
                            onClick={() => handleAck(a.alert_id)}
                            className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-white border border-slate-700 text-[11px]"
                          >
                            Ack
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-slate-500">
                      No crowd incidents triggered. System operating within normal thresholds.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right Column: Thresholds and Spatial Setup */}
        <div className="space-y-6">
          {/* Thresholds Form */}
          <div className="glass-panel p-5 rounded-2xl border border-slate-700/60 shadow-xl space-y-4">
            <h3 className="text-sm font-semibold text-white flex items-center space-x-2">
              <ShieldAlert className="w-4 h-4 text-cyan-400" />
              <span>Crowd Thresholds</span>
            </h3>

            <form onSubmit={handleSaveThresholds} className="space-y-3 text-xs">
              <div>
                <label className="text-slate-400 block font-medium mb-1">Moderate Notice (People)</label>
                <input
                  type="number"
                  min="1"
                  value={moderateThresh}
                  onChange={(e) => setModerateThresh(parseInt(e.target.value) || 1)}
                  className="w-full px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-white font-mono"
                />
              </div>

              <div>
                <label className="text-slate-400 block font-medium mb-1">High Warning (People)</label>
                <input
                  type="number"
                  min="2"
                  value={highThresh}
                  onChange={(e) => setHighThresh(parseInt(e.target.value) || 2)}
                  className="w-full px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-white font-mono"
                />
              </div>

              <div>
                <label className="text-slate-400 block font-medium mb-1">Critical Evacuation Alarm</label>
                <input
                  type="number"
                  min="3"
                  value={criticalThresh}
                  onChange={(e) => setCriticalThresh(parseInt(e.target.value) || 3)}
                  className="w-full px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-white font-mono"
                />
              </div>

              <div>
                <label className="text-slate-400 block font-medium mb-1">Alert Cooldown (Seconds)</label>
                <input
                  type="number"
                  min="1"
                  value={cooldown}
                  onChange={(e) => setCooldown(parseFloat(e.target.value) || 15)}
                  className="w-full px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-white font-mono"
                />
              </div>

              <button
                type="submit"
                className="w-full py-2 px-3 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-semibold flex items-center justify-center space-x-1.5 transition-all"
              >
                <Save className="w-3.5 h-3.5" />
                <span>Save Alert Thresholds</span>
              </button>
            </form>
          </div>

          {/* Add Polygonal ROI Form */}
          <div className="glass-panel p-5 rounded-2xl border border-slate-700/60 shadow-xl space-y-4">
            <h3 className="text-sm font-semibold text-white flex items-center space-x-2">
              <MapPin className="w-4 h-4 text-teal-400" />
              <span>Define Region of Interest</span>
            </h3>

            <form onSubmit={handleAddRegion} className="space-y-3 text-xs">
              <div>
                <label className="text-slate-400 block font-medium mb-1">Region Label</label>
                <input
                  type="text"
                  value={regName}
                  onChange={(e) => setRegName(e.target.value)}
                  className="w-full px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-white"
                />
              </div>

              <div>
                <label className="text-slate-400 block font-medium mb-1">Polygon Coordinates JSON</label>
                <input
                  type="text"
                  value={regPolyStr}
                  onChange={(e) => setRegPolyStr(e.target.value)}
                  className="w-full px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-white font-mono text-[11px]"
                />
              </div>

              <button
                type="submit"
                className="w-full py-2 px-3 rounded-lg bg-teal-600 hover:bg-teal-500 text-white font-semibold flex items-center justify-center space-x-1.5 transition-all"
              >
                <span>Add Spatial Region</span>
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};
