from __future__ import annotations

import html
import os
import re
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.table import Table as DocxTable
from docx.text.paragraph import Paragraph as DocxParagraph
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfdoc import PDFString
from reportlab.pdfbase.ttfonts import TTFont
from reportlab import rl_config
from reportlab.platypus import (
    BaseDocTemplate, Flowable, Frame, Image, KeepTogether, LongTable,
    NextPageTemplate, PageBreak, PageTemplate, Paragraph, Preformatted, Spacer, Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents
from editorial_content import (
    GLOSSARY_CHAPTERS, GLOSSARY_EXTRA, INTRO, NEW_REFERENCES, PRACTICUM,
    REFERENCE_TITLE_FIXES, TEXT_OVERRIDES,
)
from math_typesetting import formula as typeset_formula
from technical_figures import TechnicalFigure


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'manual/source.docx'
DEST = ROOT / 'manual/out/Теория_LLM_иллюстрированная.pdf'
ART = ROOT / 'manual/assets'
GLOSSARY_PAGE_MAP = {}
GLOSSARY_TERM_PAGE_MAP = {}
GLOSSARY_PARAGRAPH_TARGETS = {
    # Terms whose useful explanation starts after the chapter's first page.
    82: ('ffn',),
    83: ('rope',),
    90: ('teacher forcing',),
    91: ('gradient', 'backpropagation'),
    120: ('qlora', 'nf4', 'bf16'),
    122: ('distillation',),
    107: ('rlvr',),
    144: ('context window',),
    145: ('in-context learning',),
    146: ('kv cache',),
    147: ('prefix caching',),
    148: ('flashattention',),
    157: ('chunking',),
    164: ('moe', 'router'),
    189: ('idempotency', 'sql'),
}
PAGE_HEADER_MAP = {}
# Шрифты лежат в репозитории (manual/fonts), поэтому сборка воспроизводима из чистого клона.
# Переменная LLM_MANUAL_FONTROOT остаётся для нестандартных окружений.
_REPO_FONTS = Path(__file__).resolve().parent / 'fonts'
_FONT_ENV = os.environ.get('LLM_MANUAL_FONTROOT')
FONTROOT = Path(_FONT_ENV) if _FONT_ENV else _REPO_FONTS

pdfmetrics.registerFont(TTFont('Noto', str(FONTROOT / 'NotoSans-Regular.ttf')))
pdfmetrics.registerFont(TTFont('NotoBold', str(FONTROOT / 'NotoSans-Bold.ttf')))
pdfmetrics.registerFont(TTFont('NotoSerif', str(FONTROOT / 'NotoSerif-Regular.ttf')))
pdfmetrics.registerFont(TTFont('NotoSerifItalic', str(FONTROOT / 'NotoSerif-Italic.ttf')))
pdfmetrics.registerFont(TTFont('NotoMono', str(FONTROOT / 'LiberationMono-Regular.ttf')))
pdfmetrics.registerFont(TTFont('MathSymbols', str(FONTROOT / 'DejaVuSans.ttf')))
pdfmetrics.registerFont(TTFont('MathFull', str(FONTROOT / 'DejaVuMathTeXGyre.ttf')))
pdfmetrics.registerFontFamily('Noto', normal='Noto', bold='NotoBold')
pdfmetrics.registerFontFamily('NotoSerif', normal='NotoSerif', italic='NotoSerifItalic')
rl_config.canvas_basefontname = 'Noto'

INK = colors.HexColor('#252B2B')
MID = colors.HexColor('#586160')
PAPER = colors.HexColor('#F7F6F1')
LIME = colors.HexColor('#B8EA58')
PALE = colors.HexColor('#EAF4D7')
RULE = colors.HexColor('#CDD2CC')
WHITE = colors.white
W, H = A4
LEFT, RIGHT, TOP, BOTTOM = 54, 54, 62, 54
CONTENT = W - LEFT - RIGHT


def style(name, **kw):
    defaults = dict(fontName='Noto', fontSize=10.0, leading=15.2,
                    textColor=INK, spaceAfter=8, allowWidows=0, allowOrphans=0)
    defaults.update(kw)
    return ParagraphStyle(name, **defaults)


BODY = style('body')
LEAD = style('lead', fontSize=11.4, leading=17.4, spaceAfter=11)
CHAPTER = style('chapter', fontName='NotoBold', fontSize=18.8, leading=24,
                spaceBefore=17, spaceAfter=11, keepWithNext=True)
CAPTION = style('caption', fontSize=8.5, leading=12.3, textColor=MID,
                spaceBefore=5, spaceAfter=13)
SMALL = style('small', fontSize=8.0, leading=10.8, textColor=MID, spaceAfter=2.3)
REFERENCE = style('reference', fontSize=9.1, leading=13.4,
                  textColor=MID, spaceAfter=1.5)
TOCSTYLE = style('toc-chapter', fontName='NotoBold', fontSize=9.0,
                 leading=12.5, leftIndent=0, firstLineIndent=0,
                 rightIndent=25, spaceAfter=0)
TOCATLAS = style('toc-atlas', fontSize=8.1, leading=11.1,
                 textColor=MID, leftIndent=13, firstLineIndent=0,
                 rightIndent=25, spaceAfter=0)
CALL = style('call', fontSize=9.4, leading=14.5, spaceAfter=0)
TABLEHEAD = style('tablehead', fontName='NotoBold', fontSize=8.2, leading=11.2,
                  textColor=WHITE, spaceAfter=0)
TABLEBODY = style('tablebody', fontSize=8.3, leading=11.8, spaceAfter=0)


def esc(s):
    # The bundled Noto Sans lacks several mathematical glyphs. Paragraphs
    # need an explicit fallback or ReportLab silently drops those characters.
    fallback = '→≈√∇∞'
    return ''.join(
        '<br/>' if char == '\n' else
        f'<font name="MathSymbols">{char}</font>' if char in fallback else
        html.escape(char, quote=False)
        for char in s
    )


INLINE_CODE = re.compile(
    r'\bnpm run [a-z][a-z:]*|\bnpm test\b|\bollama pull [\w.:-]+|'
    r'\b(?:docs|src)/[\w./-]+|\bqwen2\.5:3b\b|'
    r'\bdecision\.count\b|\btariff-a-v2:price\b|'
    r'\b[A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)+\b|'
    r'\b[a-z][A-Za-z0-9]*[A-Z][A-Za-z0-9]*\b|'
    r'\b(?:executed|orders|count)\b'
)


AGENT_FORMS = (
    ('агентский', 'агентный'), ('агентская', 'агентная'),
    ('агентское', 'агентное'), ('агентские', 'агентные'),
    ('агентского', 'агентного'), ('агентскому', 'агентному'),
    ('агентском', 'агентном'), ('агентских', 'агентных'),
    ('агентскими', 'агентными'), ('агентским', 'агентным'),
    ('агентскую', 'агентную'), ('агентской', 'агентной'),
    ('Агентский', 'Агентный'), ('Агентские', 'Агентные'),
)


def normalize_terms(text):
    for old, new in AGENT_FORMS:
        text = re.sub(r'(?<!\w)' + old + r'(?!\w)', new, text)
    for old, new in (
        ('двухсторонние представления', 'двунаправленные представления'),
        ('Двухсторонние представления', 'Двунаправленные представления'),
        ('двухстороннего контекста', 'двунаправленного контекста'),
        ('torch autograd', 'torch.autograd'),
        ('decoder моделей', 'decoder-моделей'),
        ('LLM судей', 'LLM-судей'),
        ('IDs фрагментов', 'ID фрагментов'),
        ('IDs результатов', 'ID результатов'),
        ('Что проверить первым', 'Первая проверка'),
    ):
        text = text.replace(old, new)
    return text


def inline_markup(text):
    parts = []
    cursor = 0
    for match in INLINE_CODE.finditer(text):
        parts.append(esc(text[cursor:match.start()]))
        parts.append('<font name="NotoMono" color="#284B53">'
                     + esc(match.group()) + '</font>')
        cursor = match.end()
    parts.append(esc(text[cursor:]))
    return ''.join(parts)


def para(text, st=BODY):
    result = Paragraph(inline_markup(text), st)
    if st is not BODY or len(text.split()) < 8:
        return result
    result.wrap(CONTENT, H)
    lines = result.blPara.lines
    if result.blPara.kind != 0 or len(lines) < 2 or lines[-1][0] < CONTENT * .78:
        return result
    words = text.split()
    for count in range(3, min(7, len(words))):
        candidate = ' '.join(words[:-count]) + ' ' + '\u00a0'.join(words[-count:])
        adjusted = Paragraph(inline_markup(candidate), st)
        adjusted.wrap(CONTENT, H)
        if (adjusted.blPara.kind == 0 and len(adjusted.blPara.lines) == len(lines)
                and adjusted.blPara.lines[-1][0] <= CONTENT * .65):
            return adjusted
    return result


def reference_para(text):
    """Keep bibliography URLs clickable without interpreting source text as markup."""
    parts = []
    cursor = 0
    for match in re.finditer(r'https?://[^\s<>]+', text):
        url = match.group(0).rstrip('.,;')
        parts.append(esc(text[cursor:match.start()]))
        safe = html.escape(url, quote=True)
        parts.append(f'<link href="{safe}" color="#28717E">{safe}</link>')
        cursor = match.start() + len(url)
    parts.append(esc(text[cursor:]))
    return Paragraph(''.join(parts), REFERENCE)


class ChapterParagraph(Paragraph):
    def __init__(self, text, number):
        self.chapter_number = number
        super().__init__(esc(text), CHAPTER)


class ContentsParagraph(Paragraph):
    pass


class EditorialDoc(BaseDocTemplate):
    def __init__(self, filename):
        super().__init__(str(filename), pagesize=A4, leftMargin=LEFT,
                         rightMargin=RIGHT, topMargin=TOP, bottomMargin=BOTTOM,
                         title='Теория языковых моделей для владельца AI-лаборатории',
                         author='', pageCompression=1)
        body_frame = Frame(LEFT, BOTTOM, CONTENT, H - TOP - BOTTOM,
                           leftPadding=0, rightPadding=0, topPadding=0,
                           bottomPadding=0, id='bodyframe')
        cover_frame = Frame(0, 0, W, H, leftPadding=0, rightPadding=0,
                            topPadding=0, bottomPadding=0, id='coverframe')
        self.addPageTemplates([
            PageTemplate(id='cover', frames=[cover_frame], onPage=self.draw_cover),
            PageTemplate(id='body', frames=[body_frame], onPage=self.draw_body,
                         onPageEnd=self.draw_body_end),
        ])
        self.current_chapter = 'Как читать этот учебник'

    def beforeDocument(self):
        # multiBuild reruns the complete document; navigation state cannot leak.
        self.current_chapter = 'Как читать этот учебник'
        self.canv._doc.Catalog.Lang = PDFString('ru-RU')

    def draw_header_label(self, canvas, chapter):
        canvas.setFillColor(PAPER)
        canvas.rect(LEFT + 17, H - 42, CONTENT - 17, 18, fill=1, stroke=0)
        canvas.setFont('NotoBold', 7.5)
        canvas.setFillColor(MID)
        label = chapter.upper()
        if len(label) > 61:
            label = label[:58].rstrip() + '…'
        canvas.drawString(LEFT + 19, H - 35, label)

    def afterFlowable(self, flowable):
        if not hasattr(self, '_page_heading_drawn'):
            return  # Cover flowables run before the first body page.
        first_content_on_page = not self._page_heading_drawn
        if isinstance(flowable, ContentsParagraph):
            self.current_chapter = 'Содержание'
            if not self._page_heading_drawn or self.frame._y > H - TOP - 90:
                self._header_for_page = self.current_chapter
                self._page_heading_drawn = True
        if not self._page_heading_drawn and isinstance(
            flowable, (Paragraph, Table, Diagram, ProcessPlate, IsoFigure, Image,
                       TokenExample, TableOfContents)
        ):
            # A continued chapter at the top owns the page header even if a
            # new chapter starts farther down the page.
            self._header_for_page = self.current_chapter
            self._page_heading_drawn = True
        if isinstance(flowable, ChapterParagraph):
            key = f'chapter-{flowable.chapter_number}'
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(flowable.getPlainText(), key, level=0)
            self.notify('TOCEntry', (0, flowable.getPlainText(), self.page, key))
            self.current_chapter = flowable.getPlainText()
            if first_content_on_page:
                self._header_for_page = self.current_chapter
                self._page_heading_drawn = True

    def draw_cover(self, canvas, doc):
        canvas.saveState()
        canvas.setFillColor(INK)
        canvas.rect(0, 0, W, H, fill=1, stroke=0)
        canvas.setFillColor(LIME)
        canvas.rect(42, H - 60, 31, 6, fill=1, stroke=0)
        canvas.setFont('NotoBold', 11)
        canvas.setFillColor(LIME)
        canvas.drawString(42, H - 88, 'ПРАКТИЧЕСКИЙ УЧЕБНИК')
        canvas.setFont('NotoBold', 30)
        canvas.setFillColor(WHITE)
        for n, line in enumerate(['Теория языковых', 'моделей для владельца', 'AI-лаборатории']):
            canvas.drawString(42, H - 137 - n * 38, line)
        canvas.setFont('Noto', 11.4)
        canvas.setFillColor(colors.HexColor('#D6DED7'))
        canvas.drawString(43, H - 271, 'От нейросети и обучения до памяти и агентной системы')
        img = ImageReader(str(ART / 'cover.jpg'))
        # A framed illustration anchors the cover without filling it with text.
        canvas.drawImage(img, 42, 152, width=W - 84, height=342,
                         preserveAspectRatio=False, mask='auto')
        canvas.setStrokeColor(LIME)
        canvas.setLineWidth(1.2)
        canvas.line(42, 118, W - 42, 118)
        canvas.setFont('Noto', 9)
        canvas.setFillColor(colors.HexColor('#D6DED7'))
        canvas.drawString(42, 90, 'МОДЕЛЬ  /  ДАННЫЕ  /  RUNTIME  /  ПРОВЕРКА')
        canvas.restoreState()

    def draw_body(self, canvas, doc):
        canvas.saveState()
        self._page_heading_drawn = False
        self._header_for_page = self.current_chapter
        canvas.setFillColor(PAPER)
        canvas.rect(0, 0, W, H, fill=1, stroke=0)
        canvas.setFillColor(LIME)
        canvas.rect(LEFT, H - 35, 12, 4, fill=1, stroke=0)
        canvas.setStrokeColor(RULE)
        canvas.setLineWidth(0.5)
        canvas.line(LEFT, H - 47, W - RIGHT, H - 47)
        canvas.line(LEFT, 39, W - RIGHT, 39)
        canvas.setFont('Noto', 7.6)
        canvas.setFillColor(MID)
        canvas.drawString(LEFT, 25, 'Теория LLM · полный мануал')
        canvas.setFont('NotoBold', 8.2)
        canvas.setFillColor(INK)
        canvas.drawRightString(W - RIGHT, 25, f'{doc.page:02d}')
        # LongTable continuation pages may not call afterFlowable before
        # onPageEnd. Draw the previous running title as a reliable fallback.
        self.draw_header_label(canvas,
                               PAGE_HEADER_MAP.get(doc.page, self.current_chapter))
        canvas.restoreState()

    def draw_body_end(self, canvas, doc):
        canvas.saveState()
        self.draw_header_label(canvas,
                               PAGE_HEADER_MAP.get(doc.page, self._header_for_page))
        canvas.restoreState()


class Diagram(Flowable):
    def __init__(self, title, nodes, caption, variant='flow'):
        super().__init__()
        self.title, self.nodes, self.caption, self.variant = title, nodes, caption, variant
        self.width = CONTENT
        self.height = 220 if variant == 'stack' else (145 if variant == 'flow' else 175)

    def wrap(self, aw, ah):
        return self.width, self.height

    def draw_text(self, text, x, y, w, h, bold=False, size=8.2, color=INK):
        st = ParagraphStyle('diagramtext', fontName='NotoBold' if bold else 'Noto',
                            fontSize=size, leading=size * 1.32, textColor=color)
        p = Paragraph(esc(text), st)
        _, ph = p.wrap(w, h)
        p.drawOn(self.canv, x, y + h - ph)

    def draw(self):
        c = self.canv
        c.setFillColor(INK)
        c.roundRect(0, 0, self.width, self.height, 9, fill=1, stroke=0)
        c.setFillColor(LIME)
        c.rect(18, self.height - 25, 15, 3, fill=1, stroke=0)
        self.draw_text(self.title, 41, self.height - 32, self.width - 58, 20,
                       bold=True, size=10.1, color=WHITE)
        if self.variant == 'stack':
            lane_h = 27
            gap = 6
            for i, (label, detail) in enumerate(self.nodes):
                y = self.height - 65 - i * (lane_h + gap)
                c.setFillColor(colors.HexColor('#E8EDE2') if i % 2 == 0 else colors.HexColor('#DCE6D4'))
                c.roundRect(18, y - lane_h, self.width - 36, lane_h, 4, fill=1, stroke=0)
                c.setFillColor(LIME)
                c.rect(18, y - lane_h, 5, lane_h, fill=1, stroke=0)
                self.draw_text(label, 33, y - 22, 115, 18, bold=True, size=8.3)
                self.draw_text(detail, 154, y - 22, self.width - 187, 18, size=8.2)
            return
        top = self.height - 61
        n = len(self.nodes)
        gap = 8 if n > 3 else 10
        cardw = (self.width - 36 - gap * (n - 1)) / n
        cardh = 75 if self.variant == 'flow' else 80
        for i, (label, detail) in enumerate(self.nodes):
            x = 18 + i * (cardw + gap)
            y = top - cardh
            c.setFillColor(colors.HexColor('#F1F3EB') if i % 2 == 0 else colors.HexColor('#E6EDDC'))
            c.roundRect(x, y, cardw, cardh, 5, fill=1, stroke=0)
            c.setFillColor(LIME)
            c.circle(x + 12, y + cardh - 14, 7, fill=1, stroke=0)
            c.setFillColor(INK)
            c.setFont('NotoBold', 7.4)
            c.drawCentredString(x + 12, y + cardh - 16.5, str(i + 1))
            self.draw_text(label, x + 10, y + cardh - 44, cardw - 20, 19,
                           bold=True, size=8.2)
            self.draw_text(detail, x + 10, y + 8, cardw - 20, cardh - 52,
                           size=7.2, color=MID)
            if self.variant in ('flow', 'loop') and i < n - 1:
                cy = y + cardh / 2
                c.setStrokeColor(LIME)
                c.setFillColor(LIME)
                c.setLineWidth(1.4)
                c.line(x + cardw + 1, cy, x + cardw + gap - 2, cy)
                path = c.beginPath()
                path.moveTo(x + cardw + gap - 2, cy)
                path.lineTo(x + cardw + gap - 5, cy + 2.5)
                path.lineTo(x + cardw + gap - 5, cy - 2.5)
                path.close()
                c.drawPath(path, stroke=0, fill=1)
        if self.variant == 'loop':
            c.setStrokeColor(LIME)
            c.setLineWidth(1.2)
            y = 26
            c.line(self.width - 40, y, 43, y)
            c.line(43, y, 43, 40)
            c.setFont('Noto', 7)
            c.setFillColor(colors.HexColor('#C8D1C9'))
            c.drawCentredString(self.width / 2, 15, 'новое наблюдение меняет следующий шаг')
            return


class EvidenceDiagram(Flowable):
    """Compare mechanisms through a concrete change and its observable trace."""

    def __init__(self, title, subtitle, rows, caption):
        super().__init__()
        assert 2 <= len(rows) <= 4
        self.title, self.subtitle = title, subtitle
        self.rows, self.caption = rows, caption
        self.width = CONTENT
        self.height = 98 + 39 * len(rows)

    def wrap(self, aw, ah):
        return self.width, self.height

    def _cell(self, value, x, y, w, h, *, bold=False, size=7.7, color=INK):
        st = ParagraphStyle('evidence-cell', fontName='NotoBold' if bold else 'Noto',
                            fontSize=size, leading=size * 1.27, textColor=color)
        p = Paragraph(esc(value), st)
        _, ph = p.wrap(w, h)
        assert ph <= h - 6, (self.title, value, ph, h)
        p.drawOn(self.canv, x, y + (h - ph) / 2)

    def draw(self):
        c = self.canv
        c.setFillColor(INK)
        c.roundRect(0, 0, self.width, self.height, 9, fill=1, stroke=0)
        c.setFillColor(LIME)
        c.rect(18, self.height - 25, 15, 3, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont('NotoBold', 10.1)
        c.drawString(41, self.height - 27, self.title)
        c.setFillColor(colors.HexColor('#B9C9BD'))
        c.setFont('Noto', 7.8)
        c.drawString(18, self.height - 48, self.subtitle)
        c.setFont('NotoBold', 7.0)
        c.drawString(32, self.height - 65, 'КОМПОНЕНТ')
        c.drawString(150, self.height - 65, 'ЧТО МЕНЯЕТСЯ')
        c.drawString(355, self.height - 65, 'ЧЕМ ПРОВЕРИТЬ')
        row_top = self.height - 74
        row_h = 37
        for i, (label, change, evidence) in enumerate(self.rows):
            y = row_top - (i + 1) * row_h - i * 3
            c.setFillColor(colors.HexColor('#F0F3EC') if i % 2 == 0
                           else colors.HexColor('#E1EBDD'))
            c.roundRect(18, y, self.width - 36, row_h, 4, fill=1, stroke=0)
            c.setFillColor(LIME)
            c.rect(18, y, 5, row_h, fill=1, stroke=0)
            c.setStrokeColor(colors.HexColor('#C8D2C7'))
            c.setLineWidth(0.5)
            c.line(141, y + 6, 141, y + row_h - 6)
            c.line(345, y + 6, 345, y + row_h - 6)
            self._cell(label, 32, y, 104, row_h, bold=True, size=8.25)
            self._cell(change, 150, y, 187, row_h, size=7.65)
            self._cell(evidence, 355, y, 110, row_h, size=7.5,
                       color=colors.HexColor('#43564A'))


def diagram_plate(diagram):
    return KeepTogether([
        diagram,
        Paragraph('Техническая схема. ' + esc(diagram.caption), CAPTION),
    ])


class IsoFigure(Flowable):
    """Vector explanatory figure: depth is used to separate data planes."""

    DARK = colors.HexColor('#293330')
    DEEP = colors.HexColor('#1D2623')
    MIST = colors.HexColor('#DCE7DE')
    DIM = colors.HexColor('#A9BAB0')
    SLATE = colors.HexColor('#60736B')
    FACE = colors.HexColor('#ECF0E7')

    def __init__(self, kind):
        super().__init__()
        self.kind = kind
        self.width = CONTENT
        self.height = {'attention': 231, 'kv': 221, 'moe': 245,
                       'layer': 190}[kind]
        self.caption = {
            'attention': 'Схема маски для четырёх позиций. В строке Q3 доступны K1–K3; K4 скрыта как будущая позиция. Цвет показывает доступность, а не величину веса attention.',
            'kv': 'При генерации кеш хранит пары K/V для уже обработанных позиций. Новый токен добавляет новую пару; прежние пары используются повторно. Показан один слой и одна условная голова.',
            'moe': 'Пример одного токена в слое Mixtral: router выбирает два из восьми экспертов, затем их результаты объединяются с весами. Для другого токена выбор может измениться.',
            'layer': 'Остаточная связь добавляет вход к результату каждого блока. Нормализация, позиционный механизм и различия конкретных архитектур здесь опущены.',
        }[kind]

    def wrap(self, aw, ah):
        return self.width, self.height

    def label(self, value, x, y, size=8, bold=False, color=None):
        c = self.canv
        c.setFont('NotoBold' if bold else 'Noto', size)
        c.setFillColor(color or self.MIST)
        c.drawString(x, y, value)

    def center(self, value, x, y, size=8, bold=False, color=None):
        c = self.canv
        c.setFont('NotoBold' if bold else 'Noto', size)
        c.setFillColor(color or self.MIST)
        c.drawCentredString(x, y, value)

    def polygon(self, points, fill, stroke=None, width=0.5):
        c = self.canv
        p = c.beginPath()
        p.moveTo(*points[0])
        for pt in points[1:]:
            p.lineTo(*pt)
        p.close()
        c.setFillColor(fill)
        c.setStrokeColor(stroke or fill)
        c.setLineWidth(width)
        c.drawPath(p, fill=1, stroke=int(stroke is not None))

    def prism(self, x, y, w, h, label, active=False, depth=7):
        top = LIME if active else self.FACE
        front = colors.HexColor('#B9D98B') if active else colors.HexColor('#B6C3B9')
        side = colors.HexColor('#86B65A') if active else self.SLATE
        self.polygon([(x, y+h), (x+depth, y+h+depth),
                      (x+w+depth, y+h+depth), (x+w, y+h)], top)
        self.polygon([(x+w, y), (x+w+depth, y+depth),
                      (x+w+depth, y+h+depth), (x+w, y+h)], side)
        self.polygon([(x, y), (x+w, y), (x+w, y+h), (x, y+h)], front)
        self.center(label, x+w/2, y+h/2-2.5, 7.7, True, INK)

    def arrow(self, x1, y1, x2, y2, color=LIME, width=1.6):
        import math
        c = self.canv
        c.setStrokeColor(color)
        c.setFillColor(color)
        c.setLineWidth(width)
        c.line(x1, y1, x2, y2)
        angle = math.atan2(y2-y1, x2-x1)
        wing = 4.2
        back = 7
        self.polygon([(x2, y2),
                      (x2-back*math.cos(angle)+wing*math.sin(angle),
                       y2-back*math.sin(angle)-wing*math.cos(angle)),
                      (x2-back*math.cos(angle)-wing*math.sin(angle),
                       y2-back*math.sin(angle)+wing*math.cos(angle))], color)

    def base(self, title, kicker):
        c = self.canv
        c.setFillColor(self.DEEP)
        c.roundRect(0, 0, self.width, self.height, 9, fill=1, stroke=0)
        c.setFillColor(LIME)
        c.rect(18, self.height-25, 16, 3, fill=1, stroke=0)
        self.label(title, 44, self.height-27, 10.0, True, WHITE)
        self.label(kicker, 18, self.height-46, 7.7, False, self.DIM)

    def draw_attention(self):
        c = self.canv
        self.base('CAUSAL ATTENTION: КОМУ ВИДЕН КОНТЕКСТ',
                  'Строка = query текущей позиции; столбец = key позиции источника')
        # Four input positions, then a raised matrix of allowed connections.
        for n in range(4):
            y = 137-n*26
            self.prism(22, y, 37, 18, f'x{n+1}', active=n==2, depth=5)
        self.label('ПОЗИЦИИ', 22, 170, 7.0, True, self.DIM)
        self.arrow(70, 99, 104, 99)
        self.label('Q · Kᵀ', 109, 176, 8.2, True, WHITE)
        self.label('K1', 150, 58, 7.4, True)
        self.label('K2', 184, 58, 7.4, True)
        self.label('K3', 218, 58, 7.4, True)
        self.label('K4', 252, 58, 7.4, True)
        x0, y0, cw, rh, skew = 139, 76, 34, 19, 9
        # Back rows first: the plane's front edge remains visible.
        for r in range(3, -1, -1):
            q = 4-r
            yy = y0+r*rh
            xx = x0+r*skew
            self.label(f'Q{q}', xx-25, yy+8, 7.5, True,
                       LIME if q == 3 else self.MIST)
            for col in range(4):
                x = xx+col*cw
                allowed = col < q
                fill = (LIME if q == 3 and allowed else
                        colors.HexColor('#D9EAC4') if allowed else
                        colors.HexColor('#697B70'))
                self.polygon([(x, yy), (x+cw-2, yy),
                              (x+cw+skew-2, yy+rh-2),
                              (x+skew, yy+rh-2)],
                             fill, self.DARK, 0.5)
        self.polygon([(139, 76), (275, 76), (311, 152), (175, 152)],
                     colors.Color(0,0,0,alpha=0), LIME, 0.7)
        c.setFillColor(self.DARK)
        c.roundRect(329, 66, 140, 108, 5, fill=1, stroke=0)
        self.label('ПРИМЕР: Q3', 341, 151, 9.1, True, LIME)
        self.label('видит K1, K2, K3', 341, 129, 8.2)
        self.label('не видит K4', 341, 111, 8.2)
        self.label('Маска закрывает', 341, 89, 7.7, False, self.DIM)
        self.label('будущую позицию.', 341, 75, 7.7, False, self.DIM)
        c.setFillColor(LIME)
        c.rect(22, 24, 11, 7, fill=1, stroke=0)
        self.label('доступно', 39, 24, 7.5)
        c.setFillColor(colors.HexColor('#697B70'))
        c.rect(121, 24, 11, 7, fill=1, stroke=0)
        self.label('скрыто маской', 138, 24, 7.5)

    def draw_kv(self):
        c = self.canv
        self.base('KV CACHE: НОВЫЙ ТОКЕН БЕЗ ПЕРЕСЧЁТА СТАРЫХ',
                  'Пары key/value сохранены отдельно для каждого обработанного токена')
        self.label('PREFILL · исходный запрос', 19, 151, 7.9, True, self.DIM)
        for n in range(3):
            self.prism(24+n*43, 93, 30, 32, f't{n+1}', depth=7)
        self.arrow(155, 111, 177, 111)
        self.label('КЕШ СЛОЯ', 183, 153, 8.3, True, WHITE)
        self.label('K', 182, 126, 8.8, True, LIME)
        self.label('V', 182, 67, 8.8, True, LIME)
        for n in range(4):
            x = 208+n*43
            self.prism(x, 106, 29, 31, f'K{n+1}', active=n==3)
            self.prism(x, 47, 29, 31, f'V{n+1}', active=n==3)
        c.setStrokeColor(self.DIM)
        c.setDash(3, 3)
        c.line(331, 40, 331, 151)
        c.setDash()
        self.label('DECODE', 351, 153, 8.3, True, LIME)
        self.label('добавлен t4', 350, 91, 7.6, False, self.MIST)
        self.label('старые K/V', 208, 26, 7.5, False, self.DIM)
        self.label('новые K/V', 345, 26, 7.5, False, LIME)

    def draw_moe(self):
        c = self.canv
        self.base('MoE: ДВА ЭКСПЕРТА ИЗ ВОСЬМИ',
                  'Схема одного токена в одном MoE-слое Mixtral')
        self.prism(23, 86, 54, 47, 'токен', active=True)
        self.arrow(87, 110, 112, 110)
        self.prism(118, 86, 59, 47, 'router')
        self.label('выбор по входу', 107, 67, 7.5, False, self.DIM)
        for n in range(8):
            col, row = n % 4, n // 4
            x = 197+col*40
            y = 137-row*67
            self.prism(x, y, 28, 29, f'E{n+1}', active=n in (3, 7), depth=5)
        # The two branches travel outside the inactive blocks, so the selected
        # experts and both output paths remain visible at print size.
        c.setStrokeColor(LIME)
        c.setLineWidth(1.8)
        c.line(184, 118, 190, 118)
        c.line(190, 118, 190, 181)
        c.line(190, 181, 309, 181)
        self.arrow(309, 181, 315, 153, LIME, 1.8)
        c.line(184, 102, 190, 102)
        c.line(190, 102, 190, 58)
        c.line(190, 58, 309, 58)
        self.arrow(309, 58, 315, 84, LIME, 1.8)
        self.label('активны E4 и E8', 196, 47, 7.8, False, LIME)
        self.arrow(355, 151, 381, 120, LIME, 1.5)
        self.arrow(355, 84, 381, 89, LIME, 1.5)
        c.setFillColor(self.DARK)
        c.roundRect(385, 73, 82, 63, 5, fill=1, stroke=0)
        self.center('ВЗВЕШЕННАЯ', 426, 113, 7.3, True, WHITE)
        self.center('СУММА', 426, 99, 8.0, True, LIME)
        self.center('g₄E₄ + g₈E₈', 426, 83, 7.2, False, self.MIST)
        self.label('Другой токен может выбрать другую пару.', 20, 22, 8.0, False, self.DIM)

    def draw_layer(self):
        c = self.canv
        self.base('СЛОЙ ТРАНСФОРМЕРА: ATTENTION И FFN',
                  'Два преобразования и два остаточных сложения')
        # Top bypass carries the layer input to the first residual addition.
        self.prism(20, 72, 54, 42, 'вход x', depth=6)
        self.prism(112, 72, 90, 42, 'attention', depth=6)
        self.prism(270, 72, 68, 42, 'FFN', depth=6)
        self.prism(414, 72, 49, 42, 'выход', active=True, depth=6)
        for cx in (238, 373):
            c.setFillColor(LIME)
            c.circle(cx, 93, 13, fill=1, stroke=0)
            self.center('+', cx, 88, 15, True, INK)
        for a, b in ((80,106), (208,221), (251,264),
                     (344,356), (386,408)):
            self.arrow(a, 93, b, 93, LIME, 1.5)
        c.setStrokeColor(self.DIM)
        c.setLineWidth(1.2)
        c.line(80, 120, 80, 130)
        c.line(80, 130, 238, 130)
        self.arrow(238, 130, 238, 109, self.DIM, 1.2)
        c.line(238, 79, 238, 53)
        c.line(238, 53, 373, 53)
        self.arrow(373, 53, 373, 78, self.DIM, 1.2)
        self.label('смешивает позиции', 114, 36, 7.5, False, self.DIM)
        self.label('меняет признаки', 270, 36, 7.5, False, self.DIM)

    def draw(self):
        {'attention': self.draw_attention,
         'kv': self.draw_kv,
         'moe': self.draw_moe,
         'layer': self.draw_layer}[self.kind]()


EXTRA_FIGURES = {80: IsoFigure('attention'), 146: IsoFigure('kv'),
                 166: IsoFigure('moe')}


class ProcessPlate(Flowable):
    """A compact editorial infographic with explanatory arrows and no AI text."""

    def __init__(self, kind):
        super().__init__()
        self.kind = kind
        self.width = CONTENT
        self.height = 183 if kind == 'training' else 181
        self.caption = (
            'При обучении меняются веса. При инференсе меняются вход, активации '
            'и ответ; веса остаются прежними.' if kind == 'training' else
            'Поиск выбирает материал, приложение добавляет его в запрос, модель '
            'формулирует ответ. Источник нужно проверять отдельно.'
        )

    def wrap(self, aw, ah):
        return self.width, self.height

    def label(self, value, x, y, width, size=8.2, bold=False, color=INK):
        st = ParagraphStyle('processlabel', fontName='NotoBold' if bold else 'Noto',
                            fontSize=size, leading=size * 1.3, textColor=color)
        p = Paragraph(esc(value), st)
        _, ph = p.wrap(width, 60)
        p.drawOn(self.canv, x, y - ph)

    def box(self, x, y, w, h, title, detail, accent=False):
        c = self.canv
        c.setFillColor(PALE if accent else colors.HexColor('#F5F6F1'))
        c.roundRect(x, y, w, h, 5, fill=1, stroke=0)
        c.setFillColor(LIME if accent else RULE)
        c.roundRect(x, y, 4, h, 2, fill=1, stroke=0)
        self.label(title, x + 11, y + h - 10, w - 20, 8.3, True)
        self.label(detail, x + 11, y + h - 28, w - 20, 7.2, False, MID)

    def arrow(self, x1, x2, y):
        c = self.canv
        c.setStrokeColor(colors.HexColor('#84937D'))
        c.setFillColor(colors.HexColor('#84937D'))
        c.setLineWidth(1.1)
        c.line(x1, y, x2, y)
        path = c.beginPath()
        path.moveTo(x2, y)
        path.lineTo(x2 - 4, y + 2.7)
        path.lineTo(x2 - 4, y - 2.7)
        path.close()
        c.drawPath(path, fill=1, stroke=0)

    def draw(self):
        c = self.canv
        c.setFillColor(INK)
        c.roundRect(0, 0, self.width, self.height, 9, fill=1, stroke=0)
        c.setFillColor(LIME)
        c.rect(17, self.height - 24, 14, 3, fill=1, stroke=0)
        title = ('ОБУЧЕНИЕ И ИНФЕРЕНС: ЧТО МЕНЯЕТСЯ?' if self.kind == 'training'
                 else 'RAG: ОТ ВОПРОСА К ОТВЕТУ С ИСТОЧНИКОМ')
        self.label(title, 40, self.height - 15, self.width - 54, 9.7, True, WHITE)
        if self.kind == 'training':
            c.setFillColor(colors.HexColor('#E7EBE3'))
            c.roundRect(16, 88, self.width - 32, 53, 5, fill=1, stroke=0)
            c.roundRect(16, 21, self.width - 32, 53, 5, fill=1, stroke=0)
            self.label('ОБУЧЕНИЕ', 26, 129, 91, 8.0, True)
            self.label('ИНФЕРЕНС', 26, 62, 91, 8.0, True)
            self.box(115, 93, 100, 45, 'Данные', 'примеры текста')
            self.box(245, 93, 100, 45, 'Вычисление', 'ошибка и градиент')
            self.box(375, 93, 96, 45, 'Веса', 'обновляются', True)
            self.arrow(218, 241, 114)
            self.arrow(348, 371, 114)
            self.box(115, 26, 100, 45, 'Новый запрос', 'текущий вход')
            self.box(245, 26, 100, 45, 'Модель', 'те же веса')
            self.box(375, 26, 96, 45, 'Ответ', 'новые токены', True)
            self.arrow(218, 241, 47)
            self.arrow(348, 371, 47)
        else:
            c.setFillColor(colors.HexColor('#E7EBE3'))
            c.roundRect(16, 48, self.width - 32, 95, 5, fill=1, stroke=0)
            nodes = [
                ('Вопрос', 'что узнать?'),
                ('Поиск', 'выбрать фрагмент'),
                ('Контекст', 'вопрос + фрагмент'),
                ('Модель', 'те же веса'),
                ('Ответ', 'со ссылкой'),
            ]
            cardw, gap = 84, 7
            for i, (name, detail) in enumerate(nodes):
                x = 20 + i * (cardw + gap)
                self.box(x, 69, cardw, 55, name, detail, i in (2, 4))
                if i < 4:
                    self.arrow(x + cardw + 1, x + cardw + gap - 2, 97)
            self.label('Индекс хранится в приложении; веса модели при таком запросе не меняются.',
                       26, 38, self.width - 51, 7.6, False, WHITE)


def callout(text):
    label = 'Для лаборатории.'
    if text.startswith(label):
        text = text[len(label):].lstrip()
    p = Paragraph('<b>ДЛЯ ЛАБОРАТОРИИ</b><br/>' + esc(text), CALL)
    tbl = Table([[p]], colWidths=[CONTENT], hAlign='LEFT')
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), PALE),
        ('LINEBEFORE', (0, 0), (0, -1), 4, LIME),
        ('LEFTPADDING', (0, 0), (-1, -1), 13),
        ('RIGHTPADDING', (0, 0), (-1, -1), 14),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 11),
    ]))
    return KeepTogether([Spacer(1, 4), tbl, Spacer(1, 9)])


