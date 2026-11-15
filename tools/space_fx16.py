#!/usr/bin/env python3
"""Мелкие эффекты «Космоса» для 16/32 (#136): тот же приём, что у пиратов (`pixel_fx16.py`),
свои цвета: пыль реголита, бирюзовые искры кристалла, плазменная вспышка, синий выхлоп."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pixel_fx16 as fx  # noqa: E402
from pixel_brawl16 import Pal  # noqa: E402


def fx_pal():
    p = Pal(0x12101A)
    p.add("white", [0xB8C8E0, 0xDCE6F4, 0xF4F8FF, 0xFFFFFF])
    # «gold» и «fire» это роли в рисунках пиратов: искры подбора и огонь; здесь энергия и плазма.
    p.add("gold", [0x1C5A8A, 0x2FA8D8, 0x7FE3F0, 0xE8FFFF])
    p.add("dust", [0x4A4A5E, 0x74768C, 0xA0A4B8, 0xCCD0DE])
    p.add("fire", [0x3A1C8A, 0x6A4AE0, 0x6FC8F8, 0xF0FFFF])
    return p


def sprites_own():
    p = fx_pal()
    return {
        "fx16_dust": (fx.dust(p), p.colors),
        "fx16_spark": (fx.spark(p), p.colors),
        "fx16_star": (fx.star(p), p.colors),
        "fx16_flash": (fx.flash(p), p.colors),
        "fx16_fire": (fx.fire(p), p.colors),
    }


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import space16
        space16.save_sheet(sys.argv[sys.argv.index("--preview") + 1], sprites_own())
