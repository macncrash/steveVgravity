"""Tessellate the Space Shuttle orbiter locally, mirroring STEVE's components/orbiter.py
(document cf4b87db-…, revision 2): same stations, sections, lofts and placements, including `stretch`.

STEVE can't export print meshes for the orbiter's lofted skin, so renders use this mirror.
Frame: orbiter-local, mm — nose +X, payload bay opens +Z, +Y = port. Bodies are double-sided (cull=False).
"""
import math

import numpy as np

from station_mesh import frustum, box

WHITE, BLACK, GREY, SILVER, GLASS, DOOR = "#f4f4f2", "#17171a", "#6f757d", "#a7adb5", "#0b121c", "#e3e8ee"
DOCK_X, DOCK_Z = 8300, 3100


def _ruled(sections, cap=True):
    """Ruled loft through polygon sections (each (k, 3), same k): quads between neighbours + fan end caps."""
    tris = []
    for a, b in zip(sections[:-1], sections[1:]):
        a2, b2 = np.roll(a, -1, 0), np.roll(b, -1, 0)
        tris.append(np.stack([a, a2, b2], 1))
        tris.append(np.stack([a, b2, b], 1))
    if cap:
        for s in (sections[0], sections[-1]):
            c = np.repeat(s.mean(axis=0)[None], len(s), 0)
            tris.append(np.stack([c, s, np.roll(s, -1, 0)], 1))
    return np.concatenate(tris)


def _extrude(poly_yz, x0, length, caps_strip=None):
    """Extrude a (k, 2) polygon in the YZ plane from x0 along +X. caps_strip=n: cap a band polygon whose first n
    points are the outer edge and last n the inner edge (reversed), as two triangle strips."""
    k = len(poly_yz)
    a = np.column_stack([np.full(k, x0), poly_yz])
    b = a + np.array([length, 0, 0])
    side = _ruled([a, b], cap=False)
    caps = []
    for s in (a, b):
        if caps_strip:
            n = caps_strip
            outer, inner = s[:n], s[n:][::-1]
            for i in range(n - 1):
                caps.append([outer[i], outer[i + 1], inner[i + 1]])
                caps.append([outer[i], inner[i + 1], inner[i]])
        else:
            c = s.mean(axis=0)
            for i in range(k):
                caps.append([c, s[i], s[(i + 1) % k]])
    return np.concatenate([side, np.array(caps)])


def _hull_section(x, w, zb, zs, zt, rb):
    zc = (zt * zt - zs * zs - w * w) / (2 * (zt - zs))
    a0 = math.degrees(math.atan2(zs - zc, w))

    def arc(cy, cz, r, a_from, a_to, n):
        return [(cy + r * math.cos(math.radians(a_from + (a_to - a_from) * i / n)),
                 cz + r * math.sin(math.radians(a_from + (a_to - a_from) * i / n))) for i in range(n + 1)]

    pts = arc(w - rb, zb + rb, rb, 270, 360, 3) + arc(0, zc, zt - zc, a0, 180 - a0, 12) + arc(-w + rb, zb + rb, rb, 180, 270, 3)
    return np.array([(x, y, z) for y, z in pts])


def _split_colour(tris, z_cut, below, above):
    """Colour a body by the tile split plane z = z_cut (as STEVE's split + material per piece)."""
    zc = tris[:, :, 2].mean(axis=1)
    return [(tris[zc < z_cut], below), (tris[zc >= z_cut], above)]


def _rx(deg):
    t = math.radians(deg)
    return np.array([[1, 0, 0], [0, math.cos(t), -math.sin(t)], [0, math.sin(t), math.cos(t)]])


def _ry(deg):
    t = math.radians(deg)
    return np.array([[math.cos(t), 0, math.sin(t)], [0, 1, 0], [-math.sin(t), 0, math.cos(t)]])


