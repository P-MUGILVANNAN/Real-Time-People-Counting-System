from fastapi import APIRouter, HTTPException
from backend.app.schemas.schemas import CameraStartRequest, DisplayToggleRequest
from backend.app.services.cv_service import cv_service

router = APIRouter(prefix="/api/camera", tags=["Camera"])

@router.post("/start")
async def start_camera(req: CameraStartRequest):
    """Starts live inference on a connected webcam."""
    # Update tracker config if requested
    if req.tracker_type:
        cv_service.tracker.tracker_type = req.tracker_type
    if req.confidence_thresh:
        cv_service.detector.confidence_threshold = req.confidence_thresh
    if req.iou_thresh:
        cv_service.detector.iou_threshold = req.iou_thresh

    success = cv_service.video_processor.start_source(req.camera_index, source_type="webcam")
    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Unable to open camera index {req.camera_index}. Verify camera is plugged in and accessible."
        )

    cv_service.start_session(source_type="webcam", source_path=f"camera_{req.camera_index}")
    return {
        "status": "started",
        "camera_index": req.camera_index,
        "tracker_type": cv_service.tracker.tracker_type,
        "session_id": cv_service.current_session_id
    }

@router.post("/stop")
async def stop_camera():
    """Stops webcam processing and releases camera device."""
    cv_service.video_processor.stop()
    cv_service.end_current_session()
    return {"status": "stopped", "session_id": cv_service.current_session_id}

@router.post("/toggle")
async def toggle_display(req: DisplayToggleRequest):
    """Toggles overlay visibility (show_boxes, show_tracks, show_trails, show_heatmap, show_density_map, show_rois, show_lines)."""
    cv_service.video_processor.toggle_display(req.key, req.value)
    return {"status": "success", "display_options": cv_service.video_processor.display_options}

@router.post("/screenshot")
async def capture_screenshot():
    """Captures and saves a snapshot of the current frame with overlays."""
    path = cv_service.video_processor.capture_screenshot()
    if not path:
        raise HTTPException(status_code=400, detail="No active video frame available to capture.")
    return {"status": "success", "file_path": path}

@router.post("/record")
async def toggle_recording(enable: bool):
    """Enables or disables annotated video recording."""
    path = cv_service.video_processor.set_recording(enable)
    return {
        "status": "recording_started" if enable else "recording_stopped",
        "output_path": path
    }
