#!/usr/bin/env python3
"""Пять вариантов заглавной темы на пробу (2026-11-19).

Просьба Артемия: мелодии того же склада (ровные, без развития, медитативные), но без
азиатского акцента раната и гонга; ориентир это музыка музеев современного искусства и кино.
Каждый вариант это петля без шва: одна фраза на восемь тактов повторяется всю петлю.

    python3 tools/main_theme_variants.py          # все пять mp3 в debug/playtest/music/
    python3 tools/main_theme_variants.py 2 4      # только названные
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import music as M  # noqa: E402

SR = M.SR
TAU = M.TAU


class Loop:
    def __init__(self, bars, bpm):
        self.s16 = 60.0 / bpm / 4
        self.n = int(round(bars * 16 * self.s16 * SR))
        self.buf = np.zeros(self.n)

    def add(self, step, sig, gain=1.0, dt=0.0):
        i = int(round((step * self.s16 + dt) * SR)) % self.n
        idx = (i + np.arange(len(sig))) % self.n
        np.add.at(self.buf, idx, sig * gain)


def t_of(n):
    return np.arange(n) / SR


def fade(sig, a, r):
    na, nr = min(int(a * SR), len(sig)), min(int(r * SR), len(sig))
    sig[:na] *= np.linspace(0, 1, na)
    sig[len(sig) - nr:] *= np.linspace(1, 0, nr)
    return sig


# ---------- инструменты ----------
def felt(freq, seconds=3.0, vel=1.0):
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


def rhodes(freq, seconds=1.5, vel=1.0):
    """Электропиано: синус с мягкой частотной модуляцией, без звона."""
    n = int(seconds * SR)
    t = t_of(n)
    mod = np.sin(TAU * freq * t) * 1.3 * vel * np.exp(-t * 6)
    out = np.sin(TAU * freq * t + mod) * np.exp(-t * 2.8)
    out += 0.25 * np.sin(TAU * 2 * freq * t) * np.exp(-t * 5)
    return fade(out, 0.004, 0.05) * vel


def soft_pulse(freq, seconds, cutoff=1200.0):
    n = int(seconds * SR)
    ph = M.phase(freq, n)
    sig = 0.6 * M.tri(ph) + 0.4 * M.pulse(ph * 1.002, 0.35)
    return M.lowpass_note(sig, cutoff) * M.adsr(n, 0.006, 0.08, 0.4, 0.05)


def seq_note(freq, seconds, cutoff=1500.0):
    n = int(seconds * SR)
    ph = M.phase(freq, n)
    sig = 0.6 * M.saw(ph) + 0.4 * M.pulse(ph * 1.003, 0.3)
    return M.lowpass_note(sig, cutoff) * M.adsr(n, 0.003, 0.06, 0.35, 0.03)


def pad(midis, seconds, cutoff=1100.0, attack=1.2, release=1.0):
    n = int(seconds * SR)
    sig = np.zeros(n)
    for m in midis:
        sig += M.supersaw(M.hz(m), n, 3, 0.006, 0.003)
        sig += 0.5 * np.sin(TAU * M.hz(m) * t_of(n))
    return M.lowpass_note(sig, cutoff) * M.adsr(n, attack, 0.5, 0.9, release)


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


def spicc(freq, seconds):
    """Короткий штрих струнных."""
    n = int(seconds * SR)
    sig = M.supersaw(freq, n, 3, 0.006)
    return M.lowpass_note(sig, 1500) * M.adsr(n, 0.03, 0.1, 0.55, 0.08)


def bowed(freq, seconds, cutoff=2000.0):
    """Смычковый голос: пила с вибрато, медленная атака."""
    n = int(seconds * SR)
    sig = M.saw(M.phase(freq, n, 0.006, 5.2, 0.25)) + 0.6 * M.supersaw(freq, n, 3, 0.005, 0.006)
    return M.lowpass_note(sig, cutoff) * M.adsr(n, 0.14, 0.2, 0.85, 0.25)


def reed(freq, seconds):
    """Кларнет: нечётные гармоники, лёгкое дыхание."""
    n = int(seconds * SR)
    ph = M.phase(freq, n, 0.004, 4.8, 0.3)
    sig = np.sin(TAU * ph) + 0.33 * np.sin(3 * TAU * ph) + 0.12 * np.sin(5 * TAU * ph)
    breath = M.lowpass_note(np.random.default_rng(int(freq)).standard_normal(n), 2000) * 0.04
    return (sig + breath) * M.adsr(n, 0.07, 0.1, 0.85, 0.2)


def lead(freq, seconds):
    """Тёплый аналоговый голос: расстроенные пилы под фильтром."""
    n = int(seconds * SR)
    sig = M.supersaw(freq, n, 3, 0.007, 0.004) + 0.6 * np.sin(TAU * M.phase(freq, n, 0.004))
    return M.lowpass_note(sig, 1500) * M.adsr(n, 0.05, 0.15, 0.8, 0.18)


def bass_note(freq, seconds, attack=0.004):
    n = int(seconds * SR)
    ph = M.phase(freq, n)
    sig = np.sin(TAU * ph) + 0.35 * M.tri(ph * 2)
    return M.lowpass_note(sig, 400) * M.adsr(n, attack, 0.08, 0.6, min(0.3, seconds / 4))


def master(parts):
    mix = sum(parts)
    mix -= np.mean(mix)
    mix *= 0.8 / (np.max(np.abs(mix)) + 1e-9)
    return M.limit(mix)


def melody(loop, phrase, voice, bars, gain, sustain=1.0, tail=0.0, seed=5):
    rng = np.random.default_rng(seed)
    for rep in range(bars // 8):
        for bar, st, length, name in phrase:
            dt = rng.uniform(0.0, 0.008)
            vel = rng.uniform(0.85, 1.0)
            sig = voice(M.hz(M.midi(name)), length * loop.s16 * sustain + tail)
            loop.add(rep * 128 + bar * 16 + st, sig, gain * vel, dt)


# ---------- 1. Галерея: пианино с войлоком ----------
def gallery():
    """Ре мажор, 76: левая рука восьмыми по аккорду, правая поёт фразу. Сати, Нильс Фрам."""
    bars, bpm = 32, 76.0
    chords = [(38, [54, 57, 61, 64]), (35, [54, 57, 59, 62]), (31, [55, 59, 62, 66]), (33, [57, 62, 64, 69])]
    phrase = [
        (0, 0, 4, "F#5"), (0, 4, 2, "E5"), (0, 6, 2, "F#5"), (0, 8, 8, "A5"),
        (1, 0, 6, "F#5"), (1, 6, 2, "E5"), (1, 8, 8, "C#5"),
        (2, 0, 4, "D5"), (2, 4, 2, "E5"), (2, 6, 2, "F#5"), (2, 8, 8, "B5"),
        (3, 0, 6, "A5"), (3, 6, 2, "F#5"), (3, 8, 8, "D5"),
        (4, 0, 4, "B4"), (4, 4, 2, "D5"), (4, 6, 2, "G5"), (4, 8, 8, "F#5"),
        (5, 0, 6, "E5"), (5, 6, 2, "D5"), (5, 8, 8, "B4"),
        (6, 0, 4, "D5"), (6, 4, 4, "E5"), (6, 8, 8, "A5"),
        (7, 0, 4, "G5"), (7, 4, 4, "E5"), (7, 8, 8, "E5"),
    ]
    mel, left, pads, bass = (Loop(bars, bpm) for _ in range(4))
    s16 = mel.s16
    rng = np.random.default_rng(11)
    order = [0, 2, 1, 3, 2, 1, 3, 2]
    for bar in range(bars):
        root, tones = chords[(bar // 2) % 4]
        if bar % 2 == 0:
            pads.add(bar * 16, pad(tones, 32 * s16 + 1.5, 900.0, 1.5, 1.5), 0.035)
            bass.add(bar * 16, felt(M.hz(root + 12), 5.0), 0.5)
        for k in range(8):
            vel = rng.uniform(0.55, 0.75) + 0.2 * (k == 0)
            left.add(bar * 16 + k * 2, felt(M.hz(tones[order[k]]), 2.2, vel), 0.3, rng.uniform(0, 0.01))
    melody(mel, phrase, lambda f, s: felt(f, max(s * 1.6, 2.5)), bars, 0.6)
    return master([
        M.reverb(mel.buf, 3.2, 0.5, 41, 3500.0),
        M.reverb(left.buf, 2.8, 0.4, 42, 2500.0),
        M.reverb(pads.buf, 3.0, 0.5, 44, 2500.0),
        M.reverb(bass.buf, 2.0, 0.25, 45, 1500.0),
    ])


# ---------- 2. Фазы: минимализм ----------
def phases():
    """Ля минор, 104: два одинаковых узора шестнадцатыми со сдвигом, кларнет поверх. Райх, Гласс."""
    bars, bpm = 32, 104.0
    chords = [(33, [57, 60, 64, 71]), (29, [53, 57, 60, 64]), (36, [55, 60, 62, 64]), (31, [55, 59, 62, 64])]
    phrase = [
        (0, 0, 8, "E5"), (0, 8, 4, "D5"), (0, 12, 4, "C5"),
        (1, 0, 12, "B4"),
        (2, 0, 4, "A4"), (2, 4, 4, "C5"), (2, 8, 8, "E5"),
        (3, 0, 8, "F5"), (3, 8, 8, "E5"),
        (4, 0, 8, "G5"), (4, 8, 4, "E5"), (4, 12, 4, "D5"),
        (5, 0, 12, "E5"),
        (6, 0, 4, "D5"), (6, 4, 4, "B4"), (6, 8, 8, "D5"),
        (7, 0, 8, "D5"), (7, 8, 8, "B4"),
    ]
    pattern = [0, 2, 1, 3, 2, 0, 3, 1, 2, 3, 0, 2, 1, 3, 2, 1]
    mel, one, two, pads, bass = (Loop(bars, bpm) for _ in range(5))
    s16 = mel.s16
    for bar in range(bars):
        root, tones = chords[(bar // 2) % 4]
        if bar % 2 == 0:
            pads.add(bar * 16, pad(tones, 32 * s16 + 1.0, 1000.0), 0.05)
            bass.add(bar * 16, bass_note(M.hz(root), 32 * s16, 0.05), 0.2)
        for s in range(16):
            m = tones[pattern[s]] + 12
            vel = 0.7 + 0.3 * (s % 8 == 0)
            one.add(bar * 16 + s, rhodes(M.hz(m), 0.9, vel), 0.11)
            # Второй голос: тот же узор на три шестнадцатых позже, октавой ниже и глуше.
            two.add(bar * 16 + s + 3, soft_pulse(M.hz(m - 12), s16 * 0.9), 0.07 * vel)
    melody(mel, phrase, reed, bars, 0.13, 1.0, 0.15)
    return master([
        M.reverb(mel.buf, 3.0, 0.55, 41, 3000.0),
        M.reverb(one.buf, 1.8, 0.35, 42, 4000.0),
        M.reverb(M.echo(two.buf, 3 * s16, 0.3, 3), 1.8, 0.35, 43, 3000.0),
        M.reverb(pads.buf, 3.0, 0.5, 44, 3000.0),
        bass.buf,
    ])


# ---------- 3. Проектор: струнные ----------
def projector():
    """До минор, 92: остинато струнных восьмыми, смычковый голос длинными нотами. Рихтер, Гласс."""
    bars, bpm = 32, 92.0
    chords = [(36, [55, 60, 63, 67]), (32, [56, 60, 63, 67]), (39, [55, 58, 63, 67]), (38, [53, 58, 62, 65])]
    phrase = [
        (0, 0, 8, "G4"), (0, 8, 4, "C5"), (0, 12, 4, "D5"),
        (1, 0, 12, "D#5"), (1, 12, 4, "D5"),
        (2, 0, 8, "C5"), (2, 8, 4, "D#5"), (2, 12, 4, "D5"),
        (3, 0, 16, "C5"),
        (4, 0, 8, "A#4"), (4, 8, 4, "D#5"), (4, 12, 4, "F5"),
        (5, 0, 12, "G5"), (5, 12, 4, "F5"),
        (6, 0, 8, "F5"), (6, 8, 4, "D5"), (6, 12, 4, "D#5"),
        (7, 0, 12, "D5"), (7, 12, 4, "A#4"),
    ]
    order = [0, 2, 1, 2, 3, 2, 1, 2]
    mel, ost, pads, bass = (Loop(bars, bpm) for _ in range(4))
    s16 = mel.s16
    for bar in range(bars):
        root, tones = chords[(bar // 2) % 4]
        if bar % 2 == 0:
            pads.add(bar * 16, pad(tones, 32 * s16 + 1.0, 1400.0, 0.8, 1.0), 0.06)
            bass.add(bar * 16, bowed(M.hz(root), 32 * s16, 500.0), 0.16)
        for k in range(8):
            vel = 0.75 + 0.25 * (k % 4 == 0)
            ost.add(bar * 16 + k * 2, spicc(M.hz(tones[order[k]]), s16 * 1.7), 0.14 * vel)
    melody(mel, phrase, bowed, bars, 0.12, 1.0, 0.2)
    return master([
        M.reverb(mel.buf, 3.2, 0.55, 41, 3500.0),
        M.reverb(ost.buf, 2.2, 0.4, 42, 3000.0),
        M.reverb(pads.buf, 3.0, 0.5, 44, 3000.0),
        M.reverb(bass.buf, 2.0, 0.3, 45, 1200.0),
    ])


# ---------- 4. Инсталляция: эмбиент ----------
def installation():
    """Выбран 2026-11-19 и переехал в `tools/main_theme.py`."""
    import main_theme
    return main_theme.compose()


# ---------- 5. Сигнал: аналоговый синтезатор ----------
# Мелодия первой версии темы (2026-11-18).
OLD_PHRASE = [
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


def signal():
    """Ми минор, 108: прежние мелодия, аккорды и арпеджио, но голос синтезатора вместо раната
    и без гонга. Вангелис, Tangerine Dream. Показывает, сколько акцента давал один тембр."""
    bars, bpm = 32, 108.0
    chords = [(40, [52, 55, 59, 62]), (36, [48, 52, 55, 59]), (38, [50, 54, 57, 64]), (35, [47, 50, 54, 57])]
    phrase = OLD_PHRASE
    mel, pads, arps, bass = (Loop(bars, bpm) for _ in range(4))
    s16 = mel.s16
    for bar in range(bars):
        root, tones = chords[(bar // 2) % 4]
        if bar % 2 == 0:
            pads.add(bar * 16, pad(tones, 32 * s16 + 1.0), 0.06)
            bass.add(bar * 16, bass_note(M.hz(root), 32 * s16), 0.2)
        order = tones + [tones[2] + 12, tones[1] + 12] + tones[::-1][1:3]
        for s in range(16):
            vel = 0.7 + 0.3 * (s % 4 == 0)
            arps.add(bar * 16 + s, seq_note(M.hz(order[s % len(order)] + 12), s16 * 0.9), 0.055 * vel)
    for rep in range(bars // 8):
        for bar, st, length, name in phrase:
            sig = lead(M.hz(M.midi(name) - 12), length * s16 + 0.12)
            mel.add(rep * 128 + bar * 16 + st, sig, 0.13)
    return master([
        M.reverb(M.echo(mel.buf, 3 * s16, 0.25, 2), 3.0, 0.5, 41, 4000.0),
        M.reverb(M.echo(arps.buf, 3 * s16, 0.3, 3), 1.6, 0.3, 43, 4500.0),
        M.reverb(pads.buf, 3.0, 0.5, 44, 3000.0),
        bass.buf,
    ])


VARIANTS = [
    ("gallery", gallery), ("phases", phases), ("projector", projector),
    ("installation", installation), ("signal", signal),
]


def main():
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "thegames")
    picked = [int(a) for a in sys.argv[1:] if a.isdigit()] or list(range(1, len(VARIANTS) + 1))
    for i in picked:
        name, make = VARIANTS[i - 1]
        mix = make()
        print("%d %s: %s, длина %.1f с" % (i, name, M.stats(mix), len(mix) / SR))
        path = os.path.join(root, "debug", "playtest", "music", "main_theme_v%d_%s.mp3" % (i, name))
        M.save(mix, path, 1.0, 2)


if __name__ == "__main__":
    main()
