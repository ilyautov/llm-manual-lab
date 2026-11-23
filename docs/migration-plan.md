# План миграции книги на markdown-стек

Цель: перевести книгу с `manual/source.docx` + Python на Markdown-стек сестринских
репозиториев (`chapters/*.md` + pandoc + подстановка чисел). Первый шаг сделан и воспроизводим:
скрипт `scripts/extract_docx_draft.py` механически выгружает DOCX в черновик `chapters/*.md`,
сохраняя порядок, формулы и подписи. Черновик не участвует в сборке: книга пока собирается
из DOCX, и это оговорено в шапке каждого файла черновика.

## Соответствие «раздел DOCX → файл черновика»

| Файл черновика | Раздел DOCX | Элементы | Абзацы | Таблицы | Формулы | Правки | Стр. PDF |
| --- | --- | --- | --- | --- | --- | --- | --- |
| chapters/00-front-matter.md | Вступительные материалы | 0–8 | 9 | 0 | 0 | 2 | — |
| chapters/00-front-matter.md | Содержание | 9–34 | 25 | 0 | 0 | 0 | — |
| chapters/01-chto-takoe-model.md | Что такое модель | 35–41 | 6 | 0 | 0 | 2 | 5 |
| chapters/02-iz-chego-sdelana-neiroset.md | Из чего сделана нейросеть | 42–49 | 7 | 0 | 1 | 2 | 7 |
| chapters/03-tokenizatsiya.md | Токенизация | 50–56 | 6 | 0 | 0 | 4 | 9 |
| chapters/04-embeddingi-i-vnutrennie-predstavleniya.md | Эмбеддинги и внутренние представления | 57–63 | 6 | 0 | 0 | 4 | 11 |
| chapters/05-chto-yazykovaya-model-predskazyvaet.md | Что языковая модель предсказывает | 64–75 | 11 | 0 | 2 | 3 | 13 |
| chapters/06-ustroistvo-transformera.md | Устройство трансформера | 76–85 | 9 | 0 | 1 | 2 | 15 |
| chapters/07-kak-proiskhodit-pretraining.md | Как происходит pretraining | 86–97 | 11 | 0 | 2 | 2 | 19 |
| chapters/08-dannye-i-obobschenie.md | Данные и обобщение | 98–105 | 7 | 0 | 0 | 1 | 25 |
| chapters/09-post-training-i-obuchenie-instruktsiyam.md | Post-training и обучение инструкциям | 106–114 | 8 | 0 | 0 | 3 | 27 |
| chapters/10-doobuchenie-lora-i-distillyatsiya.md | Дообучение, LoRA и дистилляция | 115–125 | 10 | 0 | 1 | 4 | 32 |
| chapters/11-rassuzhdenie-i-obuchenie-po-nagrade.md | Рассуждение и обучение по награде | 126–133 | 7 | 0 | 0 | 2 | 34 |
| chapters/12-inferens-i-vybor-tokenov.md | Инференс и выбор токенов | 134–141 | 7 | 0 | 0 | 4 | 37 |
| chapters/13-kontekst-i-kv-cache.md | Контекст и KV cache | 142–149 | 7 | 0 | 0 | 4 | 39 |
| chapters/14-pamyat-i-rag.md | Память и RAG | 150–161 | 10 | 1 | 0 | 5 | 42 |
| chapters/15-routing-vnutri-modeli-i-prilozheniya.md | Роутинг внутри модели и приложения | 162–171 | 9 | 0 | 1 | 3 | 45 |
| chapters/16-instrumenty-i-agentnyi-tsikl.md | Инструменты и агентный цикл | 172–183 | 11 | 0 | 0 | 3 | 48 |
| chapters/17-kak-agent-razbiraet-oshibku-v-kode.md | Как агент разбирает ошибку в коде | 184–193 | 8 | 1 | 0 | 4 | 51 |
| chapters/18-oshibki-i-granitsy-dostovernosti.md | Ошибки и границы достоверности | 194–201 | 7 | 0 | 0 | 3 | 53 |
| chapters/19-pamyat-kompyutera-i-stoimost-vychislenii.md | Память компьютера и стоимость вычислений | 202–211 | 9 | 0 | 1 | 2 | 54 |
| chapters/20-kak-proveryat-sistemu.md | Как проверять систему | 212–220 | 8 | 0 | 0 | 1 | 56 |
| chapters/21-karta-tekhnicheskikh-reshenii.md | Карта технических решений | 221–224 | 2 | 1 | 0 | 0 | 59 |
| chapters/22-voprosy-i-praktikum-dlya-proverki-ponimaniya.md | Вопросы и практикум для проверки понимания | 225–251 | 26 | 0 | 0 | 5 | 71 |
| chapters/23-slovar.md | Словарь | 252–254 | 1 | 1 | 0 | 0 | 75 |
| chapters/24-pervoistochniki.md | Первоисточники | 255–286 | 31 | 0 | 0 | 0 | 78 |

Всего: 26 файлов, 258 абзацев, 4 таблиц,
9 формул OMML, 65 точечных правок TEXT_OVERRIDES.
Страницы PDF берутся из текущей сборки (manual/out); «—» значит, заголовок на странице не найден
(раздел целиком во врезке сборки или страница сборки не строилась).

## Что переносится автоматически

- текст абзацев и заголовков в порядке документа; маркеры `<!-- e:N -->` сохраняют индекс
  элемента DOCX, общий с ключами TEXT_OVERRIDES, REFERENCE_TITLE_FIXES и FORMULA_GUIDES;
- текст с уже применёнными правками TEXT_OVERRIDES и REFERENCE_TITLE_FIXES (замена помечена);
- таблицы: chapters 14, 17, 21, 23 DOCX становятся pipe-таблицами;
- формулы: девять OMML-абзацев выгружены линейной записью в блоках ```text.

## Что требует ручной работы

1. Формулы: перевести линейную запись девяти OMML-формул в LaTeX/MathML для pandoc
   (соответствие индексов и текущий набор символов: manual/math_typesetting.py).
2. Схемы: векторные диаграммы живут не в DOCX, а в Python (DIAGRAMS в build_pdf.py,
   технические фигуры в technical_figures.py, педагогические в pedagogy_figures.py);
   перенести их в SVG в разметке глав, как в сестринских книгах.
3. Вставки сборки: INTRO (вступление), PRACTICUM (практикум), NEW_REFERENCES ([31]–[49]),
   словарные статьи и дополнения (open_topics_pages) существуют только в коде сборки,
   в DOCX их нет; при миграции они становятся обычными разделами markdown.
4. Глоссарий: GLOSSARY_CHAPTERS/GLOSSARY_EXTRA собираются кодом; при миграции проверять
   ссылки словаря на разделы (сейчас их 78, проверка в scripts/check_pdf.py).
5. Номера страниц в этом плане отражают текущую PDF-сборку; после миграции их заменит
   подстановка из build/numbers.json, как в книгах 2 и 3 серии.

## Проверка воспроизводимости

```bash
python scripts/extract_docx_draft.py   # повторная выгрузка
git diff --stat chapters/              # пусто: выгрузка детерминирована
```

Счётчики в `chapters/_draft-stats.json` сверяются с DOCX:
число абзацев в черновике равно числу абзацев тела документа, таблицы и формулы посчитаны
тем же обходом, что использует сборка (build_pdf.get_blocks).

