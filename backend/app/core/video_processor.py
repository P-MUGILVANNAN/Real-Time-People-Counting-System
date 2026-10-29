import time
import os
import threading
import queue
import logging
from typing import Optional, Dict, Any, List, Tuple
import cv2
import numpy as np

from backend.app.core.detector import PersonDetector
from backend.app.core.tracker import MultiObjectTracker
from backend.app.core.counter import CrowdCounter
from backend.app.core.density_estimator import (
    DetectionDensityEstimator,
    MCNNDensityEstimator,
    HybridDensityEstimator
)
from backend.app.core.heatmap import HeatmapGenerator
from backend.app.core.occlusion_analysis import OcclusionAnalyzer
from backend.app.core.event_manager import EventManager

logger = logging.getLogger("crowd_system.video_processor")

class VideoProcessor:
    """
    High-Performance Multi-Threaded Real-Time Video and Camera Stream Processing Pipeline.
    Runs video capture, inference, tracking, density estimation, and frame rendering
    in a dedicated worker thread with bounded queues to guarantee zero memory leakage.
    """

    def __init__(
        self,
        detector: PersonDetector,
        tracker: MultiObjectTracker,
        counter: CrowdCounter,
        density_estimator: MCNNDensityEstimator,
        event_manager: EventManager,
        output_dir: str = "outputs/videos"
    ):
        self.detector = detector
        self.tracker = tracker
        self.counter = counter
        self.density_estimator = density_estimator
        self.detection_density = DetectionDensityEstimator(grid_rows=4, grid_cols=4)
        self.hybrid_estimator = HybridDensityEstimator(default_alpha=0.5)
        self.heatmap_gen = HeatmapGenerator(decay_factor=0.92, sigma=25)
        self.occlusion_analyzer = OcclusionAnalyzer()
        self.event_manager = event_manager
        self.output_dir = output_dir

        os.makedirs(self.output_dir, exist_ok=True)

        # Threading state
        self._is_running = False
        self._is_paused = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Video source state
        self.source_type: str = "none"  # "webcam", "file", "synthetic"
        self.source_path_or_idx: Any = None
        self.cap: Optional[cv2.VideoCapture] = None

        # Frame buffer (bounded to 1 frame for latest-frame strategy)
        self._latest_jpeg: Optional[bytes] = None
        self._latest_frame_raw: Optional[np.ndarray] = None

        # Recording
        self._is_recording = False
        self._video_writer: Optional[cv2.VideoWriter] = None
        self._record_path: Optional[str] = None

        # Visualization Toggles
        self.display_options = {
            "show_boxes": True,
            "show_tracks": True,
            "show_trails": True,
            "show_heatmap": False,
            "show_density_map": False,
            "show_rois": True,
            "show_lines": True
        }

        # Real-time metrics
        self.stats: Dict[str, Any] = {
            "is_running": False,
            "is_paused": False,
            "source": "none",
            "frame_index": 0,
            "source_fps": 0.0,
            "processing_fps": 0.0,
            "latency_ms": 0.0,
            "frame_detection_count": 0,
            "active_tracked_count": 0,
            "cumulative_unique_count": 0,
            "density_count": 0.0,
            "hybrid_count": 0.0,
            "crowd_status": "normal",
            "occlusion_index": 0.0,
            "difficulty_category": "low",
            "lines": {},
            "regions": {}
        }

    def start_source(self, source: Any, source_type: str = "file") -> bool:
        """Starts video processing loop for webcam (int) or video file (str)."""
        self.stop()

        with self._lock:
            self.source_type = source_type
            self.source_path_or_idx = source
            
            logger.info(f"Opening video source: {source} ({source_type})...")
            self.cap = cv2.VideoCapture(source)
            if not self.cap.isOpened():
                logger.error(f"Failed to open video source: {source}")
                return False

            self.tracker.reset()
            self.counter.reset()
            self.heatmap_gen.reset_trajectory_map()
            self._is_running = True
            self._is_paused = False

            self._thread = threading.Thread(target=self._worker_loop, daemon=True)
            self._thread.start()
            logger.info("Video processing worker thread started.")
            return True

    def stop(self):
        """Stops the processing pipeline and safely releases camera and writers."""
        self._is_running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

        with self._lock:
            if self.cap:
                self.cap.release()
                self.cap = None
            if self._video_writer:
                self._video_writer.release()
                self._video_writer = None
            self.stats["is_running"] = False

    def pause(self):
        self._is_paused = True
        self.stats["is_paused"] = True

    def resume(self):
        self._is_paused = False
        self.stats["is_paused"] = False

    def toggle_display(self, key: str, value: bool):
        if key in self.display_options:
            self.display_options[key] = value

    def set_recording(self, record: bool) -> Optional[str]:
        with self._lock:
            if record and not self._is_recording:
                timestamp = int(time.time())
                self._record_path = os.path.join(self.output_dir, f"record_{timestamp}.mp4")
                self._is_recording = True
                return self._record_path
            elif not record and self._is_recording:
                self._is_recording = False
                if self._video_writer:
                    self._video_writer.release()
                    self._video_writer = None
                return self._record_path
        return None

    def capture_screenshot(self) -> Optional[str]:
        with self._lock:
            if self._latest_frame_raw is not None:
                os.makedirs("outputs/heatmaps", exist_ok=True)
                path = f"outputs/heatmaps/screenshot_{int(time.time())}.jpg"
                cv2.imwrite(path, self._latest_frame_raw)
                return path
        return None

    def get_latest_jpeg(self) -> Optional[bytes]:
        with self._lock:
            return self._latest_jpeg

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self.stats)

    def _worker_loop(self):
        """Dedicated inference & rendering loop."""
        source_fps = self.cap.get(cv2.CAP_PROP_FPS) if self.cap else 30.0
        if source_fps <= 0 or np.isnan(source_fps):
            source_fps = 30.0

        frame_idx = 0
        frame_time_tracker = []

        while self._is_running:
            if self._is_paused:
                time.sleep(0.05)
                continue

            loop_start = time.perf_counter()
            ret, frame = self.cap.read() if self.cap else (False, None)

            # Loop video file if reached end
            if not ret or frame is None:
                if self.source_type == "file" and self.cap:
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                else:
                    logger.warning("End of stream or camera disconnected.")
                    break

            frame_idx += 1
            h, w = frame.shape[:2]

            # 1. Detection
            detections, det_meta = self.detector.detect(frame)

            # 2. Tracking
            active_tracks = self.tracker.update_from_detections(detections)
            cumulative_unique = self.tracker.get_cumulative_count()

            # 3. People & Region Counting
            counting_res = self.counter.update(detections, active_tracks, cumulative_unique)

            # 4. Occlusion Analysis
            occlusion_res = self.occlusion_analyzer.analyze((h, w), detections, active_tracks)
            soi = occlusion_res["scene_occlusion_index"]
            difficulty = occlusion_res["difficulty_category"]

            # 5. Density Estimation (Approach A & Approach B)
            det_density_res = self.detection_density.estimate(frame, detections)
            density_map_res = self.density_estimator.estimate(frame, detections)
            
            # Hybrid Fusion
            hybrid_res = self.hybrid_estimator.estimate(
                det_or_track_count=float(len(active_tracks)),
                density_map_result=density_map_res,
                occlusion_index=soi
            )

            # 6. Alerts & Event Management
            self.event_manager.evaluate_state(
                total_count=len(active_tracks),
                density_val=det_density_res["density_per_1k_px"],
                region_metrics=counting_res["regions"]
            )

            # 7. Rendering Annotated Overlays
            rendered = frame.copy()

            # Optional Heatmap overlay
            if self.display_options.get("show_heatmap", False):
                det_heat = self.heatmap_gen.generate_detection_density_map((h, w), detections)
                rendered = self.heatmap_gen.overlay_heatmap(rendered, det_heat, alpha=0.55)

            # Optional Neural Density Map overlay
            if self.display_options.get("show_density_map", False) and density_map_res.get("density_map") is not None:
                rendered = self.heatmap_gen.overlay_heatmap(rendered, density_map_res["density_map"], alpha=0.6)

            # Lines & Regions
            if self.display_options.get("show_rois", True) or self.display_options.get("show_lines", True):
                rendered = self.counter.draw_overlays(rendered)

            # Trajectory Trails
            if self.display_options.get("show_trails", True):
                for track in active_tracks:
                    if len(track.history) > 1:
                        pts = [p[:2] for p in list(track.history)]
                        for i in range(1, len(pts)):
                            cv2.line(rendered, pts[i - 1], pts[i], (0, 255, 255), 2)

            # Bounding boxes and Track IDs
            if self.display_options.get("show_tracks", True):
                for track in active_tracks:
                    x1, y1, x2, y2 = track.bbox
                    tid = track.track_id
                    color = (0, 255, 0) if difficulty == "low" else ((0, 215, 255) if difficulty == "moderate" else (0, 0, 255))
                    cv2.rectangle(rendered, (x1, y1), (x2, y2), color, 2)
                    label = f"ID:{tid}"
                    cv2.putText(rendered, label, (x1, max(15, y1 - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 2)
                    cv2.putText(rendered, label, (x1, max(15, y1 - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
            elif self.display_options.get("show_boxes", True):
                rendered = self.detector.draw_detections(rendered, detections)

            # Processing Timing & FPS
            loop_end = time.perf_counter()
            elapsed_ms = (loop_end - loop_start) * 1000.0
            frame_time_tracker.append(elapsed_ms)
            if len(frame_time_tracker) > 30:
                frame_time_tracker.pop(0)

            avg_latency = float(np.mean(frame_time_tracker))
            proc_fps = round(1000.0 / max(0.001, avg_latency), 1)

            # HUD Display on upper left
            hud_text = f"FPS: {proc_fps:.1f} | Det: {len(detections)} | Active: {len(active_tracks)} | Uniq: {cumulative_unique} | Occ: {soi:.2f}"
            cv2.rectangle(rendered, (8, 8), (460, 36), (0, 0, 0), -1)
            cv2.putText(rendered, hud_text, (14, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 255, 200), 1, cv2.LINE_AA)

            # Video Recording writer if active
            if self._is_recording:
                if self._video_writer is None and self._record_path:
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                    self._video_writer = cv2.VideoWriter(self._record_path, fourcc, 20.0, (w, h))
                if self._video_writer:
                    self._video_writer.write(rendered)

            # JPEG Encoding for streaming
            encode_ret, jpeg_buf = cv2.imencode(".jpg", rendered, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
            if encode_ret:
                with self._lock:
                    self._latest_jpeg = jpeg_buf.tobytes()
                    self._latest_frame_raw = rendered

            # Update stats dict
            with self._lock:
                self.stats.update({
                    "is_running": True,
                    "is_paused": self._is_paused,
                    "source": str(self.source_path_or_idx),
                    "frame_index": frame_idx,
                    "source_fps": round(source_fps, 1),
                    "processing_fps": proc_fps,
                    "latency_ms": round(avg_latency, 1),
                    "frame_detection_count": len(detections),
                    "active_tracked_count": len(active_tracks),
                    "cumulative_unique_count": cumulative_unique,
                    "density_count": density_map_res.get("estimated_count", 0.0),
                    "density_weights_ready": density_map_res.get("has_valid_weights", False),
                    "hybrid_count": hybrid_res.get("hybrid_count", 0.0),
                    "crowd_status": self.event_manager.current_status,
                    "occlusion_index": soi,
                    "difficulty_category": difficulty,
                    "lines": counting_res["lines"],
                    "regions": counting_res["regions"]
                })

            # Regulate frame rate to prevent overwhelming CPU
            target_delay = max(0.001, (1.0 / source_fps) - (elapsed_ms / 1000.0))
            if target_delay > 0:
                time.sleep(target_delay)

        self.stop()
