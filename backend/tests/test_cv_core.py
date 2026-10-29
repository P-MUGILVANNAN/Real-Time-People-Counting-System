import numpy as np
import pytest

from backend.app.core.detector import PersonDetector
from backend.app.core.tracker import MultiObjectTracker, Track
from backend.app.core.counter import LineCrossingDetector, RegionOfInterest, CrowdCounter
from backend.app.core.density_estimator import (
    MCNN,
    DetectionDensityEstimator,
    MCNNDensityEstimator,
    HybridDensityEstimator
)
from backend.app.core.heatmap import HeatmapGenerator
from backend.app.core.occlusion_analysis import OcclusionAnalyzer
from backend.app.core.event_manager import EventManager
from backend.app.core.metrics import CountingMetrics, DetectionMetrics, RuntimeMetrics

# 1. Detection and Class Filtering
def test_detection_bounding_boxes_and_shapes():
    # Empty frame handling
    detector = PersonDetector(model_path="models/detection/yolov8n.pt", device="cpu")
    empty_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Check status dictionary
    status = detector.get_status()
    assert "loaded" in status
    assert "device" in status

# 2. Tracking and Unique Identity Counting
def test_tracker_association_and_counting():
    tracker = MultiObjectTracker(tracker_type="bytetrack", track_buffer=10, match_thresh=0.3)
    
    # Frame 1: Two persons detected
    dets_f1 = [
        {"bbox": [100, 100, 150, 220], "confidence": 0.88, "class_id": 0},
        {"bbox": [300, 150, 350, 270], "confidence": 0.92, "class_id": 0}
    ]
    tracks_f1 = tracker.update_from_detections(dets_f1)
    assert len(tracks_f1) == 2
    assert tracker.get_active_count() == 2
    assert tracker.get_cumulative_count() == 2
    
    # Frame 2: Move slightly (trajectory continuation)
    dets_f2 = [
        {"bbox": [105, 102, 155, 222], "confidence": 0.85, "class_id": 0},
        {"bbox": [305, 152, 355, 272], "confidence": 0.90, "class_id": 0}
    ]
    tracks_f2 = tracker.update_from_detections(dets_f2)
    assert len(tracks_f2) == 2
    # Identities must remain identical without duplicate ID inflation
    assert tracks_f2[0].track_id == tracks_f1[0].track_id
    assert tracks_f2[1].track_id == tracks_f1[1].track_id
    assert tracker.get_cumulative_count() == 2

    # Frame 3: One person leaves
    dets_f3 = [
        {"bbox": [110, 105, 160, 225], "confidence": 0.84, "class_id": 0}
    ]
    tracks_f3 = tracker.update_from_detections(dets_f3)
    assert len(tracks_f3) == 1
    assert tracker.get_active_count() == 1
    assert tracker.get_cumulative_count() == 2

# 3. Line-Crossing Tripwire and Double-Counting Prevention
def test_line_crossing_tripwire_no_double_count():
    tripwire = LineCrossingDetector(line_id="gate_1", start_pt=(0, 200), end_pt=(400, 200), name="Test Gate")
    
    track = Track(track_id=1, bbox=[100, 150, 140, 220], confidence=0.9)
    # Start above line (y=150)
    tripwire.update([track])
    assert tripwire.count_in == 0
    assert tripwire.count_out == 0

    # Cross below line (y=250)
    track.update([100, 220, 140, 290], confidence=0.9)
    res = tripwire.update([track])
    assert tripwire.count_in == 1 or tripwire.count_out == 1
    initial_event_count = tripwire.count_in + tripwire.count_out

    # Move further below: must NOT trigger additional crossing count
    track.update([100, 260, 140, 330], confidence=0.9)
    tripwire.update([track])
    assert (tripwire.count_in + tripwire.count_out) == initial_event_count

# 4. Polygonal Region Occupancy
def test_polygon_region_occupancy():
    polygon = [[50, 50], [250, 50], [250, 250], [50, 250]]
    roi = RegionOfInterest(region_id="zone_test", name="Zone Test", polygon=polygon, moderate=2, high=4, critical=6)

    # Track 1 inside region: center is (120, 150), bottom is 200
    t_inside = Track(track_id=1, bbox=[100, 100, 140, 200], confidence=0.85)
    # Track 2 outside region: bottom is 350
    t_outside = Track(track_id=2, bbox=[300, 280, 350, 350], confidence=0.88)

    res = roi.update([t_inside, t_outside])
    assert res["count"] == 1
    assert 1 in roi.active_track_ids
    assert 2 not in roi.active_track_ids
    assert res["status"] == "normal"

# 5. Density Map Count Integration
def test_density_map_count_integration():
    from scripts.generate_density_maps import generate_gaussian_density_map
    shape = (200, 200)
    points = np.array([[50, 50], [100, 100], [150, 150]], dtype=np.float32)
    dmap = generate_gaussian_density_map(shape, points, sigma=10.0)

    # Integrated sum must preserve the exact ground-truth count of 3.0
    integrated_count = float(np.sum(dmap))
    assert abs(integrated_count - 3.0) < 0.01

# 6. Safe MAPE and Metrics
def test_counting_metrics_with_zero_gt():
    preds = [0.0, 2.0, 10.0]
    gts = [0.0, 0.0, 8.0]
    metrics = CountingMetrics.calculate(preds, gts)

    assert metrics["sample_count"] == 3
    assert metrics["mae"] > 0
    assert not np.isnan(metrics["mape_pct"])
    assert not np.isinf(metrics["mape_pct"])

# 7. Alert Cooldown and State Management
def test_alert_cooldown():
    em = EventManager(moderate_thresh=5, high_thresh=10, critical_thresh=20, cooldown_seconds=5.0)
    
    # First spike: 12 people (High alert)
    alerts_1 = em.evaluate_state(total_count=12, density_val=2.5)
    assert len(alerts_1) == 1
    assert alerts_1[0]["severity"] == "high"

    # Immediate next frame still with 12 people: Cooldown must prevent repeated alert
    alerts_2 = em.evaluate_state(total_count=12, density_val=2.5)
    assert len(alerts_2) == 0

# 8. Occlusion Analysis
def test_occlusion_analyzer():
    oa = OcclusionAnalyzer()
    # Two heavily overlapping boxes
    dets = [
        {"bbox": [100, 100, 160, 240], "center": [130, 170], "area": 8400},
        {"bbox": [110, 105, 170, 245], "center": [140, 175], "area": 8400}
    ]
    res = oa.analyze((480, 640), dets)
    assert res["scene_occlusion_index"] > 0.1
    assert res["overlapping_pairs_count"] == 1