def orbiter_bodies(stretch=0):
    """[(triangles, colour, gloss, bias, cull)] in orbiter-local coordinates."""
    S = stretch
    out = []
    add = lambda t, c, g=0.05, b=0: out.append((t, c, g, b, False))

    FWD = [(18750, 160, -1150, -1080, -870, 60), (18150, 1000, -1900, -1000, 50, 400), (16900, 1800, -2350, -500, 1100, 700),
           (15400, 2350, -2500, 250, 2200, 800), (13800, 2600, -2500, 900, 2750, 800), (11800, 2600, -2500, 1200, 2700, 600),
           (10000, 2600, -2500, 1300, 2500, 500)]
    fwd = _ruled([_hull_section(*st) for st in FWD])
    for t, c in _split_colour(fwd, -1950, BLACK, WHITE):
        add(t, c)
    mid = _extrude(np.array([(-2100, -2500), (2100, -2500), (2600, -2000), (2600, 1300), (2350, 1300), (2350, -1750),
                             (-2350, -1750), (-2350, 1300), (-2600, 1300), (-2600, -2000)], float), -8300 - S, 18300 + S)
    for t, c in _split_colour(mid, -2200, BLACK, WHITE):
        add(t, c)
    AFT = [(-8300, 2600, -2500, 1300, 1900, 500), (-10600, 2650, -2550, 1250, 1950, 450), (-12600, 2650, -2550, 1100, 1800, 400)]
    aft = _ruled([_hull_section(*st) for st in AFT]) - np.array([S, 0, 0])
    for t, c in _split_colour(aft, -2200, BLACK, WHITE):
        add(t, c)
    add(box((-13500 - S, 0, -2450), np.eye(3), (1800, 4200, 380)), BLACK)

    # windows: six windshield panes (roll, then pitch 36 deg), two overhead, two aft
    for y, z, roll in ((450, 1642, 0), (-450, 1642, 0), (1250, 1284, -36), (-1250, 1284, 36), (1850, 640, -60), (-1850, 640, 60)):
        t = box((0, 0, 0), np.eye(3), (700, 620, 200)) @ _rx(roll).T @ _ry(36).T + np.array([16100, y, z])
        add(t, GLASS, 0.8, 30)
    for y in (600, -600):
        add(box((13300, y, 2675), np.eye(3), (650, 520, 160)), GLASS, 0.8, 30)
        add(box((10050, y, 2000), np.eye(3), (150, 650, 420)), GLASS, 0.8, 30)

    # payload-bay doors open 175 deg
    def door_profile(sgn, n=9, th=70, open_deg=175.0):
        hy, hz = 2600, 1300
        zc = (2500 ** 2 - hz ** 2 - hy ** 2) / (2 * (2500 - hz))
        r = 2500 - zc
        a0 = math.atan2(hz - zc, hy)
        c, s = math.cos(math.radians(-open_deg)), math.sin(math.radians(-open_deg))

        def place(rad, a):
            dy, dz = rad * math.cos(a) - hy, zc + rad * math.sin(a) - hz
            return (sgn * (hy + c * dy - s * dz), hz + s * dy + c * dz)
        angs = [a0 + (math.pi / 2 - a0) * k / (n - 1) for k in range(n)]
        return [place(r, a) for a in angs] + [place(r - th, a) for a in reversed(angs)]
    for sgn in (1, -1):
        add(_extrude(np.array(door_profile(sgn)), -8150 - S, 18000 + S, caps_strip=9), DOOR, 0.5)

    # wings: double delta, airfoil sections, ruled; tile split at z = -2470
    def wing_section(y, xl, xt, t, zb=-2600):
        c = xl - xt
        pts = [(xl, zb + 0.32 * t), (xl - 0.08 * c, zb + 0.82 * t), (xl - 0.35 * c, zb + t), (xt + 0.25 * c, zb + 0.62 * t),
               (xt, zb + 0.18 * t), (xt, zb), (xl - 0.10 * c, zb), (xl - 0.015 * c, zb + 0.08 * t)]
        return np.array([(x - S, y, z) for x, z in pts])
    WING = [(2400, 7200, -12300, 1500), (4400, -300, -12150, 1150), (11900, -9400, -11600, 260)]
    for sgn in (1, -1):
        wing = _ruled([wing_section(sgn * y, xl, xt, t) for y, xl, xt, t in WING])
        for t, c in _split_colour(wing, -2470, BLACK, WHITE):
            add(t, c)

    # vertical stabilizer
    def fin_section(z, xl, xt, t):
        c = xl - xt
        pts = [(xl, 0), (xl - 0.2 * c, t / 2), (xt + 0.15 * c, 0.3 * t), (xt, 0.06 * t), (xt, -0.06 * t),
               (xt + 0.15 * c, -0.3 * t), (xl - 0.2 * c, -t / 2)]
        return np.array([(x - S, y, z) for x, y in pts])
    add(_ruled([fin_section(1700, -8500, -15700, 900), fin_section(9800, -15500, -17300, 320)]), WHITE)

    # OMS pods (ellipse sections, ruled) and nozzles
    OMS = [(-7700, 350, 250), (-9300, 1000, 850), (-12700, 1050, 900), (-13700, 850, 750)]
    th = np.linspace(0, 2 * math.pi, 28, endpoint=False)
    for sgn in (1, -1):
        secs = [np.column_stack([np.full(28, x - S), sgn * 1950 + ry * np.cos(th), 1900 + rz * np.sin(th)]) for x, ry, rz in OMS]
        add(_ruled(secs), WHITE)
        out.append((frustum(280, 520, 1000, (-13700 - S, sgn * 1950, 1900), (-1, 0, 0), 24), GREY, 0.4, 0, False))

    # three RS-25s: powerhead + ruled bell
    BELL = [(-13000, 300), (-13700, 720), (-14900, 1030), (-15900, 1150)]
    th = np.linspace(0, 2 * math.pi, 32, endpoint=False)
    for y, z in ((0, 950), (1350, -1150), (-1350, -1150)):
        out.append((frustum(520, 520, 700, (-12300 - S, y, z), (-1, 0, 0), 24), GREY, 0.4, 0, False))
        secs = [np.column_stack([np.full(32, x - S), y + r * np.cos(th), z + r * np.sin(th)]) for x, r in BELL]
        add(_ruled(secs), GREY, 0.4)

    # Canadarm stowed on the port sill
    ay, az = 2150, 1500
    add(box((9500, ay, az), np.eye(3), (600, 500, 600)), SILVER, 0.3)
    add(frustum(190, 190, 6300, (9200, ay, az), (-1, 0, 0), 16), WHITE)
    add(frustum(240, 240, 500, (2800, ay - 250, az), (0, 1, 0), 16), SILVER, 0.3)
    add(frustum(170, 170, 6100, (2600, ay, az), (-1, 0, 0), 16), WHITE)
    add(box((-3700, ay, az), np.eye(3), (400, 450, 450)), SILVER, 0.3)
    add(frustum(220, 220, 800, (-3900, ay, az), (-1, 0, 0), 16), SILVER, 0.3)

    # Orbiter Docking System: external airlock + NDS
    zr = DOCK_Z - 300
    add(box((DOCK_X, 0, -1050), np.eye(3), (3000, 4400, 300)), SILVER, 0.3)
    add(frustum(800, 800, 3000, (DOCK_X, 0, -1200), (0, 0, 1), 32), WHITE)
    add(frustum(950, 950, zr - 300 - 1800, (DOCK_X, 0, 1800), (0, 0, 1), 32), SILVER, 0.3)
    add(frustum(1100, 1100, 300, (DOCK_X, 0, zr - 300), (0, 0, 1), 32), SILVER, 0.3)
    add(frustum(850, 850, 300, (DOCK_X, 0, zr), (0, 0, 1), 32), SILVER, 0.3)
    return out
