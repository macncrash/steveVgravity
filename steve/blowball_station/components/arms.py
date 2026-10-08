from steve import Component
from params import hub_r, pod_r, tunnel_r, segments, seg_len, cone_len, cone_r
from station_geometry import DIRS, BUILT, r0, r_tip, r_cone, at

arms = Component("arms", name="Stalks and 7-segment Spacelab pods")

tunnels, shells, flanges, cones = [], [], [], []
for i, D in enumerate(DIRS):
    if i not in BUILT:
        continue
    # stalk: pressurized tunnel from the hub collar to the pod's berthing ring
    arms.cylinder(f"tunnel_{i}", radius=tunnel_r, height=r0 - hub_r + 250, at=at(D, hub_r - 200), direction=D, op="new", body=f"tunnel_{i}")
    # seed: `segments` Spacelab segments (one shell) with a flange ring at every joint, and an end cone
    arms.cylinder(f"pod_{i}", radius=pod_r, height=segments * seg_len, at=at(D, r0), direction=D, op="new", body=f"pod_{i}")
    for j in range(segments + 1):
        arms.cylinder(f"flange_{i}_{j}", radius=pod_r + 50, height=60, at=at(D, r0 + j * seg_len - 30), direction=D, op="new", body=f"flange_{i}_{j}")
        flanges.append(f"flange_{i}_{j}")
    arms.cone(f"cone_{i}", radius1=pod_r, radius2=cone_r, height=cone_len, at=at(D, r_tip), direction=D, op="new", body=f"cone_{i}")
    # root flare: the stalk widens into the pod (as a dandelion stalk flares into its seed head). In the pod study
    # (Pod Structural Model) a flat root bulkhead bent like a plate: 77 MPa, 136 mm tip; the flare: 18 MPa, 26 mm.
    arms.cone(f"flare_{i}", radius1=tunnel_r, radius2=pod_r, height=cone_len, at=at(D, r0 - cone_len), direction=D, op="new", body=f"flare_{i}")
    tunnels.append(f"tunnel_{i}"); shells.append(f"pod_{i}"); cones += [f"cone_{i}", f"flare_{i}"]

# pod 0 (+Z, the station axis): docking adapter with a NASA Docking System ring instead of a bloom
D0 = DIRS[0]
dock = []
if 0 in BUILT:
    arms.cylinder("dock_adapter", radius=1000, height=1100, at=at(D0, r_cone), direction=D0, op="new", body="dock_adapter")
    arms.cylinder("nds_base", radius=1100, height=200, at=at(D0, r_cone + 1100), direction=D0, op="new", body="nds_base")
    arms.cylinder("soft_ring", radius=850, height=300, at=at(D0, r_cone + 1300), direction=D0, op="new", body="soft_ring")
    arms.cylinder("dock_tunnel", radius=650, height=300, at=at(D0, r_cone + 1300), direction=D0, op="new", body="dock_tunnel")
    arms.combine("soft_ring_cut", target="soft_ring", tools=["dock_tunnel"], op="cut")
    dock = ["nds_base", "soft_ring"]

arms.material("aluminum-6061-t6")
for bodies, color, finish in ((tunnels, "#d9a441", "matte"), (shells + cones + (["dock_adapter"] if dock else []), "#efece4", "matte"),
                              (flanges + dock, "#a7adb5", "machined")):
    if bodies:
        arms.material("aluminum-6061-t6", bodies=bodies, color=color, finish=finish)
