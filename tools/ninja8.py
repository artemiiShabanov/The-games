#!/usr/bin/env python3
"""Набор «Ниндзя» для 8-bit (#137): общая часть модулей `ninja8_<демка>.py`. Палитра своя, по
мотивам `ninja16.PALETTE`: K чёрный, B синий костюм героя (он же черепица, камень и ворон),
R красный шарф и чужой клан (лак, фонари, солнце знамени), W белые обмотки, сталь и бумага,
Y золото заката (монета, дерево, бамбук, огонь фонаря). Карты как у пиратов: строка на ряд
пикселей, символ это цвет, точка прозрачна. Модуль демки отдаёт словарь `SPRITES` с пиратскими
именами слотов.

    python3 tools/ninja8.py --preview out.png   # все готовые модули одним листом
"""
import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PALETTE = {
    "K": (0x12, 0x10, 0x18),  # чёрный
    "B": (0x40, 0x54, 0xB4),  # костюм героя, черепица, камень, ворон-тэнгу
    "R": (0xD9, 0x36, 0x32),  # шарф, чужой клан, лак, бумажный фонарь, солнце знамени
    "W": (0xF3, 0xEE, 0xE2),  # обмотки, сталь, бумага, облака, кожа в прорези капюшона
    "Y": (0xF0, 0xB8, 0x4C),  # монета, дерево и бамбук, огонь, закатный свет
}
MODULES = ("ninja8_platformer", "ninja8_racing", "ninja8_shooter", "ninja8_golf", "ninja8_fight")

# Небо демок 8-bit и вектора (поля `SettingDef`), цвета RGB 0..255. Закат над прудом: сверху
# индиго, ниже слива, у горизонта приглушённый коралл; небо держится темнее спрайтов, чтобы
# синий герой и красный клан не тонули. Светило это низкое бледно-золотое солнце.
SKY_BANDS = (
    (0x16, 0x16, 0x3C),
    (0x22, 0x1C, 0x4A),
    (0x36, 0x22, 0x58),
    (0x52, 0x2A, 0x60),
    (0x7A, 0x36, 0x5E),
    (0xA8, 0x4A, 0x54),
    (0xD0, 0x6C, 0x4C),
)
SUN = (0xFB, 0xDC, 0x92)              # солнце у горизонта
HORIZON = (0x14, 0x18, 0x38)          # тёмный пруд
HORIZON_LIGHT = (0xE9, 0x7B, 0x52)    # коралловые блики на воде
SILHOUETTE = (0x3A, 0x22, 0x50)       # горы в тумане
SILHOUETTE_DARK = (0x1E, 0x14, 0x34)  # замок на утёсе, ближние сосны
# Вектор: фон, мир, акцент, опасность. Лунно-синий луч туши, золотой акцент, красный клан.
VECTOR_COLORS = (
    (0x08, 0x06, 0x12),
    (0x8A, 0xB0, 0xFF),
    (0xFF, 0xE4, 0x9A),
    (0xFF, 0x40, 0x48),
)


def sprites():
    """Слоты всех готовых модулей демок."""
    out = {}
    for name in MODULES:
        try:
            out.update(importlib.import_module(name).SPRITES)
        except ImportError:
            pass
    return out


def save_sheet(path, items, scale=6, per_line=10, bg=(0x1B, 0x1A, 0x33, 255)):
    """Лист для просмотра: спрайты как в игре (с обводкой персонажей), `per_line` в ряд."""
    import pixel_sprites as ps
    names = list(items)
    chunks = [names[i:i + per_line] for i in range(0, len(names), per_line)]
    line_h = [max(len(items[n]) for n in chunk) * scale + 8 for chunk in chunks]
    width = max(sum(len(items[n][0]) * scale + 8 for n in chunk) for chunk in chunks) + 8
    canvas = [list(bg) * width for _ in range(sum(line_h) + 8)]
    oy = 4
    for line, chunk in enumerate(chunks):
        ox = 4
        for name in chunk:
            # Обводка как у космоса: те же исключения (дэш героя без обводки).
            w, h, px = ps.render(ps.outlined("space", name, items[name]), scale, PALETTE)
            for y in range(h):
                for x in range(w):
                    p = px[y][x * 4:x * 4 + 4]
                    if p[3]:
                        canvas[oy + y][(ox + x) * 4:(ox + x) * 4 + 4] = p
            ox += w + 8
        oy += line_h[line]
    with open(path, "wb") as f:
        f.write(ps.png_bytes(width, len(canvas), canvas))
    print("лист: %s" % path)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        save_sheet(sys.argv[sys.argv.index("--preview") + 1], sprites())
