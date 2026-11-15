#!/usr/bin/env python3
"""Набор «Замки» для 16/32-bit (основа, зеркало `space16.py`): дневное сказочное средневековье,
рыцарь в стальных латах с красным плюмажем и красным табардом, стражники вражеского замка в чёрной
кольчуге. Те же ленты, размеры и число кадров, что у космоса и пиратов (`space16.sprites()`);
позы героя повторяют космонавта кадр в кадр, чтобы хитбоксы демок сходились: меняется рисунок,
не геометрия. Зелёные холмы, замок с башнями на горизонте, ели и дубы; неба и моря нет.

Слоты космоса и их замки: космонавт это рыцарь, пришелец это стражник с алебардой, кристалл это
золотая монета с короной, флаг экспедиции это знамя с гербом, грузовая капсула это окованный
ларь, метеорит это замшелый валун, настил станции это кладка с травой. Ленты, которых нет в
`sprites()` (летучая мышь вместо попугая-дрона, кабан вместо краба, ключ, зелье вместо аптечки,
арбалетный болт), лежат в `extras()` тех же размеров, что у космоса и пиратов.

Имена и порядок цветов те же, что у `space16.py` (по ним модули демок `castles_*16.py` берут цвета
по роли): K обводка, NAVY тёмная хвоя, SEA зелень холмов, AQUA яркая трава, SKY дымка и блики,
WHITE светлая сталь, GREY тень стали, SKIN и TAN кожа и дерево, GOLD и BRASS золото, METAL камень,
DARK чёрное железо и кольчуга, RED герб и плюмаж, VIOLET и PLUM багрянец стражи.

    python3 tools/castles16.py --preview out.png   # лист набора в 4 раза крупнее
    python3 tools/castles16.py --preview out.png --scale=6 --keys=hero_run,hero_idle
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pixel_sprites16 as base  # noqa: E402
from pixel_sprites import png_bytes  # noqa: E402

# Палитра «Замки»: 16 цветов, индекс это та же роль, что у пиратов и космоса.
K, NAVY, SEA, AQUA, SKY, WHITE, GREY, SKIN, TAN, GOLD, BRASS, METAL, DARK, RED, VIOLET, PLUM = range(16)
PALETTE = [
    (0x15, 0x10, 0x16),  # K      обводка
    (0x1C, 0x40, 0x38),  # NAVY   тёмная хвоя, тень зелени
    (0x38, 0x8A, 0x4A),  # SEA    зелень холмов, дубовая листва
    (0x8F, 0xCF, 0x58),  # AQUA   яркая трава, блик листвы
    (0xD6, 0xEC, 0xF2),  # SKY    дымка вдали, блик стали
    (0xE6, 0xEA, 0xF0),  # WHITE  светлая сталь лат
    (0xA3, 0xAB, 0xBC),  # GREY   тень стали
    (0xF2, 0xC8, 0x9A),  # SKIN   кожа
    (0xB8, 0x7C, 0x4A),  # TAN    дерево, тень кожи
    (0xF4, 0xD3, 0x5E),  # GOLD   золото гербов, пояс
    (0xC0, 0x8A, 0x2A),  # BRASS  тень золота
    (0x7A, 0x80, 0x8E),  # METAL  камень стен, перчатки
    (0x3B, 0x36, 0x44),  # DARK   чёрное железо, кольчуга, подошвы
    (0xD0, 0x34, 0x38),  # RED    герб, плюмаж, табард
    (0x9A, 0x2C, 0x4C),  # VIOLET багровая туника стражи
    (0x5A, 0x16, 0x34),  # PLUM   тень багрянца, плащ
]
SHADOW = {SEA: NAVY, AQUA: SEA, SKY: AQUA, WHITE: GREY, GREY: METAL, SKIN: TAN, TAN: DARK, GOLD: BRASS,
          BRASS: DARK, METAL: DARK, RED: PLUM, VIOLET: PLUM}
# Материалы для светотени рампами: латы одна сталь, зелень, кожа и дерево, золото, камень и
# железо, красное, багрянец стражи.
GROUPS = {WHITE: "steel", GREY: "steel", SKY: "steel", NAVY: "leaf", SEA: "leaf", AQUA: "leaf",
          SKIN: "skin", TAN: "wood", GOLD: "gold", BRASS: "gold", METAL: "stone", DARK: "iron", RED: "red",
          VIOLET: "guard", PLUM: "guard"}


class Canvas(base.Canvas):
    shadow = SHADOW


def strip(frames):
    out = Canvas(sum(f.w for f in frames), max(f.h for f in frames))
    x = 0
    for f in frames:
        out.paste(f, x, 0)
        x += f.w
    return out


# --- Рыцарь ------------------------------------------------------------------------------------
# Силуэт как у космонавта (те же позы и габариты), но рисунок свой: стальные серые латы с белым
# бликом по краю, вытянутый шлем с плоским верхом и выступающим забралом, красный гребень
# плюмажа, сплошной красный табард с золотым поясом. Плащ за спиной узкой тёмно-красной полоской.

def _helmet(c, x, y, face=1):
    """Шлем лицом вправо при `face` 1: вытянутый, плоский верх, забрало выступает вперёд, тёмная
    прорезь во всю переднюю половину, ниже дыхательные точки. Центр (x, y), нижний край y+5."""
    c.ellipse(x - 0.5 * face, y + 0.5, 5.4, 4.8, GREY)
    c.rect(x - 4, y - 4, x + 4, y - 3, GREY)
    # Забрало: выступ вперёд на два пикселя за обвод шлема.
    a, b = sorted((x + 3 * face, x + 7 * face))
    c.rect(a, y - 2, b, y + 2, GREY)
    # Прорезь: две строки от лба до края забрала (чёрный, не тон стали).
    a, b = sorted((x + 1 * face, x + 6 * face))
    c.rect(a, y - 1, b, y, K)
    # Дыхательные отверстия: три точки.
    for dx, dy in ((3, 3), (5, 1 + 1), (4, 4)):
        c.set(x + dx * face, y + dy + (1 if dy == 2 else 0), K)
    c.rect(x - 4, y + 4, x + 3, y + 4, METAL)
    c.rect(x - 3, y + 5, x + 3, y + 5, METAL)
    # Блик по верху и переднему краю.
    c.rect(x - 3, y - 4, x + 1, y - 4, WHITE)
    c.set(x - 4 * face, y - 2, WHITE)
    c.set(x - 4 * face, y - 1, WHITE)
    _plume(c, x, y, face)


def _plume(c, x, y, face=1):
    """Красный гребень по верху шлема от лба к затылку, 3-4 пикселя высотой, и хвост назад."""
    for dx in range(-4, 3):
        h = 3 if -2 <= dx <= 1 else 2
        c.rect(x + dx * face, y - 5 - h + 1, x + dx * face, y - 5, RED)
    c.line(x - 4 * face, y - 5, x - 7 * face, y - 1, RED, 2)
    c.line(x - 7 * face, y - 1, x - 7 * face, y + 2, RED, 1)


def _pack(c, x, y0, y1):
    """За спиной: узкая тёмно-красная полоска плаща и ножны меча с золотым наконечником."""
    c.rect(x + 1, y0 + 1, x + 2, y1 + 1, PLUM)
    c.line(x + 2, y1 - 1, x - 1, y1 + 4, DARK, 2)
    c.set(x - 1, y1 + 4, GOLD)


def _body(c, x0, y0, x1, y1, skirt=2):
    """Корпус: стальная рама, сплошной красный табард от плеч до середины бедра, золотой пояс и
    одна золотая точка герба на груди."""
    c.rect(x0, y0, x1, y1, GREY)
    c.rect(x0 + 1, y0 + 1, x1 - 1, y1 + skirt, RED)
    c.rect(x0, y1 - 2, x1, y1 - 1, GOLD)
    c.set((x0 + x1) // 2 + 1, y0 + 3, GOLD)
    c.rect(x0, y0, x1, y0, WHITE)


def _boot(c, x, y, w=4):
    c.rect(x - 1, y - 1, x + w - 2, y - 1, METAL)
    c.rect(x - 1, y, x + w - 1, y + 1, DARK)


def _arm(c, x0, y0, x1, y1, col):
    """Рука в латах с перчаткой. Ближняя (GREY) узкая в два пикселя, дальняя (METAL) в три."""
    c.line(x0, y0, x1, y1, col, 2 if col == GREY else 3)
    c.ellipse(x1, y1, 1.4, 1.4, METAL if col == GREY else DARK)


def knight_side(phase, jump=False):
    """Рыцарь сбоку, лицом вправо: бег по фазе 0..2π или прыжок."""
    c = Canvas()
    bob = 0 if jump else int(round(abs(math.sin(phase)) * 1.4))
    hip_y = 21 - bob
    swing = 0.9 if jump else math.sin(phase)
    _arm(c, 15, 15 - bob, 15 + 5 * swing, 20 - bob - (3 if jump else 0), METAL)
    for sign, cloth in ((-1, METAL), (1, GREY)):
        a = swing * sign
        lift = max(0.0, math.cos(phase) * sign) * 3.0 if not jump else (4 if sign > 0 else 1)
        foot = (15 + 6 * a, 29 - lift)
        knee = ((15 + foot[0]) / 2 + 2, (hip_y + foot[1]) / 2)
        c.line(15 + sign, hip_y, knee[0], knee[1], cloth, 4)
        c.line(knee[0], knee[1], foot[0], foot[1], cloth, 4)
        _boot(c, foot[0], foot[1])
    _pack(c, 8, 13 - bob, 19 - bob)
    _body(c, 11, 13 - bob, 19, hip_y)
    _arm(c, 16, 15 - bob, 16 - 5 * swing, 20 - bob - (4 if jump else 0), GREY)
    _helmet(c, 16, 7 - bob)
    return c.finish()


def knight_back(phase):
    """Со спины: бежит вглубь экрана, красный табард во всю спину, плюмаж вдоль затылка, прорези
    нет."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.4))
    for sign in (-1, 1):
        lift = max(0.0, s * sign) * 4.0
        x = 16 + sign * 3
        c.rect(x - 2, 21 - bob, x + 1, 28 - lift, GREY if sign > 0 else METAL)
        _boot(c, x - 1, 28 - lift)
        _arm(c, 16 + sign * 6, 15 - bob, 16 + sign * 7, 20 - bob + s * sign * 2, GREY if sign > 0 else METAL)
    c.rect(11, 13 - bob, 20, 21 - bob, GREY)
    c.rect(12, 14 - bob, 19, 22 - bob, RED)
    c.rect(11, 19 - bob, 20, 20 - bob, GOLD)
    c.rect(15, 21 - bob, 16, 22 - bob, PLUM)
    # Вытянутый шлем со спины: плоский верх, затылочный шов, гребень вдоль всей макушки.
    c.ellipse(15.5, 7.5 - bob, 5.4, 4.8, GREY)
    c.rect(11, 3 - bob, 20, 4 - bob, GREY)
    c.rect(11, 11 - bob, 20, 12 - bob, METAL)
    c.rect(12, 5 - bob, 19, 5 - bob, WHITE)
    c.rect(15, 1 - bob, 16, 11 - bob, RED)
    c.rect(14, 3 - bob, 17, 9 - bob, RED)
    c.rect(15, 12 - bob, 16, 13 - bob, RED)
    return c.finish()


