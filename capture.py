import os
import sys
import time
import json
from PIL import ImageGrab
import numpy as np

CONFIG_FILENAME = "config.json"


def app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def config_path():
    return os.path.join(app_dir(), CONFIG_FILENAME)


def get_current_project_dir():
    path = config_path()
    if not os.path.exists(path):
        return ""

    try:
        with open(path, "r", encoding="utf-8") as f:
            config = json.load(f)
            return config.get("current_project_dir", "").strip()
    except Exception:
        return ""


project_dir = get_current_project_dir()
if not project_dir:
    raise RuntimeError('Current project path was not found. Click "Start Recording" in the main app first.')

save_folder = os.path.join(project_dir, "slides")
os.makedirs(save_folder, exist_ok=True)

stop_flag = os.path.join(app_dir(), "stop.flag")

bbox = None
last_img = None
count = 1


def crop_center(img):
    """Capture the main center area to reduce border/taskbar noise."""
    h, w = img.shape[:2]
    top = int(h * 0.1)
    bottom = int(h * 0.9)
    left = int(w * 0.1)
    right = int(w * 0.9)
    return img[top:bottom, left:right]


def preprocess(img):
    """Crop and convert to grayscale."""
    img = crop_center(img)
    if len(img.shape) == 3:
        img = img.mean(axis=2)  # Convert to grayscale
    return img.astype(np.float32)


def get_diff_score(img1, img2):
    img1 = preprocess(img1)
    img2 = preprocess(img2)
    diff = np.mean(np.abs(img1 - img2))
    return diff


def is_different(img1, img2, threshold=6):
    diff = get_diff_score(img1, img2)
    return diff > threshold


while True:
    if os.path.exists(stop_flag):
        break

    img = ImageGrab.grab(bbox=bbox)
    img_np = np.array(img)

    if last_img is None:
        last_img = img_np
        filename = os.path.join(save_folder, f"slide_{count:03d}.png")
        img.save(filename)
        count += 1
    else:
        diff = get_diff_score(img_np, last_img)
        print(f"Current difference value: {diff:.2f}")

        if diff > 6:
            filename = os.path.join(save_folder, f"slide_{count:03d}.png")
            img.save(filename)
            last_img = img_np
            count += 1

            # Avoid duplicate saves caused by animation/transitions
            time.sleep(1.0)

    time.sleep(0.6)
