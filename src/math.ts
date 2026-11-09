import { softmax } from './toy-model.ts';

export function lossAtProbability(p: number): number {
  if (!(p > 0 && p <= 1)) throw new RangeError('p must lie in (0, 1]');
  return -Math.log(p);
}

/** Page 20: exact cross-entropy surface after taking differences from the target logit. */
export function lossOnSurface(x: number, y: number): number {
  if (!Number.isFinite(x) || !Number.isFinite(y)) throw new RangeError('coordinates must be finite');
  const maximum = Math.max(0, x, y);
  return maximum + Math.log(Math.exp(-maximum) + Math.exp(x - maximum) + Math.exp(y - maximum));
}

/** Number of visible position pairs in a causal attention matrix, self included. */
export function causalPairs(length: number): number {
  if (!Number.isInteger(length) || length < 1) throw new RangeError('length must be a positive integer');
  return length * (length + 1) / 2;
}

/** Trainable A and B entries for one LoRA-adapted d-by-k matrix. */
export function loraEntries(d: number, k: number, rank: number): number {
  if (![d, k, rank].every(Number.isInteger) || d < 1 || k < 1 || rank < 1) {
    throw new RangeError('dimensions and rank must be positive integers');
  }
  return rank * (d + k);
}

export function temperatureRows(): { temperature: number; probabilities: number[] }[] {
  return [0.5, 1, 2].map((temperature) => ({
    temperature,
    probabilities: softmax([2, 1, 0], temperature),
  }));
}
