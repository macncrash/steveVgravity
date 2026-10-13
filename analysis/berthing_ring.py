"""Blowball Station berthing ring: where the pressure joint goes, how many bolts, the bulkhead, and what crosses it.

python3 berthing_ring.py          -> prints the report and writes BERTHING_RING.md next to this file

The question MASS_BUDGET.md left open: a full-diameter pressure joint needs 24-82 CBM-class bolts. Keep the
pressure inside each segment and seal only a CBM-size passage instead? Every number is a published value
(SOURCES) or a labelled estimate (EST). Orders of magnitude only.
"""
import math
import os

from power_thermal import EOL, USABLE, bloom_kw  # POWER_THERMAL.md
from params import bloom_d

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCES = {
    "cbm": "NASA NTRS 20100001671: CBM, 16 powered bolts preloaded to ≈84.5 kN (19 kip); 1.27 m (50 in) square hatch",
    "iss_eps": "NASA: ISS primary power 160 V DC from the arrays, secondary 124 V DC",
    "iss_truss": "NASA: ISS truss segments are joined by the Segment-to-Segment Attach System; their Umbilical "
                 "Mating Adapters connect power, data and ammonia lines by themselves when the bolts drive",
    "iss_imv": "NASA: ISS modules exchange air through Intermodule Ventilation (IMV) ducts and valves at the hatches",
    "structural": "STRUCTURAL.md / pod_beam_check.py: 133 kN·m docking moment + 33 kN·m from 0.05 m/s² at the pod root",
    "power": "POWER_THERMAL.md: a bloom's power new, 0.85 at end of life, 0.569 usable through the eclipse",
}

P = 101325.0                       # Pa, cabin pressure
R_SHELL = 2.03                     # m, Spacelab shell radius (full-diameter seal would sit here)
R_SEAL, R_BOLT, N_BOLT = 1.00, 1.10, 20   # m, m, -: the chosen passage (steve/flight_segment rev 5)
CBM_SEAL_R, CBM_BOLTS, BOLT_PRELOAD = 0.90, 16, 84.5e3
BOLT_KG = 5.0                      # kg, EST: one powered bolt with its nut, actuator share and fitting
M_JOINT = 133e3 + 33e3             # N·m, docking + acceleration moment at the pod root: an upper bound for every joint
HATCH = 1.27                       # m, square hatch


def pressure_load(r):
    return P * math.pi * r * r


CBM_MARGIN = CBM_BOLTS * BOLT_PRELOAD / pressure_load(CBM_SEAL_R)   # the CBM's own preload / pressure load


def bolts(r_seal, r_bolt, n=None):
    """Bolts needed to keep the CBM's preload margin, and with n bolts the worst bolt's load (pressure + moment)."""
    F = pressure_load(r_seal)
    need = math.ceil(F * CBM_MARGIN / BOLT_PRELOAD)
    n = n or need
    worst = F / n + 2 * M_JOINT / (n * r_bolt)          # bolt ring in bending: peak bolt force 2M/(n·r)
    return F, need, n, worst, BOLT_PRELOAD / worst      # separation margin = preload / worst applied load


# ---------------- the bulkhead (every segment holds its own air, as a bamboo node does) ----------------
SIGMA = 150e6        # Pa, EST: allowable for Al 2219-T87 face sheets at a 2.0 pressure factor
E = 73.1e9
CORE_H = 0.15        # m, EST: sandwich depth
CORE_RHO = 50.0      # kg/m³, EST: aluminium honeycomb
RHO = 2840.0         # kg/m³, Al 2219


def bulkhead():
    """Clamped circular sandwich plate under cabin pressure (Roark: edge moment p·a²/8, centre deflection p·a⁴/64D).
    The hatch carries its own load into a frame, so the plate is treated as solid: conservative for stress."""
    a = R_SHELL
    M = P * a * a / 8                      # N·m/m at the clamped edge
    tf = M / (SIGMA * CORE_H)              # m, each face
    tf = max(tf, 1.5e-3)                   # EST: minimum gauge
    D = E * tf * CORE_H ** 2 / 2
    w = P * a ** 4 / (64 * D)
    area = math.pi * a * a
    kg_plate = area * (2 * tf * RHO + CORE_H * CORE_RHO)
    kg_frames = 4 * HATCH * 10.0           # EST: hatch frame 10 kg/m; the clamped edge is the berthing flange itself
    return dict(M=M, tf=tf, w=w, plate=kg_plate, frames=kg_frames, total=kg_plate + kg_frames)


