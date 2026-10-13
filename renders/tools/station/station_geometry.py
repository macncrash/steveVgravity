"""Shared Blowball Station geometry: pod directions, radii and orientation frames (STEVE frame, Z up, mm)."""
import math
from params import pods, k, start, seed, relax, hub_r, reach, segments, seg_len, cone_len, order, launches, berthing
from blowball_layout import pod_directions, to_steve, build_order

SUN = (1.0, 0.0, 0.0)                      # every bloom tracks the sun; +X is the sun line in this model
_dirs = pod_directions(pods, k, start, seed, relax)
DIRS = [to_steve(d) for d in _dirs]
ORDER = build_order(_dirs, int(order))
BUILT = set(ORDER[:max(0, int(launches))])
ARRIVING = ORDER[int(launches) - 1] if berthing and 2 <= int(launches) <= len(ORDER) else None
BUILT.discard(ARRIVING)

pod_len = segments * seg_len               # a pod is `segments` Spacelab segments end to end
r0 = hub_r + reach                         # pod root (berthing ring) radius
r_tip = r0 + pod_len                       # end of the last segment
r_cone = r_tip + cone_len                  # end of the Spacelab end cone
r_port = r_cone + 1600                     # pod 0: docking adapter + NDS ring face


FIN0_DROP = 3000           # mm: the docking pod's fins sit this much nearer the hub than the others. Pod 0's edge-on
                           # plane is the XZ plane, right under the Shuttle's bay, and the arm's end effector dips
                           # into it as each segment lifts out (berthing_clearance.py)


def fin_mid(i):
    """Radius of the middle of pod i's radiator fins (they cover 60 % of the pod)."""
    return r0 + 0.65 * pod_len - (FIN0_DROP if i == 0 else 0)


def at(d, r):
    return tuple(c * r for c in d)


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def unit(v):
    m = math.sqrt(sum(c * c for c in v))
    return tuple(c / m for c in v)


def edge_on_frame(d):
    """(d, w, n): d along the pod, n = normal of a panel that contains d and the sun line (edge-on to the sun)."""
    n = cross(d, SUN)
    if math.sqrt(sum(c * c for c in n)) < 1e-6:
        n = (0.0, 0.0, 1.0)
    n = unit(n)
    w = cross(n, d)
    return d, w, n


def hub_bloom_dir(dirs):
    """Where the hub's own bloom points (it flies with launch 1, which has no other power, as ISS's P6 array did).

    The centre of a gap between three pods (a face of the pods' convex hull), chosen among the widest gaps near the
    equator (|z| < 0.5: clear of the berthing lanes, which run above the docking pod's ring of neighbours), as far
    off the sun line as possible (largest |y|, so it shades little and is shaded little), sunward first, +y on a tie.
    Values are rounded to 0.01 before comparing, so float noise between Gravity and Python can't flip the choice.
    """
    n, faces = len(dirs), []
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                a, b, c = dirs[i], dirs[j], dirs[k]
                nrm = cross(tuple(b[m] - a[m] for m in range(3)), tuple(c[m] - a[m] for m in range(3)))
                side = [sum(nrm[m] * (dirs[q][m] - a[m]) for m in range(3)) for q in range(n) if q not in (i, j, k)]
                if all(s <= 1e-9 for s in side) or all(s >= -1e-9 for s in side):
                    g = unit(tuple(a[m] + b[m] + c[m] for m in range(3)))
                    gap = min(math.degrees(math.acos(max(-1.0, min(1.0, sum(g[m] * d[m] for m in range(3))))))
                              for d in dirs)
                    faces.append((g, gap))
    widest = max(gap for _, gap in faces)
    pick = [g for g, gap in faces if gap > widest - 1.0 and abs(g[2]) < 0.5] or [g for g, gap in faces if gap > widest - 1.0]
    return max(pick, key=lambda g: (round(abs(g[1]), 2), round(g[0], 2), g[1] > 0))


