/**
 * Единственное место разбора сумм из ответа модели. live-lab проверяет конфликт цен,
 * live-evaluate берёт первую и отмечает конфликт; оба читают один и тот же список.
 */

/** Все суммы в рублях из текста: «Цена 300 ₽» даёт [300], «1 200 ₽» даёт [1200]. */
export function extractPrices(text: string): number[] {
  return [...text.matchAll(/(?:^|\D)(\d[\d\s\u00a0]*?)\s*₽/gu)]
    .map((match) => Number(match[1].replace(/[\s\u00a0]/gu, '')))
    .filter((n) => Number.isFinite(n));
}

/** Первая сумма или null, когда цены нет. */
export function firstPrice(text: string): number | null {
  return extractPrices(text)[0] ?? null;
}
