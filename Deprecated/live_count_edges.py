# import json
# import os
# import cv2
# import numpy as np
# from urllib.parse import quote
# from collections import deque

# from settings import USER, PASS, IP, PORT, CHANNEL, SUBTYPE

# CONFIG_PATH = "config.json"

# # RTSP stability
# os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|stimeout;3000000|max_delay;0"


# # =========================
# # Mask tuning (MAIN CHANGE)
# # =========================
# MASK_SHRINK = 0.55   # 1.0 = original slot polygon, smaller = tighter mask (try 0.65, 0.55, 0.45)
# FOCUS_FRONT = True   # bias the shrunken mask toward the "front" of each cell
# FRONT_BIAS  = 0.18   # 0..0.5 (how much to shift mask toward front if FOCUS_FRONT is True)

# # View toggles
# SHOW_MASK_OVERLAY = False  # press M to toggle
# SHOW_VALUES = False        # press V to toggle per-slot edge ratios


# def mask_from_poly(h, w, poly):
#     mask = np.zeros((h, w), dtype=np.uint8)
#     pts = np.array(poly, dtype=np.int32).reshape(-1, 1, 2)
#     cv2.fillPoly(mask, [pts], 255)
#     return mask


# def shrink_poly(poly, shrink=0.6, focus_front=True, front_bias=0.15):
#     """
#     Shrink a polygon about its centroid (scale toward center).
#     Optionally shift it toward the 'front' (higher y) in image coords.
#     """
#     pts = np.array(poly, dtype=np.float32)
#     if pts.shape[0] < 3:
#         return poly

#     centroid = pts.mean(axis=0)
#     pts2 = centroid + (pts - centroid) * float(shrink)

#     if focus_front:
#         # In image coordinates, y increases downward.
#         min_y = pts2[:, 1].min()
#         max_y = pts2[:, 1].max()
#         height = max(1.0, max_y - min_y)
#         pts2[:, 1] += float(front_bias) * height  # shift down toward "front"

#     return pts2.astype(np.int32).tolist()


# def edge_ratio(gray, mask, c1=60, c2=180):
#     # blur reduces noise from compression artifacts
#     g = cv2.GaussianBlur(gray, (5, 5), 0)
#     edges = cv2.Canny(g, c1, c2)  # edges are 0/255
#     m = mask.astype(bool)
#     if m.sum() == 0:
#         return 0.0
#     return float(edges[m].mean() / 255.0)  # 0..1


# # Load local geometry config (kept out of git via .gitignore)
# with open(CONFIG_PATH, "r") as f:
#     cfg = json.load(f)

# roi_cfg = cfg["roi"]
# slots = cfg["slots"]
# sku_by_col = cfg.get("sku_by_col", {"1": "SKU_LEFT", "2": "SKU_MIDDLE", "3": "SKU_RIGHT"})

# # Build RTSP URL (do NOT print credentials)
# USER_ENC = quote(str(USER), safe="")
# PASS_ENC = quote(str(PASS), safe="")
# RTSP = f"rtsp://{USER_ENC}:{PASS_ENC}@{IP}:{PORT}/cam/realmonitor?channel={CHANNEL}&subtype={SUBTYPE}"

# cap = cv2.VideoCapture(RTSP, cv2.CAP_FFMPEG)
# if not cap.isOpened():
#     print("FAILED: could not open stream. Check .env values / network / channel.")
#     raise SystemExit(1)

# WIN = "Inventision - Live Count (Edges)"
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

# # ---- Build SHRUNKE*N masks per slot (KEY CHANGE) ----
# slot_polys_shrunk = {}
# slot_masks = {}
# for s in slots:
#     sid = s["id"]
#     poly = s["poly"]
#     poly2 = shrink_poly(poly, shrink=MASK_SHRINK, focus_front=FOCUS_FRONT, front_bias=FRONT_BIAS)
#     slot_polys_shrunk[sid] = poly2
#     slot_masks[sid] = mask_from_poly(H, W, poly2)

# # Debounce / smoothing per slot (prevents flicker)
# HISTORY = 5
# hist = {s["id"]: deque(maxlen=HISTORY) for s in slots}

# # Occupancy threshold (tune live)
# EDGE_THR = 0.030  # start here; press +/- to tune

# # Canny thresholds
# CANNY1, CANNY2 = 60, 180

# print("Running edge-based occupancy (SHRUNK masks).")
# print("Controls:  + / - adjust EDGE_THR | M toggle mask overlay | V toggle values | Q quit")
# print("Tip: too many ON -> press + ; nothing ON -> press -")
# print(f"Mask shrink={MASK_SHRINK:.2f} focus_front={FOCUS_FRONT} front_bias={FRONT_BIAS:.2f}")
# print(f"RTSP target (safe): {IP}:{PORT} channel={CHANNEL} subtype={SUBTYPE}")  # safe (no creds)