HUB_BLOOM = hub_bloom_dir(DIRS)          # direction of the hub's own bloom



ORB_DOCK_X, ORB_DOCK_Z = 8300, 3100
BAY_AXIS_Z = 375
SEG_FIRST_X = 5900
SEG_GAP = 100


def orbiter_to_station(p):
    return (p[0] - ORB_DOCK_X, -p[1], -p[2] + r_port + ORB_DOCK_Z)

# ---- berthing path (appended to station_geometry.py) ----
LIFT = 3900                # mm out of the bay (bay opens toward -Z): the segment's underside clears the stowed
                           # Canadarm on the side step (berthing_clearance.py; 3400 left it 3 cm short)
SIDE = 12000               # mm sideways: clear of the docking pod, and wide enough to pass outside the OMS pods and tail
RC = 50000                 # mm swing radius, horizontal: outside every bloom (Ø17 m blooms reach ~49 m)


def rotate(axis, deg, v):
    """Rodrigues rotation of v about a unit axis through the origin, right-handed."""
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    kx = cross(axis, v)
    kd = sum(axis[i] * v[i] for i in range(3))
    return tuple(v[i] * c + kx[i] * s + axis[i] * kd * (1 - c) for i in range(3))


def _angle(a, b):
    return math.degrees(math.acos(max(-1.0, min(1.0, sum(x * y for x, y in zip(unit(a), unit(b)))))))


def berthing_plan():
    """Arriving pod: per flight segment, its stowed centre and the arm legs that take it to its berth.

    Legs (each a joint, chained; axes are given at the modelled pose, i.e. with the segment still in the bay):
      lift  slide out of the bay (-Z)          side  slide sideways (+/-Y)       out  slide to radius RC in the pod's azimuth
      swing turn about the station centre onto the pod axis (far outside)      turn  turn the segment onto the pod axis
      in    slide inward along the pod axis to its berth (segments berth from the hub outward)
    """
    D = DIRS[ARRIVING]
    az = math.atan2(D[1], D[0]) if math.hypot(D[0], D[1]) > 1e-6 else 0.0
    sgn = 1.0 if math.sin(az) >= 0 else -1.0
    plan = []
    for j in range(segments):
        s0 = orbiter_to_station((SEG_FIRST_X - seg_len / 2 - j * (seg_len + SEG_GAP), 0, BAY_AXIS_Z))
        p1 = (s0[0], s0[1], s0[2] - LIFT)
        p2 = (p1[0], sgn * SIDE, p1[2])
        p3 = (RC * math.cos(az), RC * math.sin(az), p1[2])
        t3 = tuple(p3[i] - s0[i] for i in range(3))                  # carrier translation once out
        n = cross(p3, D)
        n = unit(n) if math.sqrt(sum(c * c for c in n)) > 1e-9 else (0.0, 1.0, 0.0)
        swing = _angle(p3, D)
        x_after = rotate(n, swing, (1.0, 0.0, 0.0))                   # segment axis after the swing
        e = cross(x_after, D)
        e = unit(e) if math.sqrt(sum(c * c for c in e)) > 1e-9 else n
        turn = _angle(x_after, D)
        back = lambda v: rotate(n, -swing, v)                        # world (after swing) -> modelled pose
        r3 = math.sqrt(sum(c * c for c in p3))
        out = tuple(p3[i] - p2[i] for i in range(3))
        legs = [
            ("lift", "slider", (s0, (0.0, 0.0, -1.0)), LIFT),
            ("side", "slider", (p1, (0.0, sgn, 0.0)), SIDE),
            ("out", "slider", (p2, unit(out)), math.sqrt(sum(c * c for c in out))),
            ("swing", "revolute", (tuple(-c for c in t3), n), swing),   # through the station centre once moved by t3
            ("in", "slider", (s0, back(tuple(-c for c in D))), r3 - (r0 + j * seg_len + seg_len / 2)),
            ("turn", "revolute", (s0, back(e)), turn),
        ]
        plan.append((s0, legs))
    return plan
