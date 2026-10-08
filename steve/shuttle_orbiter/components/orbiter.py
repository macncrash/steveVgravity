import math
from steve import Component
from params import orbiter_dock_x, orbiter_dock_z, stretch

orbiter = Component("orbiter", name="Space Shuttle orbiter (ODS + NDS)")


def outline(sketch_id, plane, pts):
    with orbiter.sketch(sketch_id, on=plane) as s:
        for i, p in enumerate(pts):
            s.line(f"l{i}", p, pts[(i + 1) % len(pts)])


def hull_section(sid, x, w, zb, zs, zt, rb):
    """Fuselage cross-section at station x: flat tiled belly, rounded chines, vertical sides, arched top."""
    orbiter.plane(f"{sid}_pl", on="YZ", offset=x)
    zc = (zt * zt - zs * zs - w * w) / (2 * (zt - zs))
    a0 = math.degrees(math.atan2(zs - zc, w))
    # Polygonal (faceted) section with the same vertex count at every station, so the ruled loft is all
    # flat facets: curved skins at orbiter scale crash STEVE's full-build print mesher.
    def arc_pts(cy, cz, r, a_from, a_to, n):
        return [(cy + r * math.cos(math.radians(a_from + (a_to - a_from) * i / n)),
                 cz + r * math.sin(math.radians(a_from + (a_to - a_from) * i / n))) for i in range(n + 1)]
    pts = (arc_pts(w - rb, zb + rb, rb, 270, 360, 3) + arc_pts(0, zc, zt - zc, a0, 180 - a0, 12)
           + arc_pts(-w + rb, zb + rb, rb, 180, 270, 3))
    outline(sid, f"{sid}_pl", pts)
    return sid


# ---------------- Fuselage (local frame: nose +X, payload bay opens +Z, +Y = port) ----------------
# Forward fuselage + crew cabin: lofted through stations (x, half-width, belly, shoulder, roof, chine radius)
FWD = [(18750, 160, -1150, -1080, -870, 60), (18150, 1000, -1900, -1000, 50, 400),
       (16900, 1800, -2350, -500, 1100, 700), (15400, 2350, -2500, 250, 2200, 800),
       (13800, 2600, -2500, 900, 2750, 800), (11800, 2600, -2500, 1200, 2700, 600),
       (10000, 2600, -2500, 1300, 2500, 500)]
# ruled lofts throughout: smooth (doubly curved) lofts at this size crash STEVE's full-build print mesher
orbiter.loft("fwd_hull", [hull_section(f"fs{i}", *st) for i, st in enumerate(FWD)], ruled=True, op="new", body="fwd_hull")

# Mid-fuselage: open U-channel payload bay (18.3 m)
orbiter.plane("mid_pl", on="YZ", offset=-8300 - stretch)
outline("mid_sk", "mid_pl", [(-2100, -2500), (2100, -2500), (2600, -2000), (2600, 1300), (2350, 1300),
                             (2350, -1750), (-2350, -1750), (-2350, 1300), (-2600, 1300), (-2600, -2000)])
orbiter.extrude("midbody", "mid_sk", distance=18300 + stretch, op="new", body="midbody")

# Aft fuselage closing the bay, carrying the OMS pods, tail and engines
AFT = [(-8300, 2600, -2500, 1300, 1900, 500), (-10600, 2650, -2550, 1250, 1950, 450),
       (-12600, 2650, -2550, 1100, 1800, 400)]
orbiter.loft("aft_hull", [hull_section(f"as{i}", *st) for i, st in enumerate(AFT)], ruled=True, op="new", body="aft_hull")

# Black HRSI tile line: split the hull bodies at the chine
orbiter.plane("chine_fwd", on="XY", offset=-1950)
orbiter.plane("chine_aft", on="XY", offset=-2200)
orbiter.split("fwd_tiles", body="fwd_hull", tool="chine_fwd")
orbiter.split("mid_tiles", body="midbody", tool="chine_aft")
orbiter.split("aft_tiles", body="aft_hull", tool="chine_aft")

# Body flap under the engines
orbiter.box("body_flap", 1800, 4200, 380, at=(-13500, 0, -2450), op="new", body="body_flap")

# ---------------- Windows ----------------
windows = []
# Six forward windshield panes (pitched ~36 deg, side panes rolled to the cabin curvature)
for y, z, roll in ((450, 1642, 0), (-450, 1642, 0), (1250, 1284, -36), (-1250, 1284, 36), (1850, 640, -60), (-1850, 640, 60)):
    wid = f"win_{len(windows)}"
    orbiter.box(wid, 700, 620, 200, at=(0, 0, 0), op="new", body=wid)
    orbiter.move(f"{wid}_roll", [wid], rotate=("X", roll))
    orbiter.move(f"{wid}_pos", [wid], rotate=("Y", 36), translate=(16100, y, z))
    windows.append(wid)
