#!/usr/bin/env python3
"""Набор «Ниндзя» для 16/32-bit (основа, зеркало `castles16.py` и `space16.py`): старая Япония на
закате, оранжево-розовое небо, красные клёны, тёмное дерево и черепица. Герой это ниндзя в
тёмно-синем костюме: капюшон-маска с полоской глаз, длинный красный шарф с двумя концами по ветру,
короткий меч за спиной наискось, светлые обмотки на голенях; силуэт держат концы шарфа и рукоять
меча над плечом. Враг это ниндзя чужого клана в красном с чёрной маской и серпом. Те же ленты,
размеры и число кадров, что у замков, космоса и пиратов (`castles16.sprites()`); позы героя и точка
опоры ног повторяют образцы кадр в кадр, чтобы хитбоксы демок сходились: меняется рисунок, не
геометрия.

Слоты и их ниндзя: герой это ниндзя, враг это ниндзя чужого клана с серпом, кристалл это монета с
квадратным отверстием, флаг это нобори (узкое вертикальное знамя), капсула это чёрный лаковый
ларец, метеорит это каменный фонарь, настил это каменная дорожка со мхом. Ленты, которых нет в
`sprites()` (ворон-тэнгу вместо попугая, жаба вместо краба, ключ, целебная тыква вместо аптечки,
сюрикен), лежат в `extras()` тех же размеров. Дали: закат с горами в тумане, пагода и замок на
утёсе, бамбук с клёнами и соснами.

Имена и порядок цветов те же, что у `space16.py` (по ним модули демок `ninja_*16.py` берут цвета по
роли): K обводка, NAVY тёмно-синий (капюшон, дальние конечности, тёмные горы), SEA синий костюм,
AQUA мох и хвоя, SKY персиковое небо, WHITE обмотки, знамя, GREY тень белого, SKIN и TAN кожа и
дерево, GOLD и BRASS золото, METAL камень и сталь, DARK лак, тёмное дерево, чёрная маска, RED шарф
и клёны, VIOLET розовое небо и блик клёна, PLUM тень красного.

    python3 tools/ninja16.py --preview out.png   # лист набора в 4 раза крупнее
    python3 tools/ninja16.py --preview out.png --scale=6 --keys=hero_run,hero_idle
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pixel_sprites16 as base  # noqa: E402
from pixel_sprites import png_bytes  # noqa: E402

# Палитра «Ниндзя»: 16 цветов, индекс это та же роль, что у пиратов, космоса и замков.
K, NAVY, SEA, AQUA, SKY, WHITE, GREY, SKIN, TAN, GOLD, BRASS, METAL, DARK, RED, VIOLET, PLUM = range(16)
PALETTE = [
    (0x17, 0x0E, 0x1C),  # K      обводка
    (0x1C, 0x22, 0x50),  # NAVY   капюшон, дальние конечности, тёмные горы
    (0x33, 0x47, 0x90),  # SEA    синий костюм, дымка гор
    (0x6A, 0x96, 0x4A),  # AQUA   мох, хвоя, бамбук
    (0xFF, 0xC4, 0x8A),  # SKY    персиковое небо, блик заката
    (0xF6, 0xEE, 0xE0),  # WHITE  обмотки, знамя, солнце
    (0xB9, 0xAD, 0xB6),  # GREY   тень белого, свет камня
    (0xF0, 0xC0, 0x98),  # SKIN   кожа
    (0xA8, 0x6A, 0x42),  # TAN    дерево, тень кожи
    (0xF6, 0xC8, 0x4A),  # GOLD   золото, окна-огни
    (0xB8, 0x82, 0x24),  # BRASS  тень золота
    (0x7C, 0x74, 0x88),  # METAL  камень, сталь
    (0x3A, 0x2A, 0x38),  # DARK   лак, тёмное дерево, чёрная маска
    (0xD2, 0x32, 0x32),  # RED    шарф, клёны
    (0xE8, 0x76, 0x8A),  # VIOLET розовое небо, блик клёна
    (0x7A, 0x2A, 0x4C),  # PLUM   тень красного, закатные тучи
]
SHADOW = {SEA: NAVY, NAVY: DARK, AQUA: NAVY, SKY: VIOLET, VIOLET: PLUM, WHITE: GREY, GREY: METAL, SKIN: TAN,
          TAN: DARK, GOLD: BRASS, BRASS: DARK, METAL: DARK, RED: PLUM}
# Материалы для светотени рампами: два костюма отдельно, чтобы ближняя рука не слипалась с
# дальней, обмотки и знамя льняные, мох, кожа, дерево, золото, камень, лак, красное, закат.
GROUPS = {NAVY: "hood", SEA: "suit", AQUA: "moss", SKY: "dusk", VIOLET: "dusk", WHITE: "linen",
          GREY: "linen", SKIN: "skin", TAN: "wood", GOLD: "gold", BRASS: "gold", METAL: "stone",
          DARK: "lacquer", RED: "red", PLUM: "plum"}


class Canvas(base.Canvas):
    shadow = SHADOW


def strip(frames):
    out = Canvas(sum(f.w for f in frames), max(f.h for f in frames))
    x = 0
    for f in frames:
        out.paste(f, x, 0)
        x += f.w
    return out


# --- Ниндзя ------------------------------------------------------------------------------------
# Силуэт не как у космонавта и рыцаря: тонкое тело, круглый капюшон без забрала и шлема, над
# плечом торчит рукоять меча с золотой цубой, за спиной по ветру тянутся два красных конца
# шарфа. Позы, габариты и точка опоры (ступни на 29-30 строках) те же, что у образцов.

def _head(c, x, y, face=1):
    """Капюшон лицом вправо при `face` 1: круглый, тёмно-синий; полоска глаз (кожа, два тёмных
    глаза) во всю переднюю половину, ниже маска и красный шарф на шее. Центр (x, y)."""
    c.ellipse(x - 0.5 * face, y + 0.5, 4.6, 4.6, NAVY)
    a, b = sorted((x - face, x + 4 * face))
    c.rect(a, y - 1, b, y + 1, SKY)
    for dx in (1, 3):
        c.set(x + dx * face, y, K)
    # Узелок капюшона на затылке.
    c.set(x - 5 * face, y, NAVY)
    c.set(x - 5 * face, y + 1, NAVY)
    a, b = sorted((x - 3 * face, x + 3 * face))
    c.rect(a, y + 4, b, y + 5, RED)
    c.rect(x - 5 * face, y + 4, x - 4 * face, y + 5, RED)


def _scarf(c, x, y, face=1, ph=0.0, slope=0.3, n=8):
    """Узел у шеи и два конца шарфа назад по ветру длиной `n` и `n - 2` пикселей, нижний темнее;
    волна по длине. `slope` это снос вниз на пиксель."""
    for kn, col, dy in ((n - 2, PLUM, 3.0), (n, RED, 0.0)):
        for k in range(kn):
            amp = 1.0 * min(1.0, k / 4.0)
            px = x - (5 + k) * face
            py = y + 4.6 + dy + k * slope + math.sin(k * 0.7 - ph) * amp
            c.set(px, py, col)
            if col == RED and k < n - 2:
                c.set(px, py + 1, col)


def _sword(c, x, y):
    """Меч за спиной одной прямой диагональю: короткая рукоять над дальним плечом с золотой
    цубой точкой, тёмные ножны вниз-вправо за телом (шарфа не касаются)."""
    c.line(x - 1, y - 3, x + 5, y + 4, DARK, 2)
    c.line(x - 3, y - 5, x - 4, y - 7, TAN, 2)
    c.set(x - 2, y - 4, GOLD)


def _body(c, x0, y0, x1, y1):
    """Тонкий корпус: сплошной тёмно-синий костюм с одним светлым бликом и тонкий красный пояс."""
    c.rect(x0 + 1, y0, x1 - 1, y1, NAVY)
    c.rect(x1 - 3, y0 + 1, x1 - 3, y1 - 4, SEA)
    c.rect(x0 + 1, y1 - 1, x1 - 1, y1 - 1, RED)


def _boot(c, x, y, w=4):
    """Таби: тёмная стопа с носком вперёд."""
    c.rect(x - 1, y - 1, x + 1, y - 1, DARK)
    c.rect(x - 1, y, x + w - 1, y + 1, DARK)


def _leg(c, hx, hy, kx, ky, fx, fy, cloth):
    """Нога тонкая: бедро в цвет костюма, голень в светлых обмотках, таби."""
    c.line(hx, hy, kx, ky, cloth, 3)
    c.line(kx, ky, fx, fy, cloth, 3)
    c.line(kx + (fx - kx) * 0.35, ky + (fy - ky) * 0.35, fx, fy - 1, WHITE, 3)
    _boot(c, fx, fy)


def _arm(c, x0, y0, x1, y1, col):
    """Рука: рукав, белая обмотка у запястья, кулак цвета кожи. Ближняя NAVY, дальняя DARK."""
    c.line(x0, y0, x1, y1, col, 2)
    c.ellipse(x0 + (x1 - x0) * 0.8, y0 + (y1 - y0) * 0.8, 1.0, 1.0, WHITE)
    c.ellipse(x1, y1, 1.2, 1.2, SKIN)


def ninja_side(phase, jump=False):
    """Ниндзя сбоку, лицом вправо: бег по фазе 0..2π или прыжок."""
    c = Canvas()
    bob = 0 if jump else int(round(abs(math.sin(phase)) * 1.4))
    hip_y = 21 - bob
    swing = 0.9 if jump else math.sin(phase)
    _arm(c, 15, 15 - bob, 15 + 5 * swing, 20 - bob - (3 if jump else 0), DARK)
    for sign, cloth in ((-1, DARK), (1, NAVY)):
        a = swing * sign
        lift = max(0.0, math.cos(phase) * sign) * 3.0 if not jump else (4 if sign > 0 else 1)
        foot = (15 + 6 * a, 29 - lift)
        knee = ((15 + foot[0]) / 2 + 2, (hip_y + foot[1]) / 2)
        _leg(c, 15 + sign, hip_y, knee[0], knee[1], foot[0], foot[1], cloth)
    _sword(c, 9, 9 - bob)
    _scarf(c, 16, 7 - bob, 1, phase, 0.1 if jump else 0.3)
    _body(c, 11, 13 - bob, 19, hip_y)
    _arm(c, 16, 15 - bob, 16 - 5 * swing, 20 - bob - (4 if jump else 0), NAVY)
    _head(c, 16, 7 - bob)
    return c.finish()


def ninja_back(phase):
    """Со спины: бежит вглубь экрана, два конца шарфа свисают по спине, меч наискось с рукоятью
    над правым плечом, капюшон без полоски глаз."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.4))
    for sign in (-1, 1):
        lift = max(0.0, s * sign) * 4.0
        x = 16 + sign * 3
        c.rect(x - 1, 21 - bob, x + 1, 28 - lift, NAVY if sign > 0 else DARK)
        c.rect(x - 1, 25 - bob + int(lift * 0.3), x + 1, 28 - lift, WHITE)
        _boot(c, x - 1, 28 - lift)
        _arm(c, 16 + sign * 6, 15 - bob, 16 + sign * 7, 20 - bob + s * sign * 2, NAVY if sign > 0 else DARK)
    c.rect(12, 13 - bob, 19, 21 - bob, NAVY)
    c.rect(13, 14 - bob, 13, 18 - bob, SEA)
    c.rect(12, 20 - bob, 19, 20 - bob, RED)
    # Меч наискось поверх: ножны от левого бедра к правому плечу, рукоять над плечом.
    c.line(13, 20 - bob, 20, 11 - bob, DARK, 2)
    c.line(14, 19 - bob, 20, 11 - bob, METAL, 1)
    c.line(21, 9 - bob, 22, 7 - bob, TAN, 2)
    c.set(21, 10 - bob, GOLD)
    # Один конец шарфа свисает вниз по спине.
    for k in range(8):
        x = 15 + int(round(math.sin(k * 0.7 - phase) * min(1.0, k / 3.0)))
        c.rect(x, 12 - bob + k, x + 1, 12 - bob + k, RED)
    # Круглый капюшон, затылочный узел.
    c.ellipse(15.5, 7.5 - bob, 4.8, 4.8, NAVY)
    c.rect(14, 3 - bob, 16, 3 - bob, SEA)
    c.rect(12, 11 - bob, 19, 12 - bob, RED)
    c.rect(18, 8 - bob, 20, 9 - bob, NAVY)
    return c.finish()


