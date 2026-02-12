# the method of going by background diff is faulty, because the background is not static (lighting changes, reflections, etc).
# instead, well go by edge density. the idea is that an empty slot will have a mostly smooth surface, while an occupied slot will have more edges due to the bottle shapes and labels.
# this is a simple heuristic that can work decently in good lighting and with a well-defined

# import json
# import os
# import cv2
# import numpy as np
# from urllib.parse import quote
# from collections import deque

# # RTSP stability
# os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|stimeout;3000000|max_delay;0"

# def mask_from_poly(h, w, poly):
#     mask = np.zeros((h, w), dtype=np.uint8)
#     pts = np.array(poly, dtype=np.int32).reshape(-1, 1, 2)
#     cv2.fillPoly(mask, [pts], 255)
#     return mask

# def edge_ratio(gray, mask, c1=60, c2=180):
#     # blur reduces noise from compression artifacts
#     g = cv2.GaussianBlur(gray, (5, 5), 0)
#     edges = cv2.Canny(g, c1, c2)  # edges are 0/255
#     m = mask.astype(bool)
#     if m.sum() == 0:
#         return 0.0
#     return float(edges[m].mean() / 255.0)  # 0..1

# with open(CONFIG_PATH, "r") as f:
#     cfg = json.load(f)

# IP = cfg["rtsp"]["ip"]
# PORT = cfg["rtsp"]["port"]
# CHANNEL = cfg["rtsp"]["channel"]
# SUBTYPE = cfg["rtsp"]["subtype"]
# roi_cfg = cfg["roi"]
# slots = cfg["slots"]
# sku_by_col = cfg.get("sku_by_col", {"1": "SKU_LEFT", "2": "SKU_MIDDLE", "3": "SKU_RIGHT"})

# USER_ENC = quote(USER, safe="")
# PASS_ENC = quote(PASS, safe="")
# RTSP = f"rtsp://{USER_ENC}:{PASS_ENC}@{IP}:{PORT}/cam/realmonitor?channel={CHANNEL}&subtype={SUBTYPE}"

# cap = cv2.VideoCapture(RTSP, cv2.CAP_FFMPEG)
# if not cap.isOpened():
#     print("FAILED: could not open stream. Check RTSP/auth.")
#     raise SystemExit(1)

# WIN = "Inventory Vision - Live Count (Edges)"
# cv2.namedWindow(WIN, cv2.WINDOW_NORMAL)
# cv2.resizeWindow(WIN, 1280, 720)

# # Read one frame to size masks
# ok, frame = cap.read()
# if not ok or frame is None:
#     print("FAILED: could not read initial frame.")
#     raise SystemExit(1)

# x1, y1, x2, y2 = roi_cfg["x1"], roi_cfg["y1"], roi_cfg["x2"], roi_cfg["y2"]
# roi0 = frame[y1:y2, x1:x2]
# gray0 = cv2.cvtColor(roi0, cv2.COLOR_BGR2GRAY)
# H, W = gray0.shape[:2]

# slot_masks = {s["id"]: mask_from_poly(H, W, s["poly"]) for s in slots}

# # Debounce / smoothing per slot (prevents flicker)
# HISTORY = 5
# hist = {s["id"]: deque(maxlen=HISTORY) for s in slots}

# # Occupancy threshold (tune live)
# EDGE_THR = 0.030  # start here; press +/- to tune

# # Canny thresholds
# CANNY1, CANNY2 = 60, 180

# print("Running edge-based occupancy.")
# print("Controls:  + / - adjust EDGE_THR | Q quit")
# print("Tip: too many ON -> press + ; nothing ON -> press -")

# # --- small text settings (you asked for this) ---
# FONT = cv2.FONT_HERSHEY_SIMPLEX
# TOP_SCALE = 0.50       # smaller top text
# TOP_THICK = 1
# SLOT_SCALE = 0.35      # tiny slot labels
# SLOT_THICK = 1

# while True:
#     ok, frame = cap.read()
#     if not ok or frame is None:
#         continue

#     roi = frame[y1:y2, x1:x2]
#     gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

#     overlay = roi.copy()
#     counts = {1: 0, 2: 0, 3: 0}

#     for s in slots:
#         sid = s["id"]
#         col = int(s["col"])
#         mask = slot_masks[sid]

#         ratio = edge_ratio(gray, mask, CANNY1, CANNY2)
#         occupied_now = ratio > EDGE_THR

#         # majority vote over last HISTORY frames
#         hist[sid].append(1 if occupied_now else 0)
#         occupied = (sum(hist[sid]) >= (HISTORY // 2 + 1))

#         if occupied:
#             counts[col] += 1

#         poly = np.array(s["poly"], dtype=np.int32).reshape(-1, 1, 2)

#         # Green if occupied, red if empty
#         color = (0, 255, 0) if occupied else (0, 0, 255)
#         cv2.polylines(overlay, [poly], True, color, 2)

#         # tiny slot id label near first point
#         tx, ty = s["poly"][0]
#         cv2.putText(overlay, sid, (tx + 3, ty + 12), FONT, SLOT_SCALE, (255, 255, 255), SLOT_THICK)

#     # Small top summary
#     summary = (
#         f"{sku_by_col.get('1','C1')}={counts[1]}   "
#         f"{sku_by_col.get('2','C2')}={counts[2]}   "
#         f"{sku_by_col.get('3','C3')}={counts[3]}   "
#         f"edge_thr={EDGE_THR:.3f}   (+/- to tune)"
#     )

#     # Outline text for readability
#     cv2.putText(overlay, summary, (10, 22), FONT, TOP_SCALE, (0, 0, 0), 3)
#     cv2.putText(overlay, summary, (10, 22), FONT, TOP_SCALE, (255, 255, 255), TOP_THICK)

#     cv2.imshow(WIN, overlay)

#     key = cv2.waitKey(1) & 0xFF
#     if key in (ord("q"), ord("Q")):
#         break
#     if key == ord("+") or key == ord("="):
#         EDGE_THR += 0.005
#         print(f"EDGE_THR -> {EDGE_THR:.3f}")
#     if key == ord("-") or key == ord("_"):
#         EDGE_THR = max(0.001, EDGE_THR - 0.005)
#         print(f"EDGE_THR -> {EDGE_THR:.3f}")

# cap.release()
# cv2.destroyAllWindows()
# print("Done.")
