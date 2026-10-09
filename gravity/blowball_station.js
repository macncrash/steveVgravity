// A sim is a plain module with two exports and no imports:
//   meta         plain data: title, particle count, time step, knobs (params), colouring
//   create(ctx)  runs once; returns { step(dt, p) }, called every frame
// Write x, y, z for every particle into ctx.positions (keep them within about ±20; y is up).
//
// BLOWBALL STATION v2 — a dandelion seed head as a space station.
//   receptacle (seed-head core) -> pressurized hub sphere (6 m, fits Starship's 8 m payload envelope)
//   stalk                       -> pressurized tunnel
//   achene (seed)               -> lab pod: N Spacelab segments end to end (default 7 = 18.9 m)
//   pappus (fluff)              -> a big circular solar array on a gimbal mast, always face-on to the sun (+x)
//   + two radiator fins per pod, edge-on to the sun; pod 0 (up, +y) is the docking pod with the Shuttle
// Pod directions are packed on the sphere by repulsion (Thomson k=1 … Tammes k→∞).
// Red rings: at a pod root when two pods are too close, at a bloom rim when two blooms overlap.
//
// STEVE bridge: the layout is fully determined by (pods, k, start, seed, relax) and a fixed iteration
// budget (ITERS). STEVE runs the same algorithm (blowball_layout.py) to rebuild the identical station.

