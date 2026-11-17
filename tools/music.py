#!/usr/bin/env python3
"""Музыка демок (#87): одна тема на сеттинг, одна аранжировка на технологию, жанр даёт темп
и рисунок ударных. Синтез без сэмплов, петля бесшовная (эхо и реверберация заворачиваются).

    python3 tools/music.py --pilot            # тема зомби на пяти технологиях и жанры в
                                              # thegames/debug/playtest/music/*.mp3
    python3 tools/music.py --one zombies bit16 racing out.mp3

Пока пилот на прослушивание: в игру файлы не идут.
"""
import os
import subprocess
import sys
import wave

import numpy as np

SR = 44100
BPM = 120.0            # базовый темп, жанр умножает его скоростью проигрывания
STEP = 60.0 / BPM / 2  # шаг сетки: восьмая
BAR = 8                # восьмых в такте
TECHS = ["vector", "bit8", "bit16", "lowpoly", "threed"]

NOTE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def midi(name):
    """«A4», «D#5», «G#4» в номер MIDI."""
    step = NOTE[name[0]]
    rest = name[1:]
    if rest[0] == "#":
        step += 1
        rest = rest[1:]
    return 12 * (int(rest) + 1) + step


def hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


CHORDS = {  # бас (MIDI) и трезвучие
    "Am": (45, [57, 60, 64]), "Dm": (38, [57, 62, 65]), "E": (40, [56, 59, 64]),
    "F": (41, [57, 60, 65]), "G": (43, [55, 59, 62]), "C": (36, [55, 60, 64]),
}


