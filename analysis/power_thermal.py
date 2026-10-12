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
BLOOM_KW_BOL = 40.0          # per bloom, as MASS_BUDGET.md (113 m² at ≈354 W/m², ≈26 % cells)
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
    centres = {q: np.array(G.at(G.DIRS[q], G.r_cone + mast)) for q in built}
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
    full = 12 * (bloom_d / 2) ** 2 * math.sin(2 * math.pi / 24) / PX ** 2   # the disc is a 24-gon (station_mesh)
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


def bloom_sweep(diams=(12000, 14000, 16000, 17000, 18000)):
    """Full station: shading and usable end-of-life power for other bloom diameters (shading grows with size)."""
    global bloom_d
    keep, rows = bloom_d, []
    for D in diams:
        bloom_d = M.bloom_d = D
        lit = sun_view(set(G.ORDER), shuttle=False)
        kw = sum(BLOOM_KW_BOL * (D / keep) ** 2 * f for f in lit.values()) * USABLE * EOL
        rows.append((D, 1 - sum(lit.values()) / len(lit), kw))
    bloom_d = M.bloom_d = keep
    return rows


def battery(load_kw):
    """Usable energy for one eclipse at this load, and the packaged battery mass at DOD."""
    kwh = load_kw * T_ECL / 60
    return kwh, kwh / DOD / WH_PER_KG * 1000     # kWh, kg


