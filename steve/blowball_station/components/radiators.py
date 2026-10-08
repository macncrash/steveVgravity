from steve import Component
from params import pod_r, rad_w
from station_geometry import DIRS, BUILT, r0, pod_len, at, edge_on_frame, axis_angle

radiators = Component("radiators", name="Radiator fins, edge-on to the sun")

# Two fins per pod over its outer 60 %, in the plane holding the pod axis and the sun line,
# so the sun only ever sees their edges. Inner ends start far enough out to clear neighbouring pods.
L = 0.6 * pod_len
mid = r0 + 0.65 * pod_len
off = pod_r + 400 + rad_w / 2
fins, struts = [], []
for i, D in enumerate(DIRS):
    if i not in BUILT:
        continue
    d, w, n = edge_on_frame(D)
    axis, deg = axis_angle(d, w, n)
    radiators.axis(f"ax_{i}", through=(0, 0, 0), direction=axis)
    for s, sgn in (("a", 1), ("b", -1)):
        fid = f"fin_{i}{s}"
        radiators.box(fid, L, rad_w, 80, at=(0, 0, 0), op="new", body=fid)
        centre = tuple(D[j] * mid + w[j] * sgn * off for j in range(3))
        radiators.move(f"{fid}_place", [fid], rotate=(f"ax_{i}", deg), translate=centre)
        fins.append(fid)
        for q, frac in enumerate((0.45, 0.85)):
            sid = f"strut_{i}{s}{q}"
            base = tuple(D[j] * (r0 + frac * pod_len) + w[j] * sgn * (pod_r - 50) for j in range(3))
            radiators.cylinder(sid, radius=90, height=450, at=base, direction=tuple(w[j] * sgn for j in range(3)), op="new", body=sid)
            struts.append(sid)

radiators.material("aluminum-6061-t6", color="#f5f6f7", finish="glossy")
if struts:
    radiators.material("aluminum-6061-t6", bodies=struts, color="#a7adb5", finish="machined")
