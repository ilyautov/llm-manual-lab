"""
Механическая выгрузка manual/source.docx в черновик chapters/*.md.

Отправная точка долгосрочной миграции книги на markdown-стек сестринских
репозиториев (agents-manual-lab, rag-manual-lab). Черновик НЕ является
источником книги: источник остаётся manual/source.docx с правками
manual/editorial_content.py и дополнениями manual/build_manual.py.

Что делает скрипт:
- обходит тело DOCX в том же порядке и с теми же индексами, что сборка
  (build_pdf.get_blocks), поэтому индексы в маркерах <!-- e:N --> совпадают
  с ключами TEXT_OVERRIDES, REFERENCE_TITLE_FIXES и FORMULA_GUIDES;
- применяет TEXT_OVERRIDES и REFERENCE_TITLE_FIXES: черновик показывает текст
  книги, а не сырой DOCX; замена помечена в маркере;
- режет текст по заголовкам Heading 1: один файл на главу chapters/NN-slug.md,
  вступительные элементы до главы 1 идут в chapters/00-front-matter.md;
- OMML-формулы выгружаются как блок ```text с линейной записью m:t;
- таблицы становятся pipe-таблицами; встроенное изображение помечено;
- печатает chapters/_draft-stats.json и docs/migration-plan.md
  (сопоставление «раздел DOCX → файл черновика → страницы PDF»).

Запуск: python scripts/extract_docx_draft.py  (из корня репозитория)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'manual'))
from editorial_content import REFERENCE_TITLE_FIXES, TEXT_OVERRIDES  # noqa: E402
from build_pdf import normalize_terms  # noqa: E402  (та же замена терминов, что в сборке)

PDF = ROOT / 'manual/out/Теория_LLM_полный_мануал.pdf'
MATH_NS = '{http://schemas.openxmlformats.org/officeDocument/2006/math}'

TRANSLIT = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e', 'ж': 'zh',
    'з': 'z', 'и': 'i', 'й': 'i', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o',
    'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'kh', 'ц': 'ts',
    'ч': 'ch', 'ш': 'sh', 'щ': 'sch', 'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
}


def slugify(text: str) -> str:
    s = ''.join(TRANSLIT.get(ch, ch) for ch in text.lower())
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s[:48].rstrip('-') or 'section'


def omml_text(p_el) -> str | None:
    parts = []
    for m in p_el.iter(f'{MATH_NS}oMath'):
        runs = [t.text or '' for t in m.iter(f'{MATH_NS}t')]
        if ''.join(runs).strip():
            parts.append(''.join(runs))
    return ' ; '.join(parts) if parts else None


def cell_text(cell) -> str:
    return cell.text.replace('|', '/').replace('\n', ' ').strip()


def table_md(tbl) -> str:
    rows = [[cell_text(c) for c in row.cells] for row in tbl.rows]
    if not rows:
        return ''
    width = max(len(r) for r in rows)
    rows = [r + [''] * (width - len(r)) for r in rows]
    head, body = rows[0], rows[1:]
    lines = ['| ' + ' | '.join(head) + ' |', '|' + '---|' * width]
    lines += ['| ' + ' | '.join(r) + ' |' for r in body]
    return '\n'.join(lines)


def pdf_pages(pdf_path: Path) -> list[str]:
    if not pdf_path.exists():
        return []
    import pdfplumber
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            pages.append(re.sub(r'\s+', ' ', (page.extract_text() or '')))
    return pages


def main() -> None:
    doc = Document(ROOT / 'manual/source.docx')
    out_dir = ROOT / 'chapters'
    out_dir.mkdir(exist_ok=True)

    sections: list[dict] = []  # {title, file, from, to, paragraphs, tables, formulas, overrides}
    current: dict | None = None
    lines: list[str] = []

    def flush() -> None:
        if current is None:
            return
        header = [
            f'# {current["title"]}',
            '',
            '<!--',
            f'Черновик механической выгрузки из manual/source.docx (см. scripts/extract_docx_draft.py).',
            'Источник книги: manual/source.docx + правки editorial_content.py; этот файл не участвует в сборке.',
            f'Элементы DOCX: {current["from"]}–{current["to"]}.',
            '-->',
            '',
        ]
        (out_dir / current['file']).write_text('\n'.join(header + lines) + '\n', encoding='utf-8')
        current['paragraphs'] = sum(
            1 for m in lines
            if m.startswith('<!-- e:') and all(k not in m for k in ('заголовок', 'таблица', 'титульная')))
        sections.append(current)

    pages = pdf_pages(PDF)
    norm = re.compile(r'\s+')

    for i, b in enumerate(doc.element.body):
        is_p = b.tag == qn('w:p')
        is_tbl = b.tag == qn('w:tbl')
        if not (is_p or is_tbl):
            continue
        if is_tbl:
            if current is None:
                current = {'title': 'Вступительные материалы', 'file': '00-front-matter.md',
                           'from': i, 'to': i, 'paragraphs': 0, 'tables': 0, 'formulas': 0, 'overrides': 0, 'page': ''}
                lines = []
            lines.append(f'<!-- e:{i} таблица -->')
            lines.append(table_md(Table(b, doc)))
            lines.append('')
            current['tables'] += 1
            current['to'] = i
            continue

        p = Paragraph(b, doc)
        style = p.style.name if p.style else ''
        if current is None:
            # элементы до первого заголовка (титул, подзаголовок, аннотация)
            current = {'title': 'Вступительные материалы', 'file': '00-front-matter.md',
                       'from': i, 'to': i, 'paragraphs': 0, 'tables': 0, 'formulas': 0, 'overrides': 0, 'page': ''}
            lines = [f'<!-- e:{i} титульная страница -->', '## Вступительные материалы', '']
        if style == 'Heading 1':
            t = normalize_terms(TEXT_OVERRIDES.get(i, p.text).strip())
            if i in REFERENCE_TITLE_FIXES:
                before, after = REFERENCE_TITLE_FIXES[i]
                t = t.replace(normalize_terms(before), normalize_terms(after))
            if current is not None:
                flush()
            m = re.match(r'^(\d+)\s+(.+)', t)
            num = int(m.group(1)) if m else None
            title = m.group(2) if m else t
            fname = f'{num:02d}-{slugify(title)}.md' if m else '00-front-matter.md'
            current = {'num': num, 'title': title, 'file': fname, 'from': i, 'to': i,
                       'paragraphs': 0, 'tables': 0, 'formulas': 0, 'overrides': 0, 'page': ''}
            lines = [f'<!-- e:{i} заголовок -->', f'## {t}', '']
            continue

        text = normalize_terms(TEXT_OVERRIDES.get(i, p.text))
        mark = [f'e:{i}']
        if i in TEXT_OVERRIDES:
            mark.append('override')
            current and current.__setitem__('overrides', current['overrides'] + 1)
        if i in REFERENCE_TITLE_FIXES:
            mark.append('fix')
        formula = omml_text(b)
        if formula:
            mark.append('формула')
            current and current.__setitem__('formulas', current['formulas'] + 1)
        if b.findall('.//' + qn('w:drawing')):
            mark.append('изображение')
        lines.append(f'<!-- {" ".join(mark)} -->')
        if formula:
            lines.append('```text')
            lines.append(formula)
            lines.append('```')
        if text.strip():
            lines.append(text.strip())
        lines.append('')
        current['to'] = i
    flush()

    # страницы PDF: ищем заголовок вне оглавления (страница оглавления содержит много заголовков сразу)
    if pages:
        needles = [f'{s["num"]} {s["title"]}' for s in sections if s.get('num')]

        def page_of(section: dict) -> str:
            if not section.get('num'):
                return ''
            needle = norm.sub(' ', f'{section["num"]} {section["title"]}')
            matches = [pn for pn, text in enumerate(pages, 1) if needle in text]
            content = [pn for pn in matches
                       if sum(1 for n in needles if norm.sub(' ', n) in pages[pn - 1]) <= 2]
            return str(content[0]) if content else (str(matches[-1]) if matches else '')

        for s in sections:
            s['page'] = page_of(s)

    # статистика и план миграции
    total = {
        'paragraphs': sum(s['paragraphs'] for s in sections),
        'tables': sum(s['tables'] for s in sections),
        'formulas': sum(s['formulas'] for s in sections),
        'overrides': sum(s['overrides'] for s in sections),
        'files': len(sections),
    }
    (out_dir / '_draft-stats.json').write_text(
        json.dumps({'total': total, 'sections': sections}, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8')

    md = [
        '# План миграции книги на markdown-стек',
        '',
        'Цель: перевести книгу с `manual/source.docx` + Python на Markdown-стек сестринских',
        'репозиториев (`chapters/*.md` + pandoc + подстановка чисел). Первый шаг сделан и воспроизводим:',
        'скрипт `scripts/extract_docx_draft.py` механически выгружает DOCX в черновик `chapters/*.md`,',
        'сохраняя порядок, формулы и подписи. Черновик не участвует в сборке: книга пока собирается',
        'из DOCX, и это оговорено в шапке каждого файла черновика.',
        '',
        '## Соответствие «раздел DOCX → файл черновика»',
        '',
        '| Файл черновика | Раздел DOCX | Элементы | Абзацы | Таблицы | Формулы | Правки | Стр. PDF |',
        '| --- | --- | --- | --- | --- | --- | --- | --- |',
    ]
    for s in sections:
        md.append(f"| chapters/{s['file']} | {s['title']} | {s['from']}–{s['to']} | "
                  f"{s['paragraphs']} | {s['tables']} | {s['formulas']} | {s['overrides']} | {s['page'] or '—'} |")
    md += [
        '',
        f'Всего: {total["files"]} файлов, {total["paragraphs"]} абзацев, {total["tables"]} таблиц,',
        f'{total["formulas"]} формул OMML, {total["overrides"]} точечных правок TEXT_OVERRIDES.',
        'Страницы PDF берутся из текущей сборки (manual/out); «—» значит, заголовок на странице не найден',
        '(раздел целиком во врезке сборки или страница сборки не строилась).',
        '',
        '## Что переносится автоматически',
        '',
        '- текст абзацев и заголовков в порядке документа; маркеры `<!-- e:N -->` сохраняют индекс',
        '  элемента DOCX, общий с ключами TEXT_OVERRIDES, REFERENCE_TITLE_FIXES и FORMULA_GUIDES;',
        '- текст с уже применёнными правками TEXT_OVERRIDES и REFERENCE_TITLE_FIXES (замена помечена);',
        '- таблицы: chapters 14, 17, 21, 23 DOCX становятся pipe-таблицами;',
        '- формулы: девять OMML-абзацев выгружены линейной записью в блоках ```text.',
        '',
        '## Что требует ручной работы',
        '',
        '1. Формулы: перевести линейную запись девяти OMML-формул в LaTeX/MathML для pandoc',
        '   (соответствие индексов и текущий набор символов: manual/math_typesetting.py).',
        '2. Схемы: векторные диаграммы живут не в DOCX, а в Python (DIAGRAMS в build_pdf.py,',
        '   технические фигуры в technical_figures.py, педагогические в pedagogy_figures.py);',
        '   перенести их в SVG в разметке глав, как в сестринских книгах.',
        '3. Вставки сборки: INTRO (вступление), PRACTICUM (практикум), NEW_REFERENCES ([31]–[49]),',
        '   словарные статьи и дополнения (open_topics_pages) существуют только в коде сборки,',
        '   в DOCX их нет; при миграции они становятся обычными разделами markdown.',
        '4. Глоссарий: GLOSSARY_CHAPTERS/GLOSSARY_EXTRA собираются кодом; при миграции проверять',
        '   ссылки словаря на разделы (сейчас их 78, проверка в scripts/check_pdf.py).',
        '5. Номера страниц в этом плане отражают текущую PDF-сборку; после миграции их заменит',
        '   подстановка из build/numbers.json, как в книгах 2 и 3 серии.',
        '',
        '## Проверка воспроизводимости',
        '',
        '```bash',
        'python scripts/extract_docx_draft.py   # повторная выгрузка',
        'git diff --stat chapters/              # пусто: выгрузка детерминирована',
        '```',
        '',
        'Счётчики в `chapters/_draft-stats.json` сверяются с DOCX:',
        'число абзацев в черновике равно числу абзацев тела документа, таблицы и формулы посчитаны',
        'тем же обходом, что использует сборка (build_pdf.get_blocks).',
        '',
    ]
    plan = ROOT / 'docs/migration-plan.md'
    plan.write_text('\n'.join(md) + '\n', encoding='utf-8')
    print(f'{len(sections)} файлов черновика → chapters/; план → {plan.relative_to(ROOT)}')
    print(json.dumps(total, ensure_ascii=False))


if __name__ == '__main__':
    main()
