#!/usr/bin/env python3
"""Полнота набора сеттинга (#135, docs/specs/settings.md).

Полный набор это все файлы набора пиратов в каждом формате плюс свои палитры. Скрипт сравнивает
папки `thegames/assets/settings/<id>/` с пиратской и раскладывает недостающее по семействам.

  python3 tools/check_settings.py            # сводка по всем сеттингам
  python3 tools/check_settings.py space      # чего не хватает космосу, по семействам
  python3 tools/check_settings.py --check    # ci: у сеттингов с `complete = true` всё своё
  python3 tools/check_settings.py --complete # номера готовых сеттингов кроме пиратов, для матрицы
"""
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "thegames")
ASSETS = os.path.join(ROOT, "assets", "settings")
DEFS = os.path.join(ROOT, "resources", "settings")
FORMATS = ["8bit", "16bit", "lowpoly", "threed", "rig"]
FORMAT_NAMES = {"8bit": "8-bit", "16bit": "16/32", "lowpoly": "low poly", "threed": "продвинутые",
                "rig": "на скелете"}
# Палитры и цвета в ресурсе сеттинга: без своих берутся пиратские.
PALETTES = {"sky_bands": "небо 8-bit", "vector_colors": "луч вектора", "bit16_colors": "палитра 16/32",
            "lowpoly_colors": "цвета HUD low poly"}
# Окружение 3D (#147): свои блоки света, неба и основания мира.
ENVS = {"env_lowpoly": "окружение low poly", "env_threed": "окружение продвинутых"}
# Семейства из спеки: первое подошедшее правило. Что не подошло, уходит в «прочее».
FAMILIES = {
    "8bit": [
        ("герой", r"^(hero_|shoot_hero_|golf_hero_|fight_hero_)"),
        ("соперник-боец", r"^fight_rival_"),
        ("враги", r"^(enemy_|parrot_|shoot_gunner_)"),
        ("транспорт", r"^(boat_|rival_)"),
        ("тайлы мира", r"^(ground|platform|race_(sand|water|shallow|finish)|shoot_(deck|rail|plank)|golf_(deck|hull|sand|sea))"),
        ("эффекты", r"^(fight_spark|fight_guard|golf_splash|shoot_puff)"),
        ("предметы и пропы", r""),
    ],
    "16bit": [
        ("герой", r"^(hero_|cart_hero|soccer_hero|soccer_keeper_hero|brawl_hero|pistol)"),
        ("лица HUD", r"^(face|brawl_face_)"),
        ("эффекты", r"^(fx16_|brawl_fx_|brawl_go)"),
        ("враги и соперники", r"^(crab_|parrot_|enemy_|skel_|cut_|cart_\d|soccer_rival_|soccer_keeper_rival|brawl_(thug|knife|boss))"),
        ("фоны и параллакс", r"^(par_|par3_|road_(sky|sea|islands|colors)|brawl_street|soccer_(field|out|grass))"),
        ("стены, полы, почва", r"^(wall_|floor_|ceiling_|ground|trail_)"),
        ("декор", r"^(dec_|arch_|canopy_|palm|road_(hut|rock|barrel)|rock|sign_|hold_decor)"),
        ("предметы", r""),
    ],
    "lowpoly": [
        ("текстуры уровня", r"^tex_"),
        ("персонажи", r"^(hero|enemy|captain)(_n)?\."),
        ("транспорт", r"^cart"),
        ("реквизит", r""),
    ],
    "rig": [("персонажи", r"")],
}
FAMILIES["threed"] = FAMILIES["lowpoly"]


def files(setting, fmt):
    folder = os.path.join(ASSETS, setting, fmt)
    if not os.path.isdir(folder):
        return set()
    return {f for f in os.listdir(folder)
            if not f.endswith((".import", ".uid", ".md")) and not f.startswith("README")}


