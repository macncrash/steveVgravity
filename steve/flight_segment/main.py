import math
from steve import Model

# One Spacelab-derived segment that can fly by itself and be berthed in orbit, end to end, by a robotic arm.
# Frame: segment axis = +X from x = 0 (passive flange) to x = L (active flange); Z = payload-bay "up".
# Spacelab segments were bolted together on the ground; this one closes both ends with pressure-rated hatched
# bulkheads (a bamboo node: every segment holds its own air) and berthing flanges, so seven of them can be joined
# one at a time into a 7-segment pod. The joint (analysis/BERTHING_RING.md): 16 capture latches on the outer rim
# pull the faces together; 20 powered bolts seal a CBM-size passage (seal on a 2.0 m circle) that carries the
# pressure load; utilities mate by themselves in the four spaces between the square hatch and the seal.
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

# Hatches (1.27 m square passage, as on the ISS Common Berthing Mechanism), flush in both bulkheads:
# each sits in a 20 mm pocket in its flange, so mated segments meet flange face to flange face
HT = 20           # mm hatch thickness
HW = 1270         # mm hatch: its corners (0.90 m from the axis) stay inside the seal
model.box("pocket_passive", HT, HW, HW, at=(HT / 2, 0, 0), op="cut", body="flange_passive")
model.box("pocket_active", HT, HW, HW, at=(L - HT / 2, 0, 0), op="cut", body="flange_active")
model.box("hatch_passive", HT, HW, HW, at=(HT / 2, 0, 0), op="new", body="hatch_passive")
model.box("hatch_active", HT, HW, HW, at=(L - HT / 2, 0, 0), op="new", body="hatch_active")

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

# ---- berthing ring details (all flush with the flange faces, so mated faces still meet face to face) ----
RS = 1000         # mm seal radius (Ø2.0 m sealed passage)
RB = 1100         # mm bolt circle, just outside the seal
NB = 20           # powered bolts (CBM: 16 on a ~1.8 m seal; 20 keep its preload margin on 2.0 m)
FD = 10           # mm depth of the seal and the utility plates
faces = (("passive", 0, 1), ("active", L - FD, -1))   # (side, x of the 10 mm face layer, inward direction)
face_parts, plates, bolts = [], [], []
for side, x0, _ in faces:
    fl = f"flange_{side}"
    model.cylinder(f"seal_cut_{side}", radius=RS + 20, height=FD, at=(x0, 0, 0), direction=(1, 0, 0), op="cut", body=fl)
    model.cylinder(f"seal_{side}", radius=RS + 20, height=FD, at=(x0, 0, 0), direction=(1, 0, 0), op="new", body=f"seal_{side}")
    model.cylinder(f"seal_in_{side}", radius=RS - 20, height=FD, at=(x0, 0, 0), direction=(1, 0, 0), op="cut", body=f"seal_{side}")
    model.cylinder(f"land_{side}", radius=RS - 20, height=FD, at=(x0, 0, 0), direction=(1, 0, 0), op="new", body=f"land_{side}")
    model.box(f"land_hatch_{side}", FD, HW, HW, at=(x0 + FD / 2, 0, 0), op="cut", body=f"land_{side}")
    face_parts += [f"seal_{side}", f"land_{side}"]
    # utility plates in the four spaces between hatch and seal: air (top), water (bottom), power + data A / B
    for k, util in enumerate(("air", "pwr_a", "water", "pwr_b")):
        a = math.pi / 2 - k * math.pi / 2
        cy, cz = 800 * math.cos(a), 800 * math.sin(a)
        sy, sz = (700, 180) if k % 2 == 0 else (180, 700)
        model.box(f"plate_cut_{util}_{side}", FD, sy, sz, at=(x0 + FD / 2, cy, cz), op="cut", body=f"land_{side}")
        model.box(f"plate_{util}_{side}", FD, sy, sz, at=(x0 + FD / 2, cy, cz), op="new", body=f"plate_{util}_{side}")
        plates.append(f"plate_{util}_{side}")
    # bolt circle: nut wells on the passive face, flush bolt heads on the active face
    for i in range(NB):
        a = 2 * math.pi * (i + 0.5) / NB
        y, z = RB * math.cos(a), RB * math.sin(a)
        xh = 0 if side == "passive" else L - 15
        model.cylinder(f"bolt_hole_{side}_{i}", radius=30, height=15, at=(xh, y, z), direction=(1, 0, 0), op="cut", body=fl)
        if side == "active":
            model.cylinder(f"bolt_{i}", radius=25, height=15, at=(xh, y, z), direction=(1, 0, 0), op="new", body=f"bolt_{i}")
            bolts.append(f"bolt_{i}")

# Umbilical mating adapters for the external ammonia loop (as on ISS truss segments): active plug on the active rim,
# passive pad on the passive rim, between latches; they meet when the latches close
umas = []
for j, a in enumerate((math.radians(11.25), math.radians(191.25))):
    y, z = (R + 110) * math.cos(a), (R + 110) * math.sin(a)
    model.box(f"uma_active_{j}", 100, 160, 120, at=(L - FL / 2, y, z), op="new", body=f"uma_active_{j}")
    model.box(f"uma_passive_{j}", 100, 160, 120, at=(FL / 2, y, z), op="new", body=f"uma_passive_{j}")
    umas += [f"uma_active_{j}", f"uma_passive_{j}"]

model.material("aluminum-6061-t6")
model.material("aluminum-6061-t6", bodies=["shell"], finish="matte", color="#efece4")
model.material("aluminum-6061-t6", bodies=["flange_passive"], finish="machined", color="#a7adb5")
model.material("aluminum-6061-t6", bodies=["flange_active"] + latches, finish="machined", color="#7d848d")
model.material("aluminum-6061-t6", bodies=["hatch_passive", "hatch_active"], color="#3a4048")
model.material("titanium-6al-4v", bodies=pins, finish="machined", color="#c0c4c8")
model.material("aluminum-6061-t6", bodies=["grapple_base", "grapple_pin"], color="#c9a24a")
model.material("aluminum-6061-t6", bodies=["grapple_target", "rail_p", "rail_s"], color="#e0b000")
model.material("aluminum-6061-t6", bodies=["seal_passive", "seal_active"], color="#1c1d20")
model.material("aluminum-6061-t6", bodies=["land_passive", "land_active"], finish="machined", color="#c4c9cf")
model.material("aluminum-6061-t6", bodies=plates, color="#b87333")
model.material("stainless-304", bodies=bolts, finish="machined", color="#e6e8ea")
model.material("aluminum-6061-t6", bodies=umas, color="#3b6fb6")

result = model.result()
