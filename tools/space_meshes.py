#!/usr/bin/env python3
"""Набор «Космоса» для low poly и «продвинутых» (#136): собирает модели и текстуры уровня из
модулей `space_mesh_*.py` в том же виде, что `lowpoly_meshes.SETS["pirates"]`. Подключается из
`lowpoly_meshes.py` при запуске; плотный набор «продвинутых» получается из тех же описаний."""
import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _models():
    out = []
    for name in ("space_mesh_chars", "space_mesh_items", "space_mesh_big"):
        try:
            out.extend(importlib.import_module(name).MODELS)
        except ImportError:
            pass
    return out


def _textures():
    try:
        return dict(importlib.import_module("space_mesh_tex").TEXTURES)
    except ImportError:
        return {}


SET = {"models": _models(), "textures": _textures()}
