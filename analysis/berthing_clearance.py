"""Berthing path clearance, every segment of every launch, against everything already on station.

python3 berthing_clearance.py      -> prints the table and writes BERTHING_CLEARANCE.md next to this file

STEVE's own animation check (check=True) reports overlaps but not clearances, and it can't skip the hidden carrier
instances. This check replays the same joint chain (station_geometry.berthing_plan, with the timing in
steve/blowball_station/main.py and render_all.py) offline:

- the moving segment is an exact capped cylinder (the flange radius), and the arm's end effector a capsule;
- everything else is a cloud of surface points from the same tessellation as the renders (station_mesh.py,
  orbiter_mesh.py), with no point farther than POINT_MM from its neighbours, so a clearance is good to ≈POINT_MM / 2;
- the clearance at a pose is the signed distance from the moving body to the nearest point.

Not checked, by design: the stowed segments still in the bay (they sit SEG_GAP apart along the bay and the lift
slides past them), and the arriving pod's own berthed segments during the final slide in (coaxial, it ends in
contact: that is the berth).
"""
import math
import os
import sys

import numpy as np
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(HERE, "..", "renders", "tools")
sys.path.insert(0, TOOLS)
sys.path.insert(0, os.path.join(TOOLS, "station"))
import station_mesh as M  # noqa: E402
from orbiter_mesh import orbiter_bodies  # noqa: E402
from params import pod_r, seg_len, shuttle_stretch  # noqa: E402
from render_mesh import rot_axis, subdivide  # noqa: E402

G = M.G
POINT_MM = 300.0
FLANGE_R = pod_r + 50
TIMING = {"lift": 1.5, "side": 3, "out": 6, "swing": 9, "turn": 9, "in": 12}   # as main.py
STEPS = 24                    # poses per leg window
STATIC_MM = 5000.0            # mm: at rest, only gaps under this are reported
NEAR = 6000.0                 # mm: look for points this far beyond the moving body's bounding sphere
CLASS_OF = {M.COL["disc"]: "bloom", M.COL["spar"]: "bloom", M.COL["mast"]: "bloom", M.COL["fin"]: "radiator",
            M.COL["strut"]: "radiator"}


def points(tris):
    t = subdivide(np.asarray(tris), POINT_MM)
    return np.concatenate([t.reshape(-1, 3), t.mean(axis=1)])


def shuttle_points():
    R = np.diag([1.0, -1.0, -1.0])
    off = np.array([-G.ORB_DOCK_X, 0, G.r_port + G.ORB_DOCK_Z])
    return np.concatenate([points(t @ R.T + off) for t, *_ in orbiter_bodies(stretch=shuttle_stretch)])


def obstacles(built, shuttle_pts):
    """(points, labels) for the hub, every built pod (by part), and the docked Shuttle."""
    pts, lab = [], []
    for name, bodies in [("hub", M.station_bodies(set(), with_hub=True))] + \
                        [(q, M.station_bodies({q}, with_hub=False)) for q in sorted(built)]:
        for tris, col, _ in bodies:
            p = points(tris)
            part = CLASS_OF.get(col, "pod")
            if name == "hub":
                part = "hub bloom" if part == "bloom" else "hub"
            label = part if name == "hub" else f"pod {name} {part}"
            pts.append(p)
            lab += [label] * len(p)
    pts.append(shuttle_pts)
    lab += ["Shuttle"] * len(shuttle_pts)
    return np.concatenate(pts), np.array(lab)


def berthed_points(D, j):
    """The arriving pod's segments already berthed before segment j (0-based)."""
    if j == 0:
        return np.zeros((0, 3))
    return points(M.frustum(FLANGE_R, FLANGE_R, j * seg_len, G.at(D, G.r0), D, 48))


def chain(legs, vals, x):
    """The berthing joint chain applied to points at the modelled pose (as render_all._chain)."""
    for (_, kind, (p, d), _), v in reversed(list(zip(legs, vals))):
        if kind == "slider":
            x = x + np.asarray(d) * v
        else:
            p = np.asarray(p)
            x = (x - p) @ rot_axis(d, v).T + p
    return x


