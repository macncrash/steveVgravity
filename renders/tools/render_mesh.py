"""Tiny software renderer for STEVE body meshes (binary STL per body) — painter's algorithm with Pillow.

Usage from Python:
    from render_mesh import load_stl, Scene
    scene = Scene()
    scene.add(load_stl("bodies/0.stl"), "#efece4")
    scene.render("out.png", eye=(60e3, -80e3, 50e3), target=(0, 0, 0), up=(0, 0, 1), fov=40)

Meshes are in STEVE's frame (mm, Z up). Lighting: a sun along +X (the station's sun line) plus a soft fill.
"""
import math
import struct

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def load_stl(path):
    """Triangles (n, 3, 3) float32 from a binary or ASCII STL."""
    data = open(path, "rb").read()
    if len(data) >= 84:
        n = struct.unpack("<I", data[80:84])[0]
        if 84 + n * 50 == len(data):
            rec = np.frombuffer(data, dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]), count=n, offset=84)
            return rec["v"].astype(np.float64)
    tris, cur = [], []
    for line in data.decode("ascii", "ignore").splitlines():
        p = line.split()
        if p and p[0] == "vertex":
            cur.append([float(x) for x in p[1:4]])
            if len(cur) == 3:
                tris.append(cur)
                cur = []
    return np.array(tris, dtype=np.float64).reshape(-1, 3, 3)


def subdivide(tris, max_edge):
    """Split triangles longer than max_edge (longest-edge bisection, repeated) so depth sorting works finely."""
    out = []
    t = np.asarray(tris, dtype=np.float64)
    for _ in range(12):
        e = np.stack([np.linalg.norm(t[:, 1] - t[:, 0], axis=1), np.linalg.norm(t[:, 2] - t[:, 1], axis=1),
                      np.linalg.norm(t[:, 0] - t[:, 2], axis=1)], axis=1)
        big = e.max(axis=1) > max_edge
        out.append(t[~big])
        if not big.any():
            break
        t, e = t[big], e[big]
        k = e.argmax(axis=1)                               # bisect the longest edge: (a, b) with c opposite
        a = t[np.arange(len(t)), k]
        b = t[np.arange(len(t)), (k + 1) % 3]
        c = t[np.arange(len(t)), (k + 2) % 3]
        m = (a + b) / 2
        t = np.concatenate([np.stack([a, m, c], axis=1), np.stack([m, b, c], axis=1)])
    else:
        out.append(t)
    return np.concatenate(out)


def hex_rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float64) / 255.0


def transform(tris, rot=None, trans=(0, 0, 0)):
    """Apply a 3x3 rotation then a translation to (n, 3, 3) triangles."""
    out = tris if rot is None else tris @ np.asarray(rot).T
    return out + np.asarray(trans, dtype=np.float64)


def rot_axis(axis, deg):
    a = np.asarray(axis, dtype=np.float64)
    a = a / np.linalg.norm(a)
    t = math.radians(deg)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + math.sin(t) * K + (1 - math.cos(t)) * (K @ K)


class Scene:
    def __init__(self):
        self.tris, self.cols, self.gloss, self.bias, self.cull = [], [], [], [], []

    def add(self, tris, color, gloss=0.0, max_edge=None, bias=0.0, cull=True):
        """bias (mm): drawn as if this much nearer, for thin details lying on another body (hatches, decals)."""
        if len(tris):
            tris = np.asarray(tris, dtype=np.float64)
            if max_edge:
                tris = subdivide(tris, max_edge)
            self.tris.append(tris)
            self.cols.append(np.tile(hex_rgb(color) if isinstance(color, str) else np.asarray(color), (len(tris), 1)))
            self.gloss.append(np.full(len(tris), gloss))
            self.bias.append(np.full(len(tris), bias))
            self.cull.append(np.full(len(tris), cull))

    def render(self, path, eye, target=(0, 0, 0), up=(0, 0, 1), fov=40.0, size=(1600, 1000), ss=2,
               bg=(4, 8, 18), stars=True, title=None, subtitle=None, sun=(1.0, -0.25, 0.35), earth=False, footer=None):
        T = np.concatenate(self.tris)
        C = np.concatenate(self.cols)
        G = np.concatenate(self.gloss)
        B = np.concatenate(self.bias)
        K = np.concatenate(self.cull)
        eye, target, up = (np.asarray(v, dtype=np.float64) for v in (eye, target, up))
        f = target - eye
        f /= np.linalg.norm(f)
        r = np.cross(f, up)
        r /= np.linalg.norm(r)
        u = np.cross(r, f)
        W, H = size[0] * ss, size[1] * ss
        focal = (H / 2) / math.tan(math.radians(fov) / 2)

        rel = T - eye
        x = rel @ r
        y = rel @ u
        z = rel @ f                                   # depth along the view
        keep = (z > 1.0).all(axis=1)
        x, y, z, C, G, B, K, Tk = x[keep], y[keep], z[keep], C[keep], G[keep], B[keep], K[keep], T[keep]
        px = W / 2 + focal * x / z
        py = H / 2 - focal * y / z

        # shading: two-sided Lambert from a sun direction + fill + a little specular for glossy bodies
        n = np.cross(Tk[:, 1] - Tk[:, 0], Tk[:, 2] - Tk[:, 0])
        nn = np.linalg.norm(n, axis=1)
        nn[nn == 0] = 1
        n /= nn[:, None]
        view = -(Tk.mean(axis=1) - eye)
        view /= np.linalg.norm(view, axis=1)[:, None]
        facing = (n * view).sum(axis=1) > 0
        front = facing | ~K                          # closed solids, outward winding: drop back faces (unless cull=False)
        n[~facing] *= -1                             # double-sided bodies: shade the side we see
        n, view, Tk, px, py, z, C, G, B = n[front], view[front], Tk[front], px[front], py[front], z[front], C[front], G[front], B[front]
        L = np.asarray(sun, dtype=np.float64)
        L /= np.linalg.norm(L)
        diff = np.clip(n @ L, 0, 1)
        fill = 0.5 + 0.5 * n[:, 2]
        h = L + view
        h /= np.linalg.norm(h, axis=1)[:, None]
        spec = np.clip((n * h).sum(axis=1), 0, 1) ** 40 * G
        shade = 0.16 + 0.70 * diff + 0.14 * fill
        rgb = np.clip(C * shade[:, None] + spec[:, None] * 0.6, 0, 1)

        order = np.argsort(-(z.mean(axis=1) - B))     # far to near
        img = Image.new("RGB", (W, H), bg)
        if stars:
            rng = np.random.default_rng(7)
            d = ImageDraw.Draw(img)
            for sx, sy, sb in zip(rng.uniform(0, W, 900), rng.uniform(0, H, 900), rng.uniform(60, 220, 900)):
                d.point((sx, sy), fill=(int(sb), int(sb), int(sb * 1.05)))
        if earth:   # an Earth limb across the bottom of the frame, with a thin atmosphere glow
            d = ImageDraw.Draw(img)
            R = W * 1.6
            cx, cy = W * 0.35, H * 0.86 + R
            for k, colr in enumerate([(40, 110, 200), (70, 150, 235), (120, 190, 255)]):
                d.ellipse((cx - R - 18 + k * 6, cy - R - 18 + k * 6, cx + R + 18 - k * 6, cy + R + 18 - k * 6), fill=colr)
            d.ellipse((cx - R, cy - R, cx + R, cy + R), fill=(18, 52, 98))
            img = img.filter(ImageFilter.GaussianBlur(1.5 * ss))
        draw = ImageDraw.Draw(img)
        P = np.stack([px, py], axis=2)
        cols = (rgb * 255).astype(np.uint8)
        for i in order:
            pts = P[i]
            if np.abs(pts).max() > 1e6:
                continue
            c = tuple(int(v) for v in cols[i])
            draw.polygon([tuple(p) for p in pts], fill=c, outline=c)
        img = img.resize(size, Image.LANCZOS)
        if title or subtitle:
            d = ImageDraw.Draw(img)
            try:
                from PIL import ImageFont
                ft = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 30)
                fs = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 20)
            except Exception:
                ft = fs = None
            if title:
                d.text((28, 22), title, fill=(232, 238, 248), font=ft)
            if subtitle:
                for k, line in enumerate(subtitle.split("\n")):
                    d.text((28, 62 + 26 * k), line, fill=(150, 168, 196), font=fs)
        if footer:
            d = ImageDraw.Draw(img)
            try:
                from PIL import ImageFont
                ff = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 16)
            except Exception:
                ff = None
            d.text((28, size[1] - 34), footer, fill=(110, 126, 150), font=ff)
        img.save(path)
        return path
