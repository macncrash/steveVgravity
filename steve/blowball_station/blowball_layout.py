"""Blowball Station layout: pod directions packed on a sphere.

A line-for-line port of the layout half of gravity/blowball_station.js (Gravity on holodeck1.ai),
so the same knob values give the same station in STEVE. Directions come back in Gravity's frame
(y up); to_steve() maps them to STEVE's Z-up frame (X = x, Y = -z, Z = y).
"""
import math

ITERS = 1200


def mulberry32(a):
    state = [a & 0xFFFFFFFF]

    def rnd():
        state[0] = (state[0] + 0x6D2B79F5) & 0xFFFFFFFF
        a = state[0]
        t = _imul(a ^ (a >> 15), 1 | a)
        t = ((t + _imul(t ^ (t >> 7), 61 | t)) & 0xFFFFFFFF) ^ t
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296

    return rnd


def _imul(a, b):
    return (a * b) & 0xFFFFFFFF


def start_dirs(n, start, seed):
    d = []
    if start >= 0.5:
        rnd = mulberry32(seed)
        for _ in range(n):
            y = 2 * rnd() - 1
            a = 2 * math.pi * rnd()
            r = math.sqrt(1 - y * y)
            d.append([r * math.cos(a), y, r * math.sin(a)])
    else:
        ga = math.pi * (3 - math.sqrt(5))
        for i in range(n):
            y = 1 - (2 * (i + 0.5)) / n
            r = math.sqrt(1 - y * y)
            a = i * ga
            d.append([r * math.cos(a), y, r * math.sin(a)])
    return d


def relax_step(d, k, it):
    n = len(d)
    f = [[0.0, 0.0, 0.0] for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            dx, dy, dz = d[i][0] - d[j][0], d[i][1] - d[j][1], d[i][2] - d[j][2]
            r2 = dx * dx + dy * dy + dz * dz + 1e-12
            s = 1 / math.pow(r2, (k + 2) / 2)
            f[i][0] += dx * s; f[i][1] += dy * s; f[i][2] += dz * s
            f[j][0] -= dx * s; f[j][1] -= dy * s; f[j][2] -= dz * s
    fmax = 0.0
    for i in range(n):
        dot = f[i][0] * d[i][0] + f[i][1] * d[i][1] + f[i][2] * d[i][2]
        f[i] = [f[i][c] - dot * d[i][c] for c in range(3)]
        fmax = max(fmax, math.hypot(*f[i]))
    if fmax < 1e-15:
        return
    spacing = math.sqrt(4 * math.pi / n)
    eta = 0.12 * spacing * math.pow(0.004, it / (ITERS - 1)) / fmax
    for i in range(n):
        v = [d[i][c] + eta * f[i][c] for c in range(3)]
        m = math.hypot(*v)
        d[i] = [c / m for c in v]


def canonical(d):
    """Rotate so pod 0 points +y and pod 1 lies in the x-y plane with x > 0."""
    e2 = d[0]
    ax = d[1] if len(d) > 1 else [1, 0, 0]
    dot = sum(a * b for a, b in zip(ax, e2))
    e1 = [ax[c] - dot * e2[c] for c in range(3)]
    m = math.hypot(*e1)
    if m < 1e-9:
        e1 = [1, 0, 0] if abs(e2[0]) < 0.9 else [0, 0, 1]
        dot = sum(a * b for a, b in zip(e1, e2))
        e1 = [e1[c] - dot * e2[c] for c in range(3)]
        m = math.hypot(*e1)
    e1 = [c / m for c in e1]
    e3 = [e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0]]
    return [[sum(v[c] * e[c] for c in range(3)) for e in (e1, e2, e3)] for v in d]


def pod_directions(pods, k=6, start=0, seed=7, relax=1):
    """Unit pod directions in Gravity's frame (y up), after the full ITERS relaxation."""
    d = start_dirs(int(round(pods)), start, int(round(seed)))
    if relax >= 0.5:
        for it in range(ITERS):
            relax_step(d, k, it)
    return canonical(d)


def to_steve(v):
    """Gravity (x, y-up, z) -> STEVE (X, Y, Z-up)."""
    return (v[0], -v[2], v[1])


def min_angle_deg(d):
    best = math.pi
    for i in range(len(d)):
        for j in range(i + 1, len(d)):
            c = max(-1.0, min(1.0, sum(a * b for a, b in zip(d[i], d[j]))))
            best = min(best, math.acos(c))
    return math.degrees(best)


TIE = (0.02, 1e-3, 0.0)   # per order mode: |CoM sum| in pod units; inhibitor field


def build_order(d, mode=0):
    """Assembly order (port of buildOrder in blowball_station.js). Pod 0 flies first with the hub.

    mode 0: opposite pairs - each next pod minimises the centre-of-mass offset (decussate leaves)
    mode 1: biggest gap - each next pod goes where the inhibitor field of placed pods is weakest
            (Douady & Couder phyllotaxis model, exp(-chord / 0.5))
    mode 2: index order. Near-ties (within TIE) go to the lowest index.
    """
    n = len(d)
    order, left = [0], list(range(1, n))
    while left:
        best, best_val = left[0], math.inf
        if mode != 2:
            for j in left:
                if mode == 0:
                    s = [d[j][c] + sum(d[i][c] for i in order) for c in range(3)]
                    val = math.hypot(*s)
                else:
                    val = 0.0
                    for i in order:
                        dt = sum(d[i][c] * d[j][c] for c in range(3))
                        val += math.exp(-math.sqrt(max(0.0, 2 - 2 * dt)) / 0.5)
                if val < best_val - TIE[mode]:
                    best_val, best = val, j
        order.append(best)
        left.remove(best)
    return order
