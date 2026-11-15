#!/usr/bin/env python3
"""Сборка наборов сеттингов из модулей-зеркал (#136, #137): у сеттинга `<id>` модули называются
`<id>8.py` и `<id>8_<демка>.py` (8-bit), `<id>16.py` и `<id>_<демка>16.py` (16/32),
`<id>_mesh_chars|items|big|tex.py` (low poly и «продвинутые»), `<id>_rig_chars|tex.py` (на
скелете). Генераторы берут отсюда список сеттингов и собранные наборы; модуля нет: его слоты
просто не пишутся, и проверка полноты (`check_settings.py`) покажет, чего не хватает."""
import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Сеттинги с наборами в модулях; пираты живут в самих генераторах.
IDS = ("space", "castles", "zombies", "superheroes", "fantasy", "sweets", "ninja", "dinosaurs", "office")


def module(name):
    try:
        return importlib.import_module(name)
    except ModuleNotFoundError as e:
        if e.name != name:
            raise
        return None


def const(mod, suffix):
    """Палитра слоя по окончанию имени (`SPACE_BG`, `CASTLES_BG`): зеркала называют её по-своему."""
    for key in dir(mod):
        if key.isupper() and key.endswith(suffix):
            return getattr(mod, key)
    raise AttributeError("%s: нет константы *%s" % (mod.__name__, suffix))


def mesh_set(setting):
    """Набор low poly в виде `lowpoly_meshes.SETS[...]` или None, когда модулей нет."""
    models = []
    for part in ("chars", "items", "big"):
        mod = module("%s_mesh_%s" % (setting, part))
        if mod:
            models.extend(mod.MODELS)
    tex = module("%s_mesh_tex" % setting)
    if not models and not tex:
        return None
    return {"models": models, "textures": dict(tex.TEXTURES) if tex else {}}


def rig_set(setting):
    """(модели на скелете, крупные текстуры) или None."""
    chars = module("%s_rig_chars" % setting)
    tex = module("%s_rig_tex" % setting)
    if not chars and not tex:
        return None
    return (list(chars.RIGS) if chars else [], dict(tex.PROPS) if tex else {})
