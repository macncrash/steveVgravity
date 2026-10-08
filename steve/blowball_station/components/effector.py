from steve import Component

# Station arm end effector, gripping a flight segment's grapple pin (origin = pin tip, arm hangs along -Z).
effector = Component("effector", name="Arm end effector")
effector.cylinder("snare", radius=230, height=900, at=(0, 0, 0), direction=(0, 0, -1), op="new", body="snare")
effector.box("wrist", 520, 520, 520, at=(0, 0, -1160), op="new", body="wrist")
effector.cylinder("boom", radius=190, height=1000, at=(0, 0, -1420), direction=(0, 0, -1), op="new", body="boom")
effector.material("aluminum-6061-t6", color="#e9edf2", finish="satin")
effector.material("aluminum-6061-t6", bodies=["snare", "wrist"], color="#a7adb5", finish="machined")
