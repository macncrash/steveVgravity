"""Render the Blowball Station story into ../ (stage stills, berthing video, full-bloom hero shots).

python3 render_all.py [stages|berthing|hero|all]

Geometry: the flight segment is STEVE's own exported mesh (assets/segment). STEVE can't export print meshes for
the full station or the lofted orbiter, so those are tessellated locally from the same code and parameters as the
STEVE documents (station_mesh.py, orbiter_mesh.py).
"""
import json
import math
import os
import shutil
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import station_mesh as M  # noqa: E402
from orbiter_mesh import orbiter_bodies  # noqa: E402
from params import shuttle_stretch  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "analysis"))
import mass_budget as MB  # noqa: E402  (analysis/MASS_BUDGET.md: masses and CoM per launch)
from render_mesh import Scene, load_stl, rot_axis  # noqa: E402

G = M.G
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, ".."))
ASSETS = os.path.join(HERE, "assets")
SEG_LEN = 2900
STEVE_LINK = "STEVE: stevecad.studio/?document=286c0cf5-6549-4e47-bcd1-7aaa2fd70bf3"


# ---------------- STEVE meshes ----------------
def _load_asset(name):
    meta = json.load(open(os.path.join(ASSETS, name, "bodies.json")))
    return [(load_stl(os.path.join(ASSETS, name, "bodies", f"{b['index']}.stl")), b["color"], b.get("gloss", 0.2), b.get("bias", 0))
            for b in meta]


SEGMENT = _load_asset("segment")
SHUTTLE = orbiter_bodies(stretch=shuttle_stretch)   # the New Shuttle


def shuttle_bodies():
    """New Shuttle docked on pod 0: orbiter-local (x, y, z) -> (x - 8300, -y, -z + r_port + 3100)."""
    R = np.diag([1.0, -1.0, -1.0])
    t = np.array([-G.ORB_DOCK_X, 0, G.r_port + G.ORB_DOCK_Z])
    return [(tr @ R.T + t, c, g, b, cull) for tr, c, g, b, cull in SHUTTLE]


def _chain(legs, vals, pts):
    """Apply the berthing joint chain (lift, side, out, swing, in, turn) to points at the modelled pose."""
    x = pts
    for (name, kind, (p, d), _), v in reversed(list(zip(legs, vals))):
        if kind == "slider":
            x = x + np.asarray(d) * v
        else:
            p = np.asarray(p)
            x = (x - p) @ rot_axis(d, v).T + p
    return x


def segment_bodies(stow, legs=None, vals=None):
    """A flight segment placed in the bay (rolled 180 deg about X, centre at `stow`), moved by the arm legs."""
    R = np.diag([1.0, -1.0, -1.0])
    t = np.array([stow[0] - SEG_LEN / 2, stow[1], stow[2]])
    out = []
    for tr, c, g, b in SEGMENT:
        w = tr @ R.T + t
        if legs is not None:
            w = _chain(legs, vals, w.reshape(-1, 3)).reshape(-1, 3, 3)
        out.append((w, c, g, b))
    return out


# ---------------- numbers for captions ----------------
def stats(built):
    """Pods, pressurised volume, solar power; mass and centre-of-mass offset from analysis/mass_budget.py."""
    L = len(built)
    _, mass_t, com = MB.com_by_launch()[L - 1]
    vol = len(built) * math.pi * (M.pod_r / 1000) ** 2 * (G.pod_len / 1000) + 4 / 3 * math.pi * (M.hub_r / 1000) ** 3
    blooms = len([q for q in built if q != 0])
    return dict(pods=L, vol=vol, kw_peak=blooms * 40, kw_avg=blooms * 23, com=com, mass=mass_t)


def scene_for(built, extra=(), shuttle=True, disc_bias=3000):
    s = Scene()
    for tris, col, gl in M.station_bodies(built):
        s.add(tris, col, gloss=gl, max_edge=1500, bias=disc_bias if col == M.COL["disc"] else 0)
    if shuttle and 0 in built:
        for tris, col, gl, b, cull in shuttle_bodies():
            s.add(tris, col, gloss=gl, max_edge=1500, bias=b, cull=cull)
    for tris, col, gl, b in extra:
        s.add(tris, col, gloss=gl, max_edge=900, bias=b)
    return s


HERO_EYE = (100e3, -125e3, 70e3)


