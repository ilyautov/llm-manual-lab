/** A real local LLM, a retrieved document, and one read-only application tool. */
import { pathToFileURL } from 'node:url';
import { paidOrders } from './orders.ts';
import { traceTariff } from './rag.ts';

export type ChatMessage = {
  role: 'system' | 'user' | 'assistant' | 'tool';
  content: string;
  tool_name?: string;
  tool_calls?: ToolCall[];
};
export type ToolCall = {
  type: 'function';
  function: { name: string; arguments: unknown; index?: number };
};
export type ChatRequest = {
  model: string;
  messages: ChatMessage[];
  stream: false;
  options: { temperature: number; num_predict: number };
  tools?: unknown[];
};
export type ChatResponse = {
  model?: string;
  message?: { role?: string; content?: string; tool_calls?: ToolCall[] };
  prompt_eval_count?: number;
  eval_count?: number;
};
export type ChatTransport = (request: ChatRequest) => Promise<ChatResponse>;

const DEFAULT_URL = 'http://127.0.0.1:11434';
const DEFAULT_MODEL = 'qwen2.5:3b';
const QUESTION = 'Сколько оплаченных заказов было 1 марта 2025 года?';

export function localOllamaTransport(url = process.env.OLLAMA_URL ?? DEFAULT_URL): ChatTransport {
  const endpoint = new URL('/api/chat', url);
  if (endpoint.protocol !== 'http:' || !['127.0.0.1', 'localhost', '::1'].includes(endpoint.hostname)) {
    throw new Error('Лаборатория обращается только к локальному Ollama по HTTP.');
  }
  return async (request) => {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(request),
      signal: AbortSignal.timeout(120_000),
    });
    if (!response.ok) {
      const detail = (await response.text()).slice(0, 300);
      throw new Error(`Ollama HTTP ${response.status}: ${detail}`);
    }
    const result = await response.json() as ChatResponse;
    if (!result.message || typeof result.message.content !== 'string') {
      throw new Error('Ollama вернул ответ без сообщения.');
    }
    return result;
  };
}

function request(model: string, messages: ChatMessage[], tools?: unknown[]): ChatRequest {
  return { model, messages, stream: false, options: { temperature: 0, num_predict: 200 },
    ...(tools ? { tools } : {}) };
}

export async function tariffWithRealModel(chat: ChatTransport, model = DEFAULT_MODEL,
  withDocument = true) {
  const retrieval = traceTariff(withDocument);
  const messages: ChatMessage[] = [
    { role: 'system', content: 'Ответь на вопрос только по переданному фрагменту. Если фрагмента нет, честно скажи, что цена не подтверждена. Укажи ID источника, если он есть.' },
    { role: 'user', content: `Вопрос: ${retrieval.question}\nНайденные фрагменты:\n${retrieval.context || '(ничего не найдено)'}` },
  ];
  const response = await chat(request(model, messages));
  const answer = response.message?.content ?? '';
  const prices = [...answer.matchAll(/\b(\d+)\s*₽/gu)].map((match) => Number(match[1]));
  return {
    retrievedIds: retrieval.retrievedIds,
    modelAnswer: answer,
    sourcePresent: withDocument,
    priceMatchesSource: withDocument ? prices.length === 1 && prices[0] === 300 : null,
    citesRetrievedId: withDocument ? answer.includes('tariff-a-v2:price') : null,
    unsupportedPrice: !withDocument && prices.length > 0,
    inputTokens: response.prompt_eval_count ?? null,
    outputTokens: response.eval_count ?? null,
  };
}

export function executePaidOrdersCall(call: ToolCall, role: 'reader' | 'guest' = 'reader',
  expectedDate = '2025-03-01') {
  const fn = call?.function;
  const args = fn?.arguments;
  if (fn?.name !== 'paid_orders' || !args || typeof args !== 'object' || Array.isArray(args)) {
    return { allowed: false, reason: 'unknown tool or malformed arguments', count: null };
  }
  const { date, status } = args as Record<string, unknown>;
  if (typeof date !== 'string' || status !== 'paid' || Object.keys(args).some((x) => !['date', 'status'].includes(x))) {
    return { allowed: false, reason: 'invalid paid_orders arguments', count: null };
  }
  if (date !== expectedDate) {
    return { allowed: false, reason: 'date does not match the user question', count: null };
  }
  const result = paidOrders(role, date);
  return { allowed: result.count !== null, reason: result.events.at(-1) ?? '',
    date, count: result.count, events: result.events };
}

const PAID_ORDERS_TOOL = {
  type: 'function',
  function: {
    name: 'paid_orders',
    description: 'Count paid orders on one date in the application database. Call before stating a count.',
    parameters: {
      type: 'object', required: ['date', 'status'], additionalProperties: false,
      properties: {
        date: { type: 'string', description: 'Date YYYY-MM-DD' },
        status: { type: 'string', enum: ['paid'] },
      },
    },
  },
};

export async function ordersWithRealModel(chat: ChatTransport, model = DEFAULT_MODEL,
  role: 'reader' | 'guest' = 'reader') {
  const messages: ChatMessage[] = [
    { role: 'system', content: 'Для числа заказов вызови paid_orders. Не угадывай число. Если инструмент отклонён, скажи, что число не подтверждено.' },
    { role: 'user', content: QUESTION },
  ];
  const first = await chat(request(model, messages, [PAID_ORDERS_TOOL]));
  const calls = first.message?.tool_calls ?? [];
  if (calls.length !== 1) {
    return { proposedCalls: calls.length, executed: false, reason: 'Ожидался ровно один tool_call.',
      firstAnswer: first.message?.content ?? '' };
  }
  const decision = executePaidOrdersCall(calls[0], role);
  if (!decision.allowed) {
    return { proposedCalls: 1, executed: false, decision,
      firstAnswer: first.message?.content ?? '' };
  }
  messages.push({ role: 'assistant', content: first.message?.content ?? '', tool_calls: calls });
  messages.push({ role: 'tool', tool_name: 'paid_orders',
    content: JSON.stringify({ count: decision.count, date: decision.date, status: 'paid' }) });
  const final = await chat(request(model, messages));
  const answer = final.message?.content ?? '';
  return { proposedCalls: 1, executed: true, decision, finalAnswer: answer,
    answerMatchesResult: new RegExp(`\\b${decision.count}\\b`, 'u').test(answer),
    inputTokens: (first.prompt_eval_count ?? 0) + (final.prompt_eval_count ?? 0),
    outputTokens: (first.eval_count ?? 0) + (final.eval_count ?? 0) };
}

export async function runLiveLab(chat = localOllamaTransport(), model = process.env.OLLAMA_MODEL ?? DEFAULT_MODEL) {
  return { model,
    tariffWithDocument: await tariffWithRealModel(chat, model, true),
    tariffWithoutDocument: await tariffWithRealModel(chat, model, false),
    orders: await ordersWithRealModel(chat, model) };
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  runLiveLab().then((result) => console.log(JSON.stringify(result, null, 2)))
    .catch((error) => { console.error(error.message); process.exitCode = 1; });
}
