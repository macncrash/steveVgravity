import math
from steve import Component
from params import bloom_d, mast
from station_geometry import DIRS, BUILT, SUN, r_cone, at

blooms = Component("blooms", name="Sun-tracking circular solar arrays (the pappus)")

# Each pod except pod 0 ends in a gimbal mast and a 12 m circular fan-fold array (UltraFlex-style),
# all turned face-on to the sun (+X). ~350 W/m2 at 30 % cells: ~40 kW per bloom at the default size.
R = bloom_d / 2
masts, discs, spars, gimbals = [], [], [], []
for i, D in enumerate(DIRS):
    if i == 0 or i not in BUILT:
        continue
    c = at(D, r_cone + mast)
    blooms.cylinder(f"mast_{i}", radius=250, height=mast, at=at(D, r_cone), direction=D, op="new", body=f"mast_{i}")
    blooms.cylinder(f"gimbal_{i}", radius=450, height=500, at=tuple(c[j] - SUN[j] * 500 for j in range(3)), direction=SUN, op="new", body=f"gimbal_{i}")
    # 24-gore disc (a polygon, like the fan-fold gores, and mesher-friendly at this size), face-on to the sun
    blooms.plane(f"disc_pl_{i}", on="YZ", offset=c[0])
    with blooms.sketch(f"disc_sk_{i}", on=f"disc_pl_{i}") as s:
        s.polygon("gores", (c[1], c[2]), R, 24)
    blooms.extrude(f"disc_{i}", f"disc_sk_{i}", distance=60, op="new", body=f"disc_{i}")
    for g in range(12):
        a = 2 * math.pi * g / 12
        u = (0.0, math.cos(a), math.sin(a))
        blooms.cylinder(f"spar_{i}_{g}", radius=70, height=R, at=tuple(c[j] - SUN[j] * 70 for j in range(3)), direction=u, op="new", body=f"spar_{i}_{g}")
        spars.append(f"spar_{i}_{g}")
    masts.append(f"mast_{i}"); discs.append(f"disc_{i}"); gimbals.append(f"gimbal_{i}")

blooms.material("aluminum-6061-t6")
if discs:
    blooms.material("pc", bodies=discs, color="#1b2f6e", finish="glossy")
    blooms.material("aluminum-6061-t6", bodies=spars, color="#e9edf2", finish="satin")
    blooms.material("aluminum-6061-t6", bodies=masts + gimbals, color="#8e959e", finish="machined")
