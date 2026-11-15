#!/usr/bin/env python3
"""Набор «Зомби» для 16/32-bit (основа, зеркало `space16.py` и `castles16.py`): ночной хоррор из
кино категории Б, большая луна, зелёный туман, кладбище и пригород. Герой это выживший в красной
куртке, синей бейсболке козырьком вперёд, джинсах и кроссовках, с жёлтым рюкзаком за спиной;
враги это зомби-ходоки в лохмотьях. Те же ленты, размеры и число кадров, что у космоса, пиратов
и замков (`castles16.sprites()`); позы героя и точка опоры ног повторяют образцы кадр в кадр, чтобы
хитбоксы демок сходились: меняется рисунок, не геометрия.

Слоты космоса и их зомби: космонавт это выживший, пришелец это зомби-ходок, кристалл это банка
консервов, флаг экспедиции это зелёный флаг убежища с белым крестом, грузовая капсула это
армейский ящик, метеорит это надгробие, настил станции это грязь с жухлой травой. Ленты, которых
нет в `sprites()` (ворон вместо попугая-дрона, ползущая кисть вместо краба, ключ, аптечка,
гвоздь вместо снаряда), лежат в `extras()` тех же размеров, что у образцов.

Имена и порядок цветов те же, что у `space16.py` (по ним модули демок `zombies_*16.py` берут цвета
по роли): K обводка, NAVY ночь, SEA тёмная болотная зелень, AQUA кожа зомби и ядовитый свет, SKY
туман и блики, WHITE кость, луна и крест, GREY тень кости, SKIN кожа, TAN грязь, GOLD и BRASS жёлтое
(рюкзак, окна, бурьян), METAL камень и лохмотья, DARK чёрное и силуэты, RED куртка и кровь, VIOLET
и PLUM синий (кепка, джинсы).

    python3 tools/zombies16.py --preview out.png   # лист набора в 4 раза крупнее
    python3 tools/zombies16.py --preview out.png --scale=6 --keys=hero_run,hero_idle
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pixel_sprites16 as base  # noqa: E402
from pixel_sprites import png_bytes  # noqa: E402

# Палитра «Зомби»: 16 цветов, индекс это та же роль, что у пиратов, космоса и замков.
K, NAVY, SEA, AQUA, SKY, WHITE, GREY, SKIN, TAN, GOLD, BRASS, METAL, DARK, RED, VIOLET, PLUM = range(16)
PALETTE = [
    (0x0E, 0x0C, 0x16),  # K      обводка
    (0x18, 0x22, 0x3A),  # NAVY   ночь, тень тумана
    (0x34, 0x62, 0x50),  # SEA    тёмная болотная зелень, армейский ящик
    (0x86, 0xB8, 0x5E),  # AQUA   кожа зомби, ядовитый свет, флаг убежища
    (0xBC, 0xDC, 0xC8),  # SKY    зелёный туман, блик луны
    (0xEE, 0xEC, 0xDC),  # WHITE  кость, луна, крест
    (0xA6, 0xA8, 0x9C),  # GREY   тень кости
    (0xF0, 0xC0, 0x96),  # SKIN   кожа живых
    (0x9A, 0x62, 0x3C),  # TAN    грязь, тень кожи
    (0xE8, 0xC8, 0x50),  # GOLD   рюкзак, огонь в окнах
    (0xA8, 0x78, 0x28),  # BRASS  тень жёлтого, сухая трава
    (0x6E, 0x76, 0x78),  # METAL  камень, лохмотья
    (0x2C, 0x2A, 0x36),  # DARK   силуэты, волосы, подошвы
    (0xD8, 0x30, 0x2C),  # RED    куртка, кровь
    (0x2E, 0x5E, 0xC0),  # VIOLET кепка, джинсы
    (0x1C, 0x2E, 0x70),  # PLUM   тень синего, дальняя нога
]
SHADOW = {SEA: NAVY, AQUA: SEA, SKY: AQUA, WHITE: GREY, GREY: METAL, SKIN: TAN, TAN: DARK, GOLD: BRASS,
          BRASS: DARK, METAL: DARK, RED: PLUM, VIOLET: PLUM}
# Материалы для светотени рампами: зелень и зомби, кость и луна, кожа живых, грязь, жёлтое,
# камень и лохмотья, чёрное, красное, синее.
GROUPS = {NAVY: "night", SEA: "leaf", AQUA: "leaf", SKY: "bone", WHITE: "bone", GREY: "bone",
          SKIN: "skin", TAN: "dirt", GOLD: "gold", BRASS: "gold", METAL: "stone", DARK: "iron", RED: "red",
          VIOLET: "blue", PLUM: "blue"}


class Canvas(base.Canvas):
    shadow = SHADOW


def strip(frames):
    out = Canvas(sum(f.w for f in frames), max(f.h for f in frames))
    x = 0
    for f in frames:
        out.paste(f, x, 0)
        x += f.w
    return out


# --- Выживший ----------------------------------------------------------------------------------
# Силуэт как у космонавта и рыцаря (те же позы и габариты), рисунок свой: синяя бейсболка с козырьком
# вперёд, открытое лицо, красная куртка от плеч до пояса с белой молнией, синие джинсы, белые
# кроссовки, жёлтый рюкзак с валиком спальника за спиной.

def _head(c, x, y, face=1):
    """Голова лицом вправо при `face` 1: лицо открыто, кепка козырьком вперёд, из-под неё сзади
    тёмные волосы. Центр (x, y), нижний край шеи y+6."""
    def at(dx):
        return x + dx * face

    # Шея и волосы на затылке, потом лицо.
    c.rect(at(-1), y + 5, at(1), y + 6, SKIN)
    c.ellipse(at(-1.5), y + 1.5, 3.2, 3.6, DARK)
    c.ellipse(at(0.8), y + 1.8, 3.6, 3.7, SKIN)
    # Кепка: купол, козырёк вперёд на пять пикселей, подбой козырька, эмблема.
    c.ellipse(at(-0.5), y - 3.6, 4.8, 3.0, VIOLET)
    a, b = sorted((at(2), at(7)))
    c.rect(a, y - 2, b, y - 1, VIOLET)
    a, b = sorted((at(4), at(7)))
    c.rect(a, y - 1, b, y - 1, PLUM)
    c.set(at(2), y - 4, WHITE)
    c.set(at(-3), y - 2, PLUM)
    # Лицо: глаз, нос, рот.
    c.set(at(3), y + 1, K)
    c.set(at(3), y + 2, K)
    c.set(at(5), y + 2, TAN)
    c.set(at(3), y + 4, TAN)
    c.set(at(4), y + 4, TAN)


def _pack(c, x, y0, y1):
    """За спиной: жёлтый рюкзак, клапан, карман и валик спальника сверху."""
    c.rect(x - 1, y0 + 2, x + 3, y1 + 2, GOLD)
    c.rect(x, y0 + 1, x + 2, y0 + 1, GOLD)
    c.rect(x - 1, y0 + 5, x + 3, y0 + 5, BRASS)
    c.rect(x - 1, y1, x + 1, y1 + 2, BRASS)
    c.rect(x - 1, y0 - 1, x + 3, y0, SEA)
    c.set(x + 1, y0 - 1, GREY)


def _body(c, x0, y0, x1, y1, skirt=1):
    """Куртка: красная от плеч до пояса, тёмная резинка по низу, белая молния у передней кромки,
    лямка рюкзака на плече."""
    c.rect(x0, y0, x1, y1 + skirt, RED)
    c.rect(x0, y1 + skirt, x1, y1 + skirt, DARK)
    for y in range(y0 + 1, y1 + skirt, 2):
        c.set(x1 - 1, y, WHITE)
    c.rect(x0 + 2, y0, x0 + 2, y1, BRASS)
    c.rect(x0, y0, x1, y0, PLUM)


def _shoe(c, x, y, w=4):
    """Кроссовок: белый верх, носок вперёд, тёмная подошва."""
    c.rect(x - 1, y - 1, x + 1, y - 1, WHITE)
    c.rect(x - 1, y, x + w - 1, y, WHITE)
    c.rect(x - 1, y + 1, x + w, y + 1, DARK)
    c.set(x + w - 2, y, GREY)


def _arm(c, x0, y0, x1, y1, col):
    """Рука в красном рукаве с кистью. Ближняя (RED) узкая в два пикселя, дальняя (PLUM) в три."""
    c.line(x0, y0, x1, y1, col, 2 if col == RED else 3)
    c.ellipse(x1, y1, 1.4, 1.4, SKIN)


def hero_side(phase, jump=False):
    """Выживший сбоку, лицом вправо: бег по фазе 0..2π или прыжок."""
    c = Canvas()
    bob = 0 if jump else int(round(abs(math.sin(phase)) * 1.4))
    hip_y = 21 - bob
    swing = 0.9 if jump else math.sin(phase)
    _arm(c, 15, 15 - bob, 15 + 5 * swing, 20 - bob - (3 if jump else 0), PLUM)
    for sign, cloth in ((-1, PLUM), (1, VIOLET)):
        a = swing * sign
        lift = max(0.0, math.cos(phase) * sign) * 3.0 if not jump else (4 if sign > 0 else 1)
        foot = (15 + 6 * a, 29 - lift)
        knee = ((15 + foot[0]) / 2 + 2, (hip_y + foot[1]) / 2)
        c.line(15 + sign, hip_y, knee[0], knee[1], cloth, 4)
        c.line(knee[0], knee[1], foot[0], foot[1], cloth, 4)
        _shoe(c, foot[0], foot[1])
    _pack(c, 8, 13 - bob, 19 - bob)
    _body(c, 11, 13 - bob, 19, hip_y)
    _arm(c, 16, 15 - bob, 16 - 5 * swing, 20 - bob - (4 if jump else 0), RED)
    _head(c, 16, 7 - bob)
    return c.finish()


def hero_back(phase):
    """Со спины: бежит вглубь экрана, рюкзак закрывает спину, кепка и затылок, ушей не видно."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.4))
    for sign in (-1, 1):
        lift = max(0.0, s * sign) * 4.0
        x = 16 + sign * 3
        c.rect(x - 2, 21 - bob, x + 1, 28 - lift, VIOLET if sign > 0 else PLUM)
        _shoe(c, x - 1, 28 - lift, 3)
        _arm(c, 16 + sign * 6, 15 - bob, 16 + sign * 7, 20 - bob + s * sign * 2, RED if sign > 0 else PLUM)
    c.rect(11, 13 - bob, 20, 21 - bob, RED)
    c.rect(11, 21 - bob, 20, 21 - bob, DARK)
    # Рюкзак во всю спину: лямки по бокам, клапан, карман, валик сверху.
    c.rect(12, 14 - bob, 19, 21 - bob, GOLD)
    c.rect(12, 17 - bob, 19, 17 - bob, BRASS)
    c.rect(14, 19 - bob, 17, 21 - bob, BRASS)
    c.rect(12, 12 - bob, 19, 13 - bob, SEA)
    # Голова со спины: волосы, уши, кепка с застёжкой.
    c.rect(14, 11 - bob, 17, 12 - bob, SKIN)
    c.ellipse(15.5, 8 - bob, 4.3, 3.8, DARK)
    c.set(10, 8 - bob, SKIN)
    c.set(21, 8 - bob, SKIN)
    c.set(10, 9 - bob, SKIN)
    c.set(21, 9 - bob, SKIN)
    c.ellipse(15.5, 5 - bob, 5.2, 4.0, VIOLET)
    c.rect(11, 8 - bob, 20, 8 - bob, PLUM)
    c.set(15, 8 - bob, WHITE)
    c.set(16, 8 - bob, WHITE)
    c.set(15, 1 - bob, WHITE)
    return c.finish()


