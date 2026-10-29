import math
import logging
from typing import List, Dict, Any, Optional, Tuple, Set
import numpy as np
import cv2

logger = logging.getLogger("crowd_system.counter")

class LineCrossingDetector:
    """
    Directional virtual tripwire for counting people entering and exiting.
    Uses 2D segment intersection and orientation tests with a per-track hysteresis state machine.
    """

    def __init__(
        self,
        line_id: str,
        start_pt: Tuple[int, int],
        end_pt: Tuple[int, int],
        name: str = "Main Entrance"
    ):
        self.line_id = line_id
        self.start_pt = start_pt
        self.end_pt = end_pt
        self.name = name

        self.count_in: int = 0
        self.count_out: int = 0
        self.events: List[Dict[str, Any]] = []
        # Maps track_id to last known signed side (+1, -1, or 0) and last crossing timestamp
        self.track_states: Dict[int, int] = {}
        self.crossed_tracks: Set[Tuple[int, str]] = set()  # (track_id, direction)

    def reset(self):
        self.count_in = 0
        self.count_out = 0
        self.events.clear()
        self.track_states.clear()
        self.crossed_tracks.clear()

    def _signed_distance(self, pt: Tuple[int, int]) -> float:
        """Computes cross-product signed distance from pt to directed line start_pt -> end_pt."""
        x, y = pt
        x1, y1 = self.start_pt
        x2, y2 = self.end_pt
        return (x - x1) * (y2 - y1) - (y - y1) * (x2 - x1)

    @staticmethod
    def _segments_intersect(p1: Tuple[int, int], p2: Tuple[int, int],
                            p3: Tuple[int, int], p4: Tuple[int, int]) -> bool:
        """Determines if segment p1-p2 intersects segment p3-p4."""
        def ccw(A, B, C):
            return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])
        return (ccw(p1, p3, p4) != ccw(p2, p3, p4)) and (ccw(p1, p2, p3) != ccw(p1, p2, p4))

    def update(self, tracks: List[Any]) -> Dict[str, Any]:
        """
        Updates line crossing state for all active tracks in the frame.
        """
        new_events = []

        for track in tracks:
            tid = track.track_id
            if len(track.history) < 2:
                # Initialize state
                curr_pt = track.history[-1][:2]
                dist = self._signed_distance(curr_pt)
                self.track_states[tid] = 1 if dist > 0 else (-1 if dist < 0 else 0)
                continue

            prev_pt = track.history[-2][:2]
            curr_pt = track.history[-1][:2]

            prev_dist = self._signed_distance(prev_pt)
            curr_dist = self._signed_distance(curr_pt)

            # Check if trajectory crossed the line
            if (prev_dist * curr_dist < 0) or (prev_dist == 0 and curr_dist != 0):
                # Verify segment intersection with line
                if self._segments_intersect(prev_pt, curr_pt, self.start_pt, self.end_pt):
                    # Negative to positive = IN, Positive to negative = OUT
                    direction = "IN" if curr_dist > 0 else "OUT"
                    event_key = (tid, direction)

                    if event_key not in self.crossed_tracks:
                        self.crossed_tracks.add(event_key)
                        if direction == "IN":
                            self.count_in += 1
                        else:
                            self.count_out += 1

                        event = {
                            "line_id": self.line_id,
                            "line_name": self.name,
                            "track_id": tid,
                            "direction": direction,
                            "timestamp": track.history[-1][2],
                            "position": curr_pt
                        }
                        self.events.append(event)
                        new_events.append(event)

            self.track_states[tid] = 1 if curr_dist > 0 else (-1 if curr_dist < 0 else 0)

        return {
            "line_id": self.line_id,
            "name": self.name,
            "count_in": self.count_in,
            "count_out": self.count_out,
            "net_flow": self.count_in - self.count_out,
            "new_events": new_events
        }

    def draw(self, frame: np.ndarray) -> np.ndarray:
        """Renders the virtual line and crossing stats onto the frame."""
        annotated = frame.copy()
        cv2.line(annotated, self.start_pt, self.end_pt, (0, 215, 255), 3)
        # Draw start and end markers
        cv2.circle(annotated, self.start_pt, 5, (0, 165, 255), -1)
        cv2.circle(annotated, self.end_pt, 5, (0, 165, 255), -1)

        # Label line
        mid_x = int((self.start_pt[0] + self.end_pt[0]) / 2)
        mid_y = int((self.start_pt[1] + self.end_pt[1]) / 2)
        text = f"{self.name} | IN: {self.count_in} OUT: {self.count_out}"
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
        cv2.rectangle(annotated, (mid_x - 4, mid_y - th - 6), (mid_x + tw + 6, mid_y + 4), (0, 0, 0), -1)
        cv2.putText(annotated, text, (mid_x, mid_y - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 215, 255), 1)
        return annotated