# Two overhead windows and two aft flight-deck windows looking into the bay
for y in (600, -600):
    wid = f"win_{len(windows)}"
    orbiter.box(wid, 650, 520, 160, at=(13300, y, 2675), op="new", body=wid)
    windows.append(wid)
    wid = f"win_{len(windows)}"
    orbiter.box(wid, 150, 650, 420, at=(10050, y, 2000), op="new", body=wid)
    windows.append(wid)

# ---------------- Payload bay doors, open 175 deg about the sill hinges ----------------
def door_profile(sgn, n=9, t=70, open_deg=175.0):
    hy, hz = 2600, 1300                       # hinge line (sill)
    zc = (2500 ** 2 - hz ** 2 - hy ** 2) / (2 * (2500 - hz))   # closed-door arc centre (0, zc)
    r = 2500 - zc
    a0 = math.atan2(hz - zc, hy)
    c, s = math.cos(math.radians(-open_deg)), math.sin(math.radians(-open_deg))
    def place(rad, a):
        dy, dz = rad * math.cos(a) - hy, zc + rad * math.sin(a) - hz
        return (sgn * (hy + c * dy - s * dz), hz + s * dy + c * dz)
    angs = [a0 + (math.pi / 2 - a0) * k / (n - 1) for k in range(n)]
    return [place(r, a) for a in angs] + [place(r - t, a) for a in reversed(angs)]


orbiter.plane("door_pl", on="YZ", offset=-8150 - stretch)
for side, sgn in (("p", 1), ("s", -1)):
    outline(f"door_{side}_sk", "door_pl", door_profile(sgn))
    orbiter.extrude(f"door_{side}", f"door_{side}_sk", distance=18000 + stretch, op="new", body=f"door_{side}")

# ---------------- Wings: double delta (81/45 deg), airfoil sections, ruled loft ----------------
def wing_section(sid, y, xl, xt, t, zb=-2600):
    c = xl - xt
    orbiter.plane(f"{sid}_pl", on="XZ", offset=y)
    outline(sid, f"{sid}_pl", [(xl, zb + 0.32 * t), (xl - 0.08 * c, zb + 0.82 * t), (xl - 0.35 * c, zb + t),
                              (xt + 0.25 * c, zb + 0.62 * t), (xt, zb + 0.18 * t), (xt, zb),
                              (xl - 0.10 * c, zb), (xl - 0.015 * c, zb + 0.08 * t)])
    return sid


WING = [(2400, 7200, -12300, 1500), (4400, -300, -12150, 1150), (11900, -9400, -11600, 260)]
orbiter.plane("wing_tile_pl", on="XY", offset=-2470)
for side, sgn in (("p", 1), ("s", -1)):
    # an XZ plane's offset runs along -Y, so port (+Y) wing sections sit at offset -y
    secs = [wing_section(f"w{side}{i}", -sgn * y, xl, xt, t) for i, (y, xl, xt, t) in enumerate(WING)]
    orbiter.loft(f"wing_{side}", secs, ruled=True, op="new", body=f"wing_{side}")
    orbiter.split(f"wing_{side}_tiles", body=f"wing_{side}", tool="wing_tile_pl")

# ---------------- Vertical stabilizer: tapered, swept 45 deg ----------------
def fin_section(sid, z, xl, xt, t):
    c = xl - xt
    orbiter.plane(f"{sid}_pl", on="XY", offset=z)
    outline(sid, f"{sid}_pl", [(xl, 0), (xl - 0.2 * c, t / 2), (xt + 0.15 * c, 0.3 * t), (xt, 0.06 * t),
                              (xt, -0.06 * t), (xt + 0.15 * c, -0.3 * t), (xl - 0.2 * c, -t / 2)])
    return sid


orbiter.loft("tail", [fin_section("fin0", 1700, -8500, -15700, 900), fin_section("fin1", 9800, -15500, -17300, 320)],
             ruled=True, op="new", body="tail")

# ---------------- OMS pods (lofted) and nozzles ----------------
OMS = [(-7700, 350, 250), (-9300, 1000, 850), (-12700, 1050, 900), (-13700, 850, 750)]
for side, sgn in (("p", 1), ("s", -1)):
    secs = []
    for k, (x, ry, rz) in enumerate(OMS):
        sid = f"oms_{side}{k}"
        orbiter.plane(f"{sid}_pl", on="YZ", offset=x)
        with orbiter.sketch(sid, on=f"{sid}_pl") as s:
            s.ellipse("e", (sgn * 1950, 1900), ry, rz)
        secs.append(sid)
    orbiter.loft(f"oms_{side}", secs, ruled=True, op="new", body=f"oms_{side}")
    orbiter.cone(f"oms_noz_{side}", radius1=280, radius2=520, height=1000, at=(-13700, sgn * 1950, 1900),
                 direction=(-1, 0, 0), op="new", body=f"oms_noz_{side}")

# ---------------- Three RS-25 main engines: powerhead + lofted bell ----------------
BELL = [(-13000, 300), (-13700, 720), (-14900, 1030), (-15900, 1150)]
for x, _ in BELL:
    orbiter.plane(f"bell_pl_{abs(x)}", on="YZ", offset=x)