def hero_leap(i):
    """Прыжок через клетку, четыре кадра: присел, толчок, поджал ноги, приземление."""
    c = Canvas()
    crouch = (3, 0, -1, 2)[i]
    legs = ((2, 2), (5, -4), (3, -1), (4, 3))[i]
    hip_y = 21 + crouch
    _arm(c, 15, 15 + crouch, 12 - i % 2, 11 + crouch if i in (1, 2) else 20 + crouch, PLUM)
    for sign, cloth in ((-1, PLUM), (1, VIOLET)):
        foot = (15 + sign * legs[0] + (2 if i == 1 else 0), 29 if i in (0, 3) else 27 - (2 if i == 2 else 0))
        knee = ((15 + foot[0]) / 2 + 2 + legs[1] * 0.3, (hip_y + foot[1]) / 2 + (2 if i == 2 else 0))
        c.line(15 + sign, hip_y, knee[0], knee[1], cloth, 4)
        c.line(knee[0], knee[1], foot[0], foot[1], cloth, 4)
        _shoe(c, foot[0], foot[1])
    _pack(c, 8, 13 + crouch, 19 + crouch)
    _body(c, 11, 13 + crouch, 19, hip_y)
    _arm(c, 16, 15 + crouch, 20 + i % 2, 10 + crouch if i in (1, 2) else 20 + crouch, RED)
    _head(c, 16, 7 + crouch)
    return c.finish()


