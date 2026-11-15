#!/usr/bin/env python3
"""Набор «Фэнтези» для 16/32-bit (основа, зеркало `space16.py` и `castles16.py`): волшебный лес и
летающие острова в сиреневых сумерках, магия светится бирюзой и золотом. Герой это юный маг в синей
мантии до щиколоток с золотой каймой, остроконечной шляпе с загнутым назад кончиком и короткой
палкой-посохом с бирюзовым кристаллом; враг это гоблин с дубинкой. Те же ленты, размеры и число
кадров, что у космоса, пиратов и замков (`castles16.sprites()`); позы героя повторяют рыцаря кадр в
кадр, чтобы хитбоксы демок сходились (ноги на тех же строках, рост и ширина те же): меняется рисунок,
не геометрия. Силуэт мага это конус шляпы с кончиком назад, широкие поля и колокол мантии, у рыцаря
плоский шлем с гребнем и угловатые латы. Ни лат, ни кладки, ни холмов с замками.

Слоты космоса и их фэнтези: космонавт это маг, пришелец это гоблин, кристалл это золотая монета с
руной, флаг экспедиции это фиолетовое знамя гильдии со звездой, грузовая капсула это сундук-мимик
с зубами, метеорит это рунный камень со светящимся знаком, настил станции это мох над корнями.
Ленты, которых нет в `sprites()` (блуждающий огонёк вместо попугая-дрона, слизь вместо краба,
ключ, зелье вместо аптечки, огненный шар), лежат в `extras()` тех же размеров.

Имена и порядок цветов те же, что у `space16.py` (по ним модули демок `fantasy_*16.py` берут цвета
по роли): K обводка, NAVY глубокий индиго (тень мантии и ночных крон), SEA синяя мантия, AQUA
бирюза магии, SKY светлая лаванда (дымка, блики), WHITE почти белый блик, GREY лавандово-серый
(рунный камень), SKIN и TAN кожа и корни, GOLD и BRASS золото, METAL зелень мха и кожа гоблина,
DARK тёмная земля, RED огонь и сердце, VIOLET и PLUM сиреневая листва и знамя гильдии.

    python3 tools/fantasy16.py --preview out.png   # лист набора в 4 раза крупнее
    python3 tools/fantasy16.py --preview out.png --scale=6 --keys=hero_run,hero_idle
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pixel_sprites16 as base  # noqa: E402
from pixel_sprites import png_bytes  # noqa: E402

# Палитра «Фэнтези»: 16 цветов, индекс это та же роль, что у пиратов, космоса и замков.
K, NAVY, SEA, AQUA, SKY, WHITE, GREY, SKIN, TAN, GOLD, BRASS, METAL, DARK, RED, VIOLET, PLUM = range(16)
PALETTE = [
    (0x14, 0x0E, 0x28),  # K      обводка
    (0x2A, 0x2C, 0x78),  # NAVY   глубокий индиго, тень мантии, поля шляпы
    (0x3E, 0x5C, 0xD0),  # SEA    синяя мантия
    (0x4C, 0xF0, 0xD2),  # AQUA   бирюза магии, кристалл, огоньки
    (0xD2, 0xC6, 0xF4),  # SKY    светлая лаванда, дымка, блик
    (0xF6, 0xF2, 0xFF),  # WHITE  почти белый блик, зубы
    (0x9C, 0x90, 0xC4),  # GREY   лавандово-серый, рунный камень
    (0xF6, 0xCE, 0xA6),  # SKIN   кожа
    (0x9C, 0x62, 0x42),  # TAN    корни, дерево посоха и дубинки
    (0xFC, 0xD8, 0x5A),  # GOLD   золото каймы, рун, звезды
    (0xC8, 0x8C, 0x2C),  # BRASS  тень золота
    (0x64, 0xB0, 0x48),  # METAL  мох, кожа гоблина, стебли
    (0x3A, 0x24, 0x44),  # DARK   тёмная земля, подошвы
    (0xE8, 0x50, 0x44),  # RED    огонь, сердце, язык мимика
    (0x9A, 0x6C, 0xD8),  # VIOLET сиреневая листва, знамя
    (0x5A, 0x32, 0x8C),  # PLUM   тень сирени, ночное небо
]
SHADOW = {SEA: NAVY, AQUA: SEA, SKY: GREY, WHITE: GREY, GREY: VIOLET, SKIN: TAN, TAN: DARK, GOLD: BRASS,
          BRASS: TAN, METAL: DARK, RED: PLUM, VIOLET: PLUM}
# Материалы для светотени рампами: ткань, магия, свет и камень, кожа, дерево, золото, мох, земля,
# огонь, сирень.
GROUPS = {NAVY: "cloth", SEA: "cloth", AQUA: "magic", SKY: "light", WHITE: "light", GREY: "light",
          SKIN: "skin", TAN: "wood", GOLD: "gold", BRASS: "gold", METAL: "moss", DARK: "earth", RED: "fire",
          VIOLET: "lilac", PLUM: "lilac"}


class Canvas(base.Canvas):
    shadow = SHADOW


def strip(frames):
    out = Canvas(sum(f.w for f in frames), max(f.h for f in frames))
    x = 0
    for f in frames:
        out.paste(f, x, 0)
        x += f.w
    return out


def _box(c, xa, ya, xb, yb, col):
    """Прямоугольник с любым порядком углов (нужен для зеркала по `face`)."""
    c.rect(min(xa, xb), min(ya, yb), max(xa, xb), max(ya, yb), col)


# --- Маг ---------------------------------------------------------------------------------------
# Силуэт: остроконечная шляпа с кончиком, загнутым назад и вниз, широкие поля, колокол мантии
# от плеч до щиколоток с золотой каймой по подолу и переду, поясок, носки туфель с загнутым
# носом. В ближней руке короткий посох с бирюзовым кристаллом. Позы и опора ног как у рыцаря.

def _crystal(c, x, y, big=False):
    """Кристалл посоха: ромб с белой гранью; `big` на пике свечения выше на пиксель."""
    r = 4 if big else 3
    c.poly([(x, y - r - 1), (x + 2, y), (x, y + r), (x - 2, y)], AQUA)
    c.set(x, y - 1, WHITE)
    c.set(x - 1, y, SKY)


def _staff(c, x0, y0, x1, y1, big=False):
    """Посох от нижнего конца (x0, y0) к верху (x1, y1), кристалл на верху, золотой наконечник."""
    c.line(x0, y0, x1, y1, TAN, 1)
    c.set(x0, y0, BRASS)
    c.set(x0 + (x1 - x0) * 0.15, y0 + (y1 - y0) * 0.15, BRASS)
    _crystal(c, x1, y1 - 2, big)


def _hat(c, x, y, face=1, h=8, bend=1.0):
    """Шляпа над головой с центром (x, y): поля на строке y-3, конус высотой `h`, кончик загнут
    назад и вниз, золотая лента над полями. `bend` длина загиба."""
    f = face
    y0 = y - 3
    # Конус и загнутый кончик.
    tip_y = y0 - h + 3
    c.poly([(x - 4 * f, y0), (x + 4 * f, y0), (x + 1 * f, tip_y + 2), (x + 0.5 * f, tip_y),
            (x - 1.5 * f, tip_y), (x - 2 * f, tip_y + 2)], SEA)
    k = bend
    c.poly([(x + 0.5 * f, tip_y + 2), (x + 0.5 * f, tip_y), (x - 3 * f * k, tip_y - 1.5), (x - 6.5 * f * k, tip_y),
            (x - 8 * f * k, tip_y + 4), (x - 6 * f * k, tip_y + 2.5), (x - 3 * f * k, tip_y + 1.5),
            (x - 1.5 * f, tip_y + 3)], SEA)
    c.set(x - 8 * f * k, tip_y + 4, GOLD)
    # Поля: широкий овал, верхняя кромка светлее.
    c.ellipse(x - 0.5 * f, y0 + 0.6, 8.6, 1.9, NAVY)
    c.ellipse(x - 0.5 * f, y0 + 0.1, 7.6, 1.0, SEA)
    # Лента и пряжка.
    _box(c, x - 3 * f, y0 - 2, x + 3 * f, y0 - 1, GOLD)
    c.set(x + 3 * f, y0 - 2, BRASS)
    c.set(x + 3 * f, y0 - 1, BRASS)


def _head(c, x, y, face=1, h=8, bend=1.0):
    """Голова лицом вправо при `face` 1: короткие каштановые волосы, открытое лицо, шляпа.
    Центр лица (x, y), низ подбородка y+4."""
    f = face
    c.ellipse(x - 2.5 * f, y + 0.5, 2.6, 3.4, TAN)
    c.ellipse(x + 0.5 * f, y + 1, 3.6, 3.3, SKIN)
    c.set(x + 4 * f, y + 2, SKIN)
    c.set(x + 2 * f, y + 1, K)
    c.set(x + 2 * f, y + 2, K)
    c.set(x + 3 * f, y + 3, TAN)
    _hat(c, x, y, face, h, bend)


def _sleeve(c, x0, y0, x1, y1, col):
    """Широкий рукав и рука: ткань до кисти, золотая манжета, кисть."""
    c.line(x0, y0, x1, y1, col, 3)
    n = max(1.0, math.hypot(x1 - x0, y1 - y0))
    ux, uy = (x1 - x0) / n, (y1 - y0) / n
    c.ellipse(x1, y1, 1.9, 1.9, GOLD)
    c.ellipse(x1 + ux * 1.6, y1 + uy * 1.6, 1.5, 1.5, SKIN)


def _shoe(c, x, y, face=1):
    """Туфля с загнутым носом, подошва на строке y+1."""
    f = face
    _box(c, x - 2 * f, y, x + 2 * f, y, TAN)
    _box(c, x - 2 * f, y + 1, x + 3 * f, y + 1, DARK)
    c.set(x + 3 * f, y, TAN)
    c.set(x + 4 * f, y - 1, GOLD)


def _robe(c, x, top, hem, wt=8, wh=15, sway=0.0, back=1.5, face=1, belt=True):
    """Колокол мантии: плечи на строке `top` шириной `wt`, подол на строке `hem` шириной `wh`,
    подол уезжает на `sway`, тыльный край отстаёт на `back`. Золотая кайма по подолу, по переду
    и поясок с кисточкой."""
    f = face
    c.poly([(x - wt / 2.0, top), (x + wt / 2.0, top), (x + wh / 2.0 + sway, hem), (x - wh / 2.0 + sway - back, hem)], SEA)
    # Тёмная складка со стороны спины.
    c.poly([(x - wt / 2.0, top + 1), (x - wt / 2.0 + 2, top + 1), (x - wh / 2.0 + sway + 2, hem),
            (x - wh / 2.0 + sway - back, hem)], NAVY)
    # Кайма: подол двумя строками, перед полосой.
    c.line(x - wh / 2.0 + sway - back, hem, x + wh / 2.0 + sway, hem, GOLD, 2)
    c.line(x + wt / 2.0 - 0.5, top + 1, x + wh / 2.0 + sway - 0.5, hem - 1, GOLD, 1)
    c.set(x + wt / 2.0 - 0.5, top, GOLD)
    if belt:
        by = top + 5
        c.line(x - wt / 2.0 - 0.5, by, x + wt / 2.0 + 1.0, by, BRASS, 1)
        c.set(x + 1, by, GOLD)
        c.line(x + 1, by + 1, x + 0, by + 3, GOLD, 1)


def mage_side(phase, jump=False):
    """Маг сбоку, лицом вправо: бег по фазе 0..2π или прыжок. Ноги и туфли под подолом на тех
    же местах, что сапоги рыцаря."""
    c = Canvas()
    bob = 0 if jump else int(round(abs(math.sin(phase)) * 1.4))
    swing = 0.9 if jump else math.sin(phase)
    top = 15 - bob
    hem = 26 - (1 if bob else 0) - (1 if jump else 0)
    # Дальняя рука и ноги.
    _sleeve(c, 14, top, 14 + 4 * swing, 20 - bob - (3 if jump else 0), NAVY)
    for sign in (-1, 1):
        lift = max(0.0, math.cos(phase) * sign) * 3.0 if not jump else (4 if sign > 0 else 1)
        fx, fy = 15 + 5 * swing * sign, 29 - lift
        c.line(15 + sign, hem - 1, fx, fy, DARK, 2)
        _shoe(c, fx, fy)
    _robe(c, 15.5, top, hem, 8, 15, sway=-swing * 1.2 - 1.0, back=1.5 + (1 if jump else 0))
    # Ближняя рука держит посох перед собой, посох качается с шагом.
    hx, hy = 21 + 1.5 * swing, 19 - bob - (3 if jump else 0)
    _staff(c, hx - 1, hy + 9, hx + 1, hy - 5, big=bool(jump))
    _sleeve(c, 17, top, hx, hy, SEA)
    _head(c, 16, 12 - bob)
    return c.finish()


def mage_back(phase):
    """Со спины: бежит вглубь экрана, шляпа с кончиком, падающим на плечо, звезда на спине, посох
    в правой руке."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.4))
    top = 15 - bob
    for sign in (-1, 1):
        lift = max(0.0, s * sign) * 4.0
        x = 16 + sign * 3
        c.line(x, 24 - bob, x, 28 - lift, DARK, 2)
        _shoe(c, x, 28 - lift)
    _sleeve(c, 11, top, 10, 20 - bob + s * 2, NAVY)
    # Мантия: сплошной колокол, золотой шов по спине и звезда.
    c.poly([(11, top), (21, top), (24, 26 - bob // 2), (8, 26 - bob // 2)], SEA)
    c.poly([(11, top + 1), (13, top + 1), (10, 26 - bob // 2), (8, 26 - bob // 2)], NAVY)
    c.line(8, 26 - bob // 2, 24, 26 - bob // 2, GOLD, 2)
    c.line(16, top + 3, 16, 25 - bob // 2, GOLD, 1)
    c.line(11, top + 5, 21, top + 5, BRASS, 1)
    c.poly([(16, top + 6), (17, top + 8), (19, top + 8.5), (17, top + 10), (17.5, top + 12), (16, top + 10.5),
            (14.5, top + 12), (15, top + 10), (13, top + 8.5), (15, top + 8)], GOLD)
    c.line(21, top + 1, 24, 14 - bob + 5, SEA, 1)
    # Посох справа, кристалл над плечом.
    hx = 25
    _staff(c, hx, 28 - bob, hx, 13 - bob + 1, big=False)
    _sleeve(c, 21, top, hx - 1, 21 - bob - s * 2, SEA)
    # Затылок и шляпа: волосы под полями, конус, кончик падает на правое плечо.
    c.ellipse(16, 11 - bob, 4, 3.4, TAN)
    c.poly([(11.5, 9 - bob), (20.5, 9 - bob), (17, 4 - bob), (16.5, 3 - bob), (15, 3 - bob), (14.5, 4 - bob)], SEA)
    c.poly([(15.5, 4 - bob), (16.5, 2.5 - bob), (19, 1.5 - bob), (21.5, 3.5 - bob), (22.5, 7 - bob),
            (20.5, 5 - bob), (18, 4.5 - bob), (17, 5.5 - bob)], SEA)
    c.set(22.5, 7.5 - bob, GOLD)
    c.ellipse(16, 9.6 - bob, 8.6, 1.9, NAVY)
    c.ellipse(16, 9.1 - bob, 7.6, 1.0, SEA)
    c.rect(12, 7 - bob, 20, 8 - bob, GOLD)
    return c.finish()


def mage_leap(i):
    """Прыжок через клетку, четыре кадра: присел, толчок вверх, поджал колени, приземление. Подол
    то тянется вниз, то взлетает колоколом."""
    c = Canvas()
    crouch = (3, 0, -1, 2)[i]
    top = 15 + crouch
    hem = (27, 27, 24, 27)[i]
    wide = (16, 12, 18, 16)[i]
    _sleeve(c, 14, top, 12 - i % 2, 11 + crouch if i in (1, 2) else 20 + crouch, NAVY)
    for sign in (-1, 1):
        fx = 15 + sign * (2, 3, 3, 3)[i] + (2 if i == 1 else 0)
        fy = 29 if i in (0, 3) else 27 - (2 if i == 2 else 0)
        c.line(15 + sign, hem - 1, fx, fy, DARK, 2)
        _shoe(c, fx, fy)
    _robe(c, 15.5, top, hem, 8, wide, sway=(-1, -2, 1, 0)[i], back=1.5)
    hx = 21 + i % 2
    hy = 10 + crouch if i in (1, 2) else 19 + crouch
    _staff(c, hx - 1, hy + 9, hx + 1, hy - 5, big=i in (1, 2))
    _sleeve(c, 17, top, hx, hy, SEA)
    _head(c, 16, 12 + crouch)
    return c.finish()


def mage_idle(i):
    """Стойка: два кадра, маг дышит, кристалл на втором ярче, кончик шляпы чуть качается."""
    c = Canvas()
    up = i
    top = 15 - up
    _sleeve(c, 14, top, 13, 21 - up, NAVY)
    for sign in (-1, 1):
        x = 15 + sign * 2
        c.line(x, 24, x, 28, DARK, 2)
        _shoe(c, x, 29)
    _robe(c, 15.5, top, 26, 8, 15, sway=-1.0, back=1.5)
    hx, hy = 21, 20 - up
    _staff(c, hx - 1, hy + 9, hx, hy - 5, big=bool(i))
    _sleeve(c, 17, top, hx, hy, SEA)
    _head(c, 16, 12 - up, bend=1.0 + 0.2 * i)
    return c.finish()


def _lean_robe(c, sx, sy, hx, hy, w, col=SEA):
    """Мантия под наклоном: от плеч (sx, sy) к подолу (hx, hy), ширина растёт к подолу; золотой
    подол в конце."""
    n = math.hypot(hx - sx, hy - sy)
    dx, dy = (hx - sx) / n, (hy - sy) / n
    for k in range(int(n) + 1):
        x, y = sx + dx * k, sy + dy * k
        ww = w * (0.7 + 0.5 * k / n)
        edge = GOLD if k >= int(n) - 1 else col
        c.line(x + dy * ww / 2, y - dx * ww / 2, x - dy * ww / 2, y + dx * ww / 2, edge, 2)


def mage_slide(i):
    """Подкат на боку ногами вперёд: корпус откинут, подол стелется вперёд, туфля с носком вверх,
    посох в руке торчит вперёд-вверх. Шляпа пригнута, макушка на 15-й строке. Два кадра: пыль."""
    c = Canvas()
    # Ноги и туфли вперёд, подол над ними.
    c.line(20, 27, 27, 27, DARK, 2)
    _shoe(c, 27, 27)
    _lean_robe(c, 12, 25, 24, 26 - i, 7)
    c.line(13, 28, 24, 28, NAVY, 2)
    c.line(20, 28, 25, 28, GOLD, 1)
    # Посох вперёд-вверх, рука с рукавом.
    _staff(c, 15, 26, 25, 15, big=bool(i))
    _sleeve(c, 12, 24, 17, 22, SEA)
    _head(c, 10, 21, h=3, bend=1.3)
    c.finish()
    for k, (x, y) in enumerate(((2, 30), (4, 31), (1, 28), (3, 29))):
        if (k + i) % 2 == 0:
            c.set(x, y, SKY)
    return c


def mage_crouch(i):
    """Присед: мантия складывается шатром, колени под ней, шляпа низко. Два кадра шага."""
    c = Canvas()
    step = (-1, 1)[i]
    for sign in (-1, 1):
        fx = 17 - sign * 2 + step * sign * 2
        _shoe(c, fx, 29)
    _robe(c, 15.5, 22, 28, 8, 16, sway=0.0, back=1.0, belt=False)
    c.line(11, 24, 21, 24, BRASS, 1)
    hx = 24
    _staff(c, hx, 28, hx + 1, 17, big=bool(i))
    _sleeve(c, 17, 23, hx, 25, SEA)
    _head(c, 16, 19, h=6)
    return c.finish()


def mage_hang(i):
    """На тросе: руки вверх к точке хвата, подол и туфли свисают и качаются, посох за поясом."""
    c = Canvas()
    sw = (-1, 1)[i]
    # Посох за поясом, кристалл торчит справа.
    c.line(11, 26, 23, 17, TAN, 1)
    _crystal(c, 24, 15)
    _sleeve(c, 13, 14, 12, 3, NAVY)
    _sleeve(c, 19, 14, 20, 3, SEA)
    for sign in (-1, 1):
        fx = 15.5 + sign * 2 + sw * 2
        c.line(15.5 + sign * 2, 25, fx, 28, DARK, 2)
        _shoe(c, fx, 29 - 1)
    _robe(c, 15.5, 14, 26, 8, 14, sway=sw * 1.5, back=1.0)
    _head(c, 16, 11, h=4, bend=1.2)
    return c.finish()


# --- Гоблин ------------------------------------------------------------------------------------
# Враг: приземистый зелёный гоблин с огромными острыми ушами, клыками, набедренной повязкой и
# дубинкой с шипами. Шаг и рост повторяют стражника из замков.

def _club(c, x0, y0, x1, y1):
    """Дубинка: ручка от кулака (x0, y0) вверх к утолщению (x1, y1) с шипами."""
    c.line(x0, y0, x1, y1 + 2, TAN, 2)
    c.ellipse(x1, y1, 3, 3.6, TAN)
    c.set(x1 - 3, y1 - 1, DARK)
    c.set(x1 + 3, y1 + 1, DARK)
    c.set(x1 - 1, y1 - 4, DARK)
    c.set(x1 + 1, y1 + 3, DARK)
    c.set(x1 - 1, y1, BRASS)
    c.set(x1 + 1, y1 + 1, BRASS)


def goblin_side(phase):
    """Гоблин сбоку, лицом влево (навстречу герою): шаг по фазе, дубинка поднята в ближней руке."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.2))
    # Тонкие ноги в шаге, ступни вперёд.
    for sign, col in ((-1, DARK), (1, METAL)):
        a = s * sign
        lift = max(0.0, math.cos(phase) * sign) * 2.5
        foot = (16 - 5 * a, 29 - lift)
        knee = ((16 + foot[0]) / 2 - 1.5, (23 - bob + foot[1]) / 2)
        c.line(16, 23 - bob, knee[0], knee[1], col, 3)
        c.line(knee[0], knee[1], foot[0], foot[1], col, 2)
        c.rect(foot[0] - 3, foot[1], foot[0], foot[1] + 1, METAL if col == METAL else DARK)
    # Согнутое туловище: живот и сутулая спина, набедренная повязка.
    c.ellipse(16.5, 19 - bob, 4.8, 5.2, METAL)
    c.ellipse(18.5, 15 - bob, 3.5, 3, METAL)
    c.poly([(12, 22 - bob), (21, 22 - bob), (20, 27 - bob), (16, 25 - bob), (13, 27 - bob)], TAN)
    c.rect(12, 22 - bob, 21, 22 - bob, BRASS)
    c.set(16, 26 - bob, DARK)
    # Голова с носом, клыки и огромное ухо назад-вверх.
    c.ellipse(13.5, 11 - bob, 4.8, 4.2, METAL)
    c.poly([(8, 11 - bob), (11, 9 - bob), (11, 13 - bob)], METAL)
    c.poly([(16, 8 - bob), (27, 3 - bob), (18, 13 - bob)], METAL)
    c.poly([(17, 9 - bob), (24, 5 - bob), (18, 12 - bob)], SKIN)
    c.rect(11, 14 - bob, 13, 14 - bob, DARK)
    # Рука с дубинкой.
    c.line(15, 15 - bob, 9, 17 - bob, METAL, 3)
    _club(c, 8, 17 - bob, 5, 8 - bob)
    c.finish()
    c.set(11, 10 - bob, GOLD)
    c.set(10, 10 - bob, K)
    c.set(9, 14 - bob, WHITE)
    c.set(11, 14 - bob, WHITE)
    return c


def goblin_front(phase):
    """Гоблин лицом к камере: идёт на игрока, уши в стороны, дубинка у правого плеча."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.2))
    c.line(11, 16 - bob, 8, 21 - bob + s * 2, METAL, 3)
    for sign in (-1, 1):
        lift = max(0.0, s * sign) * 3.0
        x = 16 + sign * 3
        c.line(x, 23 - bob, x, 28 - lift, METAL if sign > 0 else DARK, 3)
        c.rect(x - 2, 28 - lift, x + 1, 29 - lift, DARK)
    # Туловище и повязка.
    c.ellipse(15.5, 19 - bob, 6, 5.5, METAL)
    c.poly([(10, 22 - bob), (21, 22 - bob), (19, 27 - bob), (15.5, 25 - bob), (12, 27 - bob)], TAN)
    c.rect(10, 22 - bob, 21, 22 - bob, BRASS)
    # Голова и два больших острых уха.
    c.ellipse(15.5, 11 - bob, 5.4, 4.5, METAL)
    c.poly([(10.5, 9 - bob), (2, 3 - bob), (10.5, 14 - bob)], METAL)
    c.poly([(20.5, 9 - bob), (29, 3 - bob), (20.5, 14 - bob)], METAL)
    c.poly([(9.5, 9.5 - bob), (5, 6 - bob), (9.5, 12 - bob)], SKIN)
    c.poly([(21.5, 9.5 - bob), (26, 6 - bob), (21.5, 12 - bob)], SKIN)
    # Дубинка справа.
    c.line(19, 16 - bob, 24, 19 - bob, METAL, 3)
    _club(c, 24, 19 - bob, 26, 9 - bob)
    c.finish()
    for ex in (13, 18):
        c.set(ex, 10 - bob, GOLD)
        c.set(ex, 11 - bob, K)
    c.rect(13, 14 - bob, 18, 14 - bob, K)
    c.set(13, 13 - bob, WHITE)
    c.set(18, 13 - bob, WHITE)
    return c


# --- Вещи --------------------------------------------------------------------------------------

def coin(i):
    """Золотая монета с руной вращается: шесть кадров, ширина по косинусу, ребро темнее."""
    c = Canvas()
    rx = max(1.0, abs(math.cos(math.pi * i / 6.0)) * 7.0)
    cx = 15.5
    c.ellipse(cx, 16, rx, 10.5, BRASS)
    if rx > 2:
        c.ellipse(cx, 16, rx - 1.3, 9.2, GOLD)
    if rx > 3:
        k = rx / 7.0
        # Руна: вертикаль со стрелкой вверх и ломаным хвостом.
        c.line(cx, 10, cx, 22, BRASS, 1)
        c.line(cx, 11, cx + 3.5 * k, 14, BRASS, 1)
        c.line(cx, 15, cx - 3.5 * k, 18, BRASS, 1)
        c.line(cx, 18, cx + 3.5 * k, 21, BRASS, 1)
        c.set(cx, 9, WHITE)
        c.set(cx - rx * 0.6, 8, WHITE)
        c.set(cx - rx * 0.4, 7, WHITE)
        c.set(cx + rx * 0.6, 23, AQUA)
    return c.finish()


def _star(c, cx, cy, r, col):
    """Пятиконечная звезда с вершиной вверх."""
    pts = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5
        rr = r if k % 2 == 0 else r * 0.45
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    c.poly(pts, col)


def flag(i):
    """Знамя гильдии на древке с бирюзовым шаром: фиолетовое полотнище с ласточкиным хвостом и
    золотой звездой идёт волной."""
    c = Canvas()
    c.rect(5, 3, 6, 31, TAN)
    c.ellipse(5.5, 2, 2, 2, AQUA)
    c.set(5, 1, WHITE)
    top = []
    bottom = []
    for x in range(8, 29):
        w = math.sin(x * 0.45 - i * math.pi / 3.0) * 1.6 * (x - 8) / 20.0
        top.append((x, 5 + w))
        bottom.append((x, 19 + w))
    c.poly(top + bottom[::-1], VIOLET)
    # Вырез ласточкиным хвостом на свободном крае.
    for x in range(24, 29):
        w = math.sin(x * 0.45 - i * math.pi / 3.0) * 1.6 * (x - 8) / 20.0
        for y in range(int(round(12 + w - (x - 24))), int(round(12 + w + (x - 24))) + 1):
            if 0 <= y < c.h:
                c.px[y][x] = None
    c.shade()
    c.outline()
    mid = math.sin(15 * 0.45 - i * math.pi / 3.0) * 0.8
    # Золотая кайма сверху и звезда гильдии.
    c.rect(8, 6 + mid * 0.2, 22, 6 + mid * 0.2, GOLD)
    _star(c, 14.5, 12.5 + mid, 5, GOLD)
    c.set(14, 12 + mid, WHITE)
    return c


def heart():
    """Жизнь в HUD."""
    c = Canvas()
    c.ellipse(11, 12, 5.5, 5.5, RED)
    c.ellipse(20, 12, 5.5, 5.5, RED)
    c.poly([(5, 14), (26, 14), (15.5, 26)], RED)
    c.rect(9, 9, 10, 10, WHITE)
    c.set(23, 8, GOLD)
    return c.finish()


def _roots(c, y0, amp, ks=(1, 2, 3), cols=(TAN, TAN, BRASS)):
    """Переплетённые корни: синусоиды, период делит 32, плитка стыкуется по краям."""
    for n, k in enumerate(ks):
        for x in range(32):
            y = y0 + n * 5 + amp * math.sin(2 * math.pi * (x * k) / 32.0 + n * 1.7)
            c.set(x, y, cols[n])
            c.set(x, y + 1, cols[n] if n < 2 else TAN)


def ground(inner=False):
    """Тёмная земля, переплетённые корни; сверху бархатный мох с бирюзовыми огоньками."""
    c = Canvas()
    c.rect(0, 0, 31, 31, DARK)
    for x, y in ((3, 9), (11, 14), (19, 11), (27, 16), (7, 25), (22, 28), (14, 20), (29, 6), (2, 18), (17, 4)):
        c.set(x, y, PLUM)
    _roots(c, 9 if not inner else 5, 2.2)
    _roots(c, 25 if not inner else 21, 1.5, ks=(2,), cols=(TAN,))
    if inner:
        _roots(c, 29, 1.0, ks=(3,), cols=(BRASS,))
    if not inner:
        c.rect(0, 0, 31, 4, METAL)
        # Неровный подбой мха и свисающие нити.
        for x in range(32):
            c.set(x, 5, METAL if (x * 5 + 3) % 7 < 4 else DARK)
            if (x * 3) % 11 == 0:
                c.set(x, 6, METAL)
        # Бирюзовые огоньки и светлые ворсинки.
        for x in range(32):
            if x % 4 == 1:
                c.set(x, 0, SKY if x % 8 == 1 else AQUA)
        for x, y in ((6, 2), (15, 3), (24, 2), (28, 3), (10, 3)):
            c.set(x, y, DARK)
    return c


def rock():
    """Рунный камень: глыба лавандово-серого цвета с трещиной, светящимся бирюзовым знаком и
    мохом у подножия."""
    c = Canvas()
    c.poly([(4, 28), (3, 17), (8, 8), (17, 4), (25, 8), (30, 18), (28, 28)], GREY)
    c.poly([(8, 13), (13, 8), (20, 8), (16, 13)], SKY)
    c.line(23, 18, 26, 25, VIOLET, 1)
    c.line(9, 22, 12, 27, VIOLET, 1)
    # Светящаяся руна: стержень и два зуба, белая сердцевина, бирюзовое мерцание рядом.
    c.line(16, 12, 16, 24, AQUA, 2)
    c.line(16, 14, 21, 11, AQUA, 1)
    c.line(16, 19, 11, 16, AQUA, 1)
    c.line(16, 22, 20, 25, AQUA, 1)
    c.rect(16, 14, 16, 22, WHITE)
    c.set(21, 11, WHITE)
    c.set(11, 16, WHITE)
    # Мох на макушке и внизу.
    c.poly([(5, 26), (8, 24), (11, 28), (5, 28)], METAL)
    c.poly([(24, 27), (27, 24), (29, 27)], METAL)
    c.set(17, 5, METAL)
    c.set(19, 6, METAL)
    return c.finish()


def chest():
    """Сундук-мимик: деревянный короб с золотыми полосами, крышка приоткрыта, из пасти торчат
    зубы и красный язык, на крышке жёлтый глаз."""
    c = Canvas()
    c.rect(4, 17, 27, 28, TAN)
    # Пасть: тёмная щель, язык, нижние зубы.
    c.rect(4, 17, 27, 21, PLUM)
    c.poly([(11, 21), (20, 21), (19, 18), (13, 17)], RED)
    c.poly([(4, 17), (6, 13), (25, 13), (27, 17)], TAN)
    # Крышка с выпуклым верхом.
    c.ellipse(15.5, 11, 12, 5.5, TAN)
    c.rect(4, 13, 27, 14, TAN)
    for x in (8, 23):
        c.rect(x, 7, x + 1, 28, BRASS)
    c.rect(4, 27, 27, 28, BRASS)
    c.rect(4, 22, 27, 22, BRASS)
    # Зубы: верхние свисают с крышки, нижние растут из короба.
    for x in range(5, 27, 3):
        c.poly([(x, 14), (x + 2, 14), (x + 1, 18)], WHITE)
        c.poly([(x + 1, 22), (x + 3, 22), (x + 2, 19)], WHITE)
    # Глаз-блик на крышке.
    c.ellipse(15.5, 9, 2.4, 1.8, GOLD)
    c.finish()
    c.set(15, 9, K)
    c.set(16, 9, K)
    c.set(14, 8, WHITE)
    return c


# --- Параллакс ---------------------------------------------------------------------------------
# Три слоя дали. par_sky прозрачный (сиреневую заливку и сумерки кладёт окружение сеттинга), как
# у космоса и пиратов; par_far и par_mid с плотным низом. Высоты периодические (256 делится на
# период синусов), ленты стыкуются по краям.

def _wrap(c, fn, cx, *args):
    """Рисует `fn(c, x, *args)` в трёх копиях со сдвигом на ширину ленты, края стыкуются."""
    for k in (0, 256, -256):
        fn(c, cx + k, *args)


def _island(c, x, y, w, col_top, col_body, col_bot, tuft=True):
    """Летающий остров с центром (x, y): плоская зелёная шапка и каменное брюхо-конус вниз."""
    c.ellipse(x, y, w, 2.2, col_top)
    c.poly([(x - w + 1, y + 1), (x + w - 1, y + 1), (x + w * 0.45, y + w * 0.9), (x, y + w * 1.25),
            (x - w * 0.5, y + w * 0.8)], col_body)
    c.poly([(x + 1, y + 2), (x + w - 2, y + 2), (x + w * 0.45, y + w * 0.9), (x + 1, y + w * 1.1)], col_bot)
    if tuft:
        c.line(x - w * 0.3, y - 2, x - w * 0.3, y - 4, col_top, 1)
        c.line(x + w * 0.4, y - 2, x + w * 0.4 - 1, y - 4, col_top, 1)


def par_sky():
    """Дальний слой: лиловые облака и летающие острова далеко в дымке, звёзды, лента 256×48,
    стыкуется по краям; заливки неба нет."""
    import random
    c = Canvas(256, 48)
    # Облака полосами.
    for cx, cy, r in ((20, 34, 16), (66, 38, 20), (130, 36, 14), (182, 40, 18), (236, 33, 14)):
        _wrap(c, lambda cc, x, y, rr: (cc.ellipse(x, y, rr, rr * 0.28, VIOLET),
                                       cc.ellipse(x - rr * 0.3, y + 1, rr * 0.7, rr * 0.18, SKY)), cx, cy, r)
    # Далёкие острова: бледные силуэты, три размера.
    for cx, cy, w in ((38, 14, 9), (112, 9, 6), (150, 20, 10), (212, 12, 7)):
        _wrap(c, _island, cx, cy, w, GREY, GREY, VIOLET, False)
    # Звёзды и бирюзовые искры.
    rng = random.Random(7)
    for _ in range(30):
        c.set(rng.randint(0, 255), rng.randint(0, 22), WHITE if rng.random() < 0.6 else SKY)
    for _ in range(9):
        c.set(rng.randint(0, 255), rng.randint(2, 40), AQUA)
    return c


def _fall(c, x, y0, y1, col=AQUA, hi=WHITE):
    """Водопад: столб воды с белой пеной и брызгами внизу."""
    c.rect(x, y0, x + 1, y1, col)
    for y in range(int(y0), int(y1), 4):
        c.set(x, y, hi)
    c.rect(x - 2, y1, x + 3, y1, hi)
    c.set(x - 3, y1 - 1, hi)
    c.set(x + 4, y1 - 1, hi)


def par_far():
    """Средний слой: сиреневые холмы с Великим деревом на горизонте и летающими островами с
    водопадами, лента 256×48, низ сплошной."""
    c = Canvas(256, 48)

    def height(x):
        h = 8 + 5 * max(0.0, math.sin(x * math.pi / 64.0)) ** 2 + 2.5 * math.sin(x * math.pi / 16.0 + 1.0)
        return h + 5 * max(0.0, math.sin((x - 40) * math.pi / 128.0)) ** 4

    # Острова с водопадами: они над холмами, поток стекает до земли.
    for cx, cy, w in ((44, 11, 10), (100, 18, 7), (222, 9, 11)):
        _wrap(c, _island, cx, cy, w, METAL, VIOLET, PLUM)
        _wrap(c, lambda cc, x, y, yy: _fall(cc, x, y, yy), cx - w // 3, cy + w + 2, 47 - int(height(cx)) - 1)
    # Холмы: тёмная сирень, мох сверху, ниже сливовая толща.
    for x in range(256):
        top = 47 - int(height(x))
        c.rect(x, top, x, 47, VIOLET)
        c.rect(x, top, x, top + 1, METAL)
        c.rect(x, top + 8, x, 47, PLUM)
    # Великое дерево: толстый ствол с корневыми лапами, раскидистая крона на двух ярусах.
    gx = 170
    by = 47 - int(height(gx)) + 2
    c.poly([(gx - 9, by), (gx - 4, by - 6), (gx - 3, by - 20), (gx + 3, by - 20), (gx + 4, by - 6), (gx + 10, by)], DARK)
    c.line(gx, by - 19, gx - 10, by - 23, DARK, 3)
    c.line(gx, by - 19, gx + 10, by - 23, DARK, 3)
    c.line(gx - 2, by - 6, gx - 2, by - 18, TAN, 1)
    for ex, ey, rx, ry, col in ((gx, by - 27, 21, 8, PLUM), (gx - 13, by - 23, 10, 6, PLUM), (gx + 13, by - 23, 10, 6, PLUM),
                                (gx, by - 30, 18, 7, VIOLET), (gx - 10, by - 26, 8, 4.5, VIOLET), (gx + 11, by - 26, 8, 4.5, VIOLET)):
        c.ellipse(ex, ey, rx, ry, col)
    for ex, ey in ((gx - 8, by - 33), (gx + 3, by - 35), (gx + 12, by - 31), (gx - 15, by - 27), (gx - 2, by - 29)):
        c.ellipse(ex, ey, 3, 1.4, SKY)
    for dx, dy in ((-6, -26), (5, -28), (14, -25), (-14, -24), (1, -33), (9, -30)):
        c.set(gx + dx, by + dy, AQUA)
    # Свисающие светящиеся лианы.
    for dx in (-18, -10, 8, 16):
        c.line(gx + dx, by - 22, gx + dx, by - 16 + abs(dx) // 4, METAL, 1)
        c.set(gx + dx, by - 15 + abs(dx) // 4, AQUA)
    # Маленькие деревья по склонам.
    for px in (12, 28, 76, 124, 140, 210, 244):
        b = 47 - int(height(px)) + 2
        c.rect(px, b - 5, px, b, DARK)
        c.ellipse(px, b - 8, 4, 3.4, PLUM)
        c.ellipse(px - 1, b - 9, 2, 1.5, SKY)
    return c


def _flower(c, x, base, h, petal, core):
    """Гигантский цветок: стебель с листом и пятью лепестками вокруг сердцевины."""
    c.line(x, base, x, base - h, METAL, 2)
    c.poly([(x, base - h // 3), (x + 6, base - h // 3 - 3), (x + 1, base - h // 3 + 2)], METAL)
    top = base - h
    for dx, dy in ((-6, 1), (6, 1), (-4, -4), (4, -4), (0, -6)):
        c.ellipse(x + dx, top + dy, 3.6, 3.0, petal)
    c.ellipse(x, top - 1, 3.0, 3.0, core)
    c.set(x - 1, top - 1, WHITE)
    c.set(x, top + 1, BRASS)


def _lilac_tree(c, x, base, r):
    """Дерево с сиреневой кроной: ствол и круглая крона из бугров, светлый блик и бирюзовая искра."""
    c.rect(x - 1, base - r, x + 1, base, DARK)
    c.ellipse(x - r * 0.6, base - r * 1.3, r * 0.7, r * 0.6, PLUM)
    c.ellipse(x + r * 0.6, base - r * 1.3, r * 0.7, r * 0.6, PLUM)
    c.ellipse(x, base - r * 1.6, r * 0.95, r * 0.8, VIOLET)
    c.ellipse(x - r * 0.3, base - r * 1.95, r * 0.45, r * 0.3, SKY)
    c.set(x + r * 0.4, base - r * 1.5, AQUA)


def par_mid():
    """Ближний слой: бугры мха с деревьями в сиреневой листве и гигантскими цветами, лента 256×32."""
    c = Canvas(256, 32)

    def crest(x):
        return 14 + 3 * math.sin(x * math.pi / 32.0) + 1.5 * math.sin(x * math.pi / 8.0)

    for x in range(256):
        top = int(round(crest(x)))
        c.rect(x, top, x, 31, DARK)
        c.rect(x, top, x, top + 1, METAL)
        c.rect(x, top + 6, x, 31, PLUM)
        if (x * 7 + top * 3) % 23 == 0:
            c.rect(x, top + 3 + (x % 4), x + 1, top + 3 + (x % 4), AQUA)
    for px, kind in ((10, 0), (46, 1), (88, 0), (122, 1), (160, 0), (200, 1), (236, 0)):
        by = int(round(crest(px))) + 2
        if kind == 0:
            _lilac_tree(c, px, by, 6)
        else:
            _flower(c, px, by, 10, RED if px % 3 == 0 else GOLD, AQUA if px % 3 == 0 else RED)
    return c


def sprites():
    """Ленты основы набора в палитре `PALETTE`: герой платформера, гоблин, вещи, земля, три слоя
    дали. Ключи, размеры и число кадров те же, что у `castles16.sprites()`. Ленты демок лежат в
    модулях `fantasy_*16.py`."""
    return {
        "enemy_walk": strip([goblin_side(p) for p in base.phases()]),
        "enemy_front": strip([goblin_front(p) for p in base.phases()]),
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
        "hero_run": strip([mage_side(p) for p in base.phases()]),
        "hero_jump": mage_side(0.0, jump=True),
        "hero_leap": strip([mage_leap(i) for i in range(4)]),
        "hero_idle": strip([mage_idle(i) for i in range(2)]),
        "hero_back": strip([mage_back(p) for p in base.phases()]),
        "hero_slide": strip([mage_slide(i) for i in range(2)]),
        "hero_hang": strip([mage_hang(i) for i in range(2)]),
        "hero_crouch": strip([mage_crouch(i) for i in range(2)]),
    }


# --- Остальные слоты (ленты демок «тропа» и «до выхода» их берут) ------------------------------

def wisp(i):
    """Блуждающий огонёк (слот попугая) летит вправо: четыре кадра, огненный хвост плещет,
    бирюзовое тело с белой сердцевиной и двумя глазами. Без красной обводки опасности: её кладёт
    модуль демки."""
    c = Canvas()
    fl = (0, 2, 4, 2)[i]
    # Хвост из языков пламени назад, длина и изгиб по кадру.
    c.poly([(17, 13), (17, 21), (9 - fl, 17 + (1, -1, 1, -1)[i] * 2)], AQUA)
    c.poly([(16, 14), (16, 20), (4 - fl, 15 + i % 2 * 4)], SEA)
    c.poly([(16, 12), (14, 8 - fl // 2), (19, 13)], AQUA)
    c.poly([(18, 21), (15, 25 + fl // 2), (20, 20)], AQUA)
    # Голова: шар с ярким ядром.
    c.ellipse(21.5, 16.5, 6, 5.6, AQUA)
    c.ellipse(21.5, 16.5, 3.6, 3.2, SKY)
    c.set(25, 13, GOLD)
    c.set(8 - fl, 10 + i, GOLD)
    c.set(12, 25 - i, GOLD)
    c.finish()
    # Глаза: тёмные вертикальные овалы с белым бликом.
    for ex in (21, 25):
        c.set(ex, 15, K)
        c.set(ex, 16, K)
        c.set(ex, 17, K)
    c.set(21, 14, WHITE)
    c.set(25, 14, WHITE)
    return c


def slime(i):
    """Слизь (слот краба-ползуна) ползёт вправо: четыре кадра, студень то приседает, то
    вытягивается, внутри пузыри, два глаза."""
    c = Canvas()
    sq = (0, 1.5, 0, -1.5)[i]
    h = 8.0 - sq
    w = 12.0 + sq * 1.2
    cy = 29 - h
    c.ellipse(15.5, cy + 1, w, h, VIOLET)
    c.rect(15.5 - w, cy + 2, 15.5 + w, 29, VIOLET)
    # Капля-хохолок и лужица следом.
    c.poly([(11, cy - h + 3), (13, cy - h - 3 - (i % 2)), (15, cy - h + 2)], VIOLET)
    c.rect(2, 28, 8, 29, PLUM)
    # Блик, пузыри.
    c.ellipse(11, cy - 2, 3, 1.6, SKY)
    c.set(18, cy + 3, PLUM)
    c.set(22, cy + 1, PLUM)
    c.set(13, cy + 5, PLUM)
    c.ellipse(19, 26, 2, 1.2, PLUM)
    c.finish()
    # Глаза и рот.
    for ex in (17, 23):
        c.set(ex, cy, WHITE)
        c.set(ex + 1, cy, WHITE)
        c.set(ex + 1, cy + 1, K)
        c.set(ex, cy + 1, WHITE)
    c.rect(19, cy + 5, 22, cy + 5, K)
    return c


def key():
    """Золотой ключ с бирюзовым камнем в головке и резной бородкой."""
    c = Canvas(32, 32)
    c.ellipse(10, 16, 7, 7, GOLD)
    c.ellipse(10, 16, 3, 3, None)
    c.rect(16, 14, 29, 17, GOLD)
    c.rect(24, 18, 25, 22, GOLD)
    c.rect(28, 18, 29, 21, GOLD)
    c.rect(16, 14, 29, 14, WHITE)
    c.set(10, 10, AQUA)
    c.set(10, 9, WHITE)
    c.set(5, 16, AQUA)
    c.set(15, 16, BRASS)
    return c.finish()


def potion():
    """Зелье (аптечка): круглая колба с красным настоем, пробка, золотая шейка, четырёхлучевая
    искорка."""
    c = Canvas(32, 32)
    c.ellipse(15.5, 20, 9, 8, SKY)
    c.rect(12, 7, 19, 14, SKY)
    c.rect(12, 5, 19, 7, TAN)
    c.rect(12, 12, 19, 12, GOLD)
    c.ellipse(15.5, 21.5, 7.5, 5.5, RED)
    c.rect(15, 15, 16, 24, WHITE)
    c.rect(12, 19, 19, 20, WHITE)
    c.set(15, 19, GOLD)
    c.set(16, 20, GOLD)
    c.set(11, 17, WHITE)
    c.set(10, 19, WHITE)
    c.set(23, 10, AQUA)
    c.set(23, 9, WHITE)
    return c.finish()


def fireball():
    """Огненный шар летит вправо: ядро, красный язык хвоста, золотые искры. 16×16."""
    c = Canvas(16, 16)
    c.poly([(9, 5), (9, 11), (0, 8)], RED)
    c.poly([(9, 6), (9, 10), (3, 8)], GOLD)
    c.ellipse(11, 8, 4, 4, RED)
    c.ellipse(11.5, 8, 2.6, 2.6, GOLD)
    c.set(12, 7, WHITE)
    c.set(2, 5, GOLD)
    c.set(4, 12, GOLD)
    return c.finish()


def extras():
    """Слоты фэнтези вне `sprites()`: ленты и вещи тех же размеров, что у космоса, пиратов и
    замков."""
    return {
        "parrot_fly": strip([wisp(i) for i in range(4)]),
        "crab_walk": strip([slime(i) for i in range(4)]),
        "key": key(),
        "medkit": potion(),
        "shot": fireball(),
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


def preview(path, scale=4, keys=None, back=(0x6A, 0x58, 0x9C, 255)):
    """Лист набора: лента на строку после светотени, затем `extras()`. Фон сиреневый, как небо
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
