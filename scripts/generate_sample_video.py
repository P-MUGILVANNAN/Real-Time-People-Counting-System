import os
import argparse
import numpy as np
import cv2

def generate_crowd_video(
    output_path: str = "datasets/sample/crowd_sample.mp4",
    num_people: int = 16,
    width: int = 640,
    height: int = 480,
    duration_sec: int = 10,
    fps: int = 24
):
    """
    Generates a realistic synthetic crowd video with walking human silhouettes,
    overlapping trajectories, and occlusion scenarios for testing people detection,
    tracking, line-crossing tripwires, and density estimation.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    total_frames = duration_sec * fps
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    # Initialize agents
    people = []
    np.random.seed(42)
    for i in range(num_people):
        start_x = np.random.randint(50, width - 50)
        start_y = np.random.randint(80, height - 120)
        speed_x = np.random.uniform(-2.5, 2.5)
        speed_y = np.random.uniform(-1.0, 1.0)
        color = (int(np.random.randint(180, 240)), int(np.random.randint(70, 160)), int(np.random.randint(60, 140)))
        body_h = np.random.randint(75, 110)
        body_w = int(body_h * 0.42)
        people.append({
            "x": float(start_x),
            "y": float(start_y),
            "vx": speed_x if abs(speed_x) > 0.8 else 1.5,
            "vy": speed_y,
            "color": color,
            "w": body_w,
            "h": body_h,
            "phase": np.random.uniform(0, 2 * np.pi)
        })

    # Floor grid background
    bg = np.full((height, width, 3), 45, dtype=np.uint8)
    for y in range(0, height, 40):
        cv2.line(bg, (0, y), (width, y), (55, 55, 55), 1)
    for x in range(0, width, 40):
        cv2.line(bg, (x, 0), (x, height), (55, 55, 55), 1)

    print(f"Rendering {total_frames} frames to {output_path}...")
    for frame_idx in range(total_frames):
        frame = bg.copy()
        
        # Sort people by Y to simulate depth perspective ordering
        people.sort(key=lambda p: p["y"])

        for p in people:
            # Update position
            p["x"] += p["vx"]
            p["y"] += p["vy"]

            # Bounce off borders
            if p["x"] < 40 or p["x"] > width - 40:
                p["vx"] *= -1
            if p["y"] < 60 or p["y"] > height - 60:
                p["vy"] *= -1

            cx = int(p["x"])
            cy = int(p["y"])
            w = p["w"]
            h = p["h"]

            # Leg walking motion oscillation
            leg_offset = int(np.sin(frame_idx * 0.25 + p["phase"]) * (w * 0.3))

            # Head
            head_radius = max(6, int(w * 0.32))
            head_y = cy - h // 2 + head_radius
            cv2.circle(frame, (cx, head_y), head_radius, (210, 180, 160), -1)
            cv2.circle(frame, (cx, head_y), head_radius, (30, 30, 30), 1)

            # Torso
            torso_top = head_y + head_radius
            torso_bottom = cy + int(h * 0.15)
            cv2.rectangle(frame, (cx - w // 2, torso_top), (cx + w // 2, torso_bottom), p["color"], -1)

            # Legs
            leg_bottom = cy + h // 2
            cv2.line(frame, (cx - w // 4, torso_bottom), (cx - w // 4 + leg_offset, leg_bottom), (30, 30, 30), 3)
            cv2.line(frame, (cx + w // 4, torso_bottom), (cx + w // 4 - leg_offset, leg_bottom), (30, 30, 30), 3)

        out.write(frame)

    out.release()
    print(f"Sample video created successfully: {output_path} ({os.path.getsize(output_path)} bytes)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="datasets/sample/crowd_sample.mp4")
    parser.add_argument("--num-people", type=int, default=16)
    parser.add_argument("--duration-sec", type=int, default=10)
    args = parser.parse_args()
    generate_crowd_video(output_path=args.output, num_people=args.num_people, duration_sec=args.duration_sec)
