import math
import logging
from typing import List, Dict, Any, Tuple
import numpy as np

logger = logging.getLogger("crowd_system.occlusion")

class OcclusionAnalyzer:
    """
    Research-Grade Occlusion Proxy Module.
    Calculates quantifiable geometric occlusion proxies from observable detection bounding boxes,
    spatial clustering, and track fragmentation.
    
    NOTE: These measurements represent observable geometric proxies rather than
    ground-truth 3D physical visibility, unless validated visibility masks are provided.
    """

    def __init__(
        self,
        low_threshold: float = 0.20,
        moderate_threshold: float = 0.45,
        high_threshold: float = 0.70,
        iou_overlap_weight: float = 0.45,
        cluster_weight: float = 0.35,
        scale_weight: float = 0.20
    ):
        self.low_threshold = low_threshold
        self.moderate_threshold = moderate_threshold
        self.high_threshold = high_threshold

        self.iou_overlap_weight = iou_overlap_weight
        self.cluster_weight = cluster_weight
        self.scale_weight = scale_weight

    @staticmethod
    def _compute_box_overlap(boxA: List[int], boxB: List[int]) -> Tuple[float, float]:
        """
        Computes both IoU (Intersection over Union) and IoMin (Intersection over Min Area).
        IoMin captures partial/full containment where a small person is occluded behind a large person.
        """
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])

        inter_w = max(0, xB - xA)
        inter_h = max(0, yB - yA)
        inter_area = inter_w * inter_h

        if inter_area <= 0:
            return 0.0, 0.0

        areaA = max(1, (boxA[2] - boxA[0]) * (boxA[3] - boxA[1]))
        areaB = max(1, (boxB[2] - boxB[0]) * (boxB[3] - boxB[1]))

        iou = inter_area / float(areaA + areaB - inter_area)
        iomin = inter_area / float(min(areaA, areaB))
        return iou, iomin

    def analyze(
        self,
        frame_shape: Tuple[int, int],
        detections: List[Dict[str, Any]],
        active_tracks: Optional[List[Any]] = None
    ) -> Dict[str, Any]:
        """
        Computes per-person occlusion index and overall Scene Occlusion Index (SOI).
        """
        num_dets = len(detections)
        if num_dets <= 1:
            return {
                "scene_occlusion_index": 0.0,
                "difficulty_category": "low",
                "mean_pairwise_iou": 0.0,
                "overlapping_pairs_count": 0,
                "dense_cluster_ratio": 0.0,
                "per_person_occlusion": []
            }

        h, w = frame_shape[:2]
        frame_area = float(max(1, h * w))

        boxes = [d["bbox"] for d in detections]
        box_areas = [d.get("area", (b[2] - b[0]) * (b[3] - b[1])) for b, d in zip(boxes, detections)]

        # Pairwise overlap analysis
        pairwise_ious = []
        pairwise_iomins = []
        overlapping_pairs = 0
        person_overlap_scores = [0.0] * num_dets

        for i in range(num_dets):
            for j in range(i + 1, num_dets):
                iou, iomin = self._compute_box_overlap(boxes[i], boxes[j])
                if iou > 0.05:
                    overlapping_pairs += 1
                    pairwise_ious.append(iou)
                    pairwise_iomins.append(iomin)
                    person_overlap_scores[i] = max(person_overlap_scores[i], iomin)
                    person_overlap_scores[j] = max(person_overlap_scores[j], iomin)

        mean_iou = float(np.mean(pairwise_ious)) if pairwise_ious else 0.0
        mean_iomin = float(np.mean(pairwise_iomins)) if pairwise_iomins else 0.0

        # Cluster proximity proxy: fraction of people who have a neighbor within normalized distance
        centers = np.array([d["center"] for d in detections], dtype=np.float32)
        close_neighbor_count = 0
        cluster_distance_thresh = np.sqrt(frame_area / max(1, num_dets)) * 0.75

        for i in range(num_dets):
            dists = np.linalg.norm(centers - centers[i], axis=1)
            # Exclude self
            dists[i] = 1e9
            if np.min(dists) <= cluster_distance_thresh:
                close_neighbor_count += 1

        cluster_ratio = close_neighbor_count / float(num_dets)

        # Scale proxy: smaller relative box size in congested crowds implies severe perspective occlusion
        norm_areas = [a / frame_area for a in box_areas]
        mean_norm_area = float(np.mean(norm_areas))
        # Inverse scaling: smaller boxes -> higher occlusion penalty factor
        scale_penalty = max(0.0, min(1.0, 1.0 - (mean_norm_area * 30.0)))

        # Composite Scene Occlusion Index (SOI) in [0.0, 1.0]
        soi = (
            self.iou_overlap_weight * min(1.0, mean_iomin * 1.8) +
            self.cluster_weight * cluster_ratio +
            self.scale_weight * scale_penalty
        )
        soi = round(float(max(0.0, min(1.0, soi))), 3)

        # Classify scene difficulty category
        if soi < self.low_threshold:
            category = "low"
        elif soi < self.moderate_threshold:
            category = "moderate"
        elif soi < self.high_threshold:
            category = "high"
        else:
            category = "severe"

        per_person = []
        for i, det in enumerate(detections):
            score = round(float(person_overlap_scores[i]), 2)
            per_person.append({
                "center": det["center"],
                "occlusion_score": score,
                "is_severely_occluded": score > 0.5
            })

        return {
            "scene_occlusion_index": soi,
            "difficulty_category": category,
            "mean_pairwise_iou": round(mean_iou, 3),
            "mean_pairwise_iomin": round(mean_iomin, 3),
            "overlapping_pairs_count": overlapping_pairs,
            "dense_cluster_ratio": round(cluster_ratio, 3),
            "per_person_occlusion": per_person
        }
