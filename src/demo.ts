import { trainSentence, VOCAB } from './toy-model.ts';

const trace = trainSentence();
const round = (value: number) => Number(value.toFixed(4));
console.log('Учебная модель: таблица биграмм; это не трансформер.');
console.log(`Текст: ${trace.sentence}`);
console.log(`Токены: ${trace.tokens.join(' | ')}; ID: ${trace.ids.join(', ')}`);
console.log(`Контекст: ${trace.contextToken}; правильный следующий токен: ${trace.targetToken}`);
console.log(`Logits до: ${trace.logitsBefore.join(', ')}`);
console.log('Вероятности до:', Object.fromEntries(VOCAB.map((token, id) => [token, round(trace.probabilitiesBefore[id])])));
console.log(`Ошибка до: ${round(trace.lossBefore)}`);
console.log(`Градиент строки: ${trace.gradient.map(round).join(', ')}`);
console.log(`Logits после: ${trace.logitsAfter.map(round).join(', ')}`);
console.log('Вероятности после:', Object.fromEntries(VOCAB.map((token, id) => [token, round(trace.probabilitiesAfter[id])])));
console.log(`Ошибка после: ${round(trace.lossAfter)}`);
console.log('Один шаг повысил вероятность цели; другие строки параметров не менялись.');