def leg_values(legs, t):
    """Joint values at time t of one segment's run (each leg eases across its own window, as render_all)."""
    vals = []
    for name, _, _, travel in legs:
        end = TIMING[name]
        prev = 6.0 if name == "turn" else max([v for v in TIMING.values() if v < end], default=0.0)
        u = min(1.0, max(0.0, (t - prev) / (end - prev)))
        vals.append(travel * u * u * (3 - 2 * u))
    return vals


def sdf_cylinder(p, c, a, r, h):
    q = p - c
    ax = q @ a
    rad = np.linalg.norm(q - ax[:, None] * a, axis=1) - r
    d_ax = np.abs(ax) - h
    return np.minimum(np.maximum(rad, d_ax), 0) + np.hypot(np.maximum(rad, 0), np.maximum(d_ax, 0))


def sdf_capsule(p, a, b, r):
    ab = b - a
    t = np.clip(((p - a) @ ab) / (ab @ ab), 0, 1)
    return np.linalg.norm(p - (a + t[:, None] * ab), axis=1) - r


def check_launch(L, shuttle_pts):
    q = G.ORDER[L - 1]
    G.ARRIVING = q
    built = set(G.ORDER[:L - 1])
    D = np.array(G.DIRS[q])
    pts, lab = obstacles(built, shuttle_pts)
    tree = cKDTree(pts)
    worst = {}                                  # (phase, label) -> (clearance, segment, leg, t); phase: in the bay or out
    berth_err = 0.0
    for j, (s0, legs) in enumerate(G.berthing_plan()):
        own = berthed_points(D, j)
        own_tree = cKDTree(own) if len(own) else None
        s0 = np.array(s0)
        # the moving body at its modelled pose: segment axis X (rolled 180 deg about X), effector hanging below
        model = np.array([s0, s0 + (1, 0, 0), s0 - (0, 0, pod_r + 450), s0 - (0, 0, pod_r + 450 + 2420)])
        times = np.linspace(0, 12, 12 * STEPS // 3 + 1)[1:]          # from the first instant it moves
        for t in times:
            leg = next(n for n, e in sorted(TIMING.items(), key=lambda kv: kv[1]) if t <= e)
            c, ax1, e0, e1 = chain(legs, leg_values(legs, t), model)
            a = (ax1 - c) / np.linalg.norm(ax1 - c)
            sets = [(tree, pts, lab)]
            if own_tree is not None and t <= TIMING["swing"]:
                sets.append((own_tree, own, np.array(["own pod"] * len(own))))
            for tr, P, LB in sets:
                idx = tr.query_ball_point(c, math.hypot(FLANGE_R, seg_len / 2) + 2420 + 450 + pod_r + NEAR)
                if not idx:
                    continue
                p = P[idx]
                d = np.minimum(sdf_cylinder(p, c, a, FLANGE_R, seg_len / 2), sdf_capsule(p, e0, e1, 300))
                k = int(np.argmin(d))
                key = ("bay" if leg == "lift" else "out", LB[idx][k])
                if key not in worst or d[k] < worst[key][0]:
                    worst[key] = (float(d[k]), j + 1, leg, float(t))
        # final pose against the berth: centre on the pod axis at its segment's place, axis along the pod
        want = D * (G.r0 + j * seg_len + seg_len / 2)
        berth_err = max(berth_err, float(np.linalg.norm(c - want)), float(np.degrees(np.arccos(min(1, abs(a @ D))))))
    return q, worst, berth_err


def static_check(shuttle_pts):
    """Full station with the Shuttle docked: the smallest gap between parts that are not joined to each other
    (different pods, a pod and the hub bloom, anything and the Shuttle except the docking pod it docks on)."""
    pts, lab = obstacles(set(G.ORDER), shuttle_pts)
    keep = np.unique(np.round(pts / 50).astype(np.int64), axis=0, return_index=True)[1]   # drop duplicates (50 mm)
    pts, lab = pts[keep], lab[keep]
    owner = np.array([l.split(" ")[1] if l.startswith("pod ") else l for l in lab])
    out = {}
    for o in sorted(set(owner)):
        if o == "hub":
            continue
        mine = owner == o
        other = ~mine & (owner != "hub")
        if o == "Shuttle":
            other &= owner != "0"
        if o == "0":
            other &= owner != "Shuttle"
        d, k = cKDTree(pts[other]).query(pts[mine], distance_upper_bound=STATIC_MM, workers=-1)
        i = int(np.argmin(d))
        out[o] = (float(d[i]), lab[mine][i], lab[other][k[i]]) if np.isfinite(d[i]) else (math.inf, "-", "-")
    return out


def report(rows, static):
    out = ["# Blowball Station: berthing path clearance", "",
           "Generated by `analysis/berthing_clearance.py`: every flight segment of every launch, replayed through the "
           "same arm joint chain as the STEVE animation, against everything already on station and the docked New "
           f"Shuttle. Clearances are good to ≈{POINT_MM / 2:.0f} mm (surface points every {POINT_MM:.0f} mm). The "
           "moving body is the segment (to its flanges) plus the arm's end effector.", "",
           "| Launch | Pod | Lifting out of the bay | Outside the bay | Tightest bloom or radiator | Final pose error |",
           "|---:|---:|---|---|---:|---:|"]
    for L, q, worst, err in rows:
        cell = []
        for phase in ("bay", "out"):
            (ph, name), (d, j, leg, t) = min(((k, v) for k, v in worst.items() if k[0] == phase), key=lambda kv: kv[1][0])
            cell.append(f"{d / 1000:.2f} m to {name} (segment {j}, {leg}, t = {t:.1f} s)")
        br = min(v[0] for k, v in worst.items() if "bloom" in k[1] or "radiator" in k[1])
        out.append(f"| {L} | {q} | {cell[0]} | {cell[1]} | {br / 1000:.2f} m | {err:.1e} |")
    lo = {ph: min(v[0] for _, _, w, _ in rows for k, v in w.items() if k[0] == ph) for ph in ("bay", "out")}
    out += ["", f"**Tightest anywhere: {lo['bay'] / 1000:.2f} m while lifting out of the bay, "
            f"{lo['out'] / 1000:.2f} m outside it.** In the bay the segment starts on its trunnions just above the "
            "floor and slides out between the sills, so small gaps there are by design; outside the bay is where the "
            "station's own growth matters. Final pose error is the largest of the centre offset (mm) and the axis "
            "angle (degrees) at the berth.", "",
            "## The finished station, at rest", "",
            "The smallest gap from each part to anything it is not joined to (other pods, the hub bloom, the Shuttle):", "",
            "| Part | Gap | Between |", "|---|---:|---|"]
    for o, (d, a, b) in sorted(static.items(), key=lambda kv: kv[1][0]):
        gap = f"{d / 1000:.2f} m" if math.isfinite(d) else f"> {STATIC_MM / 1000:.0f} m"
        out.append(f"| {'pod ' + o if o.isdigit() else o} | {gap} | {a} ↔ {b} |")
    out += ["", "Not checked, by design: segments still stowed in the bay, and the arriving pod's own berthed segments "
            "during the final slide in (coaxial; it ends in contact, which is the berth).", ""]
    return "\n".join(out)


if __name__ == "__main__":
    sh = shuttle_points()
    rows = []
    for L in range(2, len(G.ORDER) + 1):
        q, worst, err = check_launch(L, sh)
        for ph in ("bay", "out"):
            (_, name), (d, j, leg, t) = min(((k, v) for k, v in worst.items() if k[0] == ph), key=lambda kv: kv[1][0])
            print(f"launch {L:2d} pod {q:2d} {ph}: tightest {d / 1000:6.2f} m against {name} (segment {j}, {leg}, "
                  f"t={t:.1f}); berth error {err:.1e}", flush=True)
        rows.append((L, q, worst, err))
    static = static_check(sh)
    for o, v in sorted(static.items(), key=lambda kv: kv[1][0]):
        print("static", o, f"{v[0] / 1000:.2f} m", v[1], "<->", v[2])
    open(os.path.join(HERE, "BERTHING_CLEARANCE.md"), "w").write(report(rows, static))
    print("wrote BERTHING_CLEARANCE.md")