export const meta = {
  title: 'Blowball Station',
  summary: 'A dandelion seed head as a space station: 7-segment Spacelab pods on stalks, packed on a sphere, each crowned by a sun-tracking solar bloom; the Shuttle docks on top.',
  particleCount: 50000,
  dt: 0.016,
  bloom: 0.45,
  pointSize: 0.01,
  camera: { position: [24, 14, 30], target: [0, 1, 0] },
  params: [
    { key: 'pods', label: 'pods (seeds)', min: 4, max: 64, step: 1, default: 12 },
    { key: 'k', label: 'repulsion hardness k', min: 1, max: 12, step: 1, default: 6 },
    { key: 'start', label: 'start layout', min: 0, max: 1, step: 1, default: 0, options: { fibonacci: 0, random: 1 } },
    { key: 'seed', label: 'random seed', min: 1, max: 99, step: 1, default: 7 },
    { key: 'relax', label: 'relax (0 = pure Fibonacci)', min: 0, max: 1, step: 1, default: 1, options: { off: 0, on: 1 } },
    { key: 'hub', label: 'hub radius (m)', min: 2, max: 4, step: 0.1, default: 3 },
    { key: 'reach', label: 'stalk length (m)', min: 2, max: 10, step: 0.1, default: 6 },
    { key: 'podR', label: 'pod radius (m)', min: 1, max: 3, step: 0.01, default: 2.03 },
    { key: 'segments', label: 'Spacelab segments / pod', min: 1, max: 7, step: 1, default: 7 },
    { key: 'bloomD', label: 'solar bloom diameter (m)', min: 0, max: 20, step: 0.5, default: 12 },
    { key: 'clear', label: 'min clearance (m)', min: 0, max: 3, step: 0.1, default: 1 },
    { key: 'shuttle', label: 'Shuttle docked on pod 0', min: 0, max: 1, step: 1, default: 1, options: { no: 0, yes: 1 } },
    { key: 'rpm', label: 'spin (rpm)', min: 0, max: 6, step: 0.1, default: 0 },
    { key: 'order', label: 'assembly order', min: 0, max: 2, step: 1, default: 0, options: { 'opposite pairs (decussate)': 0, 'biggest gap (spiral)': 1, 'index': 2 } },
    { key: 'timelapse', label: 'time-lapse assembly', min: 0, max: 1, step: 1, default: 1, options: { off: 0, on: 1 } },
    { key: 'launch', label: 'launches flown (time-lapse off)', min: 0, max: 64, step: 1, default: 64 },
  ],
  doc: {
    about: 'A dandelion blowball packs ~150–200 seeds on a domed receptacle so every stalk gets its own patch of sky. Here each seed is a 7-segment Spacelab laboratory (18.9 m, Ø4.06 m) on a pressurized stalk, and each pappus is a 12 m circular fan-fold solar array (UltraFlex-style) on a gimbal mast. Two pods whose roots sit at radius r0 and whose directions are θ apart are closest at their roots: 2·r0·sin(θ/2) — so the pod count is a Tammes problem. Default station: 12 pods ≈ 3,000 m³ pressurized (≈3× ISS), 11 blooms ≈ 11 × 40 kW ≈ 440 kW peak, ~250 kW orbit-average.',
    howItWorks: 'Pod directions start on a Fibonacci (golden-angle) sphere or at seeded random points, then slide over the sphere under pairwise repulsion F ∝ 1/d^(k+1). The step shrinks over a fixed budget of 1200 iterations so the result is reproducible; the layout is then rotated so pod 0 points up (+y) and pod 1 lies in the x–y plane. Blooms track the sun along +x (a 2-axis gimbal at each mast); radiators stay edge-on to it. Spin turns the station about y: a pod at distance ρ from the axis feels ω²ρ.',
    integrator: 'projected gradient descent on the sphere, 6 iterations/frame, annealed step, 1200 iterations total',
    mapping: 'view units are metres scaled by 19/(station radius) so everything fits; y is up, the sun is +x. STEVE frame: X = x, Y = −z, Z = y (mm = m × 1000).',
    equations: [
      { label: 'pod clearance at the roots', latex: '2 r_0 \\sin(\\theta_{ij}/2) \\ge 2 r_{pod} + c,\\quad r_0 = r_{hub} + L_{stalk}' },
      { label: 'repulsion on the sphere', latex: '\\mathbf F_i = \\sum_{j\\ne i} \\frac{\\mathbf d_i - \\mathbf d_j}{|\\mathbf d_i - \\mathbf d_j|^{k+2}}' },
      { label: 'bloom power (30 % cells, 85 % fill)', latex: 'P \\approx 1361\\,\\tfrac{W}{m^2} \\times 0.30 \\times 0.85 \\times \\tfrac{\\pi D^2}{4} \\approx 40\\,\\mathrm{kW}\\ (D = 12\\,\\mathrm{m})' },
      { label: 'spin gravity', latex: 'g = \\omega^2 \\rho,\\quad \\omega = 2\\pi\\,\\mathrm{rpm}/60' },
    ],
    assumptions: ['Pods are rigid cylinders on radial stalks; pod clearance is checked at the roots, bloom clearance between bloom centres.', 'Blooms are sun-tracking discs; shading between blooms is not computed.', 'Assembly: launch 1 = hub + axial docking pod; every later launch delivers one pod as 7 segments that are berthed one at a time from the hub outward, then its bloom and radiators unfold. The magenta cross is the centre of mass (hub 20 t, 4 t per segment, 1.5 t per bloom). Opposite pairs re-centre it after every second launch, like decussate leaves (mint, basil); the biggest-gap spiral is the sunflower rule.'],
    limitations: ['No structure, mass, life support or propulsion is modelled.', 'Sun-tracking blooms and a spinning station fight each other: with spin on, every gimbal must counter-rotate once per revolution.', '1 g at ~30 m needs ~5.5 rpm, above the ~2–4 rpm most people tolerate.'],
    references: [
      { label: 'Tammes problem', url: 'https://en.wikipedia.org/wiki/Tammes_problem' },
      { label: 'Spacelab', url: 'https://en.wikipedia.org/wiki/Spacelab' },
      { label: 'Starship payload user guide', url: 'https://www.spacex.com/media/starship_users_guide_v1.pdf' },
    ],
  },
};

// ---------------- layout (keep in sync with STEVE's blowball_layout.py) ----------------
const MAXP = 64, ITERS = 1200, PER_FRAME = 6;