def hero_idle(i):
    """Стойка: два кадра, выживший дышит."""
    c = Canvas()
    up = i
    for sign, cloth in ((-1, PLUM), (1, VIOLET)):
        x = 15 + sign * 2
        c.rect(x - 1, 21, x + 1, 28, cloth)
        _shoe(c, x, 29)
    _arm(c, 14, 15 - up, 13, 21 - up, PLUM)
    _pack(c, 8, 13 - up, 19 - up)
    _body(c, 11, 13 - up, 19, 21)
    _arm(c, 17, 15 - up, 18, 21 - up, RED)
    _head(c, 16, 7 - up)
    return c.finish()


def _lean(c, sx, sy, hx, hy, w):
    """Корпус под наклоном: от плеч (sx, sy) к бёдрам (hx, hy), ширина w; красная куртка,
    тёмная резинка у бёдер, молния белой точкой."""
    n = math.hypot(hx - sx, hy - sy)
    dx, dy = (hx - sx) / n, (hy - sy) / n
    for k in range(int(n) + 1):
        x, y = sx + dx * k, sy + dy * k
        col = DARK if k >= int(n) - 1 else RED
        c.line(x + dy * w / 2, y - dx * w / 2, x - dy * w / 2, y + dx * w / 2, col, 2)
    c.set(sx + dx * 3 + dy * (w / 2 - 1), sy + dy * 3 - dx * (w / 2 - 1), WHITE)


def hero_slide(i):
    """Подкат на боку ногами вперёд: корпус откинут, ближняя нога вытянута, дальняя коленом вверх,
    рука сзади на земле, рюкзак придавлен под спиной. Макушка кепки на 15-й строке. Два кадра:
    колено и пыль."""
    c = Canvas()
    c.line(19, 27, 24, 23 - i, PLUM, 3)
    c.line(24, 23 - i, 27, 27, PLUM, 3)
    _shoe(c, 27, 27, 3)
    c.line(13, 24, 19, 23, PLUM, 2)
    c.rect(11, 27, 18, 29, GOLD)
    c.rect(11, 27, 18, 27, SEA)
    c.rect(14, 28, 16, 29, BRASS)
    _lean(c, 12, 24, 19, 27, 6)
    c.line(19, 28, 28, 28, VIOLET, 4)
    c.line(20, 27, 27, 27, VIOLET, 1)
    c.rect(28, 26, 30, 29, WHITE)
    c.rect(28, 29, 30, 29, DARK)
    _arm(c, 11, 25, 6, 29, RED)
    _head(c, 10, 21)
    c.finish()
    for k, (x, y) in enumerate(((2, 30), (4, 31), (1, 28), (3, 29))):
        if (k + i) % 2 == 0:
            c.set(x, y, TAN)
    return c


def hero_crouch(i):
    """Присед: та же фигура, сложенная вниз, корпус прямо, колени вперёд. Два кадра шага."""
    c = Canvas()
    step = (-1, 1)[i]
    c.line(15, 24, 19, 26, PLUM, 2)
    for sign, cloth in ((-1, PLUM), (1, VIOLET)):
        hip = (14, 27)
        knee = (20 - sign + step * sign, 26)
        foot = (17 - sign * 2 + step * sign * 2, 29)
        c.line(hip[0], hip[1], knee[0], knee[1], cloth, 4)
        c.line(knee[0], knee[1], foot[0], foot[1], cloth, 3)
        _shoe(c, foot[0], foot[1])
    _pack(c, 8, 22, 26)
    _body(c, 11, 22, 18, 26, skirt=0)
    _arm(c, 14, 24, 19, 26, RED)
    _head(c, 16, 19)
    return c.finish()


def hero_hang(i):
    """На тросе: руки вверх к точке хвата (центр сверху), ноги свисают и качаются."""
    c = Canvas()
    sw = (-1, 1)[i]
    c.line(14, 13, 15, 1, PLUM, 3)
    c.line(18, 13, 17, 1, RED, 2)
    c.ellipse(15, 1, 1.2, 1.2, SKIN)
    c.ellipse(17, 1, 1.2, 1.2, SKIN)
    _pack(c, 8, 13, 19)
    _body(c, 11, 13, 20, 21, skirt=0)
    for sign, cloth in ((-1, PLUM), (1, VIOLET)):
        foot = (15.5 + sign * 2 + sw * 2, 29)
        c.line(15.5 + sign * 2, 21, foot[0], foot[1], cloth, 3)
        _shoe(c, foot[0], foot[1], 3)
    c.finish()
    hd = Canvas()
    _head(hd, 16, 8)
    hd.finish()
    for y in range(hd.h):
        for x in range(hd.w):
            if hd.px[y][x] is not None and y >= 1:
                c.set(x, y, hd.px[y][x])
    return c


# --- Зомби -------------------------------------------------------------------------------------
# Ходок в лохмотьях: зелёно-серая кожа, голова набок, пустые глазницы с красной искрой, чёрный рот
# с зубами, руки вытянуты вперёд, на рёбрах рваная рубашка, одна нога голая. Шаг и рост повторяют
# пришельца и стражника.

def _claws(c, x, y, face):
    """Кисть с когтями: три пальца торчат вперёд (`face` -1 влево)."""
    c.ellipse(x, y, 1.6, 1.6, AQUA)
    for dy in (-2, 0, 2):
        c.set(x + 2 * face, y + dy, AQUA)
        c.set(x + 3 * face, y + dy + (1 if dy > 0 else 0), WHITE)