def ninja_leap(i):
    """Прыжок через клетку, четыре кадра: присел, толчок, поджал ноги, приземление."""
    c = Canvas()
    crouch = (3, 0, -1, 2)[i]
    legs = ((2, 2), (5, -4), (3, -1), (4, 3))[i]
    hip_y = 21 + crouch
    _arm(c, 15, 15 + crouch, 12 - i % 2, 11 + crouch if i in (1, 2) else 20 + crouch, DARK)
    for sign, cloth in ((-1, DARK), (1, NAVY)):
        foot = (15 + sign * legs[0] + (2 if i == 1 else 0), 29 if i in (0, 3) else 27 - (2 if i == 2 else 0))
        knee = ((15 + foot[0]) / 2 + 2 + legs[1] * 0.3, (hip_y + foot[1]) / 2 + (2 if i == 2 else 0))
        _leg(c, 15 + sign, hip_y, knee[0], knee[1], foot[0], foot[1], cloth)
    _sword(c, 9, 9 + crouch)
    _scarf(c, 16, 7 + crouch, 1, i * 1.6, (0.5, 0.1, 0.1, 0.3)[i])
    _body(c, 11, 13 + crouch, 19, hip_y)
    _arm(c, 16, 15 + crouch, 20 + i % 2, 10 + crouch if i in (1, 2) else 20 + crouch, NAVY)
    _head(c, 16, 7 + crouch)
    return c.finish()


