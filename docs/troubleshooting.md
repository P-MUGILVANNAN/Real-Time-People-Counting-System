# Troubleshooting Guide

## 1. Camera Access Issues
- **Error**: `Unable to open camera index 0.`
- **Remedies**:
  1. Verify privacy permissions in Windows Settings: **Settings > Privacy & security > Camera > Let desktop apps access your camera**.
  2. If using an external USB camera, test Index 1 or 2 in the Live Monitoring panel.
  3. Ensure no other application (e.g. Zoom, Teams, Skype) is currently locking the camera.
  4. Use the built-in sample video (`crowd_sample.mp4`) to test video inference without requiring a physical camera.

## 2. CUDA / GPU Acceleration
- **Behavior**: System defaults to `cpu` mode.
- **Cause**: PyTorch CPU-only build is active or NVIDIA drivers are not detected.
- **Remedies**:
  1. The system fully supports CPU execution and runs cleanly on standard multi-core processors.
  2. For NVIDIA GPU acceleration, install the CUDA-enabled PyTorch wheel:
     ```powershell
     pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
     ```
  3. Verify with `python -c "import torch; print(torch.cuda.is_available())"`.
  4. Update `.env` to set `DEVICE=cuda`.

## 3. Density Model Weights
- **Status**: Density model reports `weights_missing` or `untrained`.
- **Explanation**: The system does not invent fabricated density numbers when neural network weights are absent.
- **Remedies**:
  1. To train custom MCNN weights on ShanghaiTech:
     ```powershell
     python backend/train_density_model.py --dataset datasets/density_maps/part_B --epochs 10 --output models/density/mcnn_shanghaitech.pth
     ```
  2. In demonstration mode without external weights, the system automatically uses the verified detection-based density estimator and spatial Gaussian surface.

## 4. Port Conflicts
- **Error**: `[WinError 10048] Only one usage of each socket address is normally permitted.`
- **Remedies**:
  1. Check if an earlier uvicorn process is still bound to port 8000:
     ```powershell
     Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process -Force
     ```
  2. Alternatively, specify another port in `.env` (e.g. `PORT=8001`).
