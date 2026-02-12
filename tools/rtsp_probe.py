"""
rtsp_probe.py
- Tries common RTSP URL formats across channels
- Confirms Python/OpenCV can grab at least one frame
- Saves an image like probe_success_ch5.jpg
"""

import os
import cv2
from urllib.parse import quote
from pathlib import Path

# settings.py should load .env and expose these variables:
# USER, PASS, IP, PORT
from settings import USER, PASS, IP, PORT

# Force RTSP over TCP (more reliable)
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|stimeout;3000000"

USER_ENC = quote(str(USER), safe="")
PASS_ENC = quote(str(PASS), safe="")

def urls_for_channel(ch: int):
    """
    Lorex/Dahua-style RTSP URL patterns (common).
    We never print credentials; only the safe portion after '@'.
    """
    return [
        f"rtsp://{USER_ENC}:{PASS_ENC}@{IP}:{PORT}/cam/realmonitor?channel={ch}&subtype=1",
        f"rtsp://{USER_ENC}:{PASS_ENC}@{IP}:{PORT}/cam/realmonitor?channel={ch}&subtype=0",
        f"rtsp://{USER_ENC}:{PASS_ENC}@{IP}:{PORT}/Streaming/Channels/{ch}01",
    ]

def try_open(url: str):
    cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
    if not cap.isOpened():
        cap.release()
        return False, None
    ok, frame = cap.read()
    cap.release()
    if not ok or frame is None:
        return False, None
    return True, frame

print("Probing RTSP URLs... (printing safe URL parts only)")

out_dir = Path(".")
for ch in range(1, 9):
    for url in urls_for_channel(ch):
        ok, frame = try_open(url)

        safe_url = url.split("@")[-1]
        print(("OK  " if ok else "FAIL"), "ch", ch, "-", safe_url)

        if ok:
            out = out_dir / f"probe_success_ch{ch}.jpg"
            cv2.imwrite(str(out), frame)
            print(f"\nSUCCESS on channel {ch} -> saved {out.name}")
            raise SystemExit(0)

print("\nNo URL worked.")
