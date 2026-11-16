#!/usr/bin/env python3
"""Набор «Сладости» для 8-bit (#137): общая часть модулей `sweets8_<демка>.py`. Палитра своя, по
мотивам `sweets16.PALETTE`: K чёрный (горький шоколад), W белая глазурь, зефир и сахар,
G пряник, вафля и карамель, R красный мармелад и бант, P розовая глазурь и сахарная вата.
Карты как у пиратов: строка на ряд пикселей, символ это цвет, точка прозрачна. Модуль демки
отдаёт словарь `SPRITES` с пиратскими именами слотов.

    python3 tools/sweets8.py --preview out.png   # все готовые модули одним листом
"""
import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PALETTE = {
    "K": (0x1E, 0x10, 0x16),  # чёрный: горький шоколад, обводка
    "W": (0xFF, 0xF7, 0xEC),  # глазурь героя, зефир, сахар, блики
    "G": (0xC9, 0x80, 0x3E),  # пряник, вафля, бисквит, карамель
    "R": (0xE6, 0x35, 0x45),  # мармеладный мишка, бант, полосы леденцов
    "P": (0xFF, 0x8E, 0xB6),  # розовая глазурь, сахарная вата, фантики
}
MODULES = ("sweets8_platformer", "sweets8_racing", "sweets8_shooter", "sweets8_golf", "sweets8_fight")

# Небо демок 8-bit и вектора (поля `SettingDef`), цвета RGB 0..255. Пастельный день карамельной
# страны: мятная синева сверху, к горизонту мятный крем; светило это карамельный диск.
SKY_BANDS = (
    (0x6F, 0xC3, 0xD6),
    (0x82, 0xCF, 0xD6),
    (0x96, 0xDA, 0xD6),
    (0xA9, 0xE4, 0xD8),
    (0xBC, 0xEC, 0xDC),
    (0xCB, 0xF2, 0xE1),
    (0xD9, 0xF7, 0xE8),
)
SUN = (0xFF, 0xD9, 0x7A)              # карамельное солнце
HORIZON = (0xF2, 0x7C, 0xA8)          # розовый сироп у горизонта
HORIZON_LIGHT = (0xFF, 0xC9, 0xDC)    # блики на сиропе
SILHOUETTE = (0x8F, 0xD6, 0xBE)       # дальние горы мятного мороженого
SILHOUETTE_DARK = (0x4F, 0xB0, 0xA2)  # ближние холмы мятной карамели
# Вектор: фон, мир, акцент, опасность. На шоколадной черноте карамельный луч, сливочно-розовый
# акцент, малиновый у врагов.
VECTOR_COLORS = (
    (0x10, 0x07, 0x0B),
    (0xFF, 0xC6, 0x4A),
    (0xFF, 0xE8, 0xF2),
    (0xFF, 0x2E, 0x5C),
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