def source_table(docx_table):
    rows = []
    for row in docx_table.rows:
        rows.append([normalize_terms(cell.text.strip().replace('\n', ' / '))
                     for cell in row.cells])
    n = len(rows[0])
    glossary = len(rows) > 20 and n == 2
    if glossary:
        known = {row[0].casefold() for row in rows[1:]}
        rows.extend([list(item) for item in GLOSSARY_EXTRA if item[0].casefold() not in known])
        rows = [rows[0]] + sorted(rows[1:], key=lambda row: row[0].casefold())
        for row in rows[1:]:
            if row[0].casefold() == 'loss':
                row[1] = 'Функция потерь: численная мера несоответствия прогнозов обучающим целям.'
        if GLOSSARY_PAGE_MAP:
            for row in rows[1:]:
                chapter = GLOSSARY_CHAPTERS[row[0].casefold()]
                page = GLOSSARY_TERM_PAGE_MAP.get(row[0].casefold(),
                                                  GLOSSARY_PAGE_MAP[chapter])
                if row[1] and row[1][-1] not in '.!?':
                    row[1] += '.'
                row[1] += f' См.\u00a0с.\u00a0{page}.'
    if n == 4:
        widths = [CONTENT * f for f in ([.17, .25, .30, .28] if len(rows) == 5 else [.10, .28, .34, .28])]
    elif n == 3:
        widths = [CONTENT * f for f in [.31, .35, .34]]
    else:
        widths = [CONTENT * .30, CONTENT * .70]
    data = []
    for i, row in enumerate(rows):
        cell_style = TABLEHEAD if i == 0 else (
            style('glossarycell', fontSize=9.0, leading=12.3, spaceAfter=0) if glossary else TABLEBODY)
        data.append([Paragraph(inline_markup(cell), cell_style) for cell in row])
    table = LongTable(data, colWidths=widths, repeatRows=1, hAlign='LEFT')
    cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), INK),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 3 if glossary else 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3 if glossary else 8),
        ('LINEBELOW', (0, 0), (-1, -1), .45, RULE),
    ]
    for i in range(1, len(rows)):
        if i % 2 == 0:
            cmds.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#EDEFE9')))
    table.setStyle(TableStyle(cmds))
    return table


