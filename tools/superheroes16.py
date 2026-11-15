#!/usr/bin/env python3
"""Набор «Супергерои» для 16/32-bit (основа, зеркало `space16.py` и `castles16.py`): яркий комикс,
крыши мегаполиса на закате, чистые насыщенные цвета. Герой в синем трико с жёлтым плащом до колен,
жёлтыми сапогами и перчатками, в маске-домино на открытом лице, с хохолком тёмных волос и жёлтой
звездой на груди; враг это робот-приспешник злодея. Те же ленты, размеры и число кадров, что у
космоса, пиратов и замков (`castles16.sprites()`); позы героя повторяют космонавта кадр в кадр и
точка опоры ног та же, чтобы хитбоксы демок сходились: меняется рисунок, не геометрия. Силуэт героя
узнаётся без цвета: плащ за спиной, голова без шлема, хохолок.

Слоты космоса и их супергерои: космонавт это герой в плаще, пришелец это робот-бочонок с одним
красным глазом и клешнями, кристалл это золотой значок-звезда, флаг экспедиции это синий флаг с
жёлтой звездой, грузовая капсула это бронированный кейс, метеорит это обломок бетона с арматурой,
настил станции это бетон крыши с бортиком и кирпичом ниже. Закатное небо с дальними небоскрёбами,
небоскрёбы с огнями окон и дирижабль, водяные баки, антенны и рекламные щиты на крышах. Ленты,
которых нет в `sprites()` (дрон-шпион с винтами вместо попугая, робот-паук вместо краба, ключ,
аптечка, энергозаряд), лежат в `extras()` тех же размеров, что у космоса и пиратов.

Имена и порядок цветов те же, что у `space16.py` (по ним модули демок `superheroes_*16.py` берут
цвета по роли): K обводка, NAVY тёмный синий, SEA синее трико, AQUA яркая синева и энергия, SKY
блик, WHITE свет и белая эмаль, GREY зелёно-серый корпус робота, SKIN и TAN кожа и кирпич, GOLD и
BRASS жёлтое (плащ, сапоги, звезда), METAL бетон, DARK тёмный металл и волосы, RED глаз робота и
закат, VIOLET и PLUM сумерки.

    python3 tools/superheroes16.py --preview out.png   # лист набора в 4 раза крупнее
    python3 tools/superheroes16.py --preview out.png --scale=6 --keys=hero_run,hero_idle
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pixel_sprites16 as base  # noqa: E402
from pixel_sprites import png_bytes  # noqa: E402

# Палитра «Супергерои»: 16 цветов, индекс это та же роль, что у пиратов, космоса и замков.
K, NAVY, SEA, AQUA, SKY, WHITE, GREY, SKIN, TAN, GOLD, BRASS, METAL, DARK, RED, VIOLET, PLUM = range(16)
PALETTE = [
    (0x17, 0x0F, 0x2A),  # K      обводка
    (0x1E, 0x2A, 0x78),  # NAVY   тёмный синий: тень трико, дальние небоскрёбы
    (0x2B, 0x62, 0xE0),  # SEA    синее трико, флаг
    (0x4D, 0xB4, 0xF4),  # AQUA   яркая синева, энергозаряд, блик трико
    (0xCF, 0xEC, 0xFF),  # SKY    блик, стекло, искра
    (0xF6, 0xF4, 0xFA),  # WHITE  белая эмаль, блик, солнце
    (0x8E, 0xAC, 0x98),  # GREY   зелёно-серый корпус робота
    (0xF7, 0xC8, 0x9E),  # SKIN   кожа, низ неба
    (0xC8, 0x62, 0x38),  # TAN    кирпич, ржавая арматура, тень кожи
    (0xFF, 0xD2, 0x2E),  # GOLD   плащ, сапоги, звезда, окна
    (0xE0, 0x8A, 0x14),  # BRASS  тень жёлтого, оранжевый закат
    (0x62, 0x6E, 0x84),  # METAL  бетон, сталь
    (0x2C, 0x22, 0x4C),  # DARK   тёмный металл, волосы, маска
    (0xEE, 0x32, 0x46),  # RED    глаз робота, сердце, закат
    (0x92, 0x3C, 0xB0),  # VIOLET сумерки
    (0x4C, 0x1E, 0x60),  # PLUM   тень сумерек, силуэт дали
]
SHADOW = {SEA: NAVY, AQUA: SEA, SKY: AQUA, WHITE: GREY, GREY: METAL, SKIN: TAN, TAN: DARK, GOLD: BRASS,
          BRASS: DARK, METAL: DARK, RED: PLUM, VIOLET: PLUM}
# Материалы для светотени рампами: трико одна ткань, сталь робота и эмаль, кожа, кирпич, жёлтое,
# бетон, тёмное железо, красное, сумерки.
GROUPS = {NAVY: "suit", SEA: "suit", AQUA: "suit", SKY: "steel", WHITE: "steel", GREY: "steel",
          SKIN: "skin", TAN: "brick", GOLD: "gold", BRASS: "gold", METAL: "stone", DARK: "iron", RED: "red",
          VIOLET: "dusk", PLUM: "dusk"}


class Canvas(base.Canvas):
    shadow = SHADOW


def strip(frames):
    out = Canvas(sum(f.w for f in frames), max(f.h for f in frames))
    x = 0
    for f in frames:
        out.paste(f, x, 0)
        x += f.w
    return out


# --- Герой -------------------------------------------------------------------------------------
# Позы и габариты космонавта (голова над 13-й строкой, плечи на 13-й, ноги к 29-й), рисунок свой:
# голова без шлема с хохолком и маской-домино, плащ за спиной, сапоги с отворотами, звезда на груди.

def _star(c, cx, cy, col):
    """Звезда в пять пикселей поперёк: пятиконечная, лучи вверх."""
    for dx, dy in ((0, -2), (-1, -1), (0, -1), (1, -1), (-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0),
                   (-1, 1), (0, 1), (1, 1), (-1, 2), (1, 2)):
        c.set(cx + dx, cy + dy, col)


def _head(c, x, y):
    """Голова лицом вправо, центр (x, y), подбородок на y+4: тёмные волосы с хохолком, домино на
    глазах, нос и подбородок выступают вперёд, у затылка узелок маски."""
    c.ellipse(x - 2.5, y - 0.5, 3.4, 4.0, DARK)
    c.ellipse(x + 1, y + 1, 4.2, 4.4, SKIN)
    c.ellipse(x - 0.5, y - 2.8, 4.4, 2.0, DARK)
    # Хохолок: загнутая вперёд прядь над лбом.
    c.poly([(x - 1, y - 4), (x + 1, y - 7), (x + 4, y - 7), (x + 5, y - 5), (x + 2, y - 4.5)], DARK)
    c.set(x + 4, y - 3, DARK)
    # Маска-домино: полоса через глаза, острый край к виску, в ней белая щель глаза.
    c.rect(x, y, x + 4, y + 1, DARK)
    c.set(x + 5, y, DARK)
    c.set(x - 1, y - 1, DARK)
    c.set(x - 2, y, DARK)
    c.set(x + 3, y, WHITE)
    c.set(x + 4, y, WHITE)
    # Лицо: ухо, рот, блик на скуле.
    c.set(x - 1, y + 2, TAN)
    c.set(x + 4, y + 3, TAN)
    c.set(x + 2, y + 2, WHITE)
    c.set(x + 1, y - 5, METAL)
    c.set(x + 2, y - 5, METAL)


def _torso(c, x0, y0, x1, y1):
    """Корпус сбоку лицом вправо: синее трико, жёлтый пояс, жёлтая звезда на груди, плечо светлее."""
    c.rect(x0, y0, x1, y1, SEA)
    c.rect(x0, y0 + 1, x0 + 1, y1, NAVY)
    c.rect(x0 + 1, y0, x1 - 1, y0, AQUA)
    c.rect(x0, y1 - 1, x1, y1 - 1, GOLD)
    c.set(x1 - 3, y1 - 1, BRASS)
    _star(c, x1 - 3, y0 + 4, GOLD)


def _boot(c, foot, knee):
    """Жёлтый сапог: голенище с отворотом от колена к стопе и вытянутый носок вперёд."""
    fx, fy = foot
    tx = fx + (knee[0] - fx) * 0.42
    ty = fy + (knee[1] - fy) * 0.42
    c.line(tx, ty, fx, fy, GOLD, 4)
    c.rect(fx - 1, fy - 1, fx + 3, fy + 1, GOLD)
    c.rect(fx - 1, fy + 1, fx + 3, fy + 1, BRASS)
    c.line(tx - 1.5, ty, tx + 1.5, ty, BRASS, 1)


def _leg(c, hip, knee, foot, cloth):
    c.line(hip[0], hip[1], knee[0], knee[1], cloth, 4)
    c.line(knee[0], knee[1], foot[0], foot[1], cloth, 3)
    _boot(c, foot, knee)


def _arm(c, x0, y0, x1, y1, far):
    """Рука в трико с жёлтой перчаткой и отворотом. Дальняя тёмнее."""
    col = NAVY if far else AQUA
    c.line(x0, y0, x1, y1, col, 3 if far else 2)
    c.ellipse(x1, y1, 1.6, 1.6, GOLD)
    c.set(x0 + (x1 - x0) * 0.75, y0 + (y1 - y0) * 0.75, BRASS)


def _cape_run(c, bob, phase, lift=0.0):
    """Плащ в беге: от плеч стелется назад и вниз, край рваный, волна ходит по фазе. `lift` задирает
    конец вверх (прыжок)."""
    s = math.sin(phase)
    s2 = math.sin(phase * 2 + 1.0)
    ty = 19.0 - lift * 4 + s * 1.5
    pts = [(14, 13 - bob), (9.5, 13.5 - bob), (5.5, ty - 3 + s * 0.8), (1, ty - 1 + s2),
           (1.5, ty + 2 + s2), (4, min(29, ty + 6 - s)), (7, min(29, ty + 5 + s2)),
           (9.5, min(29, ty + 8.5 - s)), (12, min(28, ty + 7.5)), (13, 22 - bob)]
    c.poly(pts, GOLD)
    c.line(13, 15 - bob, 3, ty + 1 + s2, BRASS, 1)
    c.line(13, 18 - bob, 6, min(28, ty + 5), BRASS, 1)


def _cape_hang(c, top, sway):
    """Плащ висит за спиной до колен, чуть раскачивается."""
    c.poly([(14, top), (10, top + 1), (8 + sway, top + 8), (6.5 + sway, 25), (8 + sway, 27.5),
            (11, 26), (13, 27.5), (13.5, 22), (14, top + 6)], GOLD)
    c.line(12, top + 2, 9 + sway, 25, BRASS, 1)


def hero_side(phase, jump=False):
    """Герой сбоку, лицом вправо: бег по фазе 0..2π или прыжок."""
    c = Canvas()
    bob = 0 if jump else int(round(abs(math.sin(phase)) * 1.4))
    hip_y = 21 - bob
    swing = 0.9 if jump else math.sin(phase)
    _cape_run(c, bob, phase, 1.0 if jump else 0.0)
    _arm(c, 15, 15 - bob, 15 + 5 * swing, 20 - bob - (3 if jump else 0), True)
    for sign, cloth in ((-1, NAVY), (1, SEA)):
        a = swing * sign
        lift = max(0.0, math.cos(phase) * sign) * 3.0 if not jump else (4 if sign > 0 else 1)
        foot = (15 + 6 * a, 29 - lift)
        knee = ((15 + foot[0]) / 2 + 2, (hip_y + foot[1]) / 2)
        _leg(c, (15 + sign, hip_y), knee, foot, cloth)
    _torso(c, 11, 13 - bob, 19, hip_y)
    _arm(c, 16, 15 - bob, 16 - 5 * swing, 20 - bob - (4 if jump else 0), False)
    _head(c, 16, 8 - bob)
    return c.finish()


def hero_back(phase):
    """Со спины: бежит вглубь экрана, плащ закрывает всю спину, из-под него сапоги, затылок с
    хохолком и узелком маски."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.4))
    for sign in (-1, 1):
        lift = max(0.0, s * sign) * 4.0
        x = 16 + sign * 3
        c.rect(x - 2, 21 - bob, x + 1, 28 - lift, SEA if sign > 0 else NAVY)
        c.rect(x - 2, 25 - lift, x + 1, 28 - lift, GOLD)
        c.rect(x - 2, 29 - lift, x + 2, 29 - lift, BRASS)
        _arm(c, 16 + sign * 6, 15 - bob, 16 + sign * 7, 20 - bob + s * sign * 2, sign < 0)
    # Плащ: трапеция от плеч до колен, нижний край зубцами, складки вдоль.
    c.poly([(10, 13 - bob), (21, 13 - bob), (22, 24 - bob), (20, 26.5 - bob), (18, 25 - bob),
            (16, 27 - bob), (14, 25 - bob), (12, 26.5 - bob), (10, 24 - bob)], GOLD)
    c.line(16, 15 - bob, 16, 25 - bob, BRASS, 1)
    c.line(12.5, 15 - bob, 12, 24 - bob, BRASS, 1)
    c.line(19.5, 15 - bob, 20, 24 - bob, BRASS, 1)
    c.rect(13, 12 - bob, 18, 13 - bob, BRASS)
    # Голова со спины: шея, волосы, ухо, хохолок, концы маски.
    c.rect(14, 11 - bob, 17, 12 - bob, SKIN)
    c.ellipse(15.5, 7.5 - bob, 5, 4.8, DARK)
    c.poly([(13, 4 - bob), (15, 0 - bob), (18, 1 - bob), (18, 4 - bob)], DARK)
    c.set(10, 8 - bob, SKIN)
    c.set(21, 8 - bob, SKIN)
    c.rect(11, 9 - bob, 12, 9 - bob, DARK)
    c.rect(19, 9 - bob, 20, 9 - bob, DARK)
    c.set(14, 5 - bob, METAL)
    c.set(15, 6 - bob, METAL)
    return c.finish()