def zombie_side(phase):
    """Зомби сбоку, лицом влево (навстречу герою): шаркающий шаг по фазе, обе руки вытянуты."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.2))
    # Дальняя рука повыше, ближняя пониже; кисти с когтями.
    c.line(15, 14 - bob, 6, 13 - bob + s * 0.8, SEA, 2)
    _claws(c, 5, 13 - bob + s * 0.8, -1)
    # Ноги: дальняя в лохмотьях штанов, ближняя голая ниже колена; ступни волочатся.
    for sign, col in ((-1, DARK), (1, AQUA)):
        a = s * sign
        lift = max(0.0, math.cos(phase) * sign) * 2.0
        foot = (16 - 4 * a, 29 - lift)
        knee = ((17 + foot[0]) / 2 - 1.5, (22 - bob + foot[1]) / 2)
        c.line(17, 22 - bob, knee[0], knee[1], DARK, 3)
        c.line(knee[0], knee[1], foot[0], foot[1], col, 2)
        c.rect(foot[0] - 3, foot[1], foot[0] + 1, foot[1] + 1, col if sign > 0 else DARK)
    # Торс наклонён вперёд: плечи левее бёдер. Рубашка из лохмотьев, ребра в прорехе.
    c.poly([(11, 12 - bob), (17, 12 - bob), (20, 23 - bob), (14, 23 - bob)], METAL)
    c.poly([(12, 16 - bob), (15, 16 - bob), (17, 21 - bob), (14, 21 - bob)], AQUA)
    for y in (17, 19):
        c.line(13 + (y - 16) * 0.5, y - bob, 15.5 + (y - 16) * 0.5, y - bob, WHITE, 1)
    c.rect(14, 22 - bob, 20, 23 - bob, DARK)
    # Лохмотья по подолу: клочья свисают неровно.
    for x, ln in ((13, 2), (15, 3), (17, 1), (19, 2)):
        c.line(x, 24 - bob, x - 1, 24 - bob + ln, METAL, 1)
    # Голова набок: череп и скошенная челюсть, шея кривая, жидкие волосы.
    c.poly([(14, 11 - bob), (16, 12 - bob), (15, 13 - bob), (13, 12 - bob)], AQUA)
    c.ellipse(12.2, 7.2 - bob, 4.4, 4.0, AQUA)
    c.ellipse(10.8, 10.4 - bob, 3.0, 2.4, AQUA)
    c.set(15, 4 - bob, DARK)
    c.set(16, 5 - bob, DARK)
    c.set(15, 6 - bob, DARK)
    c.set(13, 2 - bob, DARK)
    c.set(16, 3 - bob, DARK)
    # Ближняя рука поверх торса.
    c.line(16, 15 - bob, 8, 16 - bob - s * 0.8, AQUA, 2)
    c.rect(14, 14 - bob, 16, 16 - bob, METAL)
    _claws(c, 7, 16 - bob - s * 0.8, -1)
    c.finish()
    # Лицо поверх обводки: пустые глазницы с красной искрой, рот с зубами.
    c.set(8, 8 - bob, K)
    c.set(8, 7 - bob, K)
    c.set(11, 6 - bob, K)
    c.set(11, 7 - bob, K)
    c.set(8, 7 - bob, RED)
    c.set(11, 6 - bob, RED)
    c.rect(8, 11 - bob, 11, 11 - bob, K)
    c.set(9, 11 - bob, WHITE)
    c.set(11, 11 - bob, WHITE)
    return c


def zombie_front(phase):
    """Зомби лицом к камере: идёт на игрока вразвалку, руки тянутся вперёд (кисти крупно у груди)."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.2))
    for sign in (-1, 1):
        lift = max(0.0, s * sign) * 3.0
        x = 16 + sign * 3
        c.line(x, 22 - bob, x, 28 - lift, DARK if sign < 0 else AQUA, 3)
        c.rect(x - 2, 28 - lift, x + 1, 29 - lift, DARK if sign < 0 else AQUA)
    # Торс: рубашка в клочьях, левая сторона с рёбрами, правое плечо голое.
    c.rect(12, 12 - bob, 19, 22 - bob, METAL)
    c.rect(13, 15 - bob, 15, 20 - bob, AQUA)
    for y in (16, 18):
        c.rect(13, y - bob, 15, y - bob, WHITE)
    c.rect(18, 12 - bob, 19, 14 - bob, AQUA)
    c.rect(12, 22 - bob, 19, 22 - bob, DARK)
    for x, ln in ((12, 2), (14, 3), (17, 2), (19, 1)):
        c.line(x, 23 - bob, x, 23 - bob + ln, METAL, 1)
    # Руки вперёд к зрителю: короткие предплечья, кисти крупные, пальцы растопырены.
    c.line(12, 14 - bob, 7, 18 - bob + s, METAL, 3)
    c.line(19, 14 - bob, 24, 17 - bob - s, AQUA, 3)
    for hx, hy in ((6, 19 - bob + s), (25, 18 - bob - s)):
        c.ellipse(hx, hy, 2.4, 2.4, AQUA)
        for dx in (-2, 0, 2):
            c.set(hx + dx, hy - 3, AQUA)
    # Голова набок: череп съехал влево, шея кривая, челюсть отвисла.
    c.rect(14, 11 - bob, 17, 12 - bob, AQUA)
    c.ellipse(14.0, 7.0 - bob, 5.0, 4.6, AQUA)
    c.ellipse(15.0, 11.0 - bob, 3.0, 2.2, AQUA)
    c.set(18, 3 - bob, DARK)
    c.set(17, 3 - bob, DARK)
    c.set(12, 2 - bob, DARK)
    c.finish()
    c.set(12, 7 - bob, K)
    c.set(12, 6 - bob, K)
    c.set(16, 5 - bob, K)
    c.set(16, 6 - bob, K)
    c.set(12, 7 - bob, RED)
    c.set(16, 5 - bob, RED)
    c.rect(13, 10 - bob, 16, 11 - bob, K)
    c.set(14, 10 - bob, WHITE)
    c.set(16, 10 - bob, WHITE)
    return c


# --- Вещи --------------------------------------------------------------------------------------

def coin(i):
    """Банка консервов крутится: шесть кадров, красная этикетка с жёлтой каймой и белым пятном
    уходит за край, крышка с золотым кольцом, блик по ребру."""
    c = Canvas()
    cx = 15.5
    a = math.pi * i / 3.0
    c.rect(9, 9, 22, 24, METAL)
    c.ellipse(cx, 9, 6.8, 2.2, GREY)
    c.ellipse(cx, 24, 6.8, 2.2, METAL)
    c.rect(9, 12, 22, 21, RED)
    c.rect(9, 12, 22, 12, GOLD)
    c.rect(9, 21, 22, 21, GOLD)
    k = math.cos(a)
    if k > 0.25:
        lx = cx + 5.5 * math.sin(a)
        c.rect(lx - 3 * k, 14, lx + 3 * k, 19, WHITE)
        c.rect(lx - 2 * k, 15, lx + 2 * k, 15, RED)
        c.rect(lx - 2 * k, 17, lx + 1 * k, 17, RED)
    c.ellipse(cx, 9, 3.0, 1.0, METAL)
    c.rect(cx - 1, 8, cx, 8, GOLD)
    c.rect(10, 10, 10, 23, WHITE)
    return c.finish()


