"""Vector figures for the companion math and worked-example pages."""

from __future__ import annotations

import html
import math

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Flowable, Paragraph


INK = colors.HexColor('#252B2B')
MID = colors.HexColor('#586160')
LIME = colors.HexColor('#A4D945')
BLUE = colors.HexColor('#3A8997')
AMBER = colors.HexColor('#B98532')
PAPER = colors.HexColor('#F0F2EB')
RULE = colors.HexColor('#CDD2CC')
WHITE = colors.white


class Plot(Flowable):
    def __init__(self, kind: str, width: float, height: float = 190):
        super().__init__()
        self.kind, self.width, self.height = kind, width, height

    def wrap(self, aw, ah):
        return self.width, self.height

    def _text(self, value, x, y, w, h, *, size=7.8, bold=False,
              color=INK, center=False):
        style = ParagraphStyle('plot', fontName='NotoBold' if bold else 'Noto',
            fontSize=size, leading=size*1.22, textColor=color,
            alignment=TA_CENTER if center else 0)
        p = Paragraph(html.escape(str(value), quote=False), style)
        _, ph = p.wrap(w, h)
        if ph > h + .2:
            raise ValueError((self.kind, value, ph, h))
        p.drawOn(self.canv, x, y + (h-ph)/2)

    def draw(self):
        c = self.canv
        c.setFillColor(PAPER)
        c.roundRect(0, 0, self.width, self.height, 6, fill=1, stroke=0)
        if self.kind == 'exp':
            title, xlo, xhi, ymax = 'ПОЛОЖИТЕЛЬНЫЙ ВЕС: exp(z)', -2, 2, 8
            fn = math.exp
            dots = [(0, 1, '0: 1'), (1, math.e, '1: 2,72'), (2, math.e**2, '2: 7,39')]
            xlabel = 'оценка z'
        elif self.kind == 'loss':
            title, xlo, xhi, ymax = 'ШТРАФ: −ln(p)', .05, 1, 3.1
            fn = lambda x: -math.log(x)
            dots = [(.1, -math.log(.1), '0,1: 2,30'), (.8, -math.log(.8), '0,8: 0,22')]
            xlabel = 'вероятность p'
        else:
            raise ValueError(self.kind)
        self._text(title, 13, self.height-27, self.width-26, 18,
                   size=8.7, bold=True)
        x0, y0, x1, y1 = 39, 54, self.width-14, self.height-43
        c.setStrokeColor(RULE)
        c.setLineWidth(.55)
        for fraction in (.25,.5,.75,1):
            y=y0+(y1-y0)*fraction
            c.line(x0,y,x1,y)
        c.setStrokeColor(INK)
        c.line(x0,y0,x1,y0)
        c.line(x0,y0,x0,y1)
        c.setFont('Noto',6.7);c.setFillColor(MID)
        c.drawRightString(x0-4,y0-1,'0')
        c.drawRightString(x0-4,y1-2,f'{ymax:g}'.replace('.', ','))
        c.drawString(x0,y0-11,f'{xlo:g}'.replace('.', ','))
        c.drawRightString(x1,y0-11,f'{xhi:g}'.replace('.', ','))
        c.drawCentredString((x0+x1)/2,33,xlabel)
        def px(x):return x0+(x-xlo)/(xhi-xlo)*(x1-x0)
        def py(y):return y0+y/ymax*(y1-y0)
        path=c.beginPath()
        for i in range(121):
            x=xlo+(xhi-xlo)*i/120
            y=min(ymax,fn(x))
            (path.moveTo if i==0 else path.lineTo)(px(x),py(y))
        c.setStrokeColor(BLUE);c.setLineWidth(2.1);c.drawPath(path,stroke=1)
        for idx,(x,y,label) in enumerate(dots):
            c.setFillColor(LIME if idx==0 else AMBER)
            c.circle(px(x),py(y),3.5,fill=1,stroke=0)
        self._text('Учебные точки: ' + '; '.join(item[2] for item in dots),
                   14, 9, self.width-28, 14, size=6.6, color=MID)


