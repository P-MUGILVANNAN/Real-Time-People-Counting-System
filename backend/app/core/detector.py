import time
import os
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import cv2
import torch

try:
    from ultralytics import YOLO
    ULTRALYTICS_AVAILABLE = True
except ImportError:
    ULTRALYTICS_AVAILABLE = False

logger = logging.getLogger("crowd_system.detector")

class PersonDetector:
    """
    Robust Person Detector leveraging Ultralytics YOLO models (e.g. YOLOv8n/s/m or CrowdHuman fine-tuned).
    Strictly filters for the 'person' class (COCO class 0).
    Provides exact inference timings, bounding box normalization, and fallback mechanisms.
    """

    def __init__(
        self,
        model_path: str = "models/detection/yolov8n.pt",
        confidence_threshold: float = 0.35,
        iou_threshold: float = 0.45,
        input_size: int = 640,
        device: str = "cpu",
        max_detections: int = 300
    ):
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.input_size = input_size
        self.max_detections = max_detections
        
        # Determine actual device
        if device == "cuda" and torch.cuda.is_available():
            self.device = "cuda"
        else:
            self.device = "cpu"
            if device == "cuda":
                logger.warning("CUDA requested but not available. Falling back to CPU inference.")

        self.model = None
        self.is_loaded = False
        self.model_name = os.path.basename(model_path) if model_path else "yolov8n.pt"
        self.last_inference_time_ms = 0.0
        self.last_fps = 0.0

        self.load_model()

    def load_model(self) -> bool:
        """Loads or initializes the YOLO detector model."""
        if not ULTRALYTICS_AVAILABLE:
            logger.error("Ultralytics library is not installed.")
            self.is_loaded = False
            return False

        try:
            logger.info(f"Loading YOLO model from {self.model_path} on device {self.device}...")
            
            # If specified path doesn't exist locally, Ultralytics can download yolov8n.pt automatically
            if not os.path.exists(self.model_path):
                # Ensure directory exists
                os.makedirs(os.path.dirname(os.path.abspath(self.model_path)), exist_ok=True)
                logger.info(f"Local weight {self.model_path} not found. Initializing standard baseline YOLOv8n...")
                self.model = YOLO("yolov8n.pt")
                # Save to desired path if possible
                try:
                    self.model.save(self.model_path)
                except Exception:
                    pass
            else:
                self.model = YOLO(self.model_path)

            # Move to target device
            self.model.to(self.device)
            self.is_loaded = True
            logger.info(f"YOLO detector successfully loaded on {self.device}.")
            return True
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            self.is_loaded = False
            return False

    def detect(self, frame: np.ndarray) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Runs person detection on a single BGR image/frame.
        
        Returns:
            detections: List of dicts with bbox [x1, y1, x2, y2], confidence, class_id, center [cx, cy], area, aspect_ratio
            meta: Dict containing inference_time_ms, fps, frame_shape, count
        """
        if not self.is_loaded or self.model is None or frame is None or frame.size == 0:
            return [], {
                "inference_time_ms": 0.0,
                "fps": 0.0,
                "count": 0,
                "error": "Detector not loaded or empty frame"
            }

        start_time = time.perf_counter()
        height, width = frame.shape[:2]

        try:
            # Predict using YOLO with person class filter (classes=[0])
            results = self.model.predict(
                source=frame,
                conf=self.confidence_threshold,
                iou=self.iou_threshold,
                imgsz=self.input_size,
                device=self.device,
                classes=[0],  # Person class only
                max_det=self.max_detections,
                verbose=False
            )

            end_time = time.perf_counter()
            self.last_inference_time_ms = round((end_time - start_time) * 1000.0, 2)
            self.last_fps = round(1000.0 / max(self.last_inference_time_ms, 0.001), 1)

            detections: List[Dict[str, Any]] = []

            if results and len(results) > 0:
                boxes = results[0].boxes
                if boxes is not None and len(boxes) > 0:
                    xyxy = boxes.xyxy.cpu().numpy()
                    confs = boxes.conf.cpu().numpy()
                    classes = boxes.cls.cpu().numpy().astype(int)

                    for box, conf, cls_id in zip(xyxy, confs, classes):
                        if cls_id != 0:
                            continue  # Strict person filtering
                        x1, y1, x2, y2 = [int(v) for v in box]
                        # Clamp to frame bounds
                        x1 = max(0, min(width - 1, x1))
                        y1 = max(0, min(height - 1, y1))
                        x2 = max(0, min(width - 1, x2))
                        y2 = max(0, min(height - 1, y2))
                        
                        bw = max(1, x2 - x1)
                        bh = max(1, y2 - y1)
                        cx = int(x1 + bw / 2)
                        cy = int(y1 + bh / 2)
                        area = bw * bh
                        aspect_ratio = round(bh / float(bw), 2)

                        detections.append({
                            "bbox": [x1, y1, x2, y2],
                            "confidence": round(float(conf), 3),
                            "class_id": 0,
                            "class_name": "person",
                            "center": [cx, cy],
                            "width": bw,
                            "height": bh,
                            "area": area,
                            "aspect_ratio": aspect_ratio
                        })

            meta = {
                "inference_time_ms": self.last_inference_time_ms,
                "fps": self.last_fps,
                "count": len(detections),
                "device": self.device,
                "model_name": self.model_name
            }
            return detections, meta

        except Exception as e:
            logger.error(f"Detection inference error: {e}")
            return [], {
                "inference_time_ms": 0.0,
                "fps": 0.0,
                "count": 0,
                "error": str(e)
            }

    def draw_detections(
        self,
        frame: np.ndarray,
        detections: List[Dict[str, Any]],
        color: Tuple[int, int, int] = (0, 255, 128),
        show_conf: bool = True
    ) -> np.ndarray:
        """Draws bounding boxes and labels onto the frame."""
        annotated = frame.copy()
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            conf = det["confidence"]
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            
            label = f"Person {conf:.2f}" if show_conf else "Person"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
            cv2.rectangle(annotated, (x1, max(0, y1 - th - 6)), (x1 + tw + 4, max(0, y1)), color, -1)
            cv2.putText(
                annotated,
                label,
                (x1 + 2, max(th, y1 - 3)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (0, 0, 0),
                1,
                cv2.LINE_AA
            )
        return annotated

    def get_status(self) -> Dict[str, Any]:
        """Returns diagnostic details about the detector."""
        return {
            "loaded": self.is_loaded,
            "model_path": self.model_path,
            "model_name": self.model_name,
            "device": self.device,
            "confidence_threshold": self.confidence_threshold,
            "iou_threshold": self.iou_threshold,
            "input_size": self.input_size,
            "last_inference_time_ms": self.last_inference_time_ms,
            "last_fps": self.last_fps
        }
