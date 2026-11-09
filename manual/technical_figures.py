"""Vector explanations for the mechanisms that prose alone leaves abstract.

All numbers in toy examples are explicitly labelled as illustrative. The
figures deliberately encode operations, data shapes, or a testable boundary;
they are separate from the book's editorial illustrations.
"""

from __future__ import annotations

import html
import math

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Flowable, Paragraph


BG = colors.HexColor('#1D2825')
PANEL = colors.HexColor('#293732')
PALE = colors.HexColor('#EDF2E8')
MINT = colors.HexColor('#DDEBC9')
BLUE = colors.HexColor('#DCEEEF')
AMBER = colors.HexColor('#F4E7C9')
LIME = colors.HexColor('#B8EA58')
INK = colors.HexColor('#252B2B')
MID = colors.HexColor('#4C5B52')
DIM = colors.HexColor('#B9C9BD')
WHITE = colors.white


class TechnicalFigure(Flowable):
    SPECS = {
        'model': (230, 'МОДЕЛЬ: ФУНКЦИЯ С СОХРАНЁННЫМИ ПАРАМЕТРАМИ',
                  'Вход и выбранный токен меняются при вызове; параметры θ — только при обучении.',
                  'Модель выдаёт оценки продолжений. Проверка прав и чтение базы находятся в приложении.'),
        'neuron': (195, 'ОДНО ВЫЧИСЛИТЕЛЬНОЕ ЗВЕНО',
                   'Учебные числа показывают y = φ(Wx + b), а не реальный нейрон конкретной LLM.',
                   'Параметры сохраняются между вызовами; вход и промежуточные значения зависят от запроса.'),
        'embedding': (205, 'ОТ ID К КОНТЕКСТНОМУ ПРЕДСТАВЛЕНИЮ',
                      'Условный вектор показывает операцию lookup; координаты не имеют готовых словесных названий.',
                      'Исходный эмбеддинг выбирают по ID. Слои преобразуют его с учётом окружения токена.'),
        'prediction': (210, 'ОТ LOGITS К ВЫБОРУ ТОКЕНА',
                       'Учебный словарь из трёх кандидатов; logits (2, 1, 0).',
                       'Вероятность следующего токена не равна вероятности истинности итогового утверждения.'),
        'generalization': (210, 'ПРОВЕРКА ПЕРЕНОСА НА НОВЫЕ СЛУЧАИ',
                           'Train, validation и test выполняют разные роли.',
                           'Почти одинаковые примеры в train и test могут завысить видимое качество.'),
        'signals': (230, 'ТРИ ФОРМЫ ОБУЧАЮЩЕГО СИГНАЛА',
                    'Один запрос x; меняется формат разметки и цель оптимизации.',
                    'SFT, предпочтения и проверяемая награда отвечают на разные вопросы.'),
        'reward': (205, 'НАГРАДА ОБНОВЛЯЕТ ПОВЕДЕНИЕ ЧЕРЕЗ ПРОВЕРКУ',
                   'Кандидат, проверяющий и обновление параметров образуют цикл обучения.',
                   'Слабый проверяющий может награждать ответ, который не решает исходную задачу.'),
        'inference': (200, 'PREFILL И DECODE ИДУТ ПО-РАЗНОМУ',
                      'Показана упрощённая авторегрессионная генерация с KV cache.',
                      'Веса фиксированы. Decode зависит от уже выбранного продолжения.'),
    }

    def __init__(self, kind: str, width: float):
        super().__init__()
        self.kind = kind
        self.width = width
        self.height, self.title, self.subtitle, self.caption = self.SPECS[kind]

    def wrap(self, aw, ah):
        return self.width, self.height

    def text(self, value, x, y, w, h, *, size=8.0, bold=False,
             color=INK, center=False):
        st = ParagraphStyle('technical', fontName='NotoBold' if bold else 'Noto',
                            fontSize=size, leading=size * 1.26,
                            textColor=color, alignment=TA_CENTER if center else 0)
        markup = html.escape(str(value), quote=False).replace('\n', '<br/>')
        p = Paragraph(markup, st)
        _, ph = p.wrap(w, h)
        if ph > h + 0.2:
            raise ValueError((self.kind, value, round(ph, 2), h))
        p.drawOn(self.canv, x, y + (h - ph) / 2)

    def box(self, x, y, w, h, fill=PALE, radius=5):
        c = self.canv
        c.setFillColor(fill)
        c.roundRect(x, y, w, h, radius, fill=1, stroke=0)

    def arrow(self, x1, y1, x2, y2, color=LIME, width=1.5):
        c = self.canv
        c.setStrokeColor(color)
        c.setFillColor(color)
        c.setLineWidth(width)
        c.line(x1, y1, x2, y2)
        a = math.atan2(y2-y1, x2-x1)
        back, wing = 6, 3.2
        p = c.beginPath()
        p.moveTo(x2, y2)
        p.lineTo(x2-back*math.cos(a)+wing*math.sin(a),
                 y2-back*math.sin(a)-wing*math.cos(a))
        p.lineTo(x2-back*math.cos(a)-wing*math.sin(a),
                 y2-back*math.sin(a)+wing*math.cos(a))
        p.close()
        c.drawPath(p, fill=1, stroke=0)

    def base(self):
        c = self.canv
        c.setFillColor(BG)
        c.roundRect(0, 0, self.width, self.height, 9, fill=1, stroke=0)
        c.setFillColor(LIME)
        c.rect(18, self.height-25, 15, 3, fill=1, stroke=0)
        self.text(self.title, 41, self.height-36, self.width-60, 21,
                  size=9.8, bold=True, color=WHITE)
        self.text(self.subtitle, 18, self.height-59, self.width-36, 20,
                  size=7.3, color=DIM)

    def draw(self):
        self.base()
        getattr(self, f'draw_{self.kind}')()

    def draw_model(self):
        # Text enters a parameterized function; application work stays outside.
        self.box(18, 86, 91, 78, BLUE)
        self.text('ВХОД', 28, 141, 71, 16, size=7.7, bold=True)
        self.text('текст и ID\n«Сколько заказов?»', 28, 98, 71, 39, size=7.8)
        self.box(139, 77, 211, 96, PALE)
        self.text('МОДЕЛЬ fθ', 150, 148, 189, 17, size=8.6, bold=True)
        for x, label in [(150, 'эмбеддинг'), (218, 'слои'), (284, 'logits')]:
            self.box(x, 107, 55, 28, MINT, 3)
            self.text(label, x+3, 110, 49, 22, size=7.2, bold=True, center=True)
        self.arrow(206, 121, 216, 121, MID, 1)
        self.arrow(274, 121, 282, 121, MID, 1)
        self.box(380, 86, 89, 78, BLUE)
        self.text('ВЫХОД', 389, 141, 71, 16, size=7.7, bold=True)
        self.text('оценки;\nследующий токен', 389, 100, 71, 35, size=7.8)
        self.arrow(110, 125, 137, 125)
        self.arrow(352, 125, 378, 125)
        self.box(139, 45, 211, 26, AMBER, 3)
        self.text('θ: веса, смещения, эмбеддинги', 151, 48, 188, 20,
                  size=7.6, bold=True, center=True)
        self.arrow(244, 73, 244, 92, MID, 1)
        self.box(18, 15, 211, 22, MINT, 3)
        self.text('ОБУЧЕНИЕ: обновляет θ', 26, 18, 195, 16,
                  size=7.6, bold=True)
        self.box(239, 15, 230, 22, BLUE, 3)
        self.text('ИНФЕРЕНС: использует фиксированные θ', 247, 18, 214, 16,
                  size=7.5, bold=True)

    def draw_neuron(self):
        parts = [
            (18, 59, 91, 63, BLUE, 'Вход x', '(2, 3)'),
            (132, 59, 115, 63, AMBER, 'Параметры', 'W=(0,5; −1)\nb=1'),
            (270, 59, 126, 63, PALE, 'Сумма z', '2·0,5 + 3·(−1) + 1\n= −1'),
            (418, 59, 51, 63, MINT, 'φ(z)', '0'),
        ]
        for x,y,w,h,fill,label,detail in parts:
            self.box(x,y,w,h,fill)
            self.text(label,x+6,y+h-25,w-12,17,size=7.7,bold=True,center=True)
            self.text(detail,x+5,y+7,w-10,h-32,size=7.7,center=True)
        for x1,x2 in [(110,130),(248,268),(397,416)]:
            self.arrow(x1,90,x2,90)
        self.box(18, 11, 211, 38, AMBER)
        self.text('W и b: сохраняемые параметры', 29, 14, 189, 32,
                  size=8.0, bold=True)
        self.box(239, 11, 230, 38, BLUE)
        self.text('x — вход; z и φ(z) — значения этого вызова', 250, 14, 208, 32,
                  size=7.8, bold=True)

    def draw_embedding(self):
        self.box(18, 52, 74, 77, BLUE)
        self.text('ID', 27, 96, 56, 20, size=8.2, bold=True, center=True)
        self.text('t', 27, 72, 56, 20, size=9.0, center=True)
        self.arrow(94,90,111,90)
        self.box(113, 39, 190, 95, PALE)
        self.text('ТАБЛИЦА E: ВЫБОР СТРОКИ', 123, 109, 170, 18,
                  size=7.9, bold=True)
        for i,(lab,val) in enumerate([('E[t−1]','…'),('E[t]','[0,2; −0,3; 0,6; …]'),('E[t+1]','…')]):
            y = 81-i*22
            self.box(123,y,170,19,MINT if i==1 else BLUE,3)
            self.text(lab,127,y+2,43,15,size=7.0,bold=True)
            self.text(val,174,y+2,113,15,size=6.9)
        self.arrow(305,90,328,90)
        self.box(330, 52, 139, 77, MINT)
        self.text('СЛОИ МОДЕЛИ', 340, 101, 119, 18,
                  size=8.0, bold=True, center=True)
        self.text('eₜ и окружение\nдают hₜ(контекст)', 340, 66, 119, 36,
                  size=8.0, center=True)
        self.box(18, 8, 451, 25, AMBER, 3)
        self.text('Числа в E[t] условные; исходный вектор и контекстное представление — разные объекты.',
                  27,11,433,19,size=7.3)

    def draw_prediction(self):
        self.box(18, 58, 111, 89, BLUE)
        self.text('ПРЕФИКС', 28, 123, 91, 17, size=7.9, bold=True)
        self.text('x₁ … xₜ₋₁\nвход вызова', 28, 75, 91, 43, size=8.2)
        self.arrow(131,101,153,101)
        self.box(155, 39, 204, 108, PALE)
        self.text('SOFTMAX(2, 1, 0)', 166, 123, 182, 17,
                  size=8.0,bold=True)
        for i,(label,p,bar) in enumerate([('A', '0,665', 111),('B','0,245',41),('C','0,090',15)]):
            y=99-i*26
            self.text(label,166,y,17,17,size=8,bold=True)
            self.box(188,y+2,bar,13,LIME if i==0 else BLUE,2)
            self.text(p,306,y,42,17,size=7.8)
        self.arrow(361,101,377,101)
        self.box(379, 58, 90, 89, MINT)
        self.text('ВЫБОР', 389, 123, 70, 17,size=7.9,bold=True)
        self.text('greedy: A\nsampling: иногда B',389,78,70,40,size=7.7)
        self.box(18, 8, 451, 25, AMBER,3)
        self.text('p(A)+p(B)+p(C)=1. Эти оценки относятся к токенам, а не к фактической верности ответа.',
                  27,11,433,19,size=7.3)

    def draw_generalization(self):
        rows=[(18,BLUE,'TRAIN','обновляет веса','примеры и варианты'),
              (178,PALE,'VALIDATION','выбирает настройки','новые формулировки'),
              (338,MINT,'TEST','итоговая оценка','новые даты и условия')]
        for x,fill,title,role,example in rows:
            self.box(x,62,131,78,fill)
            self.text(title,x+9,116,113,18,size=8.2,bold=True)
            self.text(role,x+9,90,113,23,size=7.7)
            self.text(example,x+9,67,113,21,size=7.5,color=MID)
        self.arrow(150,101,176,101)
        self.arrow(310,101,336,101)
        self.box(18, 9, 451, 43, AMBER)
        self.text('УТЕЧКА: копия обучающего случая попала в test. Высокий балл теперь не доказывает перенос.',
                  30,12,426,36,size=8.0,bold=True)

    def draw_signals(self):
        rows=[
            ('SFT','(x, y*)','показан желаемый ответ или вызов','−log pθ(y*|x)'),
            ('Предпочтение','(x, y⁺, y⁻)','сравнены два ответа','DPO / RLHF'),
            ('RLVR','(x, y, test)','результат проверен правилом','reward, напр. 0 или 1'),
        ]
        for i,(label,data,meaning,objective) in enumerate(rows):
            y=125-i*45
            self.box(18,y,451,39,PALE if i%2==0 else BLUE)
            self.box(25,y+5,83,29,MINT,3)
            self.text(label,31,y+6,71,25,size=8.1,bold=True,center=True)
            self.text(data,119,y+6,92,27,size=8.3,bold=True)
            self.text(meaning,214,y+4,139,31,size=7.6)
            self.text(objective,359,y+4,101,31,size=7.4,bold=True)
        self.text('x — запрос; y* — эталон; y⁺/y⁻ — предпочитаемый и отвергнутый ответ.',
                  18, 5, 451, 21, size=7.3, color=DIM)

    def draw_reward(self):
        nodes=[(18,BLUE,'КАНДИДАТ','ответ / программа'),
               (160,PALE,'ПРОВЕРЯЮЩИЙ','тест или точный результат'),
               (326,MINT,'НАГРАДА','0 или 1')]
        for x,fill,title,detail in nodes:
            w=122 if x==18 else (141 if x==160 else 143)
            self.box(x,73,w,66,fill)
            self.text(title,x+10,112,w-20,19,size=8,bold=True)
            self.text(detail,x+10,82,w-20,27,size=7.7)
        self.arrow(142,106,158,106)
        self.arrow(303,106,324,106)
        self.box(18,39,451,27,BLUE,3)
        self.text('Результат проверки: градиент и обновление параметров θ',
                  28,43,431,19,size=7.9,bold=True,center=True)
        self.arrow(397,72,397,67,MID,1)
        self.box(18,8,451,24,AMBER,3)
        self.text('Если тест слабый, модель может научиться проходить тест без решения задачи.',
                  28,10,431,20,size=7.5)

    def draw_inference(self):
        self.text('PREFILL: входные позиции обрабатываются вместе',
                  18,115,451,18,size=8.1,bold=True,color=WHITE)
        for i in range(4):
            x=18+i*58
            self.box(x,72,49,32,BLUE,3)
            self.text(f'x{i+1}',x+5,78,39,20,size=8.1,bold=True,center=True)
        self.arrow(251,88,275,88)
        self.box(277,66,192,44,PALE)
        self.text('KV cache для x₁ … x₄',288,74,170,28,
                  size=8.3,bold=True,center=True)
        self.text('DECODE: продолжение зависит от уже выбранных токенов',
                  18,43,451,18,size=8.1,bold=True,color=WHITE)
        for i,(x,label) in enumerate([(18,'y₁'),(124,'y₂'),(230,'y₃')]):
            self.box(x,5,75,32,MINT,3)
            self.text(label,x+7,10,61,22,size=8.5,bold=True,center=True)
            if i<2: self.arrow(x+77,21,x+104,21)
        self.box(338,5,131,32,AMBER,3)
        self.text('те же веса θ',347,9,113,24,size=8.1,bold=True,center=True)
        self.arrow(307,21,336,21)