class ProbabilityBars(Flowable):
    def __init__(self, before, after, width):
        super().__init__()
        self.before, self.after = before, after
        self.width, self.height = width, 151

    def wrap(self, aw, ah):return self.width,self.height

    def draw(self):
        c=self.canv
        c.setFillColor(PAPER);c.roundRect(0,0,self.width,self.height,6,fill=1,stroke=0)
        c.setFont('NotoBold',9);c.setFillColor(INK)
        c.drawString(14,self.height-22,'КАК ИЗМЕНИЛОСЬ РАСПРЕДЕЛЕНИЕ')
        c.setFont('Noto',7.5);c.setFillColor(MID)
        c.drawString(110,self.height-40,'до шага')
        c.drawString(300,self.height-40,'после шага')
        names=['я','люблю','чай']
        for i,name in enumerate(names):
            y=self.height-65-i*34
            c.setFillColor(INK);c.setFont('NotoBold',8.4);c.drawString(15,y+5,name)
            for x,p,color in ((110,self.before[i],BLUE),(300,self.after[i],LIME)):
                c.setFillColor(colors.HexColor('#DEE3DB'));c.roundRect(x,y,100,12,3,fill=1,stroke=0)
                c.setFillColor(color);c.roundRect(x,y,100*p,12,3,fill=1,stroke=0)
                c.setFillColor(INK);c.setFont('Noto',7.5);c.drawRightString(
                    x+157,y+2,f'{p:.3f}'.replace('.', ','))