def knight_leap(i):
    """Прыжок через клетку, четыре кадра: присел, толчок, поджал ноги, приземление."""
    c = Canvas()
    crouch = (3, 0, -1, 2)[i]
    legs = ((2, 2), (5, -4), (3, -1), (4, 3))[i]
    hip_y = 21 + crouch
    _arm(c, 15, 15 + crouch, 12 - i % 2, 11 + crouch if i in (1, 2) else 20 + crouch, METAL)
    for sign, cloth in ((-1, METAL), (1, GREY)):
        foot = (15 + sign * legs[0] + (2 if i == 1 else 0), 29 if i in (0, 3) else 27 - (2 if i == 2 else 0))
        knee = ((15 + foot[0]) / 2 + 2 + legs[1] * 0.3, (hip_y + foot[1]) / 2 + (2 if i == 2 else 0))
        c.line(15 + sign, hip_y, knee[0], knee[1], cloth, 4)
        c.line(knee[0], knee[1], foot[0], foot[1], cloth, 4)
        _boot(c, foot[0], foot[1])
    _pack(c, 8, 13 + crouch, 19 + crouch)
    _body(c, 11, 13 + crouch, 19, hip_y)
    _arm(c, 16, 15 + crouch, 20 + i % 2, 10 + crouch if i in (1, 2) else 20 + crouch, GREY)
    _helmet(c, 16, 7 + crouch)
    return c.finish()


