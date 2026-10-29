# REST & WebSocket API Reference

The backend exposes an OpenAPI 3.0 specification accessible at `http://127.0.0.1:8000/docs`.

## 1. System & Health
- `GET /api/health`: Returns service operational status and model readiness.
- `GET /api/models`: Returns weights path, device, confidence, and tracker configuration.
- `GET /api/system/status`: Returns CPU/GPU utilization, RAM, and platform metrics.

## 2. Camera Controls
- `POST /api/camera/start`: Starts video capture on a connected webcam.
  - Body: `{"camera_index": 0, "tracker_type": "bytetrack", "confidence_thresh": 0.35}`
- `POST /api/camera/stop`: Stops camera capture and releases hardware.
- `POST /api/camera/toggle`: Toggles overlay rendering flags (`show_boxes`, `show_tracks`, `show_trails`, `show_heatmap`, `show_density_map`, `show_rois`, `show_lines`).
- `POST /api/camera/screenshot`: Captures and saves annotated frame to `outputs/heatmaps/`.
- `POST /api/camera/record?enable=true`: Toggles video recording.

## 3. Video Processing & Streaming
- `POST /api/video/upload`: Accepts `multipart/form-data` video files (MP4, AVI, MOV).
- `GET /api/video/files`: Lists sample demonstration and uploaded video files.
- `POST /api/video/start`: Starts processing an uploaded or sample video file.
- `POST /api/video/stop`: Halts video playback.
- `POST /api/video/pause` / `POST /api/video/resume`: Pauses or resumes stream.
- `GET /api/video/stream`: Real-time multipart MJPEG video stream for HTML `<img>` rendering.

## 4. Analytics & Spatial Management
- `GET /api/analytics/current`: Latest real-time telemetry snapshot and alerts.
- `GET /api/analytics/history`: Chronological snapshot records for trend charts.
- `GET /api/analytics/sessions`: Historical processing sessions list.
- `GET /api/analytics/alerts`: Crowd incident log.
- `POST /api/analytics/alerts/ack`: Acknowledges an active incident.
- `POST /api/analytics/regions`: Configures a polygonal region of interest.
- `POST /api/analytics/lines`: Configures a virtual directional tripwire.
- `POST /api/analytics/thresholds`: Updates crowd alert thresholds and cooldowns.

## 5. Exports & Reports
- `GET /api/reports/summary`: Aggregated metrics across sessions.
- `GET /api/reports/export/csv`: Downloads snapshot telemetry as CSV.
- `GET /api/reports/export/json`: Downloads snapshot telemetry as JSON.

## 6. Research Experiments
- `GET /api/experiments`: Returns completed benchmark experiments.
- `POST /api/experiments/run`: Launches background benchmark evaluation task.
- `GET /api/experiments/{id}`: Returns experiment metrics and per-sample error details.

## 7. WebSockets
- `WS /ws/analytics`: Emits real-time telemetry packets every 500ms.
- `WS /ws/stream`: Emits binary compressed JPEG frames.
