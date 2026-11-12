#!/usr/bin/env python3
"""Спрайты 16/32-bit (#95): рисуются заново, не из 8-bit (решение 2026-11-12). Кадр 32×32,
спрайт это лента кадров по горизонтали (`hero_run.png` 192×32, шесть кадров), палитра сеттинга
из 16 цветов. Рисунок собирается из примитивов (эллипс, линия с толщиной, многоугольник), потом
автоматически получает тень по нижнему и правому краю и чёрную обводку: так шесть кадров бега
выходят из одной позы с разной фазой, а не из шести карт вручную.

Здесь набор «Пиратов»: стартовый для основы и её пробных демок (герой сбоку и со спины, скелет
сбоку и лицом, дублон, флаг, земля, камень, сундук, три слоя параллакса) и для платформера
«тропа» (#98: прыжок, стойка и сердце здесь, остальное в `pixel_trail16.py`: слайд и вис героя,
краб, попугай, детальный фон и передний план в своих палитрах). Ленты остальных демок приходят
вместе с ними (#96). Пишет PNG в thegames/assets/settings/<сеттинг>/16bit/ и
превью-лист в --preview.

    python3 tools/pixel_sprites16.py                 # сгенерировать
    python3 tools/pixel_sprites16.py --preview out.png

После правки: Godot --headless --path thegames --import.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixel_sprites import png_bytes  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRAME = 32

# Палитра «Пираты» для 16/32-bit: 16 цветов. Индекс это роль, им же пользуются спрайты.
K, NAVY, SEA, AQUA, SKY, WHITE, GREY, SKIN, TAN, GOLD, BRASS, WOOD, BARK, RED, LEAF, PINE = range(16)
PIRATES = [
    (0x16, 0x14, 0x12),  # K     обводка
    (0x1B, 0x2A, 0x4A),  # NAVY  тёмное море, тень синего
    (0x2F, 0x6F, 0xB5),  # SEA   море, полосы тельняшки
    (0x6F, 0xB4, 0xE8),  # AQUA  блик воды
    (0xBF, 0xE3, 0xF5),  # SKY   небо у горизонта
    (0xF4, 0xEF, 0xE6),  # WHITE тельняшка, кости
    (0xC9, 0xC2, 0xB4),  # GREY  тень белого, камень
    (0xF2, 0xC8, 0x9A),  # SKIN  кожа
    (0xC9, 0x8F, 0x5E),  # TAN   тень кожи
    (0xF2, 0xC8, 0x5A),  # GOLD  песок, дублон
    (0xC0, 0x8A, 0x2A),  # BRASS тень золота
    (0xA8, 0x5A, 0x2A),  # WOOD  дерево
    (0x6E, 0x34, 0x18),  # BARK  тень дерева
    (0xD9, 0x43, 0x2F),  # RED   бандана
    (0x3E, 0x9B, 0x5A),  # LEAF  зелень
    (0x1F, 0x5F, 0x3A),  # PINE  тень зелени
]
# Тень цвета: чем он становится у нижнего и правого края фигуры.
SHADOW = {SEA: NAVY, AQUA: SEA, SKY: AQUA, WHITE: GREY, GREY: TAN, SKIN: TAN, TAN: BARK, GOLD: BRASS,
          BRASS: BARK, WOOD: BARK, RED: BARK, LEAF: PINE}


class Canvas:
    """Картинка в индексах палитры; None это прозрачно."""

    def __init__(self, w=FRAME, h=FRAME):
        self.w = w
        self.h = h
        self.px = [[None] * w for _ in range(h)]

    def set(self, x, y, c):
        x = int(round(x))
        y = int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y][x] = c

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.px[y][x]
        return None

    def rect(self, x0, y0, x1, y1, c):
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                self.set(x, y, c)

    def ellipse(self, cx, cy, rx, ry, c):
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - rx - 1), int(cx + rx + 2)):
                if ((x - cx) / max(rx, 0.5)) ** 2 + ((y - cy) / max(ry, 0.5)) ** 2 <= 1.0:
                    self.set(x, y, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        """Отрезок толщиной `t`: вдоль него ставятся кружки."""
        n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
        r = (t - 1) / 2.0
        for i in range(n + 1):
            k = i / n
            x = x0 + (x1 - x0) * k
            y = y0 + (y1 - y0) * k
            if t <= 1:
                self.set(x, y, c)
            else:
                self.ellipse(x, y, r, r, c)

    def poly(self, points, c):
        """Заливка многоугольника построчно."""
        ys = [p[1] for p in points]
        for y in range(int(min(ys)), int(max(ys)) + 1):
            xs = []
            for i, a in enumerate(points):
                b = points[(i + 1) % len(points)]
                if (a[1] <= y < b[1]) or (b[1] <= y < a[1]):
                    xs.append(a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1]))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                for x in range(int(round(xs[i])), int(round(xs[i + 1])) + 1):
                    self.set(x, y, c)

    def shade(self):
        """Тень: пиксель, у которого снизу или справа пусто, темнеет."""
        src = [row[:] for row in self.px]
        for y in range(self.h):
            for x in range(self.w):
                c = src[y][x]
                if c is None or c not in SHADOW:
                    continue
                below = src[y + 1][x] if y + 1 < self.h else None
                right = src[y][x + 1] if x + 1 < self.w else None
                if below is None or right is None:
                    self.px[y][x] = SHADOW[c]

    def outline(self, c=K):
        """Обводка: пустой пиксель рядом с фигурой закрашивается."""
        src = [row[:] for row in self.px]
        for y in range(self.h):
            for x in range(self.w):
                if src[y][x] is not None:
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.w and 0 <= ny < self.h and src[ny][nx] is not None:
                        self.px[y][x] = c
                        break

    def finish(self):
        self.shade()
        self.outline()
        return self

    def paste(self, other, ox, oy):
        for y in range(other.h):
            for x in range(other.w):
                if other.px[y][x] is not None:
                    self.set(ox + x, oy + y, other.px[y][x])


def strip(frames):
    """Лента кадров по горизонтали."""
    out = Canvas(sum(f.w for f in frames), max(f.h for f in frames))
    x = 0
    for f in frames:
        out.paste(f, x, 0)
        x += f.w
    return out


# --- Матрос ------------------------------------------------------------------------------------

def _stripes(c, x0, y0, x1, y1):
    """Тельняшка: белые и синие полосы по два пикселя."""
    for y in range(y0, y1 + 1):
        c.rect(x0, y, x1, y, WHITE if ((y - y0) // 2) % 2 == 0 else SEA)


def sailor_side(phase, jump=False):
    """Матрос сбоку, лицом вправо: бег по фазе 0..2π или прыжок."""
    c = Canvas()
    bob = 0 if jump else int(round(abs(math.sin(phase)) * 1.4))
    hip_y = 21 - bob
    swing = 0.9 if jump else math.sin(phase)
    # Дальняя рука и дальняя нога темнее, рисуются первыми.
    c.line(15, 14 - bob, 15 + 5 * swing, 19 - bob - (3 if jump else 0), TAN, 3)
    for sign, cloth in ((-1, NAVY), (1, SEA)):
        a = swing * sign
        lift = max(0.0, math.cos(phase) * sign) * 3.0 if not jump else (4 if sign > 0 else 1)
        foot = (15 + 6 * a, 29 - lift)
        knee = ((15 + foot[0]) / 2 + 2, (hip_y + foot[1]) / 2)
        c.line(15 + sign, hip_y, knee[0], knee[1], cloth, 4)
        c.line(knee[0], knee[1], foot[0], foot[1], cloth, 3)
        c.rect(foot[0] - 1, foot[1], foot[0] + 3, foot[1] + 1, BARK)
    _stripes(c, 11, 12 - bob, 19, hip_y)
    # Ближняя рука поверх тельняшки, в противофазе с ближней ногой.
    c.line(16, 14 - bob, 16 - 5 * swing, 19 - bob - (4 if jump else 0), SKIN, 3)
    # Голова: бандана сверху, узел на затылке, глаз и нос.
    c.ellipse(16, 7 - bob, 5, 5, SKIN)
    for y in range(1 - bob, 6 - bob):
        for x in range(10, 23):
            if c.get(x, y) == SKIN:
                c.set(x, y, RED)
    c.rect(9, 5 - bob, 10, 7 - bob, RED)
    c.set(21, 8 - bob, SKIN)
    c.finish()
    c.set(19, 7 - bob, K)
    return c


def sailor_back(phase):
    """Матрос со спины: бежит вглубь экрана, ноги по очереди, руки качаются."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.4))
    for sign in (-1, 1):
        lift = max(0.0, s * sign) * 4.0
        x = 16 + sign * 3
        c.rect(x - 2, 21 - bob, x + 1, 28 - lift, SEA if sign > 0 else NAVY)
        c.rect(x - 2, 28 - lift, x + 1, 29 - lift, BARK)
        c.line(16 + sign * 6, 14 - bob, 16 + sign * 7, 19 - bob + s * sign * 2, SKIN, 3)
    _stripes(c, 11, 12 - bob, 20, 21 - bob)
    c.ellipse(15.5, 7 - bob, 5, 5, SKIN)
    for y in range(1 - bob, 9 - bob):
        for x in range(9, 23):
            if c.get(x, y) == SKIN:
                c.set(x, y, RED)
    # Узел банданы и два хвоста.
    c.rect(14, 8 - bob, 17, 9 - bob, RED)
    c.line(14, 10 - bob, 12 + s, 13 - bob, RED, 2)
    c.line(17, 10 - bob, 19 + s, 13 - bob, RED, 2)
    return c.finish()