def knight_idle(i):
    """Стойка: два кадра, рыцарь дышит."""
    c = Canvas()
    up = i
    for sign, cloth in ((-1, METAL), (1, GREY)):
        x = 15 + sign * 2
        c.rect(x - 1, 21, x + 1, 28, cloth)
        _boot(c, x, 29)
    _arm(c, 14, 15 - up, 13, 21 - up, METAL)
    _pack(c, 8, 13 - up, 19 - up)
    _body(c, 11, 13 - up, 19, 21)
    _arm(c, 17, 15 - up, 18, 21 - up, GREY)
    _helmet(c, 16, 7 - up)
    return c.finish()


def _lean(c, sx, sy, hx, hy, w):
    """Корпус под наклоном: от плеч (sx, sy) к бёдрам (hx, hy), ширина w; сталь по краям, красный
    табард посередине, золотой пояс у бёдер."""
    n = math.hypot(hx - sx, hy - sy)
    dx, dy = (hx - sx) / n, (hy - sy) / n
    for k in range(int(n) + 1):
        x, y = sx + dx * k, sy + dy * k
        col = GOLD if k >= int(n) - 1 else GREY
        c.line(x + dy * w / 2, y - dx * w / 2, x - dy * w / 2, y + dx * w / 2, col, 2)
        if k < int(n) - 1:
            c.line(x + dy * (w / 2 - 1), y - dx * (w / 2 - 1), x - dy * (w / 2 - 1), y + dx * (w / 2 - 1), RED, 2)


def knight_slide(i):
    """Подкат на боку ногами вперёд: корпус откинут, ближняя нога вытянута, дальняя коленом вверх,
    рука сзади на земле. Макушка шлема на 15-й строке, как у матроса. Два кадра: колено и пыль."""
    c = Canvas()
    c.line(19, 27, 24, 23 - i, METAL, 3)
    c.line(24, 23 - i, 27, 27, METAL, 3)
    _boot(c, 27, 27)
    c.line(13, 24, 19, 23, METAL, 2)
    _lean(c, 12, 24, 19, 27, 6)
    c.line(19, 28, 28, 28, GREY, 4)
    c.line(20, 27, 27, 27, WHITE, 1)
    c.rect(28, 26, 30, 29, DARK)
    _arm(c, 11, 25, 6, 29, GREY)
    _helmet(c, 10, 21)
    c.finish()
    for k, (x, y) in enumerate(((2, 30), (4, 31), (1, 28), (3, 29))):
        if (k + i) % 2 == 0:
            c.set(x, y, GREY)
    return c


