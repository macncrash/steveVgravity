"""Shared Blowball Station geometry: pod directions, radii and orientation frames (STEVE frame, Z up, mm)."""
import math
from params import pods, k, start, seed, relax, hub_r, reach, segments, seg_len, cone_len, order, launches, berthing
from blowball_layout import pod_directions, to_steve, build_order

SUN = (1.0, 0.0, 0.0)                      # every bloom tracks the sun; +X is the sun line in this model
_dirs = pod_directions(pods, k, start, seed, relax)
DIRS = [to_steve(d) for d in _dirs]        # DIRS[0] = +Z = docking axis
ORDER = build_order(_dirs, int(order))     # assembly sequence; ORDER[0] = 0 flies with the hub
BUILT = set(ORDER[:max(0, int(launches))])  # pods on station after `launches` launches
# With berthing on, the last launch's pod is still in the Shuttle's bay as loose flight segments (main.py animates them)
ARRIVING = ORDER[int(launches) - 1] if berthing and 2 <= int(launches) <= len(ORDER) else None
BUILT.discard(ARRIVING)

pod_len = segments * seg_len               # a pod is `segments` Spacelab segments end to end
r0 = hub_r + reach                         # pod root (berthing ring) radius
r_tip = r0 + pod_len                       # end of the last segment
r_cone = r_tip + cone_len                  # end of the Spacelab end cone
r_port = r_cone + 1600                     # pod 0: docking adapter + NDS ring face


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


# The orbiter docks on pod 0 rolled 180 deg about X: orbiter-local (x, y, z) -> station (x - 8300, -y, -z + r_port + 3100)
ORB_DOCK_X, ORB_DOCK_Z = 8300, 3100
BAY_AXIS_Z = 375           # orbiter-local height of the payload-bay centreline (floor -1750, closed doors 2500)
SEG_FIRST_X = 5900         # orbiter-local x of the first stowed segment's forward face (aft of the ODS; keeps the
                           # first segment 0.5 m clear of the docking pod's cone as it lifts out)
SEG_GAP = 100              # mm between stowed segments


def orbiter_to_station(p):
    return (p[0] - ORB_DOCK_X, -p[1], -p[2] + r_port + ORB_DOCK_Z)


LIFT = 3400                # mm out of the bay (bay opens toward -Z): clears the sills, still under the open doors
SIDE = 12000               # mm sideways: clear of the docking pod, and wide enough to pass outside the OMS pods and tail
RC = 50000                 # mm swing radius, horizontal: outside every bloom (blooms reach ~44 m)


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
    Checked offline (simplified capsule model) against pods, blooms, radiators and the Shuttle for every launch:
    >= 0.32 m clear; tightest is segment 1 passing the docking pod's end cone as it lifts out.
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


def axis_angle(ex, ey, ez):
    """Axis-angle (axis, degrees) of the rotation taking X, Y, Z to the orthonormal frame ex, ey, ez."""
    m = [[ex[0], ey[0], ez[0]], [ex[1], ey[1], ez[1]], [ex[2], ey[2], ez[2]]]
    tr = m[0][0] + m[1][1] + m[2][2]
    if tr > 0:
        s = math.sqrt(tr + 1.0) * 2
        q = (0.25 * s, (m[2][1] - m[1][2]) / s, (m[0][2] - m[2][0]) / s, (m[1][0] - m[0][1]) / s)
    elif m[0][0] > m[1][1] and m[0][0] > m[2][2]:
        s = math.sqrt(1.0 + m[0][0] - m[1][1] - m[2][2]) * 2
        q = ((m[2][1] - m[1][2]) / s, 0.25 * s, (m[0][1] + m[1][0]) / s, (m[0][2] + m[2][0]) / s)
    elif m[1][1] > m[2][2]:
        s = math.sqrt(1.0 + m[1][1] - m[0][0] - m[2][2]) * 2
        q = ((m[0][2] - m[2][0]) / s, (m[0][1] + m[1][0]) / s, 0.25 * s, (m[1][2] + m[2][1]) / s)
    else:
        s = math.sqrt(1.0 + m[2][2] - m[0][0] - m[1][1]) * 2
        q = ((m[1][0] - m[0][1]) / s, (m[0][2] + m[2][0]) / s, (m[1][2] + m[2][1]) / s, 0.25 * s)
    qw, qx, qy, qz = q
    if qw < 0:
        qw, qx, qy, qz = -qw, -qx, -qy, -qz
    angle = 2 * math.acos(max(-1.0, min(1.0, qw)))
    sn = math.sqrt(max(1e-18, 1 - qw * qw))
    if angle < 1e-9:
        return (0.0, 0.0, 1.0), 0.0
    return (qx / sn, qy / sn, qz / sn), math.degrees(angle)
