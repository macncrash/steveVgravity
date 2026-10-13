"""Blowball Station mass budget: per flight segment, per pod, per launch and for the whole station.

python3 mass_budget.py            -> prints the tables and writes MASS_BUDGET.md next to this file

Every line is either a published reference value (SOURCES) or a labelled estimate (EST). Orders of magnitude only.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "renders", "tools", "station"))
import station_geometry as G  # noqa: E402  (same layout + order as the STEVE design)
from berthing_ring import N_BOLT, bulkhead  # noqa: E402  (BERTHING_RING.md: the joint and the bulkhead)
from params import bloom_d, mast, rad_w  # noqa: E402
from power_thermal import EOL, T_ECL, DOD, WH_PER_KG, USABLE, bloom_kw  # noqa: E402  (POWER_THERMAL.md)

SOURCES = {
    "spacelab": "ESA: Spacelab-1 pressure module 8,145 kg (two 2.7 m segments + two end cones, outfitted)",
    "destiny": "NASA: Destiny 14,515 kg, 8.5 m long, 4.3 m dia (≈1.71 t/m)",
    "columbus": "ESA: Columbus 10,275 kg empty / 12,775 kg at launch, 6.87 m long (≈1.50 / 1.86 t/m)",
    "radiator": "NASA: ISS ATCS radiators ≈7.0 kg/m²",
    "ultraflex": "NASA JPL ST8: UltraFlex-175, 175 W/kg BOL",
    "cbm": "NASA NTRS 20100001671: CBM, 16 powered bolts preloaded to ≈84.5 kN (19 kip)",
}

BLOOM_W = bloom_kw(bloom_d) * 1000                   # W in full sun, new
FIN_M2 = 0.6 * G.pod_len / 1000 * rad_w / 1000          # one radiator fin (station_mesh, radiators.py)
GIMBAL_KG, MAST_KG_M = 270, 33.0                        # EST: the old 520 kg for a 7.5 m mast and its gimbal, split
HUB_MAST_M = (G.r_cone + mast - G.hub_r) / 1000          # the hub bloom's mast: hub surface to bloom centre
BATT_KG = round(bloom_kw(bloom_d) * EOL * USABLE * T_ECL / 60 / DOD / WH_PER_KG * 1000)

# ---------------- one flight segment (2.7 m Spacelab shell + two berthing flanges) ----------------
SEGMENT = [
    # (item, kg, basis)
    ("Shell, frames, MMOD shield and subsystems (Spacelab share)", 3250, "spacelab: 8,145 kg less ~0.8 t per end cone, ÷ 2 segments"),
    ("Two pressure-rated sandwich bulkheads with 1.27 m hatches", 2 * round(bulkhead()["total"]),
     "BERTHING_RING.md: clamped plate under 1 atm, EST faces and core"),
    (f"Two berthing flanges: 16 capture latches, {N_BOLT} bolts on a Ø2.0 m sealed passage, utility plates (EST)", 550,
     "EST: CBM-class hardware; the flange is also the bulkhead's edge ring"),
    ("Racks and outfitting (EST)", 950, "EST: Spacelab-1 flew ~3 t of payload across 2 segments + pallet"),
]
# ---------------- per pod, besides its seven segments ----------------
POD_EXTRA = [
    ("End cone", 800, "spacelab: cone share"),
    ("Stalk: 6.25 m pressurized tunnel Ø1.2 m + two berthing rings (EST)", 1500, "EST"),
    (f"Radiators: 2 fins × {FIN_M2:.0f} m² at 7 kg/m² + pumps and plumbing", round(2 * FIN_M2 * 7) + 300, "radiator"),
    (f"Solar bloom: Ø{bloom_d / 1000:.0f} m, {BLOOM_W / 1000:.0f} kW BOL array at 175 W/kg + {mast / 1000:.1f} m mast "
     "+ 2-axis gimbal", round(BLOOM_W / 175 + GIMBAL_KG + MAST_KG_M * mast / 1000), "ultraflex + EST mast/gimbal"),
    (f"Batteries: one {T_ECL:.0f} min eclipse at the bloom's usable end-of-life power, {DOD * 100:.0f} % DOD, "
     f"{WH_PER_KG:.0f} Wh/kg (EST)", BATT_KG, "EST, as POWER_THERMAL.md (unshaded bloom)"),
]
DOCKING_POD_EXTRA = [("End cone", 800, "spacelab"), ("Stalk (EST)", 1500, "EST"),
                     ("Radiators", round(2 * FIN_M2 * 7) + 300, "radiator"), ("Docking adapter + NDS ring (EST)", 900, "EST")]
HUB = [
    ("6 m pressure sphere, MMOD shield (113 m² × ~25 kg/m², EST)", 2850, "EST"),
    ("12 berthing collars (EST)", 12 * 400, "EST"),
    ("Attitude control: 4 control moment gyros (EST, ISS-class)", 1100, "EST"),
    ("Propulsion module dry + 3 t propellant (EST)", 6000, "EST"),
    ("Core avionics and life support (EST)", 3500, "EST: was 4 t with temporary arrays, now replaced by the hub bloom"),
]
HUB_BLOOM = [   # the hub's own bloom (POWER_THERMAL.md): flies with launch 1, off-centre in the widest gap between pods
    (f"Hub bloom: Ø{bloom_d / 1000:.0f} m, {BLOOM_W / 1000:.0f} kW BOL array at 175 W/kg + 2-axis gimbal",
     round(BLOOM_W / 175 + GIMBAL_KG), "ultraflex + EST gimbal"),
    (f"Hub bloom mast: {HUB_MAST_M:.1f} m truss at 1.5 × a pod mast's {MAST_KG_M:.0f} kg/m (EST)",
     round(1.5 * MAST_KG_M * HUB_MAST_M), "EST"),
    ("Hub bloom batteries, as a pod's (EST)", BATT_KG, "EST, as POWER_THERMAL.md"),
]


def total(rows):
    return sum(r[1] for r in rows)


seg = total(SEGMENT)
pod = 7 * seg + total(POD_EXTRA)
pod0 = 7 * seg + total(DOCKING_POD_EXTRA)
hub = total(HUB) + total(HUB_BLOOM)
station = hub + pod0 + 11 * pod
seg_vol = math.pi * 2.03 ** 2 * 2.9
station_vol = 12 * 7 * seg_vol + 4 / 3 * math.pi * 3 ** 3

# ---------------- berthing-flange bolt check (cabin pressure across a full-diameter joint) ----------------
P = 101325.0
flange_r = 2.03
end_load = P * math.pi * flange_r ** 2                     # N, pushes the pod's end bulkhead outward through every joint
cbm_end_load = P * math.pi * 0.9 ** 2                      # N, CBM interface (~1.8 m sealed diameter)
bolts_needed = math.ceil(end_load * 1.5 / 84.5e3)          # 1.5 × pressure load carried by preload, CBM-class bolts
cbm_margin = 16 * 84.5e3 / cbm_end_load                    # CBM's own preload-to-pressure-load ratio (≈5×)
bolts_cbm_margin = math.ceil(end_load * cbm_margin / 84.5e3)

# ---------------- centre of mass by launch, with these masses ----------------
def com_by_launch():
    out = []
    for L in range(1, 13):
        built = G.ORDER[:L]
        m = hub
        # the hub bloom's array and mast sit off-centre; its batteries and the rest of the hub at the centre
        hb = [(HUB_BLOOM[0][1], G.r_cone + mast), (HUB_BLOOM[1][1], (G.hub_r + G.r_cone + mast) / 2)]
        cm = [sum(kg * G.HUB_BLOOM[k] * r for kg, r in hb) for k in range(3)]
        for q in built:
            D = G.DIRS[q]
            for j in range(7):
                r = G.r0 + (j + 0.5) * 2900
                for k in range(3):
                    cm[k] += seg * D[k] * r
            extra = DOCKING_POD_EXTRA if q == 0 else POD_EXTRA
            # radius of each extra item, in the order listed: end cone, stalk, radiators, bloom / docking adapter,
            # batteries (in the end cone, at the foot of the mast)
            radii = [G.r_tip + 650, (G.hub_r + G.r0) / 2, G.fin_mid(q),
                     G.r_cone + 550 if q == 0 else G.r_cone + mast, G.r_tip + 650]
            for (_, kg, _), r in zip(extra, radii):
                for k in range(3):
                    cm[k] += kg * D[k] * r
            m += 7 * seg + total(extra)
        off = math.sqrt(sum(c * c for c in cm)) / m / 1000
        out.append((L, m / 1000, off))
    return out


def table(rows, unit="kg"):
    return "\n".join(f"| {r[0]} | {r[1]:,} | {r[2]} |" for r in rows)


def report():
    lines = [
        "# Blowball Station: mass budget",
        "",
        "Generated by `analysis/mass_budget.py`. Values are published references (see Sources) or labelled estimates",
        "(EST). Treat them as orders of magnitude.",
        "",
        "## One flight segment (2.9 m, Ø4.06 m)",
        "",
        "| Item | kg | Basis |", "|---|---:|---|", table(SEGMENT),
        f"| **Segment total** | **{seg:,}** | {seg / 2900:.2f} t/m (Destiny 1.71, Columbus 1.50–1.86) |",
        "",
        "## One pod = 7 segments + extras",
        "",
        "| Item | kg | Basis |", "|---|---:|---|",
        f"| 7 flight segments | {7 * seg:,} | above |", table(POD_EXTRA),
        f"| **Pod total (one New Shuttle launch)** | **{pod:,}** | the docking pod (pod 0): {pod0:,} kg |",
        "",
        "## Hub",
        "",
        "| Item | kg | Basis |", "|---|---:|---|", table(HUB), table(HUB_BLOOM), f"| **Hub total** | **{hub:,}** | |",
        "",
        "## Station",
        "",
        "| | |", "|---|---|",
        f"| Total mass | **{station / 1000:,.0f} t** (the earlier 4 t/segment placeholder gave ~372 t) |",
        f"| Pressurized volume | {station_vol:,.0f} m³ |",
        f"| Launch 1 (heavy lift: hub + docking pod) | {(hub + pod0) / 1000:.1f} t |",
        f"| Launches 2–12 (New Shuttle, one pod each) | {pod / 1000:.1f} t each |",
        "",
        "### What this changes",
        "",
        f"- **The New Shuttle must lift ~{pod / 1000:.0f} t to station orbit, not 32 t.** That is about {pod / 16000:.1f}× the original "
        "Shuttle's ~16 t to ISS orbit. The vehicle needs Starship-class lift, or the pod has to be split across two flights.",
        f"- Launch 1 (hub + docking pod) is about {(hub + pod0) / 1000:.0f} t: Starship-class.",
        "",
        "## Centre of mass by launch (opposite-pair order, these masses)",
        "",
        "| Launch | Station mass (t) | CoM off the hub (m) |", "|---:|---:|---:|",
        *[f"| {L} | {m:,.0f} | {o:.2f} |" for L, m, o in com_by_launch()],
        "",
        "## Berthing flange: bolts against cabin pressure",
        "",
        f"- With every hatch open, the pressure on a pod's end bulkhead passes through every segment joint:",
        f"  p·π·r² = 101.3 kPa × π × 2.03² = **{end_load / 1000:,.0f} kN**.",
        f"- An ISS CBM carries ≈{cbm_end_load / 1000:,.0f} kN across a ~1.8 m seal, with 16 bolts at ≈84.5 kN preload each.",
        f"- With CBM-class bolts, a full-diameter flange needs **{bolts_needed} bolts** to hold a bare 1.5× the pressure "
        f"load in preload, or **{bolts_cbm_margin} bolts** to match the CBM's own margin ({cbm_margin:.1f}× preload over "
        "pressure load). The model's 16 latches are not enough on their own.",
        f"- **Decided ([BERTHING_RING.md](BERTHING_RING.md)):** keep the pressure inside each segment behind its own "
        f"bulkheads and seal only a Ø2.0 m passage, held by {N_BOLT} bolts at the CBM's margin. The 16 latches capture "
        "and pull in; the bolts seal.",
        "",
        "## Sources",
        "",
        *[f"- {v}" for v in SOURCES.values()],
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    md = report()
    open(os.path.join(HERE, "MASS_BUDGET.md"), "w").write(md)
    print(md)