def knight_crouch(i):
    """Присед: та же фигура, сложенная вниз, корпус прямо, колени вперёд. Два кадра шага."""
    c = Canvas()
    step = (-1, 1)[i]
    c.line(15, 24, 19, 26, METAL, 2)
    for sign, cloth in ((-1, METAL), (1, GREY)):
        hip = (14, 27)
        knee = (20 - sign + step * sign, 26)
        foot = (17 - sign * 2 + step * sign * 2, 29)
        c.line(hip[0], hip[1], knee[0], knee[1], cloth, 4)
        c.line(knee[0], knee[1], foot[0], foot[1], cloth, 3)
        _boot(c, foot[0], foot[1])
    _pack(c, 8, 22, 26)
    _body(c, 11, 22, 18, 26, skirt=0)
    _arm(c, 14, 24, 19, 26, GREY)
    _helmet(c, 16, 19)
    return c.finish()


def knight_hang(i):
    """На тросе: руки вверх к точке хвата (центр сверху), ноги свисают и качаются."""
    c = Canvas()
    sw = (-1, 1)[i]
    c.line(14, 13, 15, 1, METAL, 3)
    c.line(18, 13, 17, 1, GREY, 2)
    c.ellipse(15, 1, 1.2, 1.2, METAL)
    c.ellipse(17, 1, 1.2, 1.2, METAL)
    _pack(c, 8, 13, 19)
    _body(c, 11, 13, 20, 21, skirt=0)
    for sign, cloth in ((-1, METAL), (1, GREY)):
        foot = (15.5 + sign * 2 + sw * 2, 29)
        c.line(15.5 + sign * 2, 21, foot[0], foot[1], cloth, 3)
        _boot(c, foot[0], foot[1], 3)
    c.finish()
    hd = Canvas()
    _helmet(hd, 16, 8)
    hd.finish()
    for y in range(hd.h):
        for x in range(hd.w):
            if hd.px[y][x] is not None and y >= 1:
                c.set(x, y, hd.px[y][x])
    return c


# --- Стражник ----------------------------------------------------------------------------------
# Пехотинец вражеского замка: шлем-котелок с полями, чёрная кольчуга (шахматка из серых звеньев),
# багровая туника, алебарда с топором и крюком. Шаг и рост повторяют пришельца.

def _mail(c, x0, y0, x1, y1):
    """Кольчуга: на тёмном железе шахматка из звеньев."""
    for y in range(int(y0), int(y1) + 1):
        for x in range(int(x0), int(x1) + 1):
            if (x + y) % 2 == 0 and c.get(x, y) == DARK:
                c.set(x, y, METAL)


def guard_side(phase):
    """Стражник сбоку, лицом влево (навстречу герою): шаг по фазе, алебарда в ближней руке."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.2))
    c.line(17, 15 - bob, 17 + 4 * s, 20 - bob, METAL, 2)
    for sign, col in ((-1, PLUM), (1, VIOLET)):
        a = s * sign
        lift = max(0.0, math.cos(phase) * sign) * 2.5
        foot = (16 - 5 * a, 29 - lift)
        knee = ((16 + foot[0]) / 2 - 1.5, (22 - bob + foot[1]) / 2)
        c.line(16, 22 - bob, knee[0], knee[1], col, 3)
        c.line(knee[0], knee[1], foot[0], foot[1], col, 2)
        c.rect(foot[0] - 3, foot[1], foot[0], foot[1] + 1, DARK)
    # Тело: туника поверх кольчуги, пояс, подол.
    c.rect(13, 12 - bob, 18, 21 - bob, DARK)
    c.rect(13, 14 - bob, 18, 20 - bob, VIOLET)
    c.rect(13, 20 - bob, 18, 20 - bob, DARK)
    c.set(14, 20 - bob, GOLD)
    c.rect(13, 21 - bob, 18, 23 - bob, VIOLET)
    _mail(c, 13, 12 - bob, 18, 13 - bob)
    # Голова: кольчужный капюшон, лицо, котелок с полями.
    c.ellipse(16.5, 10.5 - bob, 4, 3, DARK)
    c.ellipse(13, 9.5 - bob, 3, 2.5, SKIN)
    c.ellipse(15.5, 4.5 - bob, 5.5, 3.8, METAL)
    c.ellipse(15.5, 7.3 - bob, 7.5, 1.2, GREY)
    c.set(13, 2 - bob, WHITE)
    c.set(14, 2 - bob, WHITE)
    c.set(12, 3 - bob, WHITE)
    # Алебарда: древко от земли, спица, топор и крюк. Ближняя рука держит её.
    c.line(7, 29, 7, 3 - bob, TAN, 1)
    c.rect(7, 0, 7, 3 - bob, GREY)
    c.poly([(7, 3 - bob), (2, 4 - bob), (2, 8 - bob), (7, 9 - bob)], GREY)
    c.line(3, 5 - bob, 3, 7 - bob, WHITE, 1)
    c.rect(8, 5 - bob, 9, 5 - bob, GREY)
    c.line(15, 15 - bob, 8, 17 - bob, DARK, 3)
    c.ellipse(7.5, 17 - bob, 1.5, 1.5, METAL)
    c.finish()
    c.set(11, 9 - bob, K)
    return c


def guard_front(phase):
    """Стражник лицом к камере: идёт на игрока, ноги по очереди, алебарда у правого плеча."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.2))
    c.line(11, 14 - bob, 8, 20 - bob + s * 2, DARK, 2)
    for sign in (-1, 1):
        lift = max(0.0, s * sign) * 3.0
        x = 16 + sign * 3
        c.line(x, 22 - bob, x, 28 - lift, VIOLET if sign > 0 else PLUM, 3)
        c.rect(x - 2, 28 - lift, x + 1, 29 - lift, DARK)
    c.rect(12, 12 - bob, 19, 21 - bob, DARK)
    c.rect(13, 14 - bob, 18, 20 - bob, VIOLET)
    c.rect(12, 20 - bob, 19, 20 - bob, DARK)
    c.rect(15, 20 - bob, 16, 20 - bob, GOLD)
    c.rect(12, 21 - bob, 19, 23 - bob, VIOLET)
    _mail(c, 12, 12 - bob, 19, 13 - bob)
    c.ellipse(15.5, 11 - bob, 5, 2.8, DARK)
    c.ellipse(15.5, 9.8 - bob, 3.5, 2.6, SKIN)
    c.ellipse(15.5, 4.5 - bob, 6, 3.8, METAL)
    c.ellipse(15.5, 7.4 - bob, 8, 1.2, GREY)
    c.set(13, 2 - bob, WHITE)
    c.set(14, 2 - bob, WHITE)
    c.set(12, 3 - bob, WHITE)
    # Алебарда справа, топор тянется наружу.
    c.line(25, 29, 25, 3 - bob, TAN, 1)
    c.rect(25, 0, 25, 3 - bob, GREY)
    c.poly([(25, 3 - bob), (30, 4 - bob), (30, 8 - bob), (25, 9 - bob)], GREY)
    c.line(29, 5 - bob, 29, 7 - bob, WHITE, 1)
    c.line(19, 14 - bob, 24, 18 - bob, DARK, 3)
    c.ellipse(24.5, 18 - bob, 1.5, 1.5, METAL)
    c.finish()
    c.set(14, 9 - bob, K)
    c.set(17, 9 - bob, K)
    return c