function mulberry32(a) {
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function startDirs(n, start, seed) {
  const d = new Float64Array(n * 3);
  if (start >= 0.5) {
    const rnd = mulberry32(seed);
    for (let i = 0; i < n; i++) {
      const y = 2 * rnd() - 1, a = 2 * Math.PI * rnd(), r = Math.sqrt(1 - y * y);
      d[i * 3] = r * Math.cos(a); d[i * 3 + 1] = y; d[i * 3 + 2] = r * Math.sin(a);
    }
  } else {
    const ga = Math.PI * (3 - Math.sqrt(5));
    for (let i = 0; i < n; i++) {
      const y = 1 - (2 * (i + 0.5)) / n, r = Math.sqrt(1 - y * y), a = i * ga;
      d[i * 3] = r * Math.cos(a); d[i * 3 + 1] = y; d[i * 3 + 2] = r * Math.sin(a);
    }
  }
  return d;
}

// one annealed repulsion iteration; `it` = iteration index (0…ITERS-1)
function relaxStep(d, n, k, it) {
  const f = new Float64Array(n * 3);
  for (let i = 0; i < n; i++) {
    for (let j = i + 1; j < n; j++) {
      const dx = d[i * 3] - d[j * 3], dy = d[i * 3 + 1] - d[j * 3 + 1], dz = d[i * 3 + 2] - d[j * 3 + 2];
      const r2 = dx * dx + dy * dy + dz * dz + 1e-12;
      const s = 1 / Math.pow(r2, (k + 2) / 2);
      f[i * 3] += dx * s; f[i * 3 + 1] += dy * s; f[i * 3 + 2] += dz * s;
      f[j * 3] -= dx * s; f[j * 3 + 1] -= dy * s; f[j * 3 + 2] -= dz * s;
    }
  }
  let fmax = 0;
  for (let i = 0; i < n; i++) {
    const o = i * 3, dot = f[o] * d[o] + f[o + 1] * d[o + 1] + f[o + 2] * d[o + 2];
    f[o] -= dot * d[o]; f[o + 1] -= dot * d[o + 1]; f[o + 2] -= dot * d[o + 2];
    fmax = Math.max(fmax, Math.hypot(f[o], f[o + 1], f[o + 2]));
  }
  if (fmax < 1e-15) return;
  const spacing = Math.sqrt((4 * Math.PI) / n);
  const eta = (0.12 * spacing * Math.pow(0.004, it / (ITERS - 1))) / fmax; // anneal 0.12 → 0.0005 spacing
  for (let i = 0; i < n; i++) {
    const o = i * 3;
    const x = d[o] + eta * f[o], y = d[o + 1] + eta * f[o + 1], z = d[o + 2] + eta * f[o + 2];
    const m = Math.hypot(x, y, z);
    d[o] = x / m; d[o + 1] = y / m; d[o + 2] = z / m;
  }
}

// rotate so pod 0 → +y and pod 1 lies in the x–y plane with x > 0
function canonical(d, n) {
  const out = new Float64Array(n * 3);
  const e2 = [d[0], d[1], d[2]];
  let ax = n > 1 ? [d[3], d[4], d[5]] : [1, 0, 0];
  let dot = ax[0] * e2[0] + ax[1] * e2[1] + ax[2] * e2[2];
  let e1 = [ax[0] - dot * e2[0], ax[1] - dot * e2[1], ax[2] - dot * e2[2]];
  let m = Math.hypot(e1[0], e1[1], e1[2]);
  if (m < 1e-9) { e1 = Math.abs(e2[0]) < 0.9 ? [1, 0, 0] : [0, 0, 1]; dot = e1[0] * e2[0] + e1[1] * e2[1] + e1[2] * e2[2]; e1 = [e1[0] - dot * e2[0], e1[1] - dot * e2[1], e1[2] - dot * e2[2]]; m = Math.hypot(e1[0], e1[1], e1[2]); }
  e1 = [e1[0] / m, e1[1] / m, e1[2] / m];
  const e3 = [e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0]];
  for (let i = 0; i < n; i++) {
    const o = i * 3, v = [d[o], d[o + 1], d[o + 2]];
    out[o] = v[0] * e1[0] + v[1] * e1[1] + v[2] * e1[2];
    out[o + 1] = v[0] * e2[0] + v[1] * e2[1] + v[2] * e2[2];
    out[o + 2] = v[0] * e3[0] + v[1] * e3[1] + v[2] * e3[2];
  }
  return out;
}