def ninja_idle(i):
    """Стойка: два кадра, ниндзя дышит, концы шарфа чуть колышутся."""
    c = Canvas()
    up = i
    for sign, cloth in ((-1, DARK), (1, NAVY)):
        x = 15 + sign * 2
        c.rect(x - 1, 21, x + 1, 28, cloth)
        c.rect(x - 1, 24, x + 1, 28, WHITE)
        _boot(c, x, 29)
    _arm(c, 14, 15 - up, 13, 21 - up, DARK)
    _sword(c, 9, 9 - up)
    _scarf(c, 16, 7 - up, 1, i * 2.2, 0.4, 8)
    _body(c, 11, 13 - up, 19, 21)
    _arm(c, 17, 15 - up, 18, 21 - up, NAVY)
    _head(c, 16, 7 - up)
    return c.finish()


def _lean(c, sx, sy, hx, hy, w):
    """Корпус под наклоном: от плеч (sx, sy) к бёдрам (hx, hy), ширина w; синий костюм, красный
    пояс у бёдер."""
    n = math.hypot(hx - sx, hy - sy)
    dx, dy = (hx - sx) / n, (hy - sy) / n
    for k in range(int(n) + 1):
        x, y = sx + dx * k, sy + dy * k
        col = RED if k == int(n) else NAVY
        c.line(x + dy * w / 2, y - dx * w / 2, x - dy * w / 2, y + dx * w / 2, col, 2)


def ninja_slide(i):
    """Подкат на боку ногами вперёд: корпус откинут, ближняя нога вытянута, дальняя коленом вверх,
    рука сзади на земле, шарф стелется назад. Макушка капюшона на 16-й строке. Два кадра: колено
    и пыль."""
    c = Canvas()
    c.line(19, 27, 24, 23 - i, DARK, 3)
    c.line(24, 23 - i, 27, 27, DARK, 3)
    c.line(24.5, 24, 27, 27, WHITE, 3)
    _boot(c, 27, 27)
    c.line(13, 24, 19, 23, DARK, 2)
    _scarf(c, 10, 21, 1, i * 2.0, 0.1, 8)
    _lean(c, 12, 24, 19, 27, 5)
    c.line(19, 28, 28, 28, NAVY, 3)
    c.line(22, 28, 27, 28, WHITE, 3)
    c.rect(28, 27, 30, 29, DARK)
    _arm(c, 11, 25, 6, 29, NAVY)
    _head(c, 10, 21)
    c.finish()
    for k, (x, y) in enumerate(((2, 30), (4, 31), (1, 28), (3, 29))):
        if (k + i) % 2 == 0:
            c.set(x, y, GREY)
    return c


def ninja_crouch(i):
    """Присед: та же фигура, сложенная вниз, корпус прямо, колени вперёд. Два кадра шага."""
    c = Canvas()
    step = (-1, 1)[i]
    c.line(15, 24, 19, 26, DARK, 2)
    for sign, cloth in ((-1, DARK), (1, NAVY)):
        hip = (14, 27)
        knee = (20 - sign + step * sign, 26)
        foot = (17 - sign * 2 + step * sign * 2, 29)
        c.line(hip[0], hip[1], knee[0], knee[1], cloth, 3)
        c.line(knee[0], knee[1], foot[0], foot[1], cloth, 3)
        c.line(knee[0] + (foot[0] - knee[0]) * 0.3, knee[1] + 1, foot[0], foot[1] - 1, WHITE, 2)
        _boot(c, foot[0], foot[1])
    _sword(c, 9, 18)
    _scarf(c, 16, 19, 1, i * 2.0, 0.35, 8)
    _body(c, 11, 22, 18, 26)
    _arm(c, 14, 24, 19, 26, NAVY)
    _head(c, 16, 19)
    return c.finish()


def ninja_hang(i):
    """На тросе: руки вверх к точке хвата (центр сверху), ноги свисают и качаются, шарф вьётся."""
    c = Canvas()
    sw = (-1, 1)[i]
    c.line(14, 13, 15, 1, DARK, 3)
    c.line(18, 13, 17, 1, NAVY, 2)
    c.ellipse(15, 1, 1.2, 1.2, SKIN)
    c.ellipse(17, 1, 1.2, 1.2, SKIN)
    _sword(c, 9, 13)
    _scarf(c, 16, 8, 1, i * 2.5, 0.5, 8)
    _body(c, 11, 13, 20, 21)
    for sign, cloth in ((-1, DARK), (1, NAVY)):
        foot = (15.5 + sign * 2 + sw * 2, 29)
        c.line(15.5 + sign * 2, 21, foot[0], foot[1], cloth, 3)
        c.line(15.5 + sign * 2 + sw, 25, foot[0], foot[1] - 1, WHITE, 3)
        _boot(c, foot[0], foot[1], 3)
    c.finish()
    hd = Canvas()
    _head(hd, 16, 8)
    hd.finish()
    for y in range(hd.h):
        for x in range(hd.w):
            if hd.px[y][x] is not None and y >= 1:
                c.set(x, y, hd.px[y][x])
    return c


