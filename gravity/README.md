# Gravity ⇄ STEVE: Blowball Station

`blowball_station.js` is a Gravity sim (holodeck1.ai): **New** → paste the whole file → Check → Run.
A dandelion seed head as a space station:

| Dandelion | Station |
|---|---|
| receptacle | 6 m hub sphere |
| stalk | pressurized tunnel |
| seed | lab pod: 7 Spacelab segments (18.9 m × Ø4.06 m) + end cone |
| pappus | 12 m circular solar array on a gimbal mast, face-on to the sun |

Each pod also carries two radiator fins, edge-on to the sun. Pod 0 points up and is the docking pod;
the Shuttle docks there. A red ring marks pods closer than `2·podR + clear` at their roots. An orange
ring marks blooms that overlap.

## Knobs → STEVE

Gravity's snapshot export only stores knob values, not point positions. There are two bridges.

**1. Through Gravity's own engine (no port).** The sim writes a small data block into particles 0–128: each pod's
direction, the direction flown at each launch, and a header (pod count, relax progress). `handoff.mjs` runs the sim
with [gravity-mcp](https://holodeck1.ai/mcp/)'s `run_sim`, reads the block back, and writes a data-only
`pod_layout.py` (`N`, `DIRS` in STEVE's frame, `ORDER`):

```sh
node gravity/handoff.mjs snapshot.json                  # a Gravity snapshot, or {key: value}
node gravity/handoff.mjs pods=20 k=12 order=1 --out /tmp/pod_layout.py
```

It takes about 3 s and needs Node 22.13+. The data rows sit inside the hub, so they don't show in Gravity.
Against the Python port, six knob sets agree to < 7e-5 on unit directions (< 2 mm at the pod tip), with
identical assembly order.

**2. The Python port** (`blowball_layout.py`, line for line, used by STEVE today): STEVE re-runs the same layout
from the same knobs. It agrees with Gravity to < 4e-4 on unit directions (< 7 mm at station scale). Any change to
the sim's layout code has to be ported by hand; bridge 1 doesn't have that problem.

| Gravity knob | STEVE `params.py` |
|---|---|
| pods, k, start, seed, relax, segments | same names |
| hub, reach, podR, bloomD (m) | hub_r, reach, pod_r, bloom_d (mm = m × 1000) |
| clear, rpm, shuttle | display / analysis only |

Frames: Gravity is y-up; STEVE is Z-up. STEVE (X, Y, Z) = Gravity (x, −z, y). The sun is +X in both.

STEVE designs:
- Blowball Station: https://stevecad.studio/?document=286c0cf5-6549-4e47-bcd1-7aaa2fd70bf3
- Space Shuttle Orbiter (linked into the station): https://stevecad.studio/?document=cf4b87db-20b5-41d4-b3a0-480b68700e5c

## Default station, rough numbers

These are order-of-magnitude estimates, not sized engineering.

| | |
|---|---|
| Pressurized volume | ≈ 12 × 245 m³ + hub ≈ 3,000 m³ (≈ 3× ISS) |
| Solar | 11 blooms × ~40 kW ≈ 440 kW peak, ~250 kW orbit-average |
| Radiators | 24 fins × 34 m² ≈ 820 m² (both faces radiate) |
| Mass | ≈ 400 t |

The mass is mostly pods. That assumes about 4 t per outfitted segment, which is an estimate.

## Launch and assembly (Starship: Ø8 m × 17 m payload envelope, 22 m extended, 100 t class target)

1. Hub flight: the 6 m hub, the pod 0 docking pod (short), thrusters, batteries and a temporary
   solar array. The hub fits with 2 m to spare.
2. Pod flights: each pod is integrated on the ground, 7 segments + cone ≈ 20 m, and flies whole in the
   22 m extended fairing. It weighs about 30 t, so the flight is volume-limited, not mass-limited.
   That is 11–12 flights. Pods are added in opposite pairs to keep the station balanced.
3. Blooms and radiators ride folded on the pod flights (fan-fold arrays stow as a ~1 m drum)
   and deploy once the pod is berthed.
4. Berthing: a station robotic arm grabs each pod from its Starship and berths it to a hub
   collar, the way ISS modules were added.

That is about 13–15 launches in total. For comparison, ISS took ~40 assembly flights for ~420 t.