def hero_leap(i):
    """Прыжок через клетку, четыре кадра: присел, толчок, поджал ноги, приземление."""
    c = Canvas()
    crouch = (3, 0, -1, 2)[i]
    legs = ((2, 2), (5, -4), (3, -1), (4, 3))[i]
    hip_y = 21 + crouch
    _cape_run(c, -crouch, i * 1.3, (0.0, 1.0, 1.0, 0.0)[i])
    _arm(c, 15, 15 + crouch, 12 - i % 2, 11 + crouch if i in (1, 2) else 20 + crouch, True)
    for sign, cloth in ((-1, NAVY), (1, SEA)):
        foot = (15 + sign * legs[0] + (2 if i == 1 else 0), 29 if i in (0, 3) else 27 - (2 if i == 2 else 0))
        knee = ((15 + foot[0]) / 2 + 2 + legs[1] * 0.3, (hip_y + foot[1]) / 2 + (2 if i == 2 else 0))
        _leg(c, (15 + sign, hip_y), knee, foot, cloth)
    _torso(c, 11, 13 + crouch, 19, hip_y)
    _arm(c, 16, 15 + crouch, 20 + i % 2, 10 + crouch if i in (1, 2) else 20 + crouch, False)
    _head(c, 16, 8 + crouch)
    return c.finish()


