import test from 'node:test';
import assert from 'node:assert/strict';
import { evaluationDemo, retrievalScore, wilsonInterval } from '../src/evaluation.ts';
import { constrainedSoftmax } from '../src/structured-output.ts';

test('Wilson intervals match both printed examples and handle endpoints', () => {
  const { diagnosticTwelve, sampleHundred } = evaluationDemo();
  assert.deepEqual([diagnosticTwelve.low, diagnosticTwelve.high].map((x) => Number((x * 100).toFixed(1))), [55.2, 95.3]);
  assert.deepEqual([sampleHundred.low, sampleHundred.high].map((x) => Number((x * 100).toFixed(1))), [71.1, 86.7]);
  assert.equal(wilsonInterval(0, 10).low, 0);
  assert.equal(wilsonInterval(10, 10).high, 1);
  assert.throws(() => wilsonInterval(2, 1), RangeError);
});

test('retrieval scores count absent candidates as zero reciprocal rank', () => {
  assert.deepEqual(retrievalScore([1, 2, null], 3), { recallAtK: 2 / 3, mrrAtK: .5 });
  assert.deepEqual(retrievalScore([1, 1, 2], 3), { recallAtK: 1, mrrAtK: 5 / 6 });
  assert.deepEqual(retrievalScore([4], 3), { recallAtK: 0, mrrAtK: 0 });
});

test('constrained softmax removes forbidden choices and renormalizes', () => {
  const result = constrainedSoftmax([2, 1, 0], [false, true, true]);
  assert.equal(result[0], 0);
  assert.ok(Math.abs(result[1] - .7310585786) < 1e-9);
  assert.ok(Math.abs(result[2] - .2689414214) < 1e-9);
  assert.ok(Math.abs(result.reduce((a, b) => a + b, 0) - 1) < 1e-12);
  assert.throws(() => constrainedSoftmax([2, 1], [false, false]), RangeError);
});