# ---------------- 1. launch-by-launch stages ----------------
def render_stages():
    for L in range(1, len(G.ORDER) + 1):
        built = set(G.ORDER[:L])
        st = stats(built)
        new = G.ORDER[L - 1]
        what = "hub + docking pod (pod 0) on one heavy-lift launch" if L == 1 else \
            f"pod {new} berthed ({'opposite pair complete' if L % 2 == 0 else 'opens a new opposite pair'})"
        s = scene_for(built, shuttle=L >= 2)          # launch 1 is the heavy-lift hub flight; the Shuttle visits from launch 2
        s.render(f"{OUT}/stage_{L:02d}.png", eye=HERO_EYE, target=(0, 0, 4e3), fov=36,
                 title=f"Launch {L} of {len(G.ORDER)}: {what}",
                 subtitle=f"{st['pods']} pods · {st['mass']:,.0f} t · {st['vol']:,.0f} m³ pressurised · ~{st['kw_avg']} kW orbit-average "
                          f"solar · centre of mass {st['com']:.1f} m off the hub",
                 footer="Order: opposite pairs (decussate leaves / phyllotaxis inhibitor rule) · " + STEVE_LINK)
        print("stage", L, round(st["com"], 2))


# ---------------- 2. berthing sequence (launch 6) ----------------
def render_berthing(L=6, dt=0.25):
    G.ARRIVING = G.ORDER[L - 1]
    built = set(G.ORDER[:L]) - {G.ARRIVING}
    plan = G.berthing_plan()
    timing = {"lift": 1.5, "side": 3, "out": 6, "swing": 9, "turn": 9, "in": 12}
    frames_dir = os.path.join(HERE, "..", "..", ".berthing_frames")
    os.makedirs(frames_dir, exist_ok=True)
    total = 12.5 * len(plan) + 1
    stills = {round(x, 2) for x in (1.0, 4.5, 7.5, 10.5, 12.5, 50.0, 87.5)}
    f = 0
    t = 0.0
    while t <= total + 1e-9:
        extra = []
        for j, (s0, legs) in enumerate(plan):
            local = t - 12.5 * j
            vals = []
            for name, _, _, travel in legs:
                end = timing[name]
                prev = max([v for v in timing.values() if v < end], default=0.0)
                if name == "turn":
                    prev = 6.0
                u = min(1.0, max(0.0, (local - prev) / (end - prev)))
                u = u * u * (3 - 2 * u)                                    # ease in/out
                vals.append(travel * u)
            extra += segment_bodies(s0, legs, vals)
        seg_no = min(len(plan), int(t // 12.5) + 1)
        sc = scene_for(built, extra)
        path = f"{frames_dir}/f_{f:04d}.png"
        sc.render(path, eye=(112e3, 40e3, 42e3), target=(0, 6e3, 4e3), fov=44, size=(1280, 800),
                  title=f"Launch {L}: berthing pod {G.ARRIVING}, segment {seg_no} of 7",
                  subtitle="New Shuttle docked on the axial pod · station arm: lift out of the bay → step clear → swing round "
                           "the outside → slide in along the pod axis",
                  footer=f"t = {t:5.1f} s (animation 'berthing' in STEVE) · paths checked offline: ≥ 0.32 m clear")
        if round(t, 2) in stills:
            shutil.copy(path, f"{OUT}/berthing_t{int(round(t * 10)):04d}.png")
        f += 1
        t += dt
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "24", "-i", f"{frames_dir}/f_%04d.png",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", f"{OUT}/berthing_launch{L:02d}.mp4"], check=True)
    print("berthing frames", f)


# ---------------- 3. the thesis: one blowball, full bloom ----------------
def render_hero():
    built = set(G.ORDER)
    st = stats(built)
    cap = (f"12 pods × 7 Spacelab segments · {st['vol']:,.0f} m³ pressurised (≈3× ISS) · 11 solar blooms "
           f"~{st['kw_peak']} kW peak / ~{st['kw_avg']} kW average · ~{st['mass']:.0f} t (analysis/MASS_BUDGET.md)")
    views = [
        ("hero_01_full_bloom", HERO_EYE, (0, 0, 4e3), 36, "One blowball: the station in full bloom", True),
        ("hero_02_sunward", (150e3, 20e3, 25e3), (0, 0, 2e3), 38, "Sunward face: every bloom turned to the sun", False),
        ("hero_03_from_below", (40e3, -90e3, -110e3), (0, 0, 0), 40, "From below: the seed head", False),
        ("hero_04_docking_axis", (35e3, -45e3, 55e3), (-4e3, 0, 26e3), 42, "New Shuttle on the axial docking pod", False),
    ]
    for name, eye, tgt, fov, title, earth in views:
        sc = scene_for(built, disc_bias=3000 if eye[0] > 0 else -3000)
        sc.render(f"{OUT}/{name}.png", eye=eye, target=tgt, fov=fov, size=(1920, 1200), title=title, subtitle=cap,
                  earth=earth, footer="Gravity sim → STEVE CAD · layout: repulsion-packed sphere (Tammes) · " + STEVE_LINK)
        print("hero", name)


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what in ("stages", "all"):
        render_stages()
    if what in ("hero", "all"):
        render_hero()
    if what in ("berthing", "all"):
        render_berthing()
