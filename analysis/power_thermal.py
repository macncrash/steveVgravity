"""Blowball Station power and thermal balance, launch by launch.

python3 power_thermal.py          -> prints the tables and writes POWER_THERMAL.md next to this file

Attitude: the station holds the sun on +X (as in the STEVE model): every bloom faces the sun and every radiator fin
is edge-on to it. Shadowing then depends only on what is built, so it is measured once per launch by drawing the
station as seen from the sun (orthographic, painter's order) from the same tessellation as the renders, and counting
the pixels of each bloom that stay on top. Every other number is a published value or a labelled estimate (EST).
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(HERE, "..", "renders", "tools")
sys.path.insert(0, TOOLS)
sys.path.insert(0, os.path.join(TOOLS, "station"))
import station_mesh as M  # noqa: E402
from orbiter_mesh import orbiter_bodies  # noqa: E402
from params import bloom_d, mast, pod_r, rad_w, shuttle_stretch  # noqa: E402
from render_mesh import subdivide  # noqa: E402

G = M.G
SOURCES = {
    "iss_power": "NASA: ISS solar arrays generate 84–120 kW; pressurized volume 916 m³",
    "leo": "LEO at ~400 km: 92 min orbit, up to ~36 min in eclipse (β = 0°)",
    "earth": "Earth: mean outgoing IR ≈ 237 W/m², Bond albedo ≈ 0.30, solar constant 1361 W/m²",
    "coating": "ISS radiator coating (Z-93 class white): ε ≈ 0.92, α ≈ 0.14",
}

# ---------------- generation ----------------
KW_PER_M2 = 40.0 / (math.pi * 6.0 ** 2)   # ≈354 W/m² in full sun when new (≈26 % cells): 40 kW on a 12 m bloom


def bloom_kw(d_mm):
    """A bloom's array power in full sun, new (kW)."""
    return KW_PER_M2 * math.pi * (d_mm / 2000) ** 2


BLOOM_KW_BOL = bloom_kw(bloom_d)            # per bloom, as MASS_BUDGET.md
EOL = 0.85                   # EST: 15 years of cell degradation
T_ORBIT, T_ECL = 92.0, 36.0  # min (leo, worst case β = 0)
T_SUN = T_ORBIT - T_ECL
ETA_BATT = 0.85              # EST: battery charge-discharge round trip, Li-ion + regulation
# continuous load L that a sunlit array power P can carry through the eclipse: P·t_sun = L·t_sun + L·t_ecl/η
USABLE = T_SUN / (T_SUN + T_ECL / ETA_BATT)
DOD = 0.35                   # EST: depth of discharge for ~5,700 LEO cycles a year
WH_PER_KG = 100.0            # EST: packaged Li-ion battery, ISS-class ORUs

# ---------------- demand ----------------
ISS_KW_PER_M3 = 100.0 / 916  # iss_power: ~100 kW used across 916 m³ (≈0.11 kW/m³), heavy-science density
CREW_W = 120.0               # EST: metabolic heat per person
CREW_PER_POD = 2             # EST

# ---------------- heat rejection ----------------
SIGMA = 5.670e-8
EPS, ALPHA = 0.92, 0.14      # coating
T_RAD = (265.0, 275.0, 285.0)  # K, EST: mean fin temperature (cold, nominal, warm ammonia loop)
F_EARTH = 0.70               # EST: orbit-average view factor to Earth, both faces of a fin together
FIN_EFF = 0.90               # EST: fin efficiency (temperature drop away from the coolant tubes)
EARTH_IR, ALBEDO, SOLAR = 237.0, 0.30, 1361.0
FIN_AREA = 2 * 0.6 * G.pod_len / 1000 * rad_w / 1000    # m², two fins per pod (one face each), as station_mesh


def fin_kw_per_m2(T):
    """Net rejection per m² of fin (both faces radiate; Earth IR and albedo absorbed, the sun is edge-on)."""
    emit = 2 * EPS * SIGMA * T ** 4 * FIN_EFF
    absorbed = F_EARTH * (EPS * EARTH_IR + ALPHA * ALBEDO * SOLAR * T_SUN / T_ORBIT * 0.5)  # albedo: day side, ~half
    return (emit - absorbed) / 1000


