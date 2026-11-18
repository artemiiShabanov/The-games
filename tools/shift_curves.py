#!/usr/bin/env python3
"""Сдвиг кривых параметров мини-игры по `t` (баланс по оценкам, 2026-11-18).

    python3 tools/shift_curves.py <id> <d> [param ...] [--write]

Новая кривая new(t) = old(t + d): d > 0 делает мини-игру сложнее (на t 0,5 она становится
такой, какой была на 0,5 + d), d < 0 проще. За краями старой кривой значение продолжается
наклоном крайнего отрезка, доли (share, chance, double, shift, mirror, two_axes, tricky, hard,
flip) обрезаются в 0..1, остальное не уходит ниже нуля. Без `--write` только печатает.
"""
import re
import sys
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "thegames")
SHARES = ("share", "chance", "double", "shift", "mirror", "two_axes", "tricky", "hard", "flip")


def f(pts, x):
    if x <= pts[0][0]:
        (x0, y0), (x1, y1) = pts[0], pts[1]
    elif x >= pts[-1][0]:
        (x0, y0), (x1, y1) = pts[-2], pts[-1]
    else:
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            if x0 <= x <= x1:
                break
    if x1 == x0:
        return y1
    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)


def shifted(pts, d, name):
    out = [(0.0, f(pts, d))]
    for x, y in pts:
        if 0.0 < x - d < 1.0:
            out.append((round(x - d, 4), y))
    out.append((1.0, f(pts, 1.0 + d)))
    lo, hi = (0.0, 1.0) if any(k in name for k in SHARES) else (0.0, float("inf"))
    return [(x, round(min(max(y, lo), hi), 4)) for x, y in out]


def fmt(v):
    return ("%g" % v) if v != int(v) else "%d" % v


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    write = "--write" in sys.argv
    mid, d, only = args[0], float(args[1]), args[2:]
    path = os.path.join(ROOT, "resources", "minigames", mid + ".tres")
    s = open(path, encoding="utf-8").read()
    params = dict(re.findall(r'&"(\w+)": SubResource\("([^"]+)"\)', s))
    for name, sid in params.items():
        if only and name not in only:
            continue
        m = re.search(r'(\[sub_resource type="Curve" id="%s"\]\n)(.*?)(?=\n\[|\Z)' % re.escape(sid), s, re.S)
        body = m.group(2)
        pts = [(float(a), float(b)) for a, b in re.findall(r"Vector2\(([-\d.e]+), ([-\d.e]+)\)", body)]
        if len(pts) < 2:
            pts = pts * 2 if pts else [(0.0, 0.0), (1.0, 0.0)]
        new = shifted(pts, d, name)
        print("%-14s %s -> %s" % (name, [(fmt(x), fmt(y)) for x, y in pts], [(fmt(x), fmt(y)) for x, y in new]))
        if not write:
            continue
        data = ", ".join("Vector2(%s, %s), 0.0, 0.0, 0, 0" % (fmt(x), fmt(y)) for x, y in new)
        nb = re.sub(r"_data = \[.*?\]\n", "_data = [%s]\n" % data, body, flags=re.S)
        nb = re.sub(r"point_count = \d+", "point_count = %d" % len(new), nb)
        lim = re.search(r"_limits = \[([-\d.e]+), ([-\d.e]+), ([-\d.e]+), ([-\d.e]+)\]", nb)
        if lim:
            lo = min(float(lim.group(1)), min(y for _, y in new))
            hi = max(float(lim.group(2)), max(y for _, y in new))
            nb = nb.replace(lim.group(0), "_limits = [%s, %s, %s, %s]" % (fmt(lo), fmt(hi), lim.group(3), lim.group(4)))
        s = s[:m.start(2)] + nb + s[m.end(2):]
    if write:
        open(path, "w", encoding="utf-8").write(s)


if __name__ == "__main__":
    main()