// ---------------- particles ----------------
const SEG = 2.7, CONE = 1.3, MAST_EXTRA = 1.5;            // Spacelab segment & end cone (m); mast = bloom radius + 1.5 m
const HUB = 1200, STALK = 30, POD = 280, BLOOM = 226, RAD = 96, RING = 40, BRING = 48, SHUTTLE = 2400;
const PER = STALK + POD + BLOOM + RAD + RING + BRING, COMN = 60;
// Data block (particles 0..DATA-1), read back with gravity-mcp's run_sim (particleCount = sample = 5000 → every
// particle in order). Rows 0..63: pod q's direction; rows 64..127: the direction of the pod flown at launch r + 1;
// row 128: (pods / 100, relax progress / 2, 0). Unused rows sit at the origin. Directions are in the canonical,
// un-spun frame at a fixed radius inside the hub, so they don't show; normalise to read them.
const DATA = 2 * MAXP + 1, DATA_R = 0.9;
const O_HUB = DATA, O_POD0 = O_HUB + HUB, O_SHUT = O_POD0 + MAXP * PER, O_COM = O_SHUT + SHUTTLE, O_END = O_COM + COMN;
const M_HUB = 20, M_SEG = 4, M_BLOOM = 1.5;              // tonnes, for the centre-of-mass marker

// Assembly order over the final pod directions (keep in sync with STEVE's station_geometry.py).
// Pod 0 (the axial docking pod) flies first with the hub. mode 0: opposite pairs — each next pod minimises
// the centre-of-mass offset (decussate leaves); 1: biggest gap — each next pod goes where the
// inhibitor field of the pods already there is weakest (sunflower primordia); 2: index order. Near-ties (within TIE) go to the lowest
// index, so tiny float differences between Gravity and STEVE can't change the order.
const TIE = [0.02, 1e-3, 0];   // per mode: |CoM sum| in pod units; inhibitor field
function buildOrder(v, n, mode) {
  const order = [0], left = [];
  for (let i = 1; i < n; i++) left.push(i);
  while (left.length) {
    let best = left[0], bestVal = Infinity;
    if (mode !== 2) for (const j of left) {
      let val;
      if (mode === 0) {
        let sx = v[j * 3], sy = v[j * 3 + 1], sz = v[j * 3 + 2];
        for (const i of order) { sx += v[i * 3]; sy += v[i * 3 + 1]; sz += v[i * 3 + 2]; }
        val = Math.hypot(sx, sy, sz);
      } else {   // inhibitor field (Douady & Couder): each placed pod inhibits exp(-chord / 0.5); go where it's weakest
        val = 0;
        for (const i of order) {
          const dt = v[i * 3] * v[j * 3] + v[i * 3 + 1] * v[j * 3 + 1] + v[i * 3 + 2] * v[j * 3 + 2];
          val += Math.exp(-Math.sqrt(Math.max(0, 2 - 2 * dt)) / 0.5);
        }
      }
      if (val < bestVal - TIE[mode]) { bestVal = val; best = j; }
    }
    order.push(best); left.splice(left.indexOf(best), 1);
  }
  return order;
}
const COLORS = [ // per-pod block colours, in block order
  [STALK, 0.95, 0.75, 0.3],   // stalk: gold MLI
  [POD, 0.93, 0.93, 0.9],     // pod: beta-cloth white
  [BLOOM, 0.25, 0.45, 1.0],   // bloom: solar-cell blue
  [RAD, 0.85, 0.95, 1.0],     // radiators: bright white
  [RING, 1.0, 0.18, 0.15],    // pod clash ring: red
  [BRING, 1.0, 0.45, 0.1],    // bloom clash ring: orange
];

