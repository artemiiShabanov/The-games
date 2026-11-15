#!/usr/bin/env python3
"""Набор «Космос» для 16/32-bit (#136, состав в `docs/specs/settings.md`): ретро-фантастика,
космонавт в белом скафандре с бирюзовым визором, фиолетовые пришельцы. Те же ленты и кадры, что
у пиратов (`pixel_sprites16.py` и модули демок), позы повторяют матроса, чтобы хитбоксы демок
сходились. Пишется вместе с пиратами: `python3 tools/pixel_sprites16.py`.

    python3 tools/space16.py --preview out.png   # лист набора в 4 раза крупнее
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pixel_sprites16 as base  # noqa: E402
from pixel_sprites import png_bytes  # noqa: E402

# Палитра «Космос»: 16 цветов, индекс это та же роль, что у пиратов (ими рисуют HUD и мир демки).
K, NAVY, SEA, AQUA, SKY, WHITE, GREY, SKIN, TAN, GOLD, BRASS, METAL, DARK, RED, VIOLET, PLUM = range(16)
PALETTE = [
    (0x12, 0x10, 0x18),  # K      обводка
    (0x17, 0x16, 0x3C),  # NAVY   глубокий космос, тень синего
    (0x45, 0x4A, 0xB8),  # SEA    сине-фиолетовый: даль, тень энергии
    (0x4F, 0xC3, 0xD9),  # AQUA   визор, энергия
    (0xC2, 0xEE, 0xF4),  # SKY    блик визора, свечение
    (0xEE, 0xF1, 0xF6),  # WHITE  скафандр
    (0xB3, 0xBA, 0xCB),  # GREY   тень скафандра, реголит
    (0xF2, 0xC8, 0x9A),  # SKIN   кожа
    (0xC9, 0x8F, 0x5E),  # TAN    тень кожи
    (0xF4, 0xD3, 0x5E),  # GOLD   кристалл, бонус
    (0xC0, 0x8A, 0x2A),  # BRASS  тень золота
    (0x74, 0x7D, 0x92),  # METAL  металл: ранец, перчатки, настил
    (0x3A, 0x40, 0x54),  # DARK   тёмный металл, подошвы
    (0xF0, 0x6A, 0x3A),  # RED    оранжевые нашивки, опасность
    (0x9A, 0x5F, 0xE0),  # VIOLET пришельцы, мох
    (0x55, 0x2F, 0x98),  # PLUM   тень фиолетового
]
SHADOW = {SEA: NAVY, AQUA: SEA, SKY: AQUA, WHITE: GREY, GREY: METAL, SKIN: TAN, TAN: DARK, GOLD: BRASS,
          BRASS: DARK, METAL: DARK, RED: DARK, VIOLET: PLUM}
# Материалы для светотени рампами: скафандр одна ткань, визор стекло, металл, нашивки, пришельцы.
GROUPS = {WHITE: "suit", GREY: "suit", AQUA: "glass", SKY: "glass", SEA: "glass", NAVY: "glass",
          SKIN: "skin", TAN: "skin", GOLD: "gold", BRASS: "gold", METAL: "metal", DARK: "metal", RED: "red",
          VIOLET: "alien", PLUM: "alien"}


class Canvas(base.Canvas):
    shadow = SHADOW


def strip(frames):
    out = Canvas(sum(f.w for f in frames), max(f.h for f in frames))
    x = 0
    for f in frames:
        out.paste(f, x, 0)
        x += f.w
    return out


# --- Космонавт ---------------------------------------------------------------------------------
# Силуэт: большой круглый шлем, ранец за спиной, толстые рукава и штанины, тёмные подошвы.
# Узнаётся по визору (бирюзовое стекло спереди) и оранжевой нашивке на плече.

def _helmet(c, x, y, face=1):
    """Шлем с визором, лицом вправо при `face` 1. Центр (x, y), радиус 6."""
    c.ellipse(x, y, 5.7, 5.7, WHITE)
    # Визор: стекло в передней половине шлема, обод темнее, блик сверху.
    c.ellipse(x + 2.5 * face, y + 0.5, 3.4, 3.2, DARK)
    c.ellipse(x + 2.8 * face, y + 0.5, 2.6, 2.4, AQUA)
    c.set(x + 3 * face, y - 1, SKY)
    c.set(x + 4 * face, y - 1, SKY)
    # Кольцо шеи.
    c.rect(x - 3, y + 5, x + 3, y + 5, METAL)


def _pack(c, x, y0, y1):
    """Ранец за спиной: металлический блок с огоньком."""
    c.rect(x, y0, x + 2, y1, METAL)
    c.set(x + 1, y0 + 1, AQUA)


def _body(c, x0, y0, x1, y1):
    """Корпус скафандра: белый, пояс металлом, нагрудный пульт."""
    c.rect(x0, y0, x1, y1, WHITE)
    c.rect(x0, y1 - 1, x1, y1, METAL)
    c.rect(x1 - 3, y0 + 3, x1 - 1, y0 + 4, GREY)
    c.set(x1 - 2, y0 + 3, RED)


def _boot(c, x, y, w=4):
    c.rect(x - 1, y - 1, x + w - 2, y - 1, METAL)
    c.rect(x - 1, y, x + w - 1, y + 1, DARK)


def _arm(c, x0, y0, x1, y1, col):
    """Рукав с перчаткой на конце. Белый рукав поверх белого корпуса отбит тенью снизу."""
    if col == WHITE:
        c.line(x0, y0 + 1, x1 - 1, y1 + 1, GREY, 3)
    c.line(x0, y0, x1, y1, col, 3)
    c.ellipse(x1, y1, 1.4, 1.4, METAL)


def astro_side(phase, jump=False):
    """Космонавт сбоку, лицом вправо: бег по фазе 0..2π или прыжок."""
    c = Canvas()
    bob = 0 if jump else int(round(abs(math.sin(phase)) * 1.4))
    hip_y = 21 - bob
    swing = 0.9 if jump else math.sin(phase)
    _arm(c, 15, 15 - bob, 15 + 5 * swing, 20 - bob - (3 if jump else 0), GREY)
    for sign, cloth in ((-1, GREY), (1, WHITE)):
        a = swing * sign
        lift = max(0.0, math.cos(phase) * sign) * 3.0 if not jump else (4 if sign > 0 else 1)
        foot = (15 + 6 * a, 29 - lift)
        knee = ((15 + foot[0]) / 2 + 2, (hip_y + foot[1]) / 2)
        c.line(15 + sign, hip_y, knee[0], knee[1], cloth, 4)
        c.line(knee[0], knee[1], foot[0], foot[1], cloth, 4)
        _boot(c, foot[0], foot[1])
    _pack(c, 8, 13 - bob, 19 - bob)
    _body(c, 11, 13 - bob, 19, hip_y)
    _arm(c, 16, 15 - bob, 16 - 5 * swing, 20 - bob - (4 if jump else 0), WHITE)
    c.rect(15, 14 - bob, 17, 15 - bob, RED)
    _helmet(c, 16, 7 - bob)
    return c.finish()


def astro_back(phase):
    """Со спины: бежит вглубь экрана, виден ранец с двумя баллонами."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.4))
    for sign in (-1, 1):
        lift = max(0.0, s * sign) * 4.0
        x = 16 + sign * 3
        c.rect(x - 2, 21 - bob, x + 1, 28 - lift, WHITE if sign > 0 else GREY)
        _boot(c, x - 1, 28 - lift)
        _arm(c, 16 + sign * 6, 15 - bob, 16 + sign * 7, 20 - bob + s * sign * 2, WHITE)
    c.rect(11, 13 - bob, 20, 21 - bob, WHITE)
    c.rect(11, 20 - bob, 20, 21 - bob, METAL)
    # Ранец: блок и два баллона.
    c.rect(12, 13 - bob, 19, 19 - bob, METAL)
    c.rect(13, 14 - bob, 14, 18 - bob, GREY)
    c.rect(17, 14 - bob, 18, 18 - bob, GREY)
    c.set(15, 15 - bob, AQUA)
    c.set(16, 15 - bob, AQUA)
    c.ellipse(15.5, 7 - bob, 5.7, 5.7, WHITE)
    c.rect(13, 12 - bob, 18, 12 - bob, METAL)
    c.rect(12, 5 - bob, 19, 5 - bob, GREY)
    return c.finish()


