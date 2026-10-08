from steve import Design
from params import seg_len, seg_count, port_x, orbiter_dock_x, orbiter_dock_z
from components.lab_segment import lab_segment
from components.aft_cone import aft_cone
from components.forward_cone import forward_cone
from components.radiators import radiators
from components.orbiter import orbiter

design = Design()

# Seven pressurized Spacelab lab segments along +X, end to end
design.pattern(lab_segment, count=seg_count, direction=(1, 0, 0), spacing=seg_len)
design.add(aft_cone)
design.add(forward_cone, at=((seg_len * seg_count, 0, 0), ("Z", 0)))
design.add(radiators)

# Orbiter docked at the forward NDS port: payload bay faces the station (-X), nose up (+Z).
# Rotating -90 deg about Y maps orbiter local (x, y, z) -> (-z, y, x); its docking face
# (orbiter_dock_x, 0, orbiter_dock_z) lands on the station port face (port_x, 0, 0).
design.add(orbiter, at=((port_x + orbiter_dock_z, 0, -orbiter_dock_x), ("Y", -90)))

result = design.result()