# ---------------- what crosses the joint ----------------
BLOOM_KW = bloom_kw(bloom_d)       # in full sun, new: the joint must pass all of it toward the hub
POD_HEAT_KW = BLOOM_KW * EOL * USABLE + 2 * 0.12   # usable bloom power (all ends as heat) + 2 crew, unshaded bloom
V_BUS = 160.0                      # V, iss_eps primary
J_CU = 3.0                         # A/mm², EST: copper in a pressurised, ventilated cabin
SEG_VOL = math.pi * R_SHELL ** 2 * 2.9
AIR_CHANGES_PER_H = 1.0            # EST: a whole pod's air to the hub's air revitalisation once an hour
DUCT_V = 4.0                       # m/s, EST: duct velocity (quiet)
WATER_DT, NH3_DT, NH3_CP = 10.0, 15.0, 4.7e3   # K, K, J/kg·K (single-phase liquid ammonia, as ISS ATCS)
PIPE_V = 1.0                       # m/s, EST


def utilities():
    amps = BLOOM_KW * 1e3 / V_BUS
    air = 7 * SEG_VOL * AIR_CHANGES_PER_H / 3600
    duct = 2 * math.sqrt(air / DUCT_V / math.pi)
    water = POD_HEAT_KW * 1e3 / (4186 * WATER_DT)
    nh3 = POD_HEAT_KW * 1e3 / (NH3_CP * NH3_DT)
    pipe = lambda kg_s, rho: 2 * math.sqrt(kg_s / rho / PIPE_V / math.pi)
    return [
        ("Power A / Power B (side plates)", f"{BLOOM_KW:.0f} kW each, the bloom's full output in sun, at {V_BUS:.0f} V DC: "
         f"{amps:.0f} A per bus, ≈{amps / J_CU:.0f} mm² of copper per pole. Either bus alone carries everything.",
         "self-mating power pins, as the ISS truss UMAs"),
        ("Data (side plates, with power)", "2 × fibre pairs per bus (Ethernet), plus a hard-wired bolt-and-latch "
         "status loop", "self-mating fibre ferrules"),
        ("Air (top plate)", f"one pod's air ({7 * SEG_VOL:.0f} m³) to the hub once an hour (EST): {air * 1000:.0f} L/s, "
         f"a Ø{duct * 1000:.0f} mm supply and a return duct at {DUCT_V:.0f} m/s", "IMV-style valve on each face; works with "
         "the hatch shut"),
        ("Water (bottom plate)", f"the pod's {POD_HEAT_KW:.1f} kW to the heat exchanger at {WATER_DT:.0f} K rise: "
         f"{water:.2f} kg/s, Ø{pipe(water, 1000) * 1000:.0f} mm supply + return at {PIPE_V:.0f} m/s",
         "dry-break quick disconnects"),
        ("Ammonia (outer rim, blue)", f"the same {POD_HEAT_KW:.1f} kW out to the radiator fins, two loops: "
         f"{nh3:.2f} kg/s in all, Ø{pipe(nh3 / 2, 680) * 1000:.0f} mm lines per loop", "two umbilical mating adapters "
         "between latches, outside the pressure seal: a leak can't reach the cabin"),
    ]