# ---------------- shadowing, seen from the sun ----------------
PX = 50.0                    # mm per pixel
SPAN = 60000.0               # mm: half-width of the view (y and z)


def sun_view(built, shuttle):
    """{pod: lit fraction of its bloom} for the station `built`, seen from +X (the sun)."""
    # masts and spars are left out: in the simplified mesh each mast runs in its own disc's plane up to the centre
    # (a real bloom sits on its gimbal, ahead of the mast), and a 0.5 m mast shades another bloom negligibly
    bodies = [(t, c) for t, c, _ in M.station_bodies(built) if c not in (M.COL["mast"], M.COL["spar"])]
    if shuttle and 0 in built:
        R = np.diag([1.0, -1.0, -1.0])
        t = np.array([-G.ORB_DOCK_X, 0, G.r_port + G.ORB_DOCK_Z])
        bodies += [(tr @ R.T + t, c) for tr, c, *_ in orbiter_bodies(stretch=shuttle_stretch)]
    tris, ids, disc_of = [], [], {}
    centres = {q: np.array(G.at(G.DIRS[q], G.r_cone + M.mast)) for q in built if q != 0}
    centres["hub"] = np.array(G.at(G.HUB_BLOOM, G.r_cone + M.mast))      # the hub's own bloom flies with launch 1
    for b, (t, col) in enumerate(bodies):
        if col == M.COL["disc"]:
            c = t.reshape(-1, 3).mean(axis=0)
            disc_of[b] = min(centres, key=lambda q: np.linalg.norm(centres[q] - c))
        t = subdivide(t, 1500)
        tris.append(t)
        ids.append(np.full(len(t), b + 1))
    tris, ids = np.concatenate(tris), np.concatenate(ids)
    order = np.argsort(tris[:, :, 0].mean(axis=1))          # far from the sun first; nearer ones paint over
    N = int(2 * SPAN / PX)
    img = Image.new("I", (N, N), 0)
    draw = ImageDraw.Draw(img)
    uv = (tris[:, :, 1:] + SPAN) / PX
    for i in order:
        draw.polygon([tuple(p) for p in uv[i]], fill=int(ids[i]))
    buf = np.asarray(img)
    full = 12 * (M.bloom_d / 2) ** 2 * math.sin(2 * math.pi / 24) / PX ** 2   # the disc is a 24-gon (station_mesh)
    counts = np.bincount(buf.ravel(), minlength=len(bodies) + 1)
    return {q: min(1.0, counts[b + 1] / full) for b, q in disc_of.items()}


def pod_volume():
    return math.pi * (pod_r / 1000) ** 2 * (G.pod_len / 1000)


HUB_VOL = 4 / 3 * math.pi * (M.hub_r / 1000) ** 3


def stages():
    rows = []
    for L in range(1, len(G.ORDER) + 1):
        built = set(G.ORDER[:L])
        lit = sun_view(built, shuttle=False)
        lit_s = sun_view(built, shuttle=True) if L >= 2 else lit
        blooms = len(lit)
        sun_kw = sum(BLOOM_KW_BOL * f for f in lit.values())
        avg_bol, avg_eol = sun_kw * USABLE, sun_kw * USABLE * EOL
        avg_eol_shuttle = sum(BLOOM_KW_BOL * f for f in lit_s.values()) * USABLE * EOL
        vol = HUB_VOL + L * pod_volume()
        demand = ISS_KW_PER_M3 * vol
        heat_kw = avg_eol + L * CREW_PER_POD * CREW_W / 1000      # all usable power ends up as heat, plus crew
        reject = {T: L * FIN_AREA * fin_kw_per_m2(T) for T in T_RAD}
        rows.append(dict(L=L, pod=G.ORDER[L - 1], blooms=blooms, shade=1 - (sum(lit.values()) / blooms if blooms else 1),
                         shade_s=1 - (sum(lit_s.values()) / blooms if blooms else 1), worst=min(lit.values(), default=1),
                         sun_kw=sun_kw, avg_bol=avg_bol, avg_eol=avg_eol, avg_eol_shuttle=avg_eol_shuttle,
                         vol=vol, demand=demand, density=avg_eol / vol, heat=heat_kw, reject=reject))
    return rows


