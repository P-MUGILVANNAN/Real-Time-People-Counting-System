# Density Estimation Models

## Overview
Density estimation uses regression neural networks (Multi-column CNN - MCNN or Dilated CSRNet) to map input crowd images directly to continuous 2D spatial crowd-density distributions:

$$D(x, y) \ge 0$$
$$\text{Total Crowd Count} = \iint D(x, y) \, dx \, dy$$

## Model Architectures
1. **MCNN (Multi-Column Convolutional Neural Network)**:
   - 3 parallel columns with varying filter kernel sizes (large 9x9, medium 7x7, small 5x5) to capture multi-scale crowd heads under perspective distortion.
   - Outputs a downsampled density map (1/4th resolution) which integrates to crowd count.
2. **CSRNet (Congested Scene Recognition Network)**:
   - VGG-16 front-end feature extractor with dilated convolutional layers in the back-end to enlarge the receptive field without losing spatial resolution.

## Status Handling
If weights are not found at `models/density/mcnn_shanghaitech.pth`:
- The system gracefully reports `status: "untrained"` or `"missing_weights"`.
- It does **not** generate fake density numbers.
- In demonstration mode without external weights, a calibrated spatial Gaussian kernel adapter is available to compute density distribution maps from verified detections, while the density neural network adapter provides real forward-pass metrics when trained weights are loaded.

## Training Instructions
Train on ShanghaiTech Part A or Part B:
```powershell
python backend/train_density_model.py --dataset shanghaitech --part B --epochs 80 --batch 4 --lr 1e-4 --output models/density/mcnn_shanghaitech.pth
```
