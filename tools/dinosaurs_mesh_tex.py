#!/usr/bin/env python3
"""Текстуры уровня «Динозавров» для low poly (#137): те же имена и размеры, что у пиратов в
`lowpoly_meshes.py` (`tex_sand` … `tex_sky`) и у космоса в `space_mesh_tex.py`, свой рисунок.
Стиль первой PlayStation: низкое разрешение, в которое втиснуто как можно больше деталей. Все
плитки стыкуются по краям: каждый пиксель ставится по модулю размера. Цвета из палитры
`dinosaurs16.PALETTE` и те же, что у моделей в `dinosaurs_mesh_chars.py`.

Слоты по ролям: `sand` красная глина в трещинах с трёхпалыми следами и осколками кости, `planks`
настил из брёвен, стянутых лианами, `water` основание мира, у динозавров это жидкость: лава,
та же зыбь, что у моря пиратов, тёмная корка и раскалённые жилы; `rock` кладка из лавового
камня с красными прожилками, мхом и окаменелыми аммонитами, `sail` растянутая пятнистая шкура
со швами из жил, `grass` подстилка джунглей с папоротником, `road` утоптанная тропа с колеями
там же, где колеи у пиратов, и костяными вешками по оси, `mud` смоляная яма (заметно темнее
тропы), `wind` стрелки разгона на прозрачном, `sky` панорама: день, вулканы с дымом и лавой,
шеи зауроподов над джунглями, плитка по горизонтали.

    python3 tools/dinosaurs_mesh_tex.py --preview out.png   # лист: каждая текстура плиткой 2×2
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lowpoly_meshes as lm  # noqa: E402
import dinosaurs16 as d16  # noqa: E402

rgb, mul = lm.rgb, lm.mul


def _pal(i):
    return tuple(d16.PALETTE[i])


CLAY, CLAY_D, CLAY_L = _pal(d16.TAN), rgb("8A3A26"), rgb("CC7048")  # красная глина
CLAY_DD = _pal(d16.DARK)
STONE, STONE_D, STONE_L = _pal(d16.METAL), rgb("4E4046"), rgb("A08C8E")  # лавовый камень
BONE, BONE_D = _pal(d16.WHITE), _pal(d16.GREY)
LEAF, LEAF_D, LEAF_L = _pal(d16.VIOLET), _pal(d16.PLUM), rgb("94D85E")  # листва
WOOD, WOOD_D, WOOD_L = rgb("8E5A30"), rgb("5A3420"), rgb("B88048")  # брёвна
LAVA, LAVA_L = _pal(d16.RED), _pal(d16.GOLD)
BRASS = _pal(d16.BRASS)
HAZE = _pal(d16.SKY)
NAVY, SEA, AQUA = _pal(d16.NAVY), _pal(d16.SEA), _pal(d16.AQUA)


def wpx(a, x, y, c, alpha=255):
    """Пиксель по модулю размера: рисунок, вышедший за край, продолжается с другой стороны."""
    a.px(int(x) % a.w, int(y) % a.h, c, alpha)


def wrect(a, x, y, w, h, c):
    for j in range(h):
        for i in range(w):
            wpx(a, x + i, y + j, c)


def mix(c0, c1, k):
    return tuple(int(round(c0[i] + (c1[i] - c0[i]) * k)) for i in range(3))


def footprint(a, x, y, c, flip=False):
    """Трёхпалый след раптора: пятка и три расходящихся пальца с точками когтей."""
    s = -1 if flip else 1
    wrect(a, x, y, 2, 2, c)
    for dx, dy in ((-2, -2), (-3, -3), (0, -2), (0, -3), (0, -4), (3, -2), (4, -3)):
        wpx(a, x + dx, y + dy * s + (1 if flip else 0), c)
        if dx == 0:
            wpx(a, x + 1, y + dy * s + (1 if flip else 0), c)


def crack(a, x, y, n, c, lit):
    """Трещина: ломаная в один пиксель со светлой кромкой снизу."""
    dx = 1
    for _ in range(n):
        wpx(a, x, y, c)
        wpx(a, x, y + 1, lit)
        r = a.rng.random()
        if r < 0.3:
            y += 1
        elif r < 0.45:
            y -= 1
        elif r < 0.55:
            dx = -dx
        x += dx


def ammonite(a, cx, cy, r, shell, dark):
    """Окаменелый аммонит: спираль тёмной линией по светлому диску."""
    for y in range(-r, r + 1):
        for x in range(-r, r + 1):
            d = math.hypot(x, y)
            if d <= r + 0.3:
                ang = math.atan2(y, x)
                turn = (d - ang / (2 * math.pi) * 2.0) % 2.0
                wpx(a, cx + x, cy + y, dark if (turn < 0.75 or d > r - 0.7) else shell)
    wpx(a, cx, cy, dark)


def frond(a, x, y, c, lit, right=True):
    """Листик папоротника: косой стебель и перья по обе стороны."""
    s = 1 if right else -1
    for k in range(5):
        wpx(a, x + k * s, y - k, c)
        if k % 2 == 1 or k == 4:
            wpx(a, x + (k - 1) * s, y - k - 1, lit)
            wpx(a, x + (k + 1) * s, y - k + 1, lit)


def tex_sand():
    """Красная глина: пятна тоном, сетка сухих трещин, трёхпалые следы, осколки кости и галька."""
    a = lm.Atlas(64, 64, 331)
    for y in range(64):
        for x in range(64):
            k = 1.0 + 0.06 * math.sin(x * math.pi / 16.0 + 2.0 * math.sin(y * math.pi / 32.0)) \
                + 0.05 * math.sin((y * 3 + x) * math.pi / 32.0)
            a.px(x, y, mul(CLAY, k))
    for _ in range(200):
        wpx(a, a.rng.randrange(64), a.rng.randrange(64), CLAY_D if a.rng.random() < 0.6 else CLAY_L)
    for _ in range(9):
        crack(a, a.rng.randrange(64), a.rng.randrange(64), a.rng.randrange(8, 18), CLAY_DD, CLAY_L)
    for i, (x, y) in enumerate(((12, 18), (22, 34), (10, 50), (46, 12), (52, 44))):
        footprint(a, x, y, mix(CLAY_D, CLAY_DD, 0.8), flip=(i % 2 == 1))
    for _ in range(7):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wpx(a, x, y, BONE), wpx(a, x + 1, y, BONE), wpx(a, x + 2, y + 1, BONE_D), wpx(a, x, y + 1, CLAY_DD)
    for _ in range(8):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wpx(a, x, y, STONE_L), wpx(a, x + 1, y, STONE), wpx(a, x, y + 1, STONE_D), wpx(a, x + 1, y + 1, CLAY_DD)
    a.noise(0, 0, 64, 64, 0.04)
    return a


def tex_planks():
    """Настил из брёвен: ряды по 8 пикселей, круглый бок со светлым верхом и тёмной щелью, волокна,
    сучки, торцы вразбежку и перевязки лианами с листком."""
    a = lm.Atlas(64, 64, 333)
    for row in range(8):
        y0 = row * 8
        tone = (1.0, 0.9, 1.07, 0.95, 1.03, 0.88, 1.0, 0.94)[row]
        shade = (0.62, 1.0, 1.22, 1.12, 1.0, 0.92, 0.8, 0.5)
        for j in range(8):
            for x in range(64):
                k = tone * shade[j] * (1.0 + 0.05 * math.sin((x + row * 11) * math.pi / 8.0 + j))
                a.px(x, y0 + j, mul(WOOD, k))
        # Волокна и сучки.
        for _ in range(7):
            x, j = a.rng.randrange(64), a.rng.randrange(2, 6)
            wrect(a, x, y0 + j, a.rng.randrange(3, 8), 1, mul(WOOD_D, tone * 1.15))
        kx = a.rng.randrange(64)
        wrect(a, kx, y0 + 3, 3, 2, WOOD_D), wpx(a, kx + 1, y0 + 3, mul(WOOD, 0.8))
        # Торец бревна: стык двух стволов, у каждого ряда в своём месте.
        ex = (row * 23 + 9) % 64
        wrect(a, ex, y0 + 1, 1, 6, WOOD_D)
        wrect(a, ex + 1, y0 + 1, 1, 6, mul(WOOD_L, tone))
    # Перевязки лианами: две вертикальные косицы через все брёвна.
    for x0 in (14, 46):
        for y in range(64):
            j = y % 8
            if j in (0, 7):
                continue
            off = (y // 2) % 2
            vine = mix(LEAF_D, WOOD_D, 0.35)
            wpx(a, x0 + off, y, vine)
            wpx(a, x0 + 1 + off, y, LEAF_D)
            wpx(a, x0 + 2 - off, y, LEAF if j == 2 else vine)
            wpx(a, x0 + 3, y, mul(WOOD_D, 0.9))
    for x, y in ((18, 20), (50, 44), (12, 52)):
        wpx(a, x, y, LEAF_L), wpx(a, x + 1, y, LEAF), wpx(a, x + 1, y + 1, LEAF_D), wpx(a, x + 2, y + 1, LEAF)
    a.noise(0, 0, 64, 64, 0.05)
    return a


def tex_water():
    """Лава: та же зыбь, что у моря пиратов, тёмная остывшая корка, оранжевые жилы и жёлтый жар."""
    a = lm.Atlas(64, 64, 335)
    crust, crust_l, hot, core = rgb("3A1A16"), rgb("6A2A1C"), LAVA, LAVA_L
    for y in range(64):
        for x in range(64):
            w = math.sin((x + 6.0 * math.sin(y * math.pi / 8.0)) * math.pi / 16.0) + math.sin((y * 2 + x) * math.pi / 16.0)
            c = crust_l if w > -0.4 else crust
            if w > 0.45:
                c = mix(crust_l, hot, 0.55)
            if w > 0.95:
                c = hot
            if w > 1.5:
                c = mix(hot, core, 0.6)
            if w > 1.8:
                c = core
            a.px(x, y, c)
    # Трещины в корке и искры.
    for _ in range(26):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        if a.get(x, y)[0] < 120:
            wpx(a, x, y, rgb("20100E")), wpx(a, x + 1, y + 1, rgb("20100E")), wpx(a, x + 2, y + 1, rgb("8A3A1C"))
    for _ in range(34):
        wpx(a, a.rng.randrange(64), a.rng.randrange(64), rgb("FFF4B0") if a.rng.random() < 0.35 else rgb("F88C44"))
    a.noise(0, 0, 64, 64, 0.05)
    return a


def tex_rock():
    """Кладка из лавового камня: глыбы 16×8 со сдвигом, у каждой свой тон, светлая кромка сверху,
    пузырьки пемзы, красные прожилки, мох в швах и два окаменелых аммонита."""
    a = lm.Atlas(64, 64, 337)
    a.rect(0, 0, 64, 64, STONE)
    for row in range(8):
        y = row * 8
        off = (row % 2) * 8
        for col in range(4):
            x = off + col * 16
            tone = a.rng.uniform(0.82, 1.14)
            wrect(a, x, y, 16, 8, mul(STONE, tone))
            wrect(a, x + 1, y + 1, 14, 1, mul(STONE_L, tone))
            wrect(a, x + 1, y + 7, 15, 1, mul(STONE_D, 1.1))
            wrect(a, x, y, 1, 8, STONE_D)
            wrect(a, x, y, 16, 1, STONE_D)
            # Скруглённые углы глыбы.
            wpx(a, x + 1, y + 1, STONE_D), wpx(a, x + 15, y + 1, STONE_D)
            for _ in range(3):
                px, py = x + a.rng.randrange(3, 14), y + a.rng.randrange(3, 7)
                wpx(a, px, py, STONE_D), wpx(a, px + 1, py + 1, mul(STONE_L, tone))
            if a.rng.random() < 0.35:
                cx, cy = x + a.rng.randrange(3, 10), y + a.rng.randrange(3, 5)
                for k in range(a.rng.randrange(3, 6)):
                    wpx(a, cx + k, cy + (k // 2), CLAY_D if k % 3 else LAVA)
    ammonite(a, 12, 20, 3, BONE_D, STONE_D)
    ammonite(a, 44, 51, 2, BONE_D, STONE_D)
    for _ in range(110):
        wpx(a, a.rng.randrange(64), a.rng.randrange(64), STONE_D if a.rng.random() < 0.5 else STONE_L)
    for _ in range(14):
        x, y = a.rng.randrange(64), a.rng.randrange(8) * 8
        wrect(a, x, y, a.rng.randrange(2, 6), 1, LEAF)
        wpx(a, x + 1, y + 1, LEAF_D), wpx(a, x, y - 1, LEAF_L)
    a.noise(0, 0, 64, 64, 0.07)
    return a


def tex_sail():
    """Растянутая шкура: тёплый рыжий ворс, тёмные пятна, шов из жил посередине и по краю, блики."""
    a = lm.Atlas(32, 32, 339)
    hide, hide_d, hide_l = rgb("D8843C"), rgb("A4521E"), rgb("F0B060")
    for y in range(32):
        for x in range(32):
            k = 1.0 + 0.08 * math.sin(x * math.pi / 8.0 + 1.5 * math.sin(y * math.pi / 16.0)) \
                + 0.05 * math.sin(y * math.pi / 4.0)
            a.px(x, y, mul(hide, k))
    # Ворс: короткие косые штрихи.
    for _ in range(70):
        x, y = a.rng.randrange(32), a.rng.randrange(32)
        c = hide_d if a.rng.random() < 0.5 else hide_l
        wpx(a, x, y, c), wpx(a, x + 1, y + 1, c)
    # Пятна: неровные овалы с тёмной серединой.
    for cx, cy, rx, ry in ((7, 6, 3, 2), (23, 9, 2, 3), (12, 19, 2, 2), (26, 24, 3, 2), (5, 27, 2, 2), (19, 28, 2, 1)):
        for y in range(-ry - 1, ry + 2):
            for x in range(-rx - 1, rx + 2):
                d = (x / (rx + 0.5)) ** 2 + (y / (ry + 0.5)) ** 2
                if d <= 1.0:
                    wpx(a, cx + x, cy + y, CLAY_DD if d < 0.5 else hide_d)
    # Швы: тёмная линия стыка шкур и поперечные стежки светлой жилой.
    for x0 in (0, 16):
        a.rect(x0, 0, 1, 32, hide_d)
        for y in range(1, 32, 4):
            wpx(a, x0 - 1, y, BONE), wpx(a, x0, y, BONE), wpx(a, x0 + 1, y, BONE)
            wpx(a, x0 - 1, y + 1, hide_d), wpx(a, x0 + 1, y + 1, hide_d)
    a.noise(0, 0, 32, 32, 0.06)
    return a


def tex_grass():
    """Подстилка джунглей: зелёные пятна тоном, травинки в два пикселя, листики папоротника,
    палая хвоя хвощей, проплешины глины и жёлтые спорангии."""
    a = lm.Atlas(64, 64, 341)
    for y in range(64):
        for x in range(64):
            k = 1.0 + 0.09 * math.sin(x * math.pi / 16.0 + 1.5 * math.sin(y * math.pi / 16.0)) \
                + 0.05 * math.sin((x - y) * math.pi / 8.0)
            a.px(x, y, mul(mix(LEAF, LEAF_D, 0.25), k))
    for _ in range(260):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        c = LEAF_D if a.rng.random() < 0.55 else LEAF_L
        wpx(a, x, y, c), wpx(a, x, y + 1, c)
    for _ in range(7):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wrect(a, x, y, 3, 2, CLAY_D)
        wpx(a, x + 1, y, CLAY), wpx(a, x + 3, y + 1, LEAF_D)
    for i in range(13):
        frond(a, a.rng.randrange(64), a.rng.randrange(64), LEAF_D, LEAF_L, right=(i % 2 == 0))
    for _ in range(12):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wpx(a, x, y, LAVA_L), wpx(a, x + 1, y + 1, LEAF_D)
    a.noise(0, 0, 64, 64, 0.07)
    return a


def tex_road():
    """Утоптанная тропа: светлая глина, вдавленные колеи от каменных колёс, плоские камни по
    краям, костяные вешки по оси, поперечные промоины и следы."""
    a = lm.Atlas(64, 64, 343)
    path, path_d, path_l = rgb("C88A5A"), rgb("94583A"), rgb("E4AE7C")
    for y in range(64):
        for x in range(64):
            k = 1.0 + 0.05 * math.sin(y * math.pi / 8.0 + x * math.pi / 32.0) + 0.03 * math.sin(x * math.pi / 4.0)
            a.px(x, y, mul(path, k))
    # Колеи там же, где у пиратов.
    for x in (18, 19, 44, 45):
        a.rect(x, 0, 1, 64, mul(path, 0.8))
    for x in (20, 46):
        a.rect(x, 0, 1, 64, mul(path, 1.12))
    for x in (17, 43):
        a.rect(x, 0, 1, 64, mul(path, 0.92))
    # Насечки от колёс-валунов поперёк колеи.
    for y in range(2, 64, 6):
        for x in (18, 44):
            wrect(a, x, y, 2, 1, path_d)
    # Промоины поперёк тропы.
    for y in (0, 32):
        for x in range(64):
            dy = int(round(1.2 * math.sin(x * math.pi / 8.0)))
            wpx(a, x, y + dy, path_d)
            wpx(a, x, y + dy + 1, path_l)
    # Плоские камни по краям.
    for x, y, w in ((2, 8, 5), (57, 20, 5), (3, 42, 4), (58, 52, 4), (8, 26, 3), (53, 38, 3)):
        wrect(a, x, y, w, 3, STONE)
        wrect(a, x, y, w, 1, STONE_L)
        wrect(a, x, y + 3, w, 1, path_d)
        wpx(a, x, y, path_d), wpx(a, x + w - 1, y + 2, STONE_D)
    # Костяные вешки по оси: вытянутые кости с утолщениями на концах.
    for y in (6, 38):
        a.rect(31, y + 1, 2, 10, BONE)
        a.rect(33, y + 1, 1, 10, BONE_D)
        for yy in (y, y + 10):
            a.rect(30, yy, 4, 2, BONE)
            a.px(33, yy + 1, BONE_D)
        a.rect(30, y + 12, 4, 1, path_d)
    for _ in range(160):
        wpx(a, a.rng.randrange(64), a.rng.randrange(64), path_d if a.rng.random() < 0.55 else path_l)
    footprint(a, 9, 16, path_d), footprint(a, 54, 46, path_d, flip=True)
    a.noise(0, 0, 64, 64, 0.06)
    return a


def tex_mud():
    """Смоляная яма: чёрно-бурая вязкая гладь с ленивыми разводами, пузыри с бликом, торчащие
    обломки костей. Заметно темнее тропы."""
    a = lm.Atlas(64, 64, 345)
    tar, tar_d, tar_l = rgb("2E1E1C"), rgb("180E0E"), rgb("54382E")
    for y in range(64):
        for x in range(64):
            w = math.sin((y + 5.0 * math.sin(x * math.pi / 16.0)) * math.pi / 8.0 + 2.0 * math.sin((x + y) * math.pi / 32.0))
            a.px(x, y, mul(tar, 1.0 + 0.2 * w))
            if w > 0.92:
                a.px(x, y, tar_l)
    for _ in range(11):
        cx, cy, r = a.rng.randrange(64), a.rng.randrange(64), a.rng.randrange(2, 5)
        for y in range(-r, r + 1):
            for x in range(-r, r + 1):
                d = math.hypot(x, y)
                if d <= r - 0.5:
                    wpx(a, cx + x, cy + y, tar_d)
                elif d <= r + 0.5:
                    wpx(a, cx + x, cy + y, tar_l if x + y < 0 else tar_d)
        wpx(a, cx - 1, cy - 1, rgb("8A6A52"))
    for _ in range(160):
        wpx(a, a.rng.randrange(64), a.rng.randrange(64), tar_l if a.rng.random() < 0.4 else tar_d)
    for _ in range(5):
        x, y = a.rng.randrange(64), a.rng.randrange(64)
        wpx(a, x, y, BONE_D), wpx(a, x + 1, y - 1, BONE_D), wpx(a, x + 2, y - 2, BONE), wpx(a, x + 1, y, tar_d)
    a.noise(0, 0, 64, 64, 0.08)
    return a


def tex_wind():
    """Разгонная полоса: жаркие жёлтые стрелки вперёд на прозрачном, текстура бежит по полосе."""
    a = lm.Atlas(32, 32, 347)
    white, pale = rgb("FFF8D0"), LAVA_L
    for row in (0, 16):
        for k in range(8):
            for x in (15 - k, 16 + k):
                a.px(x, row + 3 + k, white)
                a.px(x, row + 4 + k, pale)
                a.px(x, row + 5 + k, LAVA)
    return a


def tex_sky():
    """Панорама купола: бирюзовое дневное небо с дымкой у горизонта, облака, два вулкана с лавой
    и столбами дыма, шеи зауроподов над полосой джунглей. Плитка по горизонтали."""
    a = lm.Atlas(128, 64, 349)
    for y in range(64):
        t = min(y / 52.0, 1.0)
        c = mix(NAVY, SEA, min(t * 2.2, 1.0)) if t < 0.45 else mix(SEA, AQUA, (t - 0.45) / 0.3) if t < 0.75 \
            else mix(AQUA, HAZE, (t - 0.75) / 0.25)
        a.rect(0, y, 128, 1, c)
    # Дизеринг между полосами неба.
    for y in range(0, 52):
        for x in range(128):
            if (x + y) % 2 == 0 and a.rng.random() < 0.3:
                wpx(a, x, y, a.get(x, min(y + 2, 63))[:3])

    def cloud(cx, cy, rx, ry, col, shade):
        for y in range(-ry, ry + 1):
            for x in range(-rx, rx + 1):
                d = (x / (rx + 0.5)) ** 2 + (y / (ry + 0.5)) ** 2
                if d <= 1.0:
                    wpx(a, cx + x, cy + y, shade if y > ry * 0.25 else col)

    # Столбы дыма над вулканами: клубы, уходящие по ветру вправо.
    smoke, smoke_d = rgb("BCB09A"), rgb("8C8490")
    for i in range(7):
        cloud(30 + i * 4 + (i * i) // 3, 25 - i * 3, 3 + i // 2, 2 + i // 3, smoke, smoke_d)
    for i in range(5):
        cloud(98 + i * 3 + (i * i) // 3, 36 - i * 3, 2 + i // 2, 2, smoke, smoke_d)
    for cx, cy, rx, ry in ((70, 14, 9, 2), (112, 22, 7, 2), (8, 30, 8, 2), (60, 34, 6, 1)):
        cloud(cx, cy, rx, ry, rgb("F4EEDA"), HAZE)

    def volcano(cx, base, h, half, col, lit):
        """Конус с усечённой вершиной: левый склон светлее, из жерла течёт лава."""
        top = 3
        for j in range(h):
            y = base - h + j
            t = j / float(h - 1)
            w = top + (half - top) * (t ** 1.25)
            for x in range(int(-w), int(w) + 1):
                c = lit if x < -w * 0.25 else col
                if (x + j * 2) % 7 == 0 and j > 2:
                    c = mul(c, 0.86)
                wpx(a, cx + x, y, c)
        # Жерло и потёки лавы.
        for x in range(-top, top + 1):
            wpx(a, cx + x, base - h, LAVA_L if abs(x) < top else LAVA)
            wpx(a, cx + x, base - h - 1, LAVA if abs(x) < top - 1 else smoke_d)
        x = 0
        for j in range(1, int(h * 0.7)):
            if j % 3 == 0:
                x += 1 if (j // 3) % 2 else -1
            wpx(a, cx + x, base - h + j, LAVA_L if j < 4 else LAVA)
            wpx(a, cx + x + 1, base - h + j, LAVA)
        x = 2
        for j in range(1, int(h * 0.4)):
            if j % 2 == 0:
                x += 1
            wpx(a, cx + x, base - h + j, LAVA)

    volcano(30, 54, 26, 26, rgb("5A4A5E"), rgb("7C687A"))
    volcano(98, 54, 15, 17, rgb("4E5A72"), rgb("6C7C90"))
    # Дальняя гряда холмов между вулканами.
    for x in range(128):
        h = 3 + 2 * math.sin(x * math.pi / 16.0 + 0.6) + 1.5 * math.sin(x * math.pi / 8.0)
        h = max(1, int(h))
        a.rect(x, 54 - h, 1, h, mix(SEA, AQUA, 0.35))

    def sauropod(x0, base, h, flip=False):
        """Зауропод силуэтом: спина горбом над джунглями, длинная шея с наклоном вперёд,
        маленькая голова и хвост, уходящий в кроны."""
        s = -1 if flip else 1
        col, lit = NAVY, mix(NAVY, SEA, 0.55)
        for y in range(-4, 5):
            for x in range(-8, 9):
                if (x / 8.0) ** 2 + (y / 4.0) ** 2 <= 1.0:
                    wpx(a, x0 + s * x, base + y, lit if y == -4 or (y == -3 and abs(x) > 4) else col)
        # Шея: плотная линия шириной от трёх пикселей у плеч до двух у головы.
        steps = h * 3
        for k in range(steps + 1):
            t = k / float(steps)
            x = x0 + s * (5.0 + 5.0 * t + 2.0 * math.sin(t * math.pi))
            y = base - 2 - h * t
            for i in range(3 if t < 0.4 else 2):
                wpx(a, x - s * i, y, col)
        hx, hy = x0 + s * 10, base - 2 - h
        for i in range(-1, 4):
            wpx(a, hx + s * i, hy, col), wpx(a, hx + s * i, hy - 1, col if i < 3 else lit)
        wpx(a, hx + s, hy - 1, HAZE)
        # Хвост: сужается и опускается.
        for i in range(12):
            y = base - 1 + int(round(i * i / 36.0))
            wpx(a, x0 - s * (7 + i), y, col)
            if i < 7:
                wpx(a, x0 - s * (7 + i), y + 1, col)

    sauropod(63, 50, 13)
    sauropod(124, 51, 9, flip=True)
    # Полоса джунглей: кроны саговников и папоротников зубчатым краем, под ней земля.
    for x in range(128):
        h = 3 + 2 * abs(math.sin(x * math.pi / 4.0)) + 1.5 * math.sin(x * math.pi / 16.0)
        h = max(2, int(round(h)))
        a.rect(x, 56 - h, 1, h, SEA)
        a.px(x, 56 - h, mix(SEA, AQUA, 0.6))
        if x % 8 == 4:
            a.px(x, 56 - h - 1, SEA)
    a.rect(0, 56, 128, 8, LEAF_D)
    a.rect(0, 56, 128, 1, LEAF)
    for _ in range(36):
        wpx(a, a.rng.randrange(128), 57 + a.rng.randrange(7), LEAF if a.rng.random() < 0.5 else rgb("1C5030"))
    a.noise(0, 0, 128, 64, 0.03)
    return a


TEXTURES = {"sand": tex_sand, "planks": tex_planks, "water": tex_water, "rock": tex_rock, "sail": tex_sail,
            "grass": tex_grass, "road": tex_road, "mud": tex_mud, "wind": tex_wind, "sky": tex_sky}


def preview(path, scale=3):
    """Лист: каждая текстура плиткой 2×2 (швы видны посередине), подпись сверху."""
    from PIL import Image, ImageDraw
    cells = []
    for name, make in TEXTURES.items():
        im = make().im
        tile = Image.new("RGBA", (im.width * 2, im.height * 2), (0x1B, 0x1A, 0x33, 255))
        for ix in range(2):
            for iy in range(2):
                tile.alpha_composite(im, (ix * im.width, iy * im.height))
        tile = tile.resize((tile.width * scale, tile.height * scale), Image.NEAREST).convert("RGB")
        cell = Image.new("RGB", (tile.width + 8, tile.height + 20), (0x1B, 0x1A, 0x33))
        cell.paste(tile, (4, 16))
        ImageDraw.Draw(cell).text((4, 2), "tex_%s %dx%d" % (name, im.width, im.height), fill=(220, 225, 240))
        cells.append(cell)
    per = 4
    rows = [cells[i:i + per] for i in range(0, len(cells), per)]
    sheet = Image.new("RGB", (max(sum(c.width for c in r) for r in rows), sum(max(c.height for c in r) for r in rows)),
                      (0x1B, 0x1A, 0x33))
    y = 0
    for r in rows:
        x = 0
        for c in r:
            sheet.paste(c, (x, y))
            x += c.width
        y += max(c.height for c in r)
    sheet.save(path)
    print("лист: %s" % path)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        preview(sys.argv[sys.argv.index("--preview") + 1])
