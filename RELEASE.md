# Релизный процесс

Релиз книги совпадает с редакцией из `manual/publication.json`. Шаги:

1. Внести правки, обновить `CHANGELOG.md` (дата, суть, благодарности).
2. Поднять `edition` в `manual/publication.json` (формат `ГГГГ.ММ.ДД`). Обложка, метаданные PDF и выходная страница берут редакцию отсюда.
3. Собрать PDF: `python manual/build_manual.py` из корня (нужны Python 3 и `pip install -r manual/requirements.txt`; шрифты уже в `manual/fonts/`).
4. Прогнать проверку: `python scripts/check_pdf.py` (сверяет содержимое PDF с правилами книги).
5. Собрать архив: `python scripts/package_release.py` (печатает путь и число файлов).
6. Создать release на GitHub: тег `vN.M`, название «vN.M · редакция ГГГГ.ММ.ДД», вложения: PDF из `manual/out/` и zip из `dist/`.
7. Убедиться, что ссылка в README на `../../releases/latest` ведёт на новый релиз.

Сокращённый чек-лист: CHANGELOG → publication.json → build → check_pdf → package → release.
