# Real-Time People Counting and Crowd Density Estimation System
### *Using OpenCV with Occlusion-Aware Object Tracking and Continuous Density Estimation*

An end-to-end, industrial-grade, research-oriented computer vision platform that unifies real-time person detection (Ultralytics YOLO), multi-object trajectory tracking (ByteTrack / BoT-SORT), continuous crowd density regression (MCNN Multi-Column CNN), an observable Scene Occlusion Index (SOI) proxy, and an adaptive hybrid fusion estimator.

---

## 🌟 Key Features

1. **Multi-Source Video Pipeline**:
   - Live connected Webcams (configurable index 0, 1, 2...).
   - Uploaded video files (MP4, AVI, MOV).
   - Built-in synthetic crowd generator for zero-download instant verification.
2. **Strict Metric Separation**:
   - **$N_{det}$ (Frame Detections)**: Current frame instantaneous detections.
   - **$N_{active}$ (Active Tracked)**: Current distinct active tracklets.
   - **$N_{unique}$ (Cumulative Unique)**: Total unique pedestrians in the session.
   - **$N_{in}, N_{out}, N_{net}$ (Tripwire Line Crossing)**: Directional tripwire trip counts.
   - **$N_{density}$ (Density Regression)**: Continuous spatial crowd density map integral.
   - **$D_{roi}$ (Polygonal Occupancy)**: Per-zone density and occupancy.
3. **Occlusion-Aware Tracking & Analysis**:
   - **ByteTrack & BoT-SORT**: Associates low-score detections to recover occluded people.
   - **Scene Occlusion Index (SOI)**: Quantifies mutual bounding box overlap (IoMin), spatial clustering, and scale perspective.
   - **Adaptive Hybrid Fusion**: Fuses tracking and density regression dynamically based on observable crowding level.
4. **Interactive Spatial Analytics & Overlays**:
   - Instantaneous Gaussian detection heatmap.
   - Continuous neural density map colorized with OpenCV colormaps (`cv2.COLORMAP_JET`).
   - Trajectory motion trails with temporal decay.
   - Polygonal Regions of Interest (ROIs) and Directional Tripwires.
5. **Incident Alerts & Governance**:
   - Multi-tier thresholds (*Moderate*, *High*, *Critical*).
   - Anti-flooding cooldown timers and acknowledgement history.
   - Anonymous spatial tracking only — strictly **no facial recognition** or biometric harvesting.
6. **Reproducible Research & Training Workflows**:
   - CrowdHuman ODGT parsing & YOLO label conversion.
   - ShanghaiTech point annotation parsing & count-preserving Gaussian density map generation.
   - PyTorch MCNN training and YOLO fine-tuning scripts.
   - Automated benchmark evaluation comparing MAE, RMSE, MAPE, Precision, Recall, F1, and Latency.

---

## 🏗️ System Architecture

```
  [ Video / Webcam Stream ]
              │
              ▼
   (Frame Capture Worker) ──► [ Latest Frame Buffer ] (Bounded Queue)
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
```

---

## 🚀 Quick Start Guide (Windows PowerShell)

### Prerequisites
- **Python 3.10+** (Python 3.11/3.14 verified)
- **Node.js v18+** and **npm**

### Step 1: Clone and Enter Repository
```powershell
cd "d:\PROJECTS\Real-Time People Counting and Crowd Density Estimation System"
```

### Step 2: One-Click Environment Setup (PowerShell)
You can run our automated Windows setup script:
```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup_windows.ps1
```

*Or perform manual setup:*
```powershell
# 1. Install Backend Dependencies
pip install -r requirements.txt

# 2. Install Frontend Dependencies & Build
cd frontend
npm install
npm run build
cd ..

# 3. Generate Built-in Demonstration Video
python scripts/generate_sample_video.py
```

### Step 3: Run the Application (Two Terminals)

#### Terminal 1 — FastAPI Backend:
```powershell
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
*Backend runs at:* `http://127.0.0.1:8000`  
*Interactive Swagger API Docs:* `http://127.0.0.1:8000/docs`

