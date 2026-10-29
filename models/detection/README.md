# Detection Models

## Overview
This system utilizes Ultralytics YOLO (e.g. YOLOv8n, YOLOv8s, or custom fine-tuned weights on CrowdHuman) for person detection.

## Baseline Pretrained Model: YOLOv8 Nano (yolov8n.pt)
- **Source**: Ultralytics (https://github.com/ultralytics/ultralytics)
- **Architecture**: YOLOv8 (Anchor-free, decoupled head, SiLU activation)
- **Pretrained Dataset**: COCO (Common Objects in Context), filtered to Class 0 (`person`)
- **License**: AGPL-3.0 (for Ultralytics models) / Enterprise license for commercial use.
- **Acquisition**:
  The system automatically initializes or downloads the standard baseline `yolov8n.pt` into this directory upon first launch via the Ultralytics model manager, or you can place your custom weights directly as:
  `models/detection/yolov8n.pt` or `models/detection/crowdhuman_yolov8.pt`.

## CrowdHuman Fine-Tuned Model
To fine-tune YOLO on the dense CrowdHuman dataset for elevated occlusion resilience:
```powershell
python backend/train_detector.py --data datasets/processed/crowdhuman_yolo/data.yaml --epochs 50 --batch 8 --img 640
```
This produces `models/detection/crowdhuman_yolov8.pt`.
