#!/usr/bin/env python3
"""Сетка 3×2 из шести кадров в один JPEG (для `setting_shots.sh`): кадры уменьшаются до 640×360
через `sips`, склейка своя, без внешних библиотек; JPEG пишет тоже `sips`.

    python3 tools/shots_sheet.py out.jpg a.png b.png c.png d.png e.png f.png
"""
import os
import struct
import subprocess
import sys
import tempfile
import zlib

W, H = 640, 360


def read_png(path):
    """RGB-строки PNG без чересстрочности (8 бит, RGB или RGBA)."""
    data = open(path, "rb").read()
    pos, chunks, head = 8, b"", None
    while pos < len(data):
        size, kind = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + size]
        if kind == b"IHDR":
            head = struct.unpack(">IIBBBBB", body)
        elif kind == b"IDAT":
            chunks += body
        pos += 12 + size
    w, h, depth, color = head[0], head[1], head[2], head[3]
    bpp = {2: 3, 6: 4}[color]
    raw = zlib.decompress(chunks)
    stride = w * bpp
    rows, prev = [], bytearray(stride)
    for y in range(h):
        f = raw[y * (stride + 1)]
        line = bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        for i in range(stride):
            a = line[i - bpp] if i >= bpp else 0
            b = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            if f == 1:
                line[i] = (line[i] + a) & 255
            elif f == 2:
                line[i] = (line[i] + b) & 255
            elif f == 3:
                line[i] = (line[i] + (a + b) // 2) & 255
            elif f == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        prev = line
        rows.append(bytes(line[i] for x in range(w) for i in (x * bpp, x * bpp + 1, x * bpp + 2)) if bpp == 4 else bytes(line))
    return w, h, rows


def main():
    out, shots = sys.argv[1], sys.argv[2:8]
    tmp = tempfile.mkdtemp()
    grid = [bytearray(b"\x14\x14\x1c" * (W * 3)) for _ in range(H * 2)]
    for i, path in enumerate(shots):
        if not os.path.exists(path):
            continue
        small = os.path.join(tmp, "%d.png" % i)
        subprocess.run(["sips", "-z", str(H), str(W), path, "--out", small], capture_output=True, check=True)
        w, h, rows = read_png(small)
        ox, oy = (i % 3) * W, (i // 3) * H
        for y in range(min(h, H)):
            grid[oy + y][ox * 3:(ox + min(w, W)) * 3] = rows[y][:min(w, W) * 3]
    raw = b"".join(b"\x00" + bytes(r) for r in grid)

    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", W * 3, H * 2, 8, 2, 0, 0, 0)) + \
        chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b"")
    big = os.path.join(tmp, "sheet.png")
    open(big, "wb").write(png)
    subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "85", big, "--out", out], capture_output=True, check=True)
    print("лист: %s" % out)


if __name__ == "__main__":
    main()
