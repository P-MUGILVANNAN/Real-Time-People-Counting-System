import io
import csv
import json
import time
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session

from backend.app.database.database import get_db, DBService
from backend.app.schemas.schemas import (
    RegionCreateRequest,
    LineCreateRequest,
    ThresholdsConfigRequest,
    AlertAcknowledgeRequest
)
from backend.app.services.cv_service import cv_service

router = APIRouter(prefix="/api/analytics", tags=["Analytics & Reports"])

@router.get("/current")
async def get_current_analytics(db: Session = Depends(get_db)):
    """Returns the most up-to-date real-time metrics snapshot."""
    cv_service.tick_db_snapshot()
    stats = cv_service.video_processor.get_stats()
    recent_alerts = cv_service.event_manager.get_recent_alerts(limit=5)
    
    return {
        "status": "success",
        "data": stats,
        "recent_alerts": recent_alerts,
        "current_session_id": cv_service.current_session_id
    }

@router.get("/history")
async def get_history(session_id: Optional[str] = None, limit: int = 150, db: Session = Depends(get_db)):
    """Retrieves chronological metric snapshots for dashboard trend charts."""
    snaps = DBService.get_snapshots(db, session_id=session_id, limit=limit)
    return {"count": len(snaps), "snapshots": snaps}

@router.get("/sessions")
async def get_sessions(limit: int = 20, db: Session = Depends(get_db)):
    """Returns previous video processing sessions and summary counts."""
    sessions = DBService.get_sessions(db, limit=limit)
    return {"count": len(sessions), "sessions": sessions}

@router.get("/alerts")
async def get_alerts(limit: int = 50, db: Session = Depends(get_db)):
    """Returns crowd alerts log with severity and acknowledgement state."""
    alerts = DBService.get_alerts(db, limit=limit)
    return {"count": len(alerts), "alerts": alerts}

@router.post("/alerts/ack")
async def acknowledge_alert(req: AlertAcknowledgeRequest, db: Session = Depends(get_db)):
    """Acknowledges an active crowd alert."""
    cv_service.event_manager.acknowledge_alert(req.alert_id)
    success = DBService.acknowledge_alert(db, req.alert_id)
    return {"status": "success", "acknowledged": success, "alert_id": req.alert_id}

@router.get("/regions")
async def get_regions():
    """Returns configured regions of interest and tripwire lines."""
    return {
        "regions": {rid: {"name": r.name, "polygon": r.polygon.tolist(), "area": r.area_pixels} 
                    for rid, r in cv_service.counter.regions.items()},
        "lines": {lid: {"name": l.name, "start_pt": list(l.start_pt), "end_pt": list(l.end_pt)}
                  for lid, l in cv_service.counter.lines.items()}
    }

@router.post("/regions")
async def add_or_update_region(req: RegionCreateRequest):
    """Adds or updates a polygonal region of interest."""
    cv_service.counter.add_region(
        region_id=req.region_id,
        name=req.name,
        polygon=req.polygon,
        moderate=req.moderate_thresh,
        high=req.high_thresh,
        critical=req.critical_thresh
    )
    return {"status": "success", "region_id": req.region_id}

@router.post("/lines")
async def add_or_update_line(req: LineCreateRequest):
    """Configures a directional virtual tripwire."""
    if len(req.start_pt) != 2 or len(req.end_pt) != 2:
        raise HTTPException(status_code=400, detail="Start and End points must be 2D coordinates [x, y]")
    
    cv_service.counter.add_line(
        line_id=req.line_id,
        start_pt=(int(req.start_pt[0]), int(req.start_pt[1])),
        end_pt=(int(req.end_pt[0]), int(req.end_pt[1])),
        name=req.name
    )
    return {"status": "success", "line_id": req.line_id}

@router.post("/thresholds")
async def update_thresholds(req: ThresholdsConfigRequest):
    """Updates system-wide crowd alert thresholds and cooldowns."""
    cv_service.event_manager.moderate_thresh = req.moderate_crowd_threshold
    cv_service.event_manager.high_thresh = req.high_crowd_threshold
    cv_service.event_manager.critical_thresh = req.critical_crowd_threshold
    cv_service.event_manager.cooldown_seconds = req.alert_cooldown_seconds
    return {"status": "success", "thresholds": req.model_dump()}


# Reports and Exports

@router.get("/reports/summary")
async def get_reports_summary(db: Session = Depends(get_db)):
    """Computes comprehensive aggregated analytics summary across sessions."""
    sessions = DBService.get_sessions(db, limit=50)
    snaps = DBService.get_snapshots(db, limit=500)
    alerts = DBService.get_alerts(db, limit=100)

    total_sessions = len(sessions)
    total_snapshots = len(snaps)
    total_alerts = len(alerts)

    counts = [s["active_tracked_count"] for s in snaps] if snaps else [0]
    densities = [s["density_estimate"] for s in snaps] if snaps else [0.0]
    fps_list = [s["processing_fps"] for s in snaps if s["processing_fps"] > 0] if snaps else [0.0]

    return {
        "total_sessions": total_sessions,
        "total_snapshots": total_snapshots,
        "total_alerts": total_alerts,
        "peak_crowd_count": max(counts) if counts else 0,
        "average_crowd_count": round(float(sum(counts) / max(1, len(counts))), 2),
        "average_processing_fps": round(float(sum(fps_list) / max(1, len(fps_list))), 1) if fps_list else 0.0,
        "recent_sessions": sessions[:5]
    }

@router.get("/reports/export/csv")
async def export_csv(session_id: Optional[str] = None, db: Session = Depends(get_db)):
    """Exports snapshot telemetry data to downloadable CSV."""
    snaps = DBService.get_snapshots(db, session_id=session_id, limit=2000)
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Timestamp", "Frame_Index", "Detection_Count", "Active_Tracked_Count",
        "Cumulative_Unique_Count", "Density_Estimate", "Hybrid_Estimate",
        "Processing_FPS", "Latency_MS", "Occlusion_Index", "Difficulty_Category"
    ])

    for s in snaps:
        writer.writerow([
            s["timestamp"], s["frame_index"], s["detection_count"], s["active_tracked_count"],
            s["cumulative_unique_count"], s["density_estimate"], s["hybrid_estimate"],
            s["processing_fps"], s["latency_ms"], s["occlusion_index"], s["difficulty_category"]
        ])

    output.seek(0)
    filename = f"crowd_analytics_{session_id or 'all'}_{int(time.time())}.csv"
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/reports/export/json")
async def export_json(session_id: Optional[str] = None, db: Session = Depends(get_db)):
    """Exports snapshot telemetry data to downloadable JSON."""
    snaps = DBService.get_snapshots(db, session_id=session_id, limit=2000)
    alerts = DBService.get_alerts(db, limit=200)
    
    data = {
        "export_timestamp": time.time(),
        "session_id": session_id,
        "total_records": len(snaps),
        "snapshots": snaps,
        "alerts": alerts
    }
    return JSONResponse(content=data)
