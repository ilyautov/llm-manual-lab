# AGENTS.md

Руководство для людей и ИИ-агентов, которые делают правки в этом репозитории.

## Что это за репозиторий

Первая книга серии «LLM на практике» и её лаборатория. Текст книги живёт в `manual/source.docx` с редакторскими правками в `manual/editorial_content.py`; PDF собирает `manual/build_manual.py` (Python, зависимости в `manual/requirements.txt`, шрифты в `manual/fonts/`). Лаборатория на TypeScript (Node 24) в `src/`, тесты в `tests/`.

## Команды

```bash
npm test                                   # тесты лаборатории, без сети
python manual/build_manual.py              # PDF книги (python + requirements.txt)
python scripts/check_pdf.py                # регрессионная проверка содержимого PDF
python scripts/package_release.py          # архив для релиза в dist/
```

## Правила правок

1. Текст книги редактируется в DOCX и `editorial_content.py`; правки по индексам элементов хрупки, после любой вставки пересобирайте PDF и гоняйте `check_pdf.py`.
2. Редакция книги берётся из `manual/publication.json`: обложка, метаданные и выходная страница читают её автоматически.
3. Числа лаборатории фиксируются тестами; меняя расчёт, меняйте тест и текст книги.
4. Лаборатория живёт без внешних npm-зависимостей и без сети в тестах.
5. Релизный процесс описан в RELEASE.md.