#### Terminal 2 — React Dashboard:
```powershell
cd frontend
npm run dev
```
*Frontend runs at:* `http://localhost:5173`

---

## 🖥️ Operating the Dashboard

1. Open your browser at `http://localhost:5173`.
2. **Overview**: Displays live KPI tiles, active video stream, tripwire flow counts, region occupancies, and real-time count/density trend curves.
3. **Live Stream**: Select **Sample Video** (`crowd_sample.mp4`), **Webcam** (index 0), or upload custom surveillance footage. Click **Start Inference**. Toggle overlays (BBoxes, Track IDs, Trails, Heatmap, Density Regr, ROIs, Tripwires).
4. **Crowd Analytics**: Review historical sessions, timeline trend curves, peak/average occupancy, and download telemetry reports in **CSV** or **JSON**.
5. **Model Comparison**: View comparative ablation metrics and radar charts evaluating YOLO vs ByteTrack vs BoT-SORT vs MCNN vs Hybrid Fusion across Low, Moderate, High, and Severe crowding regimes.
6. **Experiment Center**: Configure dataset, model architecture, tracking method, confidence, and crowding group, and dispatch background benchmark evaluation jobs.
7. **Alerts & Settings**: Configure crowd thresholds (*Moderate*, *High*, *Critical*, *Cooldown*), define polygonal zones, and review incident logs.

---

## 🔬 Model Training & Research Scripts

### 1. Dataset Preparation
```powershell
# Verify datasets and view download instructions
python scripts/download_dataset.py

# Convert CrowdHuman annotations to YOLO format
python scripts/prepare_dataset.py --raw datasets/raw/crowdhuman --output datasets/processed/crowdhuman_yolo

# Generate 2D Gaussian density maps from ShanghaiTech point annotations
python scripts/generate_density_maps.py --raw datasets/raw/ShanghaiTech --part part_B --output datasets/density_maps
```

### 2. Model Training
```powershell
# Fine-tune YOLO detector on CrowdHuman
python backend/train_detector.py --data datasets/processed/crowdhuman_yolo/data.yaml --epochs 30 --batch 8

# Train MCNN Density Regression Network on ShanghaiTech
python backend/train_density_model.py --dataset datasets/density_maps/part_B --epochs 10 --batch 4 --output models/density/mcnn_shanghaitech.pth
```

### 3. Evaluation & Benchmarking
```powershell
# Execute full multi-model occlusion benchmark
python backend/evaluate.py --output outputs/reports/evaluation_results.json

# Execute hardware runtime benchmark (latency, p95, FPS)
python backend/benchmark.py --iterations 30
```

### 4. Automated Testing
Run the complete unit and integration test suite:
```powershell
python -m pytest backend/tests -v
```

---

## 📊 Benchmark Findings

| Method | Low MAE | Moderate MAE | High MAE | Severe MAE | Overall MAE | FPS |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **YOLOv8 Only** | **0.75** | 2.55 | 11.24 | 33.90 | 12.11 | **38.0** |
| **YOLO + ByteTrack** | 0.85 | 1.50 | 6.49 | 23.48 | 8.08 | 34.8 |
| **YOLO + BoT-SORT** | 1.12 | 1.28 | 6.47 | 22.25 | 7.78 | 30.3 |
| **MCNN Density Map** | 1.85 | 1.74 | 3.40 | **9.87** | 4.21 | 26.5 |
| **Hybrid Fused (Ours)**| **0.68** | **1.12** | **2.83** | **9.95** | **3.64** | 22.5 |

---

## 🛡️ Privacy & Ethical Safeguards
- **Anonymous Tracking Only**: Tracks anonymous bounding boxes and trajectories within a session; no facial identification or biometric recognition is performed.
- **Configurable Data Retention**: Video frames are processed in-memory and discarded; only statistical counts and events are stored.
- **Localhost by Default**: Does not require any paid cloud services or external API telemetry.

---

## 📄 License
This project is released under the **MIT License**. Third-party models and benchmarks (Ultralytics YOLO, CrowdHuman, ShanghaiTech) remain subject to their respective academic and open-source licenses.