FORMULA_GUIDES = {
    44: (
        'Одно вычислительное звено',
        'Взвесить входные числа, прибавить смещение, затем применить правило преобразования.',
        'x — числа на входе; W и b — сохраняемые параметры; φ — функция активации; y — выход.',
        'x=(2; 3), W=(0,5; −1), b=1. Тогда Wx+b=−1; при φ=ReLU получаем y=0.',
    ),
    66: (
        'Вероятность последовательности',
        'Оценку всей последовательности собирают по шагам: каждый новый токен оценивают с учётом предыдущих.',
        'xₜ — токен на шаге t; x до t — все предыдущие токены; T — длина; θ — параметры модели.',
        'Если P(X)=0,4 и P(Y при X)=0,5, то P(X, Y)=0,4 × 0,5=0,2. Второй шаг зависит от первого.',
    ),
    70: (
        'Softmax: от оценок к долям',
        'Каждую сырую оценку превращают в положительный вес и делят на сумму весов всех вариантов.',
        'zᵢ — оценка одного токена; j перебирает все варианты; e в степени z сохраняет порядок оценок и даёт положительные веса.',
        'Для оценок A=2, B=1, C=0 сумма положительных весов ≈11,11. В таблице показано, какую долю получает каждый токен.',
    ),
    79: (
        'Attention: взвесить доступный контекст',
        'Позиция сравнивает свой запрос с ключами доступных позиций, получает веса и смешивает их значения.',
        'Q — запросы; K — ключи; V — передаваемые значения; √dₖ задаёт масштаб; M закрывает запрещённые связи.',
        'Если после масштаба и маски две оценки равны 2 и 0, веса ≈0,88 и 0,12. Выход для этой позиции ≈0,88V₁ + 0,12V₂.',
    ),
    88: (
        'Loss: штраф за слабое предсказание',
        'Чем ниже оценка правильного следующего токена, тем выше штраф за этот учебный шаг.',
        'Pθ — оценка правильного токена при данном префиксе; log — натуральный логарифм; минус делает штраф неотрицательным.',
        'Если правильному токену дали 0,1, штраф ≈2,30; если 0,8 — ≈0,22. Модель учится снижать средний штраф.',
    ),
    92: (
        'Обновление весов: шаг против ошибки',
        'Градиент показывает направление роста ошибки; из параметров вычитают небольшой шаг в этом направлении.',
        'θ — параметры; L — ошибка; ∇θL — её градиент; η — размер шага обучения.',
        'θ=1, η=0,1, градиент=−2. Новый θ=1−0,1×(−2)=1,2.',
    ),
    118: (
        'LoRA: обучить компактную добавку',
        'Базовая матрица W остаётся фиксированной. Обучают две меньшие матрицы, произведение которых добавляют к W.',
        'W′ — итоговая матрица; A имеет размер r×k, B — d×r; s — масштаб; r ограничивает ранг добавки.',
        'Для одной матрицы 1000×1000 полный набор — 1 000 000 чисел. При r=8 в A и B вместе 16 000 обучаемых чисел.',
    ),
    165: (
        'MoE: смешать ответы выбранных экспертов',
        'Router выбирает внутренние сети, а выход слоя складывает их ответы с разными коэффициентами.',
        'S(x) — выбранные эксперты; Eᵢ(x) — выход эксперта; gᵢ(x) — коэффициент его вклада.',
        'Ответы 10 и 20, коэффициенты 0,7 и 0,3. Итог: 0,7×10+0,3×20=13.',
    ),
    204: (
        'Память: грубая оценка только весов',
        'Число параметров умножают на битность хранения и делят на восемь, чтобы перейти от битов к байтам.',
        'N — число параметров; bits per parameter — бит на одно число; деление на 8 переводит биты в байты.',
        '7 млрд × 4 бита / 8 = 3,5 млрд байт, около 3,5 GB. При 16 битах — около 14 GB. KV cache и буферы сюда не входят.',
    ),
}


