// Run the Gravity sim headless and record particle positions for a video.
// node gravity_record.mjs <out.bin> <frames> <dt> [json param overrides]
// Output: int32 particleCount, int32 frames, float32 colors[n*3], then float32 positions[n*3] per frame.
import fs from 'fs';
import { meta, create } from '../../gravity/blowball_station.js';

const [out, framesArg, dtArg, over] = process.argv.slice(2);
const frames = parseInt(framesArg, 10), dt = parseFloat(dtArg);
const n = meta.particleCount;
const params = Object.fromEntries(meta.params.map((p) => [p.key, p.default]));
Object.assign(params, JSON.parse(over || '{}'));
const ctx = { particleCount: n, positions: new Float32Array(n * 3), colors: new Float32Array(n * 3), params, sdk: {}, rng: Math.random };
const sim = create(ctx);
const fd = fs.openSync(out, 'w');
fs.writeSync(fd, Buffer.from(new Int32Array([n, frames]).buffer));
fs.writeSync(fd, Buffer.from(ctx.colors.buffer));
for (let f = 0; f < frames; f++) {
  sim.step(dt, params);
  fs.writeSync(fd, Buffer.from(ctx.positions.buffer));
}
fs.closeSync(fd);
