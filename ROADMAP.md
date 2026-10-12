# Blowball Station: roadmap

**Goal:** one launch carries one pod, delivered as 7 Spacelab-derived segments. In orbit the segments
are berthed one at a time, outward from the hub, until the station blooms.

**Design rule: follow nature.** The station grows the way a plant grows:
- **Stalks grow at the tip.** Each segment is berthed to the end of the one before it.
- **New organs go where the gap is.** The next pod is placed by the phyllotaxis inhibitor rule
  (Douady & Couder), which comes out as opposite pairs (decussate leaves). That keeps the centre of
  mass on the hub after every second launch.
- **Flowers open last.** The solar bloom and the radiators unfold only after the pod is complete.

## Where we are (2026-10-12)

| Piece | Where | Status |
|---|---|---|
| Station layout: pod directions packed on a sphere | Gravity `blowball_station.js` → `gravity/handoff.mjs` (gravity-mcp) → STEVE `pod_layout.py` | ✅ STEVE builds from Gravity's own output; the Python port `blowball_layout.py` agrees to < 2 mm |
| Assembly order and stage (launch N) | Gravity `order` / `launch` / `timelapse` knobs; STEVE `order` / `launches` params | ✅ identical orders in both |
| Station v2: 12 × 7-segment pods, 12 m solar blooms, radiators | [STEVE Blowball Station](https://stevecad.studio/?document=286c0cf5-6549-4e47-bcd1-7aaa2fd70bf3) | ✅ builds |
| Shuttle orbiter with ODS + NASA Docking System | [STEVE Orbiter](https://stevecad.studio/?document=cf4b87db-20b5-41d4-b3a0-480b68700e5c) | ✅ linked, docks on pod 0 |
| Berthable flight segment: hatched ends, berthing ring (sealed passage, bolts, self-mating utilities), trunnions, grapple | [STEVE Flight Segment](https://stevecad.studio/?document=767beb53-1509-49c3-8f71-a72fa61ab1a8) | ✅ rev 5; ring sized in [BERTHING_RING.md](analysis/BERTHING_RING.md) |
| One-pod payload: 7 segments in a 21.5 m bay | [STEVE Payload](https://stevecad.studio/?document=bd0b235b-73df-447d-9f4d-2a5a7854ce1e) | ✅ geometry only |
| New Shuttle: orbiter with `stretch` (8.0 m → 26.3 m bay) | [STEVE Orbiter](https://stevecad.studio/?document=cf4b87db-20b5-41d4-b3a0-480b68700e5c) / [stretched](https://stevecad.studio/?document=7d50bbe0-60ca-461c-adda-05d48c078204) | ✅ |
| Berthing animation (launch N): 7 segments, arm path lift → side → out → swing → in | STEVE station, animation `berthing` | ✅ paths checked offline for launches 2–12, ≥ 0.32 m clear; STEVE's full 48-sample sweep (rev 26, with the berthing ring) finds no collision between real parts (only the hidden motion carriers touch) |
| Renders: 12 launch stages, berthing video, full-bloom hero shots, Gravity time-lapse | `renders/index.html` | ✅ |

## What the "new shuttle" must do (derived from the payload layout)

| | Original Shuttle | New Shuttle needed | Why |
|---|---|---|---|
| Payload bay | 4.6 × 18.3 m | **4.6 × 26.3 m** | ODS (3 m) + 7 × 2.9 m segments + gaps, and the last segment must lift out clear of the OMS pod noses |
| Payload to station orbit | ~16 t | **~42 t** | one pod: 7 × 5.39 t segments + stalk, cone, radiators, bloom, batteries ([MASS_BUDGET.md](analysis/MASS_BUDGET.md)) |
| Docking | ODS / APAS | ODS + **NDS (IDSS)** | modern standard; already in the model |
| Flights per pod | n/a | **1** | one launch = one pod |

**The exception is the hub.** At 6 m across it does not fit a 4.6 m bay. Two options:
- **(a)** Launch it once on Starship (8 m envelope).
- **(b)** Make it an expandable hub that packs to under 4.5 m and inflates in orbit, like a seed head
  opening from a bud. This keeps every launch on the same vehicle.

## Next steps, in order

### 1. Make the assembly visible ✅ (2026-10-07)

- **STEVE:** animate one launch, with the 7 segments leaving the bay and berthing one at a time,
  using STEVE's keyframed animation (steve-motion skill).
- **STEVE:** a fit check at every assembly stage, covering pod–pod, bloom–bloom and Shuttle–station
  clearances. STEVE's own animation check runs out of time on this model after 1–3 of 48 poses, so the
  clearance evidence is the offline path check for now.
- **Gravity:** show the arm "walking" out along the pod, end over end on the grapple fixtures, like
  Canadarm2.

### 2. Make it believable (engineering numbers) ✅ (2026-10-12)

- ✅ Mass properties per stage: [analysis/MASS_BUDGET.md](analysis/MASS_BUDGET.md). 5.39 t/segment, 41.9 t/pod (batteries included),
  521 t station; the CoM returns to the hub after every pair. The New Shuttle must lift ~42 t.
- ✅ Power and thermal balance per stage: [analysis/POWER_THERMAL.md](analysis/POWER_THERMAL.md). The radiators
  have 1.6× margin. Power is short: 198 kW usable at end of life against 357 kW at ISS's power density (56 %).
  Launch 1 has no bloom, so it needs its own arrays. Three far-side blooms lose up to 43 % to shading. Ø16.6 m blooms
  would close the gap. Batteries (≈0.33 t per bloom pod) are now in the mass budget.
- ✅ Structural check of a pod on its stalk: [analysis/STRUCTURAL.md](analysis/STRUCTURAL.md). A flat root
  bulkhead bends like a plate (77 MPa, 136 mm); a conical **flare** fixes it (17.8 MPa, 25.6 mm, first mode
  0.62 Hz, within 5 % of the hand check). The flare is now part of the station design.
- ✅ Berthing ring: [analysis/BERTHING_RING.md](analysis/BERTHING_RING.md), STEVE Flight Segment rev 5. Every
  segment holds its own air behind two pressure-rated bulkheads (a bamboo node), so the joint seals only a Ø2.0 m
  passage: 20 bolts instead of 82, half the seal length, preload 2.7× the worst bolt load with the docking moment.
  The 1.27 m hatch sits inside the seal; power (2 × 250 A at 160 V), data, air and water mate by themselves on four
  plates beside it, and the ammonia loops cross outside the seal on two umbilical adapters.

### 3. Make the bridge automatic

- ✅ **Gravity → STEVE data:** the sim writes a hidden data block; `gravity/handoff.mjs` reads it back through
  gravity-mcp's `run_sim` and writes `pod_layout.py`, which STEVE builds from. STEVE refuses to build if
  `params.py` and `pod_layout.py` were made with different knobs. No hand-ported layout code is needed.
- **Still manual:** uploading `pod_layout.py` and the geometry knobs to STEVE, then rebuilding. An agent with
  both MCP servers does it in one pass; a single command would need STEVE's API outside MCP.
- **Gravity wish list:** `ctx.export(json)` as a first-class version of the data block.

### 4. Grow bigger (nature's next pattern)

- **Compound umbels** (dill, Queen Anne's lace): every pod tip becomes a small hub that grows its
  own ring of pods. The same layout and order code applies at each level.
- **Spin:** pod 0 is on the spin axis. Above 30 m radius, 2 rpm gives about 0.13 g. That is useful
  for crew health, and it puts the next scale, about 100 m, within reach.

## Rough totals for the default station

These are estimates, not sized engineering.

| | |
|---|---|
| Launches | 12: 1 hub launch + 11 pod launches |
| Pressurized volume | ~3,000 m³ (≈ 3× ISS) |
| Solar | ~440 kW peak, ~250 kW orbit-average |
| Mass | ~521 t ([MASS_BUDGET.md](analysis/MASS_BUDGET.md)) |
| Assembly time | ~1 week of berthing per launch; at a monthly flight rate, about a year to full bloom |
