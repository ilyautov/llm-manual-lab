/** Deterministic teaching simulator for the retrieval/context boundary. No LLM is called. */
import { pathToFileURL } from 'node:url';
export interface Fragment { id: string; version: string; text: string }
export interface RagTrace {
  question: string;
  indexVersion: string;
  retrievedIds: string[];
  context: string;
  answer: string;
}

const TARIFF_V2: Fragment = {
  id: 'tariff-a-v2:price',
  version: 'v2',
  text: 'Тариф А стоит 300 ₽ с 1 марта 2025 года.',
};

export function traceTariff(indexContainsV2: boolean): RagTrace {
  const question = 'Сколько стоит тариф А?';
  const fragments = indexContainsV2 ? [TARIFF_V2] : [];
  const retrieved = fragments.filter((f) => f.text.toLowerCase().includes('тариф а'));
  const context = retrieved.map((f) => `[${f.id}] ${f.text}`).join('\n');
  const price = context.match(/(\d+)\s*₽/u)?.[1];
  return {
    question,
    indexVersion: indexContainsV2 ? 'v2' : 'empty',
    retrievedIds: retrieved.map((f) => f.id),
    context,
    answer: price ? `Тариф А стоит ${price} ₽ (по ${retrieved[0].id}).` :
      'Цена не подтверждена: подходящий фрагмент не найден.',
  };
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  console.log(JSON.stringify({ withDocument: traceTariff(true), withoutDocument: traceTariff(false) }, null, 2));
}
