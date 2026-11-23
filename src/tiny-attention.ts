/** A hand-computable single causal attention head. Fixed weights, no training. */
import { pathToFileURL } from 'node:url';

export const ATTENTION_TOKENS = ['я', 'люблю', 'чай'] as const;
export type Vector2 = readonly [number, number];
export const EMBEDDINGS: readonly Vector2[] = [[1, 0], [0, 1], [1, 1]];

function dot(a: Vector2, b: Vector2): number {
  return a[0] * b[0] + a[1] * b[1];
}

function stableMaskedSoftmax(scores: readonly number[], visibleCount: number): number[] {
  const visible = scores.slice(0, visibleCount);
  const maximum = Math.max(...visible);
  const weights = visible.map((score) => Math.exp(score - maximum));
  const total = weights.reduce((sum, weight) => sum + weight, 0);
  return scores.map((_, index) => index < visibleCount ? weights[index] / total : 0);
}

export interface AttentionRow {
  position: number;
  rawScores: number[];
  scaledScores: number[];
  maskedScores: number[];
  probabilities: number[];
  context: Vector2;
  residual: Vector2;
  logits: number[];
  outputProbabilities: number[];
}

/** Identity Wq/Wk/Wv; output candidates use the three embedding vectors. */
export function attentionRow(position: number, embeddings: readonly Vector2[] = EMBEDDINGS): AttentionRow {
  if (!Number.isInteger(position) || position < 0 || position >= embeddings.length) {
    throw new RangeError('position outside sequence');
  }
  if (embeddings.length === 0 || embeddings.some((v) => v.length !== 2 || v.some((x) => !Number.isFinite(x)))) {
    throw new RangeError('embeddings must be finite 2D vectors');
  }
  const query = embeddings[position];
  const rawScores = embeddings.map((key) => dot(query, key));
  const scaledScores = rawScores.map((score) => score / Math.sqrt(2));
  const maskedScores = scaledScores.map((score, index) => index <= position ? score : -Infinity);
  const probabilities = stableMaskedSoftmax(scaledScores, position + 1);
  const context: Vector2 = [
    probabilities.reduce((sum, p, index) => sum + p * embeddings[index][0], 0),
    probabilities.reduce((sum, p, index) => sum + p * embeddings[index][1], 0),
  ];
  const residual: Vector2 = [query[0] + context[0], query[1] + context[1]];
  const logits = EMBEDDINGS.map((candidate) => dot(residual, candidate));
  const outputProbabilities = stableMaskedSoftmax(logits, logits.length);
  return { position, rawScores, scaledScores, maskedScores, probabilities,
    context, residual, logits, outputProbabilities };
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const row = attentionRow(1);
  console.log(JSON.stringify({ tokens: ATTENTION_TOKENS, embeddings: EMBEDDINGS,
    ...row, maskedScores: row.maskedScores.map((score) => Number.isFinite(score) ? score : '−∞') }, null, 2));
}
