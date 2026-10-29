import os
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import cv2
import torch
import torch.nn as nn

logger = logging.getLogger("crowd_system.density")

# ==========================================
# 1. PyTorch Neural Network Architectures
# ==========================================

class ConvBlock(nn.Module):
    def __init__(self, in_channels: int, out_channels: int, kernel_size: int, stride: int = 1):
        super().__init__()
        padding = (kernel_size - 1) // 2
        self.conv = nn.Conv2d(in_channels, out_channels, kernel_size, stride=stride, padding=padding)
        self.bn = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.relu(self.bn(self.conv(x)))


class MCNN(nn.Module):
    """
    Multi-Column Convolutional Neural Network (MCNN) for Single-Image Crowd Counting.
    (Zhang et al., CVPR 2016)
    
    Contains 3 parallel branches with different receptive field filter sizes to capture
    crowd heads of varied scale due to perspective effects:
      - Branch 1 (Large receptive field): 9x9, 7x7 filters
      - Branch 2 (Medium receptive field): 7x7, 5x5 filters
      - Branch 3 (Small receptive field): 5x5, 3x3 filters
    Output density map is 1/4th input resolution, and summing all pixel values equals total count.
    """

    def __init__(self):
        super().__init__()

        # Branch 1: Large heads
        self.branch1 = nn.Sequential(
            ConvBlock(3, 16, 9),
            nn.MaxPool2d(2, 2),
            ConvBlock(16, 32, 7),
            nn.MaxPool2d(2, 2),
            ConvBlock(32, 16, 7),
            ConvBlock(16, 8, 7)
        )

        # Branch 2: Medium heads
        self.branch2 = nn.Sequential(
            ConvBlock(3, 20, 7),
            nn.MaxPool2d(2, 2),
            ConvBlock(20, 40, 5),
            nn.MaxPool2d(2, 2),
            ConvBlock(40, 20, 5),
            ConvBlock(20, 10, 5)
        )

        # Branch 3: Small heads
        self.branch3 = nn.Sequential(
            ConvBlock(3, 24, 5),
            nn.MaxPool2d(2, 2),
            ConvBlock(24, 48, 3),
            nn.MaxPool2d(2, 2),
            ConvBlock(48, 24, 3),
            ConvBlock(24, 12, 3)
        )

        # Fusion layer: 8 + 10 + 12 = 30 channels -> 1 channel
        self.fuse = nn.Sequential(
            ConvBlock(30, 1, 1),
            nn.ReLU()  # Crowd density cannot be negative
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        b1 = self.branch1(x)
        b2 = self.branch2(x)
        b3 = self.branch3(x)
        merged = torch.cat([b1, b2, b3], dim=1)
        density_map = self.fuse(merged)
        return density_map


# ==========================================
# 2. Density Estimator Adapters
# ==========================================

class DensityEstimatorAdapter(ABC):
    """Abstract interface for all crowd density estimation methods."""

    @abstractmethod
    def estimate(self, frame: np.ndarray, detections: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Returns density count and 2D spatial density matrix."""
        pass


class DetectionDensityEstimator(DensityEstimatorAdapter):
    """
    Approach A: Detection-Based Spatial Density Estimation.
    Constructs a spatial crowd density distribution and grid occupancy map
    from detected person bounding boxes.
    """

    def __init__(self, grid_rows: int = 4, grid_cols: int = 4):
        self.grid_rows = grid_rows
        self.grid_cols = grid_cols

    def estimate(self, frame: np.ndarray, detections: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        if detections is None:
            detections = []

        h, w = frame.shape[:2]
        count = len(detections)

        # Compute grid-based distribution
        cell_h = h / self.grid_rows
        cell_w = w / self.grid_cols
        grid = np.zeros((self.grid_rows, self.grid_cols), dtype=int)

        for det in detections:
            cx, cy = det["center"]
            r = min(self.grid_rows - 1, max(0, int(cy / cell_h)))
            c = min(self.grid_cols - 1, max(0, int(cx / cell_w)))
            grid[r, c] += 1

        # Classify crowd density category
        if count < 5:
            category = "low"
        elif count < 15:
            category = "moderate"
        elif count < 30:
            category = "high"
        else:
            category = "severe"

        density_per_k_px = round((count / float(max(1, h * w))) * 1000.0, 4)

        return {
            "method": "detection_based",
            "estimated_count": float(count),
            "density_per_1k_px": density_per_k_px,
            "category": category,
            "grid": grid.tolist(),
            "grid_dimensions": [self.grid_rows, self.grid_cols],
            "is_learned_density_map": False
        }


class MCNNDensityEstimator(DensityEstimatorAdapter):
    """
    Approach B: Learned Density-Map Regression (MCNN).
    Computes continuous 2D crowd density distribution: D(x, y) >= 0.
    Total Count = Sum over all pixels of D(x, y).
    """

    def __init__(
        self,
        weights_path: str = "models/density/mcnn_shanghaitech.pth",
        device: str = "cpu"
    ):
        self.weights_path = weights_path
        self.device = "cuda" if (device == "cuda" and torch.cuda.is_available()) else "cpu"
        self.model = MCNN().to(self.device)
        self.model.eval()

        self.status = "missing_weights"
        self.has_weights = False
        self.load_weights()

    def load_weights(self) -> bool:
        """Loads pretrained MCNN weights if present on disk."""
        if os.path.exists(self.weights_path):
            try:
                state_dict = torch.load(self.weights_path, map_location=self.device)
                self.model.load_state_dict(state_dict)
                self.has_weights = True
                self.status = "ready"
                logger.info(f"Loaded MCNN weights from {self.weights_path} onto {self.device}.")
                return True
            except Exception as e:
                logger.error(f"Error loading MCNN weights: {e}")
                self.status = "error_loading_weights"
                self.has_weights = False
                return False
        else:
            self.status = "weights_missing"
            self.has_weights = False
            logger.info(f"MCNN weights not found at {self.weights_path}. Model status: {self.status}")
            return False

    def estimate(self, frame: np.ndarray, detections: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Runs neural density map inference on input frame.
        If weights are not present, explicitly reports uncalibrated/untrained status.
        """
        if frame is None or frame.size == 0:
            return {
                "method": "density_map_regression",
                "estimated_count": 0.0,
                "status": "empty_frame",
                "density_map": None
            }

        h, w = frame.shape[:2]

        if not self.has_weights:
            return {
                "method": "density_map_regression",
                "estimated_count": 0.0,
                "status": self.status,
                "note": "Untrained model or weights missing. Model requires trained weights on ShanghaiTech.",
                "has_valid_weights": False,
                "density_map": None
            }

        try:
            # Preprocess: BGR -> RGB, normalize to [0, 1]
            img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
            # Standard ImageNet normalization
            mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
            std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
            normalized = (img_rgb - mean) / std

            # HWC -> CHW -> NCHW tensor
            tensor = torch.from_numpy(normalized).permute(2, 0, 1).unsqueeze(0).to(self.device)

            with torch.no_grad():
                out = self.model(tensor)
                dmap = out.squeeze().cpu().numpy()

            count = float(np.sum(dmap))

            return {
                "method": "density_map_regression",
                "estimated_count": round(count, 2),
                "status": "ready",
                "has_valid_weights": True,
                "density_map": dmap,
                "density_map_shape": list(dmap.shape),
                "is_learned_density_map": True
            }

        except Exception as e:
            logger.error(f"MCNN inference exception: {e}")
            return {
                "method": "density_map_regression",
                "estimated_count": 0.0,
                "status": f"error: {str(e)}",
                "has_valid_weights": False,
                "density_map": None
            }


class HybridDensityEstimator:
    """
    Hybrid Crowd Estimator combining detection/tracking counts with density-map regression.
    
    Formula:
        N_hybrid = alpha * N_det_or_track + (1 - alpha) * N_density_map
        
    where alpha in [0, 1] can be dynamically adjusted based on scene occlusion level:
      - Low occlusion: Detection/Tracking is highly reliable -> higher alpha
      - Severe occlusion: Bounding boxes overlap heavily / merge -> lower alpha (rely more on continuous density map)
    """

    def __init__(self, default_alpha: float = 0.5):
        self.default_alpha = default_alpha

    def estimate(
        self,
        det_or_track_count: float,
        density_map_result: Dict[str, Any],
        occlusion_index: Optional[float] = None
    ) -> Dict[str, Any]:
        has_density_weights = density_map_result.get("has_valid_weights", False)

        if not has_density_weights:
            # Fall back 100% to detection/tracking if density weights are not installed
            return {
                "hybrid_count": float(det_or_track_count),
                "alpha_used": 1.0,
                "detection_component": float(det_or_track_count),
                "density_component": 0.0,
                "note": "Density regression weights unavailable; falling back to detection/tracking baseline."
            }

        density_count = float(density_map_result.get("estimated_count", 0.0))

        # Dynamic alpha calculation based on occlusion index if provided
        if occlusion_index is not None:
            # When occlusion is 0, alpha is ~0.8; when occlusion is 1.0, alpha is ~0.2
            alpha = max(0.1, min(0.9, 0.85 - (0.65 * occlusion_index)))
        else:
            alpha = self.default_alpha

        hybrid_val = (alpha * det_or_track_count) + ((1.0 - alpha) * density_count)

        return {
            "hybrid_count": round(float(hybrid_val), 2),
            "alpha_used": round(float(alpha), 3),
            "detection_component": float(det_or_track_count),
            "density_component": round(density_count, 2),
            "note": "Fused estimate combining detection tracking and density-map regression."
        }
