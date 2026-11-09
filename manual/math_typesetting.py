"""Small vector math compositor for the nine display equations in the book.

Every glyph is checked against the embedded font before layout. Variables use
serif italic, function names serif roman, and operators a complete math font.
The equations remain selectable text in the PDF.
"""

from __future__ import annotations

from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import Flowable
from reportlab.lib.colors import HexColor


VAR = 'NotoSerifItalic'
ROMAN = 'NotoSerif'
MATH = 'MathFull'


class Box:
    width: float
    top: float
    bottom: float

    def draw(self, canvas, x: float, baseline: float) -> None:
        raise NotImplementedError


class Text(Box):
    def __init__(self, value: str, font: str, size: float = 13):
        face = pdfmetrics.getFont(font).face
        missing = [char for char in value if ord(char) not in face.charWidths]
        if missing:
            raise ValueError(f'{font} lacks {missing!r} in {value!r}')
        self.value, self.font, self.size = value, font, size
        self.width = pdfmetrics.stringWidth(value, font, size)
        self.top, self.bottom = size * .82, -size * .25

    def draw(self, canvas, x, baseline):
        canvas.setFont(self.font, self.size)
        canvas.drawString(x, baseline, self.value)


class Space(Box):
    def __init__(self, width: float):
        self.width, self.top, self.bottom = width, 0, 0

    def draw(self, canvas, x, baseline):
        pass


class Row(Box):
    def __init__(self, *parts: Box):
        self.parts = parts
        self.width = sum(part.width for part in parts)
        self.top = max((part.top for part in parts), default=0)
        self.bottom = min((part.bottom for part in parts), default=0)

    def draw(self, canvas, x, baseline):
        for part in self.parts:
            part.draw(canvas, x, baseline)
            x += part.width


class Scripts(Box):
    def __init__(self, base: Box, *, sub: Box | None = None,
                 sup: Box | None = None):
        self.base, self.sub, self.sup = base, sub, sup
        self.script_x = base.width - .8
        self.sub_y, self.sup_y = -5.0, 7.5
        self.width = max(base.width, self.script_x +
                         max((part.width for part in (sub, sup) if part), default=0))
        self.top = max(base.top, self.sup_y + sup.top if sup else base.top)
        self.bottom = min(base.bottom, self.sub_y + sub.bottom if sub else base.bottom)

    def draw(self, canvas, x, baseline):
        self.base.draw(canvas, x, baseline)
        if self.sub:
            self.sub.draw(canvas, x + self.script_x, baseline + self.sub_y)
        if self.sup:
            self.sup.draw(canvas, x + self.script_x, baseline + self.sup_y)


class Fraction(Box):
    def __init__(self, numerator: Box, denominator: Box):
        self.numerator, self.denominator = numerator, denominator
        self.width = max(numerator.width, denominator.width) + 10
        self.num_y = 7 - numerator.bottom
        self.den_y = -7 - denominator.top
        self.top = self.num_y + numerator.top
        self.bottom = self.den_y + denominator.bottom

    def draw(self, canvas, x, baseline):
        self.numerator.draw(canvas,
                            x + (self.width - self.numerator.width) / 2,
                            baseline + self.num_y)
        self.denominator.draw(canvas,
                              x + (self.width - self.denominator.width) / 2,
                              baseline + self.den_y)
        canvas.setLineWidth(.8)
        canvas.line(x + 1, baseline, x + self.width - 1, baseline)


class Radical(Box):
    def __init__(self, radicand: Box):
        self.sign = Text('√', MATH, 17)
        self.radicand = radicand
        self.width = self.sign.width + radicand.width + 3
        self.top = max(self.sign.top, radicand.top + 3, 15)
        self.bottom = min(self.sign.bottom, radicand.bottom)

    def draw(self, canvas, x, baseline):
        self.sign.draw(canvas, x, baseline)
        start = x + self.sign.width
        self.radicand.draw(canvas, start + 1, baseline)
        canvas.setLineWidth(.65)
        canvas.line(start, baseline + 14, x + self.width, baseline + 14)


class Limits(Box):
    def __init__(self, symbol: str, *, lower: Box, upper: Box | None = None):
        self.symbol = Text(symbol, MATH, 22)
        self.lower, self.upper = lower, upper
        self.width = max(self.symbol.width, lower.width,
                         upper.width if upper else 0) + 2
        self.lower_y = self.symbol.bottom - lower.top - 2
        self.upper_y = (self.symbol.top - upper.bottom + 2) if upper else 0
        self.top = max(self.symbol.top,
                       self.upper_y + upper.top if upper else self.symbol.top)
        self.bottom = self.lower_y + lower.bottom

    def draw(self, canvas, x, baseline):
        for part, y in ((self.symbol, 0), (self.lower, self.lower_y),
                        (self.upper, self.upper_y)):
            if part:
                part.draw(canvas, x + (self.width - part.width) / 2,
                          baseline + y)


