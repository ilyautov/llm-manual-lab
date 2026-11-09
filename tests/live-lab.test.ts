import test from 'node:test';
import assert from 'node:assert/strict';
import { executePaidOrdersCall, ordersWithRealModel, tariffWithRealModel,
  type ChatTransport } from '../src/live-lab.ts';

const validCall = { type: 'function' as const,
  function: { name: 'paid_orders', arguments: { date: '2025-03-01', status: 'paid' } } };

test('runtime validates actual proposed arguments and privileges', () => {
  assert.equal(executePaidOrdersCall(validCall).count, 42);
  assert.equal(executePaidOrdersCall(validCall, 'guest').allowed, false);
  assert.equal(executePaidOrdersCall({ type: 'function',
    function: { name: 'paid_orders', arguments: { date: '2025-03-01', status: 'paid', admin: true } } }).allowed, false);
  assert.equal(executePaidOrdersCall({ type: 'function',
    function: { name: 'delete_orders', arguments: { date: '2025-03-01' } } }).allowed, false);
  assert.equal(executePaidOrdersCall({ type: 'function',
    function: { name: 'paid_orders', arguments: { date: '2025-03-02', status: 'paid' } } }).allowed, false);
});

test('tool result reaches the model only after runtime execution', async () => {
  const requests: unknown[] = [];
  const chat: ChatTransport = async (request) => {
    requests.push(request);
    return requests.length === 1
      ? { message: { content: '', tool_calls: [validCall] } }
      : { message: { content: '1 марта было 42 оплаченных заказа.' } };
  };
  const result = await ordersWithRealModel(chat);
  assert.equal(result.executed, true);
  assert.equal(result.answerMatchesResult, true);
  assert.equal(requests.length, 2);
  const last = requests[1] as { messages: { role: string; content: string }[] };
  assert.equal(last.messages.at(-1)?.role, 'tool');
  assert.match(last.messages.at(-1)?.content ?? '', /"count":42/u);
});

test('no model tool call is not misreported as database execution', async () => {
  const chat: ChatTransport = async () => ({ message: { content: 'Наверное, 42.' } });
  const result = await ordersWithRealModel(chat);
  assert.equal(result.executed, false);
  assert.equal(result.proposedCalls, 0);
});

test('tariff check distinguishes model output from retrieved document', async () => {
  const chat: ChatTransport = async () => ({ message: { content: 'Тариф А стоит 300 ₽.' } });
  assert.equal((await tariffWithRealModel(chat, 'test', true)).priceMatchesSource, true);
  assert.equal((await tariffWithRealModel(chat, 'test', false)).unsupportedPrice, true);
  const conflicting: ChatTransport = async () => ({ message: { content: '300 ₽ или 900 ₽' } });
  assert.equal((await tariffWithRealModel(conflicting, 'test', true)).priceMatchesSource, false);
});
