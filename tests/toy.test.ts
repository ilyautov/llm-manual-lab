import assert from 'node:assert/strict';
import test from 'node:test';
import { crossEntropy, INITIAL_LOGITS, softmax, tokenize, trainSentence } from '../src/toy-model.ts';
import { causalPairs, loraEntries, lossAtProbability, lossOnSurface, temperatureRows } from '../src/math.ts';

test('the documented sentence maps to stable token IDs', () => {
  assert.deepEqual(tokenize('я люблю чай'), [0, 1, 2]);
  assert.throws(() => tokenize('я люблю кофе'), /Unknown toy-vocabulary token/);
});

test('softmax makes a normalized distribution and temperature changes its sharpness', () => {
  const rows = temperatureRows();
  for (const row of rows) assert.ok(Math.abs(row.probabilities.reduce((a, b) => a + b, 0) - 1) < 1e-12);
  assert.ok(rows[0].probabilities[0] > rows[1].probabilities[0]);
  assert.ok(rows[1].probabilities[0] > rows[2].probabilities[0]);
  assert.deepEqual(softmax([1000, 999]).map((n) => Number(n.toFixed(3))), [0.731, 0.269]);
});

test('analytic cross-entropy gradient matches a finite difference', () => {
  const trace = trainSentence();
  const epsilon = 1e-6;
  for (let id = 0; id < 3; id++) {
    const plus = [...trace.logitsBefore];
    const minus = [...trace.logitsBefore];
    plus[id] += epsilon;
    minus[id] -= epsilon;
    const numeric = (crossEntropy(softmax(plus), trace.targetId) -
      crossEntropy(softmax(minus), trace.targetId)) / (2 * epsilon);
    assert.ok(Math.abs(numeric - trace.gradient[id]) < 1e-8);
  }
});

test('one training step improves the target without mutating the initial model', () => {
  const trace = trainSentence();
  assert.ok(trace.probabilitiesAfter[trace.targetId] > trace.probabilitiesBefore[trace.targetId]);
  assert.ok(trace.lossAfter < trace.lossBefore);
  assert.deepEqual(INITIAL_LOGITS[1], [2, 1, 0]);
  assert.ok(trace.probabilitiesAfter[trace.targetId] < 1);
});

test('the 3D surface has the exact loss at both plotted points', () => {
  const trace = trainSentence();
  for (const [logits, expected] of [[trace.logitsBefore, trace.lossBefore],
    [trace.logitsAfter, trace.lossAfter]] as const) {
    const x = logits[0] - logits[2];
    const y = logits[1] - logits[2];
    assert.ok(Math.abs(lossOnSurface(x, y) - expected) < 1e-12);
    const shifted = logits.map((z) => z + 17);
    assert.ok(Math.abs(crossEntropy(softmax(shifted), 2) - expected) < 1e-12);
  }
});

test('quantitative charts have exact mathematical anchors', () => {
  assert.ok(Math.abs(lossAtProbability(.1) - 2.30258509299) < 1e-9);
  assert.equal(causalPairs(4), 10);
  assert.equal(causalPairs(1024), 524800);
  assert.equal(loraEntries(1000, 1000, 8), 16000);
});