def formula_block(index):
    """Use one checked vector compositor for every display equation."""
    content = typeset_formula(index, CONTENT)
    title, meaning, symbols, example = FORMULA_GUIDES[index]
    kicker = style('formula-kicker', fontName='NotoBold', fontSize=8.2,
                   leading=10.5, textColor=WHITE, spaceAfter=0)
    explanation = style('formula-meaning', fontName='NotoBold', fontSize=9.0,
                        leading=12.3, textColor=INK, spaceAfter=0)
    detail = style('formula-detail', fontSize=8.8, leading=12.4,
                   textColor=INK, spaceAfter=0)
    example_style = style('formula-example', fontSize=8.8, leading=12.4,
                          textColor=INK, spaceAfter=0)
    rows = [
        [Paragraph('РАЗБОР ФОРМУЛЫ / ' + esc(title.upper()), kicker)],
        [Paragraph(esc(meaning), explanation)],
        [content],
        [Paragraph('<b>Что обозначено:</b> ' + esc(symbols), detail)],
        [Paragraph('<b>На числах:</b> ' + esc(example), example_style)],
    ]
    if index == 70:
        head = style('softmax-head', fontName='NotoBold', fontSize=7.5,
                     leading=10.0, textColor=WHITE, spaceAfter=0)
        cell = style('softmax-cell', fontSize=8.2, leading=11.0,
                     textColor=INK, spaceAfter=0)
        data = [
            [Paragraph(x, head) for x in ('ТОКЕН', 'LOGIT', 'ВЕС', 'ДОЛЯ ОТ 11,11')],
            [Paragraph(x, cell) for x in ('A', '2', '7,39', '7,39 / 11,11 = 0,665')],
            [Paragraph(x, cell) for x in ('B', '1', '2,72', '2,72 / 11,11 = 0,245')],
            [Paragraph(x, cell) for x in ('C', '0', '1', '1 / 11,11 = 0,090')],
        ]
        steps = Table(data, colWidths=[65, 65, 75, 258], hAlign='CENTER')
        steps.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#293732')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1),
             [colors.HexColor('#F7F6F1'), colors.HexColor('#EBEEE6')]),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        rows.append([steps])
    box = Table(rows, colWidths=[CONTENT], hAlign='LEFT')
    box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#1D2825')),
        ('BACKGROUND', (0, 1), (0, 1), colors.HexColor('#EAF4D7')),
        ('BACKGROUND', (0, 2), (0, 2), colors.HexColor('#F7F6F1')),
        ('BACKGROUND', (0, 3), (0, 3), colors.HexColor('#EBEEE6')),
        ('BACKGROUND', (0, 4), (0, 4), colors.HexColor('#DCEEEF')),
        ('BACKGROUND', (0, 5), (0, 5), colors.HexColor('#DCEEEF')),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('TOPPADDING', (0, 2), (0, 2), 5),
        ('BOTTOMPADDING', (0, 2), (0, 2), 4),
        ('ALIGN', (0, 2), (0, 2), 'CENTER'),
        ('NOSPLIT', (0, 0), (0, -1)),
    ]))
    if index == 70:
        box.glossary_term = 'softmax'
    return box

