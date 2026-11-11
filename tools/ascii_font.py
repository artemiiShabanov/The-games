#!/usr/bin/env python3
"""Атлас глифов ASCII-демок (#88) из GNU Unifont: узкие глифы 8×16 нужных блоков Unicode.

Unifont: https://unifoundry.com/pub/unifont/ (папка font-builds, файл unifont-<версия>.hex.gz),
лицензия SIL OFL 1.1 (`thegames/assets/fonts/unifont/LICENSE.txt`). Сам .hex в репозиторий не
кладётся, в репозитории только результат:

  thegames/assets/fonts/unifont/glyphs.png      белые глифы на прозрачном, 64 в ряд
  thegames/scripts/demos/ascii_codepoints.gd    порядок кодов в атласе

  gunzip unifont-17.0.05.hex.gz
  python3 tools/ascii_font.py unifont-17.0.05.hex
  /Applications/Godot.app/Contents/MacOS/Godot --headless --path thegames --import

Широкие глифы (16 px, например ⛵) не берутся: клетка ASCII-экрана одна на символ.
"""
import os
import struct
import sys
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PNG_OUT = os.path.join(ROOT, "thegames/assets/fonts/unifont/glyphs.png")
GD_OUT = os.path.join(ROOT, "thegames/scripts/demos/ascii_codepoints.gd")
PER_ROW = 64
CELL_W, CELL_H = 8, 16

RANGES = [
    (0x20, 0x7E),      # ASCII
    (0xA0, 0xFF),      # Latin-1
    (0x391, 0x3C9),    # греческий: Ω, Π, Ψ, Φ
    (0x400, 0x45F),    # кириллица
    (0x2010, 0x2044),  # пунктуация: † ‡ • …
    (0x2190, 0x21FF),  # стрелки
    (0x2219, 0x221E),  # ∙ √ ∞
    (0x2248, 0x2248),  # ≈
    (0x2260, 0x2265),  # ≠ ≡ ≤ ≥
    (0x2302, 0x2302),  # ⌂
    (0x2500, 0x259F),  # рамки и блоки
    (0x25A0, 0x25FF),  # геометрия
    (0x2600, 0x26FF),  # символы: ☠ ☺ ♠ ⚑
]


def load_hex(path):
    glyphs = {}
    with open(path, encoding="ascii") as f:
        for line in f:
            cp, bits = line.strip().split(":")
            glyphs[int(cp, 16)] = bits
    return glyphs


def png(path, width, height, rgba_rows):
    raw = b"".join(b"\x00" + row for row in rgba_rows)

    def chunk(kind, data):
        c = struct.pack(">I", len(data)) + kind + data
        return c + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)))
        f.write(chunk(b"IDAT", zlib.compress(raw, 9)))
        f.write(chunk(b"IEND", b""))


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    glyphs = load_hex(sys.argv[1])
    codes = []
    for lo, hi in RANGES:
        for cp in range(lo, hi + 1):
            bits = glyphs.get(cp)
            if bits is not None and len(bits) == 32:
                codes.append(cp)
    rows_n = (len(codes) + PER_ROW - 1) // PER_ROW
    w, h = PER_ROW * CELL_W, rows_n * CELL_H
    pix = [bytearray(w * 4) for _ in range(h)]
    for i, cp in enumerate(codes):
        bits = glyphs[cp]
        ox, oy = (i % PER_ROW) * CELL_W, (i // PER_ROW) * CELL_H
        for r in range(CELL_H):
            byte = int(bits[r * 2:r * 2 + 2], 16)
            for c in range(CELL_W):
                if byte >> (7 - c) & 1:
                    p = (ox + c) * 4
                    pix[oy + r][p:p + 4] = b"\xff\xff\xff\xff"
    os.makedirs(os.path.dirname(PNG_OUT), exist_ok=True)
    png(PNG_OUT, w, h, [bytes(r) for r in pix])
    lines = []
    for i in range(0, len(codes), 16):
        lines.append("\t" + ", ".join("0x%04X" % c for c in codes[i:i + 16]) + ",")
    with open(GD_OUT, "w", encoding="utf-8") as f:
        f.write("class_name AsciiCodepoints\n")
        f.write("## Порядок кодов в атласе `assets/fonts/unifont/glyphs.png`, %d в ряд, клетка 8×16.\n" % PER_ROW)
        f.write("## Сгенерировано `tools/ascii_font.py`, руками не править.\n\n")
        f.write("const PER_ROW := %d\n" % PER_ROW)
        f.write("const CODES: Array[int] = [\n%s\n]\n" % "\n".join(lines))
    print("глифов %d, атлас %d×%d" % (len(codes), w, h))


if __name__ == "__main__":
    main()
