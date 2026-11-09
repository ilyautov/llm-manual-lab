/** Deterministic calculations for the manual's evaluation atlas. */
import { pathToFileURL } from 'node:url';

export interface Interval { low: number; high: number }
export interface RetrievalScore { recallAtK: number; mrrAtK: number }

export function wilsonInterval(successes: number, trials: number, z = 1.96): Interval {
  if (!Number.isInteger(trials) || trials <= 0 || !Number.isInteger(successes) ||
      successes < 0 || successes > trials || !Number.isFinite(z) || z <= 0) {
    throw new RangeError('Expected 0 <= successes <= positive trials and z > 0');
  }
  const p = successes / trials;
  const divisor = 1 + z * z / trials;
  const center = (p + z * z / (2 * trials)) / divisor;
  const half = z * Math.sqrt(p * (1 - p) / trials + z * z / (4 * trials * trials)) / divisor;
  return { low: Math.max(0, center - half), high: Math.min(1, center + half) };
}

/** One annotated relevant fragment per query; null means absent from candidates. */
export function retrievalScore(ranks: readonly (number | null)[], k: number): RetrievalScore {
  if (ranks.length === 0 || !Number.isInteger(k) || k <= 0 ||
      ranks.some((rank) => rank !== null && (!Number.isInteger(rank) || rank <= 0))) {
    throw new RangeError('Expected nonempty ranks and positive integer k');
  }
  const visible = ranks.map((rank) => rank !== null && rank <= k ? rank : null);
  return {
    recallAtK: visible.filter((rank) => rank !== null).length / ranks.length,
    mrrAtK: visible.reduce((sum: number, rank) => sum + (rank === null ? 0 : 1 / rank), 0) / ranks.length,
  };
}

export function evaluationDemo() {
  return {
    diagnosticTwelve: wilsonInterval(10, 12),
    sampleHundred: wilsonInterval(80, 100),
    ordinarySearch: retrievalScore([1, 2, null], 3),
    hybridAndRerank: retrievalScore([1, 1, 2], 3),
    independentThreeRuns: {
      atLeastOne: Number((1 - (1 - .8) ** 3).toFixed(3)),
      allThree: Number((.8 ** 3).toFixed(3)),
    },
  };
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  console.log(JSON.stringify(evaluationDemo(), null, 2));
}
