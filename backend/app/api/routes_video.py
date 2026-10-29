import os
import time
import shutil
from typing import List, Generator
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse

from backend.app.schemas.schemas import VideoStartRequest
from backend.app.services.cv_service import cv_service

router = APIRouter(prefix="/api/video", tags=["Video"])

UPLOAD_DIR = "outputs/videos"
SAMPLE_DIR = "datasets/sample"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(SAMPLE_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}

@router.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    """Uploads a video file for people counting and density inference."""
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{ext}'. Allowed: {list(ALLOWED_EXTENSIONS)}"
        )

    # Sanitize and create unique file path
    safe_name = f"upload_{int(time.time())}_{os.path.basename(file.filename)}"
    dest_path = os.path.join(UPLOAD_DIR, safe_name)

    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "status": "uploaded",
        "filename": safe_name,
        "file_path": dest_path,
        "size_bytes": os.path.getsize(dest_path)
    }

@router.get("/files")
async def list_video_files():
    """Lists uploaded video files and built-in sample videos."""
    files = []
    
    # Check sample videos
    if os.path.exists(SAMPLE_DIR):
        for f in os.listdir(SAMPLE_DIR):
            if os.path.splitext(f)[1].lower() in ALLOWED_EXTENSIONS:
                files.append({
                    "filename": f,
                    "location": "sample",
                    "path": os.path.join(SAMPLE_DIR, f),
                    "size_mb": round(os.path.getsize(os.path.join(SAMPLE_DIR, f)) / (1024 * 1024), 2)
                })

    # Check uploaded videos
    if os.path.exists(UPLOAD_DIR):
        for f in os.listdir(UPLOAD_DIR):
            if os.path.splitext(f)[1].lower() in ALLOWED_EXTENSIONS:
                files.append({
                    "filename": f,
                    "location": "uploaded",
                    "path": os.path.join(UPLOAD_DIR, f),
                    "size_mb": round(os.path.getsize(os.path.join(UPLOAD_DIR, f)) / (1024 * 1024), 2)
                })

    return {"count": len(files), "videos": files}

@router.post("/start")
async def start_video(req: VideoStartRequest):
    """Starts video processing loop for a selected video file."""
    # Find file path
    candidate_paths = [
        os.path.join(UPLOAD_DIR, req.video_filename),
        os.path.join(SAMPLE_DIR, req.video_filename),
        req.video_filename
    ]
    target_path = None
    for p in candidate_paths:
        if os.path.exists(p) and os.path.isfile(p):
            target_path = p
            break

    if not target_path:
        raise HTTPException(
            status_code=404,
            detail=f"Video file '{req.video_filename}' not found in upload or sample directories."
        )

    if req.tracker_type:
        cv_service.tracker.tracker_type = req.tracker_type
    if req.confidence_thresh:
        cv_service.detector.confidence_threshold = req.confidence_thresh
    if req.iou_thresh:
        cv_service.detector.iou_threshold = req.iou_thresh

    success = cv_service.video_processor.start_source(target_path, source_type="file")
    if not success:
        raise HTTPException(status_code=400, detail="Could not open video file.")

    cv_service.start_session(source_type="file", source_path=target_path)
    return {
        "status": "started",
        "video": req.video_filename,
        "session_id": cv_service.current_session_id
    }

@router.post("/stop")
async def stop_video():
    """Stops video playback and processing."""
    cv_service.video_processor.stop()
    cv_service.end_current_session()
    return {"status": "stopped", "session_id": cv_service.current_session_id}

@router.post("/pause")
async def pause_video():
    cv_service.video_processor.pause()
    return {"status": "paused"}

@router.post("/resume")
async def resume_video():
    cv_service.video_processor.resume()
    return {"status": "resumed"}

@router.get("/status")
async def get_video_status():
    """Returns current video processor runtime statistics."""
    cv_service.tick_db_snapshot()
    return cv_service.video_processor.get_stats()

def _mjpeg_generator() -> Generator[bytes, None, None]:
    """Generates continuous multipart MJPEG frame stream for web browsers."""
    while True:
        jpeg = cv_service.video_processor.get_latest_jpeg()
        if jpeg is not None:
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n")
        time.sleep(0.033)  # ~30 fps max streaming

@router.get("/stream")
async def video_stream():
    """MJPEG Live Streaming Endpoint for Browser <img src='/api/video/stream' />."""
    return StreamingResponse(
        _mjpeg_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )
