"""Tessellate the Blowball Station locally, body for body, from the same parameters and geometry code as the
STEVE design (station/ holds a copy of its params.py, blowball_layout.py and station_geometry.py).

Used for colour renders because STEVE can't export per-body meshes for the full ~480-solid assembly.
Every primitive here mirrors one feature in the STEVE components (hub.py, arms.py, blooms.py, radiators.py).
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "station"))
import station_geometry as G  # noqa: E402
from params import (bloom_d, cone_len, cone_r, hub_r, mast, pod_r, rad_w, seg_len, segments,  # noqa: E402
                    tunnel_r)

COL = {
    "hub": "#eceae3", "collar": "#a7adb5", "tunnel": "#d9a441", "pod": "#efece4", "flange": "#a7adb5",
    "dock": "#a7adb5", "disc": "#1b2f6e", "spar": "#e9edf2", "mast": "#8e959e", "fin": "#f5f6f7", "strut": "#a7adb5",
}


def _orient(tris, center):
    """Make every triangle's winding face away from `center` (all primitives here are convex)."""
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    out = tris.mean(axis=1) - np.asarray(center)
    flip = (n * out).sum(axis=1) < 0
    tris[flip] = tris[flip][:, [0, 2, 1]]
    return tris


def _basis(d):
    d = np.asarray(d, dtype=float)
    d = d / np.linalg.norm(d)
    a = np.array([0, 0, 1.0]) if abs(d[2]) < 0.9 else np.array([1.0, 0, 0])
    u = np.cross(a, d)
    u /= np.linalg.norm(u)
    return d, u, np.cross(d, u)


def frustum(r1, r2, h, at, direction, seg=40):
    """Cylinder (r1 == r2) or cone frustum from `at` along `direction`, with caps."""
    d, u, v = _basis(direction)
    at = np.asarray(at, dtype=float)
    t = np.linspace(0, 2 * math.pi, seg, endpoint=False)
    ring = np.cos(t)[:, None] * u + np.sin(t)[:, None] * v
    a, b = at + r1 * ring, at + h * d + r2 * ring
    a2, b2 = np.roll(a, -1, axis=0), np.roll(b, -1, axis=0)
    side = np.concatenate([np.stack([a, a2, b2], 1), np.stack([a, b2, b], 1)])
    c0, c1 = np.repeat(at[None], seg, 0), np.repeat((at + h * d)[None], seg, 0)
    caps = np.concatenate([np.stack([c0, a2, a], 1), np.stack([c1, b, b2], 1)])
    return _orient(np.concatenate([side, caps]), at + d * h / 2)


def box(center, axes, dims):
    """Box centred at `center` with edge directions `axes` (3 unit vectors) and lengths `dims`."""
    c = np.asarray(center, dtype=float)
    A = [np.asarray(a, dtype=float) * (s / 2) for a, s in zip(axes, dims)]
    corner = lambda i, j, k: c + i * A[0] + j * A[1] + k * A[2]
    quads = []
    for ax in range(3):
        for sgn in (-1, 1):
            o = [x for x in range(3) if x != ax]
            pts = []
            for p, q in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                idx = [0, 0, 0]
                idx[ax], idx[o[0]], idx[o[1]] = sgn, p, q
                pts.append(corner(*idx))
            quads.append(np.stack([pts[0], pts[1], pts[2]]))
            quads.append(np.stack([pts[0], pts[2], pts[3]]))
    return _orient(np.array(quads), c)


def prism_polygon(center, normal, radius, sides, thickness):
    """Regular polygon of `sides` around `center` in the plane normal to `normal`, extruded `thickness` along it."""
    n, u, v = _basis(normal)
    c = np.asarray(center, dtype=float)
    t = np.linspace(0, 2 * math.pi, sides, endpoint=False)
    ring = c + radius * (np.cos(t)[:, None] * u + np.sin(t)[:, None] * v)
    top = ring + thickness * n
    r2, t2 = np.roll(ring, -1, 0), np.roll(top, -1, 0)
    cc0, cc1 = np.repeat(c[None], sides, 0), np.repeat((c + thickness * n)[None], sides, 0)
    tris = np.concatenate([np.stack([ring, r2, t2], 1), np.stack([ring, t2, top], 1),
                           np.stack([cc0, r2, ring], 1), np.stack([cc1, top, t2], 1)])
    return _orient(tris, c + n * thickness / 2)