export function create(ctx) {
  const { particleCount: total, positions: pos, colors: col, params } = ctx;
  const setCol = (from, count, r, g, b) => {
    for (let i = from; i < Math.min(from + count, total); i++) { col[i * 3] = r; col[i * 3 + 1] = g; col[i * 3 + 2] = b; }
  };
  setCol(0, DATA + HUB, 0.55, 0.72, 0.95);
  for (let q = 0; q < MAXP; q++) {
    let o = O_POD0 + q * PER;
    for (const [n, r, g, b] of COLORS) { setCol(o, n, r, g, b); o += n; }
  }
  setCol(O_SHUT, SHUTTLE, 0.97, 0.97, 0.95);
  setCol(O_COM, COMN, 1.0, 0.2, 1.0);                     // centre-of-mass marker: magenta
  setCol(O_END, total - O_END, 0, 0, 0);

  // Shuttle silhouette in orbiter-local metres (x nose, y port, z bay-up): fuselage, wings, tail, engines.
  // Fixed random-free sampling so the shape is identical every run.
  const shut = new Float32Array(SHUTTLE * 3);
  const black = new Uint8Array(SHUTTLE);
  {
    let i = 0;
    const add = (x, y, z, b = 0) => { if (i < SHUTTLE) { shut[i * 3] = x; shut[i * 3 + 1] = y; shut[i * 3 + 2] = z; black[i] = b; i++; } };
    // fuselage: rounded box sections from tail (-12.6) to nose (18.7), cabin hump forward
    for (let s = 0; s < 40; s++) {
      const x = -12.6 + (31.3 * s) / 39;
      const nose = Math.max(0, (x - 13) / 5.7);                 // taper over the last 5.7 m
      const w = 2.6 * (1 - 0.92 * nose * nose), zb = -2.5 + 1.4 * nose, zt = (x > 10 && x < 15.5 ? 2.75 : 1.9) * (1 - nose) - 0.9 * nose;
      for (let a = 0; a < 24; a++) {
        const t = (a / 24) * 2 * Math.PI, c = Math.cos(t), sn = Math.sin(t);
        const z = sn >= 0 ? zt * sn : zb * -sn;
        add(x, w * c, z, sn < -0.3 ? 1 : 0);
      }
    }
    // double-delta wings (z = -2.4), sampled on a grid inside the planform
    for (let gx = 0; gx < 38; gx++) for (let gy = 0; gy < 24; gy++) {
      const x = 7.2 - (19.5 * gx) / 37, y = 2.4 + (9.5 * gy) / 23;
      const le = y < 4.4 ? 7.2 - (7.5 * (y - 2.4)) / 2.0 : -0.3 - (9.1 * (y - 4.4)) / 7.5;
      if (x <= le && x >= -12.3) { add(x, y, -2.4, 1); add(x, -y, -2.4, 1); }
    }
    // vertical tail
    for (let gz = 0; gz < 16; gz++) for (let gx = 0; gx < 14; gx++) {
      const z = 1.9 + (7.9 * gz) / 15, le = -8.5 - (7.0 * (z - 1.9)) / 7.9, te = -15.7 - (1.6 * (z - 1.9)) / 7.9;
      add(le + ((te - le) * gx) / 13, 0, z);
    }
    // three main engines + two OMS pods (rings)
    for (const [y, z, r] of [[0, 0.95, 1.1], [1.35, -1.15, 1.1], [-1.35, -1.15, 1.1], [1.95, 1.9, 0.9], [-1.95, 1.9, 0.9]])
      for (let a = 0; a < 20; a++) add(-14.5, y + r * Math.cos(a * 0.314), z + r * Math.sin(a * 0.314));
    while (i < SHUTTLE) add(0, 0, 0);
  }
  for (let i = 0; i < SHUTTLE; i++) if (black[i] && O_SHUT + i < total) { col[(O_SHUT + i) * 3] = 0.12; col[(O_SHUT + i) * 3 + 1] = 0.12; col[(O_SHUT + i) * 3 + 2] = 0.14; }

  let n = 0, k = 0, start = -1, seed = -1, relax = -1, it = 0, dirs = null, view = null, theta = 0, clock = 0;
  const reset = (p) => {
    n = Math.round(p.pods); k = p.k; start = p.start; seed = Math.round(p.seed); relax = p.relax;
    dirs = startDirs(n, start, seed); it = 0;
  };
  const put = (i, x, y, z) => { if (i >= total) return; pos[i * 3] = x; pos[i * 3 + 1] = y; pos[i * 3 + 2] = z; };
  const park = (from, count) => { for (let i = from; i < from + count; i++) put(i, 0, 0, 0); };

  const draw = (p) => {
    const segs = Math.round(p.segments), podLen = segs * SEG;
    const R = p.bloomD / 2, mast = R > 0 ? R + MAST_EXTRA : 0;
    const r0 = p.hub + p.reach, rTip = r0 + podLen, rCone = rTip + CONE, rPort = rCone + 1.6;
    const rMax = Math.max(rCone + mast + R, rPort + 9);
    const S = Math.min(1, 19 / rMax);
    const c = Math.cos(theta), s = Math.sin(theta);
    const W = (i, x, y, z) => put(i, (x * c + z * s) * S, y * S, (-x * s + z * c) * S); // spin about y
    const Wsun = (i, x, y, z) => put(i, x * S, y * S, z * S);                              // sun-fixed (gimballed)
    const spinV = (x, y, z) => [x * c + z * s, y, -x * s + z * c];

    // assembly stage: launch 1 = hub + pod 0, then one pod per launch; within a launch (f: 0 → 1) the
    // stalk appears, segments are berthed one at a time from the hub outward (f < 0.7), then the end cone,
    // the mast, the bloom unfolding (0.8–1.0) and the radiators (≥ 0.9)
    const order = buildOrder(view, n, Math.round(p.order));
    const rank = new Int32Array(n);
    order.forEach((q, r) => { rank[q] = r; });
    const stage = p.timelapse >= 0.5 ? (clock * 0.25) % (n + 2) : Math.min(Math.round(p.launch), n);
    const frac = (q) => Math.max(0, Math.min(1, stage - rank[q]));
    const segsShown = (f) => Math.min(segs, Math.ceil((f / 0.7) * segs - 1e-9));
    const bloomScale = (f) => Math.max(0, Math.min(1, (f - 0.8) / 0.2));
    let cmx = 0, cmy = 0, cmz = 0, mass = M_HUB;

    const ga = Math.PI * (3 - Math.sqrt(5));
    for (let i = 0; i < HUB; i++) {
      const y = 1 - (2 * (i + 0.5)) / HUB, r = Math.sqrt(1 - y * y), a = i * ga;
      W(O_HUB + i, p.hub * r * Math.cos(a), p.hub * y, p.hub * r * Math.sin(a));
    }
    const dr = DATA_R * p.hub * S;                                       // data block (see DATA)
    for (let q = 0; q < MAXP; q++) {
      if (q < n) put(q, view[q * 3] * dr, view[q * 3 + 1] * dr, view[q * 3 + 2] * dr); else put(q, 0, 0, 0);
      const o = order[q];
      if (q < n) put(MAXP + q, view[o * 3] * dr, view[o * 3 + 1] * dr, view[o * 3 + 2] * dr); else put(MAXP + q, 0, 0, 0);
    }
    put(2 * MAXP, n / 100, relax >= 0.5 ? (0.5 * it) / ITERS : 0.5, 0);
    // clash tests: pod roots, and bloom centres (blooms all face the sun, so they overlap when centres
    // projected onto the sun-facing plane are closer than a diameter and they sit at similar depth)
    const lim = (2 * p.podR + p.clear) / r0;
    const clash = new Uint8Array(n), bclash = new Uint8Array(n);
    const rb = rCone + mast;
    for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j++) {
      if (frac(i) <= 0 || frac(j) <= 0) continue;           // only pods already flown can clash
      const dx = view[i * 3] - view[j * 3], dy = view[i * 3 + 1] - view[j * 3 + 1], dz = view[i * 3 + 2] - view[j * 3 + 2];
      if (Math.hypot(dx, dy, dz) < lim) { clash[i] = 1; clash[j] = 1; }
      if (R > 0 && i > 0 && Math.hypot(dx, dy, dz) * rb < p.bloomD + p.clear) { bclash[i] = 1; bclash[j] = 1; }
    }
    for (let q = 0; q < MAXP; q++) {
      let o = O_POD0 + q * PER;
      if (q >= n || frac(q) <= 0) { park(o, PER); continue; }
      const f = frac(q), shown = segsShown(f), bs = bloomScale(f);
      const dx = view[q * 3], dy = view[q * 3 + 1], dz = view[q * 3 + 2];
      for (let j = 0; j < shown; j++) {                                    // centre of mass: segments
        const r = r0 + (j + 0.5) * SEG; cmx += M_SEG * dx * r; cmy += M_SEG * dy * r; cmz += M_SEG * dz * r; mass += M_SEG;
      }
      if (q > 0 && bs > 0) { cmx += M_BLOOM * dx * rb; cmy += M_BLOOM * dy * rb; cmz += M_BLOOM * dz * rb; mass += M_BLOOM; }
      let ax = Math.abs(dy) < 0.9 ? [0, 1, 0] : [1, 0, 0];
      let ux = ax[1] * dz - ax[2] * dy, uy = ax[2] * dx - ax[0] * dz, uz = ax[0] * dy - ax[1] * dx;
      const um = Math.hypot(ux, uy, uz); ux /= um; uy /= um; uz /= um;
      const vx = dy * uz - dz * uy, vy = dz * ux - dx * uz, vz = dx * uy - dy * ux;
      const ringPt = (i, r, rad, a) => W(i, dx * r + rad * (ux * Math.cos(a) + vx * Math.sin(a)),
                                          dy * r + rad * (uy * Math.cos(a) + vy * Math.sin(a)),
                                          dz * r + rad * (uz * Math.cos(a) + vz * Math.sin(a)));
      // stalk
      for (let t = 0; t < STALK; t++) ringPt(o + t, p.hub + (p.reach * t) / (STALK - 1), 0.45, t * 1.9);
      o += STALK;
      // pod: two rings per segment (a joint ring + a mid ring), up to 7 segments → 15 rings × 16, + cone
      let i = o;
      for (let g = 0; g <= 2 * shown; g++) for (let a = 0; a < 16; a++) ringPt(i++, r0 + (SEG * g) / 2, g % 2 ? p.podR : p.podR + 0.08, (a + 0.5 * (g & 1)) * (Math.PI / 8));
      if (f >= 0.7) for (let a = 0; a < 20; a++) ringPt(i++, rTip + CONE, 1.3, a * (Math.PI / 10));
      for (let a = 0; a < 20; a++) ringPt(i++, r0, p.podR * 0.55, a * (Math.PI / 10));
      park(i, o + POD - i); o += POD;
      // bloom: gimbal mast along the pod, then a sun-facing disc (normal +x, world-fixed) — pod 0 docks instead
      i = o;
      if (q > 0 && R > 0 && f >= 0.75) {
        for (let t = 0; t < 10; t++) ringPt(i++, rCone + (mast * t) / 9, 0.25, t * 2.1);
        const C = spinV(dx * rb, dy * rb, dz * rb);
        for (let ring = 1; ring <= 6; ring++) for (let a = 0; a < 24; a++) {
          const rr = (R * bs * ring) / 6, t = (a / 24) * 2 * Math.PI + (ring & 1) * 0.13;
          Wsun(i++, C[0], C[1] + rr * Math.cos(t), C[2] + rr * Math.sin(t));
        }
        for (let g = 0; g < 12; g++) for (let t = 1; t <= 6; t++) {
          const a = (g / 12) * 2 * Math.PI + (1 - bs) * 1.2, rr = (R * bs * t) / 6.5;   // gores swing open as it unfolds
          Wsun(i++, C[0] - 0.08, C[1] + rr * Math.cos(a), C[2] + rr * Math.sin(a));
        }
      }
      park(i, o + BLOOM - i); o += BLOOM;
      // radiators: two fins over the outer 60 % of the pod, edge-on to the sun (plane holds the pod axis and +x)
      i = o;
      if (f < 0.9) park(o, RAD);
      else {
        const P = spinV(dx, dy, dz);                                  // pod axis in the sun frame
        let nx = 0, ny = P[2], nz = -P[1];                             // n = P × x̂
        let nm = Math.hypot(ny, nz);
        if (nm < 1e-6) { ny = 0; nz = 1; nm = 1; }
        ny /= nm; nz /= nm;
        const wx = ny * P[2] - nz * P[1], wy = nz * P[0] - nx * P[2], wz = nx * P[1] - ny * P[0]; // w = n × P
        for (const sg of [1, -1]) for (let a = 0; a < 12; a++) for (let b = 0; b < 4; b++) {
          const r = r0 + podLen * (0.35 + (0.6 * a) / 11), off = sg * (p.podR + 0.4 + (3 * b) / 3);
          Wsun(i++, P[0] * r + wx * off, P[1] * r + wy * off, P[2] * r + wz * off);
        }
      }
      o += RAD;
      // clash rings
      for (let a = 0; a < RING; a++) { if (clash[q]) ringPt(o + a, r0, p.podR + 0.35, (a * 2 * Math.PI) / RING); else put(o + a, 0, 0, 0); }
      o += RING;
      if (bclash[q] && q > 0 && R > 0) {
        const C = spinV(dx * rb, dy * rb, dz * rb);
        for (let a = 0; a < BRING; a++) Wsun(o + a, C[0] + 0.1, C[1] + (R + 0.4) * Math.cos((a * 2 * Math.PI) / BRING), C[2] + (R + 0.4) * Math.sin((a * 2 * Math.PI) / BRING));
      } else park(o, BRING);
    }
    // Shuttle docked at pod 0's port: orbiter-local (x, y, z) -> (x - 8.3, -z + rPort + 3.1, y) in Gravity's frame,
    // i.e. bay facing down at the station, nose toward the sun (+x).
    // It arrives once pod 0 (flown with the hub) is complete, i.e. from launch 2 on.
    if (p.shuttle >= 0.5 && frac(0) >= 1) {
      for (let i = 0; i < SHUTTLE; i++) {
        const x = shut[i * 3], y = shut[i * 3 + 1], z = shut[i * 3 + 2];
        if (x === 0 && y === 0 && z === 0) { put(O_SHUT + i, 0, 0, 0); continue; }
        W(O_SHUT + i, x - 8.3, -z + rPort + 3.1, y);
      }
    } else park(O_SHUT, SHUTTLE);
    // centre-of-mass marker: a 3-axis cross, 2 m arms (the visiting Shuttle is not counted)
    cmx /= mass; cmy /= mass; cmz /= mass;
    for (let a = 0; a < COMN; a++) {
      const t = ((a % 20) / 19 - 0.5) * 2, axis = Math.floor(a / 20);
      W(O_COM + a, cmx + (axis === 0 ? t : 0), cmy + (axis === 1 ? t : 0), cmz + (axis === 2 ? t : 0));
    }
    park(O_END, total - O_END);
  };

  reset(params);
  view = canonical(dirs, n);
  draw(params);

  return {
    step(dt, p) {
      if (Math.round(p.pods) !== n || p.k !== k || p.start !== start || Math.round(p.seed) !== seed || p.relax !== relax) reset(p);
      if (relax >= 0.5) for (let s = 0; s < PER_FRAME && it < ITERS; s++, it++) relaxStep(dirs, n, k, it);
      view = canonical(dirs, n);
      theta += (p.rpm * 2 * Math.PI / 60) * dt;
      clock += dt;
      draw(p);
    },
  };
}