class Equation(Flowable):
    def __init__(self, expression: Box, available_width: float):
        super().__init__()
        self.expression = expression
        self.width = available_width
        if expression.width > available_width - 8:
            raise ValueError(f'Equation exceeds column: {expression.width:.1f}')
        self.height = max(46, expression.top - expression.bottom + 16)

    def wrap(self, available_width, available_height):
        return self.width, self.height

    def draw(self):
        baseline = (self.height - (self.expression.top -
                                   self.expression.bottom)) / 2 - self.expression.bottom
        self.canv.saveState()
        try:
            self.canv.setFillColor(HexColor('#252B2B'))
            self.canv.setStrokeColor(HexColor('#252B2B'))
            self.expression.draw(self.canv,
                                 (self.width - self.expression.width) / 2,
                                 baseline)
        finally:
            self.canv.restoreState()


def v(value, size=13):
    return Text(value, VAR, size)


def u(value, size=13):
    return Text(value, ROMAN, size)


def m(value, size=13):
    return Text(value, MATH, size)


def sp(width=4):
    return Space(width)


def row(*parts):
    return Row(*parts)


def sub(base, below):
    return Scripts(base, sub=below)


def sup(base, above):
    return Scripts(base, sup=above)


def formula(index: int, width: float) -> Equation:
    """Build each equation from the same typographic primitives."""
    x_t = sub(v('x'), v('t', 8.7))
    x_before_t = sub(v('x'), row(m('<', 8.7), v('t', 8.7)))
    p_theta = sub(v('P'), v('θ', 8.7))

    if index == 44:
        expr = row(v('y'), sp(), m('='), sp(), v('φ'), u('('), v('Wx'),
                   sp(3), m('+'), sp(3), v('b'), u(')'))
    elif index == 66:
        product = Limits('∏', lower=row(v('t', 8.7), m('=', 8.7),
                                        u('1', 8.7)), upper=v('T', 8.7))
        expr = row(v('P'), u('('), sub(v('x'), u('1', 8.7)), u(','), sp(3),
                   m('…'), u(','), sp(3), sub(v('x'), v('T', 8.7)), u(')'),
                   sp(), m('='), sp(), product, sp(3), p_theta, u('('),
                   x_t, sp(3), m('|'), sp(3), x_before_t, u(')'))
    elif index == 70:
        numerator = sup(u('e'), sub(v('z', 9), v('i', 7)))
        denominator = row(Limits('∑', lower=v('j', 9)), sp(2),
                          sup(u('e'), sub(v('z', 9), v('j', 7))))
        expr = row(sub(v('p'), v('i', 8.7)), sp(4), m('='), sp(4),
                   Fraction(numerator, denominator))
    elif index == 79:
        qkt = sup(row(v('Q'), v('K')), v('T', 8.7))
        score = row(Fraction(qkt, Radical(sub(v('d'), v('k', 8.7)))),
                    sp(3), m('+'), sp(3), v('M'))
        expr = row(u('Attention'), u('('), v('Q'), u(','), sp(3), v('K'),
                   u(','), sp(3), v('V'), u(')'), sp(4), m('='), sp(4),
                   u('softmax'), u('('), score, u(')'), v('V'))
    elif index == 88:
        expr = row(sub(v('L'), v('t', 8.7)), sp(4), m('='), sp(4), m('−'),
                   u('log'), sp(4), p_theta, u('('), x_t, sp(3), m('|'),
                   sp(3), x_before_t, u(')'))
    elif index == 92:
        expr = row(v('θ'), sp(5), m('←'), sp(5), v('θ'), sp(4), m('−'),
                   sp(4), v('η'), sub(m('∇'), v('θ', 8.7)), v('L'))
    elif index == 118:
        expr = row(v('W′'), sp(4), m('='), sp(4), v('W'), sp(4), m('+'),
                   sp(4), v('sBA'), u(','), sp(12), u('rank'), u('('),
                   v('BA'), u(')'), sp(3), m('≤'), sp(3), v('r'))
    elif index == 165:
        experts = Limits('∑', lower=row(v('i', 8.7), m('∈', 8.7),
                                        v('S', 8.7), u('(', 8.7),
                                        v('x', 8.7), u(')', 8.7)))
        expr = row(v('y'), sp(4), m('='), sp(4), experts, sp(2),
                   sub(v('g'), v('i', 8.7)), u('('), v('x'), u(')'),
                   sub(v('E'), v('i', 8.7)), u('('), v('x'), u(')'))
    elif index == 204:
        expr = row(u('Memory'), u('('), v('weights'), u(')'), sp(4),
                   m('≈'), sp(4), v('N'), sp(4), m('×'), sp(4),
                   Fraction(u('bits per parameter', 11.5), u('8', 11.5)))
    else:
        raise KeyError(index)
    return Equation(expr, width)
