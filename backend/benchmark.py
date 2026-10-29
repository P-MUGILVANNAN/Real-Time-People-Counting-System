import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import time
import json
import argparse
import platform
import psutil
import numpy as np
import cv2
import torch

from backend.app.core.detector import PersonDetector
from backend.app.core.tracker import MultiObjectTracker
from backend.app.core.density_estimator import MCNN
from backend.app.core.metrics import RuntimeMetrics

def run_benchmark(
    iterations: int = 40,
    img_size: int = 640,
    device: str = "cpu",
    output_report: str = "outputs/reports/benchmark_results.json"
):
    os.makedirs(os.path.dirname(os.path.abspath(output_report)), exist_ok=True)
    actual_device = "cuda" if (device == "cuda" and torch.cuda.is_available()) else "cpu"
    print("=" * 65)
    print(f"HARDWARE RUNTIME BENCHMARK ({actual_device.upper()})")
    print("=" * 65)
    print(f"Platform: {platform.platform()}")
    print(f"CPU: {platform.processor()} ({psutil.cpu_count(logical=True)} logical cores)")
    print(f"Torch Version: {torch.__version__} | CUDA Available: {torch.cuda.is_available()}")
    print(f"Iterations: {iterations} | Resolution: {img_size}x{img_size}")
    print("-" * 65)

    # 1. Benchmark MCNN Density Model
    print("Benchmarking MCNN Density Regression Network...")
    mcnn = MCNN().to(actual_device)
    mcnn.eval()
    dummy_tensor = torch.randn(1, 3, 384, 512).to(actual_device)

    # Warmup
    for _ in range(5):
        with torch.no_grad():
            _ = mcnn(dummy_tensor)

    mcnn_times = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        with torch.no_grad():
            _ = mcnn(dummy_tensor)
        t1 = time.perf_counter()
        mcnn_times.append((t1 - t0) * 1000.0)

    mcnn_res = RuntimeMetrics.calculate(mcnn_times, device=actual_device)
    print(f"  MCNN: Mean {mcnn_res['mean_latency_ms']} ms | Median {mcnn_res['median_latency_ms']} ms | P95 {mcnn_res['p95_latency_ms']} ms | FPS: {mcnn_res['fps']}")

    # 2. Benchmark Tracker Alone
    print("Benchmarking Multi-Object Tracker Association...")
    tracker = MultiObjectTracker(tracker_type="bytetrack")
    dummy_dets = [
        {"bbox": [50 + i * 15, 60 + i * 10, 100 + i * 15, 180 + i * 10], "confidence": 0.85, "class_id": 0}
        for i in range(25)
    ]
    tracker_times = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        tracker.update_from_detections(dummy_dets)
        t1 = time.perf_counter()
        tracker_times.append((t1 - t0) * 1000.0)

    tracker_res = RuntimeMetrics.calculate(tracker_times, device=actual_device)
    print(f"  Tracker: Mean {tracker_res['mean_latency_ms']} ms | Median {tracker_res['median_latency_ms']} ms | FPS: {tracker_res['fps']}")

    # 3. Overall Pipeline Report
    report = {
        "device": actual_device,
        "iterations": iterations,
        "image_size": img_size,
        "system": {
            "platform": platform.platform(),
            "cpu": platform.processor(),
            "torch_version": torch.__version__,
            "cuda_available": torch.cuda.is_available()
        },
        "mcnn_benchmark": mcnn_res,
        "tracker_benchmark": tracker_res
    }

    with open(output_report, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("=" * 65)
    print(f"Benchmark report saved to: {output_report}")
    return report

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=30)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--output", default="outputs/reports/benchmark_results.json")
    args = parser.parse_args()
    run_benchmark(iterations=args.iterations, device=args.device, output_report=args.output)
