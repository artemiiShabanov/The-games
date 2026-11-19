#!/usr/bin/env python3
"""Заглавная тема Studio Running: главное меню и главный экран забега.

Вторая версия (2026-11-19). Первая (ранат, гонг, тайская пентатоника) отдавала азиатским
акцентом сильнее, чем хотелось; из пяти вариантов (`tools/main_theme_variants.py`) Артемий
выбрал «Инсталляцию». Ориентиры: музыка залов музея современного искусства и кино, Ино, Сакамото.
Фа лидийский, 60 ударов в минуту, петля 16 тактов без шва и без пульса: стеклянный пад из чистых
тонов, редкие ноты пианино с войлоком и эхом, одна низкая нота в середине аккорда, тихий «воздух
зала». Тема ровная: одна фраза на восемь тактов повторяется, без развития и без ударных.
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
BPM = 60.0
S16 = 60.0 / BPM / 4      # шестнадцатая
BARS = 16
STEPS = BARS * 16
N = int(round(STEPS * S16 * SR))

# Аккорды по два такта: Fmaj9, Am7, Dm9, Cmaj7; бас и тоны пада в MIDI.
CHORDS = [
    (41, [57, 60, 64, 67]),
    (45, [55, 60, 64, 67]),
    (38, [53, 57, 60, 64]),
    (36, [55, 59, 64, 67]),
]

# Мелодия на восемь тактов: (такт, шестнадцатая, нота). Три ноты на аккорд, третья с опозданием.
PHRASE = [
    (0, 0, "E5"), (0, 8, "G5"), (1, 4, "B5"),
    (2, 0, "A5"), (2, 8, "E5"), (3, 4, "G5"),
    (4, 0, "F5"), (4, 8, "A5"), (5, 4, "E5"),
    (6, 0, "D5"), (6, 8, "G5"), (7, 4, "B4"),
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


def fade(sig, a, r):
    na, nr = min(int(a * SR), len(sig)), min(int(r * SR), len(sig))
    sig[:na] *= np.linspace(0, 1, na)
    sig[len(sig) - nr:] *= np.linspace(1, 0, nr)
    return sig


def felt(freq, seconds=5.0, vel=1.0):
    """Пианино с войлоком: мягкая атака, обертоны гаснут быстро, глухой стук молоточка."""
    n = int(seconds * SR)
    t = t_of(n)
    out = np.zeros(n)
    for k in range(1, 8):
        fk = freq * k * np.sqrt(1.0 + 0.0004 * k * k)
        if fk > 5000:
            break
        dec = (1.1 + 0.7 * k) * (freq / 260.0) ** 0.5
        out += np.sin(TAU * fk * t + k * 0.7) * np.exp(-t * dec) / k ** 1.9
    thump = np.random.default_rng(int(freq)).standard_normal(n) * np.exp(-t * 90)
    out += M.lowpass_note(thump, 450) * 0.5
    return fade(M.lowpass_note(out, 2400), 0.008, 0.08) * vel


def sine_pad(midis, seconds, attack=3.0, release=3.0):
    """Стеклянный пад из чистых тонов с медленным биением."""
    n = int(seconds * SR)
    t = t_of(n)
    sig = np.zeros(n)
    for i, m in enumerate(midis):
        f = M.hz(m)
        sig += np.sin(TAU * f * t) + 0.7 * np.sin(TAU * f * 1.0025 * t + i)
        sig += 0.15 * np.sin(TAU * 2 * f * t + 2 * i)
    return sig * M.adsr(n, attack, 0.1, 1.0, release)


def pad(midis, seconds):
    """Тёплая подкладка под стекло: расстроенные пилы под низким фильтром."""
    n = int(seconds * SR)
    sig = np.zeros(n)
    for m in midis:
        sig += M.supersaw(M.hz(m), n, 3, 0.006, 0.003)
        sig += 0.5 * np.sin(TAU * M.hz(m) * t_of(n))
    return M.lowpass_note(sig, 700) * M.adsr(n, 3.0, 0.5, 0.9, 2.5)


def bass_note(freq, seconds):
    n = int(seconds * SR)
    ph = M.phase(freq, n)
    sig = np.sin(TAU * ph) + 0.35 * M.tri(ph * 2)
    return M.lowpass_note(sig, 400) * M.adsr(n, 1.5, 0.08, 0.6, 0.3)


def compose():
    mel, pads, low, bass = (Loop() for _ in range(4))
    rng = np.random.default_rng(5)

    for bar in range(0, BARS, 2):
        root, tones = CHORDS[(bar // 2) % 4]
        pads.add(bar * 16 - 8, sine_pad(tones, 32 * S16 + 5.0), 0.05)
        pads.add(bar * 16, pad(tones, 32 * S16 + 2.0), 0.03)
        bass.add(bar * 16, bass_note(M.hz(root), 32 * S16), 0.2)
        # Отклик в середине аккорда: одна низкая нота пианино.
        low.add(bar * 16 + 20, felt(M.hz(tones[0] - 12), 5.0, 0.7), 0.3)

    # Мелодия: одна и та же фраза на всю петлю, без развития.
    for rep in range(BARS // 8):
        for bar, st, name in PHRASE:
            dt = rng.uniform(0.0, 0.008)
            vel = rng.uniform(0.85, 1.0)
            mel.add(rep * 128 + bar * 16 + st, felt(M.hz(M.midi(name))), 0.5 * vel, dt)

    # Воздух зала: тихий шум, дышит ровно четыре раза за петлю.
    noise = M.lowpass(M.lowpass(np.random.default_rng(3).standard_normal(N), 1800), 300, 2, True)
    air = noise * (0.6 + 0.4 * np.sin(TAU * 4 * np.arange(N) / N))

    music = M.reverb(M.echo(mel.buf, 6 * S16, 0.4, 4), 4.5, 0.7, 41, 3500.0)
    music += M.reverb(low.buf, 4.0, 0.6, 42, 2000.0)
    music += M.reverb(pads.buf, 4.5, 0.6, 44, 3000.0)
    music += bass.buf
    music += air * 0.012
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
