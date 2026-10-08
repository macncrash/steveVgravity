from steve import Component
from params import seg_len, seg_r

radiators = Component("radiators", name="Deployable thermal radiators")

# Two edge-to-sun radiator fins below the lab, spanning segments 2-6
for side, y in (("p", 1100), ("s", -1100)):
    radiators.box(f"panel_{side}", seg_len * 4.5, 80, 4400, at=(seg_len * 3.5, y, -seg_r - 2400), op="new", body=f"panel_{side}")
    for i, x in enumerate((seg_len * 1.6, seg_len * 3.5, seg_len * 5.4)):
        radiators.box(f"strut_{side}{i}", 200, 200, 900, at=(x, y, -seg_r + 150), op="new", body=f"strut_{side}{i}")

radiators.material("aluminum-6061-t6", color="#f5f6f7", finish="glossy")
