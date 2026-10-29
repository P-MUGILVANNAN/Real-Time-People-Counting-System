import os
import json
import argparse
import random
from typing import Dict, Any, List
import yaml

def convert_odgt_to_yolo(
    odgt_file: str,
    images_dir: str,
    output_images_dir: str,
    output_labels_dir: str,
    box_type: str = "fbox",
    max_samples: Optional[int] = None
):
    """
    Parses CrowdHuman ODGT annotation file and writes standard YOLO label text files.
    Format per line: 0 <x_center> <y_center> <width> <height> (normalized to [0, 1]).
    """
    os.makedirs(output_images_dir, exist_ok=True)
    os.makedirs(output_labels_dir, exist_ok=True)

    if not os.path.exists(odgt_file):
        print(f"Error: ODGT annotation file not found: {odgt_file}")
        return 0, 0

    count_images = 0
    total_boxes = 0

    with open(odgt_file, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            data = json.loads(line.strip())
            img_id = data["ID"]
            gtboxes = data.get("gtboxes", [])

            # We need image dimensions to normalize coordinates
            # Default CrowdHuman resolution if image not yet downloaded:
            img_w = data.get("width", 1000)
            img_h = data.get("height", 800)

            label_filename = f"{img_id}.txt"
            label_path = os.path.join(output_labels_dir, label_filename)

            yolo_lines = []
            for box_obj in gtboxes:
                if box_obj.get("tag") != "person":
                    continue
                # Ignore extra annotations if flagged
                extra = box_obj.get("extra", {})
                if extra.get("ignore", 0) == 1:
                    continue

                # Select desired box: 'fbox' (full-body), 'vbox' (visible-body), or 'hbox' (head)
                coords = box_obj.get(box_type, box_obj.get("fbox"))
                if not coords or len(coords) < 4:
                    continue

                x, y, w, h = coords
                if w <= 0 or h <= 0:
                    continue

                # Convert top-left (x, y, w, h) to normalized center (cx, cy, nw, nh)
                cx = (x + w / 2.0) / float(img_w)
                cy = (y + h / 2.0) / float(img_h)
                nw = w / float(img_w)
                nh = h / float(img_h)

                # Clamp values to [0, 1]
                cx = max(0.0, min(1.0, cx))
                cy = max(0.0, min(1.0, cy))
                nw = max(0.0, min(1.0, nw))
                nh = max(0.0, min(1.0, nh))

                yolo_lines.append(f"0 {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}")
                total_boxes += 1

            with open(label_path, "w", encoding="utf-8") as lf:
                lf.write("\n".join(yolo_lines) + "\n")

            count_images += 1
            if max_samples and count_images >= max_samples:
                break

    return count_images, total_boxes


def prepare_crowdhuman(
    raw_dir: str = "datasets/raw/crowdhuman",
    output_dir: str = "datasets/processed/crowdhuman_yolo",
    box_type: str = "fbox",
    val_split: float = 0.2,
    seed: int = 42
):
    random.seed(seed)
    print(f"Preparing CrowdHuman dataset using box type '{box_type}'...")

    train_odgt = os.path.join(raw_dir, "annotation_train.odgt")
    val_odgt = os.path.join(raw_dir, "annotation_val.odgt")

    if not os.path.exists(train_odgt):
        print(f"CrowdHuman raw data not found at {raw_dir}.")
        print("Creating mock metadata template for demonstration pipeline...")
        # Write template data.yaml
        os.makedirs(output_dir, exist_ok=True)
        data_yaml = {
            "path": os.path.abspath(output_dir),
            "train": "images/train",
            "val": "images/val",
            "names": {0: "person"}
        }
        yaml_path = os.path.join(output_dir, "data.yaml")
        with open(yaml_path, "w") as yf:
            yaml.dump(data_yaml, yf)
        print(f"Generated YAML template: {yaml_path}")
        return

    # Process train
    train_imgs, train_boxes = convert_odgt_to_yolo(
        train_odgt,
        images_dir=os.path.join(raw_dir, "Images"),
        output_images_dir=os.path.join(output_dir, "images", "train"),
        output_labels_dir=os.path.join(output_dir, "labels", "train"),
        box_type=box_type
    )

    # Process val
    val_imgs, val_boxes = convert_odgt_to_yolo(
        val_odgt,
        images_dir=os.path.join(raw_dir, "Images"),
        output_images_dir=os.path.join(output_dir, "images", "val"),
        output_labels_dir=os.path.join(output_dir, "labels", "val"),
        box_type=box_type
    )

    # Generate data.yaml
    data_yaml = {
        "path": os.path.abspath(output_dir),
        "train": "images/train",
        "val": "images/val",
        "nc": 1,
        "names": {0: "person"}
    }
    yaml_path = os.path.join(output_dir, "data.yaml")
    with open(yaml_path, "w") as yf:
        yaml.dump(data_yaml, yf)

    print(f"Dataset preparation complete:")
    print(f"  Train: {train_imgs} images, {train_boxes} boxes")
    print(f"  Val:   {val_imgs} images, {val_boxes} boxes")
    print(f"  Config: {yaml_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", default="datasets/raw/crowdhuman")
    parser.add_argument("--output", default="datasets/processed/crowdhuman_yolo")
    parser.add_argument("--box-type", default="fbox", choices=["fbox", "vbox", "hbox"])
    args = parser.parse_args()
    prepare_crowdhuman(args.raw, args.output, args.box_type)
