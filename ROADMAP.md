# Blowball Station: roadmap

**Goal:** one launch carries one pod, delivered as 7 Spacelab-derived segments. In orbit the segments
are berthed one at a time, outward from the hub, until the station blooms.

**Design rule: follow nature.** The station grows the way a plant grows:
- **Stalks grow at the tip.** Each segment is berthed to the end of the one before it.
- **New organs go where the gap is.** The next pod is placed by the phyllotaxis inhibitor rule
  (Douady & Couder), which comes out as opposite pairs (decussate leaves). That keeps the centre of
  mass on the hub after every second launch.
- **Flowers open last.** The solar bloom and the radiators unfold only after the pod is complete.

## Where we are (2026-10-07)

| Piece | Where | Status |
|---|---|---|
| Station layout: pod directions packed on a sphere | Gravity `blowball_station.js`, STEVE `blowball_layout.py` | ✅ JS and Python agree (< 7 mm) |
| Assembly order and stage (launch N) | Gravity `order` / `launch` / `timelapse` knobs; STEVE `order` / `launches` params | ✅ identical orders in both |
| Station v2: 12 × 7-segment pods, 12 m solar blooms, radiators | [STEVE Blowball Station](https://stevecad.studio/?document=286c0cf5-6549-4e47-bcd1-7aaa2fd70bf3) | ✅ builds |
| Shuttle orbiter with ODS + NASA Docking System | [STEVE Orbiter](https://stevecad.studio/?document=cf4b87db-20b5-41d4-b3a0-480b68700e5c) | ✅ linked, docks on pod 0 |
| Berthable flight segment: hatched ends, berthing flanges, trunnions, grapple | [STEVE Flight Segment](https://stevecad.studio/?document=767beb53-1509-49c3-8f71-a72fa61ab1a8) | ✅ geometry only |
| One-pod payload: 7 segments in a 21.5 m bay | [STEVE Payload](https://stevecad.studio/?document=bd0b235b-73df-447d-9f4d-2a5a7854ce1e) | ✅ geometry only |
| New Shuttle: orbiter with `stretch` (8.0 m → 26.3 m bay) | [STEVE Orbiter](https://stevecad.studio/?document=cf4b87db-20b5-41d4-b3a0-480b68700e5c) / [stretched](https://stevecad.studio/?document=7d50bbe0-60ca-461c-adda-05d48c078204) | ✅ |
| Berthing animation (launch N): 7 segments, arm path lift → side → out → swing → in | STEVE station, animation `berthing` | ✅ paths checked offline for launches 2–12, ≥ 0.32 m clear |
| Renders: 12 launch stages, berthing video, full-bloom hero shots, Gravity time-lapse | `renders/index.html` | ✅ |

## What the "new shuttle" must do (derived from the payload layout)

| | Original Shuttle | New Shuttle needed | Why |
|---|---|---|---|
| Payload bay | 4.6 × 18.3 m | **4.6 × 26.3 m** | ODS (3 m) + 7 × 2.9 m segments + gaps, and the last segment must lift out clear of the OMS pod noses |
| Payload to station orbit | ~16 t | **~32 t** | 7 × ~4.5 t outfitted segments (estimate) |
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

### 2. Make it believable (engineering numbers)

- Mass properties per stage: a real segment mass budget instead of the 4 t placeholder, and the
  centre-of-mass track.
- Power and thermal balance per stage:
  - The hub needs its own power until the first bloom opens.
  - The radiator area has to grow with the pods.
- Structural check of a 7-segment pod cantilevered off the hub, under docking loads and reboost
  (steve-simulation skill).
- Berthing-flange design:
  - bolt count and preload against cabin pressure;
  - the hatch;
  - utility pass-throughs (power, data, air, water) across every joint.

### 3. Make the bridge automatic

- **Gravity:** add a way for a sim to hand data to CAD, for example `ctx.export(json)`. The
  snapshot export currently carries knob values only.
- **MCP server:** take Gravity knob values and update the STEVE `params.py`, then rebuild. The
  same server could expose `layout()`, `order()` and `stage()`.

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
| Mass | ~400 t |
| Assembly time | ~1 week of berthing per launch; at a monthly flight rate, about a year to full bloom |
