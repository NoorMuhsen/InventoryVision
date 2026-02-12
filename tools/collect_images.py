import os
import time
import json
import cv2
import sys
from urllib.parse import quote

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from settings import (
    INVENTISION_USER,
    INVENTISION_PASS,
    INVENTISION_IP,
    INVENTISION_PORT,
    INVENTISION_CHANNEL,
    INVENTISION_SUBTYPE,
)

OUT_DIR = os.path.join("data", "captures")
CONFIG_PATH = "config.json"

os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|stimeout;3000000|max_delay;0"


def safe_mkdir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def load_config(config_path: str):
    if not os.path.exists(config_path):
        return {}
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def save_config(config_path: str, cfg: dict):
    with open(config_path, "w") as f:
        json.dump(cfg, f, indent=2)


def load_roi_from_config(cfg: dict):
    roi = cfg.get("roi")
    if not roi:
        return None
    try:
        x1, y1, x2, y2 = int(roi["x1"]), int(roi["y1"]), int(roi["x2"]), int(roi["y2"])
        if x2 <= x1 or y2 <= y1:
            return None
        return (x1, y1, x2, y2)
    except Exception:
        return None


def clamp_roi(roi, w, h):
    x1, y1, x2, y2 = roi
    x1 = max(0, min(w - 2, x1))
    y1 = max(0, min(h - 2, y1))
    x2 = max(x1 + 1, min(w, x2))
    y2 = max(y1 + 1, min(h, y2))
    if x2 <= x1 or y2 <= y1:
        return None
    return (x1, y1, x2, y2)


def move_roi(roi, dx, dy, w, h):
    x1, y1, x2, y2 = roi
    return clamp_roi((x1 + dx, y1 + dy, x2 + dx, y2 + dy), w, h)


def scale_roi(roi, factor, w, h):
    # factor > 1 expands, < 1 shrinks
    x1, y1, x2, y2 = roi
    cx = (x1 + x2) // 2
    cy = (y1 + y2) // 2
    half_w = int((x2 - x1) * factor / 2)
    half_h = int((y2 - y1) * factor / 2)
    # enforce minimum size
    half_w = max(30, half_w)
    half_h = max(30, half_h)
    return clamp_roi((cx - half_w, cy - half_h, cx + half_w, cy + half_h), w, h)


def build_rtsp_url():
    user_enc = quote(str(INVENTISION_USER), safe="")
    pass_enc = quote(str(INVENTISION_PASS), safe="")
    return (
        f"rtsp://{user_enc}:{pass_enc}@{INVENTISION_IP}:{INVENTISION_PORT}"
        f"/cam/realmonitor?channel={INVENTISION_CHANNEL}&subtype={INVENTISION_SUBTYPE}"
    )


def main():
    safe_mkdir(OUT_DIR)

    rtsp = build_rtsp_url()
    cap = cv2.VideoCapture(rtsp, cv2.CAP_FFMPEG)
    if not cap.isOpened():
        print("FAILED: could not open RTSP stream. Check .env, network, channel/subtype.")
        raise SystemExit(1)

    cfg = load_config(CONFIG_PATH)
    roi = load_roi_from_config(cfg)

    win = "Collect Images (YOLO) - SPACE save | R toggle ROI | E edit ROI | Q quit"
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(win, 1280, 720)

    use_roi = True if roi else False
    edit_mode = False

    last_save_ts = 0.0
    save_cooldown_s = 0.15

    print("Stream opened.")
    if roi:
        print("ROI found in config.json. Press R to toggle ROI crop on/off.")
    else:
        print("No ROI found. Capturing full frame (you can create ROI in edit mode).")
        # create a default ROI once we know frame size (first frame)
    print("Controls: SPACE save | R toggle ROI | E edit ROI | S save ROI | P print ROI")

    while True:
        ok, frame = cap.read()
        if not ok or frame is None:
            continue

        h, w = frame.shape[:2]

        # If no ROI exists yet, create a reasonable default centered ROI
        if roi is None:
            roi = (w // 4, h // 4, (w * 3) // 4, (h * 3) // 4)
            use_roi = True

        active_roi = clamp_roi(roi, w, h) if (roi and use_roi) else None

        # Crop used for saving images
        crop = frame
        if active_roi:
            x1, y1, x2, y2 = active_roi
            crop = frame[y1:y2, x1:x2]

        # Preview (always show full frame + ROI box)
        preview = frame.copy()
        if active_roi:
            x1, y1, x2, y2 = active_roi
            color = (0, 255, 255) if edit_mode else (0, 255, 0)
            cv2.rectangle(preview, (x1, y1), (x2, y2), color, 2)
            cv2.putText(
                preview,
                f"ROI {'EDIT' if edit_mode else 'ON'}  ({x1},{y1})-({x2},{y2})",
                (x1 + 10, max(30, y1 + 30)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                color,
                2,
            )
        else:
            cv2.putText(
                preview,
                "ROI OFF (full frame)",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (255, 255, 255),
                2,
            )

        cv2.imshow(win, preview)
        key = cv2.waitKey(1) & 0xFF

        if key in (ord("q"), ord("Q")):
            break

        if key in (ord("r"), ord("R")):
            use_roi = not use_roi
            print(f"ROI -> {'ON' if use_roi else 'OFF'}")

        if key in (ord("e"), ord("E")):
            edit_mode = not edit_mode
            print(f"Edit mode -> {'ON' if edit_mode else 'OFF'}")

        if key in (ord("p"), ord("P")):
            if roi:
                print(f"ROI = {roi}")

        if key in (ord("s"), ord("S")):
            # Save ROI to config.json (local-only)
            if roi:
                cfg = load_config(CONFIG_PATH)
                cfg["roi"] = {"x1": roi[0], "y1": roi[1], "x2": roi[2], "y2": roi[3]}
                save_config(CONFIG_PATH, cfg)
                print(f"Saved ROI to {CONFIG_PATH}: {roi}")

        # ROI edit controls (only when edit_mode is on)
        if edit_mode and roi:
            # Hold SHIFT for faster steps
            fast = (cv2.waitKey(1) & 0xFF)  # harmless extra poll; keeps UI responsive
            step = 40 if (fast == 16) else 10  # SHIFT isn't reliable in cv2; keep simple
            step = 20  # stable default (cv2 keymods are inconsistent)

            if key in (ord("w"), ord("W")):
                roi = move_roi(roi, 0, -step, w, h)
            if key in (ord("s"), ord("S")):
                roi = move_roi(roi, 0, step, w, h)
            if key in (ord("a"), ord("A")):
                roi = move_roi(roi, -step, 0, w, h)
            if key in (ord("d"), ord("D")):
                roi = move_roi(roi, step, 0, w, h)

            # Expand/shrink ROI
            if key in (ord("+"), ord("=")):
                roi = scale_roi(roi, 1.05, w, h)
            if key in (ord("-"), ord("_")):
                roi = scale_roi(roi, 0.95, w, h)

        # Save image
        if key == 32:  # SPACE
            now = time.time()
            if now - last_save_ts < save_cooldown_s:
                continue
            last_save_ts = now

            ts = time.strftime("%Y%m%d_%H%M%S")
            ms = int((now - int(now)) * 1000)
            fname = f"cap_{ts}_{ms:03d}.jpg"
            out_path = os.path.join(OUT_DIR, fname)

            ok = cv2.imwrite(out_path, crop)
            if ok:
                print(f"Saved: {out_path}  ({crop.shape[1]}x{crop.shape[0]})")
            else:
                print("FAILED to save image.")

    cap.release()
    cv2.destroyAllWindows()
    print("Done.")


if __name__ == "__main__":
    main()
