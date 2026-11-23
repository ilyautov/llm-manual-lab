import { test } from 'node:test';
import assert from 'node:assert/strict';
import { extractPrices, firstPrice } from '../src/price.ts';

test('одна цена, цена с разрядом, отсутствие цены', () => {
  assert.deepEqual(extractPrices('Цена 300 ₽'), [300]);
  assert.deepEqual(extractPrices('Итого 1 200 ₽'), [1200]);
  assert.deepEqual(extractPrices('Нет подтверждённой цены.'), []);
  assert.equal(firstPrice('Нет цены.'), null);
});

test('две цены дают конфликт: live-lab и live-evaluate читают один список', () => {
  const answer = 'Раньше 250 ₽, теперь 300 ₽';
  const prices = extractPrices(answer);
  assert.deepEqual(prices, [250, 300]);
  assert.equal(prices.length === 1 && prices[0] === 300, false, 'live-lab: конфликту нет доверия');
  assert.equal(firstPrice(answer), 250, 'live-evaluate: первая цена без молчаливого выбора в пользу ожидания');
});
