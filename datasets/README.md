# Datasets & Preparation Guide

## 1. CrowdHuman Dataset
- **Purpose**: High-density human detection, evaluation under severe occlusion.
- **Reference**: Shao et al., "CrowdHuman: A Benchmark for Detecting Human in a Crowd", arXiv:1805.00123.
- **Official Source**: [CrowdHuman Benchmark](https://www.crowdhuman.org/)
- **Structure**:
  - `CrowdHuman_train01.zip`, `CrowdHuman_train02.zip`, `CrowdHuman_train03.zip`, `CrowdHuman_val.zip`
  - Annotations: `annotation_train.odgt`, `annotation_val.odgt`
  - Format: ODGT JSON lines containing `fbox` (full body), `vbox` (visible body), and `hbox` (head).
- **Processing**:
  Use `scripts/prepare_dataset.py --dataset crowdhuman --input datasets/raw/crowdhuman --output datasets/processed/crowdhuman_yolo` to convert ODGT format to YOLO standard format with train/val splits and `data.yaml`.

## 2. ShanghaiTech Dataset (Part A & Part B)
- **Purpose**: Point-annotated crowd counting and continuous density map regression.
- **Reference**: Zhang et al., "Single-Image Crowd Counting via Multi-Column Convolutional Neural Network", CVPR 2016.
- **Structure**:
  - `part_A/`: Highly congested scenes (482 images, total 241,667 annotations).
  - `part_B/`: Sparse crowd scenes from metropolitan Shanghai street views (716 images, 88,488 annotations).
  - Ground truth: `.mat` files containing point coordinate matrices `image_info{1,1}{1,1}{1,1}` representing head positions.
- **Processing**:
  Use `scripts/generate_density_maps.py --dataset shanghaitech --part B --raw datasets/raw/ShanghaiTech --output datasets/density_maps/part_B`
  to generate normalized 2D Gaussian density maps where $\sum_{x,y} D(x,y) = N_{people}$.

## Demonstration / Sample Mode
The system contains a built-in sample data generator:
```powershell
python scripts/generate_sample_video.py --output datasets/sample/crowd_sample.mp4 --num-people 15 --duration-sec 10
```
This generates a synthetic crowd test video with known trajectories, occlusions, and bounding boxes for zero-download instant verification!