def hub_sphere(seg=24, turns=48):
    """Revolved 24-sided half polygon (as in hub.py)."""
    ph = np.linspace(0, math.pi, seg + 1)
    th = np.linspace(0, 2 * math.pi, turns + 1)
    P = hub_r * np.stack([np.sin(ph)[:, None] * np.cos(th)[None], np.sin(ph)[:, None] * np.sin(th)[None],
                          np.repeat(np.cos(ph)[:, None], turns + 1, 1)], axis=2)
    tris = []
    for i in range(seg):
        for j in range(turns):
            a, b, c, d = P[i, j], P[i, j + 1], P[i + 1, j + 1], P[i + 1, j]
            tris += [[a, b, c], [a, c, d]]
    return _orient(np.array(tris), (0, 0, 0))


def station_bodies(built, with_hub=True):
    """[(triangles, colour, gloss)] for the hub and every pod in `built` (pods, blooms, radiators, docking pod)."""
    out = []
    at = G.at
    if with_hub:
        out.append((hub_sphere(), COL["hub"], 0.1))
        for D in G.DIRS:                                                       # the hub carries all 12 collars
            out.append((frustum(tunnel_r + 300, tunnel_r + 300, 450, at(D, hub_r - 200), D), COL["collar"], 0.3))
    for i in sorted(built):
        D = G.DIRS[i]
        out.append((frustum(tunnel_r, tunnel_r, G.r0 - hub_r + 250, at(D, hub_r - 200), D, 24), COL["tunnel"], 0.2))
        out.append((frustum(pod_r, pod_r, segments * seg_len, at(D, G.r0), D, 48), COL["pod"], 0.05))
        for j in range(segments + 1):
            out.append((frustum(pod_r + 50, pod_r + 50, 60, at(D, G.r0 + j * seg_len - 30), D, 48), COL["flange"], 0.3))
        out.append((frustum(pod_r, cone_r, cone_len, at(D, G.r_tip), D, 48), COL["pod"], 0.05))
        out.append((frustum(tunnel_r, pod_r, cone_len, at(D, G.r0 - cone_len), D, 48), COL["pod"], 0.05))  # root flare
        # radiators: two fins edge-on to the sun, plus struts
        d, w, n = G.edge_on_frame(D)
        L = 0.6 * G.pod_len
        mid = G.r0 + 0.65 * G.pod_len
        off = pod_r + 400 + rad_w / 2
        for sgn in (1, -1):
            centre = tuple(D[k] * mid + w[k] * sgn * off for k in range(3))
            out.append((box(centre, (d, w, n), (L, rad_w, 80)), COL["fin"], 0.5))
            for frac in (0.45, 0.85):
                base = tuple(D[k] * (G.r0 + frac * G.pod_len) + w[k] * sgn * (pod_r - 50) for k in range(3))
                out.append((frustum(90, 90, 450, base, tuple(w[k] * sgn for k in range(3)), 12), COL["strut"], 0.3))
        if i == 0:   # docking adapter + NDS ring
            out.append((frustum(1000, 1000, 1100, at(D, G.r_cone), D), COL["pod"], 0.05))
            out.append((frustum(1100, 1100, 200, at(D, G.r_cone + 1100), D), COL["dock"], 0.4))
            out.append((frustum(850, 850, 300, at(D, G.r_cone + 1300), D), COL["dock"], 0.4))
            continue
        # bloom: mast, gimbal, 24-gore disc face-on to the sun, 12 spars
        R = bloom_d / 2
        c = at(D, G.r_cone + mast)
        out.append((frustum(250, 250, mast, at(D, G.r_cone), D, 16), COL["mast"], 0.3))
        out.append((frustum(450, 450, 500, tuple(c[k] - G.SUN[k] * 500 for k in range(3)), G.SUN, 24), COL["mast"], 0.3))
        out.append((prism_polygon(c, G.SUN, R, 24, 60), COL["disc"], 0.9))
        for g in range(12):
            a = 2 * math.pi * g / 12
            uu = (0.0, math.cos(a), math.sin(a))
            out.append((frustum(70, 70, R, tuple(c[k] - G.SUN[k] * 70 for k in range(3)), uu, 8), COL["spar"], 0.3))
    return out
