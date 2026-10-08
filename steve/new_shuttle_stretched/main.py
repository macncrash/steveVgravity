from steve import Design
from links import shuttle

# The New Shuttle: the linked orbiter with its payload bay stretched 8.0 m (26.3 m bay) so it carries
# the ODS plus one pod's seven berthable flight segments, clear of the OMS pods.
design = Design()
design.add(shuttle(stretch=8000))

result = design.result()
