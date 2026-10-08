from steve import Component
from params import seg_r, cone_len, cone_r

forward_cone = Component("forward_cone", name="Forward end cone + NDS docking adapter")

forward_cone.cone("cone", radius1=seg_r, radius2=cone_r, height=cone_len, at=(0, 0, 0), direction=(1, 0, 0), op="new", body="cone")
# Pressurized docking adapter (IDA-style) with an IDSS / NASA Docking System ring
forward_cone.cylinder("adapter", radius=1000, height=1100, at=(cone_len, 0, 0), direction=(1, 0, 0), op="new", body="adapter")
forward_cone.cylinder("nds_base", radius=1100, height=200, at=(cone_len + 1100, 0, 0), direction=(1, 0, 0), op="new", body="nds_base")
forward_cone.cylinder("soft_ring", radius=850, height=300, at=(cone_len + 1300, 0, 0), direction=(1, 0, 0), op="new", body="soft_ring")
forward_cone.cylinder("tunnel", radius=650, height=300, at=(cone_len + 1300, 0, 0), direction=(1, 0, 0), op="new", body="tunnel")
forward_cone.combine("ring_cut", target="soft_ring", tools=["tunnel"], op="cut")
# Docking target / camera boom
forward_cone.box("target", 80, 300, 300, at=(cone_len + 1560, 0, 1250), op="new", body="target")
forward_cone.box("target_post", 80, 60, 400, at=(cone_len + 1560, 0, 1000), op="new", body="target_post")

forward_cone.material("aluminum-6061-t6")
forward_cone.material("aluminum-6061-t6", bodies=["cone", "adapter"], finish="matte", color="#efece4")
forward_cone.material("aluminum-6061-t6", bodies=["nds_base", "soft_ring"], finish="machined", color="#a7adb5")
forward_cone.material("aluminum-6061-t6", bodies=["target", "target_post"], color="#1a1a1a")
