import os
import time
import logging
from typing import Optional

from backend.app.config import settings
from backend.app.core.detector import PersonDetector
from backend.app.core.tracker import MultiObjectTracker
from backend.app.core.counter import CrowdCounter
from backend.app.core.density_estimator import MCNNDensityEstimator
from backend.app.core.event_manager import EventManager
from backend.app.core.video_processor import VideoProcessor
from backend.app.database.database import SessionLocal, DBService

logger = logging.getLogger("crowd_system.cv_service")

class CVServiceContainer:
    """
    Central Singleton Container holding instantiated CV engines,
    video processor pipeline, event manager, and database snapshot ticker.
    """

    def __init__(self):
        logger.info("Initializing CV Service Container...")

        # 1. Detector
        self.detector = PersonDetector(
            model_path=settings.DETECTION_MODEL_PATH,
            confidence_threshold=settings.CONFIDENCE_THRESHOLD,
            iou_threshold=settings.IOU_THRESHOLD,
            input_size=settings.INPUT_IMAGE_SIZE,
            device=settings.DEVICE,
            max_detections=settings.MAX_DETECTIONS
        )

        # 2. Tracker
        self.tracker = MultiObjectTracker(
            tracker_type=settings.TRACKER_TYPE,
            track_buffer=settings.TRACK_BUFFER_FRAMES
        )

        # 3. Counter & Spatial Regions
        self.counter = CrowdCounter()
        # Default regions for immediate demo
        self.counter.add_region(
            region_id="zone_a",
            name="Platform / Main Area",
            polygon=[[40, 60], [600, 60], [600, 420], [40, 420]],
            moderate=settings.MODERATE_CROWD_THRESHOLD,
            high=settings.HIGH_CROWD_THRESHOLD,
            critical=settings.CRITICAL_CROWD_THRESHOLD
        )
        # Default line crossing
        self.counter.add_line(
            line_id="line_gate",
            start_pt=(50, 240),
            end_pt=(590, 240),
            name="Main Access Tripwire"
        )

        # 4. Density Estimator (MCNN)
        self.density_estimator = MCNNDensityEstimator(
            weights_path=settings.DENSITY_MODEL_PATH,
            device=settings.DEVICE
        )

        # 5. Event Manager
        self.event_manager = EventManager(
            moderate_thresh=settings.MODERATE_CROWD_THRESHOLD,
            high_thresh=settings.HIGH_CROWD_THRESHOLD,
            critical_thresh=settings.CRITICAL_CROWD_THRESHOLD,
            cooldown_seconds=settings.ALERT_COOLDOWN_SECONDS
        )

        # 6. Video Processor
        self.video_processor = VideoProcessor(
            detector=self.detector,
            tracker=self.tracker,
            counter=self.counter,
            density_estimator=self.density_estimator,
            event_manager=self.event_manager,
            output_dir=str(settings.OUTPUTS_DIR / "videos")
        )

        self.current_session_id = f"sess_{int(time.time())}"
        self.last_snapshot_time = 0.0

    def start_session(self, source_type: str, source_path: str):
        self.current_session_id = f"sess_{int(time.time())}"
        db = SessionLocal()
        try:
            DBService.create_session(
                db=db,
                session_id=self.current_session_id,
                source_type=source_type,
                source_path=str(source_path),
                model_name=self.detector.model_name,
                tracker_type=self.tracker.tracker_type
            )
        finally:
            db.close()

    def end_current_session(self):
        db = SessionLocal()
        try:
            DBService.end_session(db, self.current_session_id)
        finally:
            db.close()

    def tick_db_snapshot(self):
        """Called periodically to persist metrics into SQLite."""
        now = time.time()
        if (now - self.last_snapshot_time) >= settings.ANALYTICS_SNAPSHOT_INTERVAL_SEC:
            self.last_snapshot_time = now
            stats = self.video_processor.get_stats()
            if stats.get("is_running", False):
                db = SessionLocal()
                try:
                    stats["session_id"] = self.current_session_id
                    DBService.add_snapshot(db, stats)

                    # Also log any new alerts
                    alerts = self.event_manager.get_recent_alerts(limit=5)
                    for a in alerts:
                        if not a.get("logged_to_db"):
                            a["session_id"] = self.current_session_id
                            try:
                                DBService.log_alert(db, a)
                                a["logged_to_db"] = True
                            except Exception:
                                pass
                except Exception as e:
                    logger.error(f"Error persisting snapshot: {e}")
                finally:
                    db.close()

# Global Singleton
cv_service = CVServiceContainer()
