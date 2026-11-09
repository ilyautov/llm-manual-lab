import test from 'node:test';
import assert from 'node:assert/strict';
import { attentionRow } from '../src/tiny-attention.ts';

test('causal mask blocks the future token and rows normalize', () => {
  const row = attentionRow(1);
  assert.deepEqual(row.rawScores, [0, 1, 1]);
  assert.equal(row.maskedScores[2], -Infinity);
  assert.equal(row.probabilities[2], 0);
  assert.ok(Math.abs(row.probabilities.reduce((a, b) => a + b, 0) - 1) < 1e-12);
  assert.ok(Math.abs(row.probabilities[0] - 0.3302384506733431) < 1e-12);
});

test('changing a future value cannot affect this attention row', () => {
  const original = attentionRow(1);
  const changed = attentionRow(1, [[1, 0], [0, 1], [500, -700]]);
  assert.deepEqual(changed.context, original.context);
  assert.deepEqual(changed.residual, original.residual);
  assert.deepEqual(changed.outputProbabilities, original.outputProbabilities);
});