engines = []
for i, (y, z) in enumerate(((0, 950), (1350, -1150), (-1350, -1150))):
    orbiter.cylinder(f"powerhead_{i}", radius=520, height=700, at=(-12300, y, z), direction=(-1, 0, 0),
                     op="new", body=f"powerhead_{i}")
    secs = []
    for x, r in BELL:
        sid = f"bell_{i}_{abs(x)}"
        with orbiter.sketch(sid, on=f"bell_pl_{abs(x)}") as s:
            s.circle("c", (y, z), r)
        secs.append(sid)
    orbiter.loft(f"ssme_{i}", secs, ruled=True, op="new", body=f"ssme_{i}")
    engines += [f"powerhead_{i}", f"ssme_{i}"]

# ---------------- Canadarm (RMS), stowed on the port sill ----------------
ay, az = 2150, 1500
orbiter.box("rms_shoulder", 600, 500, 600, at=(9500, ay, az), op="new", body="rms_shoulder")
orbiter.cylinder("rms_upper", radius=190, height=6300, at=(9200, ay, az), direction=(-1, 0, 0), op="new", body="rms_upper")
orbiter.cylinder("rms_elbow", radius=240, height=500, at=(2800, ay - 250, az), direction=(0, 1, 0), op="new", body="rms_elbow")
orbiter.cylinder("rms_lower", radius=170, height=6100, at=(2600, ay, az), direction=(-1, 0, 0), op="new", body="rms_lower")
orbiter.box("rms_wrist", 400, 450, 450, at=(-3700, ay, az), op="new", body="rms_wrist")
orbiter.cylinder("rms_effector", radius=220, height=800, at=(-3900, ay, az), direction=(-1, 0, 0), op="new", body="rms_effector")

# ---------------- Orbiter Docking System: external airlock + NDS (docking face at orbiter_dock_z) ----------------
zr = orbiter_dock_z - 300
orbiter.box("ods_truss", 3000, 4400, 300, at=(orbiter_dock_x, 0, -1050), op="new", body="ods_truss")
orbiter.cylinder("ext_airlock", radius=800, height=3000, at=(orbiter_dock_x, 0, -1200), direction=(0, 0, 1), op="new", body="ext_airlock")
orbiter.cylinder("ods_base", radius=950, height=zr - 300 - 1800, at=(orbiter_dock_x, 0, 1800), direction=(0, 0, 1), op="new", body="ods_base")
orbiter.cylinder("nds_base", radius=1100, height=300, at=(orbiter_dock_x, 0, zr - 300), direction=(0, 0, 1), op="new", body="nds_base")
orbiter.cylinder("soft_ring", radius=850, height=300, at=(orbiter_dock_x, 0, zr), direction=(0, 0, 1), op="new", body="soft_ring")
orbiter.cylinder("ods_tunnel", radius=650, height=300, at=(orbiter_dock_x, 0, zr), direction=(0, 0, 1), op="new", body="ods_tunnel")
orbiter.combine("ods_cut", target="soft_ring", tools=["ods_tunnel"], op="cut")

# ---------------- New Shuttle: stretch the payload bay ----------------
# Everything aft of the bay (aft fuselage, wings, tail, OMS pods, engines, body flap) slides aft by `stretch`;
# the mid-fuselage and doors above grow by the same amount. The crew cabin, ODS and arm stay put.
if stretch:
    aft = ["aft_tiles_1", "aft_tiles_2", "body_flap", "tail", "wing_p_tiles_1", "wing_p_tiles_2",
           "wing_s_tiles_1", "wing_s_tiles_2", "oms_p", "oms_s", "oms_noz_p", "oms_noz_s"] + engines
    orbiter.move("stretch_aft", aft, translate=(-stretch, 0, 0))

# ---------------- Appearance ----------------
white, black, grey, silver = "#f4f4f2", "#17171a", "#6f757d", "#a7adb5"
# split pieces: hull lower halves come out as _2, wing lower halves as _1 (checked against build extents)
TILES = ["fwd_tiles_2", "mid_tiles_2", "aft_tiles_2", "wing_p_tiles_1", "wing_s_tiles_1", "body_flap"]
orbiter.material("aluminum-6061-t6", color=white, finish="matte")
orbiter.material("aluminum-6061-t6", bodies=TILES, color=black, finish="matte")
orbiter.material("glass-soda-lime", bodies=windows, color="#0b121c", finish="glossy")
orbiter.material("aluminum-6061-t6", bodies=["door_p", "door_s"], color="#e3e8ee", finish="glossy")
orbiter.material("aluminum-6061-t6", bodies=engines + ["oms_noz_p", "oms_noz_s"], color=grey, finish="brushed")
orbiter.material("aluminum-6061-t6", bodies=["ods_truss", "ods_base", "nds_base", "soft_ring", "rms_shoulder", "rms_elbow", "rms_wrist", "rms_effector"], color=silver, finish="machined")