# --- Враг: ниндзя чужого клана -----------------------------------------------------------------
# Красный костюм, чёрный капюшон, красная повязка с короткими концами, серп (кама) в руке.
# Шаг и рост повторяют стражника замков.

def _sickle(c, x, y, face):
    """Серп: рукоять от (x, y+10) до (x, y), клинок дугой от верха рукояти в сторону `face`."""
    c.rect(x - (1 if face > 0 else 0), y, x - (1 if face > 0 else 0) + 1, y + 11, TAN)
    pts = [(x + face * 4.4 - face * 4.4 * math.cos(math.radians(a)), y + 4.4 * math.sin(math.radians(a)))
           for a in (0, -35, -70, -105, -140, -170)]
    for p, q in zip(pts, pts[1:]):
        c.line(p[0], p[1], q[0], q[1], GREY, 3)
    c.line(pts[0][0], pts[0][1], pts[1][0], pts[1][1], METAL, 1)
    c.set(pts[2][0] - face, pts[2][1] - 1, WHITE)
    c.set(pts[3][0], pts[3][1] - 1, WHITE)


def _rival_head(c, x, y, face):
    """Голова врага лицом в сторону `face`: чёрный капюшон, полоска кожи с глазами, красная
    повязка со сносом назад."""
    c.ellipse(x, y, 4.4, 4.4, DARK)
    a, b = sorted((x, x + 4 * face))
    c.rect(a, y, b, y + 1, SKIN)
    c.set(x + 1 * face, y, K)
    c.set(x + 3 * face, y, K)
    a, b = sorted((x - 4, x + 4))
    c.rect(a, y - 2, b, y - 1, RED)
    for k in range(1, 5):
        c.set(x - (4 + k) * face, y - 2 + k * 0.5, RED)
        c.set(x - (4 + k) * face, y - 1 + k * 0.5, PLUM)


def enemy_side(phase):
    """Ниндзя чужого клана сбоку, лицом влево (навстречу герою): шаг по фазе, серп в ближней руке."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.2))
    for sign, col in ((-1, PLUM), (1, RED)):
        a = s * sign
        lift = max(0.0, math.cos(phase) * sign) * 2.5
        foot = (16 - 5 * a, 29 - lift)
        knee = ((16 + foot[0]) / 2 - 1.5, (22 - bob + foot[1]) / 2)
        c.line(16, 22 - bob, knee[0], knee[1], col, 3)
        c.line(knee[0], knee[1], foot[0], foot[1], col, 2)
        c.rect(foot[0] - 3, foot[1], foot[0], foot[1] + 1, DARK)
    c.rect(13, 13 - bob, 18, 22 - bob, RED)
    c.rect(13, 19 - bob, 18, 20 - bob, DARK)
    c.line(13, 14 - bob, 18, 18 - bob, PLUM, 1)
    c.rect(18, 19 - bob, 20, 21 - bob, DARK)
    _rival_head(c, 15, 8 - bob, -1)
    # Серп впереди, ближняя рука держит рукоять.
    _sickle(c, 8, 11 - bob, -1)
    c.line(15, 15 - bob, 8, 18 - bob, PLUM, 2)
    c.ellipse(8, 18 - bob, 1.3, 1.3, SKIN)
    c.finish()
    return c


def enemy_front(phase):
    """Ниндзя чужого клана лицом к камере: идёт на игрока, ноги по очереди, серп у правого плеча."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.2))
    c.line(11, 14 - bob, 8, 20 - bob + s * 2, PLUM, 2)
    for sign in (-1, 1):
        lift = max(0.0, s * sign) * 3.0
        x = 16 + sign * 3
        c.line(x, 22 - bob, x, 28 - lift, RED if sign > 0 else PLUM, 3)
        c.rect(x - 2, 28 - lift, x + 1, 29 - lift, DARK)
    c.rect(12, 13 - bob, 19, 22 - bob, RED)
    c.rect(12, 19 - bob, 19, 20 - bob, DARK)
    c.line(13, 14 - bob, 18, 18 - bob, PLUM, 1)
    c.ellipse(15.5, 8 - bob, 4.8, 4.6, DARK)
    c.rect(13, 8 - bob, 18, 9 - bob, SKIN)
    c.rect(11, 5 - bob, 20, 6 - bob, RED)
    c.set(21, 6 - bob, RED)
    c.set(22, 7 - bob, PLUM)
    # Серп справа: рукоять от руки вверх, клинок крюком в сторону головы.
    _sickle(c, 25, 9 - bob, -1)
    c.line(19, 14 - bob, 24, 18 - bob, RED, 2)
    c.ellipse(24.5, 18 - bob, 1.3, 1.3, SKIN)
    c.finish()
    c.set(14, 8 - bob, K)
    c.set(17, 8 - bob, K)
    return c


# --- Вещи --------------------------------------------------------------------------------------

def coin(i):
    """Монета с квадратным отверстием вращается: шесть кадров, ширина по косинусу, ребро темнее."""
    c = Canvas()
    rx = max(1.0, abs(math.cos(math.pi * i / 6.0)) * 7.0)
    cx = 15.5
    c.ellipse(cx, 16, rx, 10.5, BRASS)
    if rx > 2:
        c.ellipse(cx, 16, rx - 1.3, 9.2, GOLD)
    if rx > 3:
        k = rx / 7.0
        # Квадратное отверстие в центре, кольцо-кант вокруг.
        h = max(2.0, 2.4 * k)
        c.rect(cx - h - 1.5 * k, 16 - 4.5, cx + h + 1.5 * k, 16 + 3.5, BRASS)
        c.rect(cx - h, 16 - 3, cx + h - 1, 16 + 2, None)
        c.line(cx - rx * 0.6, 8, cx - rx * 0.3, 7, WHITE, 1)
        c.set(cx - rx * 0.55, 20, WHITE)
        c.set(cx + rx * 0.5, 12, BRASS)
    return c.finish()


