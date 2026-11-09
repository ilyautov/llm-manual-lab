import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { runInNewContext } from 'node:vm';
import { softmax } from '../src/toy-model.ts';
import { attentionRow } from '../src/tiny-attention.ts';
import { loraEntries } from '../src/math.ts';

interface MockElement {
  value: string;
  textContent: string;
  innerHTML: string;
  style: { width: string };
  attributes: Map<string, string>;
  listeners: Map<string, () => void>;
  addEventListener(event: string, callback: () => void): void;
  setAttribute(name: string, value: string): void;
}

function page() {
  const source = readFileSync(new URL('../interactive/index.html', import.meta.url), 'utf8');
  const match = source.match(/<script>([\s\S]*?)<\/script>/u);
  assert.ok(match, 'the offline page has an inline script');
  const elements = new Map<string, MockElement>();
  const get = (id: string): MockElement => {
    if (!elements.has(id)) elements.set(id, {
      value: id === 'temperature-range' ? '1' : id === 'position-range' ? '1' :
        id === 'matrix-size' ? '4096' : id === 'rank-range' ? '16' : '',
      textContent: '', innerHTML: '', style: { width: '' },
      attributes: new Map(), listeners: new Map(),
      addEventListener(event, callback) { this.listeners.set(event, callback); },
      setAttribute(name, value) { this.attributes.set(name, value); },
    });
    return elements.get(id)!;
  };
  runInNewContext(match[1], { document: { getElementById: get } });
  const change = (id: string, value: string, event = 'input') => {
    get(id).value = value;
    const callback = get(id).listeners.get(event);
    assert.ok(callback, `${id} responds to ${event}`);
    callback();
  };
  return { source, get, change };
}

test('temperature bars use the same softmax as the laboratory', () => {
  const ui = page();
  ui.change('temperature-range', '2');
  const actual = [...ui.get('temperature-bars').innerHTML.matchAll(/<output>([\d,]+)%<\/output>/gu)]
    .map((match) => Number(match[1].replace(',', '.')));
  const expected = softmax([2, 1, 0], 2).map((p) => Math.round(p * 1000) / 10);
  assert.deepEqual(actual, expected);
});

test('causal mask closes future input positions', () => {
  const ui = page();
  ui.change('position-range', '1');
  assert.match(ui.get('attention-rows').innerHTML, /чай.*−∞.*0,0%/u);
  const expected = attentionRow(1).probabilities;
  const shown = [...ui.get('attention-rows').innerHTML.matchAll(/<output>([\d,]+)%<\/output>/gu)]
    .map((match) => Number(match[1].replace(',', '.')));
  assert.deepEqual(shown, expected.map((p) => Math.round(p * 1000) / 10));
  ui.change('position-range', '2');
  assert.doesNotMatch(ui.get('attention-rows').innerHTML, /−∞/u);
});

test('LoRA count and percent respond to rank and matrix size', () => {
  const ui = page();
  ui.change('matrix-size', '1024', 'change');
  ui.change('rank-range', '32');
  assert.equal(ui.get('lora-count').textContent.replace(/\D/gu, ''), String(loraEntries(1024, 1024, 32)));
  assert.equal(ui.get('lora-percent').textContent, '6,25%');
  assert.match(ui.get('weight-track').attributes.get('aria-label') ?? '', /6,25 процента/u);
});