def astro_leap(i):
    """Прыжок через клетку, четыре кадра: присел, толчок, поджал ноги, приземление."""
    c = Canvas()
    crouch = (3, 0, -1, 2)[i]
    legs = ((2, 2), (5, -4), (3, -1), (4, 3))[i]
    hip_y = 21 + crouch
    _arm(c, 15, 15 + crouch, 12 - i % 2, 11 + crouch if i in (1, 2) else 20 + crouch, GREY)
    for sign, cloth in ((-1, GREY), (1, WHITE)):
        foot = (15 + sign * legs[0] + (2 if i == 1 else 0), 29 if i in (0, 3) else 27 - (2 if i == 2 else 0))
        knee = ((15 + foot[0]) / 2 + 2 + legs[1] * 0.3, (hip_y + foot[1]) / 2 + (2 if i == 2 else 0))
        c.line(15 + sign, hip_y, knee[0], knee[1], cloth, 4)
        c.line(knee[0], knee[1], foot[0], foot[1], cloth, 4)
        _boot(c, foot[0], foot[1])
    _pack(c, 8, 13 + crouch, 19 + crouch)
    _body(c, 11, 13 + crouch, 19, hip_y)
    _arm(c, 16, 15 + crouch, 20 + i % 2, 10 + crouch if i in (1, 2) else 20 + crouch, WHITE)
    c.rect(15, 14 + crouch, 17, 15 + crouch, RED)
    _helmet(c, 16, 7 + crouch)
    c.finish()
    # Выхлоп ранца на толчке и в полёте.
    if i in (1, 2):
        c.set(8, 21 + crouch, AQUA)
        c.set(9, 22 + crouch, SKY)
        c.set(8, 23 + crouch, AQUA)
    return c


