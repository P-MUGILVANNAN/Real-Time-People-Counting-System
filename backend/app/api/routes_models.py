import os
import platform
import psutil
import torch
from fastapi import APIRouter
from backend.app.config import settings
from backend.app.services.cv_service import cv_service

router = APIRouter(prefix="/api", tags=["Models & System"])

@router.get("/models")
async def get_models_status():
    """Returns the operational status, device placement, and weight status of all models."""
    detector_status = cv_service.detector.get_status()
    density_status = {
        "architecture": "MCNN (Multi-Column Convolutional Neural Network)",
        "weights_path": cv_service.density_estimator.weights_path,
        "status": cv_service.density_estimator.status,
        "has_valid_weights": cv_service.density_estimator.has_weights,
        "device": cv_service.density_estimator.device,
        "description": "3-column CNN with varying receptive fields for continuous crowd density regression."
    }
    tracker_status = {
        "tracker_type": cv_service.tracker.tracker_type,
        "track_buffer": cv_service.tracker.track_buffer,
        "match_thresh": cv_service.tracker.match_thresh,
        "active_tracks_count": cv_service.tracker.get_active_count(),
        "cumulative_unique_count": cv_service.tracker.get_cumulative_count()
    }

    return {
        "detector": detector_status,
        "density_model": density_status,
        "tracker": tracker_status
    }

@router.get("/system/status")
async def get_system_status():
    """Returns hardware resource utilization, CPU/GPU status, and memory metrics."""
    cuda_available = torch.cuda.is_available()
    device_name = torch.cuda.get_device_name(0) if cuda_available else "CPU (Host System)"
    
    mem = psutil.virtual_memory()
    cpu_usage = psutil.cpu_percent(interval=None)

    return {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "torch_version": torch.__version__,
        "cuda_available": cuda_available,
        "active_device": settings.DEVICE,
        "device_name": device_name,
        "cpu_usage_pct": cpu_usage,
        "memory_total_gb": round(mem.total / (1024 ** 3), 2),
        "memory_used_gb": round(mem.used / (1024 ** 3), 2),
        "memory_used_pct": mem.percent
    }