def flag(i):
    """Нобори: узкое вертикальное знамя белого цвета с красным кругом подвешено к поперечине на
    древке с золотым навершием; полотнище колышется волной снизу вверх."""
    c = Canvas()
    c.rect(5, 4, 6, 31, TAN)
    c.rect(5, 4, 18, 5, TAN)
    c.ellipse(5.5, 3, 1.8, 1.8, GOLD)
    c.rect(18, 4, 18, 6, TAN)
    waves = []
    for y in range(6, 30):
        w = math.sin(y * 0.38 - i * math.pi / 3.0) * 1.7 * (y - 6) / 23.0
        waves.append(w)
        for x in range(7, 17):
            c.set(x + w, y, WHITE)
    # Нижний край с коротким вырезом, чтобы не был ровным.
    c.set(11.5 + waves[-1], 29, None)
    c.set(12.5 + waves[-1], 29, None)
    c.shade()
    c.outline()
    # Красный круг (солнце) и узкая красная кайма по левому краю.
    my = 15
    mw = waves[my - 6]
    c.ellipse(11.5 + mw, my, 3.4, 3.4, RED)
    c.set(10.5 + mw, my - 2, VIOLET)
    for y in range(6, 29):
        c.set(7 + waves[y - 6], y, RED)
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
    """Каменная дорожка из плит со мхом сверху; ниже тёмная земля с камнями и корешками. Плитка
    стыкуется по сторонам."""
    c = Canvas()
    c.rect(0, 0, 31, 31, DARK)
    # Земля: крапины сливового, булыжники, корешки.
    for x, y in ((3, 12), (11, 16), (19, 11), (27, 14), (7, 21), (15, 24), (24, 20), (30, 26), (2, 28), (21, 29)):
        c.set(x, y, PLUM)
        c.set(x + 1, y, PLUM)
    for cx, cy, rx, ry in ((6, 15, 3, 2), (22, 17, 3.5, 2.5), (14, 27, 4, 2.5), (29, 24, 2.5, 2), (1, 23, 2.5, 2)):
        for k in (0, 32, -32):
            c.ellipse(cx + k, cy, rx, ry, METAL)
            c.ellipse(cx + k - 0.5, cy - 0.7, rx - 1.2, ry - 1.1, GREY)
    for x in (9, 25):
        c.line(x, 9, x - 2, 12, TAN, 1)
    if not inner:
        # Плиты: светлая грань сверху, шов тёмный, плиты вразбежку.
        c.rect(0, 2, 31, 8, METAL)
        c.rect(0, 2, 31, 2, GREY)
        for x in (0, 16):
            c.rect(x, 2, x, 8, DARK)
        c.rect(0, 5, 31, 5, DARK)
        for x in (8, 24):
            c.rect(x, 5, x, 8, DARK)
        c.rect(0, 9, 31, 9, DARK)
        for x in (1, 17):
            c.rect(x, 3, x, 4, GREY)
        for x in (9, 25):
            c.rect(x, 6, x, 7, GREY)
        # Мох по кромке и в швах.
        c.rect(0, 0, 31, 1, AQUA)
        for x in range(32):
            if (x * 5 + 3) % 7 < 4:
                c.set(x, 2, AQUA)
            if (x * 3) % 8 == 0:
                c.set(x, 3, AQUA)
        for x, y in ((0, 5), (16, 5), (8, 8), (24, 8), (5, 9), (21, 9)):
            c.set(x, y, AQUA)
    return c


def rock():
    """Каменный фонарь (торо): пьедестал, столб, огневая камера с тёплым окном, широкая крыша с
    загнутыми краями и жемчужиной, мох."""
    c = Canvas()
    c.rect(8, 26, 23, 29, METAL)
    c.rect(11, 20, 20, 26, METAL)
    c.rect(13, 19, 18, 25, GREY)
    c.rect(14, 14, 17, 19, METAL)
    # Огневая камера с окном-огнём.
    c.rect(10, 8, 21, 15, METAL)
    c.rect(12, 10, 19, 13, GOLD)
    c.rect(15, 10, 16, 13, SKY)
    c.rect(10, 8, 21, 8, GREY)
    # Крыша: широкая, края вверх, жемчужина на макушке.
    c.poly([(1, 8), (4, 8), (7, 5), (24, 5), (27, 8), (30, 8), (27, 10), (4, 10)], DARK)
    c.rect(8, 3, 23, 4, DARK)
    c.rect(13, 1, 18, 2, DARK)
    c.set(15, 0, GOLD)
    c.set(16, 0, GOLD)
    c.rect(7, 5, 24, 5, METAL)
    # Мох на крыше и у основания.
    for x in (9, 12, 19, 22):
        c.set(x, 4, AQUA)
    c.rect(9, 27, 12, 28, AQUA)
    c.rect(21, 28, 22, 28, AQUA)
    c.set(11, 22, AQUA)
    return c.finish()


def chest():
    """Чёрный лаковый ларец: коробка с выпуклой крышкой, золотые угольники, полоса и замок."""
    c = Canvas()
    c.rect(4, 14, 27, 28, DARK)
    c.ellipse(15.5, 14, 12, 7, DARK)
    # Блик лака на крышке и боку.
    c.line(8, 9, 15, 7, METAL, 1)
    c.line(6, 17, 6, 25, PLUM, 1)
    # Золотые угольники, полоса по стыку крышки и замок.
    c.rect(4, 14, 27, 15, GOLD)
    c.rect(4, 14, 7, 22, GOLD)
    c.rect(24, 14, 27, 22, GOLD)
    c.rect(4, 26, 8, 28, GOLD)
    c.rect(23, 26, 27, 28, GOLD)
    c.rect(14, 13, 17, 20, GOLD)
    c.rect(14, 13, 17, 13, WHITE)
    c.set(15, 17, K)
    c.set(16, 17, K)
    c.rect(15, 18, 16, 19, K)
    # Красный шнурок-пломба.
    c.set(15, 21, RED)
    c.set(16, 21, RED)
    c.set(15, 22, RED)
    return c.finish()