def sailor_leap(i):
    """Прыжок через клетку, четыре кадра: присел, толчок, поджал ноги, приземление."""
    c = Canvas()
    crouch = (3, 0, -1, 2)[i]
    legs = ((2, 2), (5, -4), (3, -1), (4, 3))[i]
    hip_y = 21 + crouch
    c.line(15, 14 + crouch, 12 - i % 2, 11 + crouch if i in (1, 2) else 19 + crouch, TAN, 3)
    for sign, cloth in ((-1, NAVY), (1, SEA)):
        foot = (15 + sign * legs[0] + (2 if i == 1 else 0), 29 if i in (0, 3) else 27 - (2 if i == 2 else 0))
        knee = ((15 + foot[0]) / 2 + 2 + legs[1] * 0.3, (hip_y + foot[1]) / 2 + (2 if i == 2 else 0))
        c.line(15 + sign, hip_y, knee[0], knee[1], cloth, 4)
        c.line(knee[0], knee[1], foot[0], foot[1], cloth, 3)
        c.rect(foot[0] - 1, foot[1], foot[0] + 3, foot[1] + 1, BARK)
    _stripes(c, 11, 12 + crouch, 19, hip_y)
    c.line(16, 14 + crouch, 20 + i % 2, 10 + crouch if i in (1, 2) else 19 + crouch, SKIN, 3)
    c.ellipse(16, 7 + crouch, 5, 5, SKIN)
    for y in range(1 + crouch, 6 + crouch):
        for x in range(10, 23):
            if c.get(x, y) == SKIN:
                c.set(x, y, RED)
    c.rect(9, 5 + crouch, 10, 7 + crouch, RED)
    c.set(21, 8 + crouch, SKIN)
    c.finish()
    c.set(19, 7 + crouch, K)
    return c


