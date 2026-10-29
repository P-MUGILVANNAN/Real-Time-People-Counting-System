import numpy as np
import cv2
from typing import List, Dict, Any, Optional, Tuple

class HeatmapGenerator:
    """
    Generates and renders spatial crowd density heatmaps, detection-center density surfaces,
    and accumulated trajectory heatmaps.
    """

    def __init__(self, decay_factor: float = 0.95, sigma: int = 25):
        self.decay_factor = decay_factor
        self.sigma = sigma
        self.accumulated_trajectory_map: Optional[np.ndarray] = None
        self.colormap = cv2.COLORMAP_JET

    def reset_trajectory_map(self):
        self.accumulated_trajectory_map = None

    def set_colormap(self, name: str):
        maps = {
            "jet": cv2.COLORMAP_JET,
            "turbo": cv2.COLORMAP_TURBO,
            "viridis": cv2.COLORMAP_VIRIDIS,
            "inferno": cv2.COLORMAP_INFERNO
        }
        self.colormap = maps.get(name.lower(), cv2.COLORMAP_JET)

    def generate_detection_density_map(
        self,
        frame_shape: Tuple[int, int],
        detections: List[Dict[str, Any]]
    ) -> np.ndarray:
        """
        Creates an instantaneous Gaussian-smoothed crowd density map
        from current bounding box centers.
        """
        h, w = frame_shape[:2]
        density_layer = np.zeros((h, w), dtype=np.float32)

        if not detections:
            return density_layer

        ksize = self.sigma * 4 + 1
        # Precompute a small Gaussian kernel
        kernel_1d = cv2.getGaussianKernel(ksize, self.sigma)
        kernel_2d = np.outer(kernel_1d, kernel_1d)
        kernel_2d = kernel_2d / np.sum(kernel_2d)

        half_k = ksize // 2

        for det in detections:
            cx, cy = det["center"]
            # Bounding box of kernel inside image
            y1 = max(0, cy - half_k)
            y2 = min(h, cy + half_k + 1)
            x1 = max(0, cx - half_k)
            x2 = min(w, cx + half_k + 1)

            # Corresponding kernel coordinates
            ky1 = y1 - (cy - half_k)
            ky2 = ky1 + (y2 - y1)
            kx1 = x1 - (cx - half_k)
            kx2 = kx1 + (x2 - x1)

            if y2 > y1 and x2 > x1:
                density_layer[y1:y2, x1:x2] += kernel_2d[ky1:ky2, kx1:kx2]

        return density_layer

    def update_trajectory_heatmap(
        self,
        frame_shape: Tuple[int, int],
        active_tracks: List[Any]
    ) -> np.ndarray:
        """
        Updates the accumulated trajectory heatmap across time with a decay factor.
        """
        h, w = frame_shape[:2]
        if self.accumulated_trajectory_map is None or self.accumulated_trajectory_map.shape != (h, w):
            self.accumulated_trajectory_map = np.zeros((h, w), dtype=np.float32)
        else:
            self.accumulated_trajectory_map *= self.decay_factor

        for track in active_tracks:
            cx, cy = track.center
            if 0 <= cx < w and 0 <= cy < h:
                # Add Gaussian splat for active track position
                cv2.circle(self.accumulated_trajectory_map, (cx, cy), self.sigma // 2, 1.0, -1)

        return self.accumulated_trajectory_map

    def colorize_density_map(
        self,
        density_map: np.ndarray,
        global_max: Optional[float] = None
    ) -> np.ndarray:
        """
        Converts a continuous floating-point density map into an 8-bit BGR colored heatmap.
        """
        if density_map is None or density_map.size == 0:
            return np.zeros((100, 100, 3), dtype=np.uint8)

        max_val = global_max if global_max and global_max > 0 else np.max(density_map)
        if max_val <= 0:
            norm_map = np.zeros_like(density_map, dtype=np.uint8)
        else:
            norm_map = np.clip((density_map / max_val) * 255.0, 0, 255).astype(np.uint8)

        colored = cv2.applyColorMap(norm_map, self.colormap)
        return colored

    def overlay_heatmap(
        self,
        frame: np.ndarray,
        density_map: np.ndarray,
        alpha: float = 0.55
    ) -> np.ndarray:
        """
        Overlays the colorized density heatmap onto the original video frame.
        """
        if density_map is None or density_map.size == 0:
            return frame

        h, w = frame.shape[:2]
        # Resize density map if dimension differs (e.g. 1/4 resolution from MCNN)
        if density_map.shape[:2] != (h, w):
            density_map_resized = cv2.resize(density_map, (w, h), interpolation=cv2.INTER_LINEAR)
        else:
            density_map_resized = density_map

        colored = self.colorize_density_map(density_map_resized)

        # Mask out zero/near-zero density areas to keep background clear
        max_val = np.max(density_map_resized)
        if max_val <= 0.0001:
            return frame

        norm_mask = (density_map_resized / max_val)
        # Apply smooth alpha weighting where density exists
        blended = frame.copy()
        for c in range(3):
            blended[:, :, c] = np.clip(
                (1.0 - alpha * norm_mask) * frame[:, :, c] + (alpha * norm_mask) * colored[:, :, c],
                0, 255
            ).astype(np.uint8)

        return blended