ATTENTION_COST = EvidenceDiagram('ГДЕ ЗДЕСЬ КВАДРАТИЧНЫЙ РОСТ?',
    'Счёт пар позиций и полная стоимость ответа — разные величины.', [
    ('Causal attention', 'Для n позиций с самосвязями число допустимых пар равно n(n+1)/2.',
     'Сравнить длины n и 2n'),
    ('Инференс', 'Prefill обрабатывает вход; decode выдаёт токены по шагам. Их расходы различаются.',
     'Профиль времени по этапам'),
    ('Оптимизация', 'KV cache повторно использует K/V; FlashAttention сокращает переносы.',
     'Память и задержка на тех же входах')],
    'Квадратичность одной операции не описывает всю цену ответа.')

ORDER_FLOW = Diagram('ОТКУДА ВЗЯЛОСЬ ЧИСЛО 42?', [
    ('Вопрос', '1 марта, статус paid?'),
    ('Модель', 'paid_orders'),
    ('Приложение', 'права и схема вызова'),
    ('База', 'count=42'),
    ('Ответ', '42 по заданному фильтру')],
    'Источник числа — база заказов; модель помогает обратиться к ней.')


INTRO_DIAGRAM = EvidenceDiagram('ЧТО ИМЕННО ИЗМЕНИЛОСЬ В СИСТЕМЕ?',
        'Кейс: ответ про 42 заказа мог измениться по четырём причинам.', [
        ('Веса', 'SFT научил строить вызов paid_orders.',
         'Версия модели и новые тесты'),
        ('Контекст', 'В запросе уточнили дату и статус «оплачен».',
         'Точный prompt вызова'),
        ('Индекс', 'Нашли правило: какие заказы считать оплаченными.',
         'ID и версия фрагмента'),
        ('Код', 'Runtime проверил права; БД вернула число 42.',
         'Журнал вызова и ответ БД')],
        'Актуальное число сообщает база; другие компоненты влияют на путь к нему.')