def sailor_idle(i):
    """Стойка: два кадра, матрос дышит."""
    c = Canvas()
    up = i
    for sign, cloth in ((-1, NAVY), (1, SEA)):
        x = 15 + sign * 2
        c.rect(x - 1, 21, x + 1, 29, cloth)
        c.rect(x - 1, 29, x + 2, 30, BARK)
    c.line(14, 14 - up, 13, 20 - up, TAN, 3)
    _stripes(c, 11, 12 - up, 19, 21)
    c.line(17, 14 - up, 18, 20 - up, SKIN, 3)
    c.ellipse(16, 7 - up, 5, 5, SKIN)
    for y in range(1 - up, 6 - up):
        for x in range(10, 23):
            if c.get(x, y) == SKIN:
                c.set(x, y, RED)
    c.rect(9, 5 - up, 10, 7 - up, RED)
    c.set(21, 8 - up, SKIN)
    c.finish()
    c.set(19, 7 - up, K)
    return c


def heart():
    """Жизнь в HUD."""
    c = Canvas()
    c.ellipse(11, 12, 5.5, 5.5, RED)
    c.ellipse(20, 12, 5.5, 5.5, RED)
    c.poly([(5, 14), (26, 14), (15.5, 26)], RED)
    c.rect(9, 9, 10, 10, WHITE)
    return c.finish()


