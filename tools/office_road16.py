#!/usr/bin/env python3
"""Набор «Офис» для гонки × 16/32-bit «псевдо-3D» (#138), зеркало `space_road16.py` и
`pixel_road16.py`: те же ключи, размеры холстов и порядок кадров, чтобы `racing_bit16.gd` брала
их без правок. Герой едет на почтовой тележке на колёсиках (вид сзади): синий брезентовый короб
в раме из труб, четыре колёсика на вилках, поперёк ручка для толкания, на борту белый конверт и
табличка цвета экипажа, из короба торчат письма, посылка и тубус, на заднем углу короткий хлыст
с флажком (всё ниже головы клерка, без мачт и парусов: паруса только у пиратов); в коробе сидит
клерк в белой рубашке, красный галстук закинуло за плечо. Соперники на офисных креслах: высокая
спинка цвета экипажа с листком на скотче, подлокотники, газлифт и крестовина с роликами, в
кресле сотрудник в чёрном костюме, усы шире головы, в руке жёлтая папка. У дороги фикус в
горшке и вешалка с плащом вместо пальм, рабочее место с перегородками вместо хижины, принтер,
кулер, указатели раскладной табличкой «мокрый пол». На горизонте стена окон с городом и
потолок с лампами, ряды перегородок с мониторами и серверная стойка, ковролин опенспейса
плитками вместо моря. Дорога из линолеума с жёлто-чёрной лентой по краю, обочина ковролин.

Тележка, кресла и пропы в палитре `office16.PALETTE`, горизонт в своей (`OFFICE_SKY`), цвета
дороги лентой `road_colors` по местам `ROAD_COLORS`.

    python3 tools/office_road16.py --preview out.png
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import office16  # noqa: E402
from office16 import (Canvas, strip, K, NAVY, SEA, AQUA, SKY, WHITE, GREY, SKIN, TAN, GOLD, BRASS,  # noqa: E402
                      METAL, DARK, RED, VIOLET, PLUM)

# Палитра горизонта: небо за окнами, облака и потолок, ковролин, перегородки. Места те же по
# смыслу, что у пиратов и космоса.
S0, S1, S2, S3, C0, C1, C2, M0, M1, M2, M3, I0, I1, I2, I3, SUN = range(16)
OFFICE_SKY = [
    (0x6A, 0xA4, 0xDA),  # S0  небо за окном наверху
    (0x88, 0xBA, 0xE4),  # S1
    (0xAA, 0xD0, 0xEE),  # S2
    (0xD0, 0xE6, 0xF4),  # S3  небо у горизонта
    (0xB6, 0xC6, 0xDA),  # C0  дальние дома в дымке, тень облака и потолка
    (0xE2, 0xEA, 0xF2),  # C1  облако, плитка потолка
    (0xFC, 0xFD, 0xFF),  # C2  свет ламп, бумага
    (0x2A, 0x60, 0x5C),  # M0  ковролин вдали
    (0x3A, 0x7A, 0x6E),  # M1  ковролин
    (0x48, 0x90, 0x7C),  # M2  ковролин у дороги
    (0x24, 0x36, 0x48),  # M3  рамы окон, швы, корпуса техники
    (0x86, 0x9E, 0xC0),  # I0  ближние дома, дальний ряд перегородок
    (0x31, 0x4A, 0x92),  # I1  ткань перегородок
    (0xB7, 0xBF, 0xCF),  # I2  кромка перегородок, пластик
    (0x58, 0xB2, 0xDC),  # I3  экраны и огни
    (0x4F, 0x9C, 0x86),  # SUN ковролин у кромки дороги
]

# Цвета дороги по местам ленты `road_colors` (демка берёт их по индексу).
ROAD_COLORS = [
    (0x9A, 0xA0, 0xAE),  # 0 линолеум светлый
    (0x8E, 0x94, 0xA4),  # 1 линолеум тёмный
    (0xF6, 0xCD, 0x4C),  # 2 лента по краю жёлтая
    (0x2E, 0x31, 0x40),  # 3 лента по краю чёрная
    (0xF4, 0xF5, 0xF8),  # 4 разметка
    (0x4F, 0x9C, 0x86),  # 5 ковролин светлый
    (0x46, 0x8E, 0x7A),  # 6 ковролин тёмный
    (0x2A, 0x60, 0x5C),  # 7 дымка вдали
]


def _wset(c, x, y, col):
    c.set(int(math.floor(x)) % c.w, y, col)


def _wrect(c, x0, y0, x1, y1, col):
    for y in range(int(y0), int(y1) + 1):
        for x in range(int(x0), int(x1) + 1):
            _wset(c, x, y, col)


def _wellipse(c, cx, cy, rx, ry, col):
    for y in range(int(cy - ry - 1), int(cy + ry + 2)):
        for x in range(int(cx - rx - 1), int(cx + rx + 2)):
            if ((x - cx) / max(rx, 0.5)) ** 2 + ((y - cy) / max(ry, 0.5)) ** 2 <= 1.0:
                _wset(c, x, y, col)


# --- Горизонт ----------------------------------------------------------------------------------

def sky():
    """Стена окон во всю высоту, 512×128, стыкуется по краям: сверху полоса подвесного потолка с
    лампами, за стеклом дневное небо с облаками и город в два плана, поверх рамы окон."""
    rng = random.Random(271)
    c = Canvas(512, 128)
    bands = [(0, S0), (44, S1), (76, S2), (102, S3)]
    for y in range(128):
        col = S0
        for start, b in bands:
            if y >= start:
                col = b
        for x in range(512):
            cc = col
            for i, (start, b) in enumerate(bands[1:]):
                if start <= y < start + 3 and (x + y) % 2 == 0:
                    cc = bands[i][1]
            c.set(x, y, cc)
    # Облака: плоское дно, комья сверху, свет по верхней кромке.
    for cx, cy, w in ((70, 46, 30), (214, 60, 22), (330, 40, 34), (452, 66, 24), (150, 84, 18)):
        for dx, r in ((-w * 0.5, w * 0.34), (0, w * 0.5), (w * 0.5, w * 0.3)):
            _wellipse(c, cx + dx, cy - r * 0.35, r, r * 0.5, C1)
            _wellipse(c, cx + dx - 1, cy - r * 0.55, r * 0.7, r * 0.25, C2)
        _wrect(c, cx - w * 0.8, cy, cx + w * 0.8, cy + 1, C0)
    # Город: дальние дома в дымке, ближние темнее с рядами окон, антенны и баки на крышах.
    x = 0
    while x < 512:
        w = rng.randint(14, 30)
        top = rng.randint(78, 104)
        _wrect(c, x, top, x + w - 2, 127, C0)
        if rng.random() < 0.4:
            _wrect(c, x + w // 2, top - 6, x + w // 2, top, C0)
        for wy in range(top + 3, 127, 5):
            for wx in range(x + 2, x + w - 3, 4):
                _wset(c, wx, wy, S3)
        x += w
    x = 6
    while x < 500:
        w = rng.randint(18, 34)
        top = rng.randint(92, 114)
        _wrect(c, x, top, x + w, 127, I0)
        _wrect(c, x, top, x + w, top, C0)
        if rng.random() < 0.5:
            _wrect(c, x + 3, top - 4, x + 9, top, I0)
        for wy in range(top + 4, 127, 6):
            for wx in range(x + 3, x + w - 2, 5):
                _wrect(c, wx, wy, wx + 1, wy + 1, S3 if (wx + wy) % 3 else C2)
        x += w + rng.randint(4, 26)
    # Рамы: толстые стойки каждые 128, тонкие между ними, перекладина под потолком.
    for x0 in range(0, 512, 128):
        _wrect(c, x0 - 2, 14, x0 + 2, 127, M3)
        _wrect(c, x0 + 3, 14, x0 + 3, 127, I2)
        _wrect(c, x0 + 64, 14, x0 + 64, 127, M3)
    _wrect(c, 0, 30, 511, 31, M3)
    # Жалюзи, спущенные на треть в двух окнах.
    for x0 in (132, 388):
        for y in range(16, 30, 3):
            _wrect(c, x0, y, x0 + 59, y + 1, C1)
            _wrect(c, x0, y + 2, x0 + 59, y + 2, C0)
    # Потолок: плитки со швами и длинные лампы.
    _wrect(c, 0, 0, 511, 11, C1)
    _wrect(c, 0, 12, 511, 13, C0)
    _wrect(c, 0, 14, 511, 15, M3)
    for x0 in range(0, 512, 32):
        _wrect(c, x0, 0, x0, 11, C0)
    _wrect(c, 0, 5, 511, 5, C0)
    for x0 in range(40, 512, 128):
        _wrect(c, x0, 7, x0 + 46, 10, C2)
        _wrect(c, x0 - 1, 11, x0 + 47, 11, I2)
    return c


def _far_cubicle(c, x0, w, top, monitor):
    """Отсек дальнего ряда: стенка в дымке со светлой кромкой, над ней экран."""
    _wrect(c, x0, top, x0 + w, 39, I0)
    _wrect(c, x0, top, x0 + w, top, I2)
    _wrect(c, x0, top, x0, 39, I2)
    if monitor:
        mx = x0 + w // 2
        _wrect(c, mx - 4, top - 7, mx + 4, top - 2, M3)
        _wrect(c, mx - 3, top - 6, mx + 3, top - 3, I3)
        _wset(c, mx, top - 1, M3)


def islands():
    """Ряды перегородок на горизонте, 512×40, прозрачный верх: дальний ряд в дымке, ближний
    синей тканью с мониторами, лампами и фикусами, серверная стойка с мигалкой, кулер и
    колонна с часами."""
    rng = random.Random(272)
    c = Canvas(512, 40)
    x = 0
    while x < 512:
        w = rng.randint(20, 30)
        _far_cubicle(c, x, min(w, 511 - x), rng.choice((24, 25, 26)), rng.random() < 0.6)
        x += w + 1
    # Ближний ряд: отсеки группами с проходами между ними.
    for x0, x1 in ((8, 120), (150, 262), (348, 500)):
        x = x0
        while x < x1 - 20:
            w = rng.randint(24, 34)
            top = rng.choice((29, 30))
            _wrect(c, x, top, x + w, 39, I1)
            _wrect(c, x, top, x + w, top, I2)
            _wrect(c, x + w, top, x + w, 39, M3)
            for sx in range(x + 4, x + w - 2, 6):
                _wset(c, sx, top + 3, I0)
                _wset(c, sx + 3, top + 6, I0)
            kind = rng.randint(0, 3)
            mx = x + w // 2
            if kind < 2:
                # Монитор со светящимся экраном.
                _wrect(c, mx - 6, top - 10, mx + 6, top - 2, M3)
                _wrect(c, mx - 5, top - 9, mx + 5, top - 4, I3)
                _wrect(c, mx - 4, top - 8, mx - 1, top - 8, C2)
                _wrect(c, mx - 1, top - 1, mx + 1, top - 1, M3)
            elif kind == 2:
                # Фикус: горшок и крона.
                _wrect(c, mx - 2, top - 3, mx + 2, top - 1, I2)
                _wellipse(c, mx, top - 8, 5, 5, M1)
                _wellipse(c, mx - 1, top - 9, 3, 3, SUN)
            else:
                # Стопка папок.
                _wrect(c, mx - 5, top - 5, mx + 5, top - 1, C1)
                for sx in range(mx - 4, mx + 5, 3):
                    _wrect(c, sx, top - 5, sx, top - 1, C0)
            x += w + 1
    # Серверная стойка с мигалкой в проходе.
    _wrect(c, 290, 10, 312, 39, M3)
    _wrect(c, 290, 10, 312, 10, I2)
    for y in range(13, 38, 4):
        _wrect(c, 293, y, 309, y + 1, I0)
        _wset(c, 294, y, I3)
        _wset(c, 297, y, C2 if y % 8 else I3)
        _wset(c, 307, y, I3)
    _wrect(c, 299, 6, 303, 9, I3)
    _wrect(c, 300, 5, 302, 5, C2)
    _wrect(c, 297, 10, 305, 10, I2)
    # Кулер рядом со стойкой.
    _wrect(c, 322, 24, 330, 39, C1)
    _wrect(c, 322, 24, 322, 39, C2)
    _wrect(c, 323, 15, 329, 23, I3)
    _wrect(c, 324, 16, 325, 21, C2)
    _wrect(c, 324, 13, 328, 14, I3)
    _wrect(c, 325, 28, 327, 29, M3)
    # Колонна с часами в другом проходе.
    _wrect(c, 128, 0, 142, 39, C1)
    _wrect(c, 141, 0, 142, 39, C0)
    _wellipse(c, 135, 14, 5, 5, M3)
    _wellipse(c, 135, 14, 4, 4, C2)
    _wrect(c, 135, 11, 135, 14, M3)
    _wrect(c, 135, 14, 137, 14, M3)
    return c


def sea():
    """Ковролин опенспейса от горизонта, 512×24: тёмный вдали, светлее у дороги, швы плиток
    сходятся вдаль, ворс крапом, кое-где оброненные листы; у нижней кромки полоса обочины."""
    rng = random.Random(273)
    c = Canvas(512, 24)
    for y in range(24):
        col = M0 if y < 5 else (M1 if y < 14 else M2)
        c.rect(0, y, 511, y, col)
        if y in (5, 14):
            for x in range(0, 512, 2):
                c.set(x + (y % 2), y, M0 if y == 5 else M1)
    c.rect(0, 22, 511, 23, SUN)
    # Швы плиток: поперечные чаще к горизонту, продольные штрихами тем реже, чем ближе.
    rows = (2, 4, 7, 11, 16, 21)
    for i, y in enumerate(rows):
        for x in range(512):
            if (x + i * 3) % 4 < 2:
                c.set(x, y, M3 if y < 6 else (M0 if y < 15 else M1))
    for i in range(len(rows) - 1):
        step = 16 + i * 12
        while 512 % step:
            step += 1
        for x in range((i * 7) % step, 512, step):
            for y in range(rows[i] + 1, rows[i + 1]):
                _wset(c, x + (y - rows[i]) * (0.5 if x > 256 else -0.5), y, M3 if y < 6 else (M0 if y < 15 else M1))
    for _ in range(90):
        y = rng.randint(1, 20)
        _wset(c, rng.uniform(0, 512), y, M1 if y < 6 else (M2 if y < 14 else SUN))
    # Оброненные листы бумаги: плоские белые ромбики с тенью.
    for _ in range(9):
        y = rng.randint(6, 19)
        x = rng.uniform(0, 512)
        w = 2 + y // 6
        for i in range(-w, w + 1):
            _wset(c, x + i, y, C2)
            _wset(c, x + i + 1, y + 1, M3)
        for i in range(-w + 1, w):
            _wset(c, x + i + 1, y - 1, C1)
    return c


# --- Тележка, кресла и пропы (палитра спрайтов) -------------------------------------------------

def _caster(c, cx, cy, r, phase, fork_top):
    """Колёсико тележки сзади: вилка от рамы, широкая резиновая шина, полоски протектора бегут
    вниз (`phase` 0..1)."""
    w = 7
    c.rect(cx - w - 2, fork_top, cx + w + 2, fork_top + 4, METAL)
    c.rect(cx - w - 2, fork_top, cx - w, cy, METAL)
    c.rect(cx + w, fork_top, cx + w + 2, cy, METAL)
    c.rect(cx - w + 1, cy - r + 3, cx + w - 1, cy + r - 3, K)
    c.rect(cx - w + 3, cy - r, cx + w - 3, cy + r, K)
    c.rect(cx - w + 3, cy - r + 3, cx + w - 3, cy + r - 3, DARK)
    c.rect(cx - w + 3, cy - r + 3, cx - w + 4, cy + r - 3, METAL)
    step = 6
    off = int(phase * step)
    for y in range(int(cy - r + 3) + off, int(cy + r - 3), step):
        c.rect(cx - w + 4, y, cx + w - 4, y + 1, K)
        c.rect(cx - w + 4, y + 2, cx + w - 4, y + 2, METAL)
    c.rect(cx - w - 3, cy - 2, cx - w - 1, cy + 2, GREY)
    c.rect(cx + w + 1, cy - 2, cx + w + 3, cy + 2, GREY)


def _envelope(c, x, y, w, h):
    """Конверт: белый прямоугольник с клапаном галочкой."""
    c.rect(x, y, x + w, y + h, WHITE)
    c.line(x, y, x + w / 2, y + h * 0.55, GREY, 1)
    c.line(x + w, y, x + w / 2, y + h * 0.55, GREY, 1)
    c.rect(x, y + h, x + w, y + h, GREY)


def mail_cart(lean, phase, accent):
    """Почтовая тележка со спины, 160×104: синий брезентовый короб в раме из труб, под ним полка
    с посылкой и четыре колёсика (видны задние), поперёк ручка, на борту конверт и табличка
    цвета `accent`, по углам отражатели; из короба торчат письма, посылка и тубус, на углу
    короткий хлыст с флажком (всё ниже головы, без мачты); в коробе клерк со спины.
    `lean` −1..1 крен."""
    c = Canvas(160, 104)
    sh = lean * 6
    wob = 1 if phase >= 0.5 else 0
    # Колёсики и нижняя полка с посылкой.
    for wx in (26, 134):
        _caster(c, wx + sh * 0.3, 86, 15, phase, 66)
    c.rect(36 + sh * 0.4, 84, 124 + sh * 0.4, 88, METAL)
    c.rect(36 + sh * 0.4, 84, 124 + sh * 0.4, 84, GREY)
    c.rect(52 + sh * 0.4, 70, 84 + sh * 0.4, 83, BRASS)
    c.rect(52 + sh * 0.4, 70, 84 + sh * 0.4, 71, GOLD)
    c.rect(66 + sh * 0.4, 70, 70 + sh * 0.4, 83, TAN)
    c.rect(90 + sh * 0.4, 75, 112 + sh * 0.4, 83, WHITE)
    c.rect(90 + sh * 0.4, 78, 112 + sh * 0.4, 78, GREY)
    c.rect(90 + sh * 0.4, 81, 112 + sh * 0.4, 81, GREY)
    for x in (40, 120):
        c.rect(x + sh * 0.5 - 2, 66, x + sh * 0.5 + 2, 86, METAL)
    # Короб: брезент трапецией, швы и складки, рама по кромкам.
    c.poly([(24 + sh, 42), (136 + sh, 42), (130 + sh * 0.6, 68), (30 + sh * 0.6, 68)], SEA)
    for x in (52, 108):
        c.line(x + sh, 44, x + sh * 0.6 + (2 if x < 80 else -2), 67, NAVY, 1)
    c.line(27 + sh * 0.9, 50, 133 + sh * 0.9, 50, NAVY, 1)
    for x in range(30, 132, 6):
        c.set(x + sh * 0.9, 52, AQUA)
    c.rect(28 + sh * 0.6, 66, 132 + sh * 0.6, 70, METAL)
    c.rect(28 + sh * 0.6, 66, 132 + sh * 0.6, 66, GREY)
    c.rect(22 + sh, 40, 138 + sh, 44, METAL)
    c.rect(24 + sh, 41, 136 + sh, 41, SKY)
    # Конверт-эмблема и табличка цвета экипажа.
    ex = 68 + sh * 0.8
    _envelope(c, ex, 53, 24, 11)
    c.rect(ex + 26, 55, ex + 34, 62, DARK)
    c.rect(ex + 27, 56, ex + 33, 61, accent)
    c.rect(ex - 10, 55, ex - 2, 62, DARK)
    c.rect(ex - 9, 56, ex - 3, 61, accent)
    # Отражатели по углам.
    for x in (36, 124):
        c.rect(x + sh * 0.8 - 4, 54, x + sh * 0.8 + 4, 60, DARK)
        c.rect(x + sh * 0.8 - 3, 55, x + sh * 0.8 + 3, 59, RED if accent != RED else GOLD)
    # Груз слева: пачка писем веером, перетянутая резинкой.
    lx = 34 + sh * 1.1
    for i, dx in enumerate((0, 6, 12)):
        _envelope(c, lx + dx, 30 - i * 2 + (wob if i == 2 else 0), 12, 12 + i * 2)
    c.rect(lx, 37, lx + 24, 38, RED)
    # Груз справа: посылка в скотче и тубус.
    rx = 100 + sh * 1.1
    c.rect(rx, 29, rx + 20, 41, BRASS)
    c.rect(rx, 29, rx + 20, 30, GOLD)
    c.rect(rx + 8, 29, rx + 11, 41, TAN)
    c.rect(rx + 13, 33, rx + 18, 37, WHITE)
    c.line(rx + 24, 41, rx + 27, 27 - wob, GOLD, 4)
    c.rect(rx + 25, 25 - wob, rx + 29, 27 - wob, WHITE)
    # Короткий хлыст с флажком цвета экипажа у заднего угла: ниже головы клерка.
    flap = 2 * math.sin(phase * math.pi * 2)
    c.rect(136 + sh * 1.2, 26, 137 + sh * 1.2, 41, METAL)
    c.poly([(138 + sh * 1.2, 26), (148 + sh * 1.2, 29 + flap), (138 + sh * 1.2, 33)], accent)
    # Клерк со спины: белая рубашка, складка по хребту, лента бейджа, руки на кромке короба.
    x0 = 72 + sh * 1.2
    c.rect(x0 - 1, 23, x0 + 17, 41, WHITE)
    c.rect(x0 + 8, 28, x0 + 8, 40, GREY)
    c.rect(x0 + 2, 34, x0 + 5, 34, GREY)
    c.rect(x0 + 11, 36, x0 + 14, 36, GREY)
    for side in (-1, 1):
        sx = x0 + (0 if side < 0 else 16)
        c.ellipse(sx, 26, 4, 4, WHITE)
        c.line(sx, 26, sx + side * 6, 33, WHITE, 6)
        c.line(sx + side * 6, 34, sx + side * 4, 39, SKIN, 4)
        c.ellipse(sx + side * 4, 40, 3, 2.5, SKIN)
    # Шея, воротник с лентой бейджа, голова: тёмные волосы, уши, пробор.
    c.rect(x0 + 5, 20, x0 + 11, 23, SKIN)
    c.rect(x0 + 2, 22, x0 + 14, 24, WHITE)
    c.rect(x0 + 4, 23, x0 + 12, 23, AQUA)
    c.ellipse(x0 + 8, 13, 9, 9, DARK)
    c.rect(x0 + 2, 18, x0 + 14, 21, SKIN)
    c.rect(x0 + 3, 18, x0 + 13, 18, TAN)
    for side in (-1, 1):
        c.ellipse(x0 + 8 + side * 9, 15, 2, 3, SKIN)
    c.line(x0 + 11, 5, x0 + 9, 10, METAL, 1)
    # Галстук закинуло за плечо, кончик треплет ветром.
    c.line(x0 + 13, 23, x0 + 21, 21, RED, 3)
    c.line(x0 + 21, 21, x0 + 27, 19 + flap, RED, 3)
    c.finish()
    # Дужки очков за ушами поверх обводки.
    for side in (-1, 1):
        c.rect(x0 + 8 + side * 8 - (1 if side < 0 else 0), 14, x0 + 8 + side * 8 + (1 if side > 0 else 0), 14, K)
    return c


def _roller(c, x, y, phase, turn):
    """Ролик кресла: вилка и парное колёсико, метка на ободе мигает по `phase`."""
    c.rect(x - 2, y - 9, x + 2, y - 4, DARK)
    c.ellipse(x - 3 + turn, y, 4, 5, K)
    c.ellipse(x + 3 + turn, y, 4, 5, K)
    c.ellipse(x + turn, y, 5, 5, DARK)
    c.rect(x - 1 + turn, y - 3 if phase < 0.25 else y + 1, x + 1 + turn, y - 2 if phase < 0.25 else y + 2, METAL)


def chair(lean, phase, accent):
    """Офисное кресло со спины, 160×104: высокая спинка цвета `accent` со строчкой и листком на
    скотче, подлокотники, сиденье, газлифт и крестовина с роликами; в кресле сотрудник в чёрном
    костюме, усы торчат шире головы, в отведённой руке жёлтая папка. Ни стоек, ни мачт выше
    головы."""
    c = Canvas(160, 104)
    sh = lean * 6
    bx = 80 + sh * 0.3
    blink = phase < 0.25
    # Крестовина: лучи от ступицы к роликам, задние ближе к камере и ниже.
    for tx, ty in ((-52, 92), (52, 92), (-24, 97), (24, 97)):
        c.line(bx, 84, bx + tx, ty - 8, METAL, 5)
        c.line(bx, 83, bx + tx, ty - 9, GREY, 1)
    for i, (tx, ty) in enumerate(((-52, 92), (52, 92), (-24, 97), (24, 97))):
        _roller(c, bx + tx, ty, phase if i % 2 == 0 else (phase + 0.5) % 1.0, lean * 2)
    c.ellipse(bx, 85, 8, 5, DARK)
    # Газлифт: кожух и блестящий шток, рычаг сбоку.
    c.rect(bx - 6 + sh * 0.2, 74, bx + 6 + sh * 0.2, 84, DARK)
    c.rect(bx - 3 + sh * 0.3, 66, bx + 3 + sh * 0.3, 75, GREY)
    c.rect(bx - 3 + sh * 0.3, 66, bx - 2 + sh * 0.3, 75, WHITE)
    c.line(bx + 8 + sh * 0.4, 70, bx + 24 + sh * 0.4, 72, DARK, 2)
    c.ellipse(bx + 25 + sh * 0.4, 72, 2.5, 2.5, K)
    # Сиденье: толстая подушка шире спинки.
    sx = 80 + sh * 0.6
    c.ellipse(sx, 64, 50, 7, DARK)
    c.rect(sx - 46, 58, sx + 46, 64, DARK)
    c.rect(sx - 44, 58, sx + 44, 59, METAL)
    # Руки сотрудника в стороны на подлокотники: рукава пиджака, манжеты, кисти.
    px = 80 + sh * 1.0
    for side in (-1, 1):
        c.line(px + side * 26, 30, px + side * 44, 46, DARK, 9)
        c.line(px + side * 44, 46, px + side * 46, 52, DARK, 7)
        c.rect(px + side * 46 - 4, 52, px + side * 46 + 4, 53, WHITE)
    # Папка в отведённой правой руке: жёлтая, с листами и корешком, покачивается.
    fy = 26 + (0 if blink else 1)
    c.poly([(px + 45, fy), (px + 64, fy - 4), (px + 68, fy + 20), (px + 49, fy + 24)], GOLD)
    c.line(px + 47, fy + 1, px + 51, fy + 23, BRASS, 2)
    c.line(px + 64, fy - 5, px + 68, fy + 19, WHITE, 2)
    c.rect(px + 54, fy + 6, px + 62, fy + 10, WHITE)
    c.ellipse(px + 48, fy + 25, 4, 4, SKIN)
    c.ellipse(px - 46, 51, 4, 3.5, SKIN)
    # Подлокотники: стойка от сиденья и мягкая накладка.
    for side in (-1, 1):
        ax = sx + side * 48
        c.rect(ax - 2, 56, ax + 2, 66, METAL)
        c.rect(ax - 9, 53, ax + 9, 57, K)
        c.rect(ax - 8, 53, ax + 8, 54, METAL)
    # Спинка: рама, обивка цвета экипажа, строчка, поясничный валик.
    tx = 80 + sh * 1.1
    c.poly([(tx - 36, 28), (tx + 36, 28), (sx + 40, 60), (sx - 40, 60)], DARK)
    c.ellipse(tx, 29, 36, 7, DARK)
    c.poly([(tx - 32, 29), (tx + 32, 29), (sx + 36, 57), (sx - 36, 57)], accent)
    c.ellipse(tx, 29, 32, 5, accent)
    stitch = NAVY if accent in (SEA, AQUA) else (BRASS if accent == GOLD else DARK)
    for k in (0.3, 0.62):
        y = 29 + 28 * k
        x_half = 32 + 4 * k
        for x in range(int(-x_half) + 3, int(x_half) - 2, 4):
            c.rect(tx + (sx - tx) * k + x, y, tx + (sx - tx) * k + x + 1, y, stitch)
    c.rect(sx - 30, 52, sx + 30, 54, stitch)
    # Листок на скотче посреди спинки: строчки текста, уголок отогнут.
    lx = tx + (sx - tx) * 0.4 - 11
    c.rect(lx, 32, lx + 22, 49, WHITE)
    c.rect(lx + 6, 30, lx + 16, 33, GREY)
    for i, y in enumerate((36, 39, 42, 45)):
        c.rect(lx + 3, y, lx + (19 if i % 2 == 0 else 14), y, METAL)
    c.poly([(lx + 22, 49), (lx + 17, 49), (lx + 22, 44)], GREY)
    # Плечи и голова над спинкой: пиджак, белый воротник, зализанные волосы, уши, усы в стороны.
    c.rect(px - 28, 22, px + 28, 31, DARK)
    c.ellipse(px - 27, 27, 5, 6, DARK)
    c.ellipse(px + 27, 27, 5, 6, DARK)
    c.rect(px - 7, 19, px + 7, 22, WHITE)
    c.rect(px - 5, 16, px + 5, 19, SKIN)
    c.ellipse(px, 10, 9, 9, DARK)
    c.rect(px - 6, 15, px + 6, 17, SKIN)
    c.rect(px - 5, 15, px + 5, 15, TAN)
    for side in (-1, 1):
        c.ellipse(px + side * 9, 12, 2, 3, SKIN)
        # Кончик уса виден из-за щеки.
        c.line(px + side * 10, 17, px + side * 15, 16 + (0 if blink else 1), DARK, 2)
    c.line(px - 4, 3, px - 2, 8, METAL, 1)
    c.finish()
    return c


def carts_strip(accent, alien):
    """Три крена (влево, прямо, вправо) по два кадра: лента 6 кадров по 160, порядок как у пиратов.
    `alien` это соперник: кресло вместо тележки."""
    frames = []
    for lean in (-1.0, 0.0, 1.0):
        for ph in (0.0, 0.5):
            frames.append(chair(lean, ph, accent) if alien else mail_cart(lean, ph, accent))
    return strip(frames)


def _leaf(c, x, y, a, length, w, col, rib):
    """Лист фикуса: овал вдоль направления `a` с жилкой и острым кончиком."""
    ca, sa = math.cos(a), math.sin(a)
    n = int(length)
    for i in range(n + 1):
        k = i / max(n, 1)
        half = w * math.sin(math.pi * min(1.0, k * 1.15)) ** 0.7
        px, py = x + ca * i, y + sa * i
        c.line(px - sa * half, py + ca * half, px + sa * half, py - ca * half, col, 2)
    c.line(x + ca * 2, y + sa * 2, x + ca * (length - 2), y + sa * (length - 2), rib, 1)


def ficus():
    """Фикус в горшке у обочины, 120×240 (место пальмы): белый горшок с поддоном, плетёный
    ствол, крона шаром из крупных глянцевых листьев, пара листьев упала у горшка."""
    rng = random.Random(281)
    c = Canvas(120, 240)
    # Ствол: три пряди косой.
    for i in range(132):
        y = 206 - i
        k = i / 131
        for j in range(3):
            x = 60 + math.sin(i * 0.22 + j * 2.1) * (5 - 2 * k)
            c.rect(x - 2, y, x + 2, y, BRASS if j != 1 else TAN)
    # Ветки в крону.
    for bx, by in ((34, 60), (86, 56), (60, 34), (46, 96), (78, 100)):
        c.line(60, 86, bx, by, BRASS, 3)
    # Крона: тёмная глубина, поверх крупные листья кольцами от центра к краю; лист смотрит
    # наружу и провисает вниз, светлые и тёмные чередуются, чтобы каждый читался отдельно.
    c.ellipse(60, 62, 36, 42, PLUM)
    n = 0
    for ring, count, length, width in ((0.35, 7, 17, 5.5), (0.62, 11, 19, 6.0), (0.9, 15, 21, 6.0)):
        for i in range(count):
            a = math.pi * 2 * (i + 0.5 * (n % 2)) / count + rng.uniform(-0.12, 0.12)
            x = 60 + math.cos(a) * 34 * ring
            y = 60 + math.sin(a) * 40 * ring
            droop = a + 0.45 * math.cos(a) * (1 if math.sin(a) > -0.3 else 0.3)
            light = (i + n) % 3 != 0
            _leaf(c, x, y, droop, length + rng.uniform(-2, 2), width, VIOLET if light else PLUM,
                  PLUM if light else VIOLET)
        n += 1
    # Верхушка: пара молодых листьев свечкой.
    _leaf(c, 58, 22, -1.9, 15, 4.0, VIOLET, PLUM)
    _leaf(c, 64, 24, -1.2, 14, 4.0, VIOLET, PLUM)
    # Горшок: белая керамика конусом, ободок, земля, поддон.
    c.poly([(34, 200), (86, 200), (80, 234), (40, 234)], WHITE)
    c.rect(31, 194, 89, 201, WHITE)
    c.rect(31, 201, 89, 201, GREY)
    c.rect(36, 192, 84, 194, DARK)
    c.rect(46, 210, 74, 213, AQUA)
    c.rect(46, 218, 74, 219, GREY)
    c.rect(34, 234, 86, 239, GREY)
    c.rect(52, 189, 68, 192, BRASS)
    # Опавшие листья у горшка.
    _leaf(c, 6, 236, -0.15, 16, 3.5, VIOLET, PLUM)
    _leaf(c, 96, 237, -0.1, 15, 3.0, PLUM, VIOLET)
    c.finish()
    return c


def coat_rack():
    """Вешалка у обочины, 120×240 (место второй пальмы): стойка на крестовине с рогами наверху,
    на макушке шляпа, слева длинный синий плащ с поясом, справа полосатый шарф и зонт-трость,
    у основания портфель."""
    c = Canvas(120, 240)
    # Крестовина основания и стойка.
    c.poly([(22, 239), (30, 228), (90, 228), (98, 239)], DARK)
    c.rect(30, 226, 90, 229, METAL)
    c.ellipse(60, 226, 12, 5, METAL)
    c.rect(57, 30, 62, 228, METAL)
    c.rect(57, 30, 58, 228, GREY)
    for y in (96, 168):
        c.rect(55, y, 64, y + 3, DARK)
    # Рога: четыре крюка дугой с шариками.
    for side in (-1, 1):
        for reach, y0 in ((30, 48), (20, 66)):
            c.line(60, y0 + 12, 60 + side * reach * 0.6, y0 + 8, METAL, 3)
            c.line(60 + side * reach * 0.6, y0 + 8, 60 + side * reach, y0 - 4, METAL, 3)
            c.ellipse(60 + side * reach, y0 - 6, 3, 3, GOLD)
    # Шляпа на макушке: тулья с красной лентой и поля.
    c.ellipse(60, 30, 26, 5, DARK)
    c.rect(46, 12, 74, 28, DARK)
    c.ellipse(60, 12, 14, 5, DARK)
    c.rect(46, 23, 74, 26, RED)
    c.line(52, 10, 66, 10, METAL, 1)
    # Плащ на левом крюке: плечи, длинные полы, рукав, воротник, пояс с пряжкой, пуговицы.
    c.poly([(26, 46), (50, 50), (54, 70), (52, 190), (8, 190), (12, 80), (16, 56)], SEA)
    c.poly([(8, 100), (2, 164), (12, 168), (16, 104)], SEA)
    c.ellipse(7, 168, 5, 4, NAVY)
    c.poly([(24, 46), (40, 48), (36, 70), (30, 60)], NAVY)
    c.poly([(40, 48), (50, 50), (50, 66), (42, 62)], NAVY)
    c.rect(9, 118, 52, 124, NAVY)
    c.rect(26, 116, 34, 126, GOLD)
    c.rect(28, 119, 32, 123, NAVY)
    for y in (82, 98, 140, 158):
        c.ellipse(40, y, 2, 2, GOLD)
    c.line(22, 128, 20, 188, NAVY, 1)
    c.line(44, 128, 45, 188, NAVY, 1)
    c.rect(8, 188, 52, 190, NAVY)
    # Шарф на правом верхнем крюке: перекинут через рог, две ленты разной длины в полоску,
    # на концах бахрома.
    c.ellipse(91, 44, 9, 5, RED)
    c.rect(84, 44, 91, 132, RED)
    c.rect(93, 44, 100, 104, RED)
    for y in range(54, 130, 12):
        c.rect(84, y, 91, y + 2, WHITE)
    for y in range(54, 102, 12):
        c.rect(93, y, 100, y + 2, WHITE)
    for x in (84, 87, 90):
        c.rect(x, 133, x + 1, 139, RED)
    for x in (93, 96, 99):
        c.rect(x, 105, x + 1, 111, RED)
    # Зонт-трость висит ручкой на правом нижнем крюке: крюк ручки, сложенный купол, хлястик.
    c.line(80, 60, 76, 56, BRASS, 3)
    c.line(76, 56, 72, 62, BRASS, 3)
    c.rect(71, 62, 73, 80, BRASS)
    c.poly([(68, 80), (77, 80), (75, 176), (70, 176)], AQUA)
    c.line(72, 82, 72, 174, SEA, 1)
    c.rect(68, 116, 77, 118, SEA)
    c.rect(71, 176, 73, 186, METAL)
    # Портфель на полу у основания: ручка, клапан, застёжка.
    c.rect(82, 196, 96, 200, DARK)
    c.rect(85, 198, 93, 200, METAL)
    c.rect(70, 202, 108, 236, BRASS)
    c.poly([(70, 202), (108, 202), (108, 216), (89, 222), (70, 216)], TAN)
    c.rect(86, 216, 92, 225, GOLD)
    c.rect(70, 234, 108, 236, DARK)
    c.finish()
    return c


def printer():
    """Принтер у дороги, 96×64 (место камня): приземистый серый корпус, сзади лоток с пачкой
    бумаги, спереди выползает лист, панель с экраном и кнопками, решётка, лоток кассеты."""
    c = Canvas(96, 64)
    # Задний лоток с бумагой.
    c.poly([(22, 20), (26, 2), (74, 2), (78, 20)], WHITE)
    c.poly([(18, 20), (20, 8), (26, 8), (24, 20)], METAL)
    c.poly([(72, 20), (70, 8), (76, 8), (78, 20)], METAL)
    for y in (6, 10, 14):
        c.line(27, y, 73, y, GREY, 1)
    # Корпус: верхняя крышка светлее, скос, тёмный низ с кассетой.
    c.poly([(6, 63), (4, 30), (12, 18), (84, 18), (92, 30), (90, 63)], GREY)
    c.poly([(12, 18), (84, 18), (92, 30), (4, 30)], WHITE)
    c.rect(4, 30, 92, 31, METAL)
    c.rect(6, 54, 90, 63, METAL)
    c.rect(14, 56, 70, 61, DARK)
    c.rect(36, 57, 48, 58, GREY)
    # Щель выдачи и лист с текстом, лежащий на выходном лотке.
    c.rect(16, 34, 64, 37, K)
    c.poly([(20, 36), (60, 36), (64, 50), (16, 50)], WHITE)
    for i, y in enumerate((40, 43, 46)):
        c.line(22, y, 52 if i != 1 else 44, y, METAL, 1)
    c.rect(12, 50, 68, 52, METAL)
    # Панель: экран, кнопки, огонёк.
    c.rect(70, 34, 88, 50, DARK)
    c.rect(72, 36, 86, 42, AQUA)
    c.rect(73, 37, 78, 38, SKY)
    c.rect(72, 45, 75, 48, VIOLET)
    c.rect(78, 45, 81, 48, RED)
    c.rect(84, 45, 86, 48, GOLD)
    # Решётка на крышке и стикер.
    for x in range(18, 40, 4):
        c.line(x, 22, x - 2, 27, METAL, 1)
    c.rect(56, 21, 66, 27, GOLD)
    c.rect(56, 27, 66, 27, BRASS)
    return c.finish()


def cooler():
    """Кулер, 48×64 (место бочки): голубая бутыль горлом вниз на белой тумбе, два крана,
    поддон, сбоку стопка стаканчиков."""
    c = Canvas(48, 64)
    # Бутыль: плечи, рёбра, уровень воды, блик.
    c.rect(11, 3, 37, 20, AQUA)
    c.ellipse(24, 4, 13, 4, AQUA)
    c.poly([(11, 20), (37, 20), (29, 27), (19, 27)], AQUA)
    c.rect(11, 4, 37, 7, SKY)
    c.ellipse(24, 3, 12, 3, SKY)
    c.rect(11, 8, 37, 8, SEA)
    for y in (12, 16):
        c.rect(11, y, 37, y, SEA)
    c.rect(14, 9, 16, 19, SKY)
    c.ellipse(30, 13, 1.5, 1.5, SKY)
    c.ellipse(27, 17, 1, 1, SKY)
    # Тумба: воротник, корпус, ниша с кранами, поддон, ножки.
    c.rect(8, 26, 40, 30, GREY)
    c.rect(6, 30, 42, 63, WHITE)
    c.rect(38, 30, 42, 63, GREY)
    c.rect(11, 34, 37, 46, DARK)
    c.rect(15, 34, 19, 39, RED)
    c.rect(16, 40, 18, 41, METAL)
    c.rect(29, 34, 33, 39, AQUA)
    c.rect(30, 40, 32, 41, METAL)
    c.rect(9, 46, 39, 48, METAL)
    for x in range(12, 38, 3):
        c.set(x, 47, DARK)
    c.rect(11, 52, 37, 53, GREY)
    c.rect(11, 57, 37, 57, GREY)
    c.rect(6, 61, 42, 63, METAL)
    # Стаканчики стопкой в держателе на боку.
    c.rect(42, 36, 46, 52, WHITE)
    for y in (39, 43, 47):
        c.rect(42, y, 46, y, GREY)
    c.rect(41, 52, 47, 54, METAL)
    return c.finish()


def sign(right):
    """Указатель поворота, 96×112: раскладная жёлтая табличка «мокрый пол» домиком, сверху
    вырез ручки и восклицательный знак, ниже чёрные шевроны в сторону поворота, ножки."""
    c = Canvas(96, 112)
    # Задняя створка видна по краям и внизу.
    c.poly([(26, 6), (70, 6), (95, 108), (1, 108)], BRASS)
    c.poly([(22, 3), (74, 3), (88, 104), (8, 104)], GOLD)
    c.rect(22, 3, 74, 5, WHITE)
    c.poly([(9, 100), (87, 100), (88, 104), (8, 104)], BRASS)
    # Ручка: вырез под ладонь.
    c.rect(38, 8, 58, 12, K)
    c.rect(38, 12, 58, 12, BRASS)
    # Знак: треугольник с восклицательным знаком.
    c.poly([(48, 16), (60, 36), (36, 36)], K)
    c.poly([(48, 21), (56, 34), (40, 34)], GOLD)
    c.rect(47, 24, 49, 30, K)
    c.rect(47, 32, 49, 33, K)
    # Шевроны в сторону поворота.
    d = 1 if right else -1
    for k in range(3):
        cx = 48 + d * (k * 20 - 20)
        c.poly([(cx - d * 8, 44), (cx + d * 10, 66), (cx - d * 8, 88), (cx - d * 2, 66)], K)
    # Полоса текста под шевронами и ножки.
    c.rect(22, 93, 74, 96, K)
    for x in range(26, 72, 6):
        c.rect(x, 94, x + 3, 95, GOLD)
    for x in (6, 84):
        c.rect(x, 104, x + 6, 111, DARK)
    return c.finish()


def cubicle():
    """Рабочее место у дороги, 192×160 (место хижины): перегородки из трёх секций синей ткани
    в серой раме, наверху полка с папками, стол с тумбой, монитор с графиком, лампа, часы,
    стикеры, стопка бумаг, кружка, кактус, перед столом кресло."""
    c = Canvas(192, 160)
    # Перегородки: рама, три секции ткани, фактура точками.
    c.rect(8, 44, 184, 159, METAL)
    c.rect(8, 44, 184, 47, GREY)
    for x0, x1 in ((12, 66), (70, 124), (128, 180)):
        c.rect(x0, 50, x1, 156, SEA)
        c.rect(x0, 50, x1, 51, NAVY)
        for y in range(56, 154, 7):
            for x in range(x0 + 3 + (y % 2) * 3, x1 - 1, 7):
                c.set(x, y, NAVY)
    # Полка с папками над перегородкой.
    c.rect(20, 40, 124, 44, GREY)
    x = 24
    for w, h, col in ((9, 26, RED), (9, 26, RED), (8, 24, GOLD), (10, 28, DARK), (8, 22, WHITE), (9, 26, VIOLET),
                      (9, 26, VIOLET), (8, 24, GOLD), (10, 20, WHITE)):
        c.rect(x, 40 - h, x + w - 1, 39, col)
        c.rect(x + 2, 40 - h + 4, x + w - 3, 40 - h + 9, WHITE if col not in (WHITE, GOLD) else METAL)
        c.ellipse(x + w / 2 - 0.5, 34, 1.5, 1.5, K)
        x += w + 1
    # Коробка бумаги на краю полки.
    c.rect(134, 24, 172, 43, BRASS)
    c.rect(134, 24, 172, 27, GOLD)
    c.rect(150, 24, 156, 43, TAN)
    c.rect(138, 32, 147, 38, WHITE)
    # Часы на правой секции.
    c.ellipse(154, 66, 12, 12, DARK)
    c.ellipse(154, 66, 10, 10, WHITE)
    c.line(154, 66, 154, 59, K, 1)
    c.line(154, 66, 160, 69, K, 1)
    for a in range(0, 360, 90):
        c.set(154 + math.cos(math.radians(a)) * 8, 66 + math.sin(math.radians(a)) * 8, METAL)
    # Стикеры и график на левой секции.
    for sx, sy, col in ((18, 58, GOLD), (32, 62, RED), (20, 76, AQUA), (36, 80, GOLD), (50, 60, VIOLET)):
        c.rect(sx, sy, sx + 10, sy + 10, col)
        c.rect(sx + 2, sy + 3, sx + 8, sy + 3, K)
        c.rect(sx + 2, sy + 6, sx + 6, sy + 6, K)
    c.rect(134, 82, 176, 96, WHITE)
    c.line(138, 93, 148, 88, RED, 1)
    c.line(148, 88, 158, 91, RED, 1)
    c.line(158, 91, 172, 84, RED, 1)
    c.rect(136, 95, 174, 95, GREY)
    # Монитор: рамка, экран с окнами и графиком, стикер на углу, ножка.
    c.rect(74, 66, 122, 102, DARK)
    c.rect(77, 69, 119, 97, AQUA)
    c.rect(77, 69, 119, 72, SEA)
    c.rect(79, 75, 97, 94, WHITE)
    for y in (78, 82, 86, 90):
        c.rect(81, y, 95 if y != 86 else 90, y, METAL)
    for i, h in enumerate((6, 10, 8, 14)):
        c.rect(101 + i * 4, 94 - h, 103 + i * 4, 94, SKY)
    c.rect(114, 62, 124, 72, GOLD)
    c.rect(94, 102, 102, 108, DARK)
    c.rect(86, 108, 110, 110, DARK)
    # Настольная лампа слева: основание, колено, абажур, пятно света.
    c.ellipse(34, 108, 9, 3, DARK)
    c.line(34, 106, 28, 92, METAL, 2)
    c.line(28, 92, 42, 84, METAL, 2)
    c.poly([(38, 80), (52, 82), (54, 92), (40, 90)], RED)
    c.rect(43, 91, 52, 92, GOLD)
    # Столешница и тумба с ящиками, боковина.
    c.rect(14, 110, 178, 116, WHITE)
    c.rect(14, 116, 178, 118, GREY)
    c.rect(18, 118, 24, 159, GREY)
    c.rect(124, 118, 174, 159, GREY)
    for y in (120, 133, 146):
        c.rect(127, y, 171, y + 10, WHITE)
        c.rect(143, y + 4, 155, y + 5, METAL)
    c.rect(124, 157, 174, 159, METAL)
    # На столе: клавиатура, стопка бумаг, кружка, кактус.
    c.rect(78, 111, 118, 113, DARK)
    for x in range(80, 118, 4):
        c.set(x, 112, GREY)
    c.rect(136, 100, 160, 109, WHITE)
    for y in (102, 105, 108):
        c.rect(136, y, 160, y, GREY)
    c.rect(164, 100, 172, 109, RED)
    c.rect(172, 102, 175, 106, RED)
    c.rect(165, 100, 171, 100, DARK)
    c.rect(54, 102, 64, 109, TAN)
    c.rect(53, 101, 65, 102, BRASS)
    c.ellipse(59, 93, 5, 9, VIOLET)
    c.ellipse(53, 96, 3, 4, VIOLET)
    c.rect(59, 86, 59, 100, PLUM)
    c.set(56, 90, WHITE)
    c.set(62, 94, WHITE)
    c.set(52, 95, WHITE)
    # Кресло перед столом: спинка, сиденье, газлифт, крестовина с роликами.
    c.poly([(50, 114), (94, 114), (98, 142), (46, 142)], DARK)
    c.ellipse(72, 114, 22, 5, DARK)
    c.rect(52, 120, 92, 121, METAL)
    c.rect(52, 130, 92, 131, METAL)
    c.rect(42, 142, 102, 148, DARK)
    c.rect(44, 142, 100, 143, METAL)
    c.rect(69, 148, 75, 154, METAL)
    c.line(72, 153, 46, 156, DARK, 3)
    c.line(72, 153, 98, 156, DARK, 3)
    for x in (46, 72, 98):
        c.ellipse(x, 157, 3, 2.5, K)
    return c.finish()


def road_colors():
    """Лента цветов дороги 8×1: индекс это место в `ROAD_COLORS`."""
    c = Canvas(8, 1)
    for i in range(8):
        c.set(i, 0, i)
    return c


def sprites():
    """Ленты гонки в палитре спрайтов, ключи как у пиратов."""
    out = {
        "cart_hero": carts_strip(RED, False),
        "palm": ficus(),
        "palm_b": coat_rack(),
        "road_rock": printer(),
        "road_barrel": cooler(),
        "sign_left": sign(False),
        "sign_right": sign(True),
        "road_hut": cubicle(),
    }
    for i, accent in enumerate((SEA, GOLD, RED, AQUA)):
        out["cart_%d" % i] = carts_strip(accent, True)
    return out


def horizon():
    """Горизонт в своей палитре `OFFICE_SKY`."""
    return {"road_sky": sky(), "road_islands": islands(), "road_sea": sea()}


def road_palette():
    return {"road_colors": road_colors()}


def preview(path):
    items = office16.shaded(sprites())
    for key, canvas in horizon().items():
        items[key] = (canvas, OFFICE_SKY)
    for key, canvas in road_palette().items():
        items[key] = (canvas, ROAD_COLORS)
    office16.save_sheet(path, items, scale=2, max_w=512)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        preview(sys.argv[sys.argv.index("--preview") + 1])
