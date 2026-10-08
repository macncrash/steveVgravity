import math
from steve import Model

# One Spacelab-derived segment that can fly by itself and be berthed in orbit, end to end, by a robotic arm.
# Frame: segment axis = +X from x = 0 (passive flange) to x = L (active flange); Z = payload-bay "up".
# Spacelab segments were bolted together on the ground; this one closes both ends with hatched
# bulkheads and full-diameter berthing flanges (a CBM-style ring of powered bolts and capture latches)
# so seven of them can be joined one at a time into a 7-segment pod.
R = 2030          # mm Spacelab outer radius (4.06 m)
SHELL = 2700      # mm Spacelab segment length
FL = 100          # mm berthing flange thickness, each end
L = SHELL + 2 * FL

model = Model()

model.cylinder("shell", radius=R, height=SHELL, at=(FL, 0, 0), direction=(1, 0, 0), op="new", body="shell")
model.cylinder("flange_passive", radius=R + 50, height=FL, at=(0, 0, 0), direction=(1, 0, 0), op="new", body="flange_passive")
model.cylinder("flange_active", radius=R + 50, height=FL, at=(FL + SHELL, 0, 0), direction=(1, 0, 0), op="new", body="flange_active")

# 16 capture latches around the active flange rim, inside the segment's length so stowed segments
# don't touch (they pull the next segment's passive flange in, then the bolts drive)
latches = []
for i in range(16):
    a = 2 * math.pi * i / 16
    lid = f"latch_{i}"
    model.box(lid, 100, 120, 120, at=(L - FL / 2, (R + 110) * math.cos(a), (R + 110) * math.sin(a)), op="new", body=lid)
    latches.append(lid)

# Hatches (1.27 m square passage, as on the ISS Common Berthing Mechanism), flush in both bulkheads
model.box("hatch_passive", 20, 1500, 1500, at=(-10, 0, 0), op="new", body="hatch_passive")
model.box("hatch_active", 20, 1500, 1500, at=(L + 10, 0, 0), op="new", body="hatch_active")

# Payload-bay mounting: four longeron trunnions (+/-Y) and a keel pin (-Z), like every Shuttle payload
pins = []
for x in (FL + 500, FL + SHELL - 500):
    for sgn in (1, -1):
        pid = f"trunnion_{'p' if sgn > 0 else 's'}_{x}"
        model.cylinder(pid, radius=80, height=450, at=(x, sgn * (R - 50), 0), direction=(0, sgn, 0), op="new", body=pid)
        pins.append(pid)
model.cylinder("keel_pin", radius=80, height=350, at=(FL + SHELL / 2, 0, -(R - 50)), direction=(0, 0, -1), op="new", body="keel_pin")
pins.append("keel_pin")

# Grapple fixture on top (the arm's handle) and two EVA handrails
model.box("grapple_base", 450, 450, 120, at=(FL + SHELL / 2, 0, R + 40), op="new", body="grapple_base")
model.cylinder("grapple_pin", radius=60, height=350, at=(FL + SHELL / 2, 0, R + 100), direction=(0, 0, 1), op="new", body="grapple_pin")
model.cylinder("grapple_target", radius=150, height=40, at=(FL + SHELL / 2 + 350, 0, R + 100), direction=(0, 0, 1), op="new", body="grapple_target")
for sgn in (1, -1):
    model.box(f"rail_{'p' if sgn > 0 else 's'}", SHELL - 400, 40, 40, at=(FL + SHELL / 2, sgn * 800, R + 120), op="new", body=f"rail_{'p' if sgn > 0 else 's'}")

model.material("aluminum-6061-t6")
model.material("aluminum-6061-t6", bodies=["shell"], finish="matte", color="#efece4")
model.material("aluminum-6061-t6", bodies=["flange_passive"], finish="machined", color="#a7adb5")
model.material("aluminum-6061-t6", bodies=["flange_active"] + latches, finish="machined", color="#7d848d")
model.material("aluminum-6061-t6", bodies=["hatch_passive", "hatch_active"], color="#3a4048")
model.material("titanium-6al-4v", bodies=pins, finish="machined", color="#c0c4c8")
model.material("aluminum-6061-t6", bodies=["grapple_base", "grapple_pin"], color="#c9a24a")
model.material("aluminum-6061-t6", bodies=["grapple_target", "rail_p", "rail_s"], color="#e0b000")

result = model.result()
