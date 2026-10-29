import os
import argparse
import logging
import torch

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("train_detector")

def train_yolo(
    data_yaml: str = "datasets/processed/crowdhuman_yolo/data.yaml",
    base_model: str = "yolov8n.pt",
    epochs: int = 50,
    batch_size: int = 8,
    img_size: int = 640,
    device: str = "cpu",
    output_weights: str = "models/detection/crowdhuman_yolov8.pt"
):
    """
    Fine-tunes YOLO for robust person detection in dense, occluded crowd scenes.
    """
    if YOLO is None:
        logger.error("Ultralytics library is not installed.")
        return

    if not os.path.exists(data_yaml):
        logger.error(f"Dataset config '{data_yaml}' not found. Run scripts/prepare_dataset.py first.")
        return

    # Check device
    actual_device = "cuda" if (device == "cuda" and torch.cuda.is_available()) else "cpu"
    logger.info(f"Initializing YOLO fine-tuning on device: {actual_device}")
    logger.info(f"Base model: {base_model} | Epochs: {epochs} | Batch size: {batch_size}")

    model = YOLO(base_model)

    # Train
    results = model.train(
        data=data_yaml,
        epochs=epochs,
        batch=batch_size,
        imgsz=img_size,
        device=actual_device,
        project="outputs/train_detector",
        name="crowdhuman_run",
        exist_ok=True,
        save=True
    )

    # Copy best weights to models/detection
    best_weights = "outputs/train_detector/crowdhuman_run/weights/best.pt"
    if os.path.exists(best_weights):
        os.makedirs(os.path.dirname(os.path.abspath(output_weights)), exist_ok=True)
        import shutil
        shutil.copy(best_weights, output_weights)
        logger.info(f"Trained model checkpoint saved to: {output_weights}")
    else:
        logger.info("Training complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train YOLO detector on CrowdHuman")
    parser.add_argument("--data", default="datasets/processed/crowdhuman_yolo/data.yaml")
    parser.add_argument("--weights", default="yolov8n.pt")
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--img", type=int, default=640)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--output", default="models/detection/crowdhuman_yolov8.pt")
    args = parser.parse_args()

    train_yolo(
        data_yaml=args.data,
        base_model=args.weights,
        epochs=args.epochs,
        batch_size=args.batch,
        img_size=args.img,
        device=args.device,
        output_weights=args.output
    )
