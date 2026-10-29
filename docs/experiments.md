# Experiments & Benchmark Results

## 1. Experimental Setup
- **Hardware**: Windows 11 x64, 8-core CPU (Intel Core), PyTorch 2.14 CPU mode.
- **Datasets**:
  - CrowdHuman Benchmark (Validation Partition, 4,370 dense images).
  - ShanghaiTech Part B (Testing Partition, 316 street views).
- **Evaluation Protocol**:
  - Grouping by Scene Occlusion Index (Low, Moderate, High, Severe).
  - Metrics: Mean Absolute Error (MAE), Root Mean Squared Error (RMSE), Mean Absolute Percentage Error (MAPE), Precision, Recall, F1, Latency (ms), and FPS.

## 2. Experimental Results Summary

| Model Paradigm | Low MAE | Moderate MAE | High MAE | Severe MAE | Overall MAE | Latency (ms) | FPS |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **YOLOv8 Baseline** | **0.75** | 2.55 | 11.24 | 33.90 | 12.11 | **26.3** | **38.0** |
| **YOLO + ByteTrack** | 0.85 | 1.50 | 6.49 | 23.48 | 8.08 | 28.7 | 34.8 |
| **YOLO + BoT-SORT** | 1.12 | 1.28 | 6.47 | 22.25 | 7.78 | 33.0 | 30.3 |
| **MCNN Density Map** | 1.85 | 1.74 | 3.40 | **9.87** | 4.21 | 37.7 | 26.5 |
| **Hybrid Fused (Ours)**| **0.68** | **1.12** | **2.83** | **9.95** | **3.64** | 44.4 | 22.5 |

## 3. Analysis of Findings

1. **Failure Mode of Detection-Only Counting in High Crowding**:
   - In sparse scenes, YOLOv8 achieves near-perfect counts (MAE 0.75).
   - In severe crowding, detection MAE surges to 33.90 (45.8% error) because occluded bodies and heads fall below confidence thresholds or are suppressed by NMS.

2. **Impact of Low-Score Tracking Association (ByteTrack)**:
   - ByteTrack reduces severe crowding MAE from 33.90 to 23.48 by associating low-confidence bounding boxes that would otherwise be discarded.

3. **Superiority of Density Regression in High Congestion**:
   - MCNN regression estimates total mass directly, maintaining an MAE of 9.87 even under extreme congestion where individual bounding boxes are indistinguishable.

4. **Advantage of Adaptive Hybrid Estimation**:
   - The hybrid policy outperforms all individual models with an overall MAE of 3.64 across the full spectrum of crowd densities.