def report(rows, sweep):
    f = rows[-1]
    out = ["# Blowball Station: power and thermal balance (step 2)", "",
           "**Question:** do the blooms power the station, and can the radiators get rid of the heat, at every launch?", "",
           "**Answer:** the radiators are fine throughout; power is short.",
           f"- **Full station:** {f['avg_eol']:.0f} kW orbit-average usable at end of life ({f['avg_bol']:.0f} kW new) "
           f"against {f['demand']:.0f} kW at ISS's power density. That is {f['density'] * 1000:.0f} W/m³, "
           f"{f['density'] / ISS_KW_PER_M3 * 100:.0f} % of ISS's {ISS_KW_PER_M3 * 1000:.0f} W/m³.",
           "- **Launch 1 has no power at all.** The hub and the docking pod carry no bloom. The first flight needs its "
           "own arrays, as ISS's first truss segment (P6) did.",
           f"- **Shadowing costs {f['shade'] * 100:.0f} % of the bloom area at full bloom** "
           f"({f['shade_s'] * 100:.0f} % with the New Shuttle docked), almost all of it on three far-side blooms "
           "that sit behind other pods.",
           f"- **Batteries:** riding through a {T_ECL:.0f} min eclipse at full load needs "
           f"≈{battery(f['avg_eol'])[1] / 1000:.1f} t of batteries in all, now carried in MASS_BUDGET.md.", "",
           "## Assumptions", "",
           f"- **Attitude:** sun held on +X, as in the STEVE model. Every bloom faces the sun, every radiator fin is "
           "edge-on to it, and shadowing changes only as pods are added.",
           f"- **Blooms:** {BLOOM_KW_BOL:.0f} kW each in full sun when new (MASS_BUDGET.md); {EOL:.2f} × that at "
           f"end of life (EST).",
           f"- **Orbit:** {T_ORBIT:.0f} min with {T_ECL:.0f} min of eclipse (worst case). Batteries carry the "
           f"eclipse at {ETA_BATT:.2f} round trip (EST), so the usable continuous power is {USABLE:.3f} × the "
           "sunlit array power.",
           f"- **Demand:** ISS density, ≈{ISS_KW_PER_M3 * 1000:.0f} W per m³ pressurized (≈100 kW over 916 m³). "
           "This is a heavy-science benchmark, not a requirement.",
           f"- **Heat:** all usable power becomes heat, plus {CREW_PER_POD} crew per pod at {CREW_W:.0f} W (EST). "
           "Heat soaking in through the MLI is not counted.",
           f"- **Radiators:** {FIN_AREA:.1f} m² of fin per pod (two 3 m × {0.6 * G.pod_len / 1000:.1f} m fins), "
           f"both faces radiating. ε {EPS}, α {ALPHA} (Z-93-class white), fin efficiency {FIN_EFF} (EST). "
           f"Orbit-average view factor to Earth {F_EARTH} for both faces together (EST). Net rejection per m² of "
           "fin: " + ", ".join(f"{fin_kw_per_m2(T) * 1000:.0f} W at {T:.0f} K" for T in T_RAD) + ".",
           "- **Shadowing:** the station drawn as seen from the sun at 50 mm per pixel, from the same tessellation "
           "as the renders (station_mesh.py, orbiter_mesh.py). Masts and spars are left out (see the code).", "",
           "## Launch by launch", "",
           "| Launch | Pod | Blooms | Shaded | Usable, new (kW) | Usable, end of life (kW) | Demand at ISS density (kW) | "
           "Balance (kW) | Heat (kW) | Radiator capacity at 265 / 275 / 285 K (kW) |",
           "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
    for r in rows:
        bal = r["avg_eol"] - r["demand"]
        rej = " / ".join(f"{r['reject'][T]:.0f}" for T in T_RAD)
        out.append(f"| {r['L']} | {r['pod']} | {r['blooms']} | {r['shade'] * 100:.1f} % | {r['avg_bol']:.0f} | "
                   f"{r['avg_eol']:.0f} | {r['demand']:.0f} | {bal:+.0f} | {r['heat']:.0f} | {rej} |")
    kwh, kg = battery(f["avg_eol"])
    need = f["demand"] / f["avg_eol"]
    d_need = float(np.interp(f["demand"], [kw for *_, kw in sweep], [D for D, *_ in sweep])) / 1000
    out += ["",
            "## Reading it", "",
            f"- **Power is the binding constraint.** Each new pod adds {pod_volume():.0f} m³ and one bloom worth "
            f"≈{BLOOM_KW_BOL * USABLE * EOL:.0f} kW usable at end of life; at ISS density that pod wants "
            f"{ISS_KW_PER_M3 * pod_volume():.0f} kW. The hub and the docking pod add "
            f"{ISS_KW_PER_M3 * (HUB_VOL + pod_volume()):.0f} kW of demand and no bloom.",
            f"- **Ways to close it:**",
            f"  - Larger blooms: Ø{d_need:.1f} m instead of Ø{bloom_d / 1000:.0f} m covers ISS density at end of "
            "life. Larger discs shade each other more, so this comes from the sweep below, not from scaling the "
            f"area. Bloom centres sit ≈40 m apart, so the discs still clear each other physically. The mast must stay "
            f"longer than the bloom radius: ≈{d_need / 2 + 1.5:.1f} m instead of {mast / 1000:.1f} m (Gravity uses "
            "radius + 1.5 m).",
            "  - Better cells: ≈32 % triple-junction cells instead of ≈26 % gives about 1.2× per m².",
            "  - A hub array for launch 1 that stays on as the hub's own supply, as ISS's P6 did.",
            "  - Or accept a lower density: the station as drawn supports "
            f"{f['density'] * 1000:.0f} W/m³, which is plenty for habitation-heavy use.",
            f"- **Radiators have margin.** At 275 K the fins reject {f['reject'][275.0]:.0f} kW against "
            f"{f['heat']:.0f} kW of heat at full bloom ({f['reject'][275.0] / f['heat']:.1f}×). If the blooms "
            "grow to close the power gap, the heat grows too, and the margin shrinks to about "
            f"{f['reject'][275.0] / (f['heat'] * need):.1f}×.",
            f"- **Batteries:** one eclipse at {f['avg_eol']:.0f} kW takes {kwh:.0f} kWh. At {DOD * 100:.0f} % depth "
            f"of discharge and {WH_PER_KG:.0f} Wh/kg that is ≈{kg / 1000:.1f} t "
            f"(≈{kg / len(rows) / 1000:.2f} t per pod). MASS_BUDGET.md books "
            f"{BLOOM_KW_BOL * EOL * USABLE * T_ECL / 60 / DOD / WH_PER_KG:.2f} t on every bloom pod, sized for an "
            "unshaded bloom, so it holds a little margin.",
            f"- **Shading falls on the far side.** Blooms whose pods point away from the sun sit behind the station, "
            "and their light passes the pods in front. The worst bloom keeps only "
            f"{min(r['worst'] for r in rows) * 100:.0f} % of its area; blooms on the sunward side are unshaded. "
            "Fixes: a longer mast on the far-side pods, or a gimbal that offsets the disc out of the shadow.", "",
            "## Bloom size sweep (full station, end of life)", "",
            "| Bloom Ø (m) | Shaded | Usable (kW) | At ISS density? |", "|---:|---:|---:|---|"]
    out += [f"| {D / 1000:.0f} | {sh * 100:.1f} % | {kw:.0f} | {'yes' if kw >= f['demand'] else 'no'} |"
            for D, sh, kw in sweep]
    out += ["",
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
    for D, sh, kw in sweep:
        print(f"bloom {D / 1000:.0f} m: shaded {sh * 100:.1f}%, usable {kw:.0f} kW")
    open(os.path.join(HERE, "POWER_THERMAL.md"), "w").write(report(rows, sweep))
    print("wrote POWER_THERMAL.md")