def hero_idle(i):
    """Стойка: два кадра, герой дышит, кулак на поясе, плащ чуть качается."""
    c = Canvas()
    up = i
    _cape_hang(c, 13 - up, i)
    for sign, cloth in ((-1, NAVY), (1, SEA)):
        x = 15 + sign * 2
        c.rect(x - 1, 21, x + 1, 26, cloth)
        _boot(c, (x, 29), (x, 21))
    _arm(c, 14, 15 - up, 11, 18 - up, True)
    _torso(c, 11, 13 - up, 19, 21)
    # Ближняя рука согнута: плечо, локоть назад-вправо, кулак на поясе.
    c.line(17, 15 - up, 20, 18 - up, AQUA, 2)
    c.line(20, 18 - up, 18, 20 - up, AQUA, 2)
    c.ellipse(18, 20 - up, 1.6, 1.6, GOLD)
    _head(c, 16, 8 - up)
    return c.finish()


def _lean(c, sx, sy, hx, hy, w):
    """Корпус под наклоном: от плеч (sx, sy) к бёдрам (hx, hy), ширина w; трико по краям, звезда
    на груди, жёлтый пояс у бёдер."""
    n = math.hypot(hx - sx, hy - sy)
    dx, dy = (hx - sx) / n, (hy - sy) / n
    for k in range(int(n) + 1):
        x, y = sx + dx * k, sy + dy * k
        col = GOLD if k >= int(n) - 1 else NAVY
        c.line(x + dy * w / 2, y - dx * w / 2, x - dy * w / 2, y + dx * w / 2, col, 2)
        if k < int(n) - 1:
            c.line(x + dy * (w / 2 - 1), y - dx * (w / 2 - 1), x - dy * (w / 2 - 1), y + dx * (w / 2 - 1), SEA, 2)
    mx, my = sx + dx * n * 0.4, sy + dy * n * 0.4
    c.set(mx, my - 1, GOLD)
    c.set(mx - 1, my, GOLD)
    c.set(mx, my, GOLD)
    c.set(mx + 1, my, GOLD)
    c.set(mx, my + 1, GOLD)


