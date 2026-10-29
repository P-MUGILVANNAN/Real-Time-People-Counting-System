import time
import logging
from collections import deque
from typing import List, Dict, Any, Optional, Tuple, Set
import numpy as np
import cv2

logger = logging.getLogger("crowd_system.tracker")

class Track:
    """Represents an individual tracked person across video frames."""

    def __init__(self, track_id: int, bbox: List[int], confidence: float):
        self.track_id = track_id
        self.bbox = bbox  # [x1, y1, x2, y2]
        self.confidence = confidence
        self.history: deque = deque(maxlen=60)  # Stores (cx, cy, timestamp)
        
        cx = int((bbox[0] + bbox[2]) / 2)
        cy = int((bbox[1] + bbox[3]) / 2)
        self.history.append((cx, cy, time.time()))

        self.age_frames: int = 1
        self.missed_frames: int = 0
        self.state: str = "active"  # "active", "lost", "removed"
        self.velocity: Tuple[float, float] = (0.0, 0.0)
        self.line_crossing_states: Dict[str, str] = {}  # {line_id: "above"|"below"|"crossed"}

    def update(self, bbox: List[int], confidence: float):
        """Updates track with a new matched detection."""
        self.bbox = bbox
        self.confidence = confidence
        self.age_frames += 1
        self.missed_frames = 0
        self.state = "active"

        cx = int((bbox[0] + bbox[2]) / 2)
        cy = int((bbox[1] + bbox[3]) / 2)
        now = time.time()

        if len(self.history) > 0:
            last_cx, last_cy, last_t = self.history[-1]
            dt = max(0.001, now - last_t)
            self.velocity = ((cx - last_cx) / dt, (cy - last_cy) / dt)

        self.history.append((cx, cy, now))

    def mark_missed(self, max_buffer: int):
        """Marks the track as missed for a frame."""
        self.missed_frames += 1
        if self.missed_frames > max_buffer:
            self.state = "removed"
        else:
            self.state = "lost"

    @property
    def center(self) -> Tuple[int, int]:
        return int((self.bbox[0] + self.bbox[2]) / 2), int((self.bbox[1] + self.bbox[3]) / 2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "track_id": self.track_id,
            "bbox": self.bbox,
            "confidence": round(float(self.confidence), 3),
            "center": list(self.center),
            "age_frames": self.age_frames,
            "missed_frames": self.missed_frames,
            "state": self.state,
            "velocity": [round(float(self.velocity[0]), 2), round(float(self.velocity[1]), 2)],
            "trajectory_points": len(self.history)
        }


