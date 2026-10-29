import React, { useState } from 'react';
import {
  Camera,
  Layers,
  Activity,
  Flame,
  Grid,
  MapPin,
  CircleDot,
  Video,
  Download,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import { apiService } from '../services/api';
import { TelemetryStats } from '../types';

interface VideoPlayerProps {
  stats: TelemetryStats;
}

export const VideoPlayer: React.FC<VideoPlayerProps> = ({ stats }) => {
  const [toggles, setToggles] = useState({
    show_boxes: true,
    show_tracks: true,
    show_trails: true,
    show_heatmap: false,
    show_density_map: false,
    show_rois: true,
    show_lines: true
  });
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [screenshotMsg, setScreenshotMsg] = useState<string>('');

  const handleToggle = async (key: keyof typeof toggles) => {
    const newVal = !toggles[key];
    setToggles(prev => ({ ...prev, [key]: newVal }));
    try {
      await apiService.toggleDisplay(key, newVal);
    } catch (e) {
      console.error('Failed to toggle overlay:', e);
    }
  };

  const handleScreenshot = async () => {
    try {
      const res = await apiService.captureScreenshot();
      setScreenshotMsg(`Saved: ${res.data.file_path}`);
      setTimeout(() => setScreenshotMsg(''), 4000);
    } catch (e) {
      setScreenshotMsg('Screenshot failed. Video may not be active.');
      setTimeout(() => setScreenshotMsg(''), 4000);
    }
  };

  const handleRecord = async () => {
    const nextState = !isRecording;
    setIsRecording(nextState);
    try {
      await apiService.toggleRecording(nextState);
    } catch (e) {
      console.error('Failed to toggle recording:', e);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'critical':
        return 'bg-rose-500/20 text-rose-300 border-rose-500/40';
      case 'high':
        return 'bg-orange-500/20 text-orange-300 border-orange-500/40';
      case 'moderate':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/40';
      default:
        return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40';
    }
  };

  return (
    <div className="glass-panel rounded-2xl overflow-hidden border border-slate-700/60 shadow-2xl flex flex-col">
      {/* Video Stream Container */}
      <div className="relative aspect-video w-full bg-slate-950 flex items-center justify-center overflow-hidden">
        {stats.is_running ? (
          <img
            src={apiService.getVideoStreamUrl()}
            alt="Live Stream"
            className="w-full h-full object-contain"
            onError={(e) => {
              (e.target as HTMLElement).style.display = 'none';
            }}
          />
        ) : (
          <div className="flex flex-col items-center justify-center text-slate-500 space-y-3 p-8 text-center">
            <div className="p-4 rounded-full bg-slate-900 border border-slate-800">
              <Video className="w-8 h-8 text-slate-600" />
            </div>
            <div>
              <div className="text-base font-semibold text-slate-300">Video Inference Idle</div>
              <div className="text-xs text-slate-400 mt-1 max-w-sm">
                Connect a webcam or select a video from the Live Monitoring tab to begin real-time detection and density tracking.
              </div>
            </div>
          </div>
        )}

        {/* Floating Top HUD */}
        {stats.is_running && (
          <div className="absolute top-3 left-3 right-3 flex items-center justify-between pointer-events-none">
            <div className="flex items-center space-x-2">
              <span className="flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-black/70 backdrop-blur-md border border-white/10 text-xs font-mono text-cyan-400">
                <span className="w-2 h-2 rounded-full bg-red-500 animate-ping mr-1" />
                LIVE | {stats.processing_fps.toFixed(1)} FPS
              </span>
              <span className={`px-2.5 py-1 rounded-lg text-xs font-bold uppercase tracking-wider border backdrop-blur-md ${getStatusBadge(stats.crowd_status)}`}>
                {stats.crowd_status} CROWD
              </span>
            </div>

            <div className="flex items-center space-x-2">
              <span className="px-2.5 py-1 rounded-lg bg-black/70 backdrop-blur-md border border-white/10 text-xs font-mono text-slate-300">
                Occlusion Index: <strong className="text-amber-400">{(stats.occlusion_index * 100).toFixed(0)}%</strong> ({stats.difficulty_category})
              </span>
            </div>
          </div>
        )}

        {/* Screenshot feedback message */}
        {screenshotMsg && (
          <div className="absolute bottom-4 left-4 bg-black/80 backdrop-blur-md border border-cyan-500/40 text-cyan-300 text-xs px-3 py-1.5 rounded-lg">
            {screenshotMsg}
          </div>
        )}
      </div>

      {/* Control Bar & Overlay Toggles */}
      <div className="p-4 bg-slate-900/80 border-t border-slate-800 flex flex-wrap items-center justify-between gap-3">
        {/* Toggles */}
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="text-xs uppercase font-semibold text-slate-400 mr-2 flex items-center space-x-1">
            <Layers className="w-3.5 h-3.5" />
            <span>Overlays:</span>
          </span>

          <button
            onClick={() => handleToggle('show_boxes')}
            className={`px-2.5 py-1 text-xs rounded-lg font-medium transition-all border ${
              toggles.show_boxes
                ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40'
                : 'bg-slate-800 text-slate-400 border-slate-700 hover:text-slate-200'
            }`}
          >
            BBoxes
          </button>

          <button
            onClick={() => handleToggle('show_tracks')}
            className={`px-2.5 py-1 text-xs rounded-lg font-medium transition-all border ${
              toggles.show_tracks
                ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                : 'bg-slate-800 text-slate-400 border-slate-700 hover:text-slate-200'
            }`}
          >
            Track IDs
          </button>

          <button
            onClick={() => handleToggle('show_trails')}
            className={`px-2.5 py-1 text-xs rounded-lg font-medium transition-all border ${
              toggles.show_trails
                ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                : 'bg-slate-800 text-slate-400 border-slate-700 hover:text-slate-200'
            }`}
          >
            Trails
          </button>

          <button
            onClick={() => handleToggle('show_heatmap')}
            className={`flex items-center space-x-1 px-2.5 py-1 text-xs rounded-lg font-medium transition-all border ${
              toggles.show_heatmap
                ? 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                : 'bg-slate-800 text-slate-400 border-slate-700 hover:text-slate-200'
            }`}
          >
            <Flame className="w-3 h-3" />
            <span>Heatmap</span>
          </button>

          <button
            onClick={() => handleToggle('show_density_map')}
            className={`flex items-center space-x-1 px-2.5 py-1 text-xs rounded-lg font-medium transition-all border ${
              toggles.show_density_map
                ? 'bg-indigo-500/20 text-indigo-300 border-indigo-500/40'
                : 'bg-slate-800 text-slate-400 border-slate-700 hover:text-slate-200'
            }`}
          >
            <Grid className="w-3 h-3" />
            <span>Density Regr</span>
          </button>

          <button
            onClick={() => handleToggle('show_rois')}
            className={`flex items-center space-x-1 px-2.5 py-1 text-xs rounded-lg font-medium transition-all border ${
              toggles.show_rois
                ? 'bg-teal-500/20 text-teal-300 border-teal-500/40'
                : 'bg-slate-800 text-slate-400 border-slate-700 hover:text-slate-200'
            }`}
          >
            <MapPin className="w-3 h-3" />
            <span>ROIs</span>
          </button>

          <button
            onClick={() => handleToggle('show_lines')}
            className={`flex items-center space-x-1 px-2.5 py-1 text-xs rounded-lg font-medium transition-all border ${
              toggles.show_lines
                ? 'bg-purple-500/20 text-purple-300 border-purple-500/40'
                : 'bg-slate-800 text-slate-400 border-slate-700 hover:text-slate-200'
            }`}
          >
            <CircleDot className="w-3 h-3" />
            <span>Tripwires</span>
          </button>
        </div>

        {/* Capture / Record Buttons */}
        <div className="flex items-center space-x-2">
          <button
            onClick={handleScreenshot}
            className="flex items-center space-x-1 px-3 py-1.5 text-xs font-medium rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-all"
          >
            <Camera className="w-3.5 h-3.5" />
            <span>Snapshot</span>
          </button>

          <button
            onClick={handleRecord}
            className={`flex items-center space-x-1 px-3 py-1.5 text-xs font-medium rounded-lg border transition-all ${
              isRecording
                ? 'bg-rose-500 text-white border-rose-600 animate-pulse'
                : 'bg-slate-800 hover:bg-slate-700 text-slate-200 border-slate-700'
            }`}
          >
            <span className={`w-2 h-2 rounded-full ${isRecording ? 'bg-white' : 'bg-rose-500'}`} />
            <span>{isRecording ? 'Stop Recording' : 'Record'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