def hero_slide(i):
    """Подкат на боку ногами вперёд: корпус откинут, ближняя нога вытянута, дальняя коленом вверх,
    рука сзади на земле, плащ стелется по земле позади. Макушка на 14-й строке. Два кадра: колено
    и пыль."""
    c = Canvas()
    c.poly([(12, 20), (7, 22), (1, 26 + i), (1.5, 29), (5, 30), (9, 29.5), (12, 28)], GOLD)
    c.line(11, 23, 3, 28 + i, BRASS, 1)
    c.line(19, 27, 24, 23 - i, NAVY, 3)
    c.line(24, 23 - i, 27, 27, NAVY, 3)
    _boot(c, (27, 27), (24, 23 - i))
    c.line(13, 24, 19, 23, NAVY, 2)
    _lean(c, 12, 24, 19, 27, 6)
    c.line(19, 28, 28, 28, SEA, 4)
    c.line(20, 27, 27, 27, AQUA, 1)
    c.rect(26, 26, 30, 29, GOLD)
    c.rect(26, 29, 30, 29, BRASS)
    c.line(11, 25, 6, 29, NAVY, 2)
    c.ellipse(5.5, 29, 1.6, 1.6, GOLD)
    _head(c, 10, 21)
    c.finish()
    for k, (x, y) in enumerate(((2, 31), (4, 31), (0, 29), (3, 30))):
        if (k + i) % 2 == 0:
            c.set(x, y, SKY)
    return c


def hero_crouch(i):
    """Присед: та же фигура, сложенная вниз, корпус прямо, колени вперёд. Два кадра шага."""
    c = Canvas()
    step = (-1, 1)[i]
    c.poly([(13, 22), (9, 23), (6, 27), (8, 29), (11, 28), (14, 27)], GOLD)
    c.line(15, 24, 19, 26, NAVY, 2)
    for sign, cloth in ((-1, NAVY), (1, SEA)):
        hip = (14, 27)
        knee = (20 - sign + step * sign, 26)
        foot = (17 - sign * 2 + step * sign * 2, 29)
        c.line(hip[0], hip[1], knee[0], knee[1], cloth, 4)
        c.line(knee[0], knee[1], foot[0], foot[1], cloth, 3)
        _boot(c, foot, knee)
    _torso(c, 11, 22, 18, 26)
    c.line(14, 24, 19, 26, SEA, 2)
    c.ellipse(19, 26, 1.6, 1.6, GOLD)
    _head(c, 16, 17)
    return c.finish()


def hero_hang(i):
    """На тросе: руки вверх к точке хвата (центр сверху), ноги свисают и качаются, плащ свисает."""
    c = Canvas()
    sw = (-1, 1)[i]
    _cape_hang(c, 14, sw)
    c.line(13, 15, 14, 2, NAVY, 3)
    c.line(19, 15, 18, 2, SEA, 2)
    c.ellipse(14, 1.5, 1.6, 1.6, GOLD)
    c.ellipse(18, 1.5, 1.6, 1.6, GOLD)
    for sign, cloth in ((-1, NAVY), (1, SEA)):
        foot = (15.5 + sign * 2 + sw * 2, 29)
        c.line(15.5 + sign * 2, 21, foot[0], foot[1] - 3, cloth, 3)
        _boot(c, (foot[0], foot[1]), (foot[0], foot[1] - 8))
    _torso(c, 11, 14, 20, 21)
    _head(c, 16, 9)
    return c.finish()


# --- Робот-приспешник --------------------------------------------------------------------------
# Бочонок на двух стойках-поршнях: зелёно-серый корпус с тёмными обручами и заклёпками, куполок с
# одним красным глазом в тёмной прорези, антенна с красной лампой, вместо рук клешни.

def _claw(c, x, y, dx, dy, open_):
    """Клешня: два зубца от запястья (x, y) в сторону (dx, dy), раствор `open_` 1..3."""
    for k in (-1, 1):
        c.line(x, y, x + dx * 4 + dy * k * (1 + open_), y + dy * 4 + dx * k * (1 + open_), METAL, 2)
        c.set(x + dx * 5 + dy * k * (1 + open_) * 0.6, y + dy * 5 + dx * k * (1 + open_) * 0.6, SKY)
    c.ellipse(x, y, 1.8, 1.8, DARK)


def _hoops(c, x0, x1, ys):
    for y in ys:
        for x in range(int(x0), int(x1) + 1):
            if c.get(x, y) == GREY:
                c.set(x, y, DARK)


def robot_side(phase):
    """Робот сбоку, лицом влево (навстречу герою): шаг по фазе, клешня вперёд, глаз горит."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.2))
    # Поршни ног.
    for sign, col in ((-1, DARK), (1, METAL)):
        a = s * sign
        lift = max(0.0, math.cos(phase) * sign) * 2.5
        foot = (16 - 4 * a, 29 - lift)
        c.line(16 + sign * 2, 22 - bob, foot[0], foot[1] - 1, col, 3)
        c.rect(foot[0] - 3, foot[1] - 1, foot[0] + 1, foot[1] + 1, DARK if sign < 0 else GREY)
    # Рука-манипулятор и клешня вперёд.
    c.line(12, 16 - bob, 7, 17 - bob + s, METAL, 2)
    _claw(c, 7, 17 - bob + s, -1, 0, 1 + int(abs(s) * 2))
    # Бочонок: тело, обручи, блик слева, заклёпки.
    c.ellipse(16, 16 - bob, 6.6, 7, GREY)
    c.rect(10, 12 - bob, 22, 20 - bob, GREY)
    c.ellipse(16, 12 - bob, 6.6, 2.5, GREY)
    _hoops(c, 9, 23, (13 - bob, 19 - bob))
    c.rect(11, 14 - bob, 11, 18 - bob, WHITE)
    for x in (11, 21):
        c.set(x, 13 - bob, SKY)
        c.set(x, 19 - bob, SKY)
    # Пластина на груди с красным знаком злодея.
    c.rect(14, 15 - bob, 18, 17 - bob, DARK)
    c.set(15, 16 - bob, RED)
    c.set(17, 16 - bob, RED)
    c.set(16, 17 - bob, RED)
    # Купол головы с прорезью и глазом, антенна.
    c.ellipse(15.5, 8.5 - bob, 5.5, 3.8, GREY)
    c.rect(10, 7 - bob, 15, 10 - bob, DARK)
    c.ellipse(11.5, 8.5 - bob, 1.9, 1.9, RED)
    c.set(11, 8 - bob, SKY)
    c.line(17, 5 - bob, 18, 2 - bob, DARK, 1)
    c.ellipse(18, 1.5 - bob, 1.3, 1.3, RED)
    return c.finish()


def robot_front(phase):
    """Робот лицом к камере: идёт на игрока, ноги по очереди, клешни разведены и щёлкают."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.2))
    for sign in (-1, 1):
        lift = max(0.0, s * sign) * 3.0
        x = 16 + sign * 3
        c.rect(x - 1, 22 - bob, x, 28 - lift, DARK if sign < 0 else METAL)
        c.rect(x - 2, 28 - lift, x + 1, 29 - lift, DARK)
    # Руки с клешнями по бокам.
    for sign in (-1, 1):
        wy = 19 - bob + s * sign * 2
        c.line(16 + sign * 6, 15 - bob, 16 + sign * 9, wy, METAL, 2)
        _claw(c, 16 + sign * 9, wy, sign * 0.4, 1, 1 + int(abs(s) * 2))
    c.ellipse(15.5, 16 - bob, 7, 7.2, GREY)
    c.rect(9, 12 - bob, 22, 20 - bob, GREY)
    c.ellipse(15.5, 12 - bob, 7, 2.5, GREY)
    _hoops(c, 8, 23, (13 - bob, 19 - bob))
    c.rect(10, 14 - bob, 10, 18 - bob, WHITE)
    for x in (10, 21):
        c.set(x, 13 - bob, SKY)
        c.set(x, 19 - bob, SKY)
    c.rect(13, 15 - bob, 18, 17 - bob, DARK)
    c.set(14, 16 - bob, RED)
    c.set(17, 16 - bob, RED)
    c.set(15, 17 - bob, RED)
    c.set(16, 17 - bob, RED)
    c.ellipse(15.5, 8.5 - bob, 6, 3.9, GREY)
    c.rect(10, 7 - bob, 21, 10 - bob, DARK)
    c.ellipse(15.5, 8.5 - bob, 2, 2, RED)
    c.set(15, 8 - bob, SKY)
    c.line(15.5, 5 - bob, 15.5, 2 - bob, DARK, 1)
    c.ellipse(15.5, 1.5 - bob, 1.3, 1.3, RED)
    return c.finish()