class Theme:
    """Такт это восемь меток: нота, «.» тянуть, «_» пауза."""

    def __init__(self, bars, chords):
        assert len(bars) == len(chords)
        self.bars = len(bars)
        self.steps = self.bars * BAR
        self.chords = [CHORDS[c] for c in chords]
        self.notes = []  # (шаг, длина в шагах, midi)
        for b, text in enumerate(bars):
            cells = text.split()
            assert len(cells) == BAR, (b, text)
            for i, cell in enumerate(cells):
                if cell == ".":
                    if self.notes and self.notes[-1][0] + self.notes[-1][1] == b * BAR + i:
                        self.notes[-1][1] += 1
                elif cell != "_":
                    self.notes.append([b * BAR + i, 1, midi(cell)])

    def chord(self, step):
        return self.chords[(step // BAR) % self.bars]


THEMES = {
    # Зомби: ля минор, маршик с хроматикой, гармонический минор в каденциях.
    "zombies": Theme([
        "A4 . C5 . E5 . D#5 E5",
        "C5 . A4 . _ . E4 .",
        "F4 . A4 . C5 . B4 C5",
        "B4 . G#4 . E4 . _ .",
        "A4 . C5 . E5 . D#5 E5",
        "A5 . G5 E5 . C5 A4 .",
        "D5 . F5 . A5 . G5 F5",
        "E5 . G#5 . B5 . . _",
        "C5 C5 . A4 . F4 . A4",
        "D5 D5 . B4 . G4 . B4",
        "E5 E5 . C5 . A4 C5 E5",
        "A5 . . . E5 . _ .",
        "F5 E5 D5 . A4 . D5 .",
        "A5 G5 F5 . C5 . F5 .",
        "E5 . D5 . B4 . G#4 .",
        "E4 . G#4 B4 E5 . _ .",
    ], ["Am", "Am", "F", "E", "Am", "Am", "Dm", "E", "F", "G", "Am", "Am", "Dm", "F", "E", "E"]),
}

# Жанр: множитель темпа и рисунок ударных в шестнадцатых такта.
GENRES = {
    "platformer": dict(rate=1.0, kick=[0, 6, 8], snare=[4, 12], hat=[0, 2, 4, 6, 8, 10, 12, 14]),
    "racing": dict(rate=1.12, kick=[0, 4, 8, 12], snare=[4, 12], hat=list(range(16))),
    "shooter": dict(rate=1.06, kick=[0, 3, 6, 8, 11], snare=[4, 12], hat=[0, 2, 4, 6, 8, 10, 12, 14]),
    "sport": dict(rate=0.92, kick=[0, 8], snare=[4, 12], hat=[2, 6, 10, 14]),
    "fighting": dict(rate=1.04, kick=[0, 2, 8, 10], snare=[4, 12, 14, 15], hat=[0, 2, 4, 6, 8, 10, 12, 14]),
}


# ---------- кирпичи синтеза ----------

def tt(seconds):
    return np.arange(int(seconds * SR)) / SR


def adsr(n, a=0.005, d=0.08, s=0.7, r=0.04):
    env = np.full(n, s)
    na, nd, nr = int(a * SR), int(d * SR), int(r * SR)
    na, nr = min(na, n), min(nr, n)
    env[:na] = np.linspace(0, 1, na, endpoint=False)
    nd = min(nd, n - na)
    env[na:na + nd] = np.linspace(1, s, nd, endpoint=False)
    env[n - nr:] *= np.linspace(1, 0, nr)
    return env


def phase(freq, n, vib=0.0, vib_hz=5.5, vib_after=0.18):
    t = np.arange(n) / SR
    f = np.full(n, float(freq))
    if vib:
        f *= 1.0 + vib * np.sin(TAU * vib_hz * t) * np.clip((t - vib_after) * 6, 0, 1)
    return np.cumsum(f) / SR


TAU = 2 * np.pi


def pulse(ph, duty=0.5):
    return np.where(ph % 1.0 < duty, 1.0, -1.0)


def tri(ph):
    return 2.0 * np.abs(2.0 * (ph % 1.0) - 1.0) - 1.0


def saw(ph):
    return 2.0 * (ph % 1.0) - 1.0


def lowpass(x, cutoff, order=2, high=False):
    """Фильтр Баттерворта по амплитуде без сдвига фазы, по кругу: петля остаётся бесшовной."""
    spec = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1.0 / SR)
    gain = 1.0 / np.sqrt(1.0 + (f / cutoff) ** (2 * order))
    if high:
        gain = np.sqrt(np.maximum(0.0, 1.0 - gain ** 2))
    return np.fft.irfft(spec * gain, len(x))


def reverb(x, seconds, wet, seed=1, damp=3500.0):
    """Свёртка с затухающим шумом по кругу: хвост конца петли ложится на её начало."""
    rng = np.random.default_rng(seed)
    n = int(seconds * SR)
    ir = rng.standard_normal(n) * np.exp(-6.0 * np.arange(n) / n)
    ir[: int(0.012 * SR)] = 0.0
    full = np.zeros(len(x))
    full[:n] = ir
    full = lowpass(full, damp)
    tail = np.fft.irfft(np.fft.rfft(x) * np.fft.rfft(full), len(x))
    tail *= np.sqrt(np.mean(x ** 2) + 1e-9) / (np.sqrt(np.mean(tail ** 2)) + 1e-9)
    return x + tail * wet


def echo(x, delay, feedback=0.35, taps=4):
    out = x.copy()
    for k in range(1, taps + 1):
        out += np.roll(x, int(delay * SR) * k) * feedback ** k
    return out


def crush(x, rate, bits=0):
    """Звук старого железа: держим отсчёт и режем разрядность."""
    k = max(1, int(round(SR / rate)))
    y = np.repeat(x[::k], k)[: len(x)]
    if bits:
        q = 2 ** (bits - 1)
        y = np.round(y * q) / q
    return y


def pluck(freq, seconds, bright=0.5, seed=0):
    """Щипок Карплуса-Стронга."""
    n = int(seconds * SR)
    period = max(2, int(round(SR / freq)))
    rng = np.random.default_rng(seed + int(freq))
    buf = rng.uniform(-1, 1, period)
    buf = lowpass_small(buf, bright)
    out = np.empty(n)
    pos = 0
    while pos < n:
        m = min(period, n - pos)
        out[pos:pos + m] = buf[:m]
        buf = 0.996 * 0.5 * (buf + np.roll(buf, 1))
        pos += m
    out *= adsr(n, 0.002, 0.0, 1.0, min(0.05, seconds / 2))
    return out


def lowpass_small(buf, bright):
    k = int(1 + (1.0 - bright) * 6)
    for _ in range(k):
        buf = 0.5 * (buf + np.roll(buf, 1))
    return buf / (np.max(np.abs(buf)) + 1e-9)


class Track:
    def __init__(self, steps):
        self.n = int(round(steps * STEP * SR))
        self.buf = np.zeros(self.n)

    def add(self, start, sig, gain=1.0):
        """Кладёт сигнал с секунды `start`, хвост за концом петли заворачивается в начало."""
        i = int(round(start * SR)) % self.n
        idx = (i + np.arange(len(sig))) % self.n
        np.add.at(self.buf, idx, sig * gain)


# ---------- ударные ----------

def kick(deep=1.0, seconds=0.22):
    t = tt(seconds)
    f = 45 * deep + 110 * np.exp(-t * 32)
    return np.sin(TAU * np.cumsum(f) / SR) * np.exp(-t * 14)


def snare(seconds=0.2, body=190.0, noise=0.8, seed=2):
    t = tt(seconds)
    rng = np.random.default_rng(seed)
    n = lowpass(lowpass(rng.standard_normal(len(t)), 1800, 2, high=True), 6000, 2) * np.exp(-t * 22)
    tone = np.sin(TAU * body * t) * np.exp(-t * 30)
    return n * noise * 0.5 + tone * 0.6


def hat(seconds=0.05, seed=3):
    t = tt(seconds)
    rng = np.random.default_rng(seed)
    n = lowpass(lowpass(rng.standard_normal(len(t)), 5000, 3, high=True), 9000, 3)
    return n * np.exp(-t * 90) * 0.4


def drums(theme, genre, kit):
    """Дорожка ударных: `kit` это функции kick, snare, hat и их громкости."""
    tr = Track(theme.steps)
    pat = GENRES[genre]
    six = STEP / 2
    for bar in range(theme.bars):
        base = bar * BAR * STEP
        for name in ("kick", "snare", "hat"):
            sound, gain = kit[name]
            for k in pat[name]:
                tr.add(base + k * six, sound, gain)
        fill = kit.get("fill")
        if fill is not None and bar % 8 == 7:
            for j, k in enumerate((12, 13, 14, 15)):
                tr.add(base + k * six, fill[0][j], fill[1])
    return tr.buf


# ---------- аранжировки ----------

def bass_line(theme, pattern):
    """Ноты баса: `pattern` это (шаг в такте, сдвиг в полутонах от основного тона, длина)."""
    out = []
    for bar in range(theme.bars):
        root = theme.chords[bar][0]
        for step, shift, length in pattern:
            out.append((bar * BAR + step, length, root + shift))
    return out


def arrange_vector(theme, genre):
    """Пищалка: один однобитный голос. Мелодия чередуется с басом, в паузах арпеджио аккорда,
    вместо ударных короткие трески на том же голосе."""
    tr = Track(theme.steps)
    six = STEP / 2
    n16 = int(six * SR)
    sounding = {}
    onset = set()
    for start, length, m in theme.notes:
        onset.add(start)
        for s in range(start, start + length):
            sounding[s] = m
    pat = GENRES[genre]
    for k in range(theme.steps * 2):
        step = k // 2
        root, triad = theme.chord(step)
        if step in sounding and (k % 2 == 0 or step in onset):
            m = sounding[step]
        elif step in sounding:
            m = root + 12
        else:
            m = triad[k % 3] + 12
        seg = pulse(phase(hz(m), n16), 0.5)
        in_bar = k % 16
        if in_bar in pat["kick"]:
            c = int(0.03 * SR)
            seg[:c] = pulse(phase(70, c), 0.5)
        elif in_bar in pat["snare"]:
            c = int(0.025 * SR)
            seg[:c] = crush(np.sign(np.random.default_rng(k).standard_normal(c)), 5000)
        seg[-int(0.004 * SR):] = 0.0
        tr.add(k * six, seg, 0.3)
    return crush(tr.buf, 22050), None


def arrange_bit8(theme, genre):
    """Чиптюн: два пульса (ведущий и его эхо), треугольный бас, шумовые ударные."""
    tr = Track(theme.steps)
    for start, length, m in theme.notes:
        n = int(length * STEP * SR)
        lead = pulse(phase(hz(m), n, 0.006), 0.25) * adsr(n, 0.003, 0.06, 0.65, 0.02)
        tr.add(start * STEP, lead, 0.22)
        second = pulse(phase(hz(m), n), 0.125) * adsr(n, 0.003, 0.05, 0.5, 0.02)
        tr.add((start + 1) * STEP, second, 0.085)
    for start, length, m in bass_line(theme, [(0, 0, 1), (1, 0, 1), (2, 7, 1), (3, 0, 1), (4, 12, 1), (5, 0, 1), (6, 7, 1), (7, 0, 1)]):
        n = int(length * STEP * SR * 0.85)
        b = np.round(tri(phase(hz(m), n)) * 7.5) / 7.5
        tr.add(start * STEP, b * adsr(n, 0.002, 0.0, 1.0, 0.01), 0.32)
    t = tt(0.07)
    k8 = np.round(tri(np.cumsum(50 + 140 * np.exp(-t * 40)) / SR) * 7.5) / 7.5 * np.exp(-t * 20)
    rng = np.random.default_rng(8)
    s8 = lowpass_note(crush(np.sign(rng.standard_normal(int(0.1 * SR))), 4000), 5000) * np.exp(-tt(0.1) * 28)
    h8 = lowpass_note(crush(np.sign(rng.standard_normal(int(0.025 * SR))), 9000), 8000) * np.exp(-tt(0.025) * 120)
    kit = dict(kick=(k8, 0.5), snare=(s8, 0.15), hat=(h8, 0.035))
    return crush(tr.buf + drums(theme, genre, kit), 32000), None


def fm(freq, n, ratio, index, decay, vib=0.0):
    ph = phase(freq, n, vib)
    t = np.arange(n) / SR
    return np.sin(TAU * ph + index * np.exp(-t * decay) * np.sin(TAU * ph * ratio))


def arrange_bit16(theme, genre):
    """Трекер: FM-голос, колокольчик, бас, пэд, арпеджио, ударные и эхо."""
    tr = Track(theme.steps)
    for start, length, m in theme.notes:
        n = int(length * STEP * SR)
        tr.add(start * STEP, fm(hz(m), n, 2.0, 1.8, 6.0, 0.006) * adsr(n, 0.004, 0.1, 0.7, 0.03), 0.2)
        if length >= 2:
            nb = int(0.5 * SR)
            tr.add(start * STEP, fm(hz(m + 12), nb, 3.5, 2.5, 9.0) * np.exp(-tt(0.5) * 7), 0.06)
    for start, length, m in bass_line(theme, [(0, 0, 1), (1, 0, 1), (2, 12, 1), (3, 0, 1), (4, 0, 1), (5, 7, 1), (6, 12, 1), (7, 7, 1)]):
        n = int(length * STEP * SR * 0.9)
        tr.add(start * STEP, lowpass_note(saw(phase(hz(m), n)), 700) * adsr(n, 0.003, 0.08, 0.5, 0.02), 0.24)
    for bar in range(theme.bars):
        _, triad = theme.chords[bar]
        n = int(BAR * STEP * SR)
        for m in triad:
            tr.add(bar * BAR * STEP, tri(phase(hz(m), n, 0.003)) * adsr(n, 0.25, 0.2, 0.8, 0.25), 0.05)
        for k in range(16):
            na = int(0.11 * SR)
            m = triad[k % 3] + 12 + (12 if k % 6 >= 3 else 0)
            tr.add(bar * BAR * STEP + k * STEP / 2, tri(phase(hz(m), na)) * np.exp(-tt(0.11) * 22), 0.05)
    mix = echo(tr.buf, STEP * 3, 0.32, 3)
    kit = dict(kick=(kick(), 0.5), snare=(snare(0.18), 0.26), hat=(hat(0.04), 0.08))
    return crush(mix, 22050) + drums(theme, genre, kit), None


def lowpass_note(sig, cutoff):
    """Фильтр отдельной ноты: по кругу нельзя, поэтому дополняем тишиной."""
    pad = np.concatenate([sig, np.zeros(2048)])
    return lowpass(pad, cutoff)[: len(sig)]


def supersaw(freq, n, voices=3, spread=0.008, vib=0.0):
    out = np.zeros(n)
    for v in range(voices):
        det = 1.0 + spread * (v - (voices - 1) / 2)
        out += saw(phase(freq * det, n, vib) + v * 0.31)
    return out / voices


def arrange_lowpoly(theme, genre):
    """Синтезаторы PS1: расстроенные пилы, электропиано, струнный пэд, суб-бас, реверберация."""
    tr = Track(theme.steps)
    for start, length, m in theme.notes:
        n = int(length * STEP * SR)
        lead = lowpass_note(supersaw(hz(m), n, 3, 0.009, 0.005), 2600) * adsr(n, 0.008, 0.12, 0.7, 0.05)
        tr.add(start * STEP, lead, 0.2)
    for start, length, m in bass_line(theme, [(0, 0, 2), (3, 0, 1), (4, 12, 1), (6, 7, 2)]):
        n = int(length * STEP * SR * 0.9)
        ph = phase(hz(m), n)
        b = np.sin(TAU * ph) * 0.8 + lowpass_note(saw(ph), 350) * 0.5
        tr.add(start * STEP, b * adsr(n, 0.004, 0.1, 0.7, 0.03), 0.26)
    for bar in range(theme.bars):
        _, triad = theme.chords[bar]
        n = int(BAR * STEP * SR)
        for m in triad:
            pad = lowpass_note(supersaw(hz(m), n, 2, 0.006), 1500) * adsr(n, 0.4, 0.3, 0.8, 0.4)
            tr.add(bar * BAR * STEP, pad, 0.05)
        for step in (0, 3, 6):
            ne = int(0.45 * SR)
            for m in triad:
                tr.add((bar * BAR + step) * STEP, fm(hz(m + 12), ne, 1.0, 2.2, 10.0) * np.exp(-tt(0.45) * 6), 0.045)
    pitched = reverb(tr.buf, 1.3, 0.28, 4)
    sn = reverb_one(snare(0.22, 170.0, 1.0), 0.35, 0.5)
    rng = np.random.default_rng(5)
    shaker = lowpass_note(rng.standard_normal(int(0.03 * SR)), 5000) * np.exp(-tt(0.03) * 80) * 0.2
    kit = dict(kick=(kick(0.9, 0.26), 0.55), snare=(sn, 0.24), hat=(hat(0.045), 0.07))
    d = drums(theme, genre, kit)
    sh = Track(theme.steps)
    for k in range(theme.steps * 2):
        sh.add(k * STEP / 2, shaker, 0.025 if k % 2 else 0.01)
    return pitched + d + sh.buf, None


def reverb_one(sig, seconds, wet):
    pad = np.concatenate([sig, np.zeros(int(seconds * SR))])
    return reverb(pad, seconds, wet, 9)


def flute(freq, n):
    ph = phase(freq, n, 0.008, 5.0, 0.12)
    t = np.arange(n) / SR
    rng = np.random.default_rng(int(freq))
    breath = lowpass_note(rng.standard_normal(n), 2500) * 0.08
    return (np.sin(TAU * ph) + 0.3 * np.sin(2 * TAU * ph) + 0.1 * np.sin(3 * TAU * ph) + breath) * adsr(n, 0.05, 0.1, 0.85, 0.08) * (1 - 0.2 * np.exp(-t * 3))


def arrange_threed(theme, genre):
    """Почти живой состав: щипковая мелодия, флейта во второй половине, струнные, перебор
    аккордов, бас, ударные с перебивкой, зал. Играют неровно, как люди."""
    tr = Track(theme.steps)
    rng = np.random.default_rng(17)

    def human():
        return rng.uniform(-0.006, 0.006), rng.uniform(0.85, 1.0)

    for start, length, m in theme.notes:
        dt, vel = human()
        seconds = length * STEP + 0.35
        tr.add(start * STEP + dt, pluck(hz(m), seconds, 0.7, 1), 0.34 * vel)
        tr.add(start * STEP + dt + 0.004, pluck(hz(m + 12), seconds * 0.6, 0.5, 2), 0.07 * vel)
        if start >= theme.steps // 2:
            tr.add(start * STEP, flute(hz(m + 12), int(length * STEP * SR)), 0.075)
    for start, length, m in bass_line(theme, [(0, 0, 3), (3, 0, 1), (4, 7, 2), (6, 0, 1), (7, 7, 1)]):
        dt, vel = human()
        tr.add(start * STEP + dt, lowpass_note(pluck(hz(m), length * STEP + 0.2, 0.25, 3), 900), 0.42 * vel)
    for bar in range(theme.bars):
        _, triad = theme.chords[bar]
        n = int(BAR * STEP * SR)
        for m in triad + [triad[0] + 12]:
            strings = lowpass_note(supersaw(hz(m), n, 3, 0.007, 0.004), 2100) * adsr(n, 0.5, 0.3, 0.85, 0.5)
            tr.add(bar * BAR * STEP, strings, 0.038)
        for step in (0, 4):
            for j, m in enumerate(triad):
                dt, vel = human()
                tr.add((bar * BAR + step) * STEP + j * 0.018 + dt, pluck(hz(m), 0.9, 0.45, 4 + j), 0.1 * vel)
    pitched = reverb(tr.buf, 2.1, 0.33, 6, 4500.0)
    rngd = np.random.default_rng(11)
    brush = lowpass_note(rngd.standard_normal(int(0.09 * SR)), 5000) * np.exp(-tt(0.09) * 35) * 0.6
    sn = reverb_one(snare(0.24, 200.0, 1.2, 12), 0.6, 0.7)
    toms = [np.sin(TAU * np.cumsum(f + 40 * np.exp(-tt(0.25) * 20)) / SR) * np.exp(-tt(0.25) * 12) for f in (190, 160, 130, 100)]
    kit = dict(kick=(kick(1.1, 0.3) * 0.9, 0.5), snare=(sn, 0.22), hat=(brush, 0.07), fill=(toms, 0.3))
    return pitched + reverb(drums(theme, genre, kit), 0.9, 0.18, 13), None


# Прямоугольники без огибающей звучат громче при том же пике.
LEVEL = dict(vector=0.3, bit8=0.75)
ARRANGERS = dict(vector=arrange_vector, bit8=arrange_bit8, bit16=arrange_bit16,
                 lowpoly=arrange_lowpoly, threed=arrange_threed)


def render(setting, tech, genre):
    mix, _ = ARRANGERS[tech](THEMES[setting], genre)
    mix = mix - np.mean(mix)
    mix = np.tanh(mix / (np.max(np.abs(mix)) + 1e-9) * 1.4) / np.tanh(1.4)
    return mix * 0.85 * LEVEL.get(tech, 1.0)


def save(mix, path, rate=1.0, loops=1):
    """`rate` это скорость проигрывания жанра: в игре `pitch_scale`, здесь частота файла."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".wav"
    data = np.tile(mix, loops)
    with wave.open(tmp, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(int(SR * rate))
        w.writeframes((np.clip(data, -1, 1) * 32767).astype("<i2").tobytes())
    if path.endswith(".wav"):
        os.replace(tmp, path)
        return
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-ar", "44100", "-b:a", "160k", path], check=True)
    os.remove(tmp)


def stats(mix):
    seam = abs(mix[0] - mix[-1])
    return "пик %.2f, RMS %.3f, шов %.3f" % (np.max(np.abs(mix)), np.sqrt(np.mean(mix ** 2)), seam)


def pilot():
    out = os.path.join(os.path.dirname(__file__), "..", "thegames", "debug", "playtest", "music")
    for i, tech in enumerate(TECHS):
        mix = render("zombies", tech, "platformer")
        save(mix, os.path.join(out, "zombies_%d_%s.mp3" % (i + 1, tech)), 1.0, 2)
        print(tech, stats(mix))
    for genre in ("racing", "sport", "fighting"):
        mix = render("zombies", "bit16", genre)
        save(mix, os.path.join(out, "zombies_genre_%s_bit16.mp3" % genre), GENRES[genre]["rate"], 2)
        print("bit16", genre, stats(mix))


if __name__ == "__main__":
    if "--pilot" in sys.argv:
        pilot()
    elif "--one" in sys.argv:
        i = sys.argv.index("--one")
        setting, tech, genre, path = sys.argv[i + 1:i + 5]
        save(render(setting, tech, genre), path, GENRES[genre]["rate"], 2)
    else:
        print(__doc__)
