# Blowball Station: power and thermal balance (step 2)

**Question:** do the blooms power the station, and can the radiators get rid of the heat, at every launch?

**Answer:** yes, with Ø17 m blooms, a bloom on the hub, and 4.5 m radiator fins (the Ø12 m blooms, no hub array and 3 m fins of the first pass fell short; see the history below).
- **Full station:** 413 kW orbit-average usable at end of life (486 kW new) against 357 kW at ISS's power density: 127 W/m³, 116 % of ISS's 109 W/m³.
- **Launch 1 has power now.** The hub carries its own bloom on a 37.6 m mast in the widest gap between pods, as ISS's first truss segment (P6) did. It gives ≈39 kW usable at end of life and stays on as the hub's own supply.
- **Every launch is in surplus except launch 1**: 39 kW against 41 kW (95 %), and launch 1 flies uncrewed.
- **Radiators keep a margin at every launch:** 1.04× or better at 275 K (1.18× at full bloom).
- **Shadowing costs 11 % of the bloom area at full bloom** (11 % with the New Shuttle docked), mostly on far-side blooms behind other pods. The hub bloom is never shaded.
- **Batteries:** riding through a 36 min eclipse at full load needs ≈7.1 t of batteries in all, carried in MASS_BUDGET.md.

## Assumptions

- **Attitude:** sun held on +X, as in the STEVE model. Every bloom faces the sun, every radiator fin is edge-on to it, and shadowing changes only as pods are added.
- **Blooms:** Ø17 m, 80 kW each in full sun when new (354 W/m², ≈26 % cells, as the first pass's 40 kW on Ø12 m); 0.85 × that at end of life (EST). Each sits on a mast of radius + 1.5 m (10.0 m), as in Gravity.
- **Orbit:** 92 min with 36 min of eclipse (worst case). Batteries carry the eclipse at 0.85 round trip (EST), so the usable continuous power is 0.569 × the sunlit array power.
- **Demand:** ISS density, ≈109 W per m³ pressurized (≈100 kW over 916 m³). This is a heavy-science benchmark, not a requirement.
- **Heat:** all usable power becomes heat, plus 2 crew per pod at 120 W (EST). Heat soaking in through the MLI is not counted.
- **Radiators:** 109.6 m² of fin per pod (two 4.5 m × 12.2 m fins), both faces radiating. ε 0.92, α 0.14 (Z-93-class white), fin efficiency 0.9 (EST). Orbit-average view factor to Earth 0.7 for both faces together (EST). Net rejection per m² of fin: 298 W at 265 K, 372 W at 275 K, 455 W at 285 K.
- **Shadowing:** the station drawn as seen from the sun at 50 mm per pixel, from the same tessellation as the renders (station_mesh.py, orbiter_mesh.py). Masts and spars are left out (see the code).

## Launch by launch

Blooms include the hub's.

| Launch | Pod | Blooms | Shaded | Usable, new (kW) | Usable, end of life (kW) | Demand at ISS density (kW) | Balance (kW) | Heat (kW) | Radiator capacity at 265 / 275 / 285 K (kW) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | 0 | 1 | 0.0 % | 46 | 39 | 41 | -2 | 39 | 33 / 41 / 50 |
| 2 | 9 | 2 | 0.0 % | 91 | 78 | 70 | +8 | 78 | 65 / 82 / 100 |
| 3 | 1 | 3 | 0.0 % | 137 | 117 | 98 | +18 | 117 | 98 / 122 / 150 |
| 4 | 10 | 4 | 7.6 % | 169 | 144 | 127 | +16 | 145 | 131 / 163 / 199 |
| 5 | 2 | 5 | 6.1 % | 215 | 182 | 156 | +27 | 184 | 163 / 204 / 249 |
| 6 | 11 | 6 | 8.9 % | 250 | 212 | 184 | +28 | 214 | 196 / 245 / 299 |
| 7 | 3 | 7 | 7.6 % | 296 | 251 | 213 | +38 | 253 | 229 / 286 / 349 |
| 8 | 7 | 8 | 6.7 % | 341 | 290 | 242 | +48 | 292 | 262 / 326 / 399 |
| 9 | 4 | 9 | 7.2 % | 382 | 324 | 271 | +54 | 327 | 294 / 367 / 449 |
| 10 | 8 | 10 | 9.4 % | 414 | 352 | 299 | +53 | 354 | 327 / 408 / 498 |
| 11 | 5 | 11 | 11.3 % | 446 | 379 | 328 | +51 | 382 | 360 / 449 / 548 |
| 12 | 6 | 12 | 11.3 % | 486 | 413 | 357 | +57 | 416 | 392 / 490 / 598 |

## Reading it

- **What each pod brings:** 263 m³, which wants 29 kW at ISS density, and one bloom worth ≈39 kW usable at end of life before shading. The hub and the docking pod want 41 kW and get the hub bloom's 39 kW.
- **Why the hub bloom, not only bigger blooms:** without it launch 1 has no power at all, and the hub and docking pod's demand is a debt that the pod blooms only pay back after several launches. The sweep below shows it: every size up to the chosen one leaves some early launch short.
- **Where the hub bloom goes:** the centre of the widest gap between three pods, near the equator (clear of the berthing lanes, which run above the docking pod's neighbours), as far off the sun line as possible (station_geometry.hub_bloom_dir). Gravity and STEVE compute it from the same pod directions.
- **Other ways to buy the same power:** ≈32 % triple-junction cells instead of ≈26 % give about 1.2× per m², which would allow ≈Ø15.5 m blooms. Or accept a lower density for habitation-heavy use.
- **Radiators:** the bigger blooms put more heat into the station, so the fins grew from 3 m to 4.5 m wide. At 275 K they reject 490 kW against 416 kW of heat at full bloom (1.18×). Running the loop warmer (285 K) gives 1.44×.
- **Batteries:** one eclipse at 413 kW takes 248 kWh. At 35 % depth of discharge and 100 Wh/kg that is ≈7.1 t (≈0.59 t per bloom). MASS_BUDGET.md books 0.67 t on every bloom, sized for an unshaded bloom, so it holds a little margin.
- **Shading falls on the far side.** Blooms whose pods point away from the sun sit behind the station. The worst bloom keeps only 65 % of its area; blooms on the sunward side are unshaded. Fixes: a longer mast on the far-side pods, or a gimbal that offsets the disc out of the shadow.

## Bloom size sweep (with the hub bloom, end of life)

| Bloom Ø (m) | Shaded at full bloom | Usable at full bloom (kW) | Worst launch balance (kW) |
|---:|---:|---:|---:|
| 12 | 6.7 % | 217 | -140 |
| 14 | 8.2 % | 290 | -66 |
| 15 | 9.3 % | 329 | -27 |
| 16 | 10.4 % | 370 | -7 |
| 16.5 | 10.9 % | 391 | -4 |
| 17 | 11.3 % | 413 | -2 |
| 17.5 | 11.8 % | 436 | +0 |

## History

- **First pass (Ø12 m blooms, no hub bloom, 3 m fins):** 198 kW usable at full bloom against 357 kW (56 % of ISS density), every launch short, launch 1 with no power at all; the radiators had 1.6× margin.
- **Now:** the numbers above. The station grew by the bigger arrays, masts, batteries and fins and by the hub bloom (MASS_BUDGET.md).

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