# --- Вещи --------------------------------------------------------------------------------------

def _star_poly(c, cx, cy, ro, ri, col, kx=1.0):
    """Пятиконечная звезда лучом вверх, сжатая по горизонтали на `kx`."""
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        r = ro if i % 2 == 0 else ri
        pts.append((cx + math.cos(a) * r * kx, cy + math.sin(a) * r))
    c.poly(pts, col)


def coin(i):
    """Золотой значок-звезда вращается: шесть кадров, ширина по косинусу, ребро темнее."""
    c = Canvas()
    rx = max(1.0, abs(math.cos(math.pi * i / 6.0)) * 7.0)
    k = rx / 7.0
    cx = 15.5
    c.ellipse(cx, 16, rx, 10.5, BRASS)
    if rx > 2:
        c.ellipse(cx, 16, rx - 1.3, 9.2, GOLD)
    if rx > 3:
        _star_poly(c, cx, 16.5, 8.2, 3.6, BRASS, k)
        _star_poly(c, cx, 16.5, 6.0, 2.6, WHITE, k)
        c.set(cx - 2 * k, 9, WHITE)
        c.line(cx - rx * 0.6, 8, cx - rx * 0.3, 7, WHITE, 1)
    return c.finish()


def flag(i):
    """Синий флаг на стальном древке с золотым шаром: полотнище идёт волной, на нём жёлтая звезда."""
    c = Canvas()
    c.rect(5, 3, 6, 31, GREY)
    c.ellipse(5.5, 2, 2, 2, GOLD)
    top = []
    bottom = []
    for x in range(8, 29):
        w = math.sin(x * 0.45 - i * math.pi / 3.0) * 1.6 * (x - 8) / 20.0
        top.append((x, 5 + w))
        bottom.append((x, 19 + w))
    c.poly(top + bottom[::-1], SEA)
    c.shade()
    c.outline()
    for x in range(8, 29):
        w = math.sin(x * 0.45 - i * math.pi / 3.0) * 1.6 * (x - 8) / 20.0
        c.set(x, 5 + w, AQUA)
    mid = math.sin(17 * 0.45 - i * math.pi / 3.0) * 1.0
    _star_poly(c, 17.5, 12.3 + mid, 5.8, 2.5, GOLD)
    c.set(15, 10 + mid, WHITE)
    return c


def heart():
    """Жизнь в HUD."""
    c = Canvas()
    c.ellipse(11, 12, 5.5, 5.5, RED)
    c.ellipse(20, 12, 5.5, 5.5, RED)
    c.poly([(5, 14), (26, 14), (15.5, 26)], RED)
    c.rect(9, 9, 10, 10, WHITE)
    c.set(8, 11, WHITE)
    return c.finish()


