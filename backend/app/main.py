import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.config import settings
from backend.app.database.database import init_db
from backend.app.services.cv_service import cv_service

# Routers
from backend.app.api.routes_camera import router as camera_router
from backend.app.api.routes_video import router as video_router
from backend.app.api.routes_analytics import router as analytics_router
from backend.app.api.routes_models import router as models_router
from backend.app.api.routes_experiments import router as experiments_router
from backend.app.api.websocket import router as ws_router

logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("crowd_system.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure DB & directories
    logger.info("Starting Crowd Intelligence System backend...")
    init_db()
    for d in ["outputs/videos", "outputs/heatmaps", "outputs/reports", "outputs/logs", "datasets/sample"]:
        os.makedirs(d, exist_ok=True)
    yield
    # Shutdown: Release CV resources & video capture
    logger.info("Shutting down backend and releasing camera/threads...")
    cv_service.video_processor.stop()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Full-stack real-time computer vision system for people counting, multi-object tracking, and continuous crowd density estimation.",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(camera_router)
app.include_router(video_router)
app.include_router(analytics_router)
app.include_router(models_router)
app.include_router(experiments_router)
app.include_router(ws_router)

@app.get("/api/health", tags=["Health"])
async def health_check():
    """Health check endpoint validating system status and model readiness."""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "device": settings.DEVICE,
        "detector_loaded": cv_service.detector.is_loaded,
        "density_model_status": cv_service.density_estimator.status
    }

@app.get("/", tags=["Root"])
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs_url": "/docs",
        "status": "operational"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
