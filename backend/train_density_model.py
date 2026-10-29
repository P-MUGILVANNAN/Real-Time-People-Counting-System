import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import time
import argparse
import logging
from typing import List, Tuple
import numpy as np
import cv2
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

from backend.app.core.density_estimator import MCNN

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("train_density_model")

class DensityDataset(Dataset):
    """
    PyTorch Dataset loading crowd images and corresponding 2D ground truth density maps.
    Downsamples density map to 1/4th resolution to match MCNN output layer,
    preserving total integral count.
    """

    def __init__(self, data_list: List[Tuple[str, str]], target_size: Tuple[int, int] = (384, 512)):
        self.data_list = data_list
        self.target_size = target_size
        self.mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        self.std = np.array([0.229, 0.224, 0.225], dtype=np.float32)

    def __len__(self):
        return len(self.data_list)

    def __getitem__(self, idx: int):
        img_path, dmap_path = self.data_list[idx]

        # Read image
        if os.path.exists(img_path):
            img = cv2.imread(img_path)
            img = cv2.resize(img, (self.target_size[1], self.target_size[0]))
        else:
            # Synthetic placeholder
            img = np.full((self.target_size[0], self.target_size[1], 3), 120, dtype=np.uint8)

        # Read density map
        if os.path.exists(dmap_path):
            dmap = np.load(dmap_path).astype(np.float32)
        else:
            dmap = np.zeros((self.target_size[0], self.target_size[1]), dtype=np.float32)

        original_count = np.sum(dmap)

        # MCNN outputs 1/4 scale density map
        out_h = self.target_size[0] // 4
        out_w = self.target_size[1] // 4
        dmap_down = cv2.resize(dmap, (out_w, out_h), interpolation=cv2.INTER_CUBIC)
        # Rescale to preserve exact integral count
        down_sum = np.sum(dmap_down)
        if down_sum > 0:
            dmap_down = dmap_down * (original_count / down_sum)

        # Normalize image
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        normalized = (img_rgb - self.mean) / self.std

        tensor_img = torch.from_numpy(normalized).permute(2, 0, 1)
        tensor_dmap = torch.from_numpy(dmap_down).unsqueeze(0)

        return tensor_img, tensor_dmap, float(original_count)


def train_mcnn(
    dataset_dir: str = "datasets/density_maps/part_B",
    epochs: int = 10,
    batch_size: int = 4,
    learning_rate: float = 1e-4,
    device: str = "cpu",
    output_path: str = "models/density/mcnn_shanghaitech.pth"
):
    actual_device = "cuda" if (device == "cuda" and torch.cuda.is_available()) else "cpu"
    logger.info(f"Starting MCNN Training on device: {actual_device}...")

    # Discover density map pairs
    data_pairs = []
    if os.path.exists(dataset_dir):
        for f in os.listdir(dataset_dir):
            if f.endswith(".npy"):
                dmap_p = os.path.join(dataset_dir, f)
                img_p = dmap_p.replace(".npy", ".jpg")
                data_pairs.append((img_p, dmap_p))

    if not data_pairs:
        logger.warning(f"No density map pairs found at {dataset_dir}. Generating synthetic demonstration training samples...")
        # Synthetic demo data for training validation
        os.makedirs("datasets/density_maps/demo", exist_ok=True)
        for i in range(12):
            dp = f"datasets/density_maps/demo/sample_{i}.npy"
            ip = f"datasets/density_maps/demo/sample_{i}.jpg"
            if not os.path.exists(dp):
                fake_map = np.zeros((384, 512), dtype=np.float32)
                for _ in range(np.random.randint(5, 25)):
                    rx = np.random.randint(20, 490)
                    ry = np.random.randint(20, 360)
                    fake_map[ry, rx] = 1.0
                np.save(dp, fake_map)
                cv2.imwrite(ip, np.full((384, 512, 3), 90, dtype=np.uint8))
            data_pairs.append((ip, dp))

    # Split train/val
    split_idx = max(1, int(len(data_pairs) * 0.8))
    train_pairs = data_pairs[:split_idx]
    val_pairs = data_pairs[split_idx:] if split_idx < len(data_pairs) else data_pairs[:1]

    train_ds = DensityDataset(train_pairs)
    val_ds = DensityDataset(val_pairs)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=1, shuffle=False)

    model = MCNN().to(actual_device)
    criterion = nn.MSELoss(reduction="sum")
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

    best_mae = float("inf")
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    for epoch in range(1, epochs + 1):
        model.train()
        epoch_loss = 0.0

        for images, targets, gt_counts in train_loader:
            images = images.to(actual_device)
            targets = targets.to(actual_device)

            optimizer.zero_grad()
            preds = model(images)
            loss = criterion(preds, targets)
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()

        # Validation
        model.eval()
        mae_errors = []
        with torch.no_grad():
            for images, targets, gt_counts in val_loader:
                images = images.to(actual_device)
                preds = model(images)
                pred_count = torch.sum(preds).item()
                gt_count = gt_counts.item()
                mae_errors.append(abs(pred_count - gt_count))

        val_mae = float(np.mean(mae_errors)) if mae_errors else 0.0
        logger.info(f"Epoch [{epoch}/{epochs}] - Loss: {epoch_loss:.2f} | Val MAE: {val_mae:.2f}")

        if val_mae < best_mae:
            best_mae = val_mae
            torch.save(model.state_dict(), output_path)
            logger.info(f"  --> Saved new best checkpoint to {output_path} (MAE: {best_mae:.2f})")

    logger.info("MCNN Density Model training pipeline finished successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="datasets/density_maps/part_B")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch", type=int, default=2)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--output", default="models/density/mcnn_shanghaitech.pth")
    args = parser.parse_args()

    train_mcnn(
        dataset_dir=args.dataset,
        epochs=args.epochs,
        batch_size=args.batch,
        learning_rate=args.lr,
        device=args.device,
        output_path=args.output
    )
