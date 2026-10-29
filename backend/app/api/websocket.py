import asyncio
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.app.services.cv_service import cv_service

router = APIRouter(tags=["WebSockets"])
logger = logging.getLogger("crowd_system.websocket")

@router.websocket("/ws/analytics")
async def websocket_analytics(websocket: WebSocket):
    """
    Real-time high-efficiency telemetry stream for dashboard charts and metrics.
    Emits comprehensive analytics snapshots every 500ms.
    """
    await websocket.accept()
    logger.info("WebSocket analytics client connected.")
    try:
        while True:
            cv_service.tick_db_snapshot()
            stats = cv_service.video_processor.get_stats()
            alerts = cv_service.event_manager.get_recent_alerts(limit=5)
            
            payload = {
                "stats": stats,
                "alerts": alerts,
                "session_id": cv_service.current_session_id
            }
            await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        logger.info("WebSocket analytics client disconnected.")
    except Exception as e:
        logger.error(f"WebSocket analytics error: {e}")
        try:
            await websocket.close()
        except Exception:
            pass


@router.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    """
    WebSocket endpoint streaming compressed JPEG binary video frames.
    """
    await websocket.accept()
    logger.info("WebSocket video stream client connected.")
    try:
        while True:
            jpeg = cv_service.video_processor.get_latest_jpeg()
            if jpeg is not None:
                await websocket.send_bytes(jpeg)
            await asyncio.sleep(0.04)  # ~25 fps
    except WebSocketDisconnect:
        logger.info("WebSocket stream client disconnected.")
    except Exception as e:
        logger.error(f"WebSocket stream error: {e}")
        try:
            await websocket.close()
        except Exception:
            pass
