from steve import Design
from components.orbiter import orbiter

# Space Shuttle orbiter with an Orbiter Docking System carrying a NASA Docking System (IDSS) ring.
# Local frame: nose +X, payload bay opens +Z, +Y = port. The docking face is the plane z = orbiter_dock_z,
# centred at (orbiter_dock_x, 0). Place it in a station by mapping that point onto the station's port.
design = Design()
design.add(orbiter)

result = design.result()
