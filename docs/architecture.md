# System Architecture

## 1. High-Level Architectural Overview
The **Real-Time People Counting and Crowd Density Estimation System** is engineered using a decoupled, asynchronous, modular architecture separating real-time computer vision inference, RESTful backend APIs, state persistence, and a reactive TypeScript/Tailwind dashboard.

```
       +--------------------------------------------------------------+
       |                        Input Sources                         |
       |  - Webcam Device Index (0, 1)   - MP4 / AVI Video Files      |
       |  - Network IP Stream / RTSP     - Synthetic Crowd Generator  |
       +------------------------------+-------------------------------+
                                      |
                                      v
       +--------------------------------------------------------------+
       |                  FastAPI Backend Processing                  |
       |                                                              |
       |  [ VideoProcessor Worker Thread ] (Bounded Queue)            |
       |    │                                                         |
       |    ├──► [ PersonDetector ] ──► YOLOv8 (Class 0 Strict)       |
       |    ├──► [ MultiObjectTracker ] ──► ByteTrack / BoT-SORT      |
       |    ├──► [ CrowdCounter ] ──► Tripwires & Polygonal ROIs      |
       |    ├──► [ DensityEstimator ] ──► MCNN 3-Column CNN           |
       |    ├──► [ OcclusionAnalyzer ] ──► Geometric Proxy (SOI)      |
       |    ├──► [ HybridEstimator ] ──► Dynamic Blended Fusion       |
       |    └──► [ EventManager ] ──► Multi-tier Cooldown Alerts      |
       |                                                              |
       |  [ SQLite Database ] (SQLAlchemy ORM)                        |
       |    - Sessions, Snapshots, Alerts, Experiments                |
       +------------------------------+-------------------------------+
                                      |
                                      v
       +--------------------------------------------------------------+
       |                  Delivery & Presentation                     |
       |                                                              |
       |  - WebSocket (/ws/analytics) ──► 2Hz Real-Time Telemetry     |
       |  - MJPEG Stream (/api/video/stream) ──► Low-Latency Visuals  |
       |  - REST Endpoints (/api/*) ──► Controls, Exports & Reports   |
       |  - React + Vite Dashboard ──► Responsive UI & Charts         |
       +--------------------------------------------------------------+
```

## 2. Core Subsystems

### 2.1 Video Worker & Threading Model
- Video frame capture and deep learning inferences run in an independent background worker thread (`VideoProcessor`).
- Uses a **latest-frame strategy** with bounded queues, ensuring FastAPI request handling is never blocked by compute-heavy neural network operations.
- Frame rates are dynamically regulated to prevent memory leaks and excessive CPU saturation.

### 2.2 Computer Vision Engine
1. **PersonDetector (`backend/app/core/detector.py`)**:
   - Integrates Ultralytics YOLOv8.
   - Enforces strict single-class filtering for class 0 (`person`).
   - Supports CPU and CUDA inference with automatic device fallback.
2. **MultiObjectTracker (`backend/app/core/tracker.py`)**:
   - Implements ByteTrack association principles matching high-confidence boxes first, then matching low-confidence boxes with remaining active tracklets to recover occluded targets.
3. **CrowdCounter (`backend/app/core/counter.py`)**:
   - Distinctly tracks Frame Detections ($N_{det}$), Active Tracked ($N_{active}$), Cumulative Unique ($N_{unique}$), Directional Line Crossings ($N_{in}, N_{out}$), and Polygonal Region Occupancies ($N_{roi}$).
4. **MCNN Density Estimator (`backend/app/core/density_estimator.py`)**:
   - Multi-Column Convolutional Neural Network with 3 receptive field branches (Large: 9x9, Medium: 7x7, Small: 5x5) outputting continuous crowd density maps where $\iint D(x, y) dx dy = N_{people}$.
5. **OcclusionAnalyzer (`backend/app/core/occlusion_analysis.py`)**:
   - Calculates Scene Occlusion Index (SOI) from pairwise IoU, cluster proximity, and box scale ratios.
6. **Hybrid Density Estimator**:
   - Evaluates dynamic fusion: $N_{hybrid} = \alpha N_{track} + (1 - \alpha) N_{density}$.

### 2.3 Data Storage
- Local SQLite database managed via SQLAlchemy.
- Automatically initializes on startup.
- Stores sessions, interval snapshots (default every 2 seconds), crowd alert logs, and benchmark experiment configurations.
