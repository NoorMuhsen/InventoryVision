#This is faulty, the perspective is off and the grid doesnt line up where it needs to
# will keep this code as reference, but will be redone and won't be using it


 ###################################################################
# import json
# import os
# import cv2
# from urllib.parse import quote

# # ======= ROI CROP =======
# # If you want to reuse the exact crop from your overlay, set these:
# X1, Y1, X2, Y2 = 1172, 715, 1756, 1045
# # ============================================

# GRID_COLS = 3   # 3 SKUs (left/mid/right)
# GRID_ROWS = 3   # depth up to 3 (front/mid/back)

# os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|stimeout;3000000|max_delay;0"

# USER_ENC = quote(USER, safe="")
# PASS_ENC = quote(PASS, safe="")
# RTSP = f"rtsp://{USER_ENC}:{PASS_ENC}@{IP}:{PORT}/cam/realmonitor?channel={CHANNEL}&subtype={SUBTYPE}"

# cap = cv2.VideoCapture(RTSP, cv2.CAP_FFMPEG)
# if not cap.isOpened():
#     print("FAILED: could not open stream")
#     raise SystemExit(1)

# WIN = "Slot Calibrator (click TL then BR)"
# cv2.namedWindow(WIN, cv2.WINDOW_NORMAL)
# cv2.resizeWindow(WIN, 1200, 700)

# clicks = []  # two clicks: (x,y) in ROI coordinates
# last_roi = None

# def clamp(v, lo, hi):
#     return max(lo, min(hi, v))

# def on_mouse(event, x, y, flags, param):
#     global clicks
#     if event == cv2.EVENT_LBUTTONDOWN:
#         if len(clicks) < 2:
#             clicks.append((x, y))
#             print(f"Click {len(clicks)}: ({x},{y})")

# cv2.setMouseCallback(WIN, on_mouse)

# print("Instructions:")
# print("1) Click TOP-LEFT of the surface where bottles sit (inside the ROI window).")
# print("2) Click BOTTOM-RIGHT of that same surface.")
# print("Keys: R reset clicks | S save config.json | Q quit")

# while True:
#     ok, frame = cap.read()
#     if not ok or frame is None:
#         continue

#     h, w = frame.shape[:2]
#     x1 = clamp(X1, 0, w-1); y1 = clamp(Y1, 0, h-1)
#     x2 = clamp(X2, 1, w);   y2 = clamp(Y2, 1, h)
#     roi = frame[y1:y2, x1:x2].copy()
#     last_roi = roi

#     # draw clicks
#     for pt in clicks:
#         cv2.circle(roi, pt, 6, (0, 255, 255), -1)

#     # draw grid if we have 2 points
#     slots = []
#     if len(clicks) == 2:
#         (tlx, tly), (brx, bry) = clicks
#         tlx, brx = sorted([tlx, brx])
#         tly, bry = sorted([tly, bry])

#         # clamp within ROI
#         H, W = roi.shape[:2]
#         tlx = clamp(tlx, 0, W-1); brx = clamp(brx, 1, W)
#         tly = clamp(tly, 0, H-1); bry = clamp(bry, 1, H)

#         # draw bounding rect
#         cv2.rectangle(roi, (tlx, tly), (brx, bry), (0, 255, 0), 2)

#         cell_w = (brx - tlx) / GRID_COLS
#         cell_h = (bry - tly) / GRID_ROWS

#         # grid lines + slot rectangles
#         for r in range(GRID_ROWS):
#             for c in range(GRID_COLS):
#                 sx1 = int(tlx + c * cell_w)
#                 sy1 = int(tly + r * cell_h)
#                 sx2 = int(tlx + (c + 1) * cell_w)
#                 sy2 = int(tly + (r + 1) * cell_h)

#                 cv2.rectangle(roi, (sx1, sy1), (sx2, sy2), (255, 255, 255), 1)
#                 slot_id = f"c{c+1}_d{r+1}"  # c=SKU column, d=depth row
#                 cv2.putText(roi, slot_id, (sx1 + 5, sy1 + 20),
#                             cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)

#                 slots.append({
#                     "id": slot_id,
#                     "col": c+1,
#                     "depth": r+1,
#                     "x1": sx1, "y1": sy1, "x2": sx2, "y2": sy2
#                 })

#     cv2.imshow(WIN, roi)
#     key = cv2.waitKey(1) & 0xFF

#     if key in (ord('q'), ord('Q')):
#         break

#     if key in (ord('r'), ord('R')):
#         clicks = []
#         print("Reset clicks.")

#     if key in (ord('s'), ord('S')):
#         if len(clicks) != 2:
#             print("Need 2 clicks before saving.")
#             continue
#         config = {
#             "rtsp": {
#                 "ip": IP, "port": PORT, "channel": CHANNEL, "subtype": SUBTYPE
#             },
#             "roi": {"x1": X1, "y1": Y1, "x2": X2, "y2": Y2},
#             "surface_bbox": {"tl": clicks[0], "br": clicks[1]},
#             "grid": {"cols": GRID_COLS, "rows": GRID_ROWS},
#             "slots": slots,
#             # Optional: name your SKUs by column later:
#             "sku_by_col": {"1": "SKU_LEFT", "2": "SKU_MIDDLE", "3": "SKU_RIGHT"}
#         }
#         with open("config.json", "w") as f:
#             json.dump(config, f, indent=2)
#         print("Saved config.json")

# cap.release()
# cv2.destroyAllWindows()
# print("Done.")