# --- Вещи --------------------------------------------------------------------------------------

def coin(i):
    """Золотая монета с короной вращается: шесть кадров, ширина по косинусу, ребро темнее."""
    c = Canvas()
    rx = max(1.0, abs(math.cos(math.pi * i / 6.0)) * 7.0)
    cx = 15.5
    c.ellipse(cx, 16, rx, 10.5, BRASS)
    if rx > 2:
        c.ellipse(cx, 16, rx - 1.3, 9.2, GOLD)
    if rx > 3:
        k = rx / 7.0
        # Корона: основание и три зубца с шариками.
        c.poly([(cx - 4 * k, 20), (cx + 4 * k, 20), (cx + 4.5 * k, 13), (cx + 2 * k, 16),
                (cx, 12), (cx - 2 * k, 16), (cx - 4.5 * k, 13)], BRASS)
        c.rect(cx - 4 * k, 20, cx + 4 * k, 21, BRASS)
        c.set(cx, 11, WHITE)
        c.set(cx - 4.5 * k, 12, WHITE)
        c.set(cx + 4.5 * k, 12, WHITE)
        c.set(cx, 17, WHITE)
        c.line(cx - rx * 0.6, 8, cx - rx * 0.3, 7, WHITE, 1)
    return c.finish()


def flag(i):
    """Знамя на древке с золотым навершием: красное полотнище с ласточкиным хвостом и золотым
    крестом-гербом идёт волной."""
    c = Canvas()
    c.rect(5, 3, 6, 31, TAN)
    c.ellipse(5.5, 2, 2, 2, GOLD)
    top = []
    bottom = []
    for x in range(8, 29):
        w = math.sin(x * 0.45 - i * math.pi / 3.0) * 1.6 * (x - 8) / 20.0
        top.append((x, 5 + w))
        bottom.append((x, 18 + w))
    c.poly(top + bottom[::-1], RED)
    # Вырез ласточкиным хвостом на свободном крае.
    for x in range(24, 29):
        w = math.sin(x * 0.45 - i * math.pi / 3.0) * 1.6 * (x - 8) / 20.0
        for y in range(int(round(11.5 + w - (x - 24))), int(round(11.5 + w + (x - 24))) + 1):
            if 0 <= y < c.h:
                c.px[y][x] = None
    c.shade()
    c.outline()
    mid = math.sin(15 * 0.45 - i * math.pi / 3.0) * 0.8
    # Герб: золотой крест с кружком в середине.
    c.rect(14, 7 + mid, 15, 16 + mid, GOLD)
    c.rect(11, 10 + mid, 18, 11 + mid, GOLD)
    c.ellipse(14.5, 10.5 + mid, 2, 2, BRASS)
    c.set(14, 10 + mid, WHITE)
    return c


def heart():
    """Жизнь в HUD."""
    c = Canvas()
    c.ellipse(11, 12, 5.5, 5.5, RED)
    c.ellipse(20, 12, 5.5, 5.5, RED)
    c.poly([(5, 14), (26, 14), (15.5, 26)], RED)
    c.rect(9, 9, 10, 10, WHITE)
    return c.finish()


