from steve import Component
from params import seg_count, pitch, bay_len, bay_d

bay = Component("bay", name="Stretched payload-bay envelope (sills, keel, bulkheads)")

# Frame: bay axis +X from x = 0 (forward bulkhead), Z = up; segment trunnions sit at z = 0 on the sills.
half = bay_d / 2
for sgn, side in ((1, "p"), (-1, "s")):
    bay.box(f"sill_{side}", bay_len, 250, 300, at=(bay_len / 2, sgn * (half + 125), 0), op="new", body=f"sill_{side}")
bay.box("keel", bay_len, 300, 250, at=(bay_len / 2, 0, -half - 125), op="new", body="keel")
for x, name in ((0, "fwd"), (bay_len, "aft")):
    bay.plane(f"bh_{name}_pl", on="YZ", offset=x)
    with bay.sketch(f"bh_{name}_sk", on=f"bh_{name}_pl") as s:
        s.polygon("ring", (0, 0), half + 250, 24)
        s.polygon("open", (0, 0), half, 24)
    bay.extrude(f"bulkhead_{name}", f"bh_{name}_sk", distance=120, op="new", body=f"bulkhead_{name}")

bay.material("aluminum-6061-t6", color="#8e959e", finish="machined")