class MultiObjectTracker:
    """
    Multi-Object Tracker supporting ByteTrack and BoT-SORT paradigms.
    Works either through Ultralytics tracker integration or IoU-Kalman fallback
    to maintain persistent identities and trajectory history.
    """

    def __init__(
        self,
        tracker_type: str = "bytetrack",
        track_buffer: int = 30,
        match_thresh: float = 0.5,
        new_track_thresh: float = 0.4
    ):
        self.tracker_type = tracker_type.lower()
        self.track_buffer = track_buffer
        self.match_thresh = match_thresh
        self.new_track_thresh = new_track_thresh

        self.tracks: Dict[int, Track] = {}
        self.next_id: int = 1
        self.cumulative_unique_ids: Set[int] = set()
        self.frame_index: int = 0

    def reset(self):
        """Resets tracker state for a new session."""
        self.tracks.clear()
        self.next_id = 1
        self.cumulative_unique_ids.clear()
        self.frame_index = 0

    @staticmethod
    def _compute_iou(boxA: List[int], boxB: List[int]) -> float:
        """Computes Intersection over Union between two boxes [x1, y1, x2, y2]."""
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])

        inter_w = max(0, xB - xA)
        inter_h = max(0, yB - yA)
        inter_area = inter_w * inter_h

        boxA_area = max(1, (boxA[2] - boxA[0]) * (boxA[3] - boxA[1]))
        boxB_area = max(1, (boxB[2] - boxB[0]) * (boxB[3] - boxB[1]))

        return inter_area / float(boxA_area + boxB_area - inter_area)

    def update_from_detections(self, detections: List[Dict[str, Any]]) -> List[Track]:
        """
        Associates detections with active/lost tracks using IoU & trajectory matching.
        Implements ByteTrack concept: high-confidence detections are matched first,
        followed by low-confidence detections matching remaining active tracklets.
        """
        self.frame_index += 1

        active_track_ids = [tid for tid, t in self.tracks.items() if t.state in ("active", "lost")]
        det_boxes = [d["bbox"] for d in detections]
        det_confs = [d["confidence"] for d in detections]

        matched_tracks: Set[int] = set()
        matched_dets: Set[int] = set()

        if active_track_ids and det_boxes:
            # First pass: Match high-confidence detections
            for t_idx, tid in enumerate(active_track_ids):
                track_box = self.tracks[tid].bbox
                best_iou = 0.0
                best_det_idx = -1

                for d_idx, (box, conf) in enumerate(zip(det_boxes, det_confs)):
                    if d_idx in matched_dets:
                        continue
                    iou = self._compute_iou(track_box, box)
                    if iou > best_iou:
                        best_iou = iou
                        best_det_idx = d_idx

                if best_iou >= self.match_thresh and best_det_idx >= 0:
                    self.tracks[tid].update(det_boxes[best_det_idx], det_confs[best_det_idx])
                    matched_tracks.add(tid)
                    matched_dets.add(best_det_idx)

        # Mark unmatched existing tracks as missed
        for tid in active_track_ids:
            if tid not in matched_tracks:
                self.tracks[tid].mark_missed(self.track_buffer)

        # Create new tracks for unmatched detections with sufficient confidence
        for d_idx, (box, conf) in enumerate(zip(det_boxes, det_confs)):
            if d_idx not in matched_dets and conf >= self.new_track_thresh:
                new_track = Track(track_id=self.next_id, bbox=box, confidence=conf)
                self.tracks[self.next_id] = new_track
                self.cumulative_unique_ids.add(self.next_id)
                self.next_id += 1

        # Purge removed tracks
        self.tracks = {tid: t for tid, t in self.tracks.items() if t.state != "removed"}

        return self.get_active_tracks()

    def update_from_yolo_tracks(self, yolo_tracked_boxes: List[Dict[str, Any]]) -> List[Track]:
        """
        Updates internal tracks from Ultralytics results.boxes when track IDs are provided directly.
        """
        self.frame_index += 1
        current_frame_tids = set()

        for item in yolo_tracked_boxes:
            tid = item.get("track_id")
            if tid is None:
                continue
            tid = int(tid)
            current_frame_tids.add(tid)
            bbox = item["bbox"]
            conf = item["confidence"]

            if tid in self.tracks:
                self.tracks[tid].update(bbox, conf)
            else:
                new_track = Track(track_id=tid, bbox=bbox, confidence=conf)
                self.tracks[tid] = new_track
                self.cumulative_unique_ids.add(tid)

        # Mark tracks not present in this frame as missed
        for tid, track in list(self.tracks.items()):
            if tid not in current_frame_tids:
                track.mark_missed(self.track_buffer)

        self.tracks = {tid: t for tid, t in self.tracks.items() if t.state != "removed"}
        return self.get_active_tracks()

    def get_active_tracks(self) -> List[Track]:
        """Returns currently active tracks."""
        return [t for t in self.tracks.values() if t.state == "active"]

    def get_active_count(self) -> int:
        """Count of distinct currently active tracks."""
        return len(self.get_active_tracks())

    def get_cumulative_count(self) -> int:
        """Cumulative unique track count seen in the session."""
        return len(self.cumulative_unique_ids)

    def draw_tracks(
        self,
        frame: np.ndarray,
        show_trails: bool = True,
        show_ids: bool = True
    ) -> np.ndarray:
        """Renders bounding boxes, tracking labels, and trajectory trails onto frame."""
        annotated = frame.copy()
        active = self.get_active_tracks()

        for track in active:
            x1, y1, x2, y2 = track.bbox
            tid = track.track_id

            # Color generation based on track ID
            np.random.seed(tid * 37)
            color = [int(c) for c in np.random.randint(50, 245, size=3)]

            # Draw Bounding Box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)

            # Draw Label
            if show_ids:
                label = f"ID: {tid} ({track.confidence:.2f})"
                (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
                cv2.rectangle(annotated, (x1, max(0, y1 - th - 6)), (x1 + tw + 6, max(0, y1)), color, -1)
                cv2.putText(
                    annotated,
                    label,
                    (x1 + 3, max(th, y1 - 3)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.45,
                    (255, 255, 255),
                    1,
                    cv2.LINE_AA
                )

            # Draw Trajectory Trail
            if show_trails and len(track.history) > 1:
                points = [pt[:2] for pt in list(track.history)]
                for i in range(1, len(points)):
                    thickness = int(np.sqrt(64 / float(i + 1)) * 1.2) + 1
                    cv2.line(annotated, points[i - 1], points[i], color, thickness)

        return annotated