def ground(inner=False):
    """Кладка из тёсаного камня; у кромки дёрн с травой и свисающими корешками."""
    c = Canvas()
    c.rect(0, 0, 31, 31, METAL)
    # Ряды кирпичей по 8 строк, швы вразбежку, светлая кромка сверху и слева у каждого камня.
    for row in range(4):
        y = row * 8
        c.rect(0, y + 7, 31, y + 7, DARK)
        shift = 15 if row % 2 == 0 else 7
        for x in (shift, shift + 16):
            c.rect(x % 32, y, x % 32, y + 6, DARK)
        c.rect(0, y, 31, y, GREY)
        for x in (shift + 1, shift + 17):
            c.rect(x % 32, y + 1, x % 32, y + 6, GREY)
        for dx in (4, 20):
            c.set((shift + dx) % 32, y + 4, DARK)
    if not inner:
        c.rect(0, 0, 31, 4, SEA)
        c.rect(0, 0, 31, 1, AQUA)
        # Подбой дёрна неровный, местами свисают корешки.
        for x in range(32):
            c.set(x, 5, SEA if (x * 5 + 3) % 7 < 4 else METAL)
            if (x * 3) % 11 == 0:
                c.set(x, 6, NAVY)
        for x in range(1, 32, 6):
            c.set(x, 2, NAVY)
    return c


def rock():
    """Замшелый валун: серая глыба с трещиной и шапкой мха."""
    c = Canvas()
    c.poly([(4, 28), (2, 18), (8, 9), (17, 5), (26, 10), (30, 20), (27, 28)], METAL)
    c.poly([(8, 14), (14, 9), (20, 10), (15, 15)], GREY)
    c.poly([(5, 14), (9, 9), (17, 6), (24, 9), (20, 11), (15, 10), (10, 13)], SEA)
    c.set(13, 7, AQUA)
    c.set(18, 7, AQUA)
    c.set(10, 10, AQUA)
    c.line(14, 20, 18, 26, DARK, 1)
    c.line(18, 17, 20, 19, DARK, 1)
    c.ellipse(21, 21, 2, 1.5, GREY)
    return c.finish()


def chest():
    """Окованный ларь: деревянный короб с выпуклой крышкой, железные полосы и золотой замок."""
    c = Canvas()
    c.rect(4, 12, 27, 28, TAN)
    c.ellipse(15.5, 12, 12, 6, TAN)
    for x in (8, 23):
        c.rect(x, 7, x + 1, 28, METAL)
    c.rect(4, 19, 27, 20, METAL)
    c.rect(4, 27, 27, 28, METAL)
    # Замок и заклёпки.
    c.rect(14, 17, 17, 22, GOLD)
    c.rect(14, 17, 17, 17, WHITE)
    c.set(15, 20, K)
    for x, y in ((6, 13), (25, 13), (6, 25), (25, 25)):
        c.set(x, y, GREY)
    return c.finish()


# --- Параллакс ---------------------------------------------------------------------------------
# Три слоя дали без неба: нет заливки сверху, только холмы. Высоты периодические (256 делится на
# период синусов), ленты стыкуются по краям. Низ слоя сплошной.

def _wrap_ellipse(c, cx, cy, rx, ry, col):
    for k in (0, 256, -256):
        c.ellipse(cx + k, cy, rx, ry, col)