DIAGRAMS = {
    1: TechnicalFigure('model', CONTENT),
    2: TechnicalFigure('neuron', CONTENT),
    3: Diagram('ТЕКСТ СТАНОВИТСЯ ВХОДОМ МОДЕЛИ', [
        ('Строка', '«аромадиффузор»'), ('Токены', '8 фрагментов'),
        ('ID', '8 номеров cl100k_base'), ('Векторы', 'lookup по ID')],
        'Число токенов зависит от токенизатора и самого текста.'),
    4: TechnicalFigure('embedding', CONTENT),
    5: TechnicalFigure('prediction', CONTENT),
    6: IsoFigure('layer'),
    7: ProcessPlate('training'),
    8: TechnicalFigure('generalization', CONTENT),
    9: TechnicalFigure('signals', CONTENT),
    10: EvidenceDiagram('ТРИ СПОСОБА ИЗМЕНИТЬ РЕЗУЛЬТАТ',
        'Для каждого способа меняется свой объект и остаётся свой след.', [
        ('Инструкция', 'Задали формат ответа и правило обращения к инструменту.',
         'Текст prompt и пробный запрос'),
        ('RAG', 'Добавили актуальный документ в индекс и контекст.',
         'Версия и ID фрагмента'),
        ('Fine-tuning', 'На SFT-примерах закрепили устойчивый формат вызова.',
         'Checkpoint и новые тесты')],
        'Выбор зависит от требуемого поведения и частоты обновления данных.'),
    11: TechnicalFigure('reward', CONTENT),
    12: TechnicalFigure('inference', CONTENT),
    13: Diagram('ЧЕТЫРЕ ЗНАЧЕНИЯ СЛОВА «ПАМЯТЬ»', [
        ('Веса', 'обученные параметры'), ('Контекст', 'данные этого вызова'),
        ('Внешняя запись', 'хранилище приложения'), ('KV cache', 'сохранённые ключи и значения')],
        'Это разные ресурсы с разными правилами обновления.', 'stack'),
    14: ProcessPlate('rag'),
    15: EvidenceDiagram('ДВА УРОВНЯ РОУТИНГА',
        'Одинаковое слово описывает выбор на разных границах системы.', [
        ('Внутри MoE', 'В слое токен направлен к двум экспертам из восьми в Mixtral.',
         'Трасса слоя, если доступна'),
        ('В приложении', 'Запрос направили модели, инструменту или ветке процесса.',
         'Журнал решений runtime')],
        'Выбор экспертов внутри модели не равен маршрутизации запросов приложения.'),
    16: Diagram('АГЕНТНЫЙ ЦИКЛ', [
        ('Модель', 'tool_call и аргументы'), ('Runtime', 'права и схема вызова'),
        ('Инструмент', 'запрос к базе'), ('Результат', 'count=42 в контекст')],
        'Факт выполнения подтверждает внешняя система, а не текст ответа.', 'loop'),
    19: Diagram('ОЦЕНКА ПАМЯТИ НЕ ЗАКАНЧИВАЕТСЯ НА ВЕСАХ', [
        ('Параметры', 'сырые веса'), ('KV cache', 'зависит от контекста'),
        ('Буферы', 'обслуживание инференса'), ('Runtime', 'служебные расходы')],
        'Блоки перечисляют статьи расхода и не показывают их относительный размер.', 'stack'),
}