def report():
    full = bolts(R_SHELL, R_SHELL + 0.05)
    pas = bolts(R_SEAL, R_BOLT, N_BOLT)
    bh = bulkhead()
    lines = [
        "# Blowball Station: berthing ring (step 3)", "",
        "**Question:** MASS_BUDGET.md found that a full-diameter pressure joint needs 24–82 CBM-class bolts. Is "
        "there a better joint, and what has to cross it?", "",
        "**Answer:** seal only a CBM-size passage, and let every segment hold its own air behind a pressure-rated "
        "bulkhead, the way bamboo closes every internode with a node. The joint then needs "
        f"**{N_BOLT} bolts instead of {full[1]}**, half the seal length, and nothing that the bulkheads did not "
        "already need. Modelled in STEVE as Flight Segment revision 5.", "",
        "## Why the bulkhead decides it", "",
        "- **Every segment needs a pressure-rated bulkhead anyway.** If a segment is holed, the crew shuts its "
        "hatches and the bulkheads must hold a full atmosphere on one side. The same holds on the ground (leak test "
        "of each segment) and in the bay (each segment flies sealed).",
        "- With a full-diameter joint the bulkheads carry nothing in normal use, and the bolt ring carries the whole "
        "end load. With a sealed passage the bulkheads carry it, and the joint carries only the passage.",
        "- So the full-diameter joint pays for the pressure load twice.", "",
        "## The two joints", "",
        "| | Full diameter | **Sealed passage (chosen)** |", "|---|---:|---:|",
        f"| Seal radius | {R_SHELL:.2f} m | **{R_SEAL:.2f} m** |",
        f"| Pressure load across the joint | {full[0] / 1e3:,.0f} kN | **{pas[0] / 1e3:,.0f} kN** |",
        f"| Bolts at the CBM's preload margin ({CBM_MARGIN:.1f}×, 84.5 kN each) | {full[1]} | **{pas[1]}** (fitted: {N_BOLT}) |",
        f"| Worst bolt with the {M_JOINT / 1e3:.0f} kN·m root moment added | {full[3] / 1e3:.1f} kN | **{pas[3] / 1e3:.1f} kN** |",
        f"| Preload over worst bolt load (joint stays closed) | {full[4]:.1f}× | **{pas[4]:.1f}×** |",
        f"| Seal length per joint | {2 * math.pi * R_SHELL:.1f} m | **{2 * math.pi * R_SEAL:.1f} m** |",
        f"| Seal length, whole station (12 pods × 8 joints) | {96 * 2 * math.pi * R_SHELL:,.0f} m | "
        f"**{96 * 2 * math.pi * R_SEAL:,.0f} m** |",
        "",
        f"**Why not one bulkhead per joint?** Two segments meeting put two bulkheads back to back; one would do "
        "for isolating a leak. But a segment with an open end fills its whole cross-section with air, so the seal "
        f"must then sit at full diameter: back to {full[1]} bolts. The second bulkhead (≈{bh['total']:.0f} kg) weighs "
        f"about what the extra {full[1] - N_BOLT} powered bolts would at ≈{BOLT_KG:.0f} kg each "
        f"(≈{(full[1] - N_BOLT) * BOLT_KG:.0f} kg, EST, before the heavier flange), and buys a sealed segment for "
        "the ground leak test and the ride up, a double barrier, and a small leak-check volume.", "",
        f"The {M_JOINT / 1e3:.0f} kN·m is the docking and acceleration moment at the pod root (STRUCTURAL.md), an "
        "upper bound for every segment joint further out. The 16 capture latches on the outer rim add a second "
        "load path for that moment and are not counted.", "",
        "## The bulkhead", "",
        f"A clamped Ø{2 * R_SHELL:.2f} m sandwich plate (Al 2219 faces on a {CORE_H * 1000:.0f} mm honeycomb core, EST) "
        "under one atmosphere:", "",
        f"- Edge moment p·a²/8 = {bh['M'] / 1e3:.1f} kN·m/m, so each face needs {bh['tf'] * 1000:.1f} mm at "
        f"{SIGMA / 1e6:.0f} MPa (2.0 pressure factor on 2219-T87, EST).",
        f"- Centre deflection {bh['w'] * 1000:.0f} mm.",
        f"- Mass ≈ {bh['plate']:.0f} kg of plate + {bh['frames']:.0f} kg of hatch frame = **{bh['total']:.0f} kg**. "
        "MASS_BUDGET.md now takes its bulkhead line from this script (it had guessed 300 kg each).",
        "- The edge moment and shear go into the berthing flange, which is already budgeted as the stiff ring "
        "frame they need. A shallow dome would be lighter but costs rack length.", "",
        "## What crosses the joint", "",
        "Everything mates by itself when the bolts drive, as on the ISS truss segments: no crew jumpers across "
        "84 joints. The pressurised utilities sit on four plates in the spaces between the square hatch and the "
        "round seal (copper in the renders); the ammonia stays outside the seal.", "",
        "| Line | Sized for | Connector |", "|---|---|---|",
        *[f"| {a} | {b} | {c} |" for a, b, c in utilities()],
        "",
        "## Berthing sequence (one joint)", "",
        "1. The arm brings the segment into the capture envelope, active flange to passive flange.",
        "2. The 16 capture latches on the outer rim close and pull the faces together.",
        f"3. The {N_BOLT} powered bolts drive in stages to 84.5 kN preload. The utility plates and the umbilical "
        "adapters mate as the faces close.",
        "4. Leak check: the space between the two closed hatches inside the seal is only a few litres, so a pressure "
        "decay test there is quick and sensitive.",
        "5. Open both hatches. Power, data, air and water are already connected.", "",
        "## In the STEVE model (Flight Segment revision 5)", "",
        "- Seal ring Ø2.0 m on both faces, 20 bolt heads on a Ø2.2 m circle (wells on the passive face), the 1.27 m "
        "hatch, four utility plates, two ammonia umbilical adapters on the rim between latches.",
        "- Everything on the faces is flush, so mated segments still meet face to face, and the berthing collision "
        "check stays meaningful.", "",
        "## Not modelled (never claimed)", "",
        "- Seal design, leak rates, bolt actuators, latch kinematics and alignment guides.",
        "- Connector designs, misalignment tolerance of the self-mating plates.",
        "- Thermal distortion of the faces between sun and shade.",
        "- Fatigue of the bolts over many docking cycles.", "",
        "## Sources", "",
        *[f"- **{k}:** {v}" for k, v in SOURCES.items()],
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    md = report()
    open(os.path.join(HERE, "BERTHING_RING.md"), "w").write(md)
    print(md)
