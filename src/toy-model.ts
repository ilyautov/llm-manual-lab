/**
 * A complete training step for a three-token bigram language model.
 * This is deliberately NOT a transformer or an LLM. A row of trainable logits
 * is selected by the previous token; the row is updated by cross-entropy.
 */
export const VOCAB = ['я', 'люблю', 'чай'] as const;
export type Token = (typeof VOCAB)[number];
export const INITIAL_LOGITS: readonly (readonly number[])[] = [
  [0, 0, 0],
  [2, 1, 0],
  [0, 0, 0],
];

export function tokenize(sentence: string): number[] {
  return sentence.trim().toLowerCase().split(/\s+/u).map((word) => {
    const id = VOCAB.indexOf(word as Token);
    if (id < 0) throw new Error(`Unknown toy-vocabulary token: ${word}`);
    return id;
  });
}

export function softmax(logits: readonly number[], temperature = 1): number[] {
  if (!Number.isFinite(temperature) || temperature <= 0) {
    throw new RangeError('Temperature must be a positive finite number');
  }
  if (logits.length === 0 || logits.some((value) => !Number.isFinite(value))) {
    throw new RangeError('Logits must be a nonempty list of finite numbers');
  }
  const scaled = logits.map((value) => value / temperature);
  const maximum = Math.max(...scaled);
  const weights = scaled.map((value) => Math.exp(value - maximum));
  const total = weights.reduce((sum, value) => sum + value, 0);
  return weights.map((value) => value / total);
}

export function crossEntropy(probabilities: readonly number[], targetId: number): number {
  if (!Number.isInteger(targetId) || targetId < 0 || targetId >= probabilities.length) {
    throw new RangeError('Target ID is outside the vocabulary');
  }
  return -Math.log(probabilities[targetId]);
}

export interface TrainingTrace {
  sentence: string;
  tokens: string[];
  ids: number[];
  contextToken: string;
  contextId: number;
  targetToken: string;
  targetId: number;
  learningRate: number;
  logitsBefore: number[];
  probabilitiesBefore: number[];
  lossBefore: number;
  gradient: number[];
  logitsAfter: number[];
  probabilitiesAfter: number[];
  lossAfter: number;
}

export function trainSentence(sentence = 'я люблю чай', learningRate = 1): TrainingTrace {
  if (!Number.isFinite(learningRate) || learningRate <= 0) {
    throw new RangeError('Learning rate must be positive and finite');
  }
  const ids = tokenize(sentence);
  if (ids.length < 2) throw new Error('The sentence needs at least two tokens');
  const contextId = ids[ids.length - 2];
  const targetId = ids[ids.length - 1];
  const logitsBefore = [...INITIAL_LOGITS[contextId]];
  const probabilitiesBefore = softmax(logitsBefore);
  const gradient = probabilitiesBefore.map((p, id) => p - Number(id === targetId));
  const logitsAfter = logitsBefore.map((z, id) => z - learningRate * gradient[id]);
  const probabilitiesAfter = softmax(logitsAfter);
  return {
    sentence,
    tokens: ids.map((id) => VOCAB[id]),
    ids,
    contextToken: VOCAB[contextId],
    contextId,
    targetToken: VOCAB[targetId],
    targetId,
    learningRate,
    logitsBefore,
    probabilitiesBefore,
    lossBefore: crossEntropy(probabilitiesBefore, targetId),
    gradient,
    logitsAfter,
    probabilitiesAfter,
    lossAfter: crossEntropy(probabilitiesAfter, targetId),
  };
}
