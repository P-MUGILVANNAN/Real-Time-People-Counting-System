from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class CameraStartRequest(BaseModel):
    camera_index: int = Field(0, description="Webcam device index (0, 1, ...)")
    tracker_type: str = Field("bytetrack", description="Tracking algorithm ('bytetrack' or 'botsort')")
    confidence_thresh: Optional[float] = Field(0.35, ge=0.05, le=0.95)
    iou_thresh: Optional[float] = Field(0.45, ge=0.05, le=0.95)

class VideoStartRequest(BaseModel):
    video_filename: str = Field(..., description="Uploaded video filename located in outputs/videos or datasets/sample")
    tracker_type: str = Field("bytetrack")
    confidence_thresh: Optional[float] = Field(0.35, ge=0.05, le=0.95)
    iou_thresh: Optional[float] = Field(0.45, ge=0.05, le=0.95)

class DisplayToggleRequest(BaseModel):
    key: str = Field(..., description="show_boxes, show_tracks, show_trails, show_heatmap, show_density_map, show_rois, show_lines")
    value: bool

class RegionCreateRequest(BaseModel):
    region_id: str
    name: str
    polygon: List[List[int]]
    moderate_thresh: int = 8
    high_thresh: int = 15
    critical_thresh: int = 25

class LineCreateRequest(BaseModel):
    line_id: str
    name: str
    start_pt: List[int]
    end_pt: List[int]

class ThresholdsConfigRequest(BaseModel):
    moderate_crowd_threshold: int = Field(10, ge=1)
    high_crowd_threshold: int = Field(25, ge=2)
    critical_crowd_threshold: int = Field(50, ge=3)
    alert_cooldown_seconds: float = Field(15.0, ge=1.0)

class AlertAcknowledgeRequest(BaseModel):
    alert_id: str

class ExperimentRunRequest(BaseModel):
    name: str = Field(..., description="Descriptive experiment identifier")
    dataset_name: str = Field("crowdhuman", description="crowdhuman or shanghaitech")
    model_type: str = Field("yolo", description="yolo, mcnn, or hybrid")
    tracker_type: str = Field("bytetrack", description="bytetrack or botsort")
    confidence_thresh: float = Field(0.35, ge=0.1, le=0.9)
    iou_thresh: float = Field(0.45, ge=0.1, le=0.9)
    crowding_group: str = Field("all", description="all, low, moderate, high, severe")