class RegionOfInterest:
    """
    Arbitrary polygon region of interest (ROI) for crowd density and occupancy measurement.
    """

    def __init__(
        self,
        region_id: str,
        name: str,
        polygon: List[List[int]],
        moderate_thresh: int = 8,
        high_thresh: int = 15,
        critical_thresh: int = 25,
        **kwargs
    ):
        self.region_id = region_id
        self.name = name
        self.polygon = np.array(polygon, dtype=np.int32)
        self.moderate_thresh = kwargs.get("moderate", moderate_thresh)
        self.high_thresh = kwargs.get("high", high_thresh)
        self.critical_thresh = kwargs.get("critical", critical_thresh)
        self.current_count: int = 0
        self.current_density: float = 0.0  # count per 10,000 pixels
        self.active_track_ids: Set[int] = set()

        # Compute geometric area of polygon
        self.area_pixels = max(1.0, float(abs(cv2.contourArea(self.polygon))))

    def contains_point(self, pt: Tuple[int, int]) -> bool:
        """Tests whether a 2D point (x, y) falls inside the ROI polygon."""
        dist = cv2.pointPolygonTest(self.polygon, (float(pt[0]), float(pt[1])), False)
        return dist >= 0

    def update(self, tracks: List[Any], detections: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Calculates occupancy within this ROI using bottom-center (feet position)
        or bounding box center.
        """
        self.active_track_ids.clear()
        
        # Test tracks
        for track in tracks:
            # Use bottom center (feet) for best ground plane representation
            x1, y1, x2, y2 = track.bbox
            feet_pt = (int((x1 + x2) / 2), y2)
            if self.contains_point(feet_pt):
                self.active_track_ids.add(track.track_id)

        self.current_count = len(self.active_track_ids)
        # Normalized crowd density: count per 10,000 px^2
        self.current_density = round((self.current_count / self.area_pixels) * 10000.0, 3)

        status = "normal"
        if self.current_count >= self.critical_thresh:
            status = "critical"
        elif self.current_count >= self.high_thresh:
            status = "high"
        elif self.current_count >= self.moderate_thresh:
            status = "moderate"

        return {
            "region_id": self.region_id,
            "name": self.name,
            "count": self.current_count,
            "density_per_10k_px": self.current_density,
            "status": status,
            "area_pixels": int(self.area_pixels)
        }

    def draw(self, frame: np.ndarray) -> np.ndarray:
        """Renders ROI polygon with semi-transparent fill and status color."""
        overlay = frame.copy()
        
        color = (0, 200, 0)  # Normal green
        if self.current_count >= self.critical_thresh:
            color = (0, 0, 255)  # Red
        elif self.current_count >= self.high_thresh:
            color = (0, 140, 255)  # Orange
        elif self.current_count >= self.moderate_thresh:
            color = (0, 255, 255)  # Yellow

        cv2.fillPoly(overlay, [self.polygon], color)
        # Blend overlay
        cv2.addWeighted(overlay, 0.22, frame, 0.78, 0, frame)
        cv2.polylines(frame, [self.polygon], True, color, 2)

        # Label centroid
        M = cv2.moments(self.polygon)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
        else:
            cx, cy = int(self.polygon[0][0]), int(self.polygon[0][1])

        label = f"{self.name}: {self.current_count} ({self.current_density:.2f}/10k px)"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
        cv2.rectangle(frame, (cx - 4, cy - th - 4), (cx + tw + 4, cy + 4), (0, 0, 0), -1)
        cv2.putText(frame, label, (cx, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)
        return frame


class CrowdCounter:
    """
    Centralized People Counting and Region Occupancy Manager.
    Guarantees strict semantic separation between:
    - Frame detection count (N_det)
    - Active tracked count (N_active)
    - Cumulative unique track count (N_unique)
    - Line-crossing counts (N_in, N_out, net)
    - Region occupancy counts (N_roi)
    """

    def __init__(self):
        self.lines: Dict[str, LineCrossingDetector] = {}
        self.regions: Dict[str, RegionOfInterest] = {}

    def add_line(self, line_id: str, start_pt: Tuple[int, int], end_pt: Tuple[int, int], name: str = "Line"):
        self.lines[line_id] = LineCrossingDetector(line_id, start_pt, end_pt, name)

    def add_region(self, region_id: str, name: str, polygon: List[List[int]],
                   moderate: int = 8, high: int = 15, critical: int = 25):
        self.regions[region_id] = RegionOfInterest(region_id, name, polygon, moderate, high, critical)

    def reset(self):
        for line in self.lines.values():
            line.reset()

    def update(
        self,
        detections: List[Dict[str, Any]],
        active_tracks: List[Any],
        cumulative_unique_count: int
    ) -> Dict[str, Any]:
        """
        Processes current frame and produces a validated snapshot of all counting metrics.
        """
        frame_det_count = len(detections)
        active_track_count = len(active_tracks)

        line_results = {}
        total_in = 0
        total_out = 0
        for lid, line in self.lines.items():
            res = line.update(active_tracks)
            line_results[lid] = res
            total_in += res["count_in"]
            total_out += res["count_out"]

        region_results = {}
        for rid, region in self.regions.items():
            region_results[rid] = region.update(active_tracks, detections)

        return {
            "frame_detection_count": frame_det_count,
            "active_tracked_count": active_track_count,
            "cumulative_unique_count": cumulative_unique_count,
            "lines": line_results,
            "regions": region_results,
            "total_line_in": total_in,
            "total_line_out": total_out,
            "total_line_net": total_in - total_out
        }

    def draw_overlays(self, frame: np.ndarray) -> np.ndarray:
        """Renders regions and lines onto the frame."""
        annotated = frame.copy()
        for region in self.regions.values():
            annotated = region.draw(annotated)
        for line in self.lines.values():
            annotated = line.draw(annotated)
        return annotated
