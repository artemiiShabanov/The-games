#!/usr/bin/env python3
"""Набор «Зомби» для 8-bit (#137): общая часть модулей `zombies8_<демка>.py`. Палитра своя, по
мотивам `zombies16.PALETTE`: K чёрный, R красная куртка и кровь, G мёртвая кожа и зелёный
туман, W кость, луна и кожа выжившего, B синий сланец (бейсболка, джинсы, камень, ночь).
Карты как у пиратов: строка на ряд пикселей, символ это цвет, точка прозрачна. Модуль демки
отдаёт словарь `SPRITES` с пиратскими именами слотов.

    python3 tools/zombies8.py --preview out.png   # все готовые модули одним листом
"""
import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PALETTE = {
    "K": (0x12, 0x10, 0x14),  # чёрный
    "R": (0xD2, 0x3B, 0x2E),  # куртка выжившего, кровь, огонь, этикетки
    "G": (0x7F, 0xA8, 0x62),  # мёртвая кожа, туман, мох, флаг убежища
    "W": (0xEE, 0xEB, 0xDD),  # кость, луна, кожа выжившего, жесть, лохмотья
    "B": (0x4E, 0x62, 0x8C),  # бейсболка, джинсы, камень и плиты, ночные облака
}
MODULES = ("zombies8_platformer", "zombies8_racing", "zombies8_shooter", "zombies8_golf", "zombies8_fight")

# Небо демок 8-bit и вектора (поля `SettingDef`), цвета RGB 0..255. Ночь над кладбищем: тёмный
# верх, к горизонту синева с зеленью тумана; светило это луна.
SKY_BANDS = (
    (0x07, 0x0A, 0x1A),
    (0x0B, 0x10, 0x26),
    (0x10, 0x18, 0x32),
    (0x16, 0x21, 0x3F),
    (0x1D, 0x2C, 0x4A),
    (0x25, 0x39, 0x52),
    (0x30, 0x48, 0x58),
)
SUN = (0xEE, 0xEB, 0xDD)              # луна
HORIZON = (0x12, 0x22, 0x1E)          # болотная жижа у горизонта
HORIZON_LIGHT = (0x5C, 0x86, 0x58)    # блики зелёного тумана
SILHOUETTE = (0x16, 0x1E, 0x34)       # холм с часовней, пригород
SILHOUETTE_DARK = (0x0D, 0x12, 0x22)  # ближние кресты и мёртвые деревья
# Вектор: фон, мир, акцент, опасность. Ядовито-зелёный луч, лунный акцент, кровь у врагов.
VECTOR_COLORS = (
    (0x06, 0x05, 0x0E),
    (0xB4, 0xF0, 0x3C),
    (0xF2, 0xEE, 0xD8),
    (0xFF, 0x3B, 0x3B),
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