def settings():
    """id → (номер `Game.Setting`, complete, текст ресурса)."""
    out = {}
    for f in sorted(os.listdir(DEFS)):
        if not f.endswith(".tres"):
            continue
        text = open(os.path.join(DEFS, f), encoding="utf-8").read()
        number = int((re.search(r"^setting = (\d+)", text, re.M) or [0, 0])[1])
        out[f[:-5]] = (number, bool(re.search(r"^complete = true", text, re.M)), text)
    return out


def missing(setting, known):
    """формат → семейство → недостающие файлы; плюс недостающие палитры."""
    out = {}
    for fmt in FORMATS:
        own = files(setting, fmt)
        for f in sorted(files("pirates", fmt)):
            # Поля футбола лежат у пиратов под именем сеттинга: чужие не нужны, своё считается своим.
            m = re.match(r"soccer_(field|out)_([a-z]+)\.", f)
            if m:
                if m[2] != "pirates":
                    continue
                f = f.replace("pirates", setting)
                if f in own or f in files("pirates", fmt):
                    continue
            if f in own:
                continue
            family = next(name for name, rule in FAMILIES[fmt] if re.search(rule, f))
            out.setdefault(fmt, {}).setdefault(family, []).append(f)
    text = known[setting][2]
    palettes = [label for key, label in PALETTES.items()
                if not re.search(r"^%s = .*Color\(" % key, text, re.M)]
    if not re.search(r"^tones = Dictionary", text, re.M):
        palettes.append("тона рисунка из кода")
    if not re.search(r"^words = Dictionary", text, re.M):
        palettes.append("слова подписей")
    palettes += [label for key, label in ENVS.items() if not re.search(r"^%s = SubResource" % key, text, re.M)]
    return out, palettes


def count(tree):
    return sum(len(v) for fam in tree.values() for v in fam.values())


def main():
    args = sys.argv[1:]
    known = settings()
    if "--complete" in args:
        print(" ".join(str(known[s][0]) for s in known if known[s][1] and s != "pirates"))
        return 0
    if "--check" in args:
        status = 0
        for s in known:
            if not known[s][1] or s == "pirates":
                continue
            tree, palettes = missing(s, known)
            if count(tree) or palettes:
                print("FAIL %s помечен готовым, но не хватает %d файлов, %d палитр и окружений"
                      % (s, count(tree), len(palettes)))
                status = 1
        ready = [s for s in known if known[s][1]]
        print("готовые сеттинги: %s" % ", ".join(ready))
        return status
    names = [a for a in args if not a.startswith("--")]
    if not names:
        total = {fmt: len(files("pirates", fmt)) for fmt in FORMATS}
        print("%-10s %s  палитры и окружение" % ("сеттинг", "  ".join("%-12s" % FORMAT_NAMES[f] for f in FORMATS)))
        for s in known:
            tree, palettes = missing(s, known)
            cells = []
            for fmt in FORMATS:
                lack = sum(len(v) for v in tree.get(fmt, {}).values())
                cells.append("%-12s" % ("%d/%d" % (total[fmt] - lack, total[fmt])))
            print("%-10s %s  %s" % (s, "  ".join(cells), "все" if not palettes else "нет: " + ", ".join(palettes)))
        return 0
    for s in names:
        if s not in known:
            print("нет сеттинга %s, есть: %s" % (s, ", ".join(known)))
            return 1
        tree, palettes = missing(s, known)
        print("%s: не хватает %d файлов" % (s, count(tree)))
        for fmt in FORMATS:
            for family, lack in tree.get(fmt, {}).items():
                print("  %-12s %-20s %3d  %s" % (FORMAT_NAMES[fmt], family, len(lack), " ".join(
                    sorted({os.path.splitext(f)[0] for f in lack}))))
        if palettes:
            print("  палитры и окружение: нет своих: %s" % ", ".join(palettes))
    return 0


if __name__ == "__main__":
    sys.exit(main())
