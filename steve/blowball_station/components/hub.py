import math
from steve import Component
from params import hub_r, tunnel_r
from station_geometry import DIRS, at

hub = Component("hub", name="Hub sphere (receptacle)")

# Faceted sphere: a 24-sided half-polygon revolved, so every face is a cone (singly curved).
# A true sphere this large crashes STEVE's full-build print mesher (signal 11).
seg = 24
pts = [(hub_r * math.sin(math.pi * i / seg), hub_r * math.cos(math.pi * i / seg)) for i in range(seg + 1)]
with hub.sketch("shell_sk", on="XZ") as s:
    for i in range(seg):
        s.line(f"f{i}", pts[i], pts[i + 1])
    s.line("axis", pts[-1], pts[0])
hub.revolve("shell", "shell_sk", axis="Z", op="new", body="shell")

collars = []
for i, D in enumerate(DIRS):
    hub.cylinder(f"collar_{i}", radius=tunnel_r + 300, height=450, at=at(D, hub_r - 200), direction=D, op="new", body=f"collar_{i}")
    collars.append(f"collar_{i}")

hub.material("aluminum-6061-t6", color="#eceae3", finish="matte")
hub.material("aluminum-6061-t6", bodies=collars, color="#a7adb5", finish="machined")
