import math
from steve import Component
from params import bloom_d, mast, hub_r
from station_geometry import DIRS, BUILT, SUN, HUB_BLOOM, r_cone, at

blooms = Component("blooms", name="Sun-tracking circular solar arrays (the pappus)")

# Each pod except pod 0 ends in a gimbal mast and a circular fan-fold array (UltraFlex-style), all turned face-on
# to the sun (+X): ~354 W/m2 new, so ~80 kW per 17 m bloom. The hub carries one more on a long mast through the
# widest gap between pods (station_geometry.hub_bloom_dir): launch 1's power, as ISS's P6 array was.
R = bloom_d / 2
masts, discs, spars, gimbals = [], [], [], []


def bloom(tag, D, r_from, length, mast_r=250):
    c = at(D, r_from + length)
    blooms.cylinder(f"mast_{tag}", radius=mast_r, height=length, at=at(D, r_from), direction=D, op="new", body=f"mast_{tag}")
    blooms.cylinder(f"gimbal_{tag}", radius=450, height=500, at=tuple(c[j] - SUN[j] * 500 for j in range(3)), direction=SUN, op="new", body=f"gimbal_{tag}")
    # 24-gore disc (a polygon, like the fan-fold gores, and mesher-friendly at this size), face-on to the sun
    blooms.plane(f"disc_pl_{tag}", on="YZ", offset=c[0])
    with blooms.sketch(f"disc_sk_{tag}", on=f"disc_pl_{tag}") as s:
        s.polygon("gores", (c[1], c[2]), R, 24)
    blooms.extrude(f"disc_{tag}", f"disc_sk_{tag}", distance=60, op="new", body=f"disc_{tag}")
    for g in range(12):
        a = 2 * math.pi * g / 12
        u = (0.0, math.cos(a), math.sin(a))
        blooms.cylinder(f"spar_{tag}_{g}", radius=70, height=R, at=tuple(c[j] - SUN[j] * 70 for j in range(3)), direction=u, op="new", body=f"spar_{tag}_{g}")
        spars.append(f"spar_{tag}_{g}")
    masts.append(f"mast_{tag}"); discs.append(f"disc_{tag}"); gimbals.append(f"gimbal_{tag}")


for i, D in enumerate(DIRS):
    if i == 0 or i not in BUILT:
        continue
    bloom(i, D, r_cone, mast)
if 0 in BUILT:     # the hub bloom flies with launch 1 (hub + docking pod); its mast is 4x a pod's, so stouter
    bloom("hub", HUB_BLOOM, hub_r - 200, r_cone + mast - hub_r + 200, mast_r=400)

blooms.material("aluminum-6061-t6")
if discs:
    blooms.material("pc", bodies=discs, color="#1b2f6e", finish="glossy")
    blooms.material("aluminum-6061-t6", bodies=spars, color="#e9edf2", finish="satin")
    blooms.material("aluminum-6061-t6", bodies=masts + gimbals, color="#8e959e", finish="machined")
