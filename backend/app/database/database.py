import os
import time
import json
from typing import Generator, List, Dict, Any, Optional
from sqlalchemy import create_engine, desc, func
from sqlalchemy.orm import sessionmaker, Session

from backend.app.config import settings
from backend.app.database.models import Base, SessionRecord, AnalyticsSnapshot, AlertLog, ExperimentRecord

# Ensure output directory exists for database file
db_path = settings.DATABASE_URL.replace("sqlite:///", "")
if db_path.startswith("./"):
    db_path = db_path[2:]
os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initializes database tables."""
    Base.metadata.create_all(bind=engine)

def get_db() -> Generator[Session, None, None]:
    """FastAPI database dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Database Service Operations

class DBService:

    @staticmethod
    def create_session(
        db: Session,
        session_id: str,
        source_type: str,
        source_path: str,
        model_name: str,
        tracker_type: str
    ) -> SessionRecord:
        record = SessionRecord(
            session_id=session_id,
            source_type=source_type,
            source_path=source_path,
            model_name=model_name,
            tracker_type=tracker_type,
            start_time=time.time(),
            status="active"
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def end_session(db: Session, session_id: str):
        record = db.query(SessionRecord).filter(SessionRecord.session_id == session_id).first()
        if record:
            record.end_time = time.time()
            record.status = "completed"
            
            # Compute session aggregations
            snaps = db.query(AnalyticsSnapshot).filter(AnalyticsSnapshot.session_id == session_id).all()
            if snaps:
                record.total_frames = len(snaps)
                record.peak_count = max(s.active_tracked_count for s in snaps)
                record.avg_count = round(float(sum(s.active_tracked_count for s in snaps) / len(snaps)), 2)
            db.commit()

    @staticmethod
    def add_snapshot(db: Session, data: Dict[str, Any]) -> AnalyticsSnapshot:
        snap = AnalyticsSnapshot(
            session_id=data.get("session_id", "default"),
            timestamp=data.get("timestamp", time.time()),
            frame_index=data.get("frame_index", 0),
            detection_count=data.get("frame_detection_count", 0),
            active_tracked_count=data.get("active_tracked_count", 0),
            cumulative_unique_count=data.get("cumulative_unique_count", 0),
            density_estimate=data.get("density_count", 0.0),
            hybrid_estimate=data.get("hybrid_count", 0.0),
            processing_fps=data.get("processing_fps", 0.0),
            latency_ms=data.get("latency_ms", 0.0),
            occlusion_index=data.get("occlusion_index", 0.0),
            difficulty_category=data.get("difficulty_category", "low")
        )
        db.add(snap)
        db.commit()
        return snap

    @staticmethod
    def log_alert(db: Session, alert_data: Dict[str, Any]) -> AlertLog:
        alert = AlertLog(
            alert_id=alert_data["alert_id"],
            session_id=alert_data.get("session_id"),
            severity=alert_data.get("severity", "moderate"),
            message=alert_data.get("message", ""),
            source=alert_data.get("source", "global"),
            metric_value=alert_data.get("metric_value", 0.0),
            threshold_value=alert_data.get("threshold_value", 0.0),
            timestamp=alert_data.get("timestamp", time.time())
        )
        db.add(alert)
        db.commit()
        return alert

    @staticmethod
    def acknowledge_alert(db: Session, alert_id: str) -> bool:
        alert = db.query(AlertLog).filter(AlertLog.alert_id == alert_id).first()
        if alert:
            alert.acknowledged = True
            alert.acknowledged_at = time.time()
            db.commit()
            return True
        return False

    @staticmethod
    def get_sessions(db: Session, limit: int = 20) -> List[Dict[str, Any]]:
        sessions = db.query(SessionRecord).order_by(desc(SessionRecord.start_time)).limit(limit).all()
        return [
            {
                "session_id": s.session_id,
                "source_type": s.source_type,
                "source_path": s.source_path,
                "model_name": s.model_name,
                "tracker_type": s.tracker_type,
                "start_time": s.start_time,
                "end_time": s.end_time,
                "total_frames": s.total_frames,
                "peak_count": s.peak_count,
                "avg_count": s.avg_count,
                "status": s.status
            }
            for s in sessions
        ]

    @staticmethod
    def get_snapshots(db: Session, session_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        q = db.query(AnalyticsSnapshot)
        if session_id:
            q = q.filter(AnalyticsSnapshot.session_id == session_id)
        snaps = q.order_by(AnalyticsSnapshot.timestamp.asc()).limit(limit).all()
        return [
            {
                "timestamp": s.timestamp,
                "frame_index": s.frame_index,
                "detection_count": s.detection_count,
                "active_tracked_count": s.active_tracked_count,
                "cumulative_unique_count": s.cumulative_unique_count,
                "density_estimate": s.density_estimate,
                "hybrid_estimate": s.hybrid_estimate,
                "processing_fps": s.processing_fps,
                "latency_ms": s.latency_ms,
                "occlusion_index": s.occlusion_index,
                "difficulty_category": s.difficulty_category
            }
            for s in snaps
        ]

    @staticmethod
    def get_alerts(db: Session, limit: int = 50) -> List[Dict[str, Any]]:
        alerts = db.query(AlertLog).order_by(desc(AlertLog.timestamp)).limit(limit).all()
        return [
            {
                "alert_id": a.alert_id,
                "session_id": a.session_id,
                "severity": a.severity,
                "message": a.message,
                "source": a.source,
                "metric_value": a.metric_value,
                "threshold_value": a.threshold_value,
                "timestamp": a.timestamp,
                "acknowledged": a.acknowledged,
                "acknowledged_at": a.acknowledged_at
            }
            for a in alerts
        ]

    @staticmethod
    def save_experiment(db: Session, exp: Dict[str, Any]) -> ExperimentRecord:
        rec = ExperimentRecord(
            experiment_id=exp["experiment_id"],
            name=exp["name"],
            dataset_name=exp.get("dataset_name", "crowdhuman"),
            model_type=exp.get("model_type", "yolo"),
            tracker_type=exp.get("tracker_type", "bytetrack"),
            confidence_thresh=exp.get("confidence_thresh", 0.35),
            iou_thresh=exp.get("iou_thresh", 0.45),
            crowding_group=exp.get("crowding_group", "all"),
            sample_count=exp.get("sample_count", 0),
            mae=exp.get("mae", 0.0),
            rmse=exp.get("rmse", 0.0),
            mape=exp.get("mape", 0.0),
            precision=exp.get("precision", 0.0),
            recall=exp.get("recall", 0.0),
            f1=exp.get("f1", 0.0),
            ap50=exp.get("ap50", 0.0),
            mean_latency_ms=exp.get("mean_latency_ms", 0.0),
            fps=exp.get("fps", 0.0),
            created_at=time.time(),
            status=exp.get("status", "completed"),
            results_json=json.dumps(exp.get("results_json", {}))
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)
        return rec

    @staticmethod
    def get_experiments(db: Session) -> List[Dict[str, Any]]:
        exps = db.query(ExperimentRecord).order_by(desc(ExperimentRecord.created_at)).all()
        res = []
        for e in exps:
            try:
                res_dict = json.loads(e.results_json) if e.results_json else {}
            except Exception:
                res_dict = {}
            res.append({
                "experiment_id": e.experiment_id,
                "name": e.name,
                "dataset_name": e.dataset_name,
                "model_type": e.model_type,
                "tracker_type": e.tracker_type,
                "confidence_thresh": e.confidence_thresh,
                "iou_thresh": e.iou_thresh,
                "crowding_group": e.crowding_group,
                "sample_count": e.sample_count,
                "mae": e.mae,
                "rmse": e.rmse,
                "mape": e.mape,
                "precision": e.precision,
                "recall": e.recall,
                "f1": e.f1,
                "ap50": e.ap50,
                "mean_latency_ms": e.mean_latency_ms,
                "fps": e.fps,
                "created_at": e.created_at,
                "status": e.status,
                "results": res_dict
            })
        return res