def flag(i):
    """Флаг убежища на жёрдочке: зелёное полотнище с белым крестом идёт волной, на навершии
    жёлтый огонёк."""
    c = Canvas()
    c.rect(5, 3, 6, 31, METAL)
    c.ellipse(5.5, 2, 2, 2, GOLD)
    top = []
    bottom = []
    for x in range(8, 29):
        w = math.sin(x * 0.45 - i * math.pi / 3.0) * 1.6 * (x - 8) / 20.0
        top.append((x, 5 + w))
        bottom.append((x, 19 + w))
    c.poly(top + bottom[::-1], AQUA)
    c.shade()
    c.outline()
    mid = math.sin(17 * 0.45 - i * math.pi / 3.0) * 0.9
    # Белый крест посередине полотнища.
    c.rect(16, 7 + mid, 17, 17 + mid, WHITE)
    c.rect(12, 10 + mid, 21, 11 + mid, WHITE)
    c.rect(11, 5, 11, 5, AQUA)
    return c


def heart():
    """Жизнь в HUD: красное сердце с белым бликом и тёмными стежками шва."""
    c = Canvas()
    c.ellipse(11, 12, 5.5, 5.5, RED)
    c.ellipse(20, 12, 5.5, 5.5, RED)
    c.poly([(5, 14), (26, 14), (15.5, 26)], RED)
    c.rect(9, 9, 10, 10, WHITE)
    c.finish()
    for x, y in ((14, 8), (16, 10), (18, 12), (15, 12), (17, 14)):
        c.set(x, y, PLUM if (x + y) % 2 == 0 else DARK)
    return c


def ground(inner=False):
    """Грязь с камешками и костями; сверху жухлая трава, местами обожжённая до коричневого."""
    c = Canvas()
    c.rect(0, 0, 31, 31, TAN)
    # Тёмные пласты и крапины: узор повторяется по обеим осям, плитка стыкуется.
    for y in range(32):
        for x in range(32):
            h = (x * 7 + y * 13 + (x * y) % 5) % 23
            if h in (0, 1) or (y % 11 == 6 and (x + y) % 5 < 2):
                c.set(x, y, DARK)
            elif h == 2:
                c.set(x, y, BRASS)
    for x, y in ((6, 14), (22, 22), (13, 28)):
        c.ellipse(x, y, 1.6, 1.2, METAL)
        c.set(x - 1, y - 1, GREY)
    # Кусочек кости в земле.
    c.line(20, 12, 25, 14, WHITE, 1)
    c.set(19, 12, WHITE)
    c.set(19, 13, WHITE)
    c.set(26, 14, WHITE)
    c.set(26, 15, WHITE)
    if not inner:
        c.rect(0, 0, 31, 3, SEA)
        # Подбой дёрна неровный, местами свисают корешки.
        for x in range(32):
            c.set(x, 4, SEA if (x * 5 + 3) % 7 < 4 else TAN)
            if (x * 3) % 11 == 0:
                c.set(x, 5, NAVY)
        # Жухлая трава: торчащие клочки разной высоты, жёлтые и бурые.
        for x in range(32):
            h = (x * 5 + 2) % 4
            col = BRASS if x % 3 else TAN
            c.rect(x, 0, x, h - 1 if h else 0, col)
            if x % 4 == 1:
                c.set(x, 2, GOLD)
    return c


def rock():
    """Надгробие: серая плита с полукруглым верхом, высеченным крестом, трещиной и мхом, у подножия
    холмик свежей земли."""
    c = Canvas()
    c.ellipse(15.5, 29, 13, 3, TAN)
    c.rect(7, 12, 24, 29, METAL)
    c.ellipse(15.5, 12, 8.8, 6.5, METAL)
    c.rect(7, 12, 8, 29, GREY)
    c.ellipse(13, 9.5, 4, 2.5, GREY)
    # Высеченный крест.
    c.rect(15, 11, 16, 21, DARK)
    c.rect(12, 14, 19, 15, DARK)
    # Трещина и мох.
    c.line(17, 22, 15, 27, DARK, 1)
    c.line(15, 27, 18, 29, DARK, 1)
    c.rect(20, 17, 23, 18, SEA)
    c.set(21, 19, SEA)
    c.set(9, 28, SEA)
    c.set(10, 28, SEA)
    c.set(10, 27, AQUA)
    c.set(22, 17, AQUA)
    return c.finish()


def chest():
    """Армейский ящик: оливковый короб с белым крестом по трафарету, железные уголки, верёвочные
    ручки по бокам и жёлтые защёлки."""
    c = Canvas()
    c.rect(4, 9, 27, 28, SEA)
    c.rect(4, 9, 27, 9, AQUA)
    c.rect(4, 16, 27, 16, NAVY)
    c.rect(4, 17, 27, 17, GREY)
    for x in (4, 27):
        c.rect(x, 9, x, 28, METAL)
    c.rect(4, 28, 27, 28, METAL)
    # Ручки из верёвки по торцам.
    c.rect(2, 13, 3, 14, TAN)
    c.rect(28, 13, 29, 14, TAN)
    # Белый крест и защёлки.
    c.rect(15, 19, 16, 26, WHITE)
    c.rect(12, 21, 19, 22, WHITE)
    for x in (8, 23):
        c.rect(x, 14, x + 1, 17, GOLD)
        c.set(x, 14, BRASS)
    for x, y in ((6, 11), (25, 11), (6, 26), (25, 26)):
        c.set(x, y, GREY)
    return c.finish()


# --- Параллакс ---------------------------------------------------------------------------------
# Три слоя дали: у par_sky небо во весь кадр, у двух других над холмами и оградой пусто. Высоты
# периодические (256 делится на период синусов), предметы не заходят за край ленты, ленты стыкуются.
# Низ слоя сплошной.

def _hash(x, y):
    return (x * 73856093 ^ y * 19349663) % 1000


def _house(c, x, base, w, h, roof, col, lit):
    """Дом пригорода силуэтом: коробка, двускатная крыша, труба, пара окон с жёлтым светом."""
    c.rect(x, base - h, x + w, base, col)
    c.poly([(x - 1, base - h), (x + w + 1, base - h), (x + w / 2.0, base - h - roof)], col)
    c.rect(x + w - 3, base - h - roof, x + w - 2, base - h - 1, col)
    for k, (wx, wy) in enumerate(lit):
        c.rect(x + wx, base - h + wy, x + wx + 1, base - h + wy + 1, GOLD if k % 2 == 0 else BRASS)


