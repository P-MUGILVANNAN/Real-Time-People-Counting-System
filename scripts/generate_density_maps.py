import os
import argparse
import numpy as np
import cv2
import scipy.io as io
from scipy.ndimage import gaussian_filter

def generate_gaussian_density_map(
    img_shape: tuple,
    points: np.ndarray,
    sigma: float = 15.0
) -> np.ndarray:
    """
    Generates a 2D continuous density map from discrete head point annotations.
    Guarantees exact count preservation: sum(density_map) == len(points).
    """
    h, w = img_shape[:2]
    density = np.zeros((h, w), dtype=np.float32)
    num_points = len(points)
    if num_points == 0:
        return density

    for pt in points:
        x = min(w - 1, max(0, int(round(pt[0]))))
        y = min(h - 1, max(0, int(round(pt[1]))))
        density[y, x] += 1.0

    # Apply spatial Gaussian blur
    density = gaussian_filter(density, sigma=sigma, mode="constant")
    
    # Enforce strict count preservation
    current_sum = np.sum(density)
    if current_sum > 0:
        density = density * (num_points / current_sum)

    return density


def process_shanghaitech(
    raw_dir: str = "datasets/raw/ShanghaiTech",
    part: str = "part_B",
    output_dir: str = "datasets/density_maps",
    sigma: float = 15.0
):
    part_dir = os.path.join(raw_dir, part)
    target_out = os.path.join(output_dir, part)
    os.makedirs(target_out, exist_ok=True)

    print(f"Generating Gaussian density maps for ShanghaiTech {part}...")

    train_gt_dir = os.path.join(part_dir, "train_data", "ground-truth")
    train_img_dir = os.path.join(part_dir, "train_data", "images")

    if not os.path.exists(train_gt_dir):
        print(f"ShanghaiTech {part} not found at {part_dir}.")
        print("Creating synthetic demonstration density map for pipeline validation...")
        # Create a sample density map to verify integration
        sample_img_shape = (480, 640)
        sample_points = np.array([
            [120, 150], [140, 160], [180, 210], [200, 220], [350, 180],
            [370, 190], [400, 210], [420, 230], [500, 300], [520, 310]
        ], dtype=np.float32)

        dmap = generate_gaussian_density_map(sample_img_shape, sample_points, sigma=sigma)
        sample_out = os.path.join(target_out, "sample_demo_density.npy")
        np.save(sample_out, dmap)
        print(f"Generated sample density map: {sample_out}")
        print(f"  Shape: {dmap.shape}, Integrated Count: {np.sum(dmap):.2f} (Expected: {len(sample_points)})")
        return

    # Process all images
    mat_files = [f for f in os.listdir(train_gt_dir) if f.endswith(".mat")]
    print(f"Found {len(mat_files)} annotation files.")

    for mat_file in mat_files:
        mat_path = os.path.join(train_gt_dir, mat_file)
        # Load .mat
        mat = io.loadmat(mat_path)
        # ShanghaiTech structure: image_info{1,1}{1,1}{1,1}
        try:
            points = mat["image_info"][0, 0][0, 0][0].astype(np.float32)
        except Exception:
            continue

        img_name = mat_file.replace("GT_IMG_", "IMG_").replace(".mat", ".jpg")
        img_path = os.path.join(train_img_dir, img_name)
        if not os.path.exists(img_path):
            continue

        img = cv2.imread(img_path)
        dmap = generate_gaussian_density_map(img.shape[:2], points, sigma=sigma)

        out_name = os.path.splitext(img_name)[0] + ".npy"
        np.save(os.path.join(target_out, out_name), dmap)

    print("Density map generation complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", default="datasets/raw/ShanghaiTech")
    parser.add_argument("--part", default="part_B", choices=["part_A", "part_B"])
    parser.add_argument("--output", default="datasets/density_maps")
    parser.add_argument("--sigma", type=float, default=15.0)
    args = parser.parse_args()
    process_shanghaitech(args.raw, args.part, args.output, args.sigma)
