# Blowball Station: berthing ring (step 3)

**Question:** MASS_BUDGET.md found that a full-diameter pressure joint needs 24–82 CBM-class bolts. Is there a better joint, and what has to cross it?

**Answer:** seal only a CBM-size passage, and let every segment hold its own air behind a pressure-rated bulkhead, the way bamboo closes every internode with a node. The joint then needs **20 bolts instead of 82**, half the seal length, and nothing that the bulkheads did not already need. Modelled in STEVE as Flight Segment revision 5.

## Why the bulkhead decides it

- **Every segment needs a pressure-rated bulkhead anyway.** If a segment is holed, the crew shuts its hatches and the bulkheads must hold a full atmosphere on one side. The same holds on the ground (leak test of each segment) and in the bay (each segment flies sealed).
- With a full-diameter joint the bulkheads carry nothing in normal use, and the bolt ring carries the whole end load. With a sealed passage the bulkheads carry it, and the joint carries only the passage.
- So the full-diameter joint pays for the pressure load twice.

## The two joints

| | Full diameter | **Sealed passage (chosen)** |
|---|---:|---:|
| Seal radius | 2.03 m | **1.00 m** |
| Pressure load across the joint | 1,312 kN | **318 kN** |
| Bolts at the CBM's preload margin (5.2×, 84.5 kN each) | 82 | **20** (fitted: 20) |
| Worst bolt with the 166 kN·m root moment added | 17.9 kN | **31.0 kN** |
| Preload over worst bolt load (joint stays closed) | 4.7× | **2.7×** |
| Seal length per joint | 12.8 m | **6.3 m** |
| Seal length, whole station (12 pods × 8 joints) | 1,224 m | **603 m** |

**Why not one bulkhead per joint?** Two segments meeting put two bulkheads back to back; one would do for isolating a leak. But a segment with an open end fills its whole cross-section with air, so the seal must then sit at full diameter: back to 82 bolts. The second bulkhead (≈318 kg) weighs about what the extra 62 powered bolts would at ≈5 kg each (≈310 kg, EST, before the heavier flange), and buys a sealed segment for the ground leak test and the ride up, a double barrier, and a small leak-check volume.

The 166 kN·m is the docking and acceleration moment at the pod root (STRUCTURAL.md), an upper bound for every segment joint further out. The 16 capture latches on the outer rim add a second load path for that moment and are not counted.

## The bulkhead

A clamped Ø4.06 m sandwich plate (Al 2219 faces on a 150 mm honeycomb core, EST) under one atmosphere:

- Edge moment p·a²/8 = 52.2 kN·m/m, so each face needs 2.3 mm at 150 MPa (2.0 pressure factor on 2219-T87, EST).
- Centre deflection 14 mm.
- Mass ≈ 268 kg of plate + 51 kg of hatch frame = **318 kg**. MASS_BUDGET.md now takes its bulkhead line from this script (it had guessed 300 kg each).
- The edge moment and shear go into the berthing flange, which is already budgeted as the stiff ring frame they need. A shallow dome would be lighter but costs rack length.

## What crosses the joint

Everything mates by itself when the bolts drive, as on the ISS truss segments: no crew jumpers across 84 joints. The pressurised utilities sit on four plates in the spaces between the square hatch and the round seal (copper in the renders); the ammonia stays outside the seal.

| Line | Sized for | Connector |
|---|---|---|
| Power A / Power B (side plates) | 40 kW each, the bloom's full output in sun, at 160 V DC: 250 A per bus, ≈83 mm² of copper per pole. Either bus alone carries everything. | self-mating power pins, as the ISS truss UMAs |
| Data (side plates, with power) | 2 × fibre pairs per bus (Ethernet), plus a hard-wired bolt-and-latch status loop | self-mating fibre ferrules |
| Air (top plate) | one pod's air (263 m³) to the hub once an hour (EST): 73 L/s, a Ø152 mm supply and a return duct at 4 m/s | IMV-style valve on each face; works with the hatch shut |
| Water (bottom plate) | the pod's 19.6 kW to the heat exchanger at 10 K rise: 0.47 kg/s, Ø24 mm supply + return at 1 m/s | dry-break quick disconnects |
| Ammonia (outer rim, blue) | the same 19.6 kW out to the radiator fins, two loops: 0.28 kg/s in all, Ø16 mm lines per loop | two umbilical mating adapters between latches, outside the pressure seal: a leak can't reach the cabin |

## Berthing sequence (one joint)

1. The arm brings the segment into the capture envelope, active flange to passive flange.
2. The 16 capture latches on the outer rim close and pull the faces together.
3. The 20 powered bolts drive in stages to 84.5 kN preload. The utility plates and the umbilical adapters mate as the faces close.
4. Leak check: the space between the two closed hatches inside the seal is only a few litres, so a pressure decay test there is quick and sensitive.
5. Open both hatches. Power, data, air and water are already connected.

## In the STEVE model (Flight Segment revision 5)

- Seal ring Ø2.0 m on both faces, 20 bolt heads on a Ø2.2 m circle (wells on the passive face), the 1.27 m hatch, four utility plates, two ammonia umbilical adapters on the rim between latches.
- Everything on the faces is flush, so mated segments still meet face to face, and the berthing collision check stays meaningful.

## Not modelled (never claimed)

- Seal design, leak rates, bolt actuators, latch kinematics and alignment guides.
- Connector designs, misalignment tolerance of the self-mating plates.
- Thermal distortion of the faces between sun and shade.
- Fatigue of the bolts over many docking cycles.

## Sources

- **cbm:** NASA NTRS 20100001671: CBM, 16 powered bolts preloaded to ≈84.5 kN (19 kip); 1.27 m (50 in) square hatch
- **iss_eps:** NASA: ISS primary power 160 V DC from the arrays, secondary 124 V DC
- **iss_truss:** NASA: ISS truss segments are joined by the Segment-to-Segment Attach System; their Umbilical Mating Adapters connect power, data and ammonia lines by themselves when the bolts drive
- **iss_imv:** NASA: ISS modules exchange air through Intermodule Ventilation (IMV) ducts and valves at the hatches
- **structural:** STRUCTURAL.md / pod_beam_check.py: 133 kN·m docking moment + 33 kN·m from 0.05 m/s² at the pod root
- **power:** POWER_THERMAL.md: 40 kW per bloom new, 0.85 at end of life, 0.569 usable through the eclipse
