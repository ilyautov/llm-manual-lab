import assert from 'node:assert/strict';
import test from 'node:test';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { traceTariff } from '../src/rag.ts';
import { fixtureOrders, paidOrders } from '../src/orders.ts';
import { countDeliveries, openWebhookDb } from '../src/webhook.ts';
import { runWorker } from '../src/webhook-demo.ts';

test('the tariff answer requires a retrieved fragment in the context', () => {
  const withDocument = traceTariff(true);
  const withoutDocument = traceTariff(false);
  assert.deepEqual(withDocument.retrievedIds, ['tariff-a-v2:price']);
  assert.match(withDocument.context, /300 ₽/u);
  assert.match(withDocument.answer, /по tariff-a-v2:price/u);
  assert.equal(withoutDocument.context, '');
  assert.match(withoutDocument.answer, /не подтверждена/u);
});

test('the runtime checks permission before reading the order fixture', () => {
  assert.equal(fixtureOrders().length, 45);
  const allowed = paidOrders('reader', '2025-03-01');
  const denied = paidOrders('guest', '2025-03-01');
  assert.equal(allowed.count, 42);
  assert.ok(allowed.events.some((event) => event === 'db_result: count=42'));
  assert.equal(denied.count, null);
  assert.ok(!denied.events.some((event) => event.startsWith('db_query:')));
});

test('two separate processes deliver one event to a SQLite unique index', async () => {
  const temp = mkdtempSync(join(tmpdir(), 'llm-manual-test-'));
  try {
    const path = join(temp, 'deliveries.sqlite');
    const first = openWebhookDb(path);
    first.close();
    const results = await Promise.all([runWorker(path, 'evt-42'), runWorker(path, 'evt-42')]);
    const db = openWebhookDb(path);
    try {
      assert.equal(results.filter((item) => item.inserted).length, 1);
      assert.equal(countDeliveries(db, 'evt-42'), 1);
    } finally { db.close(); }
  } finally { rmSync(temp, { recursive: true, force: true }); }
});
