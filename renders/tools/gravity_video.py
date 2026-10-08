"""Turn a gravity_record.mjs recording into PNG frames (glowing points, orbiting camera) and an MP4.

python3 gravity_video.py <recording.bin> <out_dir> <out.mp4> [stills: comma-separated frame numbers]
"""
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

rec, out_dir, mp4 = sys.argv[1:4]
stills = [int(s) for s in sys.argv[4].split(",")] if len(sys.argv) > 4 else []
W, H = 1280, 720

raw = open(rec, "rb").read()
n, frames = np.frombuffer(raw[:8], dtype=np.int32)
col = np.frombuffer(raw[8:8 + n * 12], dtype=np.float32).reshape(n, 3)
pos_all = np.frombuffer(raw[8 + n * 12:], dtype=np.float32).reshape(frames, n, 3)
os.makedirs(out_dir, exist_ok=True)
try:
    font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 20)
    fbig = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 26)
except Exception:
    font = fbig = None

rng = np.random.default_rng(3)
stars = np.stack([rng.uniform(0, W, 700), rng.uniform(0, H, 700), rng.uniform(0.15, 0.7, 700)], axis=1)

for f in range(frames):
    p = pos_all[f]
    live = np.any(p != 0, axis=1)
    p, c = p[live], col[live]
    az = math.radians(35 + 40 * f / frames)          # slow orbit
    el = math.radians(18)
    dist = 46.0
    eye = np.array([dist * math.cos(el) * math.cos(az), dist * math.sin(el) + 2, dist * math.cos(el) * math.sin(az)])
    tgt = np.array([0.0, 4.0, 0.0])
    fwd = tgt - eye; fwd /= np.linalg.norm(fwd)
    right = np.cross(fwd, [0, 1, 0]); right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    rel = p - eye
    z = rel @ fwd
    x = W / 2 + (H * 1.05) * (rel @ right) / z
    y = H / 2 - (H * 1.05) * (rel @ up) / z
    ok = (z > 1) & (x >= 0) & (x < W - 1) & (y >= 0) & (y < H - 1)
    xi, yi, cc = x[ok].astype(int), y[ok].astype(int), c[ok]
    img = np.zeros((H, W, 3), dtype=np.float32)
    for k in range(3):
        np.add.at(img[:, :, k], (yi, xi), cc[:, k] * 0.9)
    for sx, sy, sb in stars:
        img[int(sy), int(sx)] += sb * 0.6
    core = np.clip(img, 0, 1)
    glow = np.asarray(Image.fromarray((core * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3)), dtype=np.float32) / 255
    frame = np.clip(core + 0.9 * glow + np.array([0.015, 0.03, 0.06]), 0, 1)
    im = Image.fromarray((frame * 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    d.text((24, 20), "Blowball Station: assembly time-lapse (Gravity sim)", fill=(230, 236, 246), font=fbig)
    d.text((24, 56), "launch 1: hub + docking pod, then one 7-segment pod per launch, opposite pairs; magenta = centre of mass",
           fill=(150, 168, 196), font=font)
    im.save(f"{out_dir}/frame_{f:04d}.png")
    if f in stills:
        im.save(f"{os.path.dirname(mp4)}/gravity_timelapse_{f:04d}.png")

subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "30", "-i", f"{out_dir}/frame_%04d.png",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", mp4], check=True)
print("wrote", mp4, frames, "frames")