# # --- small text settings ---
# FONT = cv2.FONT_HERSHEY_SIMPLEX
# TOP_SCALE = 0.40
# TOP_THICK = 1
# SLOT_SCALE = 0.35
# SLOT_THICK = 1

# while True:
#     ok, frame = cap.read()
#     if not ok or frame is None:
#         continue

#     roi = frame[y1:y2, x1:x2]
#     gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

#     overlay = roi.copy()
#     counts = {1: 0, 2: 0, 3: 0}

#     # If mask overlay is enabled, we’ll draw translucent fill
#     if SHOW_MASK_OVERLAY:
#         mask_vis = np.zeros_like(overlay, dtype=np.uint8)

#     # Track ratios for debugging
#     ratios = {}

#     for s in slots:
#         sid = s["id"]
#         col = int(s["col"])
#         mask = slot_masks[sid]

#         ratio = edge_ratio(gray, mask, CANNY1, CANNY2)
#         ratios[sid] = ratio
#         occupied_now = ratio > EDGE_THR

#         # majority vote over last HISTORY frames
#         hist[sid].append(1 if occupied_now else 0)
#         occupied = (sum(hist[sid]) >= (HISTORY // 2 + 1))

#         if occupied:
#             counts[col] += 1

#         # Draw original polygon outline (thin)
#         poly_orig = np.array(s["poly"], dtype=np.int32).reshape(-1, 1, 2)
#         cv2.polylines(overlay, [poly_orig], True, (255, 255, 255), 1)

#         # Draw shrunken polygon outline (thick = the real measured region)
#         poly_shr = np.array(slot_polys_shrunk[sid], dtype=np.int32).reshape(-1, 1, 2)
#         color = (0, 255, 0) if occupied else (0, 0, 255)
#         cv2.polylines(overlay, [poly_shr], True, color, 2)

#         # Optional translucent mask fill
#         if SHOW_MASK_OVERLAY:
#             cv2.fillPoly(mask_vis, [poly_shr], (255, 255, 255))

#         # tiny slot id label
#         tx, ty = s["poly"][0]
#         cv2.putText(
#             overlay,
#             sid,
#             (tx + 3, ty + 12),
#             FONT,
#             SLOT_SCALE,
#             (255, 255, 255),
#             SLOT_THICK,
#         )

#         # Optional ratio value near slot
#         if SHOW_VALUES:
#             cv2.putText(
#                 overlay,
#                 f"{ratio:.3f}",
#                 (tx + 3, ty + 28),
#                 FONT,
#                 0.33,
#                 (255, 255, 0),
#                 1,
#             )

#     # Blend mask overlay if enabled
#     if SHOW_MASK_OVERLAY:
#         overlay = cv2.addWeighted(overlay, 1.0, mask_vis, 0.18, 0)

#     summary = (
#         f"{sku_by_col.get('1','C1')}={counts[1]}   "
#         f"{sku_by_col.get('2','C2')}={counts[2]}   "
#         f"{sku_by_col.get('3','C3')}={counts[3]}   "
#         f"edge_thr={EDGE_THR:.3f}  shrink={MASK_SHRINK:.2f}"
#     )

#     cv2.putText(overlay, summary, (10, 22), FONT, TOP_SCALE, (0, 0, 0), 3)
#     cv2.putText(overlay, summary, (10, 22), FONT, TOP_SCALE, (255, 255, 255), TOP_THICK)

#     cv2.imshow(WIN, overlay)

#     key = cv2.waitKey(1) & 0xFF

#     if key in (ord("q"), ord("Q")):
#         break
#     if key in (ord("+"), ord("=")):
#         EDGE_THR += 0.005
#         print(f"EDGE_THR -> {EDGE_THR:.3f}")
#     if key in (ord("-"), ord("_")):
#         EDGE_THR = max(0.001, EDGE_THR - 0.005)
#         print(f"EDGE_THR -> {EDGE_THR:.3f}")

#     if key in (ord("m"), ord("M")):
#         SHOW_MASK_OVERLAY = not SHOW_MASK_OVERLAY
#         print(f"SHOW_MASK_OVERLAY -> {SHOW_MASK_OVERLAY}")

#     if key in (ord("v"), ord("V")):
#         SHOW_VALUES = not SHOW_VALUES
#         print(f"SHOW_VALUES -> {SHOW_VALUES}")

# cap.release()
# cv2.destroyAllWindows()
# print("Done.")
