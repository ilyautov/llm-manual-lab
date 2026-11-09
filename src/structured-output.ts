/** One illustrative way to constrain token choices before softmax. */
import { pathToFileURL } from 'node:url';
import { softmax } from './toy-model.ts';

export function constrainedSoftmax(logits: readonly number[], allowed: readonly boolean[]): number[] {
  if (logits.length === 0 || logits.length !== allowed.length ||
      !allowed.some(Boolean) || logits.some((x) => !Number.isFinite(x))) {
    throw new RangeError('Expected finite logits and at least one allowed candidate');
  }
  const permitted = logits.filter((_, i) => allowed[i]);
  const probabilities = softmax(permitted);
  let cursor = 0;
  return logits.map((_, i) => allowed[i] ? probabilities[cursor++] : 0);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  console.log(JSON.stringify({ logits: [2, 1, 0], ordinary: softmax([2, 1, 0]),
    allowed: [false, true, true], constrained: constrainedSoftmax([2, 1, 0], [false, true, true]) }, null, 2));
}
