from steve import Component
from params import seg_r, cone_len, cone_r

aft_cone = Component("aft_cone", name="Aft end cone + iROSA power truss")

aft_cone.cone("cone", radius1=seg_r, radius2=cone_r, height=cone_len, at=(0, 0, 0), direction=(-1, 0, 0), op="new", body="cone")
aft_cone.cylinder("mast", radius=350, height=3600, at=(-cone_len, 0, 0), direction=(-1, 0, 0), op="new", body="mast")
aft_cone.box("gimbal", 900, 2400, 900, at=(-3500, 0, 0), op="new", body="gimbal")

# Roll-out solar array wings (iROSA-style), one each side
for side, sgn in (("p", 1), ("s", -1)):
    aft_cone.box(f"blanket_{side}", 4600, 16000, 40, at=(-3500, sgn * 9400, 0), op="new", body=f"blanket_{side}")
    aft_cone.cylinder(f"mandrel_{side}", radius=220, height=5000, at=(-1000, sgn * 17500, 0), direction=(-1, 0, 0), op="new", body=f"mandrel_{side}")
    aft_cone.cylinder(f"root_{side}", radius=220, height=5000, at=(-1000, sgn * 1300, 0), direction=(-1, 0, 0), op="new", body=f"root_{side}")
    for edge, x in (("a", -1150), ("b", -5850)):
        aft_cone.cylinder(f"boom_{side}{edge}", radius=70, height=16400, at=(x, sgn * 1300, 0), direction=(0, sgn, 0), op="new", body=f"boom_{side}{edge}")

aft_cone.material("aluminum-6061-t6")
aft_cone.material("aluminum-6061-t6", bodies=["cone"], finish="matte", color="#efece4")
aft_cone.material("aluminum-6061-t6", bodies=["mast", "gimbal"], color="#9aa0a8")
aft_cone.material("pc", bodies=["blanket_p", "blanket_s"], finish="glossy", color="#1d2f6b")
aft_cone.material("aluminum-6061-t6", bodies=["mandrel_p", "mandrel_s", "root_p", "root_s"], color="#c9a24a")
