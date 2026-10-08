from steve import Component

# Hidden motion carrier: sits at a flight segment's centre (inside it) and carries the slide + turn joints.
carrier = Component("carrier", name="Berthing motion carrier (hidden)")
carrier.box("c", 20, 20, 20, op="new", body="c")
carrier.material("aluminum-6061-t6", color="#a7adb5")