def set_bloom(d_mm):
    """Draw every bloom (and its mast: radius + 1.5 m, as params.py) at another diameter."""
    M.bloom_d, M.mast = d_mm, d_mm // 2 + 1500


def bloom_sweep(diams=(12000, 14000, 15000, 16000, 16500, 17000, 17500)):
    """Shading and usable end-of-life power for other bloom diameters (shading grows with size): the full station,
    and the worst launch-by-launch balance against demand at ISS density."""
    rows = []
    for D in diams:
        set_bloom(D)
        worst, full = None, None
        for L in range(1, len(G.ORDER) + 1):
            built = set(G.ORDER[:L])
            lit = sun_view(built, shuttle=False)
            kw = sum(bloom_kw(D) * f for f in lit.values()) * USABLE * EOL
            bal = kw - ISS_KW_PER_M3 * (HUB_VOL + L * pod_volume())
            worst = bal if worst is None else min(worst, bal)
            full = (1 - sum(lit.values()) / len(lit), kw)
        rows.append((D, *full, worst))
    set_bloom(bloom_d)
    return rows


def battery(load_kw):
    """Usable energy for one eclipse at this load, and the packaged battery mass at DOD."""
    kwh = load_kw * T_ECL / 60
    return kwh, kwh / DOD / WH_PER_KG * 1000     # kWh, kg