class LossSurface3D(Flowable):
    """An oblique vector rendering of the exact three-token cross-entropy surface."""

    def __init__(self, before_logits, after_logits, width):
        super().__init__()
        self.width, self.height = width, 286
        self.before = self._point(before_logits)
        self.after = self._point(after_logits)

    @staticmethod
    def _loss(x, y):
        maximum = max(0.0, x, y)
        return maximum + math.log(math.exp(-maximum) +
                                  math.exp(x-maximum) + math.exp(y-maximum))

    @classmethod
    def _point(cls, logits):
        x, y = logits[0]-logits[2], logits[1]-logits[2]
        return x, y, cls._loss(x, y)

    def wrap(self, aw, ah):
        return self.width, self.height

    def _project(self, x, y, z=0):
        u = (x+1.5)/4.5
        v = (y+2)/4.5
        return (86+225*u+96*v, 67-22*u+77*v+136*z/4.2)

    @staticmethod
    def _blend(a, b, t):
        return colors.Color(a.red*(1-t)+b.red*t,
                            a.green*(1-t)+b.green*t,
                            a.blue*(1-t)+b.blue*t)

    def _color(self, z):
        low=colors.HexColor('#9BDD73')
        mid=colors.HexColor('#5BB7B7')
        high=colors.HexColor('#EDB96A')
        t=min(1,max(0,z/3.8))
        return self._blend(low,mid,t/.55) if t<.55 else self._blend(mid,high,(t-.55)/.45)

    def _polyline(self, points, color, width):
        c=self.canv
        path=c.beginPath()
        for i,(x,y) in enumerate(points):
            (path.moveTo if i==0 else path.lineTo)(x,y)
        c.setStrokeColor(color);c.setLineWidth(width)
        c.drawPath(path,stroke=1)

    def draw(self):
        c=self.canv
        dark=colors.HexColor('#1D2825')
        grid=colors.HexColor('#45534D')
        ink=colors.HexColor('#E9F2E7')
        c.setFillColor(dark)
        c.roundRect(0,0,self.width,self.height,8,fill=1,stroke=0)
        c.setFillColor(LIME);c.rect(18,self.height-25,15,3,fill=1,stroke=0)
        c.setFont('NotoBold',9.4);c.setFillColor(WHITE)
        c.drawString(41,self.height-28,'ПОВЕРХНОСТЬ ОШИБКИ ОДНОГО УЧЕБНОГО ПРИМЕРА')

        # The floor grid establishes depth independently of the surface color.
        for index in range(5):
            u=index/4
            x=-1.5+4.5*u
            y=-2+4.5*u
            self._polyline([self._project(x,-2),self._project(x,2.5)],grid,.45)
            self._polyline([self._project(-1.5,y),self._project(3,y)],grid,.45)

        # Draw far facets first. The surface is computed, not an illustrative mesh.
        steps=26
        facets=[]
        for i in range(steps):
            for j in range(steps):
                xy=[]
                for a,b in ((i,j),(i+1,j),(i+1,j+1),(i,j+1)):
                    x=-1.5+4.5*a/steps
                    y=-2+4.5*b/steps
                    xy.append((x,y,self._loss(x,y)))
                facets.append((i+j,xy))
        for _,xyz in sorted(facets,key=lambda item:item[0],reverse=True):
            path=c.beginPath()
            for n,(x,y,z) in enumerate(xyz):
                px,py=self._project(x,y,z)
                (path.moveTo if n==0 else path.lineTo)(px,py)
            path.close()
            col=self._color(sum(p[2] for p in xyz)/4)
            c.setFillColor(col)
            c.setStrokeColor(self._blend(col,dark,.18))
            c.setLineWidth(.22)
            c.drawPath(path,fill=1,stroke=1)

        # A few vector iso-lines make the slopes legible at print size.
        line=colors.HexColor('#CBE9C5')
        for fixed in (-1.5,-.6,.3,1.2,2.1,3):
            self._polyline([self._project(fixed,-2+4.5*k/50,
                self._loss(fixed,-2+4.5*k/50)) for k in range(51)],line,.42)
        for fixed in (-2,-1.1,-.2,.7,1.6,2.5):
            self._polyline([self._project(-1.5+4.5*k/50,fixed,
                self._loss(-1.5+4.5*k/50,fixed)) for k in range(51)],line,.42)

        origin=self._project(-1.5,-2)
        axis=colors.HexColor('#D8E7D9')
        self._polyline([origin,self._project(3,-2)],axis,1.15)
        self._polyline([origin,self._project(-1.5,2.5)],axis,1.15)
        self._polyline([origin,self._project(-1.5,-2,4.2)],axis,1.15)

        before=self._project(*self.before)
        after=self._project(*self.after)
        # Dark under-stroke protects the trajectory against both light and dark facets.
        self._polyline([before,after],dark,6)
        self._polyline([before,after],WHITE,2.6)
        angle=math.atan2(after[1]-before[1],after[0]-before[0])
        head=c.beginPath();head.moveTo(*after)
        for offset in (.48,-.48):
            head.lineTo(after[0]-12*math.cos(angle+offset),
                        after[1]-12*math.sin(angle+offset))
        head.close();c.setFillColor(WHITE);c.drawPath(head,fill=1,stroke=0)
        for point,fill in ((before,AMBER),(after,LIME)):
            c.setFillColor(dark);c.circle(*point,7,fill=1,stroke=0)
            c.setFillColor(fill);c.circle(*point,4.3,fill=1,stroke=0)

        c.setFont('NotoBold',7.4);c.setFillColor(ink)
        c.drawString(312,39,'x = z(я) − z(чай)')
        c.drawString(18,216,'loss')
        y_end=self._project(-1.5,2.5)
        c.setFillColor(dark);c.circle(y_end[0]+7,y_end[1]+9,8.7,fill=1,stroke=0)
        c.setFillColor(ink);c.drawCentredString(y_end[0]+7,y_end[1]+6,'y')
        c.setFillColor(AMBER);c.circle(23,19,3.3,fill=1,stroke=0)
        c.setFillColor(ink);c.setFont('Noto',7.6)
        c.drawString(32,16,f'до: {self.before[2]:.3f}'.replace('.', ','))
        c.setFillColor(LIME);c.circle(155,19,3.3,fill=1,stroke=0)
        c.setFillColor(ink);c.drawString(164,16,
            f'после: {self.after[2]:.3f}'.replace('.', ','))
        c.setFillColor(colors.HexColor('#B7C9BE'))
        c.drawRightString(self.width-17,16,'высота = −ln p(«чай»)')


