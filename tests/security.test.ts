import test from 'node:test';
import assert from 'node:assert/strict';
import { executeWithReadOnlyPolicy, injectionDemo } from '../src/security.ts';

test('untrusted document cannot grant write or log sending permission', () => {
  const demo = injectionDemo();
  assert.match(demo.source, /измени статус заказа/u);
  assert.deepEqual(demo.decisions.map((x) => x.allowed), [false, false, true]);
  assert.equal(demo.decisions[2].result, 'db_result: count=42');
  assert.match(demo.decisions[0].result, /runtime_denied/u);
  assert.match(demo.decisions[1].result, /runtime_denied/u);
  assert.equal(executeWithReadOnlyPolicy({ name: 'paid_orders', date: 'bad' }).allowed, false);
});
