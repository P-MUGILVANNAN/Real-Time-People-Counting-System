import React from 'react';
import {
  BookOpen,
  Cpu,
  Layers,
  Database,
  Shield,
  FileCode,
  ExternalLink,
  Code2,
  GitBranch
} from 'lucide-react';
import { API_BASE_URL } from '../services/api';

export const DocumentationPage: React.FC = () => {
  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-white flex items-center space-x-2.5">
          <BookOpen className="w-7 h-7 text-cyan-400" />
          <span>System Architecture & Research Methodology</span>
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          Technical specifications, mathematical formulations, algorithmic workflows, and ethical privacy framework.
        </p>
      </div>

      {/* Quick Links Banner */}
      <div className="glass-panel p-4 rounded-xl border border-slate-700/60 flex items-center justify-between">
        <div className="flex items-center space-x-2 text-xs text-slate-300">
          <FileCode className="w-4 h-4 text-cyan-400" />
          <span>Interactive Swagger REST API Documentation available at:</span>
        </div>
        <a
          href={`${API_BASE_URL}/docs`}
          target="_blank"
          rel="noreferrer"
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 text-xs font-semibold transition-all"
        >
          <span>Open Swagger UI</span>
          <ExternalLink className="w-3.5 h-3.5" />
        </a>
      </div>

      {/* 1. Mathematical Formulations */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-700/60 shadow-xl space-y-4">
        <h3 className="text-base font-bold text-white flex items-center space-x-2">
          <Code2 className="w-5 h-5 text-indigo-400" />
          <span>1. Mathematical Foundations & Formulations</span>
        </h3>

        <div className="space-y-4 text-xs text-slate-300 leading-relaxed font-sans">
          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
            <h4 className="font-semibold text-cyan-400 text-sm">A. Continuous Density Map Integration</h4>
            <p>
              Unlike discrete bounding box counting which suffers when people overlap, continuous crowd density estimation models represent crowd spatial distribution as a real-valued 2D field:
            </p>
            <div className="p-2.5 bg-black/60 rounded-lg font-mono text-center text-slate-200">
              N_density = ∬ D(x, y) dx dy ≈ ∑_(x,y) D(x, y), where D(x, y) ≥ 0
            </div>
            <p>
              In training, ground-truth point annotations are convolved with normalized 2D Gaussian kernels ensuring exact count preservation.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
            <h4 className="font-semibold text-amber-400 text-sm">B. Scene Occlusion Index (SOI) Proxy</h4>
            <p>
              Physical 3D occlusion is quantified using a multi-factor geometric proxy combining pairwise bounding box overlap, cluster density proximity, and apparent scale factor:
            </p>
            <div className="p-2.5 bg-black/60 rounded-lg font-mono text-center text-slate-200">
              SOI = w₁ · mean(IoMin) + w₂ · Ratio_cluster + w₃ · Penalty_scale
            </div>
            <p>
              Calibrated thresholds categorize difficulty into: <em>Low (&lt; 0.20)</em>, <em>Moderate (0.20 - 0.45)</em>, <em>High (0.45 - 0.70)</em>, and <em>Severe (&ge; 0.70)</em>.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
            <h4 className="font-semibold text-emerald-400 text-sm">C. Adaptive Hybrid Fusion Estimator</h4>
            <p>
              To eliminate detection undercounting in dense crowds while avoiding density-regression overestimation in sparse scenes, an adaptive fusion policy is implemented:
            </p>
            <div className="p-2.5 bg-black/60 rounded-lg font-mono text-center text-slate-200">
              N_hybrid = α · N_track + (1 - α) · N_density
            </div>
            <p>
              Where the blending weight α ∈ [0.1, 0.9] dynamically adjusts based on the active Scene Occlusion Index: α(SOI) = clip(0.85 - 0.65 · SOI, 0.1, 0.9).
            </p>
          </div>
        </div>
      </div>

      {/* 2. System Architecture Workflow */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-700/60 shadow-xl space-y-4">
        <h3 className="text-base font-bold text-white flex items-center space-x-2">
          <GitBranch className="w-5 h-5 text-emerald-400" />
          <span>2. End-to-End System Pipeline</span>
        </h3>

        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 font-mono text-xs text-slate-300 overflow-x-auto">
          <pre>{`
  [ Video / Webcam Stream ]
              │
              ▼
   (Frame Capture Thread) ──► [ Latest Frame Buffer ] (Bounded Queue)
              │
      ┌───────┴──────────────────────────┐
      ▼                                  ▼
[ Person Detector ]            [ Density Map Estimator ]
   YOLOv8 Class 0                    MCNN 3-Column CNN
      │                                  │
      ▼                                  ▼
[ Multi-Object Tracker ]        Continuous Density Surface
   ByteTrack / BoT-SORT                  │
      │                                  │
      ▼                                  │
[ Tripwires & ROI Polygon ]              │
   In/Out & Density                      │
      │                                  │
      └─────────────────┬────────────────┘
                        ▼
            [ Occlusion Proxy Analysis ]
            [ Adaptive Hybrid Fusion ]
                        │
                        ▼
      ┌─────────────────┴─────────────────┐
      ▼                                   ▼
[ Event Manager & Alerts ]      [ Annotated Frame Renderer ]
   SQLite Persistent DB             MJPEG / WebSocket Stream
   Snapshots & Telemetry            React Vite Dashboard
`}</pre>
        </div>
      </div>

      {/* 3. Research Datasets */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-700/60 shadow-xl space-y-4">
        <h3 className="text-base font-bold text-white flex items-center space-x-2">
          <Database className="w-5 h-5 text-amber-400" />
          <span>3. Supported Research Datasets</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-slate-300">
          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
            <h4 className="font-semibold text-cyan-400 text-sm">CrowdHuman Benchmark</h4>
            <p>
              Designed explicitly for human detection in heavily occluded scenarios. Contains ~470,000 instances across 15,000 images with full-body (<code>fbox</code>), visible-body (<code>vbox</code>), and head (<code>hbox</code>) annotations.
            </p>
            <div className="text-[11px] text-slate-400">
              Reference: Shao et al., "CrowdHuman: A Benchmark for Detecting Human in a Crowd", arXiv:1805.00123.
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
            <h4 className="font-semibold text-amber-400 text-sm">ShanghaiTech (Part A & B)</h4>
            <p>
              Standard benchmark for continuous crowd counting. Part A features highly dense crowds from the internet; Part B consists of street surveillance views in metropolitan Shanghai.
            </p>
            <div className="text-[11px] text-slate-400">
              Reference: Zhang et al., "Single-Image Crowd Counting via Multi-Column CNN", CVPR 2016.
            </div>
          </div>
        </div>
      </div>

      {/* 4. Ethics, Privacy & Safety Governance */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-700/60 shadow-xl space-y-3">
        <h3 className="text-base font-bold text-white flex items-center space-x-2">
          <Shield className="w-5 h-5 text-rose-400" />
          <span>4. Ethical Principles & Privacy Safeguards</span>
        </h3>

        <div className="space-y-2 text-xs text-slate-300 leading-relaxed">
          <p>
            This system is strictly engineered for <strong>anonymous spatial crowd density monitoring</strong> and safety occupancy estimation.
          </p>
          <ul className="list-disc pl-5 space-y-1 text-slate-400">
            <li><strong>No Facial Recognition:</strong> Faces are neither identified, extracted, matched, nor stored.</li>
            <li><strong>Session-Scoped Anonymity:</strong> Tracking IDs exist strictly within an ephemeral video processing session and are never mapped to individual identities.</li>
            <li><strong>Configurable Data Retention:</strong> Raw video frames are discarded by default, with only aggregate statistical metrics persisted to local SQLite.</li>
            <li><strong>Safety Threshold Demonstration:</strong> Threshold levels provided are experimental demonstration settings and must be calibrated according to specific facility safety codes before production deployment.</li>
          </ul>
        </div>
      </div>
    </div>
  );
};
