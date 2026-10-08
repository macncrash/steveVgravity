from steve import Design
from params import seg_count, pitch, bay_len
from components.bay import bay
from links import segment

# One launch = one pod: seven berthable flight segments stowed nose-to-tail in a stretched payload bay.
# In orbit the station arm lifts them out one at a time (grapple fixture on top) and berths each to the
# last, growing the pod outward from the hub like a stalk.
design = Design()
design.add(bay)
# segments' trunnions (z = 0) seat on the sills; centred in the bay with 100 mm between flanges
design.pattern(segment, count=seg_count, direction=(1, 0, 0), spacing=pitch,
               at=(((bay_len - seg_count * pitch + 100) / 2, 0, 0), ("Z", 0)))

result = design.result()
