#!/usr/bin/env python3
"""Спрайты 8-bit из текстовых карт по сеттингам: «Пираты» здесь, «Космос» и «Замки» в
pixel_sets_extra.py (#47). Тайлы 16×16, палитра сеттинга 4 цвета плюс чёрный, одинаковые слоты.
Пишет PNG в thegames/assets/settings/<сеттинг>/8bit/ и превью-лист (×8) всех наборов в --preview.

    python3 tools/pixel_sprites.py                 # сгенерировать все наборы
    python3 tools/pixel_sprites.py --preview out.png

Карты правятся прямо здесь: символ = цвет палитры, точка = прозрачно. После правки:
Godot --headless --path thegames --import.
"""
import os
import struct
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pixel_sets_extra  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Палитра «Пираты» для 8-bit: 4 цвета плюс чёрный.
PALETTE = {
    "K": (0x16, 0x14, 0x12),  # чёрный
    "B": (0x2F, 0x6F, 0xB5),  # море, полосы тельняшки
    "W": (0xF4, 0xEF, 0xE6),  # тельняшка, кости, череп
    "S": (0xF2, 0xC8, 0x5A),  # песок, кожа, дублон
    "R": (0xA8, 0x5A, 0x2A),  # дерево палубы, бандана
}

SPRITES = {
    "hero_run_0": [
        "................",
        ".....KKKKKK.....",
        "....KRRRRRRK....",
        "...KRRRRRRRRK...",
        "....KSSSSSSK....",
        "....KSKSSKSK....",
        "....KSSSSSSK....",
        ".....KSSSSK.....",
        "....KWWWWWWK....",
        "...KWBBBBBBWK...",
        "...KBWWWWWWBK...",
        "...KWBBBBBBWK...",
        "....KWWWWWWK....",
        "....KBBKKBBK....",
        "...KBBK..KBBK...",
        "...KKKK..KKKK...",
    ],
    "hero_run_1": [
        "................",
        ".....KKKKKK.....",
        "....KRRRRRRK....",
        "...KRRRRRRRRK...",
        "....KSSSSSSK....",
        "....KSKSSKSK....",
        "....KSSSSSSK....",
        ".....KSSSSK.....",
        "....KWWWWWWK....",
        "...KWBBBBBBWK...",
        "...KBWWWWWWBK...",
        "...KWBBBBBBWK...",
        "....KWWWWWWK....",
        "....KBBBBBBK....",
        ".....KBBBBK.....",
        ".....KKKKKK.....",
    ],
    "hero_run_2": [
        "................",
        ".....KKKKKK.....",
        "....KRRRRRRK....",
        "...KRRRRRRRRK...",
        "....KSSSSSSK....",
        "....KSKSSKSK....",
        "....KSSSSSSK....",
        ".....KSSSSK.....",
        "....KWWWWWWK....",
        "...KWBBBBBBWK...",
        "...KBWWWWWWBK...",
        "...KWBBBBBBWK...",
        "....KWWWWWWK....",
        "....KBBKKBBK....",
        "..KBBK....KBBK..",
        "..KKKK....KKKK..",
    ],
    "hero_jump": [
        "................",
        ".....KKKKKK.....",
        "....KRRRRRRK....",
        "...KRRRRRRRRK...",
        "....KSSSSSSK....",
        "....KSKSSKSK....",
        "....KSSSSSSK....",
        ".....KSSSSK.....",
        "..K.KWWWWWWK.K..",
        ".KSKWBBBBBBWKSK.",
        "..KKBWWWWWWBKK..",
        "...KWBBBBBBWK...",
        "....KWWWWWWK....",
        "....KBBKKBBK....",
        "...KBBK..KBBK...",
        "...KKK....KKK...",
    ],
    "hero_dash": [
        "................",
        "......KKKKKK....",
        ".....KRRRRRRK...",
        "..KKKKRRRRRRRK..",
        ".KRRK.KSSSSSSK..",
        "..KK..KSKSSKSK..",
        "......KSSSSSSK..",
        ".......KSSSSK...",
        "....KKKWWWWWWKK.",
        "...KSKWBBBBBBWSK",
        "....KKBWWWWWWBK.",
        "......KWBBBBBWK.",
        ".....KWWWWWWWK..",
        "...KBBBBKKBBBK..",
        ".KBBBBK...KBBK..",
        ".KKKKKK...KKKK..",
    ],
    "parrot_0": [
        "................",
        "................",
        "................",
        "......KK........",
        ".....KBBK.......",
        "....KBBBBK......",
        "....KBBBK.KK....",
        ".....KRRRKSSK...",
        "...KKRRKWRRKSK..",
        "..KBBRRRRRRK....",
        "..KBBKRRRRK.....",
        "...KK.KRRK......",
        ".......KK.......",
        "................",
        "................",
        "................",
    ],
    "parrot_1": [
        "................",
        "................",
        "................",
        "................",
        "................",
        "..........KK....",
        ".....KRRRKSSK...",
        "...KKRRKWRRKSK..",
        "..KBBRRRRRRK....",
        "..KBBKRRRRK.....",
        "...KKKBBBK......",
        ".....KBBBBK.....",
        "......KBBK......",
        ".......KK.......",
        "................",
        "................",
    ],
    "enemy_0": [
        "................",
        ".....KKKKKK.....",
        "....KWWWWWWK....",
        "...KWWWWWWWWK...",
        "...KWKKWWKKWK...",
        "...KWKKWWKKWK...",
        "...KWWWWWWWWK...",
        "....KWKWWKWK....",
        ".....KKKKKK.....",
        "......KWWK......",
        "...KKKWWWWKKK...",
        "..KWWKKWWKKWWK..",
        "..KKK.KWWK.KKK..",
        "......KWWK......",
        ".....KW..WK.....",
        ".....KK..KK.....",
    ],
    "enemy_1": [
        "................",
        ".....KKKKKK.....",
        "....KWWWWWWK....",
        "...KWWWWWWWWK...",
        "...KWKKWWKKWK...",
        "...KWKKWWKKWK...",
        "...KWWWWWWWWK...",
        "....KWKWWKWK....",
        ".....KKKKKK.....",
        "......KWWK......",
        "...KKKWWWWKKK...",
        "..KWWKKWWKKWWK..",
        "..KKK.KWWK.KKK..",
        "......KWWK......",
        "......KWWK......",
        "......KKKK......",
    ],
    "coin": [
        "................",
        "................",
        "................",
        "......KKKK......",
        ".....KSSSSK.....",
        "....KSWSSSSK....",
        "....KSSSKSSK....",
        "....KSSSKSSK....",
        "....KSSSKSSK....",
        "....KSSSSSSK....",
        ".....KSSSSK.....",
        "......KKKK......",
        "................",
        "................",
        "................",
        "................",
    ],
    "checkpoint": [
        "................",
        ".......KK.......",
        ".......KSKKK....",
        ".......KSSSSK...",
        ".......KSSSSSK..",
        ".......KSSSSK...",
        ".......KSKKK....",
        ".......KK.......",
        ".......KK.......",
        ".......KK.......",
        ".......KK.......",
        ".......KK.......",
        ".......KK.......",
        "......KRRK......",
        ".....KRRRRK.....",
        ".....KKKKKK.....",
    ],
    "flag": [
        ".....KK.........",
        ".....KKKKKKKKKK.",
        ".....KKWWWKKKKK.",
        ".....KKWKWKKKKK.",
        ".....KKWWWKKKKK.",
        ".....KKKWKKKKKK.",
        ".....KKWKWKKKKK.",
        ".....KKKKKKKKK..",
        ".....KK.........",
        ".....KK.........",
        ".....KK.........",
        ".....KK.........",
        ".....KK.........",
        "....KRRK........",
        "...KRRRRK.......",
        "...KKKKKK.......",
    ],
    "cloud_small": [
        "................",
        "................",
        "................",
        "................",
        "......KKKK......",
        ".....KWWWWK.....",
        "...KKWWWWWWKK...",
        "..KWWWWWWWWWWK..",
        "..KWWWWWWWWWWK..",
        "...KKKKKKKKKK...",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
    ],
    "cloud_big": [
        "................................",
        "................................",
        "................................",
        "..........KKKK..................",
        ".........KWWWWK.......KKKK......",
        ".......KKWWWWWWKK...KKWWWWKK....",
        ".....KKWWWWWWWWWWKKKWWWWWWWWK...",
        "...KKWWWWWWWWWWWWWWWWWWWWWWWWKK.",
        "..KWWWWWWWWWWWWWWWWWWWWWWWWWWWWK",
        "..KWWWWWWWWWWWWWWWWWWWWWWWWWWWWK",
        "...KKKKKKKKKKKKKKKKKKKKKKKKKKKK.",
        "................................",
        "................................",
        "................................",
        "................................",
        "................................",
    ],
    "ground": [
        "SSSSSSSSSSSSSSSS",
        "RRRRRRRRRRRRRRRR",
        "RRRRRRRRRRRRKRRR",
        "RRRRRRRRRRRRKRRR",
        "KKKKKKKKKKKKKKKK",
        "RRRRKRRRRRRRRRRR",
        "RRRRKRRRRRRRRRRR",
        "RRRRKRRRRRRRRRRR",
        "KKKKKKKKKKKKKKKK",
        "RRRRRRRRRKRRRRRR",
        "RRRRRRRRRKRRRRRR",
        "RRRRRRRRRKRRRRRR",
        "KKKKKKKKKKKKKKKK",
        "RKRRRRRRRRRRRRRR",
        "RKRRRRRRRRRRRRRR",
        "RKRRRRRRRRRRRRRR",
    ],
    "ground_inner": [
        "RRRRRRRRRRRRRRRR",
        "RRRRRRRRRRRRRRRR",
        "RRRRRRRRRRRRKRRR",
        "RRRRRRRRRRRRKRRR",
        "KKKKKKKKKKKKKKKK",
        "RRRRKRRRRRRRRRRR",
        "RRRRKRRRRRRRRRRR",
        "RRRRKRRRRRRRRRRR",
        "KKKKKKKKKKKKKKKK",
        "RRRRRRRRRKRRRRRR",
        "RRRRRRRRRKRRRRRR",
        "RRRRRRRRRKRRRRRR",
        "KKKKKKKKKKKKKKKK",
        "RKRRRRRRRRRRRRRR",
        "RKRRRRRRRRRRRRRR",
        "RKRRRRRRRRRRRRRR",
    ],
    "platform": [
        "SSSSSSSSSSSSSSSS",
        "RRRRRRRRRRRRRRRR",
        "RRRRRKRRRRRKRRRR",
        "RRRRRKRRRRRKRRRR",
        "KKKKKKKKKKKKKKKK",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
    ],
}


