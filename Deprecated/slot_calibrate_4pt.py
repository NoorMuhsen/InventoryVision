# import json
# import os
# import cv2
# import numpy as np
# from urllib.parse import quote

# # SAFE: pulls secrets from .env via settings.py
# from settings import USER, PASS, IP, PORT, CHANNEL, SUBTYPE

# # ======= ROI CROP (your locked zoom area) =======
# X1, Y1, X2, Y2 = 1172, 715, 1756, 1045
# # ===============================================

# GRID_COLS = 3   # 3 SKUs
# GRID_ROWS = 3   # depth up to 3

# CONFIG_OUT = "config.json"

# # Force RTSP over TCP (stability)
# os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|stimeout;3000000|max_delay;0"

# USER_ENC = quote(str(USER), safe="")
# PASS_ENC = quote(str(PASS), safe="")
# RTSP = f"rtsp://{USER_ENC}:{PASS_ENC}@{IP}:{PORT}/cam/realmonitor?channel={CHANNEL}&subtype={SUBTYPE}"

# cap = cv2.VideoCapture(RTSP, cv2.CAP_FFMPEG)
# if not cap.isOpened():
#     print("FAILED: could not open stream. Check .env / network / channel.")
#     raise SystemExit(1)

# WIN = "Slot Calibrator (4 clicks: TL,TR,BR,BL)"
# cv2.namedWindow(WIN, cv2.WINDOW_NORMAL)
# cv2.resizeWindow(WIN, 1200, 700)

# pts = []  # 4 points in ROI

# def on_mouse(event, x, y, flags, param):
#     global pts
#     if event == cv2.EVENT_LBUTTONDOWN:
#         if len(pts) < 4:
#             pts.append((x, y))
#             print(f"Point {len(pts)}: ({x},{y})")

# cv2.setMouseCallback(WIN, on_mouse)

# def order_points(pts_arr):
#     pts_arr = np.array(pts_arr, dtype=np.float32)
#     s = pts_arr.sum(axis=1)
#     diff = np.diff(pts_arr, axis=1).reshape(-1)
#     tl = pts_arr[np.argmin(s)]
#     br = pts_arr[np.argmax(s)]
#     tr = pts_arr[np.argmin(diff)]
#     bl = pts_arr[np.argmax(diff)]
#     return np.array([tl, tr, br, bl], dtype=np.float32)

# print("Instructions:")
# print("Click the 4 corners of the TOP SURFACE where bottles sit (any order).")
# print("Keys: R reset | S save config.json | Q quit")
# print("Depth labeling: d1 = FRONT (closest), d3 = BACK (farthest)")
# print(f"RTSP target (safe): {IP}:{PORT} channel={CHANNEL} subtype={SUBTYPE}")  # no creds printed

# while True:
#     ok, frame = cap.read()
#     if not ok or frame is None:
#         continue

#     roi = frame[Y1:Y2, X1:X2].copy()
#     overlay = roi.copy()

#     # Draw clicked points
#     for i, (x, y) in enumerate(pts):
#         cv2.circle(overlay, (x, y), 6, (0, 255, 255), -1)
#         cv2.putText(
#             overlay, str(i + 1), (x + 8, y - 8),
#             cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2
#         )

#     slots = []

#     if len(pts) == 4:
#         src = order_points(pts)

#         # Determine rectified size
#         widthA = np.linalg.norm(src[2] - src[3])   # br-bl
#         widthB = np.linalg.norm(src[1] - src[0])   # tr-tl
#         maxW = int(max(widthA, widthB))

#         heightA = np.linalg.norm(src[1] - src[2])  # tr-br
#         heightB = np.linalg.norm(src[0] - src[3])  # tl-bl
#         maxH = int(max(heightA, heightB))

#         maxW = max(200, min(2000, maxW))
#         maxH = max(200, min(2000, maxH))

#         dst = np.array([
#             [0, 0],
#             [maxW - 1, 0],
#             [maxW - 1, maxH - 1],
#             [0, maxH - 1]
#         ], dtype=np.float32)

#         M = cv2.getPerspectiveTransform(src, dst)
#         Minv = cv2.getPerspectiveTransform(dst, src)

#         cell_w = maxW / GRID_COLS
#         cell_h = maxH / GRID_ROWS

#         # Draw surface outline
#         cv2.polylines(overlay, [src.astype(int)], True, (0, 255, 0), 2)

#         # Draw grid and store slot polygons back in ROI coords
#         for r in range(GRID_ROWS):
#             for c in range(GRID_COLS):
#                 gx1 = int(c * cell_w)
#                 gy1 = int(r * cell_h)
#                 gx2 = int((c + 1) * cell_w)
#                 gy2 = int((r + 1) * cell_h)

#                 rect = np.array([
#                     [gx1, gy1],
#                     [gx2, gy1],
#                     [gx2, gy2],
#                     [gx1, gy2]
#                 ], dtype=np.float32).reshape(-1, 1, 2)

#                 rect_back = cv2.perspectiveTransform(rect, Minv).reshape(-1, 2)
#                 poly = rect_back.astype(int)

#                 # FLIP DEPTH: top row (back) becomes d3, bottom row (front) becomes d1
#                 depth = GRID_ROWS - r
#                 slot_id = f"c{c + 1}_d{depth}"

#                 cv2.polylines(overlay, [poly.reshape(-1, 1, 2)], True, (255, 255, 255), 1)

#                 tl = tuple(poly[0])
#                 cv2.putText(
#                     overlay, slot_id, (tl[0] + 5, tl[1] + 20),
#                     cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1
#                 )

#                 slots.append({
#                     "id": slot_id,
#                     "col": c + 1,
#                     "depth": depth,
#                     "poly": poly.tolist()
#                 })

#     cv2.imshow(WIN, overlay)

#     key = cv2.waitKey(1) & 0xFF
#     if key in (ord('q'), ord('Q')):
#         break

#     if key in (ord('r'), ord('R')):
#         pts = []
#         print("Reset points.")

#     if key in (ord('s'), ord('S')):
#         if len(pts) != 4:
#             print("Need 4 corner clicks before saving.")
#             continue

#         config = {
#             "roi": {"x1": X1, "y1": Y1, "x2": X2, "y2": Y2},
#             "surface_corners_roi": order_points(pts).tolist(),
#             "grid": {"cols": GRID_COLS, "rows": GRID_ROWS},
#             "slots": slots,
#             "sku_by_col": {"1": "SKU_LEFT", "2": "SKU_MIDDLE", "3": "SKU_RIGHT"}
#         }

#         with open(CONFIG_OUT, "w") as f:
#             json.dump(config, f, indent=2)

#         print(f"Saved {CONFIG_OUT} (no network secrets; depth flipped: d1 front).")

# cap.release()
# cv2.destroyAllWindows()
# print("Done.")
