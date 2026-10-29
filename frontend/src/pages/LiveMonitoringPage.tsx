import React, { useState, useEffect } from 'react';
import {
  Play,
  Square,
  Pause,
  Upload,
  Camera,
  Film,
  Sliders,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Video
} from 'lucide-react';
import { apiService } from '../services/api';
import { VideoPlayer } from '../components/VideoPlayer';
import { TelemetryStats } from '../types';

interface LiveMonitoringPageProps {
  stats: TelemetryStats;
}

export const LiveMonitoringPage: React.FC<LiveMonitoringPageProps> = ({ stats }) => {
  const [sourceMode, setSourceMode] = useState<'sample' | 'webcam' | 'upload'>('sample');
  const [cameraIndex, setCameraIndex] = useState<number>(0);
  const [selectedFile, setSelectedFile] = useState<string>('crowd_sample.mp4');
  const [videoFiles, setVideoFiles] = useState<any[]>([]);
  const [trackerType, setTrackerType] = useState<string>('bytetrack');
  const [confidence, setConfidence] = useState<number>(0.35);
  const [iou, setIou] = useState<number>(0.45);
  const [uploading, setUploading] = useState<boolean>(false);
  const [statusMsg, setStatusMsg] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const fetchVideos = async () => {
    try {
      const res = await apiService.getVideoFiles();
      if (res.data && res.data.videos) {
        setVideoFiles(res.data.videos);
        if (res.data.videos.length > 0 && !selectedFile) {
          setSelectedFile(res.data.videos[0].filename);
        }
      }
    } catch (e) {
      console.error('Error fetching videos:', e);
    }
  };

  useEffect(() => {
    fetchVideos();
  }, []);

  const handleStart = async () => {
    setStatusMsg(null);
    try {
      if (sourceMode === 'webcam') {
        await apiService.startCamera(cameraIndex, trackerType, confidence);
        setStatusMsg({ text: `Camera ${cameraIndex} stream started successfully.`, type: 'success' });
      } else {
        await apiService.startVideo(selectedFile, trackerType, confidence);
        setStatusMsg({ text: `Video '${selectedFile}' processing started.`, type: 'success' });
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to start source. Verify camera or video file.';
      setStatusMsg({ text: msg, type: 'error' });
    }
  };

  const handleStop = async () => {
    try {
      if (sourceMode === 'webcam') {
        await apiService.stopCamera();
      } else {
        await apiService.stopVideo();
      }
      setStatusMsg({ text: 'Inference pipeline stopped.', type: 'success' });
    } catch (e) {
      console.error(e);
    }
  };

  const handlePauseResume = async () => {
    try {
      if (stats.is_paused) {
        await apiService.resumeVideo();
      } else {
        await apiService.pauseVideo();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];
    setUploading(true);
    setStatusMsg(null);
    try {
      const res = await apiService.uploadVideo(file);
      setStatusMsg({ text: `Uploaded '${res.data.filename}' successfully.`, type: 'success' });
      await fetchVideos();
      setSelectedFile(res.data.filename);
      setSourceMode('upload');
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Upload failed.';
      setStatusMsg({ text: msg, type: 'error' });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Status Alert Banner if present */}
      {statusMsg && (
        <div className={`p-4 rounded-xl border flex items-center space-x-3 text-sm ${
          statusMsg.type === 'success'
            ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
            : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
        }`}>
          {statusMsg.type === 'success' ? <CheckCircle2 className="w-5 h-5 flex-shrink-0" /> : <AlertTriangle className="w-5 h-5 flex-shrink-0" />}
          <span>{statusMsg.text}</span>
        </div>
      )}

      {/* Main Layout: Video on Left, Configuration & Controls on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Big Live Video Screen */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-white flex items-center space-x-2">
              <Video className="w-5 h-5 text-cyan-400" />
              <span>Real-Time Annotated Inference Monitor</span>
            </h2>
            <div className="flex items-center space-x-3 text-xs">
              <span className="font-mono text-slate-400">
                Resolution: <strong className="text-slate-200">640x480</strong>
              </span>
              <span className="font-mono text-slate-400">
                Frame: <strong className="text-cyan-400">#{stats.frame_index}</strong>
              </span>
            </div>
          </div>

          <VideoPlayer stats={stats} />
        </div>

        {/* Right: Source & Hyperparameter Controls */}
        <div className="space-y-6">
          {/* Source Selector Card */}
          <div className="glass-panel p-5 rounded-2xl border border-slate-700/60 shadow-xl space-y-4">
            <h3 className="text-sm font-semibold text-white flex items-center space-x-2">
              <Sliders className="w-4 h-4 text-cyan-400" />
              <span>Input Stream Source</span>
            </h3>

            {/* Mode selection buttons */}
            <div className="grid grid-cols-3 gap-2">
              <button
                onClick={() => setSourceMode('sample')}
                className={`py-2 px-3 rounded-lg text-xs font-semibold flex items-center justify-center space-x-1.5 transition-all border ${
                  sourceMode === 'sample'
                    ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40 shadow-md'
                    : 'bg-slate-800/80 text-slate-400 border-slate-700 hover:text-slate-200'
                }`}
              >
                <Film className="w-3.5 h-3.5" />
                <span>Sample</span>
              </button>

              <button
                onClick={() => setSourceMode('webcam')}
                className={`py-2 px-3 rounded-lg text-xs font-semibold flex items-center justify-center space-x-1.5 transition-all border ${
                  sourceMode === 'webcam'
                    ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40 shadow-md'
                    : 'bg-slate-800/80 text-slate-400 border-slate-700 hover:text-slate-200'
                }`}
              >
                <Camera className="w-3.5 h-3.5" />
                <span>Webcam</span>
              </button>

              <button
                onClick={() => setSourceMode('upload')}
                className={`py-2 px-3 rounded-lg text-xs font-semibold flex items-center justify-center space-x-1.5 transition-all border ${
                  sourceMode === 'upload'
                    ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40 shadow-md'
                    : 'bg-slate-800/80 text-slate-400 border-slate-700 hover:text-slate-200'
                }`}
              >
                <Upload className="w-3.5 h-3.5" />
                <span>Upload</span>
              </button>
            </div>

            {/* Source Specific Configuration */}
            {sourceMode === 'webcam' ? (
              <div className="space-y-2">
                <label className="text-xs text-slate-400 block font-medium">Camera Index</label>
                <input
                  type="number"
                  min="0"
                  max="5"
                  value={cameraIndex}
                  onChange={(e) => setCameraIndex(parseInt(e.target.value) || 0)}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-cyan-500 font-mono"
                />
                <p className="text-[11px] text-slate-500">
                  Standard built-in webcam is usually Index 0. External USB cameras use 1 or 2.
                </p>
              </div>
            ) : sourceMode === 'sample' ? (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-xs text-slate-400 block font-medium">Select Sample Video</label>
                  <button onClick={fetchVideos} className="text-slate-400 hover:text-cyan-400 p-1">
                    <RefreshCw className="w-3 h-3" />
                  </button>
                </div>
                <select
                  value={selectedFile}
                  onChange={(e) => setSelectedFile(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                >
                  {videoFiles.map((v) => (
                    <option key={v.filename} value={v.filename}>
                      {v.filename} ({v.location}, {v.size_mb} MB)
                    </option>
                  ))}
                </select>
                <p className="text-[11px] text-slate-500">
                  Built-in multi-person crowd video generated for zero-download demonstration.
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                <label className="text-xs text-slate-400 block font-medium">Upload Custom Video</label>
                <label className="flex flex-col items-center justify-center border-2 border-dashed border-slate-700 hover:border-cyan-500/60 rounded-xl p-4 cursor-pointer bg-slate-900/50 transition-all">
                  <Upload className="w-6 h-6 text-cyan-400 mb-1" />
                  <span className="text-xs text-slate-300 font-medium">
                    {uploading ? 'Uploading...' : 'Choose MP4, AVI, or MOV'}
                  </span>
                  <input
                    type="file"
                    accept="video/mp4,video/avi,video/quicktime"
                    className="hidden"
                    onChange={handleFileUpload}
                    disabled={uploading}
                  />
                </label>
              </div>
            )}

            {/* Model & Tracker Controls */}
            <div className="border-t border-slate-800 pt-4 space-y-3">
              <div>
                <label className="text-xs text-slate-400 block font-medium mb-1">Tracker Algorithm</label>
                <select
                  value={trackerType}
                  onChange={(e) => setTrackerType(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                >
                  <option value="bytetrack">ByteTrack (Low-confidence association, best for occlusion)</option>
                  <option value="botsort">BoT-SORT (Motion + Camera compensation)</option>
                </select>
              </div>

              <div>
                <div className="flex justify-between text-xs text-slate-400 mb-1">
                  <span>Confidence Threshold</span>
                  <span className="font-mono text-cyan-300">{confidence.toFixed(2)}</span>
                </div>
                <input
                  type="range"
                  min="0.1"
                  max="0.9"
                  step="0.05"
                  value={confidence}
                  onChange={(e) => setConfidence(parseFloat(e.target.value))}
                  className="w-full accent-cyan-400 cursor-pointer"
                />
              </div>

              <div>
                <div className="flex justify-between text-xs text-slate-400 mb-1">
                  <span>IoU Matching Threshold</span>
                  <span className="font-mono text-cyan-300">{iou.toFixed(2)}</span>
                </div>
                <input
                  type="range"
                  min="0.1"
                  max="0.9"
                  step="0.05"
                  value={iou}
                  onChange={(e) => setIou(parseFloat(e.target.value))}
                  className="w-full accent-cyan-400 cursor-pointer"
                />
              </div>
            </div>

            {/* Execution Buttons */}
            <div className="pt-2 flex items-center space-x-2">
              {!stats.is_running ? (
                <button
                  onClick={handleStart}
                  className="flex-1 py-2.5 px-4 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-semibold text-xs flex items-center justify-center space-x-2 shadow-lg shadow-cyan-500/20 transition-all"
                >
                  <Play className="w-4 h-4 fill-current" />
                  <span>Start Inference</span>
                </button>
              ) : (
                <>
                  <button
                    onClick={handlePauseResume}
                    className="flex-1 py-2.5 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-semibold text-xs flex items-center justify-center space-x-1.5 border border-slate-700 transition-all"
                  >
                    <Pause className="w-3.5 h-3.5" />
                    <span>{stats.is_paused ? 'Resume' : 'Pause'}</span>
                  </button>

                  <button
                    onClick={handleStop}
                    className="flex-1 py-2.5 px-3 rounded-xl bg-rose-600/90 hover:bg-rose-500 text-white font-semibold text-xs flex items-center justify-center space-x-1.5 shadow-lg shadow-rose-600/20 transition-all"
                  >
                    <Square className="w-3.5 h-3.5 fill-current" />
                    <span>Stop</span>
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
