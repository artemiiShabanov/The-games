#!/usr/bin/env python3
"""Просмотр мешей без Godot (#136): грубый рендер моделей генераторов в PNG, чтобы смотреть
форму и раскладку атласа до записи в проект. Ортографический вид в три четверти и вид сбоку,
буфер глубины, текстура ближайшим соседом, свет по нормали грани.

    import mesh_preview
    mesh_preview.save_models("out.png", [model, ...])        # `lowpoly_meshes.Model`
    mesh_preview.save_rigs("out.png", [(rig, color), ...])   # `rig_models.Rig` и картинка цвета

    python3 tools/mesh_preview.py out.png            # проверка на наборе пиратов
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BACK = (0x1B, 0x1A, 0x33)
LIGHT = np.array([-0.45, 0.75, 0.5])
LIGHT = LIGHT / np.linalg.norm(LIGHT)


def _view(yaw, pitch):
    cy, sy = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)
    turn = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    tilt = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]])
    return tilt @ turn


def render(tris, image, size=220, yaw=0.6, pitch=0.35):
    """`tris`: список (три вершины xyz, три точки развёртки в долях 0..1). Картинка `size`×`size`."""
    out = np.zeros((size, size, 3), dtype=np.uint8)
    out[:] = BACK
    if not tris:
        return Image.fromarray(out)
    tex = np.asarray(image.convert("RGBA"))
    th, tw = tex.shape[:2]
    m = _view(yaw, pitch)
    pts = np.array([[m @ np.array(v, dtype=float) for v in t[0]] for t in tris])
    uvs = np.array([t[1] for t in tris], dtype=float)
    lo = pts.reshape(-1, 3).min(axis=0)
    hi = pts.reshape(-1, 3).max(axis=0)
    span = max(hi[0] - lo[0], hi[1] - lo[1], 1e-6)
    scale = (size - 16) / span
    mid = (lo + hi) / 2.0
    depth = np.full((size, size), -1e9)
    for p, uv in zip(pts, uvs):
        x = (p[:, 0] - mid[0]) * scale + size / 2.0
        y = size / 2.0 - (p[:, 1] - mid[1]) * scale
        n = np.cross(p[1] - p[0], p[2] - p[0])
        ln = np.linalg.norm(n)
        if ln < 1e-12:
            continue
        shade = 0.55 + 0.45 * abs(float((n / ln) @ (m @ LIGHT)))
        x0, x1 = max(int(math.floor(x.min())), 0), min(int(math.ceil(x.max())), size - 1)
        y0, y1 = max(int(math.floor(y.min())), 0), min(int(math.ceil(y.max())), size - 1)
        if x0 > x1 or y0 > y1:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        den = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
        if abs(den) < 1e-9:
            continue
        a = ((y[1] - y[2]) * (gx - x[2]) + (x[2] - x[1]) * (gy - y[2])) / den
        b = ((y[2] - y[0]) * (gx - x[2]) + (x[0] - x[2]) * (gy - y[2])) / den
        c = 1.0 - a - b
        inside = (a >= -1e-6) & (b >= -1e-6) & (c >= -1e-6)
        z = a * p[0, 2] + b * p[1, 2] + c * p[2, 2]
        u = np.clip(((a * uv[0, 0] + b * uv[1, 0] + c * uv[2, 0]) * tw).astype(int), 0, tw - 1)
        v = np.clip(((a * uv[0, 1] + b * uv[1, 1] + c * uv[2, 1]) * th).astype(int), 0, th - 1)
        texel = tex[v, u]
        win = depth[y0:y1 + 1, x0:x1 + 1]
        hit = inside & (z > win) & (texel[..., 3] > 40)
        win[hit] = z[hit]
        out[y0:y1 + 1, x0:x1 + 1][hit] = np.clip(texel[..., :3][hit] * shade, 0, 255).astype(np.uint8)
    return Image.fromarray(out)


def _row(name, tris, image, size):
    """Три четверти спереди, сбоку, сзади и сам атлас."""
    row = Image.new("RGB", (size * 4, size + 14), BACK)
    for i, (yaw, pitch) in enumerate(((0.6, 0.3), (math.pi / 2, 0.05), (math.pi + 0.6, 0.3))):
        row.paste(render(tris, image, size, yaw, pitch), (i * size, 14))
    atlas = image.convert("RGB").resize((size - 16, size - 16), Image.NEAREST)
    row.paste(atlas, (3 * size + 8, 22))
    ImageDraw.Draw(row).text((4, 1), "%s  %d tris" % (name, len(tris)), fill=(220, 225, 240))
    return row


def _stack(path, rows):
    sheet = Image.new("RGB", (max(r.width for r in rows), sum(r.height for r in rows)), BACK)
    y = 0
    for r in rows:
        sheet.paste(r, (0, y))
        y += r.height
    sheet.save(path)
    print("лист: %s" % path)


def save_models(path, models, size=200):
    """Лист моделей `lowpoly_meshes.Model`: модель смотрит в −Z, камера спереди справа."""
    rows = []
    for m in models:
        tris = [(t[0], t[1]) for part in m.parts for t in part[3]]
        # Модель смотрит в −Z: разворачиваем к камере.
        tris = [([(-v[0], v[1], -v[2]) for v in vs], uv) for vs, uv in tris]
        rows.append(_row(m.name, tris, m.atlas.im, size))
    _stack(path, rows)


def save_rigs(path, rigs, size=260):
    """Лист моделей на скелете: `rigs` это пары (`rig_models.Rig`, картинка цвета)."""
    rows = []
    for rig, color in rigs:
        tris = [([tuple(-c if k != 1 else c for k, c in enumerate(rig.verts[i])) for i in t], [rig.uvs[i] for i in t])
                for t in rig.tris]
        rows.append(_row(rig.name, tris, color, size))
    _stack(path, rows)


if __name__ == "__main__":
    import lowpoly_meshes as lm
    out = sys.argv[1] if len(sys.argv) > 1 else "mesh_preview.png"
    save_models(out, [make() for make in lm.SETS["pirates"]["models"][:4]])
