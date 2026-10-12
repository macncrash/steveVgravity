"""Bring assets/segment up to STEVE Flight Segment revision 5 (the berthing ring) by local tessellation.

python3 segment_rev5.py

Bodies 0-30 are STEVE's own export of revision 4. Revision 5 changed the flanges (seal groove, bolt holes) and the
hatches (1.27 m), and added bodies 31-66 (seals, lands, utility plates, bolts, umbilical adapters). Those are written
here from the same dimensions as steve/flight_segment/main.py, with the same body indices and colours as STEVE.
The face layer is tiled so no two bodies overlap (the flange is an annulus outside the seal, the land fills only what
the hatch and the utility plates leave), because the painter's renderer sorts whole triangles and coplanar overlaps
flicker. Only the bolt heads lie on another body, so only they carry a depth bias.
"""
import json
import math
import os
import struct

import numpy as np

from station_mesh import box, frustum

HERE = os.path.dirname(os.path.abspath(__file__))
SEG = os.path.join(HERE, "assets", "segment")
R, SHELL, FL = 2030, 2700, 100
L = SHELL + 2 * FL
HT, HW = 20, 1270
RS, RB, NB, FD = 1000, 1100, 20, 10
X = ((1, 0, 0), (0, 1, 0), (0, 0, 1))


def ring(r_out, r_in, x0, h, seg=72):
    """Flat annulus from x0 along +X (inner and outer walls, both faces), double-sided."""
    t = np.linspace(0, 2 * math.pi, seg, endpoint=False)
    t2 = np.roll(t, -1)
    out = []
    for a, b in zip(t, t2):
        p = lambda r, x, ang: (x, r * math.cos(ang), r * math.sin(ang))
        for x in (x0, x0 + h):
            out += [(p(r_in, x, a), p(r_out, x, a), p(r_out, x, b)), (p(r_in, x, a), p(r_out, x, b), p(r_in, x, b))]
        for r in (r_in, r_out):
            out += [(p(r, x0, a), p(r, x0, b), p(r, x0 + h, b)), (p(r, x0, a), p(r, x0 + h, b), p(r, x0 + h, a))]
    out = np.array(out)
    return np.concatenate([out, out[:, [0, 2, 1]]])      # both windings: the annulus is not convex, so no culling


def land(x0, h, step=20.0):
    """The land: inside the seal, outside the square hatch and the four utility plates; tiled in each of the four
    spaces as strips across the space (u: distance from the axis along the space's centre line, v: across it)."""
    lo, r_in, pu, pv = HW / 2, RS - 20, (710.0, 890.0), 350.0
    quads = []
    for k in range(4):
        a = math.pi / 2 - k * math.pi / 2
        eu, ev = np.array([0, math.cos(a), math.sin(a)]), np.array([0, -math.sin(a), math.cos(a)])
        vmax = math.sqrt(r_in ** 2 - lo ** 2)
        vs = np.linspace(-vmax, vmax, int(2 * vmax / step) + 1)
        for v0, v1 in zip(vs[:-1], vs[1:]):
            vm = (v0 + v1) / 2
            u_out = math.sqrt(max(r_in ** 2 - vm ** 2, lo ** 2))
            spans = [(lo, pu[0]), (pu[1], u_out)] if abs(vm) < pv else [(lo, u_out)]
            for u0, u1 in spans:
                if u1 > u0:
                    quads.append([u0 * eu + v0 * ev, u1 * eu + v0 * ev, u1 * eu + v1 * ev, u0 * eu + v1 * ev])
    q = np.array(quads)
    tris = []
    for x in (x0, x0 + h):
        qq = q + np.array([x, 0, 0])
        tris += [qq[:, [0, 1, 2]], qq[:, [0, 2, 3]]]
    t = np.concatenate(tris)
    return np.concatenate([t, t[:, [0, 2, 1]]])


def write_stl(path, tris):
    tris = np.asarray(tris, dtype=np.float32)
    with open(path, "wb") as f:
        f.write(b"segment_rev5 local tessellation".ljust(80, b" "))
        f.write(struct.pack("<I", len(tris)))
        for t in tris:
            n = np.cross(t[1] - t[0], t[2] - t[0])
            n = n / (np.linalg.norm(n) or 1)
            f.write(struct.pack("<12fH", *n, *t.ravel(), 0))


bodies = {}   # index -> (tris, colour, gloss, bias)
bodies[1] = (ring(R + 50, RS + 20, 0, FL, 96), "#a7adb5", 0.3, 0)
bodies[2] = (ring(R + 50, RS + 20, FL + SHELL, FL, 96), "#7d848d", 0.3, 0)
bodies[19] = (box((HT / 2, 0, 0), X, (HT, HW, HW)), "#3a4048", 0.2, 0)
bodies[20] = (box((L - HT / 2, 0, 0), X, (HT, HW, HW)), "#3a4048", 0.2, 0)
i = 31
for side, x0 in (("passive", 0), ("active", L - FD)):
    bodies[i] = (ring(RS + 20, RS - 20, x0, FD), "#1c1d20", 0.1, 0)
    bodies[i + 1] = (land(x0, FD), "#c4c9cf", 0.3, 0)
    for k in range(4):
        a = math.pi / 2 - k * math.pi / 2
        sy, sz = (700, 180) if k % 2 == 0 else (180, 700)
        bodies[i + 2 + k] = (box((x0 + FD / 2, 800 * math.cos(a), 800 * math.sin(a)), X, (FD, sy, sz)), "#b87333", 0.3, 0)
    i += 6
for b in range(NB):
    a = 2 * math.pi * (b + 0.5) / NB
    bodies[43 + b] = (frustum(25, 25, 15, (L - 15, RB * math.cos(a), RB * math.sin(a)), (1, 0, 0), 16), "#e6e8ea", 0.5, 120)
for j, a in enumerate((math.radians(11.25), math.radians(191.25))):
    y, z = (R + 110) * math.cos(a), (R + 110) * math.sin(a)
    bodies[63 + 2 * j] = (box((L - FL / 2, y, z), X, (100, 160, 120)), "#3b6fb6", 0.3, 0)
    bodies[64 + 2 * j] = (box((FL / 2, y, z), X, (100, 160, 120)), "#3b6fb6", 0.3, 0)

meta = {b["index"]: b for b in json.load(open(os.path.join(SEG, "bodies.json")))}
for idx, (tris, col, gloss, bias) in bodies.items():
    write_stl(os.path.join(SEG, "bodies", f"{idx}.stl"), tris)
    meta[idx] = {"index": idx, "color": col, "gloss": meta.get(idx, {}).get("gloss", gloss), "bias": bias,
                 "source": "local tessellation (segment_rev5.py)"}
json.dump([meta[k] for k in sorted(meta)], open(os.path.join(SEG, "bodies.json"), "w"), indent=1)
print(f"wrote {len(bodies)} bodies; assets/segment now has {len(meta)}")