# --- Скелет ------------------------------------------------------------------------------------

def skeleton_side(phase):
    """Скелет сбоку, лицом влево (навстречу герою): шаг по фазе."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.2))
    c.line(16, 15 - bob, 16 - 5 * s, 20 - bob, GREY, 2)
    for sign, bone in ((-1, GREY), (1, WHITE)):
        a = s * sign
        lift = max(0.0, math.cos(phase) * sign) * 2.5
        foot = (16 - 5 * a, 29 - lift)
        knee = ((16 + foot[0]) / 2 - 1.5, (22 - bob + foot[1]) / 2)
        c.line(16, 22 - bob, knee[0], knee[1], bone, 2)
        c.line(knee[0], knee[1], foot[0], foot[1], bone, 2)
        c.rect(foot[0] - 3, foot[1], foot[0], foot[1] + 1, bone)
    # Позвоночник, рёбра, таз.
    c.line(16, 12 - bob, 16, 22 - bob, WHITE, 2)
    for y in (13, 15, 17):
        c.line(12, y - bob, 19, y - bob, WHITE, 1)
    c.rect(13, 21 - bob, 19, 22 - bob, WHITE)
    c.line(16, 14 - bob, 16 + 5 * s, 20 - bob, WHITE, 2)
    # Череп с глазницей и челюстью.
    c.ellipse(15, 6 - bob, 5.5, 5, WHITE)
    c.rect(11, 10 - bob, 16, 11 - bob, WHITE)
    c.finish()
    c.rect(11, 5 - bob, 13, 7 - bob, K)
    c.set(10, 8 - bob, K)
    for x in (11, 13, 15):
        c.set(x, 11 - bob, K)
    return c


def skeleton_front(phase):
    """Скелет лицом к камере: идёт на игрока, ноги по очереди."""
    c = Canvas()
    s = math.sin(phase)
    bob = int(round(abs(s) * 1.2))
    for sign in (-1, 1):
        lift = max(0.0, s * sign) * 3.0
        x = 16 + sign * 3
        c.line(x, 22 - bob, x, 28 - lift, WHITE, 2)
        c.rect(x - 2, 28 - lift, x + 1, 29 - lift, WHITE)
        c.line(16 + sign * 5, 13 - bob, 16 + sign * 8, 20 - bob - s * sign * 2, WHITE, 2)
    c.line(15.5, 12 - bob, 15.5, 22 - bob, WHITE, 2)
    for y in (13, 15, 17):
        c.line(11, y - bob, 20, y - bob, WHITE, 1)
    c.rect(12, 21 - bob, 19, 22 - bob, WHITE)
    c.ellipse(15.5, 6 - bob, 6, 5.5, WHITE)
    c.rect(12, 10 - bob, 19, 11 - bob, WHITE)
    c.finish()
    c.rect(11, 4 - bob, 13, 7 - bob, K)
    c.rect(18, 4 - bob, 20, 7 - bob, K)
    c.rect(15, 8 - bob, 16, 9 - bob, K)
    for x in (13, 15, 17):
        c.set(x, 11 - bob, K)
    return c


# --- Вещи --------------------------------------------------------------------------------------

def coin(i):
    """Дублон вращается: шесть кадров, ширина по косинусу."""
    c = Canvas()
    rx = max(1.0, abs(math.cos(math.pi * i / 6.0)) * 9.0)
    c.ellipse(15.5, 16, rx, 9, GOLD)
    if rx > 4:
        c.ellipse(15.5, 16, rx - 3, 6, BRASS)
        c.ellipse(15.5, 16, rx - 4.5, 4.5, GOLD)
        c.line(15.5 - rx + 2, 11, 15.5 - rx + 2, 14, WHITE, 1)
    return c.finish()


def flag(i):
    """Флаг с черепом на мачте: полотнище идёт волной."""
    c = Canvas()
    c.rect(5, 2, 6, 31, WOOD)
    c.ellipse(5.5, 2, 2, 2, GOLD)
    top = []
    bottom = []
    for x in range(8, 29):
        w = math.sin(x * 0.45 - i * math.pi / 3.0) * 1.6 * (x - 8) / 20.0
        top.append((x, 5 + w))
        bottom.append((x, 18 + w))
    c.poly(top + bottom[::-1], NAVY)
    c.shade()
    c.outline()
    mid = math.sin(17 * 0.45 - i * math.pi / 3.0) * 0.8
    c.ellipse(17, 10 + mid, 3, 2.6, WHITE)
    c.rect(15, 13 + mid, 19, 13 + mid, WHITE)
    c.set(16, 10 + mid, K)
    c.set(18, 10 + mid, K)
    return c


def ground(inner=False):
    """Палуба: доски; у кромки сверху светлая полоса и гвозди."""
    c = Canvas()
    c.rect(0, 0, 31, 31, WOOD)
    for y in (7, 15, 23, 31):
        c.rect(0, y, 31, y, BARK)
    for row, y in enumerate((0, 8, 16, 24)):
        x = (row * 13 + 9) % 32
        c.rect(x, y, x, y + 6, BARK)
        c.set((x + 3) % 32, y + 2, BRASS)
    if not inner:
        c.rect(0, 0, 31, 1, GOLD)
        c.rect(0, 2, 31, 2, BRASS)
    return c


def rock():
    c = Canvas()
    c.poly([(4, 28), (2, 18), (8, 9), (17, 5), (26, 10), (30, 20), (27, 28)], GREY)
    c.poly([(8, 14), (14, 9), (20, 10), (15, 15)], WHITE)
    c.line(18, 18, 24, 24, TAN, 1)
    return c.finish()


def chest():
    c = Canvas()
    c.rect(4, 14, 27, 28, WOOD)
    c.ellipse(15.5, 14, 12, 7, WOOD)
    c.rect(4, 14, 27, 15, BARK)
    for x in (8, 23):
        c.rect(x, 8, x + 1, 28, BRASS)
    c.rect(14, 15, 17, 19, GOLD)
    return c.finish()


# --- Параллакс ---------------------------------------------------------------------------------

def par_sky():
    """Дальний слой: облака, лента 256×48, стыкуется по краям."""
    c = Canvas(256, 48)
    for cx, cy, r in ((30, 18, 13), (52, 22, 9), (120, 30, 11), (140, 26, 15), (166, 31, 9), (226, 14, 12), (246, 19, 8)):
        c.ellipse(cx, cy, r, r * 0.55, WHITE)
        c.ellipse(cx - r * 0.5, cy + 2, r * 0.7, r * 0.4, WHITE)
        c.ellipse(cx % 256 - 256 if cx > 240 else cx, cy, r, r * 0.55, WHITE)
    c.shade()
    return c


def par_far():
    """Средний слой: острова на горизонте, лента 256×48, низ сплошной."""
    c = Canvas(256, 48)
    for x in range(256):
        h = 10 + 12 * max(0.0, math.sin(x * math.pi / 64.0)) ** 2 + 5 * math.sin(x * math.pi / 16.0 + 1.0)
        h += 14 * max(0.0, math.sin((x - 40) * math.pi / 128.0)) ** 6
        top = 47 - int(max(h, 3))
        c.rect(x, top, x, 47, PINE)
        c.rect(x, top, x, top + 2, LEAF)
    # Пальмы на макушках.
    for px in (32, 96, 104, 168, 232):
        base = 47 - int(10 + 12 * max(0.0, math.sin(px * math.pi / 64.0)) ** 2 + 5 * math.sin(px * math.pi / 16.0 + 1.0)
                        + 14 * max(0.0, math.sin((px - 40) * math.pi / 128.0)) ** 6)
        c.line(px, base, px + 1, base - 9, BARK, 1)
        for dx in (-5, -3, 3, 5):
            c.line(px + 1, base - 9, px + 1 + dx, base - 8 + abs(dx) // 2, LEAF, 1)
    return c


def par_mid():
    """Ближний слой: волны с барашками, лента 256×32."""
    c = Canvas(256, 32)
    for x in range(256):
        crest = 6 + 3 * math.sin(x * math.pi / 32.0) + 1.5 * math.sin(x * math.pi / 8.0)
        top = int(round(crest))
        c.rect(x, top, x, 31, SEA)
        c.rect(x, top, x, top + 1, AQUA)
        if math.sin(x * math.pi / 32.0) > 0.92:
            c.rect(x, top - 1, x, top, WHITE)
        if (x // 4 + top) % 5 == 0:
            c.set(x, top + 9 + (x % 7), AQUA)
    return c


# --- Наборы и запись ---------------------------------------------------------------------------

def phases(n=6):
    return [2.0 * math.pi * i / n for i in range(n)]


def pirates():
    return {
        "hero_run": strip([sailor_side(p) for p in phases()]),
        "hero_jump": sailor_side(0.0, jump=True),
        "hero_leap": strip([sailor_leap(i) for i in range(4)]),
        "hero_idle": strip([sailor_idle(i) for i in range(2)]),
        "heart": heart(),
        "hero_back": strip([sailor_back(p) for p in phases()]),
        "enemy_walk": strip([skeleton_side(p) for p in phases()]),
        "enemy_front": strip([skeleton_front(p) for p in phases()]),
        "coin": strip([coin(i) for i in range(6)]),
        "flag": strip([flag(i) for i in range(6)]),
        "ground": ground(),
        "ground_inner": ground(inner=True),
        "rock": rock(),
        "chest": chest(),
        "par_sky": par_sky(),
        "par_far": par_far(),
        "par_mid": par_mid(),
    }


def sets():
    """Наборы: имя папки сеттинга → (палитра, спрайты, палитры отдельных лент). Фон и передний план
    тропы (#98) в своих палитрах, как слои у 16-битных приставок."""
    import pixel_trail16 as trail
    sprites = pirates()
    sprites.update(trail.sprites())
    own = {}
    for key, canvas in trail.backdrop().items():
        sprites[key] = canvas
        own[key] = trail.PIRATES_BG
    for key, canvas in trail.foreground().items():
        sprites[key] = canvas
        own[key] = trail.PIRATES_FG
    # Гонка «псевдо-3D» (#99): повозки и пропы в палитре спрайтов, горизонт в своей, цвета
    # дороги лентой.
    import pixel_road16 as road
    sprites.update(road.sprites())
    # Шутер «до выхода» (#100): текстуры, скелеты, оружие, лицо в палитре спрайтов.
    import pixel_hold16 as hold
    sprites.update(hold.sprites())
    # Футбол «один на одного» (#101): игроки, мяч, трава в палитре спрайтов.
    import pixel_soccer16 as soccer
    sprites.update(soccer.sprites())
    for key, canvas in road.horizon().items():
        sprites[key] = canvas
        own[key] = road.PIRATES_SKY
    for key, canvas in road.road_palette().items():
        sprites[key] = canvas
        own[key] = road.ROAD_COLORS
    return {"pirates": (PIRATES, sprites, own)}


def rgba_rows(canvas, palette, scale=1, back=None):
    rows = []
    for y in range(canvas.h):
        row = []
        for x in range(canvas.w):
            c = canvas.px[y][x]
            if c is None:
                px = back if back is not None else (0, 0, 0, 0)
            else:
                px = palette[c] + (255,)
            row.extend(px * scale)
        for _ in range(scale):
            rows.append(row)
    return rows


def main():
    for name, (palette, sprites, own) in sets().items():
        out = os.path.join(ROOT, "thegames", "assets", "settings", name, "16bit")
        os.makedirs(out, exist_ok=True)
        for key, canvas in sprites.items():
            with open(os.path.join(out, key + ".png"), "wb") as f:
                f.write(png_bytes(canvas.w, canvas.h, rgba_rows(canvas, own.get(key, palette))))
        print("%s: %d спрайтов в %s" % (name, len(sprites), out))
    if "--preview" in sys.argv:
        path = sys.argv[sys.argv.index("--preview") + 1]
        palette, sprites, own = sets()["pirates"]
        scale = 2
        pad = 8
        back = (0x3A, 0x56, 0x7A, 255)
        width = (max(c.w for c in sprites.values()) + 2 * pad) * scale
        rows = []
        blank = list(back) * (width // scale) * scale
        for _ in range(pad * scale):
            rows.append(blank[:])
        for key, canvas in sprites.items():
            for row in rgba_rows(canvas, own.get(key, palette), scale, back):
                line = list(back) * pad * scale + row
                rows.append(line + list(back) * ((len(blank) - len(line)) // 4))
            for _ in range(pad * scale):
                rows.append(blank[:])
        with open(path, "wb") as f:
            f.write(png_bytes(width, len(rows), rows))
        print("превью: %s" % path)


if __name__ == "__main__":
    main()