class TraceLine(Flowable):
    def __init__(self,width):
        super().__init__();self.width,self.height=width,165

    def wrap(self,aw,ah):return self.width,self.height

    def draw(self):
        c=self.canv
        c.setFillColor(colors.HexColor('#1D2825'))
        c.roundRect(0,0,self.width,self.height,8,fill=1,stroke=0)
        c.setFillColor(LIME);c.rect(18,self.height-25,15,3,fill=1,stroke=0)
        c.setFillColor(WHITE);c.setFont('NotoBold',9.4)
        c.drawString(41,self.height-28,'ОДНА И ТА ЖЕ ФРАЗА НА ЧЕТЫРЁХ ШАГАХ')
        cards=[
            ('ТЕКСТ','я люблю чай'),
            ('ID ТОКЕНОВ','0, 1, 2'),
            ('КОНТЕКСТ','люблю: строка 2, 1, 0'),
            ('ВЕРОЯТНОСТЬ','p(чай) = 0,090'),
        ]
        cardw=103
        for i,(title,body) in enumerate(cards):
            x=18+i*116
            c.setFillColor(colors.HexColor('#E8F0E7') if i<3 else colors.HexColor('#DDEBC9'))
            c.roundRect(x,49,cardw,75,5,fill=1,stroke=0)
            title_style=ParagraphStyle('trace-title',fontName='NotoBold',fontSize=7.3,
                leading=9.3,textColor=INK)
            body_style=ParagraphStyle('trace-body',fontName='Noto',fontSize=8.2,
                leading=11.1,textColor=INK)
            p=Paragraph(html.escape(title),title_style);_,h=p.wrap(cardw-16,25)
            p.drawOn(c,x+8,103-h)
            p=Paragraph(html.escape(body),body_style);_,h=p.wrap(cardw-16,45)
            if h>43:raise ValueError((title,body,h))
            p.drawOn(c,x+8,77-h)
            if i<3:
                c.setStrokeColor(LIME);c.setFillColor(LIME);c.setLineWidth(1.5)
                c.line(x+cardw+2,86,x+113,86)
                path=c.beginPath();path.moveTo(x+113,86)
                path.lineTo(x+108,89);path.lineTo(x+108,83);path.close()
                c.drawPath(path,fill=1,stroke=0)
        c.setFillColor(colors.HexColor('#C9D5CA'));c.setFont('Noto',7.8)
        c.drawString(18,22,'Правильный следующий токен — «чай»; до обучения модель выше оценивает «я».')


class TemperatureBars(Flowable):
    def __init__(self, width):
        super().__init__()
        self.width,self.height=width,199

    def wrap(self,aw,ah):return self.width,self.height

    def draw(self):
        c=self.canv
        c.setFillColor(PAPER);c.roundRect(0,0,self.width,self.height,6,fill=1,stroke=0)
        c.setFillColor(INK);c.setFont('NotoBold',9)
        c.drawString(14,self.height-23,'ОДНИ LOGITS (2, 1, 0) — РАЗНЫЕ ТЕМПЕРАТУРЫ')
        names=['A','B','C'];colors_by=[LIME,BLUE,AMBER]
        for row,temp in enumerate((.5,1,2)):
            scaled=[2/temp,1/temp,0]
            weights=[math.exp(z-max(scaled)) for z in scaled]
            total=sum(weights);ps=[w/total for w in weights]
            y=self.height-62-row*48
            c.setFillColor(INK);c.setFont('NotoBold',8.5)
            c.drawString(16,y+16,f'T = {temp:g}'.replace('.', ','))
            for j,(name,p,col) in enumerate(zip(names,ps,colors_by)):
                x=95+j*125
                c.setFillColor(col);c.roundRect(x,y,68*p,12,3,fill=1,stroke=0)
                c.setFillColor(INK);c.setFont('Noto',7.7)
                c.drawString(x+73,y+2,f'{name} {p:.3f}'.replace('.', ','))
        c.setFillColor(MID);c.setFont('Noto',7.5)
        c.drawString(15,12,'Меньше T — резче распределение; смысл вариантов и истинность не меняются.')


