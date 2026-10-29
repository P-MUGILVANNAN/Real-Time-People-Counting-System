# Multi-Object Tracking Models

## Tracking Algorithms Supported
1. **ByteTrack**:
   - Associates every detection box rather than just high-confidence ones.
   - Low-score detection boxes (often caused by occlusion or motion blur) are retained and matched using motion trajectory similarity (Kalman Filter) with existing tracklets.
   - Ideal for crowded scenes with substantial occlusion.

2. **BoT-SORT**:
   - Combines Kalman Filter motion modeling with Camera Motion Compensation (CMC) and optional visual appearance feature re-identification (ReID).

## Configuration
Tracker configuration files are handled through Ultralytics tracker configurations (`bytetrack.yaml` and `botsort.yaml`), with parameters exposed in `.env` and the application settings page:
- `track_high_thresh`: Threshold for first-round association.
- `track_low_thresh`: Threshold for second-round association of occluded detections.
- `new_track_thresh`: Minimum score to initiate a new track.
- `track_buffer`: Buffer duration in frames before a lost track is purged.
- `match_thresh`: IoU matching threshold for assignment.