def astro_idle(i):
    """Стойка: два кадра, космонавт дышит, огонёк ранца мигает."""
    c = Canvas()
    up = i
    for sign, cloth in ((-1, GREY), (1, WHITE)):
        x = 15 + sign * 2
        c.rect(x - 1, 21, x + 1, 28, cloth)
        _boot(c, x, 29)
    _arm(c, 14, 15 - up, 13, 21 - up, GREY)
    _pack(c, 8, 13 - up, 19 - up)
    _body(c, 11, 13 - up, 19, 21)
    _arm(c, 17, 15 - up, 18, 21 - up, WHITE)
    c.rect(15, 14 - up, 17, 15 - up, RED)
    _helmet(c, 16, 7 - up)
    c.finish()
    if i == 1:
        c.set(9, 14 - up, SKY)
    return c


def _lean(c, sx, sy, hx, hy, w):
    """Корпус под наклоном: от плеч (sx, sy) к бёдрам (hx, hy), ширина w; пояс у бёдер."""
    n = math.hypot(hx - sx, hy - sy)
    dx, dy = (hx - sx) / n, (hy - sy) / n
    for k in range(int(n) + 1):
        x, y = sx + dx * k, sy + dy * k
        col = METAL if k >= int(n) - 1 else WHITE
        c.line(x + dy * w / 2, y - dx * w / 2, x - dy * w / 2, y + dx * w / 2, col, 2)