ILLUSTRATIONS = {
    89: ('training_editorial.jpg',
         'Обучение на множестве примеров меняет веса; готовая модель обрабатывает новый запрос без такой настройки.', 390),
    155: ('rag_editorial.jpg',
          'Сведения берут из внешнего источника и передают модели на время ответа; веса при этом не обновляются.'),
    182: ('agent_editorial.jpg',
          'Модель предлагает действие; программа проверяет разрешение, вызывает инструмент и получает результат.'),
}


def image_plate(filename, caption, width=420):
    img = Image(str(ART / filename), width=width, height=width * 2 / 3)
    img.hAlign = 'CENTER'
    return KeepTogether([
        Spacer(1, 7), img,
        Paragraph('Художественная иллюстрация. Метафора, а не схема вычисления. '
                  + esc(caption), CAPTION),
    ])


class TokenExample(Flowable):
    """One verified cl100k_base encoding, with visible token IDs."""

    CHUNKS = ['ар', 'ом', 'ад', 'иф', 'ф', 'у', 'з', 'ор']
    IDS = [17721, 12507, 23680, 62809, 19916, 3865, 9136, 9239]

    def __init__(self):
        super().__init__()
        self.width = CONTENT
        self.height = 118

    def wrap(self, aw, ah):
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.setFillColor(colors.HexColor('#EBEEE6'))
        c.roundRect(0, 0, self.width, self.height, 8, fill=1, stroke=0)
        c.setFont('NotoBold', 9.2)
        c.setFillColor(INK)
        c.drawString(16, self.height - 25, 'ОДНО СЛОВО / ВОСЕМЬ ТОКЕНОВ')
        gap = 5
        cardw = (self.width - 32 - 7 * gap) / 8
        for i, (chunk, ident) in enumerate(zip(self.CHUNKS, self.IDS)):
            x = 16 + i * (cardw + gap)
            c.setFillColor(WHITE)
            c.roundRect(x, 22, cardw, 62, 5, fill=1, stroke=0)
            c.setFillColor(LIME)
            c.rect(x, 22, cardw, 4, fill=1, stroke=0)
            c.setFillColor(INK)
            c.setFont('NotoBold', 13)
            c.drawCentredString(x + cardw / 2, 59, chunk)
            c.setFont('Noto', 7.2)
            c.setFillColor(MID)
            c.drawCentredString(x + cardw / 2, 39, str(ident))
        c.setFont('Noto', 7.3)
        c.setFillColor(MID)
        c.drawString(16, 9, 'Фрагменты показаны сверху, идентификаторы словаря — снизу.')


def token_example_plate():
    return KeepTogether([
        TokenExample(),
        Paragraph('Проверено библиотекой tiktoken 0.14.0 для cl100k_base. '
                  'Номера токенов не содержат значения слова сами по себе [31].', CAPTION),
    ])


def code_example():
    label = style('codelabel', fontName='NotoBold', fontSize=8.6,
                  leading=12, spaceAfter=5)
    code = ParagraphStyle('code', fontName='NotoMono', fontSize=8.2,
                          leading=11, textColor=INK)
    bad = Table([
        [Paragraph('ПОЧЕМУ ПРОВЕРКИ НЕДОСТАТОЧНО', label)],
        [Preformatted('if not order_exists(event_id):\n    create_order(event_id)', code)],
    ], colWidths=[CONTENT])
    bad.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F0EAE5')),
        ('LINEBEFORE', (0, 0), (0, -1), 3, colors.HexColor('#C46E4B')),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    good = Table([
        [Paragraph('ГРАНИЦА УНИКАЛЬНОСТИ В БАЗЕ', label)],
        [Preformatted('CREATE TABLE orders (\n'
                      '  order_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,\n'
                      '  event_id text NOT NULL UNIQUE\n'
                      ');\n'
                      "INSERT INTO orders(event_id) VALUES ('evt-101')\n"
                      'ON CONFLICT (event_id) DO NOTHING;', code)],
    ], colWidths=[CONTENT])
    good.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), PALE),
        ('LINEBEFORE', (0, 0), (0, -1), 3, LIME),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    return [KeepTogether([
        Paragraph('Минимальный фрагмент реализации',
                  style('codesubhead', fontName='NotoBold', fontSize=11.2,
                        leading=15, spaceBefore=12, spaceAfter=8)),
        para('Два обработчика могут одновременно увидеть «заказа ещё нет» и оба '
             'попытаться его создать. Уникальный ключ на уровне базы не даст '
             'записать два заказа для одного event_id.'),
        bad, Spacer(1, 7), good,
        Paragraph('Схема для PostgreSQL: у заказа свой ключ, у события — '
                  'отдельное ограничение UNIQUE. Отметку события и создание '
                  'заказа записывают в одной транзакции; внешние эффекты '
                  'проверяют отдельно. При двух параллельных вызовах с одним '
                  'event_id должна остаться одна запись [32].', CAPTION),
    ])]


