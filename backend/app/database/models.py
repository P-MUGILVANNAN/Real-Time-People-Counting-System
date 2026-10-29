import time
from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class SessionRecord(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), unique=True, index=True, nullable=False)
    source_type = Column(String(32), default="webcam")  # webcam, video, stream
    source_path = Column(String(255), default="")
    model_name = Column(String(64), default="yolov8n.pt")
    tracker_type = Column(String(32), default="bytetrack")
    start_time = Column(Float, default=time.time)
    end_time = Column(Float, nullable=True)
    total_frames = Column(Integer, default=0)
    peak_count = Column(Integer, default=0)
    avg_count = Column(Float, default=0.0)
    status = Column(String(32), default="active")  # active, completed, stopped

    snapshots = relationship("AnalyticsSnapshot", back_populates="session", cascade="all, delete-orphan")
    alerts = relationship("AlertLog", back_populates="session", cascade="all, delete-orphan")


class AnalyticsSnapshot(Base):
    __tablename__ = "analytics_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), ForeignKey("sessions.session_id"), nullable=False, index=True)
    timestamp = Column(Float, default=time.time, index=True)
    frame_index = Column(Integer, default=0)
    detection_count = Column(Integer, default=0)
    active_tracked_count = Column(Integer, default=0)
    cumulative_unique_count = Column(Integer, default=0)
    density_estimate = Column(Float, default=0.0)
    hybrid_estimate = Column(Float, default=0.0)
    processing_fps = Column(Float, default=0.0)
    latency_ms = Column(Float, default=0.0)
    occlusion_index = Column(Float, default=0.0)
    difficulty_category = Column(String(32), default="low")

    session = relationship("SessionRecord", back_populates="snapshots")


class AlertLog(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String(64), unique=True, nullable=False, index=True)
    session_id = Column(String(64), ForeignKey("sessions.session_id"), nullable=True)
    severity = Column(String(32), default="moderate")  # moderate, high, critical
    message = Column(String(255), nullable=False)
    source = Column(String(64), default="global")
    metric_value = Column(Float, default=0.0)
    threshold_value = Column(Float, default=0.0)
    timestamp = Column(Float, default=time.time, index=True)
    acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(Float, nullable=True)

    session = relationship("SessionRecord", back_populates="alerts")


class ExperimentRecord(Base):
    __tablename__ = "experiments"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(128), nullable=False)
    dataset_name = Column(String(64), default="crowdhuman")
    model_type = Column(String(64), default="yolo")
    tracker_type = Column(String(64), default="bytetrack")
    confidence_thresh = Column(Float, default=0.35)
    iou_thresh = Column(Float, default=0.45)
    crowding_group = Column(String(32), default="all")  # all, low, moderate, high, severe
    sample_count = Column(Integer, default=0)
    mae = Column(Float, default=0.0)
    rmse = Column(Float, default=0.0)
    mape = Column(Float, default=0.0)
    precision = Column(Float, default=0.0)
    recall = Column(Float, default=0.0)
    f1 = Column(Float, default=0.0)
    ap50 = Column(Float, default=0.0)
    mean_latency_ms = Column(Float, default=0.0)
    fps = Column(Float, default=0.0)
    created_at = Column(Float, default=time.time)
    status = Column(String(32), default="completed")  # running, completed, failed
    results_json = Column(Text, default="{}")
