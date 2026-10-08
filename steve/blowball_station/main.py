from steve import Design
from components.hub import hub
from components.arms import arms
from components.blooms import blooms
from components.radiators import radiators
from components.carrier import carrier
from components.effector import effector
from links import shuttle, segment
from params import shuttle_stretch, seg_len, pod_r, launches
from station_geometry import r_port, BUILT, ARRIVING, ORB_DOCK_X, ORB_DOCK_Z, berthing_plan

# Blowball Station v2: built from the same knob values as the Gravity sim "Blowball Station"
# (gravity/blowball_station.js). Change params.py to match the Gravity knobs and regenerate.
#   hub sphere -> 12 pressurized stalks -> 7-segment Spacelab pods -> sun-tracking 12 m solar blooms
#   pod 0 points +Z and carries the docking port instead of a bloom.
design = Design()
design.add(hub)
design.add(arms)
design.add(blooms)
design.add(radiators)

# New Shuttle docked at pod 0's NDS port (+Z): rolled 180 deg about X so its bay faces down at the station;
# (x, y, z) -> (x, -y, -z) puts its docking face (8300, 0, 3100) on the port (0, 0, r_port).
# It visits from launch 2 on, once the docking pod (flown with the hub) is in place.
if 0 in BUILT and launches >= 2:
    design.add(shuttle(stretch=shuttle_stretch), at=((-ORB_DOCK_X, 0, r_port + ORB_DOCK_Z), ("X", 180)))

# Berthing (launch `launches`): the arriving pod's 7 flight segments ride the arm's end effector out of the bay
# one at a time and berth from the hub outward. Each segment hangs from a chain of hidden carriers, one per arm
# leg (lift, side, out, swing, in; see station_geometry.berthing_plan), and turns onto the pod axis while it
# swings round the outside of the station; the effector is gripped rigidly at its grapple pin.
if ARRIVING is not None:
    keys, t = [], 0.0
    timing = {"lift": 1.5, "side": 3, "out": 6, "swing": 9, "turn": 9, "in": 12}   # seconds into each segment's run
    for j, (stow, legs) in enumerate(berthing_plan(), 1):
        cx, cy, cz = stow
        parent = "hub"
        for name, kind, axis, travel in legs:
            child = f"seg_{j}" if name == "turn" else f"c{j}_{name}"
            if name != "turn":
                design.add(carrier, name=child, at=(stow, ("Z", 0)))
            else:
                design.add(segment, name=child, at=((cx - seg_len / 2, cy, cz), ("X", 180)))
            joint = design.slider if kind == "slider" else design.revolute
            joint(f"{name}_{j}", parent, child, axis=axis, limits=(0, max(travel, 0.001)))
            parent = child
        design.add(effector, name=f"eff_{j}", at=((cx, cy, cz - (pod_r + 450)), ("Z", 0)))
        design.rigid(f"grip_{j}", f"seg_{j}", f"eff_{j}")
        full = {f"{name}_{j}": travel for name, _, _, travel in legs}
        keys.append(({k: 0 for k in full}, t))
        for when in sorted(set(timing.values())):
            keys.append(({f"{n}_{j}": full[f"{n}_{j}"] for n, s in timing.items() if s == when}, t + when))
        t += 12.5
    keys.append((keys[-1][0], t + 1))   # hold the finished pod for a moment
    design.animation("berthing", keys, check=True)

result = design.result()
