#!/usr/bin/env python3
"""Фоны карточек конструктора (полировка 2026-11-17): жанр, технология, сеттинг.

Картинки собираются из готовых ассетов игры, своего арта здесь нет:
- сеттинг: коллаж его ассетов из разных технологий (спрайты 8-bit и 16/32, модели low poly)
  наклейками на поле цвета сеттинга;
- технология: кадр одного и того же платформера (замки) в рендере этой технологии;
- жанр: кадр игры этого жанра в 16/32, сведённый к двум тонам цвета жанра, чтобы карточка
  читалась жанром, а не сеттингом.
Кадры технологий и жанров это снимки демок: `--capture` переснимает их через автотест (нужно
окно Godot) в `thegames/debug/playtest/cards/`. Низ карточки притемнён под подпись, углы
скруглены в самой картинке.

    python3 tools/card_art.py                 # собрать thegames/assets/cards/*.png
    python3 tools/card_art.py --capture       # сначала переснять кадры демок
    python3 tools/card_art.py --preview x.png # лист всех карточек, в проект не пишет
"""
import os
import subprocess
import sys

from PIL import Image, ImageChops, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_DIR = os.path.join(ROOT, "thegames", "assets", "settings")
FRAMES = os.path.join(ROOT, "thegames", "debug", "playtest", "cards")
OUT = os.path.join(ROOT, "thegames", "assets", "cards")

# Карточка 260×190 показывается до 1,37× и на экранах двойной плотности: картинка втрое.
SIZE = (780, 570)
RADIUS = 72
ASPECT = SIZE[0] / SIZE[1]

# Улица битемапа (карточка жанра «Файтинг»): левый край окна, пиксели арта.
STREET_TOP = 34
STREET_H = 330
STREET_X = {
    "pirates": 0, "space": 0, "castles": 250, "zombies": 330, "superheroes": 330,
    "fantasy": 560, "sweets": 0, "ninja": 320, "dinosaurs": 560, "office": 330,
}
FIGHTER = (96, 112)
FEET_Y = 322

# Технология: кадр платформера на замках и окно в нём (экран 1920×1080: x, y, ширина).
TECH_SHOTS = {
    "vector": ("plat_vector", 600, 300, 800),
    "bit8": ("plat_bit8", 520, 300, 760),
    "bit16": ("plat_bit16", 400, 262, 860),
    "lowpoly": ("plat_lowpoly", 600, 215, 900),
    "threed": ("plat_threed", 330, 270, 930),
}
# Жанр: кадр демки 16/32 и окно в нём; файтинг собирается из ассетов, как сеттинг.
GENRE_SHOTS = {
    "platformer": ("plat_bit16", 380, 330, 720),
    "racing": ("g_racing", 500, 300, 925),
    "shooter": ("g_shooter", 605, 330, 711),
    "sport": ("g_sport", 735, 355, 420),
}
GENRE_COLORS = {
    "platformer": (232, 185, 58), "racing": (224, 69, 123), "shooter": (43, 179, 122),
    "sport": (240, 122, 28), "fighting": (142, 68, 173),
}
# Что снять для `--capture`: имя кадра и аргументы тестовой сцены демки.
CAPTURES = [
    ("plat_vector", "--tech=vector --freeze=7 --frames=640"),
    ("plat_bit8", "--tech=bit8 --freeze=7 --frames=640"),
    ("plat_bit16", "--tech=bit16 --freeze=7 --frames=640"),
    ("plat_lowpoly", "--tech=lowpoly --freeze=7 --frames=640"),
    ("plat_threed", "--tech=threed --freeze=7 --frames=640"),
    ("g_racing", "--genre=racing --tech=bit16 --freeze=9 --frames=760"),
    ("g_shooter", "--genre=shooter --tech=bit16 --freeze=9 --frames=760"),
    ("g_sport", "--genre=sport --tech=bit16 --freeze=9 --frames=760"),
]