def practicum_block(number, title, task, answer):
    heading = style('exerciseheading', fontName='NotoBold', fontSize=10.0,
                    leading=14, textColor=WHITE, spaceAfter=0)
    body = style('exercisebody', fontSize=9.2, leading=13.4, spaceAfter=0)
    table = Table([
        [Paragraph(f'{number:02d}  ' + esc(title), heading)],
        [Paragraph('<b>Задание.</b> ' + esc(task), body)],
    ], colWidths=[CONTENT], hAlign='LEFT')
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), INK),
        ('TEXTCOLOR', (0, 0), (0, 0), WHITE),
        ('BACKGROUND', (0, 1), (0, 1), PALE),
        ('LINEBEFORE', (0, 1), (0, 1), 3, LIME),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    return KeepTogether([table, Spacer(1, 13)])


def get_blocks():
    d = Document(SOURCE)
    for i, b in enumerate(d.element.body):
        if b.tag == qn('w:p'):
            yield i, DocxParagraph(b, d)
        elif b.tag == qn('w:tbl'):
            yield i, DocxTable(b, d)


def build_story():
    blocks = list(get_blocks())
    story = [Spacer(1, H - 3), NextPageTemplate('body'), PageBreak()]
    story.append(Paragraph('Как читать этот учебник', style('introtitle', fontName='NotoBold', fontSize=20, leading=25, spaceAfter=16)))
    for n, text in enumerate(INTRO):
        story.append(para(text, LEAD if n in (0, 1) else BODY))
    story.append(Paragraph('Как читать формулы', style('math-intro-title',
        fontName='NotoBold', fontSize=10.7, leading=14.5, spaceBefore=4,
        spaceAfter=5)))
    story.append(para('Сначала прочитайте смысл обычными словами, затем пройдите '
        'учебный расчёт и вернитесь к общей записи. Буквы нужны, чтобы одно '
        'правило работало для любых данных; числовые примеры показывают один '
        'конкретный случай, а не параметры настоящей LLM.', SMALL))
    story.append(Spacer(1, 13))
    story.append(diagram_plate(INTRO_DIAGRAM))
    story.append(PageBreak())
    story.append(ContentsParagraph('Содержание', style('toctitle', fontName='NotoBold', fontSize=20, leading=26, spaceAfter=20)))
    toc = TableOfContents()
    toc.levelStyles = [TOCSTYLE, TOCATLAS]
    toc.tableStyle = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), .5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), .5),
    ])
    toc.dotsMinLevel = 0
    story.append(toc)
    story.append(Spacer(1, 8))
    story.append(para('Маршрут: основы модели — 1–6; обучение — 7–11; '
                      'инференс и приложение — 12–19; оценка — 20–21; '
                      'затем лаборатория, шесть дополнений и глава 22; '
                      'в конце — шпаргалка.', SMALL))
    story.append(PageBreak())

    current = 0
    after_first_para = False
    for i, block in blocks:
        if i < 35:
            continue
        if isinstance(block, DocxTable):
            story.append(Spacer(1, 7))
            story.append(source_table(block))
            story.append(Spacer(1, 10))
            continue
        p = block
        t = TEXT_OVERRIDES.get(i, p.text).strip()
        t = normalize_terms(t)
        if i in REFERENCE_TITLE_FIXES:
            before, after = REFERENCE_TITLE_FIXES[i]
            assert before in t, (i, before, t)
            t = t.replace(before, after)
        if p.style.name == 'Heading 1':
            match = re.match(r'^(\d+)\s+(.+)', t)
            if not match:
                continue
            current = int(match.group(1))
            after_first_para = False
            if current in (23, 24):
                story.append(PageBreak())
            if current == 7:
                story.append(KeepTogether([
                    ChapterParagraph(t, current),
                    Spacer(1, 6),
                    DIAGRAMS[7],
                    Paragraph('Техническая схема. ' + esc(DIAGRAMS[7].caption), CAPTION),
                    Spacer(1, 9),
                ]))
                after_first_para = True
            else:
                story.append(ChapterParagraph(t, current))
            continue
        if i in FORMULA_GUIDES:
            if i == 204:
                continue  # Attached to its introduction below.
            story.append(formula_block(i))
            story.append(Spacer(1, 7))
            continue
        if not t:
            continue
        if t.startswith('Для лаборатории.'):
            story.append(callout(t))
            if current == 6:
                story.append(Spacer(1, 9))
                story.append(diagram_plate(ATTENTION_COST))
                story.append(Spacer(1, 9))
                story.append(Paragraph('Сквозной пример под капотом',
                    style('examplesubhead', fontName='NotoBold', fontSize=12.3,
                          leading=17, spaceBefore=12, spaceAfter=8)))
                for pnum in (5, 6, 7):
                    detail = TEXT_OVERRIDES.get(pnum, blocks[pnum][1].text)
                    if pnum == 7:
                        detail = detail.replace('Runtime проверяет',
                            'Runtime — программа исполнения приложения — проверяет')
                    story.append(para(detail))
            continue
        if t == 'Агентный цикл с проверкой действия и обновлением состояния':
            continue  # The new cycle diagram already has its own caption.
        if i == 203:
            formula_box = formula_block(204)
            story.append(KeepTogether([para(t), formula_box, Spacer(1, 7)]))
            continue
        if 238 <= i <= 250:
            continue
        if i == 189:
            body = para(t)
            body.glossary_terms = GLOSSARY_PARAGRAPH_TARGETS[i]
            story.append(KeepTogether([body]))
        elif current == 24:
            if t.startswith('[17]'):
                story.append(PageBreak())
                story.append(Paragraph('Первоисточники · продолжение',
                    style('references-continued', fontName='NotoBold',
                          fontSize=11, leading=15, spaceAfter=11)))
            story.append(reference_para(t) if t.startswith('[') else para(t, SMALL))
        elif current == 22 and re.match(r'^\d+\.', t):
            story.append(para(t, style('qa', fontSize=9, leading=13.4, spaceAfter=4)))
        else:
            body = para(t)
            if i in GLOSSARY_PARAGRAPH_TARGETS:
                body.glossary_terms = GLOSSARY_PARAGRAPH_TARGETS[i]
            story.append(body)
        if i == 52:
            story.append(Spacer(1, 6))
            story.append(token_example_plate())
        if i == 188:
            story.extend(code_example())
        if i == 251:
            practice_title = Paragraph('Практикум: три проверки',
                style('practicumtitle', fontName='NotoBold', fontSize=17,
                      leading=23, spaceAfter=10))
            practice_intro = para('Все данные ниже учебные. Выполните действия в тестовой '
                                  'среде, затем сравните свой вывод с приложением «Ответы и критерии проверки».')
            story.append(KeepTogether([
                practice_title, practice_intro, practicum_block(1, *PRACTICUM[0]),
            ]))
            for number, exercise in enumerate(PRACTICUM[1:], 2):
                story.append(practicum_block(number, *exercise))
            story.append(Paragraph('Бланк контрольной трассы', style('trace-form-title',
                fontName='NotoBold', fontSize=11.3, leading=15,
                spaceBefore=9, spaceAfter=7)))
            story.append(para('Для любого задания заполните все четыре поля. '
                'Пустой источник означает, что итоговое утверждение пока не подтверждено.', SMALL))
            form_rows = [[Paragraph(esc(label), TABLEBODY),
                          Paragraph('________________________________________________________________', TABLEBODY)]
                         for label in ('Ожидаемый источник', 'Фактическая трасса',
                                       'Результат проверки', 'Граница вывода')]
            form = Table(form_rows, colWidths=[CONTENT*.32, CONTENT*.68],
                         rowHeights=[42]*4, hAlign='LEFT')
            form.setStyle(TableStyle([
                ('ROWBACKGROUNDS', (0, 0), (-1, -1), [PAPER, colors.HexColor('#EDEFE9')]),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('LINEBELOW', (0, 0), (-1, -1), .5, RULE),
            ]))
            story.append(form)
        if i in ILLUSTRATIONS:
            story.append(image_plate(*ILLUSTRATIONS[i]))
        if i in EXTRA_FIGURES:
            story.append(Spacer(1, 5))
            story.append(diagram_plate(EXTRA_FIGURES[i]))
        if not after_first_para and current in DIAGRAMS:
            story.append(Spacer(1, 6))
            story.append(diagram_plate(DIAGRAMS[current]))
            story.append(Spacer(1, 9))
            after_first_para = True
    for reference in NEW_REFERENCES:
        story.append(reference_para(reference))
    return story


if __name__ == '__main__':
    DEST.parent.mkdir(parents=True, exist_ok=True)
    doc = EditorialDoc(DEST)
    doc.multiBuild(build_story())
    print(DEST)
