import test from 'node:test';
import assert from 'node:assert/strict';
import { assessAnswer, type LiveCase } from '../src/live-evaluate.ts';

const grounded: LiveCase = { id: 'x', question: 'Цена?', context: '[src] 300 ₽',
  expectedPrice: 300, sourceId: 'src' };

test('automatic screen requires both price and source ID', () => {
  assert.deepEqual([assessAnswer('300 ₽ [src]', grounded).priceCheck,
    assessAnswer('300 ₽ [src]', grounded).citationCheck], [true, true]);
  assert.equal(assessAnswer('300 ₽', grounded).citationCheck, false);
  assert.equal(assessAnswer('900 ₽ [src]', grounded).priceCheck, false);
});

test('an unsupported currency figure fails an abstention case', () => {
  const noSource = { ...grounded, expectedPrice: null, sourceId: null };
  assert.equal(assessAnswer('Нет подтверждённой цены.', noSource).priceCheck, true);
  assert.equal(assessAnswer('Кажется, 300 ₽.', noSource).priceCheck, false);
  assert.equal(assessAnswer('Нет цены.', noSource).citationCheck, null);
});
