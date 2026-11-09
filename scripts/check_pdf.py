"""Check editorial regressions in the rendered manual, not just its source."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pdfplumber
from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'manual'))
from editorial_content import GLOSSARY_CHAPTERS  # noqa: E402


DEFAULT_PDF = Path(__file__).resolve().parents[1] / 'manual/out/Теория_LLM_полный_мануал.pdf'
PDF = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PDF
PUBLICATION = json.loads((Path(__file__).resolve().parents[1] /
                          'manual/publication.json').read_text())


def page_containing(pages: list[str], phrase: str) -> int:
    # The contents also lists section titles on page 3.
    needle = ' '.join(phrase.split())
    matches = [n for n, value in enumerate(pages, 1)
               if n > 4 and needle in ' '.join(value.split())]
    if len(matches) != 1:
        raise AssertionError((phrase, matches))
    return matches[0]


with pdfplumber.open(PDF) as document:
    pages = [page.extract_text() or '' for page in document.pages]
    all_text = '\n'.join(pages)
    for fragment in ('агентни', 'агентние', 'агентних', 'Агентский цикл'):
        assert fragment.casefold() not in all_text.casefold(), fragment
    assert '16 Инструменты и агентный цикл' in all_text
    assert 'Четыре задачи с числами' in all_text
    assert 'Задачи на счёт: ход решения' in all_text
    assert 'Исходный embedding' not in all_text
    assert '\x00' not in all_text, 'A font dropped a character in the rendered PDF'
    assert all_text.count('РАЗБОР ФОРМУЛЫ') == 9
    flat = lambda n: ' '.join(pages[n - 1].split())
    assert 'Матрицы проекций W_Q, W_K и W_V' in flat(18)
    assert '[1]' not in flat(18), 'The attention example is not sourced from [1]'
    assert '[8]' not in flat(26), 'Datasheets [8] does not support a sample threshold'
    assert 'Top-p оставляет наименьший набор токенов' in flat(37)
    assert 'Prefill обрабатывает вход; decode выдаёт токены' in flat(17)
    assert 'RLVR означает обучение с проверяемой наградой' in flat(27)
    assert 'RLVR означает' not in flat(28)
    assert 'Reinforcement learning with verifiable rewards:' not in flat(28)
    assert 'На числах: Учебный случай' not in all_text
    assert 'в сумме дают 1.' in flat(21)
    assert 'сформулируйте, что проверка показала' in flat(4)
    assert 'Если в системе есть router, он выбирает исполнителя.' in flat(52)
    assert 'фиксировать трассу:' in flat(56)
    assert 'trace_id' in flat(60)
    assert 'Двунаправленные представления' in all_text
    assert 'Двухсторонние представления' not in all_text
    assert 'KV cache хранит ключи K и значения V' in flat(40)
    assert 'Запустить Ollama; затем ollama pull' in flat(62)
    assert 'одно черновое продолжение длиной K' in flat(64)
    assert 'трансграничная передача' in flat(66)
    assert 'база заморожена, обучаются параметры адаптера' in flat(
        page_containing(pages, 'ПРИЛОЖЕНИЕ / ОТВЕТЫ'))
    for stale in ('Матрицы Q, K и V здесь единичные',
                  'несколько продолжений', 'PagedAttention исследует',
                  'модель тупая', 'уверенной чепухи', 'не угадать число',
                  'постоянную цифру'):
        assert stale not in all_text, stale
    additions = [
        'Что меняется, когда вход — изображение',
        'Почему быстрее — не всегда дешевле',
        'Что показывает исследование внутренних связей',
        'Данные, веса и условия использования',
        'Агент в продакшене',
        'Сравнение версий и доверие к оценщику',
    ]
    addition_pages = [page_containing(pages, title) for title in additions]
    assert addition_pages == list(range(addition_pages[0], addition_pages[0] + len(additions)))
    assert all('ДОПОЛНЕНИЕ /' in pages[page - 1] for page in addition_pages)
    assert page_containing(pages, '21 Карта технических решений') < addition_pages[0]
    assert addition_pages[-1] < page_containing(pages, '22 Вопросы и практикум')
    for number, url in {
        37: '2304.08485', 38: '2302.01318', 39: '2407.02646',
        40: 'consultant.ru/document/cons_doc_LAW_61801',
        41: 'repositories-licenses', 42: '2405.15793',
        43: 'building-effective-agents', 44: 'BF02295996',
        45: '001316446002000104', 46: '1176344552', 47: '2310.18018',
    }.items():
        assert re.search(rf'\[{number}\][^\[]*{re.escape(url)}', all_text, re.S), number
    quick_page = page_containing(pages, 'Откуда взялся ответ и что проверять')
    assert page_containing(pages, 'ПРИЛОЖЕНИЕ / ОТВЕТЫ') < quick_page
    assert quick_page == len(pages) - bool(PUBLICATION['author'].strip())
    assert 'Пять следов одного ответа' in pages[quick_page - 1]
    assert 'Симптом → первая проверка → механизм' in pages[quick_page - 1]
    if PUBLICATION['author'].strip():
        assert document.metadata['Author'] == PUBLICATION['author'].strip()
        assert page_containing(pages, 'Об издании') == len(pages)
        assert PUBLICATION['edition'] in pages[-1]
        for field in ('error_contact', 'license'):
            if PUBLICATION[field].strip():
                assert PUBLICATION[field].strip() in pages[-1], field

    # These anchors were chosen from the actual explanatory passage, not
    # merely the first page of the containing chapter.
    targets = {
        'Backpropagation': 'После прямого прохода backpropagation',
        'BF16': 'QLoRA обучает адаптеры',
        'BPE': 'Одно слияние BPE руками',
        'Causal mask': 'будущее «чай» не участвует',
        'Chunking': 'Chunking должен сохранять',
        'Confidence interval': 'Сколько ошибок скрывает доля успеха',
        'Constrained decoding': 'runtime оставляет только',
        'Context window': 'Контекстное окно — поддерживаемый лимит',
        'Cross-entropy': 'Для cross-entropy градиент',
        'Distillation': 'Дистилляция (distillation) переносит',
        'DPO': 'DPO — другой способ',
        'FFN': 'Далее полносвязная сеть FFN',
        'FlashAttention': 'FlashAttention уменьшает перемещения',
        'Gradient': 'После прямого прохода backpropagation',
        'Idempotency': 'Идемпотентность означает',
        'In-context learning': 'In-context learning означает',
        'JSON': 'В настоящем JSON',
        'KV cache': 'KV cache хранит ключи K и значения V',
        'MoE': 'В Mixture of Experts, MoE',
        'MRR@k': 'Нашёл ли поиск нужный фрагмент',
        'NF4': 'QLoRA обучает адаптеры',
        'Precision / recall': 'Для классификации полезны precision и recall',
        'Prefix caching': 'Prefix caching повторно использует',
        'Prompt': 'Prompt как проверяемая версия решения',
        'Prompt injection': 'Инструкция внутри найденного документа',
        'QLoRA': 'QLoRA обучает адаптеры',
        'Regression set': 'Регрессионный набор храните',
        'RLHF': 'RLHF означает',
        'RLVR': 'На схеме ниже RLVR означает',
        'Recall@k': 'Нашёл ли поиск нужный фрагмент',
        'Reranking': 'Нашёл ли поиск нужный фрагмент',
        'Reward model': 'В InstructGPT после демонстраций',
        'RoPE': 'поворачивает компоненты query',
        'Router': 'Router вычисляет',
        'Scaling laws': 'Scaling laws описывают',
        'Softmax': 'РАЗБОР ФОРМУЛЫ / SOFTMAX',
        'SQL': 'CREATE TABLE orders',
        'Teacher forcing': 'При teacher forcing модель',
        'Batching': 'Batching объединяет работу разных запросов',
        'Speculative decoding': 'При speculative decoding малая draft-модель',
        'Визуальный энкодер': 'Типичная схема для вопроса по изображению',
        'Интерпретируемость': 'От наблюдения к причинной проверке',
        'Мультимодальность': 'Что меняется, когда вход — изображение',
    }
    target_phrases = {term.casefold(): phrase for term, phrase in targets.items()}
    glossary_start = page_containing(pages, '23 Словарь') - 1
    references_start = page_containing(pages, '24 Первоисточники') - 1
    assert page_containing(pages, '[41] Hugging Face') == references_start + 2
    glossary = '\n'.join(document.pages[i].extract_text(layout=True) or ''
                         for i in range(glossary_start, references_start))
    assert not re.search(r'(?<![.!?]) См\. с\.', ' '.join(glossary.split())), \
        'A glossary definition is missing terminal punctuation'
    glossary_lines = glossary.splitlines()
    assert len(GLOSSARY_CHAPTERS) == 78
    for term in GLOSSARY_CHAPTERS:
        longer = [other for other in GLOSSARY_CHAPTERS
                  if other.startswith(term + ' ')]
        rows = [' '.join(glossary_lines[i:i + 4])
                for i, line in enumerate(glossary_lines)
                if re.match(r'^\s*' + re.escape(term) + r'\s+', line, re.I)
                and not any(re.match(r'^\s*' + re.escape(other) + r'\s+', line, re.I)
                            for other in longer)]
        assert len(rows) == 1, (term, rows)
        match = re.search(r'См\. с\. (\d+)\.', rows[0])
        assert match, f'Missing glossary link: {term}'
        target_page = int(match.group(1))
        assert 5 <= target_page <= glossary_start, (term, target_page)
        if term in target_phrases:
            expected_page = page_containing(pages, target_phrases[term])
            assert target_page == expected_page, (term, target_page, expected_page)
        else:
            chapter = GLOSSARY_CHAPTERS[term]
            # The remaining chapter-first links are checked against the
            # rendered heading; their explanatory fit was reviewed manually.
            assert re.search(rf'(?m)^{chapter} [^\n]+', pages[target_page - 1]), (term, target_page)

    required_math = {
        'ОДНО ВЫЧИСЛИТЕЛЬНОЕ ЗВЕНО': 'φ',
        'ВЕРОЯТНОСТЬ ПОСЛЕДОВАТЕЛЬНОСТИ': '∏',
        'SOFTMAX: ОТ ОЦЕНОК К ДОЛЯМ': '∑',
        'ATTENTION: ВЗВЕСИТЬ ДОСТУПНЫЙ КОНТЕКСТ': '√',
        'LOSS: ШТРАФ ЗА СЛАБОЕ ПРЕДСКАЗАНИЕ': '−',
        'ОБНОВЛЕНИЕ ВЕСОВ: ШАГ ПРОТИВ ОШИБКИ': '←∇−',
        'LORA: ОБУЧИТЬ КОМПАКТНУЮ ДОБАВКУ': '≤′',
        'MOE: СМЕШАТЬ ОТВЕТЫ ВЫБРАННЫХ ЭКСПЕРТОВ': '∑∈',
        'ПАМЯТЬ: ГРУБАЯ ОЦЕНКА ТОЛЬКО ВЕСОВ': '≈×',
    }
    for title, glyphs in required_math.items():
        page = pages[page_containing(pages, 'РАЗБОР ФОРМУЛЫ / ' + title) - 1]
        for glyph in glyphs:
            assert glyph in page, (title, glyph)

    used_fonts = {char['fontname'] for page in document.pages for char in page.chars}
    assert not any('Helvetica' in name for name in used_fonts), used_fonts
    reader = PdfReader(PDF)
    assert reader.trailer['/Root'].get('/Lang') == 'ru-RU'
    linked_urls = []
    for page in reader.pages:
        fonts = page['/Resources']['/Font'].get_object()
        assert all('/Helvetica' != str(ref.get_object().get('/BaseFont'))
                   for ref in fonts.values())
        for ref in page.get('/Annots', []):
            action = ref.get_object().get('/A')
            if action and action.get('/URI'):
                linked_urls.append(str(action['/URI']))
    for suffix in ('2304.08485', '2302.01318', '2407.02646',
                   'consultant.ru/document/cons_doc_LAW_61801/',
                   'repositories-licenses',
                   'creativecommons.org/licenses/by-nc/4.0/',
                   'opensource.org/license/mit',
                   't.me/gorilla_under_hood'):
        assert sum(suffix in url for url in linked_urls) == 1, suffix

print(f'PDF checks passed: {len(pages)} pages; all 78 glossary references, '
      f'{len(targets)} explanatory anchors; '
      'all nine formulas retain their symbols')