def _dead_tree(c, x, base, h, col):
    """Мёртвое дерево: кривой ствол и голые ветви вилкой."""
    lean = (x * 7) % 5 - 2
    c.line(x, base, x + lean, base - h, col, 2)
    top = (x + lean, base - h)
    for k, (dx, dy, ln) in enumerate(((-5, -5, 1.0), (5, -7, 1.0), (-3, -9, 0.8), (4, -3, 0.7))):
        sy = base - h * (0.45 + 0.17 * k)
        sx = x + lean * (0.45 + 0.17 * k)
        c.line(sx, sy, sx + dx * ln, sy + dy * ln, col, 1)
        if k < 2:
            c.line(sx + dx * ln, sy + dy * ln, sx + dx * ln * 1.5, sy + dy * ln * 0.6 - 2, col, 1)
    c.line(top[0], top[1], top[0] + (1 if lean >= 0 else -1) * 2, top[1] - 3, col, 1)


def par_sky():
    """Дальний слой: ночное небо с большой луной в дымке тумана, звёзды и силуэт пригорода на
    горизонте с редкими жёлтыми окнами, лента 256×48, стыкуется по краям."""
    c = Canvas(256, 48)
    for y in range(48):
        for x in range(256):
            if y < 14:
                col = NAVY
            elif y < 20:
                col = SEA if (x + y) % 2 == 0 and y > 16 else NAVY
            elif y < 30:
                col = SEA
            else:
                col = SEA if (x + y) % 2 == 0 or y < 37 else AQUA
            c.set(x, y, col)
    # Звёзды россыпью по верхней части.
    for x in range(256):
        for y in range(0, 22):
            h = _hash(x, y)
            if h < 4:
                c.set(x, y, WHITE if h < 2 else SKY)
    # Луна: широкое гало в шахматку, диск, кратеры, холодный блик слева, тень справа внизу.
    mx, my = 66, 17
    for y in range(my - 20, my + 21):
        for x in range(mx - 22, mx + 23):
            r = math.hypot(x - mx, y - my)
            if 11.5 < r < 17 and (x + y) % 2 == 0 and 0 <= y < 40:
                c.set(x, y, SEA)
            elif 17 <= r < 20 and (x % 2 == 0 and y % 2 == 0) and 0 <= y < 40:
                c.set(x, y, SEA)
    c.ellipse(mx, my, 11, 11, WHITE)
    c.ellipse(mx + 3, my + 3, 8, 8, GREY)
    c.ellipse(mx - 1, my - 1, 9.5, 9.5, WHITE)
    for cx, cy, r in ((mx - 3, my - 4, 2.2), (mx + 4, my + 2, 1.8), (mx - 5, my + 4, 1.4), (mx + 2, my - 6, 1.2)):
        c.ellipse(cx, cy, r, r, GREY)
    c.rect(mx - 9, my - 4, mx - 9, my - 1, SKY)
    # Дымка поперёк луны.
    for cx, cy, rx in ((mx - 4, my + 8, 16), (mx + 9, my + 12, 14)):
        c.ellipse(cx, cy, rx, 1.5, SEA)
    # Пригород: низкие дома с крышами, голые деревья, чёрная полоса земли. Окна почти тёмные.
    base = 46
    houses = ((10, 14, 11, 7, ((3, 3), (9, 3))), (34, 11, 14, 6, ((2, 4),)), (58, 16, 9, 8, ((3, 2), (10, 2))),
              (88, 12, 12, 7, ((4, 3),)), (110, 14, 10, 7, ()), (146, 18, 12, 7, ((4, 3), (11, 3))),
              (174, 11, 15, 8, ((3, 4),)), (196, 15, 10, 6, ((2, 2), (9, 2))), (222, 13, 12, 7, ((5, 3),)))
    for hx, hw, hh, roof, lit in houses:
        _house(c, hx, base, hw, hh, roof, DARK, lit)
    for tx, th in ((26, 12), (84, 13), (132, 14), (168, 11), (214, 12), (244, 13)):
        _dead_tree(c, tx, base, th, DARK)
    c.rect(0, 44, 255, 47, DARK)
    return c