class ScalingLines(Flowable):
    def __init__(self,width):
        super().__init__();self.width,self.height=width,228

    def wrap(self,aw,ah):return self.width,self.height

    def draw(self):
        c=self.canv
        c.setFillColor(PAPER);c.roundRect(0,0,self.width,self.height,6,fill=1,stroke=0)
        c.setFillColor(INK);c.setFont('NotoBold',9)
        c.drawString(14,self.height-23,'ПРИ УДВОЕНИИ КОНТЕКСТА РАСТУТ РАЗНЫЕ РЕСУРСЫ')
        x0,y0,x1,y1=67,43,self.width-25,self.height-52
        c.setStrokeColor(INK);c.setLineWidth(.8);c.line(x0,y0,x1,y0);c.line(x0,y0,x0,y1)
        c.setFont('Noto',7);c.setFillColor(MID)
        for val in (0,4,8,12,16):
            y=y0+(y1-y0)*val/16
            c.setStrokeColor(RULE);c.line(x0,y,x1,y)
            c.setFillColor(MID);c.drawRightString(x0-6,y-2,f'{val}×')
        lengths=(512,1024,2048)
        base_pairs=512*513/2
        series=[(LIME,[n*(n+1)/2/base_pairs for n in lengths]),
                (BLUE,[n/512 for n in lengths])]
        xs=[x0+(x1-x0)*i/2 for i in range(3)]
        for color,ys in series:
            c.setStrokeColor(color);c.setFillColor(color);c.setLineWidth(2.4)
            path=c.beginPath()
            for i,yval in enumerate(ys):
                y=y0+(y1-y0)*yval/16
                (path.moveTo if i==0 else path.lineTo)(xs[i],y)
                c.circle(xs[i],y,3.4,fill=1,stroke=0)
            c.drawPath(path,stroke=1)
        c.setFillColor(INK);c.setFont('Noto',7.5)
        for x,n in zip(xs,lengths):c.drawCentredString(x,29,str(n))
        c.drawCentredString((x0+x1)/2,14,'число позиций n')
        c.setFillColor(LIME);c.roundRect(75,self.height-41,9,6,2,fill=1,stroke=0)
        c.setFillColor(INK);c.drawString(87,self.height-42,'разрешённые пары attention')
        c.setFillColor(BLUE);c.roundRect(280,self.height-41,9,6,2,fill=1,stroke=0)
        c.setFillColor(INK);c.drawString(292,self.height-42,'слоты KV cache')


class LoraBars(Flowable):
    def __init__(self,width):
        super().__init__();self.width,self.height=width,180

    def wrap(self,aw,ah):return self.width,self.height

    def draw(self):
        c=self.canv
        c.setFillColor(PAPER);c.roundRect(0,0,self.width,self.height,6,fill=1,stroke=0)
        c.setFillColor(INK);c.setFont('NotoBold',9)
        c.drawString(14,self.height-23,'ДОБАВКА РАСТЁТ С РАНГОМ r; БАЗА W ЗАМОРОЖЕНА')
        c.setFont('Noto',7.7);c.setFillColor(MID)
        c.drawString(14,self.height-39,'Одна матрица W: 1000 × 1000 = 1 000 000 коэффициентов')
        for i,r in enumerate((4,8,16,32)):
            y=self.height-66-i*27
            count=r*2000;pct=count/1_000_000*100
            c.setFont('NotoBold',8);c.setFillColor(INK)
            c.drawString(15,y+2,f'r = {r}')
            c.setFillColor(colors.HexColor('#DEE3DB'));c.roundRect(87,y,230,12,3,fill=1,stroke=0)
            c.setFillColor(LIME);c.roundRect(87,y,230*pct/6.4,12,3,fill=1,stroke=0)
            c.setFillColor(INK);c.setFont('Noto',8)
            c.drawString(327,y+1,f'{count:,}'.replace(',',' ')+'  /  '+
                         f'{pct:g}% от W'.replace('.', ','))
