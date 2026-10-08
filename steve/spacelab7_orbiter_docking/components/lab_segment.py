from steve import Component
from params import seg_len, seg_r

lab_segment = Component("lab_segment", name="Spacelab lab segment")

# Pressure shell, MLI-wrapped
lab_segment.cylinder("shell", radius=seg_r, height=seg_len - 120, at=(60, 0, 0), direction=(1, 0, 0), op="new", body="shell")
# Joint flange rings at each end
lab_segment.cylinder("flange_a", radius=seg_r + 50, height=60, at=(0, 0, 0), direction=(1, 0, 0), op="new", body="flange_a")
lab_segment.cylinder("flange_b", radius=seg_r + 50, height=60, at=(seg_len - 60, 0, 0), direction=(1, 0, 0), op="new", body="flange_b")
# Science viewport on top, Earth-facing scientific airlock below
lab_segment.cylinder("viewport", radius=280, height=160, at=(seg_len / 2, 0, seg_r - 40), direction=(0, 0, 1), op="new", body="viewport")
lab_segment.cylinder("sci_airlock", radius=500, height=350, at=(seg_len / 2, 0, -seg_r - 300), direction=(0, 0, 1), op="new", body="sci_airlock")
# EVA handrails
lab_segment.box("rail_l", seg_len - 400, 40, 40, at=(seg_len / 2, 700, seg_r - 100 + 160), op="new", body="rail_l")
lab_segment.box("rail_r", seg_len - 400, 40, 40, at=(seg_len / 2, -700, seg_r - 100 + 160), op="new", body="rail_r")
# Side-mounted external payload adapter
lab_segment.box("payload_box", 900, 500, 700, at=(seg_len / 2, seg_r + 200, 0), op="new", body="payload_box")

lab_segment.material("aluminum-6061-t6")
lab_segment.material("aluminum-6061-t6", bodies=["shell"], finish="matte", color="#efece4")
lab_segment.material("aluminum-6061-t6", bodies=["flange_a", "flange_b"], finish="machined", color="#b9bdc3")
lab_segment.material("glass-soda-lime", bodies=["viewport"], color="#1c2a3a")
lab_segment.material("aluminum-6061-t6", bodies=["sci_airlock", "payload_box"], color="#c9a24a")
lab_segment.material("aluminum-6061-t6", bodies=["rail_l", "rail_r"], color="#e0b000")
