import os
import argparse
import sys

def verify_datasets(base_dir: str = "datasets"):
    """
    Validates presence and directory layout of research datasets:
    - CrowdHuman
    - ShanghaiTech (Part A & Part B)
    Provides official links and ethical licensing terms when files are absent.
    """
    raw_dir = os.path.join(base_dir, "raw")
    os.makedirs(raw_dir, exist_ok=True)

    crowdhuman_dir = os.path.join(raw_dir, "crowdhuman")
    shanghaitech_dir = os.path.join(raw_dir, "ShanghaiTech")

    print("=" * 60)
    print("RESEARCH DATASET VERIFICATION & SETUP GUIDE")
    print("=" * 60)

    # 1. CrowdHuman
    print("\n[1] Checking CrowdHuman Dataset...")
    if os.path.exists(crowdhuman_dir):
        files = os.listdir(crowdhuman_dir)
        print(f"  Directory found: {crowdhuman_dir} ({len(files)} files/folders)")
        has_train_anno = os.path.exists(os.path.join(crowdhuman_dir, "annotation_train.odgt"))
        has_val_anno = os.path.exists(os.path.join(crowdhuman_dir, "annotation_val.odgt"))
        print(f"  - annotation_train.odgt present: {has_train_anno}")
        print(f"  - annotation_val.odgt present:   {has_val_anno}")
    else:
        print(f"  [MISSING] CrowdHuman not found at: {crowdhuman_dir}")
        print("  --> Official source: https://www.crowdhuman.org/")
        print("  --> Reference: Shao et al., 'CrowdHuman: A Benchmark for Detecting Human in a Crowd', arXiv:1805.00123")
        print("  --> Setup Steps:")
        print("      1. Request access from official benchmark portal.")
        print("      2. Download images and annotation_train.odgt, annotation_val.odgt.")
        print(f"      3. Extract into: {crowdhuman_dir}/")

    # 2. ShanghaiTech
    print("\n[2] Checking ShanghaiTech Dataset...")
    if os.path.exists(shanghaitech_dir):
        has_part_a = os.path.exists(os.path.join(shanghaitech_dir, "part_A"))
        has_part_b = os.path.exists(os.path.join(shanghaitech_dir, "part_B"))
        print(f"  Directory found: {shanghaitech_dir}")
        print(f"  - part_A present: {has_part_a}")
        print(f"  - part_B present: {has_part_b}")
    else:
        print(f"  [MISSING] ShanghaiTech not found at: {shanghaitech_dir}")
        print("  --> Reference: Zhang et al., 'Single-Image Crowd Counting via Multi-Column Convolutional Neural Network', CVPR 2016")
        print("  --> Official release: Academic Google Drive / Baidu Yun repository.")
        print("  --> Setup Steps:")
        print("      1. Download ShanghaiTech.zip from authorized academic repository.")
        print(f"      2. Unzip into {shanghaitech_dir}/ with 'part_A' and 'part_B' subfolders.")

    print("\n[3] Checking Demonstration / Sample Data...")
    sample_file = os.path.join(base_dir, "sample", "crowd_sample.mp4")
    if os.path.exists(sample_file):
        print(f"  [READY] Built-in demonstration video present: {sample_file} ({os.path.getsize(sample_file)} bytes)")
        print("  --> The system is ready to demonstrate live detection, tracking, tripwires, and heatmaps out of the box!")
    else:
        print(f"  [ACTION] Generate sample video using: python scripts/generate_sample_video.py")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default="datasets")
    args = parser.parse_args()
    verify_datasets(args.dir)
