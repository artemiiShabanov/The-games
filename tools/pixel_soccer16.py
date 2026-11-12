"""Рисунок футбола × 16/32-bit «один на одного» (#101) для pixel_sprites16.py, графика по
Sensible Soccer (решение 2026-11-12): вид сверху, крошечные стоящие игроки 16×16 в восьми
направлениях
(три кадра бега, подкат, лежит), формы четырёх цветов и двух вратарей, мяч, трава полосами.
Всё в палитре спрайтов сеттинга.
"""
import math

from pixel_sprites16 import (Canvas, strip, K, NAVY, SEA, AQUA, WHITE, GREY, SKIN, TAN, GOLD, BRASS, WOOD, BARK,
                             RED, LEAF, PINE)

F = 16
# Направления по кругу: 0 вправо, дальше по часовой (y вниз), как угол atan2.
DIRS = [(math.cos(a), math.sin(a)) for a in [i * math.pi / 4.0 for i in range(8)]]


def player(d, frame, shirt, shorts, hair=BARK, mode="run"):
    """Игрок маленькой стоящей фигуркой под крутым углом, как в Sensible Soccer: ноги, трусы,
    футболка, голова. Взгляд вниз: лицо; вверх: затылок; вбок: профиль, руки и ноги шагают."""
    c = Canvas(F, F)
    dx, dy = DIRS[d]
    if mode == "down":
        # Лежит на траве поперёк.
        c.rect(3, 10, 12, 12, shirt)
        c.rect(10, 10, 12, 12, shorts)
        c.ellipse(3, 11, 2, 1.5, SKIN)
        c.rect(1, 10, 3, 10, hair)
        return c.finish()
    if mode == "slide":
        # Подкат: тело низко, нога вытянута по ходу.
        sgn = 1 if dx >= 0 else -1
        c.rect(5, 10, 10, 12, shirt)
        c.line(8, 12, 8 + sgn * 6, 13, shorts, 2)
        c.ellipse(8 - sgn * 4, 10, 2, 2, SKIN)
        c.rect(8 - sgn * 5, 8, 8 - sgn * 3, 8, hair)
        return c.finish()
    side = abs(dx) > 0.38
    back = dy < -0.38
    sgn = 1 if dx >= 0 else -1
    step = (0, 1, -1)[frame]
    # Ноги.
    if side:
        c.rect(7 + step * sgn, 12, 7 + step * sgn, 14, SKIN)
        c.rect(8 - step * sgn, 12, 8 - step * sgn, 14, SKIN)
        c.set(7 + step * sgn + sgn, 15, K)
        c.set(8 - step * sgn + sgn, 15, K)
    else:
        c.rect(6, 12, 6, 14 - (1 if step > 0 else 0), SKIN)
        c.rect(9, 12, 9, 14 - (1 if step < 0 else 0), SKIN)
        c.set(6, 15 - (1 if step > 0 else 0), K)
        c.set(9, 15 - (1 if step < 0 else 0), K)
    # Трусы, футболка, руки.
    c.rect(5 if not side else 6, 10, 10 if not side else 9, 11, shorts)
    c.rect(5 if not side else 6, 6, 10 if not side else 9, 9, shirt)
    if side:
        c.set(7 - step * sgn, 9, SKIN)
    else:
        c.rect(4, 7 + (1 if step > 0 else 0), 4, 8 + (1 if step > 0 else 0), SKIN)
        c.rect(11, 7 + (1 if step < 0 else 0), 11, 8 + (1 if step < 0 else 0), SKIN)
    # Голова.
    c.rect(6, 2, 9, 5, SKIN)
    if back:
        c.rect(6, 2, 9, 5, hair)
    elif side:
        c.rect(6, 2, 9, 3, hair)
        c.rect(6 if sgn > 0 else 9, 2, 6 if sgn > 0 else 9, 5, hair)
        c.set(8 + (1 if sgn > 0 else -2), 4, K)
    else:
        c.rect(6, 2, 9, 2, hair)
        c.set(7, 4, K)
        c.set(8, 4, K)
    return c.finish()


def kit_strip(shirt, shorts, hair=BARK):
    frames = []
    for d in range(8):
        for fr in range(3):
            frames.append(player(d, fr, shirt, shorts, hair))
    for d in range(8):
        frames.append(player(d, 0, shirt, shorts, hair, "slide"))
    for d in range(8):
        frames.append(player(d, 0, shirt, shorts, hair, "down"))
    return strip(frames)


def ball(i):
    c = Canvas(8, 8)
    c.ellipse(3.5, 3.5, 3, 3, WHITE)
    for k, (x, y) in enumerate(((2, 2), (5, 3), (3, 5))):
        if (k + i) % 2 == 0:
            c.set(x, y, K)
    return c.finish()


def grass():
    """Трава 64×64: полоса светлая и тёмная по 32, мелкие травинки."""
    c = Canvas(64, 64)
    for x in range(64):
        for y in range(64):
            band = LEAF if x < 32 else PINE
            if (x * 7 + y * 13) % 17 == 0:
                band = PINE if band == LEAF else LEAF
            c.set(x, y, band)
    return c


def sprites():
    return {
        "soccer_hero": kit_strip(RED, WHITE),
        "soccer_rival_0": kit_strip(SEA, WHITE, GOLD),
        "soccer_rival_1": kit_strip(GOLD, NAVY),
        "soccer_rival_2": kit_strip(WHITE, NAVY, K),
        "soccer_keeper_hero": kit_strip(PINE, K),
        "soccer_keeper_rival": kit_strip(GREY, K, K),
        "soccer_ball": strip([ball(i) for i in range(2)]),
        "soccer_grass": grass(),
    }
