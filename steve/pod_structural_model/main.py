import math
from steve import Model

# One Blowball pod as a single solid for structural and modal studies, cantilevered from the hub collar.
# Frame: pod axis +Z, hub collar face at z = 0 (the support).
# "Smeared" idealisation: each wall stands for skin + stringers + ring frames, and the study's material density
# is set so the solid carries the whole pod's mass from the mass budget (analysis/MASS_BUDGET.md).
STALK_R, STALK_T, STALK_L = 600, 20, 6250        # mm pressurized tunnel (Ø1.2 m)
POD_R, POD_T, POD_L = 2030, 40, 20300            # mm seven 2.9 m flight segments (Ø4.06 m)
BULK = 60                                        # mm end bulkheads
HALF = True                                      # keep only y >= 0: symmetry about the X-Z plane halves the mesh
                                                 # (studies hold the cut face in y; loads must lie in the X-Z plane)
FLARE = True                                     # conical stalk-to-pod transition (False: flat root bulkhead only)
CONE_L, CONE_T = 1300, 30                        # mm flare length (= a Spacelab end cone) and wall thickness

model = Model()

# stalk tube, running 60 mm into the root bulkhead (or 10 mm into the flare) so the parts fuse into one solid
stalk_h = (STALK_L - CONE_L + 10) if FLARE else (STALK_L + BULK)
model.cylinder("stalk", radius=STALK_R, height=stalk_h, at=(0, 0, 0), direction=(0, 0, 1), op="new", body="pod")
model.cylinder("stalk_bore", radius=STALK_R - STALK_T, height=stalk_h, at=(0, 0, 0), direction=(0, 0, 1), op="new", body="stalk_bore")
model.combine("stalk_tube", target="pod", tools=["stalk_bore"], op="cut")
if FLARE:
    # The flat root bulkhead alone bends like a plate under the pod's moment (STEVE static: 77 MPa, 136 mm tip).
    # A cone carries the moment in membrane action instead, as the dandelion stalk flares into its seed head.
    slope = math.atan2(POD_R - STALK_R, CONE_L)
    off = CONE_T / math.cos(slope)                # radial offset that gives the wall its normal thickness
    z0 = STALK_L - CONE_L
    model.cone("flare", radius1=STALK_R, radius2=POD_R, height=CONE_L, at=(0, 0, z0), direction=(0, 0, 1), op="new", body="flare")
    model.cone("flare_in", radius1=STALK_R - off, radius2=POD_R - off, height=CONE_L, at=(0, 0, z0), direction=(0, 0, 1),
               op="new", body="flare_in")
    model.combine("flare_shell", target="flare", tools=["flare_in"], op="cut")
    model.combine("fuse_flare", target="pod", tools=["flare"], op="join")

# pod shell with closed root and tip bulkheads; the root bulkhead has the 1.16 m passage from the stalk
model.cylinder("shell", radius=POD_R, height=POD_L, at=(0, 0, STALK_L), direction=(0, 0, 1), op="new", body="shell")
model.cylinder("cabin", radius=POD_R - POD_T, height=POD_L - 2 * BULK, at=(0, 0, STALK_L + BULK), direction=(0, 0, 1), op="new", body="cabin")
model.combine("hollow", target="shell", tools=["cabin"], op="cut")
model.cylinder("passage", radius=STALK_R - STALK_T, height=BULK, at=(0, 0, STALK_L), direction=(0, 0, 1), op="new", body="passage")
model.combine("open_root", target="shell", tools=["passage"], op="cut")
model.combine("fuse", target="pod", tools=["shell"], op="join")
if HALF:
    model.box("minus_y", 5000, 2500, STALK_L + POD_L + 1000, at=(0, -1250, (STALK_L + POD_L) / 2), op="new", body="minus_y")
    model.combine("symmetry_cut", target="pod", tools=["minus_y"], op="cut")

model.material("aluminum-6061-t6")
result = model.result()