def par_far():
    """Средний слой: тёмные холмы, на самом высоком кладбищенская часовня с шпилем, мёртвые деревья
    на склонах и туман у подножия, лента 256×48, низ сплошной."""
    c = Canvas(256, 48)
    gx = 168

    def height(x):
        h = 12 + 7 * max(0.0, math.sin(x * math.pi / 64.0)) ** 2 + 3 * math.sin(x * math.pi / 16.0 + 1.0)
        h += 9 * max(0.0, math.sin((x - 40) * math.pi / 128.0)) ** 4
        t = min(1.0, max(0.0, (abs(x - gx) - 11) / 16.0))
        t = t * t * (3 - 2 * t)
        return height_plateau * (1 - t) + h * t

    height_plateau = 12 + 7 * max(0.0, math.sin(gx * math.pi / 64.0)) ** 2 + 3 * math.sin(gx * math.pi / 16.0 + 1.0) \
        + 9 * max(0.0, math.sin((gx - 40) * math.pi / 128.0)) ** 4
    for x in range(256):
        top = 47 - int(max(height(x), 3))
        c.rect(x, top, x, 47, SEA)
        c.rect(x, top, x, top, METAL)
        c.rect(x, top + 9, x, 47, NAVY)
        if (x * 5 + top) % 13 == 0:
            c.set(x, top + 3 + x % 4, NAVY)
    # Часовня: нефа с двускатной крышей, шпиль с крестом, арка двери, два окна с жёлтым светом.
    base = 47 - int(height_plateau) + 1
    c.rect(gx - 9, base - 9, gx + 2, base, DARK)
    c.poly([(gx - 10, base - 9), (gx + 3, base - 9), (gx - 3.5, base - 15)], DARK)
    c.rect(gx + 3, base - 18, gx + 8, base, DARK)
    c.poly([(gx + 2, base - 18), (gx + 9, base - 18), (gx + 5.5, base - 28)], DARK)
    c.rect(gx + 5, base - 34, gx + 6, base - 27, DARK)
    c.rect(gx + 3, base - 32, gx + 8, base - 31, DARK)
    c.rect(gx - 7, base - 6, gx - 6, base - 4, GOLD)
    c.rect(gx - 2, base - 6, gx - 1, base - 4, GOLD)
    c.rect(gx + 5, base - 14, gx + 6, base - 12, GOLD)
    c.rect(gx + 4, base - 5, gx + 7, base, K)
    c.ellipse(gx + 5.5, base - 5, 1.8, 1.8, K)
    # Мёртвые деревья на склонах, ближние выше.
    for px, h in ((18, 17), (44, 14), (74, 18), (104, 13), (128, 16), (206, 17), (232, 14), (248, 16)):
        _dead_tree(c, px, 47 - int(height(px)) + 3, h, DARK)
    # Туман у подножия.
    for cx, cy, r in ((40, 43, 14), (112, 44, 16), (176, 42, 12), (234, 44, 14)):
        for k in (0, 256, -256):
            c.ellipse(cx + k, cy, r, 1.6, AQUA if (cx // 8) % 2 else SEA)
    return c


def _cross(c, x, base, h, col, hi=METAL):
    """Крест на могиле: столб и перекладина, блик слева."""
    c.rect(x, base - h, x + 1, base, col)
    c.rect(x - 3, base - h + 3, x + 4, base - h + 4, col)
    c.rect(x, base - h, x, base - 1, hi)


def _stone(c, x, base, w, h, col, hi):
    """Надгробие со скруглённым верхом и крестиком."""
    c.rect(x, base - h, x + w, base, col)
    c.ellipse(x + w / 2.0, base - h, w / 2.0 + 0.5, 3, col)
    c.rect(x, base - h, x, base, hi)
    c.set(x + w // 2, base - h + 2, DARK)


def par_mid():
    """Ближний слой: бугристая земля кладбища, кресты, надгробия, кованая ограда с пиками и сухой
    бурьян, лента 256×32."""
    c = Canvas(256, 32)

    def crest(x):
        return int(round(14 + 2 * math.sin(x * math.pi / 32.0) + 1.5 * math.sin(x * math.pi / 8.0)))

    for x in range(256):
        top = crest(x)
        c.rect(x, top, x, 31, DARK)
        c.rect(x, top, x, top, METAL)
        c.rect(x, top + 7, x, 31, K)
        if (x * 7 + top * 3) % 19 == 0:
            c.set(x, top + 3 + x % 3, NAVY)
    # Кресты и надгробия, кое-где накренились.
    for px, kind in ((12, 0), (40, 1), (88, 0), (122, 1), (170, 0), (214, 1), (244, 0)):
        by = crest(px) + 1
        if kind == 0:
            _cross(c, px, by, 11 + px % 3, DARK)
        else:
            _stone(c, px, by, 6, 8 + px % 3, DARK, METAL)
    # Кованая ограда: два пролёта, столбы с шарами, пики.
    for x0, x1 in ((50, 80), (176, 208)):
        top = crest(x0)
        c.rect(x0, top - 7, x1, top - 6, DARK)
        c.rect(x0, top - 3, x1, top - 3, DARK)
        for x in range(x0, x1 + 1, 3):
            by = crest(x) + 1
            c.rect(x, top - 8, x, by, DARK)
            c.set(x, top - 9, METAL)
        for x in (x0, x1):
            c.rect(x - 1, top - 12, x + 1, crest(x) + 1, DARK)
            c.ellipse(x, top - 13, 1.5, 1.5, DARK)
    # Сухой бурьян: жёлтые и бурые стебли вразброс.
    for px in (24, 66, 100, 132, 150, 186, 230):
        by = crest(px) + 1
        for k, dx in enumerate((-3, -1, 1, 3)):
            c.line(px, by, px + dx, by - 6 - (k * 3) % 4, BRASS if k % 2 else TAN, 1)
        c.set(px - 3, by - 6, GOLD)
        c.set(px + 3, by - 9, GOLD)
    return c


def sprites():
    """Ленты основы набора в палитре `PALETTE`: герой платформера, зомби, вещи, земля, три слоя
    дали. Ключи, размеры и число кадров те же, что у `castles16.sprites()`. Ленты демок лежат в
    модулях `zombies_*16.py`."""
    return {
        "enemy_walk": strip([zombie_side(p) for p in base.phases()]),
        "enemy_front": strip([zombie_front(p) for p in base.phases()]),
        "coin": strip([coin(i) for i in range(6)]),
        "flag": strip([flag(i) for i in range(6)]),
        "heart": heart(),
        "ground": ground(),
        "ground_inner": ground(inner=True),
        "rock": rock(),
        "chest": chest(),
        "par_sky": par_sky(),
        "par_far": par_far(),
        "par_mid": par_mid(),
        "hero_run": strip([hero_side(p) for p in base.phases()]),
        "hero_jump": hero_side(0.0, jump=True),
        "hero_leap": strip([hero_leap(i) for i in range(4)]),
        "hero_idle": strip([hero_idle(i) for i in range(2)]),
        "hero_back": strip([hero_back(p) for p in base.phases()]),
        "hero_slide": strip([hero_slide(i) for i in range(2)]),
        "hero_hang": strip([hero_hang(i) for i in range(2)]),
        "hero_crouch": strip([hero_crouch(i) for i in range(2)]),
    }


# --- Остальные слоты (ленты демок «тропа» и «до выхода» их берут) ------------------------------

def raven(i):
    """Ворон (слот попугая) летит вправо: четыре кадра взмаха (вверх, середина, вниз, середина),
    тело по центру кадра. Без красной обводки опасности: её кладёт модуль демки."""
    c = Canvas()
    wing = (-9, -3, 6, -3)[i]
    # Дальнее крыло темнее и чуть смещено, ближнее поверх; края перьев зубчатые.
    for dx, col in ((-3, NAVY), (0, METAL)):
        pts = [(13 + dx, 17), (19 + dx, 17)]
        xs = list(range(24, 6, -2))
        for k, x in enumerate(xs):
            edge = abs(x - 15.5 - dx) / 9.0
            tip = k % 2 == 0
            pts.append((x + dx, 17 + wing * (1.5 if tip else 0.9) * edge))
        c.poly(pts, col)
        c.line(14 + dx, 17, 7 + dx, 17 + wing * 1.3, DARK, 1)
    # Хвост клином, тело, грудь с отливом, голова с клювом.
    c.poly([(12, 17), (4, 17), (3, 21), (12, 20)], DARK)
    c.ellipse(15.5, 18.5, 5.5, 3.6, DARK)
    c.ellipse(17, 19.5, 3, 1.8, METAL)
    c.ellipse(21.5, 15.5, 3.0, 2.8, DARK)
    c.poly([(23, 14), (28, 15.5), (23, 17.5)], GOLD)
    c.finish()
    c.set(22, 14, RED)
    c.set(23, 14, RED)
    return c


def crawler(i):
    """Ползущая кисть (слот краба) идёт вправо на кончиках пальцев: четыре кадра, пальцы ходят
    по очереди, из запястья торчит кость. Кожа зелёно-серая, ногти костяные."""
    c = Canvas()
    bob = (0, 1, 0, 1)[i]
    # Пальцы как лапы паука: исходная точка, колено над землёй, кончик на земле.
    legs = (((19, 18), (25, 15), (29, 28)), ((18, 21), (23, 20), (25, 28)),
            ((11, 21), (7, 20), (5, 28)), ((14, 22), (11, 24), (12, 29)))
    for k, (o, kn, tp) in enumerate(legs):
        up = 3 if (i + k) % 4 < 2 else 0
        tip = (tp[0] + (2 if up else 0), tp[1] - up)
        knee = (kn[0], kn[1] - up // 2 + bob)
        c.line(o[0], o[1] + bob, knee[0], knee[1], AQUA if k % 2 == 0 else SEA, 2)
        c.line(knee[0], knee[1], tip[0], tip[1], AQUA if k % 2 == 0 else SEA, 2)
        c.set(tip[0], tip[1], WHITE)
    # Ладонь и обрубок запястья с костью и рваным рукавом.
    c.ellipse(15, 19.5 + bob, 6.5, 3.2, AQUA)
    for o, _, _ in legs:
        c.set(o[0], o[1] + bob - 1, GREY)
    c.poly([(10, 16 + bob), (4, 11 + bob), (6, 9 + bob), (12, 15 + bob)], AQUA)
    c.poly([(8, 14 + bob), (3, 10 + bob), (5, 7 + bob), (10, 12 + bob)], METAL)
    c.rect(3, 6 + bob, 4, 8 + bob, WHITE)
    c.set(5, 8 + bob, RED)
    c.set(6, 10 + bob, RED)
    return c.finish()


def key():
    """Ключ от убежища: жёлтый, с красной биркой на кольце."""
    c = Canvas(32, 32)
    c.ellipse(10, 16, 7, 7, GOLD)
    c.ellipse(10, 16, 3, 3, None)
    c.rect(16, 14, 29, 17, GOLD)
    c.rect(24, 18, 25, 22, GOLD)
    c.rect(28, 18, 29, 21, GOLD)
    c.rect(16, 14, 29, 14, WHITE)
    c.rect(3, 22, 7, 27, RED)
    c.set(5, 24, WHITE)
    return c.finish()


def medkit():
    """Аптечка: белая коробка с красным крестом, ручка сверху, серые уголки."""
    c = Canvas(32, 32)
    c.rect(5, 10, 26, 27, WHITE)
    c.rect(12, 6, 19, 8, METAL)
    c.rect(11, 8, 12, 10, METAL)
    c.rect(19, 8, 20, 10, METAL)
    c.rect(5, 26, 26, 27, GREY)
    c.rect(5, 10, 26, 10, SKY)
    c.rect(14, 13, 17, 24, RED)
    c.rect(10, 17, 21, 20, RED)
    c.set(5, 10, GREY)
    c.set(26, 10, GREY)
    return c.finish()


def nail():
    """Гвоздь летит вправо: плоская шляпка сзади, стальное тело, острое жало. 16×16."""
    c = Canvas(16, 16)
    c.rect(1, 5, 2, 10, METAL)
    c.line(3, 7, 11, 7, METAL, 1)
    c.line(3, 8, 11, 8, GREY, 1)
    c.poly([(11, 6), (15, 8), (11, 9)], WHITE)
    c.rect(3, 7, 10, 7, WHITE)
    return c.finish()


def extras():
    """Слоты зомби вне `sprites()`: ленты и вещи тех же размеров, что у космоса, пиратов и замков."""
    return {
        "parrot_fly": strip([raven(i) for i in range(4)]),
        "crab_walk": strip([crawler(i) for i in range(4)]),
        "key": key(),
        "medkit": medkit(),
        "shot": nail(),
    }


def shaded(items):
    """Ленты в палитре `PALETTE` → {ключ: (холст, палитра)} как в игре: силуэты получают
    светотень рампами (`pixel_sprites16.reshade`), сплошные плитки остаются в палитре сеттинга."""
    out = {}
    for key, canvas in items.items():
        if base.wants_reshade(key, canvas):
            out[key] = base.reshade(canvas, PALETTE, GROUPS)
        else:
            out[key] = (canvas, PALETTE)
    return out


def save_sheet(path, items, scale=3, pad=6, back=(0x1B, 0x1A, 0x33, 255), max_w=640):
    """Лист для просмотра: `items` это {ключ: (холст, палитра)}, лента на строку; ленты шире
    `max_w` режутся на строки по `max_w`."""
    width = (min(max(c.w for c, _ in items.values()), max_w) + 2 * pad) * scale
    blank = list(back) * width
    rows = [blank[:] for _ in range(pad * scale)]
    for key, (canvas, palette) in items.items():
        for x0 in range(0, canvas.w, max_w):
            part = Canvas(min(max_w, canvas.w - x0), canvas.h)
            for y in range(canvas.h):
                part.px[y] = canvas.px[y][x0:x0 + part.w]
            for row in base.rgba_rows(part, palette, scale, back):
                line = list(back) * pad * scale + row
                rows.append(line + list(back) * ((len(blank) - len(line)) // 4))
            rows.extend(blank[:] for _ in range(pad * scale))
    with open(path, "wb") as f:
        f.write(png_bytes(width, len(rows), rows))
    print("лист: %s" % path)


def preview(path, scale=4, keys=None, back=(0x6E, 0x9C, 0xC0, 255)):
    """Лист набора: лента на строку после светотени, затем `extras()`. Фон голубой, как небо
    за кадром игры: на тёмном не видно, держит ли обводка. `keys` оставляет часть лент."""
    items = shaded(sprites())
    items.update(shaded(extras()))
    if keys:
        items = {k: v for k, v in items.items() if k in keys}
    save_sheet(path, items, scale=scale, back=back, max_w=256)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        args = sys.argv
        scale = 4
        keys = None
        for a in args:
            if a.startswith("--scale="):
                scale = int(a.split("=", 1)[1])
            if a.startswith("--keys="):
                keys = a.split("=", 1)[1].split(",")
        preview(args[args.index("--preview") + 1], scale, keys)