def ground(inner=False):
    """Бетон крыши с бортиком сверху, ниже кирпичная кладка: кирпичи 8×3 вразбежку, раствор тёмный,
    бетонный бортик со светлой кромкой и тенью под ним. Тайл стыкуется по всем краям."""
    c = Canvas()
    c.rect(0, 0, 31, 31, TAN)
    for row in range(8):
        y = row * 4
        c.rect(0, y + 3, 31, y + 3, PLUM)
        off = 4 if row % 2 else 0
        for x in range(off, 32 + off, 8):
            c.rect(x % 32, y, x % 32, y + 2, PLUM)
            # Кирпич: светлая верхняя кромка, в разбивку красноватые.
            for dx in range(1, 8):
                c.set((x + dx) % 32, y, SKIN if (x // 8 + row) % 5 == 0 else BRASS)
            if (x // 8 * 3 + row * 5) % 7 == 0:
                c.rect((x + 1) % 32, y + 1, (x + 6) % 32 if x % 32 + 6 < 32 else 31, y + 2, RED)
    if not inner:
        c.rect(0, 0, 31, 4, METAL)
        c.rect(0, 0, 31, 0, SKY)
        c.rect(0, 1, 31, 1, WHITE)
        c.rect(0, 2, 31, 2, GREY)
        for x in range(0, 32, 16):
            c.rect(x + 7, 3, x + 7, 4, DARK)
        c.rect(0, 5, 31, 5, DARK)
        c.rect(0, 6, 31, 6, PLUM)
    return c


def rock():
    """Обломок бетона с арматурой: серая глыба со сколами, из верха и бока торчат ржавые прутья."""
    c = Canvas()
    c.poly([(4, 28), (2, 20), (6, 12), (14, 9), (22, 11), (29, 17), (28, 28)], METAL)
    c.poly([(7, 15), (14, 11), (21, 13), (17, 18), (10, 19)], SKY)
    c.line(14, 20, 17, 27, DARK, 1)
    c.line(17, 20, 21, 22, DARK, 1)
    c.line(21, 22, 21, 26, DARK, 1)
    c.ellipse(24, 22, 2, 1.5, SKY)
    c.ellipse(8, 24, 1.5, 1.2, SKY)
    # Арматура: прутья с загнутыми концами.
    c.line(12, 10, 11, 3, TAN, 1)
    c.line(11, 3, 13, 1, TAN, 1)
    c.line(17, 10, 19, 4, TAN, 1)
    c.line(28, 18, 31, 15, TAN, 1)
    c.line(3, 18, 0, 15, TAN, 1)
    return c.finish()


def chest():
    """Бронированный кейс: стальной короб с ребром жёсткости, угловыми накладками и ручкой, замок с
    жёлтой звездой и красным огоньком."""
    c = Canvas()
    c.rect(4, 12, 27, 28, METAL)
    c.rect(4, 12, 27, 13, GREY)
    c.rect(4, 19, 27, 19, DARK)
    c.rect(4, 20, 27, 20, GREY)
    # Ручка: скоба сверху.
    c.rect(11, 8, 20, 11, DARK)
    c.rect(13, 9, 18, 11, None)
    for x, y in ((4, 12), (4, 27), (26, 12), (26, 27)):
        c.rect(x, y, x + 1, y + 1, DARK)
    c.rect(13, 16, 18, 23, DARK)
    _star(c, 15, 20, GOLD)
    c.set(16, 17, RED)
    c.set(6, 24, SKY)
    c.set(25, 15, SKY)
    c.rect(6, 25, 9, 26, NAVY)
    return c.finish()


# --- Параллакс ---------------------------------------------------------------------------------
# Три слоя дали. Ленты периодические по ширине 256 (постройки считаются от одного набора чисел, у
# шва стоят вплотную), поэтому края сходятся. У слоёв дали низ сплошной.

def _rng(seed):
    """Детерминированная последовательность без модуля random: каждый вызов даёт следующее число."""
    state = [seed]

    def nxt(n):
        state[0] = (state[0] * 1103515245 + 12345) & 0x7FFFFFFF
        return (state[0] >> 9) % n
    return nxt


def par_sky():
    """Дальний слой: закатное небо сверху вниз от лилового через красный и оранжевый к золотому и
    розовому у горизонта, полосы стыкует шахматка, солнце, тонкие облака и силуэты дальних
    небоскрёбов. Лента 256×48, сплошная."""
    c = Canvas(256, 48)
    bands = ((0, VIOLET), (13, RED), (22, BRASS), (31, GOLD), (40, SKIN))
    for y in range(48):
        for x in range(256):
            idx = max(i for i, (y0, _) in enumerate(bands) if y >= y0 - 0)
            col = bands[idx][1]
            if idx + 1 < len(bands):
                d = bands[idx + 1][0] - y
                if d == 1 and (x + y) % 2 == 0:
                    col = bands[idx + 1][1]
                elif d == 2 and x % 2 == 0 and y % 2 == 0:
                    col = bands[idx + 1][1]
            c.set(x, y, col)
    # Тонкие облака: горизонтальные полосы чуть темнее фона.
    for cx, cy, rx, col in ((30, 17, 20, VIOLET), (120, 25, 26, RED), (200, 19, 16, VIOLET),
                            (70, 34, 18, BRASS), (180, 36, 20, BRASS), (250, 26, 14, RED)):
        for k in (0, 256, -256):
            c.ellipse(cx + k, cy, rx, 1.2, col)
    # Солнце у горизонта с ореолом.
    c.ellipse(80, 40, 11, 11, GOLD)
    c.ellipse(80, 40, 8, 8, SKIN)
    c.ellipse(80, 40, 5, 5, WHITE)
    # Силуэты: сплошная полоса домов от шва до шва, выше и ниже по ряду.
    rnd = _rng(11)
    x = 0
    while x < 256:
        w = 8 + rnd(9)
        h = 11 + rnd(20)
        c.rect(x, 47 - h, x + w - 1, 47, PLUM)
        roof = rnd(4)
        if roof == 0:
            c.rect(x + w // 2, 47 - h - 5, x + w // 2, 47 - h, PLUM)
        elif roof == 1:
            c.rect(x + 2, 47 - h - 3, x + w - 3, 47 - h, PLUM)
        for gx in range(x + 2, x + w - 2, 3):
            for gy in range(47 - h + 3, 46, 4):
                if (gx * 7 + gy * 13) % 9 == 0:
                    c.set(gx, gy, VIOLET)
        x += w
    return c


def _blimp(c, cx, cy):
    """Дирижабль: белая сигара с красным поясом и золотой звездой, красные стабилизаторы, гондола."""
    c.ellipse(cx, cy, 15, 5.5, WHITE)
    c.ellipse(cx, cy + 2, 14, 3, GREY)
    c.ellipse(cx - 1, cy - 1.5, 12, 2.5, WHITE)
    c.rect(cx - 12, cy, cx + 12, cy, RED)
    c.poly([(cx - 12, cy), (cx - 18, cy - 6), (cx - 9, cy - 3)], RED)
    c.poly([(cx - 12, cy), (cx - 18, cy + 6), (cx - 9, cy + 3)], PLUM)
    c.rect(cx - 4, cy + 6, cx + 4, cy + 7, DARK)
    c.set(cx - 3, cy + 6, SKY)
    c.set(cx, cy + 6, SKY)
    c.set(cx + 3, cy + 6, SKY)
    _star(c, cx + 5, cy - 1, GOLD)
    c.set(cx + 15, cy, DARK)


def par_far():
    """Средний слой: небоскрёбы тёмно-синим с огнями окон, антеннами и шпилями, над ними дирижабль,
    лента 256×48, над домами пусто, низ сплошной."""
    c = Canvas(256, 48)
    _blimp(c, 168, 9)
    rnd = _rng(5)
    x = 1
    while x < 256:
        w = 10 + rnd(8)
        h = 14 + rnd(22)
        if 140 <= x <= 200:
            h = min(h, 24)
        top = 47 - h
        c.rect(x, top, x + w - 1, 47, NAVY)
        c.rect(x, top, x, 47, SEA)
        c.rect(x + w - 1, top, x + w - 1, 47, DARK)
        c.rect(x, top, x + w - 1, top, SEA)
        roof = rnd(5)
        if roof == 0:
            c.line(x + w // 2, top - 8, x + w // 2, top, DARK, 1)
            c.set(x + w // 2, top - 9, RED)
        elif roof == 1:
            c.rect(x + 2, top - 4, x + w - 3, top, NAVY)
            c.rect(x + 2, top - 4, x + w - 3, top - 4, SEA)
        elif roof == 2:
            c.poly([(x + w // 2, top - 9), (x + w - 2, top), (x + 1, top)], NAVY)
            c.line(x + w // 2, top - 9, x + 1, top, SEA, 1)
        for gx in range(x + 2, x + w - 3, 4):
            for gy in range(top + 3, 46, 5):
                hsh = (gx * 7 + gy * 13 + x) % 6
                if hsh < 3:
                    c.rect(gx, gy, gx + 1, gy + 1, GOLD)
                elif hsh == 3:
                    c.rect(gx, gy, gx + 1, gy + 1, BRASS)
        x += w + rnd(3)
    return c


def _tank(c, x, base):
    """Водяной бак на ножках: бочка с обручами и конусом крыши."""
    c.line(x - 4, base, x - 4, base - 4, DARK, 1)
    c.line(x + 4, base, x + 4, base - 4, DARK, 1)
    c.rect(x - 5, base - 12, x + 5, base - 5, TAN)
    c.rect(x - 5, base - 12, x - 4, base - 5, BRASS)
    c.rect(x - 5, base - 9, x + 5, base - 9, DARK)
    c.rect(x - 5, base - 6, x + 5, base - 6, DARK)
    c.poly([(x, base - 17), (x + 6, base - 12), (x - 6, base - 12)], DARK)
    c.set(x - 2, base - 15, TAN)


def _antenna(c, x, base, h):
    """Антенна: мачта с перекладинами и красной лампой."""
    c.line(x, base, x, base - h, DARK, 1)
    for k in range(3, h - 2, 4):
        c.line(x - 3 + k // 5, base - k, x + 3 - k // 5, base - k, DARK, 1)
    c.rect(x - 1, base - h - 2, x + 1, base - h - 1, RED)
    c.set(x, base - h - 3, SKY)


def _billboard(c, x, base, face):
    """Рекламный щит на двух опорах: рамка, цветное поле, звезда и строчки текста."""
    c.rect(x - 7, base - 6, x - 6, base, DARK)
    c.rect(x + 6, base - 6, x + 7, base, DARK)
    c.rect(x - 11, base - 17, x + 11, base - 6, DARK)
    c.rect(x - 10, base - 16, x + 10, base - 7, face)
    _star(c, x - 6, base - 11, GOLD if face != GOLD else DARK)
    c.rect(x - 1, base - 14, x + 8, base - 14, WHITE)
    c.rect(x - 1, base - 12, x + 6, base - 12, WHITE)
    c.rect(x - 1, base - 10, x + 8, base - 10, SKY)
    c.rect(x - 10, base - 16, x + 10, base - 16, AQUA if face == SEA else SKIN)


def par_mid():
    """Ближний слой: плоские крыши тёмными блоками с оранжевой кромкой заката, на них водяные баки,
    антенны и рекламные щиты, лента 256×32, низ сплошной."""
    c = Canvas(256, 32)
    rnd = _rng(23)
    tops = [0] * 256
    x = 0
    while x < 256:
        w = 24 + rnd(20)
        t = 20 + rnd(4)
        for xx in range(x, min(256, x + w)):
            tops[xx] = t
        c.rect(x, t, x + w - 1, 31, DARK)
        c.rect(x, t, x + w - 1, t, BRASS)
        c.rect(x, t + 1, x + w - 1, t + 1, METAL)
        c.rect(x, t, x, 31, METAL)
        for gx in range(x + 4, x + w - 3, 6):
            for gy in range(t + 5, 30, 5):
                if (gx * 5 + gy * 3) % 7 < 2:
                    c.rect(gx, gy, gx + 1, gy + 1, GOLD)
        x += w
    # Предметы на крышах по порядку, не заходят за шов.
    for px, kind in ((20, 0), (56, 2), (96, 1), (126, 0), (160, 3), (196, 1), (226, 0)):
        base = tops[px]
        if kind == 0:
            _tank(c, px, base)
        elif kind == 1:
            _antenna(c, px, base, 14)
        elif kind == 2:
            _billboard(c, px, base, SEA)
        else:
            _billboard(c, px, base, RED)
    return c


def sprites():
    """Ленты основы набора в палитре `PALETTE`: герой платформера, робот, вещи, земля, три слоя
    дали. Ключи, размеры и число кадров те же, что у `castles16.sprites()`. Ленты демок лежат в
    модулях `superheroes_*16.py`."""
    return {
        "enemy_walk": strip([robot_side(p) for p in base.phases()]),
        "enemy_front": strip([robot_front(p) for p in base.phases()]),
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


# --- Остальные слоты (ленты демок их берут) ----------------------------------------------------

def drone(i):
    """Дрон-шпион (слот попугая) летит вправо: четыре кадра, винты на штангах мелькают, тело по
    центру кадра. Круглый корпус с красной линзой-камерой, полозья. Без красной обводки опасности:
    её кладёт модуль демки."""
    c = Canvas()
    span = (9, 5, 9, 3)[i]
    tilt = (0, 2, 0, -2)[i]
    # Штанги и ступицы винтов.
    for hx, hy in ((8.5, 11), (22.5, 11)):
        c.line(15.5, 15, hx, hy, DARK, 2)
        c.rect(hx - 1, hy - 3, hx, hy, METAL)
    # Полозья.
    c.line(11, 23, 20, 23, DARK, 1)
    c.line(12, 20, 11, 23, DARK, 1)
    c.line(19, 20, 20, 23, DARK, 1)
    # Корпус: тёмная сфера с зелёно-серой верхней половиной.
    c.ellipse(15.5, 18, 7, 5.2, DARK)
    c.ellipse(15.5, 16.8, 6, 3.6, GREY)
    c.rect(10, 18, 21, 18, METAL)
    # Линза-камера впереди и огонёк на хвосте.
    c.ellipse(20.5, 18.5, 2.4, 2.4, DARK)
    c.ellipse(21, 18.5, 1.4, 1.4, RED)
    c.set(8, 16, RED)
    c.finish()
    # Лопасти поверх обводки: размах меняется по кадрам, у ближней пары наклон.
    for hx, hy in ((8.5, 8), (22.5, 8)):
        c.line(hx - span, hy + tilt * 0.3, hx + span, hy - tilt * 0.3, SKY, 1)
        c.set(hx, hy, WHITE)
    c.set(21, 17.5, SKY)
    return c


def spider(i):
    """Робот-паук (слот краба-ползуна) идёт вправо: четыре кадра, четыре ноги из двух звеньев по
    очереди, купол с красным глазом, лапки-иглы."""
    c = Canvas()
    for k, hx in enumerate((11, 14, 18, 21)):
        up = 2 if (k + i) % 2 == 0 else 0
        side = -1 if hx < 16 else 1
        kx = hx + side * 5
        fx = hx + side * 8 + (1 if up else -1)
        c.line(hx, 21, kx, 15 + up * 0.5, DARK if k % 2 == 0 else METAL, 2)
        c.line(kx, 15 + up * 0.5, fx, 29 - up, DARK if k % 2 == 0 else METAL, 2)
    c.ellipse(15.5, 20, 8, 4.6, GREY)
    c.ellipse(15.5, 17.5, 5.6, 3.8, GREY)
    c.rect(9, 20, 22, 20, DARK)
    c.ellipse(21, 18, 2.2, 2.2, DARK)
    c.finish()
    c.set(21, 18, RED)
    c.set(21, 17, SKY)
    c.set(12, 15, WHITE)
    c.set(13, 14, WHITE)
    return c


def key():
    """Золотой ключ: головка-звезда, стержень с двумя зубцами."""
    c = Canvas(32, 32)
    _star_poly(c, 10, 16, 8.5, 3.6, GOLD)
    c.ellipse(10, 16.5, 2, 2, None)
    c.rect(16, 14, 29, 17, GOLD)
    c.rect(24, 18, 25, 22, GOLD)
    c.rect(28, 18, 29, 21, GOLD)
    c.rect(16, 14, 29, 14, WHITE)
    c.set(6, 12, WHITE)
    return c.finish()


def medkit():
    """Аптечка: белый кейс со скруглёнными углами, красный крест, серая ручка и синий замок."""
    c = Canvas(32, 32)
    c.rect(5, 12, 26, 27, WHITE)
    c.rect(6, 11, 25, 11, WHITE)
    c.rect(11, 7, 20, 10, GREY)
    c.rect(13, 8, 18, 10, None)
    c.rect(14, 14, 17, 25, RED)
    c.rect(9, 18, 22, 21, RED)
    c.rect(5, 26, 26, 27, GREY)
    c.rect(5, 12, 5, 27, SKY)
    c.set(7, 14, SEA)
    c.set(24, 14, SEA)
    return c.finish()


def bolt():
    """Энергозаряд летит вправо: белое ядро, голубая оболочка, хвост-шлейф искр. 16×16."""
    c = Canvas(16, 16)
    c.poly([(0, 8), (6, 5), (6, 11)], SEA)
    c.poly([(2, 8), (8, 6), (8, 10)], AQUA)
    c.ellipse(10.5, 8, 4.5, 3.4, AQUA)
    c.ellipse(11, 8, 3.2, 2.2, SKY)
    c.ellipse(11.5, 8, 1.8, 1.2, WHITE)
    c.set(5, 4, SKY)
    c.set(3, 12, SKY)
    c.set(8, 3, AQUA)
    return c.finish()


def extras():
    """Слоты супергероев вне `sprites()`: ленты и вещи тех же размеров, что у космоса и замков."""
    return {
        "parrot_fly": strip([drone(i) for i in range(4)]),
        "crab_walk": strip([spider(i) for i in range(4)]),
        "key": key(),
        "medkit": medkit(),
        "shot": bolt(),
    }


def shaded(items):
    """Ленты в палитре `PALETTE` → {ключ: (холст, палитра)} как в игре: силуэты получают
    светотень рампами (`pixel_sprites16.reshade`), сплошные плитки остаются в палитре сеттинга."""
    out = {}
    for key_, canvas in items.items():
        if base.wants_reshade(key_, canvas):
            out[key_] = base.reshade(canvas, PALETTE, GROUPS)
        else:
            out[key_] = (canvas, PALETTE)
    return out


def save_sheet(path, items, scale=3, pad=6, back=(0x1B, 0x1A, 0x33, 255), max_w=640):
    """Лист для просмотра: `items` это {ключ: (холст, палитра)}, лента на строку; ленты шире
    `max_w` режутся на строки по `max_w`."""
    width = (min(max(c.w for c, _ in items.values()), max_w) + 2 * pad) * scale
    blank = list(back) * width
    rows = [blank[:] for _ in range(pad * scale)]
    for key_, (canvas, palette) in items.items():
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