def _pine(c, x, base, h, col, hi=None):
    """Ель треугольными ярусами; широкий низ, острая макушка."""
    for k in range(3):
        top = base - h + k * h // 3 - 1
        w = 2 + k * 2
        c.poly([(x, top), (x + w, top + h // 2), (x - w, top + h // 2)], col)
    c.rect(x, base - 2, x, base, col)
    if hi is not None:
        c.line(x - 1, base - h + 3, x - 2, base - h // 2, hi, 1)


def _oak(c, x, base, r, col, hi):
    """Дуб: круглая крона с бликом и короткий ствол."""
    c.rect(x - 1, base - r, x, base, DARK)
    c.ellipse(x, base - r - r * 0.4, r, r * 0.85, col)
    c.ellipse(x - r * 0.35, base - r - r * 0.7, r * 0.45, r * 0.35, hi)


def _tower(c, x, base, w, h, col, hi, roof, flag_col=None):
    """Башня с зубцами или остроконечной крышей, окошко-бойница."""
    c.rect(x - w // 2, base - h, x + w // 2, base, col)
    c.rect(x - w // 2, base - h, x - w // 2, base, hi)
    if roof is None:
        for dx in range(-(w // 2), w // 2 + 1, 2):
            c.rect(x + dx, base - h - 2, x + dx, base - h, col)
    else:
        c.poly([(x, base - h - w), (x + w // 2 + 1, base - h), (x - w // 2 - 1, base - h)], roof)
        if flag_col is not None:
            c.line(x, base - h - w, x, base - h - w - 3, col, 1)
            c.rect(x + 1, base - h - w - 3, x + 3, base - h - w - 2, flag_col)
    if h > 8:
        c.rect(x, base - h + 4, x, base - h + 6, K)


def _castle(c, x, base, scale, col, hi, roof, flag_col):
    """Замок на горизонте: стена с зубцами, центральный донжон, две башни по краям, ворота."""
    s = scale
    c.rect(x - 14 * s, base - 8 * s, x + 14 * s, base, col)
    for dx in range(-14 * s, 14 * s + 1, 2):
        c.rect(x + dx, base - 10 * s, x + dx, base - 8 * s, col)
    _tower(c, x, base, 8 * s, 22 * s, col, hi, roof, flag_col)
    _tower(c, x - 13 * s, base, 6 * s, 16 * s, col, hi, roof, flag_col)
    _tower(c, x + 13 * s, base, 6 * s, 14 * s, col, hi, None)
    c.rect(x - 2 * s, base - 5 * s, x + 2 * s, base, K)
    c.ellipse(x, base - 5 * s, 2 * s, 2 * s, K)


def par_sky():
    """Дальний слой: сизые холмы в дымке с силуэтом замка на горизонте, лента 256×48, стыкуется
    по краям, неба нет (над холмами пусто)."""
    c = Canvas(256, 48)

    def height(x):
        return 18 + 6 * math.sin(x * math.pi * 2 / 256.0 * 2 + 0.6) + 4 * math.sin(x * math.pi * 2 / 256.0 * 5 + 2.0)

    for x in range(256):
        top = 47 - int(height(x))
        c.rect(x, top, x, 47, SKY)
        c.rect(x, top + 1, x, 47, AQUA)
        c.rect(x, top + 8, x, 47, SEA)
    # Далёкий замок: три башни и стена, цвет едва темнее дымки.
    gx = 190
    base = 47 - int(height(gx)) + 1
    c.rect(gx - 9, base - 7, gx + 9, base, GREY)
    _tower(c, gx, base, 5, 14, GREY, WHITE, METAL)
    _tower(c, gx - 8, base, 4, 10, GREY, WHITE, METAL)
    _tower(c, gx + 8, base, 4, 9, GREY, WHITE, None)
    # Дымка у подножия, облачка зелёных рощ.
    for cx, cy, r in ((40, 33, 12), (96, 36, 14), (150, 31, 10), (232, 34, 13)):
        _wrap_ellipse(c, cx, cy, r, r * 0.35, SKY)
    return c


def par_far():
    """Средний слой: зелёные холмы с замком и башнями на горизонте и дальними елями, лента 256×48,
    низ сплошной."""
    c = Canvas(256, 48)

    def height(x):
        h = 10 + 8 * max(0.0, math.sin(x * math.pi / 64.0)) ** 2 + 3 * math.sin(x * math.pi / 16.0 + 1.0)
        return h + 10 * max(0.0, math.sin((x - 40) * math.pi / 128.0)) ** 4

    for x in range(256):
        top = 47 - int(max(height(x), 3))
        c.rect(x, top, x, 47, SEA)
        c.rect(x, top, x, top + 1, AQUA)
        c.rect(x, top + 10, x, 47, NAVY)
    # Замок на плато (холм выровнен под ним), красные вымпелы на башнях.
    gx = 168
    base = 47 - int(height(gx)) + 2
    _castle(c, gx, base, 1, METAL, GREY, VIOLET, RED)
    # Ели и дубы на склонах, ближе к низу крупнее.
    for px, kind in ((20, 0), (34, 1), (68, 0), (80, 0), (112, 1), (126, 0), (214, 0), (228, 1), (244, 0)):
        by = 47 - int(height(px)) + 3
        if kind == 0:
            _pine(c, px, by, 11, NAVY, SEA)
        else:
            _oak(c, px, by, 4, SEA, AQUA)
    return c


def par_mid():
    """Ближний слой: бугры холмов с дубами и елями, лента 256×32."""
    c = Canvas(256, 32)
    for x in range(256):
        crest = 8 + 3 * math.sin(x * math.pi / 32.0) + 1.5 * math.sin(x * math.pi / 8.0)
        top = int(round(crest))
        c.rect(x, top, x, 31, SEA)
        c.rect(x, top, x, top + 1, AQUA)
        c.rect(x, top + 8, x, 31, NAVY)
        if (x * 7 + top * 3) % 23 == 0:
            c.rect(x, top + 5 + (x % 6), x + 1, top + 5 + (x % 6), AQUA)
    for px, kind in ((14, 1), (58, 0), (96, 1), (140, 0), (178, 1), (222, 0), (246, 1)):
        by = int(round(8 + 3 * math.sin(px * math.pi / 32.0) + 1.5 * math.sin(px * math.pi / 8.0))) + 2
        if kind == 0:
            _pine(c, px, by, 13, NAVY, SEA)
        else:
            _oak(c, px, by, 5, NAVY, SEA)
    return c


def sprites():
    """Ленты основы набора в палитре `PALETTE`: герой платформера, стражник, вещи, земля, три
    слоя дали. Ключи, размеры и число кадров те же, что у `space16.sprites()`. Ленты демок лежат
    в модулях `castles_*16.py`."""
    return {
        "enemy_walk": strip([guard_side(p) for p in base.phases()]),
        "enemy_front": strip([guard_front(p) for p in base.phases()]),
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
        "hero_run": strip([knight_side(p) for p in base.phases()]),
        "hero_jump": knight_side(0.0, jump=True),
        "hero_leap": strip([knight_leap(i) for i in range(4)]),
        "hero_idle": strip([knight_idle(i) for i in range(2)]),
        "hero_back": strip([knight_back(p) for p in base.phases()]),
        "hero_slide": strip([knight_slide(i) for i in range(2)]),
        "hero_hang": strip([knight_hang(i) for i in range(2)]),
        "hero_crouch": strip([knight_crouch(i) for i in range(2)]),
    }


# --- Остальные слоты (ленты демок «тропа» и «до выхода» их берут) ------------------------------

def bat(i):
    """Летучая мышь (слот попугая) летит вправо: четыре кадра взмаха (вверх, середина, вниз,
    середина), тело по центру кадра. Без красной обводки опасности: её кладёт модуль демки."""
    c = Canvas()
    wing = (-9, -3, 6, -3)[i]
    # Дальнее крыло позади тела, ближнее поверх; перепонка с зубцами, косточка по краю.
    for dx, col in ((-4, PLUM), (0, VIOLET)):
        c.poly([(13 + dx, 17), (19 + dx, 17), (23 + dx, 17 + wing * 1.5), (19 + dx, 16 + wing * 1.1),
                (16 + dx, 17 + wing * 1.4), (12 + dx, 16 + wing), (8 + dx, 17 + wing * 1.5)], col)
        c.line(14 + dx, 17, 8 + dx, 17 + wing * 1.5, DARK, 1)
    c.ellipse(15.5, 18, 4.5, 4, DARK)
    c.ellipse(22, 15, 3.2, 3, DARK)
    c.poly([(20, 13), (20, 9), (23, 12)], DARK)
    c.poly([(23, 13), (25, 9), (26, 13)], DARK)
    c.ellipse(15.5, 19, 2.5, 2, METAL)
    c.finish()
    c.set(23, 14, RED)
    c.set(25, 17, WHITE)
    c.set(23, 17, WHITE)
    return c


def boar(i):
    """Кабан (слот краба-ползуна) идёт вправо: четыре кадра, ноги по очереди, щетина на загривке,
    белые клыки."""
    c = Canvas()
    for k, dx in enumerate((-9, -6, 5, 8)):
        lift = 1 if (k + i) % 2 == 0 else 0
        c.rect(16 + dx - 1, 24, 16 + dx, 29 - lift, DARK)
        c.rect(16 + dx - 1, 29 - lift, 16 + dx + 1, 29 - lift, K)
    c.ellipse(15, 19.5, 11, 6, TAN)
    for x in range(7, 20, 2):
        c.line(x, 16, x + 1, 14 + (x + i) % 2, DARK, 1)
    c.ellipse(25, 19, 5, 4.5, TAN)
    c.poly([(26, 20), (31, 21), (30, 24), (25, 24)], SKIN)
    c.ellipse(21, 16, 1.5, 1.5, TAN)
    c.finish()
    c.set(26, 18, K)
    c.set(30, 22, K)
    c.set(28, 24, WHITE)
    c.set(29, 23, WHITE)
    c.set(28, 23, WHITE)
    return c


def key():
    """Железный ключ с золотой бородкой и кольцом-гербом."""
    c = Canvas(32, 32)
    c.ellipse(10, 16, 7, 7, GOLD)
    c.ellipse(10, 16, 3, 3, None)
    c.rect(16, 14, 29, 17, GOLD)
    c.rect(24, 18, 25, 22, GOLD)
    c.rect(28, 18, 29, 21, GOLD)
    c.rect(16, 14, 29, 14, WHITE)
    c.set(10, 10, RED)
    return c.finish()


def potion():
    """Пузырёк зелья с красным крестом (аптечка): круглая колба, пробка, золотая шейка."""
    c = Canvas(32, 32)
    c.ellipse(15.5, 20, 9, 8, SKY)
    c.rect(12, 7, 19, 14, SKY)
    c.rect(12, 5, 19, 7, TAN)
    c.rect(12, 12, 19, 12, GOLD)
    c.ellipse(15.5, 21.5, 7.5, 5.5, RED)
    c.rect(14, 16, 17, 26, WHITE)
    c.rect(11, 19, 20, 22, WHITE)
    c.rect(15, 17, 16, 25, RED)
    c.rect(12, 20, 19, 21, RED)
    c.set(11, 17, WHITE)
    c.set(10, 19, WHITE)
    return c.finish()


def bolt():
    """Арбалетный болт летит вправо: оперение, древко, стальной наконечник. 16×16."""
    c = Canvas(16, 16)
    c.line(2, 8, 11, 8, TAN, 1)
    c.poly([(1, 5), (5, 8), (1, 8)], WHITE)
    c.poly([(1, 11), (5, 8), (1, 8)], GREY)
    c.poly([(10, 6), (15, 8), (10, 10)], WHITE)
    return c.finish()


def extras():
    """Слоты замков вне `sprites()`: ленты и вещи тех же размеров, что у космоса и пиратов."""
    return {
        "parrot_fly": strip([bat(i) for i in range(4)]),
        "crab_walk": strip([boar(i) for i in range(4)]),
        "key": key(),
        "medkit": potion(),
        "shot": bolt(),
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