# --- Параллакс ---------------------------------------------------------------------------------
# Три слоя дали. Высоты периодические (синусы с целым числом периодов на 256), ленты стыкуются
# по краям. Небо только в `par_sky`.

def _wrap_ellipse(c, cx, cy, rx, ry, col):
    for k in (0, 256, -256):
        c.ellipse(cx + k, cy, rx, ry, col)


def _dither(x, y):
    return (x + y) % 2 == 0


def par_sky():
    """Дальний слой: закат, розовый верх, персиковая середина, золото у горизонта, солнце и тучи,
    две гряды гор в тумане; лента 256×48, стыкуется по краям."""
    c = Canvas(256, 48)
    tau = math.pi * 2 / 256.0
    # Небо полосами с шахматным переходом.
    for y in range(48):
        for x in range(256):
            if y < 9:
                col = VIOLET
            elif y < 12:
                col = SKY if _dither(x, y) else VIOLET
            elif y < 24:
                col = SKY
            elif y < 27:
                col = GOLD if _dither(x, y) else SKY
            else:
                col = GOLD
            c.set(x, y, col)
    # Солнце с ореолом, на закате над дальней грядой.
    sx, sy = 88, 30
    c.ellipse(sx, sy, 15, 15, SKY)
    c.ellipse(sx, sy, 11, 11, GOLD)
    c.ellipse(sx, sy, 7, 7, WHITE)
    # Тучи: длинные тонкие полосы сливового и розового, светлая кромка снизу.
    for cx, cy, rx in ((30, 7, 24), (140, 4, 30), (205, 14, 26), (60, 16, 18), (118, 18, 20)):
        for k in (0, 256, -256):
            c.ellipse(cx + k, cy, rx, 1.3, PLUM)
            c.ellipse(cx + k, cy + 1.2, rx * 0.8, 0.8, VIOLET)
            c.ellipse(cx + k + 2, cy + 2.2, rx * 0.5, 0.6, SKY)

    def ridge_a(x):
        return 14 + 9 * abs(math.sin(x * tau * 3 + 0.4)) + 3 * math.sin(x * tau * 8 + 1.0)

    def ridge_b(x):
        return 7 + 6 * abs(math.sin(x * tau * 4 + 1.9)) + 2 * math.sin(x * tau * 11)

    for x in range(256):
        ta = 47 - int(ridge_a(x))
        c.rect(x, ta, x, 47, METAL)
        c.set(x, ta, GREY)
        # Туман: к подножию гряда растворяется в светлой дымке.
        for y in range(ta + 5, 47):
            if y >= 34 and (_dither(x, y) or y >= 38):
                c.set(x, y, SKY if y < 38 else GREY)
    # Лента тумана между грядами.
    for y in range(36, 41):
        for x in range(256):
            if (x // 2 + y) % 2 == 0 or y in (37, 38, 39):
                c.set(x, y, GREY if y != 39 else SKY)
    for x in range(256):
        tb = 47 - int(ridge_b(x))
        c.rect(x, tb, x, 47, SEA)
        c.set(x, tb, METAL)
        c.rect(x, tb + 6, x, 47, NAVY)
    # Вечерняя стая в небе: маленькие чёрные галочки.
    for bx, by in ((150, 14), (156, 17), (162, 13), (167, 16)):
        c.set(bx, by, DARK)
        c.set(bx + 1, by - 1, DARK)
        c.set(bx + 2, by, DARK)
    return c


def _roof(c, x, y, hw, col, edge=None):
    """Загнутая черепичная крыша: центр (x, y) нижней кромки, полуширина `hw`, края вверх."""
    c.poly([(x - hw - 4, y - 3), (x - hw - 1, y), (x + hw + 1, y), (x + hw + 4, y - 3), (x + hw - 1, y - 3),
            (x + hw - 3, y - 5), (x - hw + 3, y - 5), (x - hw + 1, y - 3)], col)
    if edge is not None:
        c.rect(x - hw - 1, y, x + hw + 1, y, edge)


def _pagoda(c, x, base, tiers, w):
    """Пагода на горизонте: ярусы с красными колоннами, тёмные загнутые крыши, шпиль с золотом."""
    y = base
    for t in range(tiers):
        hw = max(3, w // 2 - t * 2)
        c.rect(x - hw + 1, y - 5, x + hw - 1, y, PLUM)
        c.rect(x - hw + 1, y - 5, x - hw + 1, y, RED)
        c.rect(x + hw - 1, y - 5, x + hw - 1, y, RED)
        c.set(x, y - 3, GOLD)
        y -= 5
        _roof(c, x, y, hw + 1, DARK, METAL)
    c.line(x, y - 6, x, y - 14, DARK, 1)
    c.set(x, y - 15, GOLD)
    c.rect(x - 1, y - 9, x + 1, y - 9, GOLD)


def _keep(c, x, base):
    """Японский замок на каменном основании: три яруса белых стен с тёмными крышами, золотые
    дельфины на коньке."""
    c.poly([(x - 20, base), (x - 16, base - 9), (x + 16, base - 9), (x + 20, base)], METAL)
    c.rect(x - 16, base - 9, x + 16, base - 9, GREY)
    y = base - 9
    for hw, hh in ((12, 6), (9, 5), (6, 4)):
        c.rect(x - hw, y - hh, x + hw, y, WHITE)
        c.rect(x - hw, y - 2, x + hw, y - 2, GREY)
        for wx in range(x - hw + 3, x + hw - 1, 5):
            c.rect(wx, y - hh + 1, wx, y - hh + 2, DARK)
        y -= hh
        _roof(c, x, y, hw + 1, DARK, METAL)
        y -= 1
    c.set(x - 6, y - 5, GOLD)
    c.set(x + 6, y - 5, GOLD)
    c.rect(x, y - 5, x, y - 3, DARK)
    c.set(x, y - 6, GOLD)


def par_far():
    """Средний слой: тёмные утёсы в закатной дымке, на одном пагода, на другом замок; сосны на
    склонах. Лента 256×48, низ сплошной, неба нет."""
    c = Canvas(256, 48)
    tau = math.pi * 2 / 256.0

    def height(x):
        h = 7 + 3 * math.sin(x * tau * 6 + 0.5)
        h += 17 * max(0.0, math.sin((x - 24) * math.pi / 72.0)) ** 2 if 24 <= x <= 96 else 0
        h += 12 * max(0.0, math.sin((x - 140) * math.pi / 104.0)) ** 2 if 140 <= x <= 244 else 0
        return h

    for x in range(256):
        top = 47 - int(height(x))
        c.rect(x, top, x, 47, METAL)
        c.rect(x, top, x, top, GREY)
        c.rect(x, top + 1, x, top + 1, SKY)
        c.rect(x, top + 8, x, 47, SEA)
        c.rect(x, top + 20, x, 47, NAVY)
    # Пагода на левом утёсе, замок на правом (оба стоят на ровной вершине).
    px = 60
    pb = 47 - int(height(px)) + 1
    _pagoda(c, px, pb, 3, 12)
    kx = 192
    kb = 47 - int(height(kx)) + 1
    _keep(c, kx, kb)
    # Сосны на склонах (силуэты), мелкие.
    for x in (36, 84, 112, 150, 238):
        by = 47 - int(height(x)) + 2
        c.line(x, by, x + 1, by - 8, DARK, 1)
        for dy, rx in ((-9, 5), (-6, 4)):
            c.ellipse(x + 1, by + dy, rx, 1.5, NAVY)
    return c


def _bamboo(c, x, base, h, ph):
    """Стебель бамбука: тёмный с моховым бликом, колена, наверху пара узких листьев."""
    top = base - h
    c.rect(x, top, x + 1, base, DARK)
    c.rect(x, top, x, base, AQUA)
    for y in range(top + 4, base, 6):
        c.rect(x, y, x + 1, y, DARK)
    for dx, dy in ((-4, 2), (4, 3), (-5, 7), (5, 8)):
        c.line(x + 1, top + dy - 1, x + 1 + dx, top + dy + 1, AQUA, 1)
        c.set(x + 1 + dx, top + dy + 2, DARK)


def _maple(c, x, base, r):
    """Клён: тёмный ствол, красная крона из гроздей с розовым бликом, золотые листья."""
    c.line(x, base, x - 1, base - r * 0.8, DARK, 2)
    c.line(x - 1, base - r * 0.8, x - r * 0.5, base - r * 1.4, DARK, 1)
    for dx, dy, rr, col in ((0, -1.2, 0.9, RED), (-0.8, -0.6, 0.7, PLUM), (0.8, -0.7, 0.7, RED),
                            (-0.3, -1.7, 0.6, RED), (0.9, -1.4, 0.5, PLUM)):
        c.ellipse(x + dx * r, base - r * 1.2 + dy * r * 0.8, rr * r, rr * r * 0.7, col)
    c.ellipse(x - r * 0.3, base - r * 2.0, r * 0.4, r * 0.25, VIOLET)
    c.set(x + r * 0.8, base - r * 0.6, GOLD)
    c.set(x - r * 0.9, base - r * 0.4, GOLD)


def _pine(c, x, base, h):
    """Японская сосна: изогнутый ствол и несколько плоских ярусов хвои с тёмным низом."""
    c.line(x, base, x + 2, base - h * 0.5, DARK, 2)
    c.line(x + 2, base - h * 0.5, x - 1, base - h, DARK, 1)
    for dx, dy, rx in ((2, 0.5, 6), (-4, 0.7, 5), (-1, 1.0, 6)):
        cy = base - h * dy
        c.ellipse(x + dx, cy, rx, 2, DARK)
        c.ellipse(x + dx, cy - 1, rx - 0.5, 1.4, AQUA)


def par_mid():
    """Ближний слой: бугры холмов с бамбуком, красными клёнами и соснами, лента 256×32."""
    c = Canvas(256, 32)

    def crest(x):
        return 17 + 3 * math.sin(x * math.pi / 32.0) + 1.5 * math.sin(x * math.pi / 8.0 + 1.0)

    # Деревья сперва (за буграми), потом земля поверх подножий.
    for px in (36, 40, 44, 122, 126, 130, 134, 214):
        _bamboo(c, px, int(crest(px)) + 4, 17 + (px * 7) % 6, px)
    for px, r in ((18, 5), (82, 6), (170, 5), (244, 5)):
        _maple(c, px, int(crest(px)) + 4, r)
    for px in (62, 108, 150, 196):
        _pine(c, px, int(crest(px)) + 4, 17)
    for x in range(256):
        top = int(round(crest(x)))
        c.rect(x, top, x, 31, DARK)
        c.rect(x, top, x, top + 1, AQUA)
        if (x * 5 + top) % 9 == 0:
            c.set(x, top + 2, AQUA)
        if (x * 3 + top) % 11 == 0:
            c.set(x, top + 12 + x % 5, PLUM)
        if (x * 7 + top * 3) % 23 == 0:
            c.set(x, top + 5 + (x % 6), METAL)
    return c


def sprites():
    """Ленты основы набора в палитре `PALETTE`: герой платформера, враг, вещи, земля, три слоя
    дали. Ключи, размеры и число кадров те же, что у `castles16.sprites()`. Ленты демок лежат
    в модулях `ninja_*16.py`."""
    return {
        "enemy_walk": strip([enemy_side(p) for p in base.phases()]),
        "enemy_front": strip([enemy_front(p) for p in base.phases()]),
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
        "hero_run": strip([ninja_side(p) for p in base.phases()]),
        "hero_jump": ninja_side(0.0, jump=True),
        "hero_leap": strip([ninja_leap(i) for i in range(4)]),
        "hero_idle": strip([ninja_idle(i) for i in range(2)]),
        "hero_back": strip([ninja_back(p) for p in base.phases()]),
        "hero_slide": strip([ninja_slide(i) for i in range(2)]),
        "hero_hang": strip([ninja_hang(i) for i in range(2)]),
        "hero_crouch": strip([ninja_crouch(i) for i in range(2)]),
    }


# --- Остальные слоты (ленты демок «тропа» и «до выхода» их берут) ------------------------------

def tengu(i):
    """Ворон-тэнгу (слот попугая) летит вправо: четыре кадра взмаха (вверх, середина, вниз,
    середина), тело по центру кадра. Чёрное оперение веером маховых, длинный красный клюв-нос,
    красная маска у глаза. Без красной обводки опасности: её кладёт модуль демки."""
    c = Canvas()
    ang = (272, 235, 100, 235)[i]
    # Дальнее крыло темнее и чуть позади, ближнее поверх: веер из четырёх маховых перьев.
    for sx, col, spread in ((13, PLUM, 14), (16, DARK, 16)):
        for j in range(4):
            a = math.radians(ang + (j - 1.5) * spread)
            ln = 15 - j * 1.5 + (2 if j == 0 else 0)
            c.line(sx, 17, sx + ln * math.cos(a), 17 + ln * math.sin(a) * 0.9, col, 3 if j < 2 else 2)
        if col == DARK:
            for j in range(4):
                a = math.radians(ang + (j - 1.5) * spread)
                c.set(sx + 5 * math.cos(a), 17 + 5 * math.sin(a) * 0.9 - 1, METAL)
    c.ellipse(15.5, 18, 4.5, 3.6, DARK)
    c.ellipse(15.5, 19.5, 2.6, 1.6, METAL)
    # Хвост веером.
    c.poly([(11, 18), (3, 16), (4, 19), (3, 22), (11, 21)], DARK)
    c.line(5, 19, 10, 19, METAL, 1)
    # Голова и красный длинный клюв-нос тэнгу.
    c.ellipse(21.5, 15, 3.2, 3.0, DARK)
    c.poly([(23, 14), (31, 16), (23, 18)], RED)
    c.line(24, 16, 30, 16, PLUM, 1)
    c.ellipse(21.5, 14.5, 1.2, 1.0, RED)
    c.finish()
    c.set(22, 14, WHITE)
    c.set(23, 14, K)
    return c


def toad(i):
    """Жаба (слот краба-ползуна) идёт прыжками вправо: четыре кадра (присела, толчок, в воздухе,
    приземление), бородавки, золотой глаз навыкате, широкий рот."""
    c = Canvas()
    lift = (0, 2, 5, 1)[i]
    ext = (0.0, 0.5, 1.0, 0.2)[i]
    # Дальние лапы тёмные, ближние в цвет тела.
    for dx, col in ((2, DARK), (0, AQUA)):
        foot = (8 - 5 * ext + dx, 29 - lift * 0.4)
        knee = (6 + dx, 22 - lift)
        c.line(12 + dx, 23 - lift, knee[0], knee[1], col, 4)
        c.line(knee[0], knee[1], foot[0], foot[1], col, 3)
        c.rect(foot[0] - 1, foot[1], foot[0] + 3, foot[1] + 1, col)
        fx = 22 + dx + 3 * ext
        c.line(fx, 24 - lift, fx + 1 + ext * 2, 29 - lift * 0.4, col, 2)
        c.rect(fx, 29 - int(lift * 0.4), fx + 3, 29 - int(lift * 0.4), col)
    c.ellipse(15, 21 - lift, 9.5, 6.2, AQUA)
    c.ellipse(17, 25 - lift, 6, 2.4, SKIN)
    c.ellipse(24, 19 - lift, 4.5, 3.6, AQUA)
    c.rect(20, 21 - lift, 29, 21 - lift, DARK)
    c.ellipse(22, 15 - lift, 2.3, 2.2, GOLD)
    c.ellipse(26, 16 - lift, 1.8, 1.8, GOLD)
    for wx, wy in ((8, 18), (12, 16), (16, 17), (11, 21), (18, 21), (14, 19), (6, 21)):
        c.set(wx, wy - lift, DARK)
    c.finish()
    c.set(22, 15 - lift, K)
    c.set(26, 16 - lift, K)
    c.set(28, 19 - lift, K)
    return c


def key():
    """Бронзовый ключ: кольцо-головка с квадратным отверстием (как у монеты), красная кисть."""
    c = Canvas(32, 32)
    c.ellipse(9, 16, 7, 7, GOLD)
    c.rect(7, 14, 10, 17, None)
    c.rect(16, 14, 29, 17, GOLD)
    c.rect(24, 18, 25, 22, GOLD)
    c.rect(28, 18, 29, 21, GOLD)
    c.rect(16, 14, 29, 14, WHITE)
    c.line(9, 23, 7, 30, RED, 1)
    c.line(10, 23, 11, 30, RED, 1)
    c.set(9, 23, PLUM)
    return c.finish()


def potion():
    """Целебная тыква-горлянка (аптечка): двойная тыква, красная верёвка на талии, пробка,
    белый круг с красным крестом."""
    c = Canvas(32, 32)
    c.ellipse(15.5, 22, 8.5, 7, TAN)
    c.ellipse(15.5, 12, 5.5, 5, TAN)
    c.rect(12, 14, 19, 17, TAN)
    c.rect(14, 4, 17, 7, DARK)
    c.rect(14, 3, 17, 3, GOLD)
    c.rect(11, 16, 20, 17, RED)
    c.set(10, 18, RED)
    c.set(9, 20, RED)
    c.set(21, 18, RED)
    c.ellipse(15.5, 23, 4.2, 4.2, WHITE)
    c.rect(15, 20, 16, 26, RED)
    c.rect(13, 22, 18, 23, RED)
    c.set(12, 10, SKIN)
    c.set(11, 20, SKIN)
    return c.finish()


def shuriken():
    """Сюрикен летит вправо: четырёхконечная стальная звезда с отверстием в центре. 16×16."""
    c = Canvas(16, 16)
    c.poly([(8, 0), (10, 6), (15, 8), (10, 10), (8, 15), (6, 10), (0, 8), (6, 6)], METAL)
    c.poly([(8, 1), (9, 6), (6, 6)], GREY)
    c.poly([(14, 8), (10, 7), (10, 6)], GREY)
    c.line(7, 5, 8, 2, WHITE, 1)
    c.rect(7, 7, 8, 8, None)
    return c.finish()


def extras():
    """Слоты ниндзя вне `sprites()`: ленты и вещи тех же размеров, что у замков, космоса и пиратов."""
    return {
        "parrot_fly": strip([tengu(i) for i in range(4)]),
        "crab_walk": strip([toad(i) for i in range(4)]),
        "key": key(),
        "medkit": potion(),
        "shot": shuriken(),
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
