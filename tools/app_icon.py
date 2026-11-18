#!/usr/bin/env python3
"""Иконка окна и приложения Studio Running (2026-11-18): белый скруглённый квадрат, «SR» шрифтом
логотипа Nunito 900 и красная лампа над R, как точка над «ı». Пишет `thegames/icon.png` 512×512.

    python3 tools/app_icon.py [--preview out.png]   # превью с размерами 16, 32, 64
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "thegames")
FONT = os.path.join(ROOT, "assets", "fonts", "nunito", "Nunito-Variable.ttf")
BG = (255, 255, 255)
INK = (0x1C, 0x1B, 0x19)
ACCENT = (0xCB, 0x2F, 0x43)
SIZE = 512
SS = 4  # сглаживание: рисуем крупнее и уменьшаем


def draw() -> Image.Image:
    s = SIZE * SS
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pad = int(s * 0.04)
    d.rounded_rectangle((pad, pad, s - pad, s - pad), radius=int(s * 0.2), fill=BG + (255,),
                        outline=(0xEC, 0xE8, 0xE1, 255), width=int(s * 0.012))
    font = ImageFont.truetype(FONT, int(s * 0.5))
    font.set_variation_by_axes([900])
    text = "SR"
    track = -int(s * 0.02)
    ws = [d.textbbox((0, 0), ch, font=font) for ch in text]
    width = sum(r - l for l, _, r, _ in ws) + track
    l0, t, _, b = d.textbbox((0, 0), text, font=font)
    h = b - t
    x = (s - width) / 2
    y = (s - h) / 2 + int(s * 0.06) - t
    for ch, (l, _, r, _) in zip(text, ws):
        d.text((x - l, y), ch, font=font, fill=INK + (255,))
        x += r - l + track
    # Лампа над R, как точка над «ı» в логотипе.
    dot = int(s * 0.07)
    cx = s / 2 + width / 2 - dot * 0.6
    cy = (s - h) / 2 + int(s * 0.06) - dot * 1.9
    d.ellipse((cx - dot, cy - dot, cx + dot, cy + dot), fill=ACCENT + (255,))
    return img.resize((SIZE, SIZE), Image.LANCZOS)


def main() -> None:
    icon = draw()
    icon.save(os.path.join(ROOT, "icon.png"))
    if "--preview" in sys.argv:
        out = sys.argv[sys.argv.index("--preview") + 1]
        sheet = Image.new("RGBA", (512 + 64 + 32 + 16 + 80, 512), (0x3A, 0x3A, 0x3A, 255))
        sheet.paste(icon, (0, 0), icon)
        x = 532
        for n in (64, 32, 16):
            small = icon.resize((n, n), Image.LANCZOS)
            sheet.paste(small, (x, 20), small)
            x += n + 10
        sheet.save(out)


if __name__ == "__main__":
    main()
