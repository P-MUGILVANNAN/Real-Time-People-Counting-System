import React, { useState, useEffect } from 'react';
import {
  FlaskConical,
  Play,
  RotateCcw,
  CheckCircle2,
  Clock,
  Layers,
  Database,
  BarChart,
  Download
} from 'lucide-react';
import { apiService } from '../services/api';
import { ExperimentItem } from '../types';

export const ExperimentCenterPage: React.FC = () => {
  const [experiments, setExperiments] = useState<ExperimentItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [running, setRunning] = useState<boolean>(false);
  const [selectedExp, setSelectedExp] = useState<ExperimentItem | null>(null);

  // Form parameters
  const [name, setName] = useState<string>('CrowdHuman_Occlusion_Ablation');
  const [dataset, setDataset] = useState<string>('crowdhuman');
  const [modelType, setModelType] = useState<string>('hybrid');
  const [trackerType, setTrackerType] = useState<string>('bytetrack');
  const [confThresh, setConfThresh] = useState<number>(0.35);
  const [iouThresh, setIouThresh] = useState<number>(0.45);
  const [crowdGroup, setCrowdGroup] = useState<string>('all');
  const [statusMsg, setStatusMsg] = useState<string>('');

  const fetchExperiments = async () => {
    try {
      const res = await apiService.getExperiments();
      if (res.data && res.data.experiments) {
        setExperiments(res.data.experiments);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExperiments();
    const timer = setInterval(fetchExperiments, 5000);
    return () => clearInterval(timer);
  }, []);

  const handleRunExperiment = async (e: React.FormEvent) => {
    e.preventDefault();
    setRunning(true);
    setStatusMsg('');
    try {
      await apiService.runExperiment({
        name,
        dataset_name: dataset,
        model_type: modelType,
        tracker_type: trackerType,
        confidence_thresh: confThresh,
        iou_thresh: iouThresh,
        crowding_group: crowdGroup
      });
      setStatusMsg(`Experiment '${name}' dispatched to background evaluation runner.`);
      setTimeout(() => {
        fetchExperiments();
        setRunning(false);
      }, 1500);
    } catch (err: any) {
      setStatusMsg('Failed to dispatch experiment.');
      setRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-white flex items-center space-x-2">
          <FlaskConical className="w-6 h-6 text-purple-400" />
          <span>Research Experiment Center</span>
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Launch automated evaluation jobs, benchmark detection & tracking under varying occlusion proxies, and record reproducible metrics.
        </p>
      </div>

      {/* Grid: Form on Left, History Table on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Experiment Configuration Form */}
        <div className="glass-panel p-5 rounded-2xl border border-slate-700/60 shadow-xl space-y-4">
          <h3 className="text-sm font-semibold text-white flex items-center space-x-2">
            <Layers className="w-4 h-4 text-cyan-400" />
            <span>Configure Benchmark Run</span>
          </h3>

          <form onSubmit={handleRunExperiment} className="space-y-3.5 text-xs">
            <div>
              <label className="text-slate-400 block font-medium mb-1">Experiment Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-cyan-500 font-mono"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-slate-400 block font-medium mb-1">Dataset</label>
                <select
                  value={dataset}
                  onChange={(e) => setDataset(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-cyan-500"
                >
                  <option value="crowdhuman">CrowdHuman (Dense Boxes)</option>
                  <option value="shanghaitech">ShanghaiTech (Part B Points)</option>
                </select>
              </div>

              <div>
                <label className="text-slate-400 block font-medium mb-1">Model Architecture</label>
                <select
                  value={modelType}
                  onChange={(e) => setModelType(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-cyan-500"
                >
                  <option value="hybrid">Hybrid Fused (Ours)</option>
                  <option value="yolo">YOLOv8 Baseline</option>
                  <option value="mcnn">MCNN Density Regression</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-slate-400 block font-medium mb-1">Tracker</label>
                <select
                  value={trackerType}
                  onChange={(e) => setTrackerType(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-cyan-500"
                >
                  <option value="bytetrack">ByteTrack</option>
                  <option value="botsort">BoT-SORT</option>
                </select>
              </div>

              <div>
                <label className="text-slate-400 block font-medium mb-1">Crowding Regime</label>
                <select
                  value={crowdGroup}
                  onChange={(e) => setCrowdGroup(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-cyan-500"
                >
                  <option value="all">All Groups (Composite)</option>
                  <option value="low">Low Crowding (SOI &lt; 0.2)</option>
                  <option value="moderate">Moderate (0.2 &le; SOI &lt; 0.45)</option>
                  <option value="high">High Crowding (0.45 &le; SOI &lt; 0.7)</option>
                  <option value="severe">Severe Crowding (SOI &ge; 0.7)</option>
                </select>
              </div>
            </div>

            <div>
              <div className="flex justify-between text-slate-400 mb-1">
                <span>Confidence Threshold</span>
                <span className="font-mono text-cyan-300">{confThresh.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0.1"
                max="0.8"
                step="0.05"
                value={confThresh}
                onChange={(e) => setConfThresh(parseFloat(e.target.value))}
                className="w-full accent-cyan-400"
              />
            </div>

            <div>
              <div className="flex justify-between text-slate-400 mb-1">
                <span>IoU Association Threshold</span>
                <span className="font-mono text-cyan-300">{iouThresh.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0.2"
                max="0.8"
                step="0.05"
                value={iouThresh}
                onChange={(e) => setIouThresh(parseFloat(e.target.value))}
                className="w-full accent-cyan-400"
              />
            </div>

            {statusMsg && (
              <div className="p-2.5 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 text-xs">
                {statusMsg}
              </div>
            )}

            <button
              type="submit"
              disabled={running}
              className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-semibold flex items-center justify-center space-x-2 shadow-lg shadow-purple-600/20 transition-all disabled:opacity-50"
            >
              <Play className="w-4 h-4 fill-current" />
              <span>{running ? 'Dispatching...' : 'Run Experiment (Background)'}</span>
            </button>
          </form>
        </div>

        {/* Experiment Results History */}
        <div className="lg:col-span-2 glass-panel p-5 rounded-2xl border border-slate-700/60 shadow-xl space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white flex items-center space-x-2">
              <Database className="w-4 h-4 text-emerald-400" />
              <span>Saved Experiment Records ({experiments.length})</span>
            </h3>
            <button onClick={fetchExperiments} className="text-slate-400 hover:text-cyan-400 text-xs flex items-center space-x-1">
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Refresh</span>
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900/80 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
                <tr>
                  <th className="py-3 px-3">Experiment</th>
                  <th className="py-3 px-3">Model</th>
                  <th className="py-3 px-3">Regime</th>
                  <th className="py-3 px-3 text-center">MAE</th>
                  <th className="py-3 px-3 text-center">RMSE</th>
                  <th className="py-3 px-3 text-center">F1</th>
                  <th className="py-3 px-3 text-center">FPS</th>
                  <th className="py-3 px-3 text-center">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {experiments.length > 0 ? (
                  experiments.map((e) => (
                    <tr key={e.experiment_id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="py-3 px-3 font-sans font-medium text-slate-200">
                        <div className="font-semibold text-cyan-300">{e.name}</div>
                        <div className="text-[10px] text-slate-400 font-mono">{e.experiment_id}</div>
                      </td>
                      <td className="py-3 px-3 text-slate-300 font-sans uppercase text-[11px] font-semibold">{e.model_type}</td>
                      <td className="py-3 px-3 text-slate-400 font-sans">{e.crowding_group}</td>
                      <td className="py-3 px-3 text-center font-bold text-emerald-400">{e.mae.toFixed(2)}</td>
                      <td className="py-3 px-3 text-center text-slate-300">{e.rmse.toFixed(2)}</td>
                      <td className="py-3 px-3 text-center text-cyan-400">{e.f1.toFixed(3)}</td>
                      <td className="py-3 px-3 text-center text-slate-400">{e.fps.toFixed(1)}</td>
                      <td className="py-3 px-3 text-center font-sans">
                        <button
                          onClick={() => setSelectedExp(e)}
                          className="px-2.5 py-1 text-[11px] rounded bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-slate-700"
                        >
                          View
                        </button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={8} className="py-8 text-center text-slate-500 font-sans">
                      No experiments recorded yet. Fill out the configuration and launch a benchmark!
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Detailed Experiment Modal / Card */}
          {selectedExp && (
            <div className="mt-4 p-4 rounded-xl bg-slate-900/90 border border-cyan-500/30 space-y-3 animate-fadeIn">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <span className="font-semibold text-white text-xs">
                  Experiment Details: <span className="text-cyan-400">{selectedExp.name}</span>
                </span>
                <button
                  onClick={() => setSelectedExp(null)}
                  className="text-slate-400 hover:text-white text-xs px-2 py-0.5 rounded bg-slate-800"
                >
                  Close
                </button>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                <div>
                  <span className="text-slate-500 block">Mean Abs Error (MAE):</span>
                  <span className="font-mono font-bold text-emerald-400">{selectedExp.mae.toFixed(3)}</span>
                </div>
                <div>
                  <span className="text-slate-500 block">Root Mean Sq (RMSE):</span>
                  <span className="font-mono font-bold text-slate-200">{selectedExp.rmse.toFixed(3)}</span>
                </div>
                <div>
                  <span className="text-slate-500 block">Mean Latency:</span>
                  <span className="font-mono text-cyan-400">{selectedExp.mean_latency_ms.toFixed(1)} ms</span>
                </div>
                <div>
                  <span className="text-slate-500 block">Detection Precision / Recall:</span>
                  <span className="font-mono text-slate-300">{(selectedExp.precision * 100).toFixed(0)}% / {(selectedExp.recall * 100).toFixed(0)}%</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
