# Blowball Station: power and thermal balance (step 2)

**Question:** do the blooms power the station, and can the radiators get rid of the heat, at every launch?

**Answer:** the radiators are fine throughout; power is short.
- **Full station:** 198 kW orbit-average usable at end of life (233 kW new) against 357 kW at ISS's power density. That is 61 W/m³, 56 % of ISS's 109 W/m³.
- **Launch 1 has no power at all.** The hub and the docking pod carry no bloom. The first flight needs its own arrays, as ISS's first truss segment (P6) did.
- **Shadowing costs 7 % of the bloom area at full bloom** (7 % with the New Shuttle docked), almost all of it on three far-side blooms that sit behind other pods.
- **Batteries:** riding through a 36 min eclipse at full load needs ≈3.4 t of batteries in all, now carried in MASS_BUDGET.md.

## Assumptions

- **Attitude:** sun held on +X, as in the STEVE model. Every bloom faces the sun, every radiator fin is edge-on to it, and shadowing changes only as pods are added.
- **Blooms:** 40 kW each in full sun when new (MASS_BUDGET.md); 0.85 × that at end of life (EST).
- **Orbit:** 92 min with 36 min of eclipse (worst case). Batteries carry the eclipse at 0.85 round trip (EST), so the usable continuous power is 0.569 × the sunlit array power.
- **Demand:** ISS density, ≈109 W per m³ pressurized (≈100 kW over 916 m³). This is a heavy-science benchmark, not a requirement.
- **Heat:** all usable power becomes heat, plus 2 crew per pod at 120 W (EST). Heat soaking in through the MLI is not counted.
- **Radiators:** 73.1 m² of fin per pod (two 3 m × 12.2 m fins), both faces radiating. ε 0.92, α 0.14 (Z-93-class white), fin efficiency 0.9 (EST). Orbit-average view factor to Earth 0.7 for both faces together (EST). Net rejection per m² of fin: 298 W at 265 K, 372 W at 275 K, 455 W at 285 K.
- **Shadowing:** the station drawn as seen from the sun at 50 mm per pixel, from the same tessellation as the renders (station_mesh.py, orbiter_mesh.py). Masts and spars are left out (see the code).

## Launch by launch

| Launch | Pod | Blooms | Shaded | Usable, new (kW) | Usable, end of life (kW) | Demand at ISS density (kW) | Balance (kW) | Heat (kW) | Radiator capacity at 265 / 275 / 285 K (kW) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | 0 | 0 | 0.0 % | 0 | 0 | 41 | -41 | 0 | 22 / 27 / 33 |
| 2 | 9 | 1 | 0.0 % | 23 | 19 | 70 | -50 | 20 | 44 / 54 / 66 |
| 3 | 1 | 2 | 0.0 % | 46 | 39 | 98 | -60 | 39 | 65 / 82 / 100 |
| 4 | 10 | 3 | 14.2 % | 59 | 50 | 127 | -77 | 51 | 87 / 109 / 133 |
| 5 | 2 | 4 | 10.6 % | 81 | 69 | 156 | -87 | 70 | 109 / 136 / 166 |
| 6 | 11 | 5 | 8.5 % | 104 | 89 | 184 | -96 | 90 | 131 / 163 / 199 |
| 7 | 3 | 6 | 7.1 % | 127 | 108 | 213 | -105 | 110 | 153 / 190 / 233 |
| 8 | 7 | 7 | 6.1 % | 150 | 127 | 242 | -115 | 129 | 174 / 218 / 266 |
| 9 | 4 | 8 | 5.3 % | 173 | 147 | 271 | -124 | 149 | 196 / 245 / 299 |
| 10 | 8 | 9 | 6.6 % | 192 | 163 | 299 | -136 | 165 | 218 / 272 / 332 |
| 11 | 5 | 10 | 7.6 % | 211 | 179 | 328 | -149 | 182 | 240 / 299 / 365 |
| 12 | 6 | 11 | 6.9 % | 233 | 198 | 357 | -158 | 201 | 262 / 326 / 399 |

## Reading it

- **Power is the binding constraint.** Each new pod adds 263 m³ and one bloom worth ≈19 kW usable at end of life; at ISS density that pod wants 29 kW. The hub and the docking pod add 41 kW of demand and no bloom.
- **Ways to close it:**
  - Larger blooms: Ø16.6 m instead of Ø12 m covers ISS density at end of life. Larger discs shade each other more, so this comes from the sweep below, not from scaling the area. Bloom centres sit ≈40 m apart, so the discs still clear each other physically. The mast must stay longer than the bloom radius: ≈9.8 m instead of 7.5 m (Gravity uses radius + 1.5 m).
  - Better cells: ≈32 % triple-junction cells instead of ≈26 % gives about 1.2× per m².
  - A hub array for launch 1 that stays on as the hub's own supply, as ISS's P6 did.
  - Or accept a lower density: the station as drawn supports 61 W/m³, which is plenty for habitation-heavy use.
- **Radiators have margin.** At 275 K the fins reject 326 kW against 201 kW of heat at full bloom (1.6×). If the blooms grow to close the power gap, the heat grows too, and the margin shrinks to about 0.9×.
- **Batteries:** one eclipse at 198 kW takes 119 kWh. At 35 % depth of discharge and 100 Wh/kg that is ≈3.4 t (≈0.28 t per pod). MASS_BUDGET.md books 0.33 t on every bloom pod, sized for an unshaded bloom, so it holds a little margin.
- **Shading falls on the far side.** Blooms whose pods point away from the sun sit behind the station, and their light passes the pods in front. The worst bloom keeps only 57 % of its area; blooms on the sunward side are unshaded. Fixes: a longer mast on the far-side pods, or a gimbal that offsets the disc out of the shadow.

## Bloom size sweep (full station, end of life)

| Bloom Ø (m) | Shaded | Usable (kW) | At ISS density? |
|---:|---:|---:|---|
| 12 | 6.9 % | 198 | no |
| 14 | 8.9 % | 264 | no |
| 16 | 11.6 % | 335 | no |
| 17 | 12.7 % | 373 | yes |
| 18 | 13.7 % | 414 | yes |

## Not modelled (never claimed)

- Attitudes other than sun-held (e.g. local-vertical for Earth observation), and the station's own gravity-gradient torque in sun-held attitude.
- Beta-angle variation: eclipses shorten at high β, so these figures are worst-case.
- Power distribution losses, voltage levels and the conversion chain.
- Transient thermal behaviour, freezing of the coolant loop in eclipse, and heat leaking through MLI.
- Radiators shading blooms when the sun is off +X.

## Sources

- **iss_power:** NASA: ISS solar arrays generate 84–120 kW; pressurized volume 916 m³
- **leo:** LEO at ~400 km: 92 min orbit, up to ~36 min in eclipse (β = 0°)
- **earth:** Earth: mean outgoing IR ≈ 237 W/m², Bond albedo ≈ 0.30, solar constant 1361 W/m²
- **coating:** ISS radiator coating (Z-93 class white): ε ≈ 0.92, α ≈ 0.14
