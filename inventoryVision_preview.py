"""
inventoryVision_preview.py

Open RTSP stream and show a live preview window with digital zoom/pan.
Controls:
  +/-   zoom in/out
  WASD  pan
  R     reset view
  C     save current view to zoom_view.jpg
  Q     quit

"""

import cv2
from urllib.parse import quote

from settings import USER, PASS, IP, PORT, CHANNEL, SUBTYPE  # loaded from .env

# URL-encode creds (handles special characters)
USER_ENC = quote(str(USER), safe="")
PASS_ENC = quote(str(PASS), safe="")

RTSP = f"rtsp://{USER_ENC}:{PASS_ENC}@{IP}:{PORT}/cam/realmonitor?channel={CHANNEL}&subtype={SUBTYPE}"

cap = cv2.VideoCapture(RTSP, cv2.CAP_FFMPEG)
if not cap.isOpened():
    print("FAILED: could not open RTSP stream (check .env values / channel / network).")
    raise SystemExit(1)

print("OK: stream opened.")
print("Controls: +/- zoom | WASD pan | R reset | C save zoomed view | Q quit")
print(f"RTSP target (safe): {IP}:{PORT} channel={CHANNEL} subtype={SUBTYPE}")  # no creds printed

WIN = "InventoryVision Preview"
cv2.namedWindow(WIN, cv2.WINDOW_NORMAL)
cv2.resizeWindow(WIN, 1400, 800)

zoom = 1.0          # 1.0 = no zoom
cx, cy = None, None # zoom center (set on first frame)
step = 0.10         # zoom increment (10%)
pan_px = 60         # pan step in pixels (original-frame coords)

while True:
    ok, frame = cap.read()
    if not ok or frame is None:
        continue

    h, w = frame.shape[:2]
    if cx is None:
        cx, cy = w // 2, h // 2

    # Crop size based on zoom
    crop_w = int(w / zoom)
    crop_h = int(h / zoom)

    # Clamp crop size
    crop_w = max(80, min(w, crop_w))
    crop_h = max(80, min(h, crop_h))

    x1 = int(cx - crop_w // 2)
    y1 = int(cy - crop_h // 2)
    x2 = x1 + crop_w
    y2 = y1 + crop_h

    # Clamp to frame bounds
    if x1 < 0:
        x2 -= x1
        x1 = 0
    if y1 < 0:
        y2 -= y1
        y1 = 0
    if x2 > w:
        x1 -= (x2 - w)
        x2 = w
    if y2 > h:
        y1 -= (y2 - h)
        y2 = h
    x1 = max(0, x1)
    y1 = max(0, y1)

    view = frame[y1:y2, x1:x2]

    # Scale to display (keep same window size feel)
    disp = cv2.resize(view, (w, h), interpolation=cv2.INTER_LINEAR)

    # Overlay info
    cv2.putText(
        disp,
        f"zoom={zoom:.2f}  center=({cx},{cy})  crop=({x1},{y1})-({x2},{y2})",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2,
    )

    cv2.imshow(WIN, disp)

    key = cv2.waitKey(1) & 0xFF

    # Quit
    if key in (ord("q"), ord("Q")):
        break

    # Zoom in/out
    if key in (ord("+"), ord("=")):
        zoom = min(10.0, zoom * (1.0 + step))
    if key in (ord("-"), ord("_")):
        zoom = max(1.0, zoom / (1.0 + step))

    # Pan (original-frame coords)
    if key in (ord("a"), ord("A")):
        cx = max(0, cx - pan_px)
    if key in (ord("d"), ord("D")):
        cx = min(w, cx + pan_px)
    if key in (ord("w"), ord("W")):
        cy = max(0, cy - pan_px)
    if key in (ord("s"), ord("S")):
        cy = min(h, cy + pan_px)

    # Reset
    if key in (ord("r"), ord("R")):
        zoom = 1.0
        cx, cy = w // 2, h // 2

    # Save current view
    if key in (ord("c"), ord("C")):
        cv2.imwrite("zoom_view.jpg", disp)
        print("Saved zoom_view.jpg")

cap.release()
cv2.destroyAllWindows()
print("Done.")