def png_bytes(width, height, rgba_rows):
    raw = b"".join(b"\x00" + bytes(row) for row in rgba_rows)

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")


def sets():
    """Наборы: имя папки сеттинга → (палитра, спрайты)."""
    return {
        "pirates": (PALETTE, SPRITES),
        "space": (pixel_sets_extra.SPACE_PALETTE, pixel_sets_extra.SPACE),
        "castles": (pixel_sets_extra.CASTLES_PALETTE, pixel_sets_extra.CASTLES),
    }


def render(rows, scale=1, palette=None):
    palette = palette or PALETTE
    h = len(rows)
    w = len(rows[0])
    out = []
    for y in range(h):
        assert len(rows[y]) == w, "строки разной длины"
        line = []
        for x in range(w):
            ch = rows[y][x]
            px = (0, 0, 0, 0) if ch == "." else palette[ch] + (255,)
            line.extend(px * scale)
        for _ in range(scale):
            out.append(line)
    return w * scale, h * scale, out


def main():
    all_sets = sets()
    for set_name, (palette, sprites) in all_sets.items():
        out = os.path.join(ROOT, "thegames", "assets", "settings", set_name, "8bit")
        os.makedirs(out, exist_ok=True)
        assert set(sprites) == set(SPRITES), "у %s не те слоты: %s" % (set_name, set(SPRITES) ^ set(sprites))
        for name, rows in sprites.items():
            w, h, px = render(rows, 1, palette)
            with open(os.path.join(out, name + ".png"), "wb") as f:
                f.write(png_bytes(w, h, px))
        print("%s: спрайтов %d в %s" % (set_name, len(sprites), os.path.relpath(out, ROOT)))
    if "--preview" in sys.argv:
        path = sys.argv[sys.argv.index("--preview") + 1]
        scale = 6
        names = list(SPRITES)
        cell = 32 * scale + 8
        width, height = len(names) * (16 * scale + 8) + 16 * scale, len(all_sets) * (16 * scale + 8)
        bg = (0xF4, 0xF1, 0xEC, 255)
        canvas = [list(bg) * width for _ in range(height)]
        for row, (set_name, (palette, sprites)) in enumerate(all_sets.items()):
            ox = 4
            for name in names:
                w, h, px = render(sprites[name], scale, palette)
                oy = row * (16 * scale + 8) + 4
                for y in range(h):
                    for x in range(w):
                        p = px[y][x * 4:x * 4 + 4]
                        if p[3]:
                            canvas[oy + y][(ox + x) * 4:(ox + x) * 4 + 4] = p
                ox += w + 8
        with open(path, "wb") as f:
            f.write(png_bytes(width, height, canvas))
        print("превью:", path)


if __name__ == "__main__":
    main()