def astro_slide(i):
    """Подкат ногами вперёд: корпус откинут, ближняя нога вытянута, дальняя коленом вверх, рука
    сзади на земле. Макушка шлема на 15-й строке, как у матроса. Два кадра: колено и пыль."""
    c = Canvas()
    c.line(19, 27, 24, 23 - i, GREY, 3)
    c.line(24, 23 - i, 27, 27, GREY, 3)
    _boot(c, 27, 27)
    c.line(13, 24, 19, 23, GREY, 2)
    _lean(c, 12, 24, 19, 27, 6)
    c.line(19, 28, 28, 28, WHITE, 4)
    c.rect(28, 26, 30, 29, DARK)
    _arm(c, 11, 25, 6, 29, WHITE)
    _helmet(c, 10, 21)
    c.finish()
    for k, (x, y) in enumerate(((2, 30), (4, 31), (1, 28), (3, 29))):
        if (k + i) % 2 == 0:
            c.set(x, y, GREY)
    return c


def astro_crouch(i):
    """Присед: та же фигура, сложенная вниз, корпус прямо, колени вперёд. Два кадра шага."""
    c = Canvas()
    step = (-1, 1)[i]
    c.line(15, 24, 19, 26, GREY, 2)
    for sign, cloth in ((-1, GREY), (1, WHITE)):
        hip = (14, 27)
        knee = (20 - sign + step * sign, 26)
        foot = (17 - sign * 2 + step * sign * 2, 29)
        c.line(hip[0], hip[1], knee[0], knee[1], cloth, 4)
        c.line(knee[0], knee[1], foot[0], foot[1], cloth, 3)
        _boot(c, foot[0], foot[1])
    _pack(c, 8, 22, 26)
    c.rect(11, 22, 18, 26, WHITE)
    _arm(c, 14, 24, 19, 26, WHITE)
    _helmet(c, 16, 19)
    return c.finish()


def astro_hang(i):
    """На тросе: руки вверх к точке хвата (центр сверху), ноги свисают и качаются."""
    c = Canvas()
    sw = (-1, 1)[i]
    c.line(14, 13, 15, 1, GREY, 3)
    c.line(18, 13, 17, 1, WHITE, 3)
    c.ellipse(15, 1, 1.2, 1.2, METAL)
    c.ellipse(17, 1, 1.2, 1.2, METAL)
    _pack(c, 8, 13, 19)
    _body(c, 11, 13, 20, 21)
    for sign, cloth in ((-1, GREY), (1, WHITE)):
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


def sprites():
    """Все ленты набора в палитре `PALETTE`; пока готов герой платформера, остальное по семействам."""
    return {
        "hero_run": strip([astro_side(p) for p in base.phases()]),
        "hero_jump": astro_side(0.0, jump=True),
        "hero_leap": strip([astro_leap(i) for i in range(4)]),
        "hero_idle": strip([astro_idle(i) for i in range(2)]),
        "hero_back": strip([astro_back(p) for p in base.phases()]),
        "hero_slide": strip([astro_slide(i) for i in range(2)]),
        "hero_hang": strip([astro_hang(i) for i in range(2)]),
        "hero_crouch": strip([astro_crouch(i) for i in range(2)]),
    }


def preview(path, scale=4, pad=6, back=(0x1B, 0x1A, 0x33, 255)):
    """Лист набора: лента на строку, как в игре, после светотени."""
    palette, items, own = base.space_set()
    width = (max(c.w for c in items.values()) + 2 * pad) * scale
    blank = list(back) * width
    rows = [blank[:] for _ in range(pad * scale)]
    for key, canvas in items.items():
        for row in base.rgba_rows(canvas, own.get(key, palette), scale, back):
            line = list(back) * pad * scale + row
            rows.append(line + list(back) * ((len(blank) - len(line)) // 4))
        rows.extend(blank[:] for _ in range(pad * scale))
    with open(path, "wb") as f:
        f.write(png_bytes(width, len(rows), rows))
    print("превью: %s" % path)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        preview(sys.argv[sys.argv.index("--preview") + 1])
