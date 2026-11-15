#!/usr/bin/env python3
"""Модели на скелете и крупные текстуры «Космоса» для «продвинутых» (#136): собирает
`space_rig_chars.RIGS` и `space_rig_tex.PROPS` в том же виде, что `rig_models.SETS` и `PROPS`.
Подключается из `rig_models.py` при запуске."""
import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _take(module, attr, empty):
    try:
        return getattr(importlib.import_module(module), attr)
    except ImportError:
        return empty


RIGS = list(_take("space_rig_chars", "RIGS", []))
PROPS = dict(_take("space_rig_tex", "PROPS", {}))
