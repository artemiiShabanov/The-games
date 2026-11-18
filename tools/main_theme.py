#!/usr/bin/env python3
"""Заглавная тема Studio Running (2026-11-18): главное меню и главный экран забега.

Ориентиры Артемия: современный интерактивный музей, тайский массаж, загадочно, транс.
Ми минор с тайской пентатоникой, 108 ударов в минуту, петля 32 такта без шва:
одна и та же фраза на ранате (деревянный ксилофон) с тремоло на длинных нотах, гонг кхонг-вонг
на смене аккордов, тёплый пад, тянущийся бас, транс-арпеджио шестнадцатыми. По просьбе Артемия
тема ровная: без развития мелодии по частям и без ударных.
Кирпичи синтеза общие с музыкой демок (`tools/music.py`).

    python3 tools/main_theme.py            # thegames/assets/music/main_theme.ogg
    python3 tools/main_theme.py --preview  # и mp3 на две петли в debug/playtest/music/
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import music as M  # noqa: E402

SR = M.SR
TAU = M.TAU
BPM = 108.0
S16 = 60.0 / BPM / 4      # шестнадцатая
BARS = 32
STEPS = BARS * 16
N = int(round(STEPS * S16 * SR))

# Аккорды по два такта: Em7, Cmaj7, D(add9), Bm7; бас и тоны пада в MIDI.
CHORDS = [
    (40, [52, 55, 59, 62]),
    (36, [48, 52, 55, 59]),
    (38, [50, 54, 57, 64]),
    (35, [47, 50, 54, 57]),
]

# Мелодия на восемь тактов: (такт, шестнадцатая, длина в шестнадцатых, нота).
PHRASE = [
    (0, 0, 2, "B4"), (0, 2, 2, "E5"), (0, 4, 1, "G5"), (0, 5, 1, "A5"), (0, 6, 4, "B5"),
    (0, 10, 2, "A5"), (0, 12, 2, "G5"), (0, 14, 2, "E5"),
    (1, 0, 3, "D5"), (1, 3, 1, "E5"), (1, 4, 4, "G5"), (1, 8, 6, "E5"),
    (2, 0, 2, "E5"), (2, 2, 2, "G5"), (2, 4, 2, "B5"), (2, 6, 2, "D6"), (2, 8, 4, "B5"),
    (2, 12, 2, "A5"), (2, 14, 2, "G5"),
    (3, 0, 6, "A5"), (3, 6, 2, "G5"), (3, 8, 8, "E5"),
    (4, 0, 2, "D5"), (4, 2, 2, "F#5"), (4, 4, 2, "A5"), (4, 6, 2, "B5"), (4, 8, 2, "A5"),
    (4, 10, 2, "F#5"), (4, 12, 2, "E5"), (4, 14, 2, "D5"),
    (5, 0, 4, "E5"), (5, 4, 2, "D5"), (5, 6, 2, "B4"), (5, 8, 8, "D5"),
    (6, 0, 2, "B4"), (6, 2, 2, "D5"), (6, 4, 4, "F#5"), (6, 8, 2, "E5"), (6, 10, 2, "D5"),
    (6, 12, 4, "B4"),
    (7, 0, 4, "A4"), (7, 4, 12, "B4"),
]


class Loop:
    def __init__(self):
        self.buf = np.zeros(N)

    def add(self, step, sig, gain=1.0, dt=0.0):
        """С шестнадцатой `step` (дробной можно), хвост за концом петли уходит в начало."""
        i = int(round((step * S16 + dt) * SR)) % N
        idx = (i + np.arange(len(sig))) % N
        np.add.at(self.buf, idx, sig * gain)


def t_of(n):
    return np.arange(n) / SR


def ranat(freq, seconds=1.2, vel=1.0):
    """Ранат: деревянная пластина, неровные обертоны гаснут быстро, щелчок колотушки."""
    n = int(seconds * SR)
    t = t_of(n)
    body = np.sin(TAU * freq * t) * np.exp(-t * 5.5)
    body += 0.45 * np.sin(TAU * freq * 3.93 * t) * np.exp(-t * 16)
    body += 0.18 * np.sin(TAU * freq * 9.4 * t) * np.exp(-t * 38)
    click = np.random.default_rng(int(freq)).standard_normal(n) * np.exp(-t * 400) * 0.25
    out = (body + M.lowpass(click, 4000)) * vel
    out[: int(0.002 * SR)] *= np.linspace(0, 1, int(0.002 * SR))
    return out


def gong(freq, seconds=3.5):
    """Кхонг-вонг: бронзовый гонг с биением, мягкая атака."""
    n = int(seconds * SR)
    t = t_of(n)
    out = np.zeros(n)
    for ratio, amp, dec in ((1.0, 1.0, 1.1), (1.003, 0.6, 1.2), (2.0, 0.35, 1.8), (2.76, 0.3, 2.4), (5.4, 0.1, 5.0)):
        out += amp * np.sin(TAU * freq * ratio * t) * np.exp(-t * dec)
    att = int(0.012 * SR)
    out[:att] *= np.linspace(0, 1, att)
    return out


def pad(midis, seconds):
    n = int(seconds * SR)
    sig = np.zeros(n)
    for m in midis:
        sig += M.supersaw(M.hz(m), n, 3, 0.006, 0.003)
        sig += 0.5 * np.sin(TAU * M.hz(m) * t_of(n))
    sig = M.lowpass_note(sig, 1100)
    return sig * M.adsr(n, 1.2, 0.5, 0.9, 1.0)


def arp_note(freq, cutoff, seconds):
    n = int(seconds * SR)
    ph = M.phase(freq, n)
    sig = 0.6 * M.saw(ph) + 0.4 * M.pulse(ph * 1.003, 0.3)
    return M.lowpass_note(sig, cutoff) * M.adsr(n, 0.003, 0.06, 0.35, 0.03)


def bass_note(freq, seconds):
    n = int(seconds * SR)
    ph = M.phase(freq, n)
    sig = np.sin(TAU * ph) + 0.35 * M.tri(ph * 2)
    return M.lowpass_note(sig, 400) * M.adsr(n, 0.004, 0.08, 0.6, 0.04)


def compose():
    mel, bells, pads, arps, bass = (Loop() for _ in range(5))
    rng = np.random.default_rng(5)

    for bar in range(BARS):
        root, tones = CHORDS[(bar // 2) % 4]
        if bar % 2 == 0:
            pads.add(bar * 16, pad(tones, 2 * 16 * S16 + 1.0), 0.05)
            bells.add(bar * 16, gong(M.hz(root + 24), 4.0), 0.14)
            bass.add(bar * 16, bass_note(M.hz(root), 32 * S16), 0.2)
        # Транс-арпеджио: тоны аккорда шестнадцатыми вверх-вниз, фильтр стоит на месте.
        order = tones + [tones[2] + 12, tones[1] + 12] + tones[::-1][1:3]
        for s in range(16):
            m = order[s % len(order)] + 12
            vel = 0.7 + 0.3 * (s % 4 == 0)
            arps.add(bar * 16 + s, arp_note(M.hz(m), 1500.0, S16 * 0.9), 0.05 * vel)

    # Мелодия: одна и та же фраза ранатом на всю петлю, без развития.
    for rep in range(BARS // 8):
        for bar, st, length, name in PHRASE:
            m = M.midi(name)
            step = rep * 128 + bar * 16 + st
            dt = rng.uniform(-0.005, 0.005)
            vel = rng.uniform(0.82, 1.0)
            if length >= 4:
                # Тайское тремоло: длинная нота перекатом шестнадцатыми, тише к концу.
                for k in range(length):
                    mel.add(step + k, ranat(M.hz(m), 0.6, vel * (1.0 - 0.5 * k / length)), 0.22, dt)
            else:
                mel.add(step, ranat(M.hz(m), 1.2, vel), 0.26, dt)

    music = M.reverb(mel.buf, 2.6, 0.45, 41, 5000.0)
    music += M.reverb(bells.buf, 4.0, 0.6, 42, 3500.0)
    music += M.reverb(M.echo(arps.buf, 3 * S16, 0.3, 3), 1.6, 0.3, 43, 4500.0)
    music += M.reverb(pads.buf, 3.0, 0.5, 44, 3000.0)
    music += bass.buf
    music -= np.mean(music)
    music *= 0.8 / (np.max(np.abs(music)) + 1e-9)
    return M.limit(music)


def main():
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "thegames")
    mix = compose()
    print("тема:", M.stats(mix), "длина %.1f с" % (N / SR))
    M.save(mix, os.path.join(root, "assets", "music", "main_theme.ogg"))
    if "--preview" in sys.argv:
        M.save(mix, os.path.join(root, "debug", "playtest", "music", "main_theme.mp3"), 1.0, 2)


if __name__ == "__main__":
    main()