def report(rows, sweep):
    f = rows[-1]
    short = [r for r in rows if r["avg_eol"] < r["demand"]]
    hub_kw = bloom_kw(bloom_d) * USABLE * EOL
    out = ["# Blowball Station: power and thermal balance (step 2)", "",
           "**Question:** do the blooms power the station, and can the radiators get rid of the heat, at every launch?", "",
           f"**Answer:** yes, with Ø{bloom_d / 1000:.0f} m blooms, a bloom on the hub, and {rad_w / 1000:.1f} m "
           "radiator fins (the Ø12 m blooms, no hub array and 3 m fins of the first pass fell short; see the history below).",
           f"- **Full station:** {f['avg_eol']:.0f} kW orbit-average usable at end of life ({f['avg_bol']:.0f} kW new) "
           f"against {f['demand']:.0f} kW at ISS's power density: {f['density'] * 1000:.0f} W/m³, "
           f"{f['density'] / ISS_KW_PER_M3 * 100:.0f} % of ISS's {ISS_KW_PER_M3 * 1000:.0f} W/m³.",
           f"- **Launch 1 has power now.** The hub carries its own bloom on a {(G.r_cone + mast - M.hub_r) / 1000:.1f} m "
           f"mast in the widest gap between pods, as ISS's first truss segment (P6) did. It gives ≈{hub_kw:.0f} kW "
           "usable at end of life and stays on as the hub's own supply.",
           ("- **Every launch is in surplus" + (f" except launch {', '.join(str(r['L']) for r in short)}" if short else "")
            + "**" + (f": {short[0]['avg_eol']:.0f} kW against {short[0]['demand']:.0f} kW "
                      f"({short[0]['avg_eol'] / short[0]['demand'] * 100:.0f} %), and launch 1 flies uncrewed."
                      if short else ".")),
           f"- **Radiators keep a margin at every launch:** {min(r['reject'][275.0] / r['heat'] for r in rows if r['heat']):.2f}× "
           f"or better at 275 K ({f['reject'][275.0] / f['heat']:.2f}× at full bloom).",
           f"- **Shadowing costs {f['shade'] * 100:.0f} % of the bloom area at full bloom** "
           f"({f['shade_s'] * 100:.0f} % with the New Shuttle docked), mostly on far-side blooms behind other pods. "
           "The hub bloom is never shaded.",
           f"- **Batteries:** riding through a {T_ECL:.0f} min eclipse at full load needs "
           f"≈{battery(f['avg_eol'])[1] / 1000:.1f} t of batteries in all, carried in MASS_BUDGET.md.", "",
           "## Assumptions", "",
           "- **Attitude:** sun held on +X, as in the STEVE model. Every bloom faces the sun, every radiator fin is "
           "edge-on to it, and shadowing changes only as pods are added.",
           f"- **Blooms:** Ø{bloom_d / 1000:.0f} m, {BLOOM_KW_BOL:.0f} kW each in full sun when new "
           f"({KW_PER_M2 * 1000:.0f} W/m², ≈26 % cells, as the first pass's 40 kW on Ø12 m); {EOL:.2f} × that at end "
           f"of life (EST). Each sits on a mast of radius + 1.5 m ({mast / 1000:.1f} m), as in Gravity.",
           f"- **Orbit:** {T_ORBIT:.0f} min with {T_ECL:.0f} min of eclipse (worst case). Batteries carry the "
           f"eclipse at {ETA_BATT:.2f} round trip (EST), so the usable continuous power is {USABLE:.3f} × the "
           "sunlit array power.",
           f"- **Demand:** ISS density, ≈{ISS_KW_PER_M3 * 1000:.0f} W per m³ pressurized (≈100 kW over 916 m³). "
           "This is a heavy-science benchmark, not a requirement.",
           f"- **Heat:** all usable power becomes heat, plus {CREW_PER_POD} crew per pod at {CREW_W:.0f} W (EST). "
           "Heat soaking in through the MLI is not counted.",
           f"- **Radiators:** {FIN_AREA:.1f} m² of fin per pod (two {rad_w / 1000:.1f} m × {0.6 * G.pod_len / 1000:.1f} m "
           f"fins), both faces radiating. ε {EPS}, α {ALPHA} (Z-93-class white), fin efficiency {FIN_EFF} (EST). "
           f"Orbit-average view factor to Earth {F_EARTH} for both faces together (EST). Net rejection per m² of "
           "fin: " + ", ".join(f"{fin_kw_per_m2(T) * 1000:.0f} W at {T:.0f} K" for T in T_RAD) + ".",
           "- **Shadowing:** the station drawn as seen from the sun at 50 mm per pixel, from the same tessellation "
           "as the renders (station_mesh.py, orbiter_mesh.py). Masts and spars are left out (see the code).", "",
           "## Launch by launch", "",
           "Blooms include the hub's.", "",
           "| Launch | Pod | Blooms | Shaded | Usable, new (kW) | Usable, end of life (kW) | Demand at ISS density (kW) | "
           "Balance (kW) | Heat (kW) | Radiator capacity at 265 / 275 / 285 K (kW) |",
           "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
    for r in rows:
        bal = r["avg_eol"] - r["demand"]
        rej = " / ".join(f"{r['reject'][T]:.0f}" for T in T_RAD)
        out.append(f"| {r['L']} | {r['pod']} | {r['blooms']} | {r['shade'] * 100:.1f} % | {r['avg_bol']:.0f} | "
                   f"{r['avg_eol']:.0f} | {r['demand']:.0f} | {bal:+.0f} | {r['heat']:.0f} | {rej} |")
    kwh, kg = battery(f["avg_eol"])
    out += ["",
            "## Reading it", "",
            f"- **What each pod brings:** {pod_volume():.0f} m³, which wants {ISS_KW_PER_M3 * pod_volume():.0f} kW at "
            f"ISS density, and one bloom worth ≈{BLOOM_KW_BOL * USABLE * EOL:.0f} kW usable at end of life before "
            "shading. The hub and the docking pod want "
            f"{ISS_KW_PER_M3 * (HUB_VOL + pod_volume()):.0f} kW and get the hub bloom's {hub_kw:.0f} kW.",
            "- **Why the hub bloom, not only bigger blooms:** without it launch 1 has no power at all, and the hub and "
            "docking pod's demand is a debt that the pod blooms only pay back after several launches. The sweep below "
            "shows it: every size up to the chosen one leaves some early launch short.",
            "- **Where the hub bloom goes:** the centre of the widest gap between three pods, near the equator (clear "
            "of the berthing lanes, which run above the docking pod's neighbours), as far off the sun line as possible "
            "(station_geometry.hub_bloom_dir). Gravity and STEVE compute it from the same pod directions.",
            "- **Other ways to buy the same power:** ≈32 % triple-junction cells instead of ≈26 % give about 1.2× per "
            "m², which would allow ≈Ø15.5 m blooms. Or accept a lower density for habitation-heavy use.",
            f"- **Radiators:** the bigger blooms put more heat into the station, so the fins grew from 3 m to "
            f"{rad_w / 1000:.1f} m wide. At 275 K they reject {f['reject'][275.0]:.0f} kW against {f['heat']:.0f} kW of "
            f"heat at full bloom ({f['reject'][275.0] / f['heat']:.2f}×). Running the loop warmer (285 K) gives "
            f"{f['reject'][285.0] / f['heat']:.2f}×.",
            f"- **Batteries:** one eclipse at {f['avg_eol']:.0f} kW takes {kwh:.0f} kWh. At {DOD * 100:.0f} % depth "
            f"of discharge and {WH_PER_KG:.0f} Wh/kg that is ≈{kg / 1000:.1f} t "
            f"(≈{kg / len(rows) / 1000:.2f} t per bloom). MASS_BUDGET.md books "
            f"{BLOOM_KW_BOL * EOL * USABLE * T_ECL / 60 / DOD / WH_PER_KG:.2f} t on every bloom, sized for an "
            "unshaded bloom, so it holds a little margin.",
            f"- **Shading falls on the far side.** Blooms whose pods point away from the sun sit behind the station. "
            f"The worst bloom keeps only {min(r['worst'] for r in rows) * 100:.0f} % of its area; blooms on the sunward "
            "side are unshaded. Fixes: a longer mast on the far-side pods, or a gimbal that offsets the disc out of "
            "the shadow.", "",
            "## Bloom size sweep (with the hub bloom, end of life)", "",
            "| Bloom Ø (m) | Shaded at full bloom | Usable at full bloom (kW) | Worst launch balance (kW) |",
            "|---:|---:|---:|---:|"]
    out += [f"| {D / 1000:g} | {sh * 100:.1f} % | {kw:.0f} | {worst:+.0f} |" for D, sh, kw, worst in sweep]
    out += ["",
            "## History", "",
            "- **First pass (Ø12 m blooms, no hub bloom, 3 m fins):** 198 kW usable at full bloom against 357 kW "
            "(56 % of ISS density), every launch short, launch 1 with no power at all; the radiators had 1.6× margin.",
            "- **Now:** the numbers above. The station grew by the bigger arrays, masts, batteries and fins and by the "
            "hub bloom (MASS_BUDGET.md).", "",
            "## Not modelled (never claimed)", "",
            "- Attitudes other than sun-held (e.g. local-vertical for Earth observation), and the station's own "
            "gravity-gradient torque in sun-held attitude.",
            "- Beta-angle variation: eclipses shorten at high β, so these figures are worst-case.",
            "- Power distribution losses, voltage levels and the conversion chain.",
            "- Transient thermal behaviour, freezing of the coolant loop in eclipse, and heat leaking through MLI.",
            "- Radiators shading blooms when the sun is off +X.", "",
            "## Sources", ""]
    out += [f"- **{k}:** {v}" for k, v in SOURCES.items()]
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    rows = stages()
    for r in rows:
        print(f"L{r['L']:2d} pod {r['pod']:2d} blooms {r['blooms']:2d} shade {r['shade'] * 100:4.1f}% "
              f"(+shuttle {r['shade_s'] * 100:4.1f}%) usable {r['avg_bol']:5.0f}/{r['avg_eol']:5.0f} kW "
              f"demand {r['demand']:5.0f} heat {r['heat']:5.0f} reject@275 {r['reject'][275.0]:5.0f}")
    sweep = bloom_sweep()
    for D, sh, kw, worst in sweep:
        print(f"bloom {D / 1000:g} m: shaded {sh * 100:.1f}%, usable {kw:.0f} kW, worst launch {worst:+.0f} kW")
    open(os.path.join(HERE, "POWER_THERMAL.md"), "w").write(report(rows, sweep))
    print("wrote POWER_THERMAL.md")