def capture():
    os.makedirs(FRAMES, exist_ok=True)
    for name, args in CAPTURES:
        env = dict(os.environ, SHOT=f"debug/playtest/cards/{name}.png")
        cmd = ["sh", os.path.join(ROOT, "tools", "autotest.sh"), "--scene=demo_test", "--setting=2", "--no-checks"] + args.split()
        code = subprocess.run(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode
        print(("ok   " if code == 0 else "FAIL ") + name)


def sprite(setting, name):
    return Image.open(os.path.join(SETTINGS_DIR, setting, "16bit", name + ".png")).convert("RGBA")


def fighter(setting, name, frame, flip=False):
    sheet = sprite(setting, name)
    img = sheet.crop((frame * FIGHTER[0], 0, (frame + 1) * FIGHTER[0], FIGHTER[1]))
    return img.transpose(Image.FLIP_LEFT_RIGHT) if flip else img


def street_scene(setting, hero_frame=0, foe_frame=0, hit=False):
    """Окно в улицу сеттинга с героем и врагом лицом к лицу, в пикселях арта."""
    w = round(STREET_H * ASPECT)
    street = sprite(setting, "brawl_street")
    x0 = min(STREET_X[setting], street.width - w)
    scene = street.crop((x0, STREET_TOP, x0 + w, STREET_TOP + STREET_H))
    feet = FEET_Y - STREET_TOP
    hero_x = round(w * 0.60) if not hit else round(w * 0.52)
    foe_x = round(w * 0.84) if not hit else round(w * 0.70)
    for img, cx in [(fighter(setting, "brawl_thug", foe_frame, True), foe_x), (fighter(setting, "brawl_hero", hero_frame), hero_x)]:
        shadow = Image.new("RGBA", scene.size, (0, 0, 0, 0))
        ImageDraw.Draw(shadow).ellipse((cx - 26, feet - 7, cx + 26, feet + 5), fill=(0, 0, 0, 70))
        scene.alpha_composite(shadow)
        scene.alpha_composite(img, (cx - FIGHTER[0] // 2, feet - FIGHTER[1] + 2))
    if hit:
        fx = sprite(setting, "brawl_fx_hit")
        spark = fx.crop((40, 0, 80, 40))
        scene.alpha_composite(spark, ((hero_x + foe_x) // 2 - 6, feet - 78))
    # Пиксели арта остаются пикселями: сначала вдвое ближайшим соседом, потом к размеру.
    return scene.resize((scene.width * 2, scene.height * 2), Image.NEAREST).resize(SIZE, Image.LANCZOS)


def setting_color(setting):
    """Цвет сеттинга из каталога конструктора."""
    import re
    text = open(os.path.join(ROOT, "thegames", "resources", "catalog", "settings.tres"), encoding="utf-8").read()
    m = re.search(r'id = &"%s".*?color = Color\(([^)]*)\)' % setting, text, re.S)
    return tuple(round(float(v) * 255) for v in m.group(1).split(",")[:3])


def sprite8(setting, name):
    return Image.open(os.path.join(SETTINGS_DIR, setting, "8bit", name + ".png")).convert("RGBA")


def model3d(setting, name, size, yaw=0.6, pitch=0.3):
    """Модель low poly сеттинга грубым рендером без Godot (`mesh_preview`), фон прозрачный."""
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import numpy as np
    import lowpoly_meshes as lm
    import mesh_preview
    import setting_sets
    if setting == "pirates":
        make = getattr(lm, "pirate_" + name)
    else:
        make = next(f for f in setting_sets.mesh_set(setting)["models"] if f.__name__.endswith("_" + name))
    m = make()
    tris = [([(-v[0], v[1], -v[2]) for v in t[0]], t[1]) for part in m.parts for t in part[3]]
    img = mesh_preview.render(tris, m.atlas.im, size, yaw, pitch).convert("RGBA")
    px = np.asarray(img).copy()
    px[(px[..., :3] == np.array(mesh_preview.BACK)).all(axis=-1), 3] = 0
    return Image.fromarray(px)


def stick(canvas, img, center, scale=1.0, angle=0.0, flip=False):
    """Наклейка на коллаж: пиксели ближайшим соседом, поворот, мягкая тень."""
    from PIL import ImageFilter
    if flip:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    img = img.resize((max(1, round(img.width * scale)), max(1, round(img.height * scale))), Image.NEAREST)
    if angle:
        img = img.rotate(angle, Image.BICUBIC, expand=True)
    x, y = round(center[0] - img.width / 2), round(center[1] - img.height / 2)
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    dark = Image.new("RGBA", img.size, (0, 0, 0, 255))
    dark.putalpha(img.getchannel("A").point(lambda v: v * 90 // 255))
    shadow.paste(dark, (x + 8, y + 12), dark)
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(7)))
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    layer.paste(img, (x, y), img)
    canvas.alpha_composite(layer)


def collage(setting):
    """Коллаж сеттинга: его ассеты из разных технологий наклейками на поле цвета сеттинга.
    Ретро (8-bit) крупными пикселями, 2D (16/32) спрайтами, 3D моделями low poly."""
    color = setting_color(setting)
    canvas = Image.new("RGBA", SIZE, color + (255,))
    glow = Image.new("L", SIZE, 0)
    ImageDraw.Draw(glow).ellipse((120, -60, 900, 520), fill=70)
    from PIL import ImageFilter
    light = Image.new("RGBA", SIZE, (255, 255, 255, 255))
    light.putalpha(glow.filter(ImageFilter.GaussianBlur(120)))
    canvas.alpha_composite(light)
    frame = lambda sheet, w, h, i=0: sheet.crop((i * w, 0, (i + 1) * w, h))
    stick(canvas, sprite(setting, "palm"), (96, 250), 1.9, 6)
    stick(canvas, model3d(setting, "cart", 300, 0.9), (300, 190), 1.0, -6)
    stick(canvas, frame(sprite(setting, "brawl_boss"), 144, 136), (668, 268), 2.4, -4, True)
    stick(canvas, model3d(setting, "hero", 250), (236, 400), 1.0, 5)
    stick(canvas, frame(sprite(setting, "brawl_hero"), 96, 112), (478, 322), 3.2, 3)
    stick(canvas, sprite8(setting, "hero_run_0"), (430, 96), 6, -10)
    stick(canvas, sprite8(setting, "enemy_0"), (566, 92), 5, 8)
    stick(canvas, sprite8(setting, "coin"), (176, 84), 5, -8)
    stick(canvas, frame(sprite(setting, "coin"), 32, 32), (724, 86), 2.6, 10)
    stick(canvas, sprite(setting, "chest"), (716, 492), 3.2, -5)
    stick(canvas, sprite8(setting, "flag"), (88, 476), 5, 8)
    return canvas


def shot(name, x, y, w):
    path = os.path.join(FRAMES, name + ".png")
    if not os.path.exists(path):
        sys.exit(f"нет кадра {path}: запусти с --capture")
    frame = Image.open(path).convert("RGBA")
    k = frame.width / 1920.0
    box = tuple(round(v * k) for v in (x, y, x + w, y + w / ASPECT))
    return frame.crop(box).resize(SIZE, Image.LANCZOS)


def duotone(img, color):
    """Два тона цвета жанра: тени тёмным, середина самим цветом, света почти белым."""
    lum = img.convert("L")
    lo, hi = lum.getextrema()
    span = max(hi - lo, 1)
    dark = tuple(round(c * 0.22) for c in color)
    light = tuple(round(c + (255 - c) * 0.82) for c in color)
    table = []
    for ch in range(3):
        for v in range(256):
            t = min(max((v - lo) / span, 0.0), 1.0)
            if t < 0.5:
                table.append(round(dark[ch] + (color[ch] - dark[ch]) * t * 2.0))
            else:
                table.append(round(color[ch] + (light[ch] - color[ch]) * (t - 0.5) * 2.0))
    return Image.merge("RGB", [lum.point(table[i * 256:(i + 1) * 256]) for i in range(3)]).convert("RGBA")


def finish(img):
    """Притемнить низ под подпись и скруглить углы."""
    img = img.convert("RGBA")
    shade = Image.new("L", (1, SIZE[1]))
    for y in range(SIZE[1]):
        t = max(0.0, (y / SIZE[1] - 0.45) / 0.55)
        shade.putpixel((0, y), round(205 * t * t * (3 - 2 * t)))
    dark = Image.new("RGBA", SIZE, (16, 14, 24, 255))
    dark.putalpha(shade.resize(SIZE))
    img.alpha_composite(dark)
    mask = Image.new("L", (SIZE[0] * 2, SIZE[1] * 2), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, SIZE[0] * 2 - 1, SIZE[1] * 2 - 1), RADIUS * 2, fill=255)
    img.putalpha(ImageChops.multiply(img.getchannel("A"), mask.resize(SIZE, Image.LANCZOS)))
    return img


def build():
    cards = {}
    for setting in STREET_X:
        cards["setting_" + setting] = finish(collage(setting))
    for tech, (name, x, y, w) in TECH_SHOTS.items():
        cards["tech_" + tech] = finish(shot(name, x, y, w))
    for genre, (name, x, y, w) in GENRE_SHOTS.items():
        cards["genre_" + genre] = finish(duotone(shot(name, x, y, w), GENRE_COLORS[genre]))
    cards["genre_fighting"] = finish(duotone(street_scene("castles", 19, 16, True), GENRE_COLORS["fighting"]))
    return cards


def preview(cards, path):
    names = sorted(cards)
    cols = 5
    cell = (SIZE[0] // 2, SIZE[1] // 2)
    sheet = Image.new("RGB", (cols * (cell[0] + 12) + 12, ((len(names) + cols - 1) // cols) * (cell[1] + 12) + 12), (244, 241, 236))
    for i, name in enumerate(names):
        small = cards[name].resize(cell, Image.LANCZOS)
        sheet.paste(small, (12 + (i % cols) * (cell[0] + 12), 12 + (i // cols) * (cell[1] + 12)), small)
    sheet.save(path)
    print("лист:", path)


def main():
    args = sys.argv[1:]
    if "--capture" in args:
        capture()
    cards = build()
    if "--preview" in args:
        preview(cards, args[args.index("--preview") + 1])
        return
    os.makedirs(OUT, exist_ok=True)
    for name, img in cards.items():
        img.save(os.path.join(OUT, name + ".png"))
    print(f"карточек {len(cards)}: {OUT}")


if __name__ == "__main__":
    main()
