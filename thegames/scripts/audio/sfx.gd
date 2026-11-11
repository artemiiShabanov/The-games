class_name Sfx
extends RefCounted
## Синтез коротких звуков оболочки без ассетов: синус с затуханием в `AudioStreamWAV`.
## Пока не появятся настоящие звуки (#17), мини-игры берут отсюда щелчки и попадания.

const MIX_RATE := 44100


## Короткий тон: частота в герцах, длительность, громкость 0..1, `decay` скорость затухания.
static func blip(freq: float, seconds: float, volume := 0.5, decay := 18.0) -> AudioStreamWAV:
	var n := int(seconds * MIX_RATE)
	var data := PackedByteArray()
	data.resize(n * 2)
	for i in n:
		var tm := float(i) / MIX_RATE
		var env := exp(-decay * tm) * minf(1.0, tm * 400.0)
		var v := sin(TAU * freq * tm) * env * volume
		var s := int(clampf(v, -1.0, 1.0) * 32767.0)
		data.encode_s16(i * 2, s)
	var wav := AudioStreamWAV.new()
	wav.format = AudioStreamWAV.FORMAT_16_BITS
	wav.mix_rate = MIX_RATE
	wav.stereo = false
	wav.data = data
	return wav


## Глухой короткий стук для промаха: шум с быстрым затуханием.
static func thud(seconds := 0.12, volume := 0.4) -> AudioStreamWAV:
	var n := int(seconds * MIX_RATE)
	var data := PackedByteArray()
	data.resize(n * 2)
	var rng := RandomNumberGenerator.new()
	rng.seed = 7
	var last := 0.0
	for i in n:
		var tm := float(i) / MIX_RATE
		var env := exp(-30.0 * tm)
		# Фильтрованный шум: низкий, без шипения.
		last = lerpf(last, rng.randf_range(-1.0, 1.0), 0.08)
		var s := int(clampf(last * env * volume * 3.0, -1.0, 1.0) * 32767.0)
		data.encode_s16(i * 2, s)
	var wav := AudioStreamWAV.new()
	wav.format = AudioStreamWAV.FORMAT_16_BITS
	wav.mix_rate = MIX_RATE
	wav.stereo = false
	wav.data = data
	return wav


## Чиптюн-петля на три голоса: квадратная мелодия, квадратный бас октавой ниже, шумовой хэт.
## Ноты как полутоны от A4 (0), пауза null. Петля зациклена, подходит как музыка демки 8-bit.
static func chiptune_loop(melody: Array, bass: Array, bpm := 140.0, volume := 0.35) -> AudioStreamWAV:
	var step := 60.0 / bpm / 2.0
	var steps := melody.size()
	var n := int(steps * step * MIX_RATE)
	var data := PackedByteArray()
	data.resize(n * 2)
	var rng := RandomNumberGenerator.new()
	rng.seed = 3
	for i in n:
		var tm := float(i) / MIX_RATE
		var si := int(tm / step) % steps
		var local := tm - si * step
		var env := exp(-4.0 * local) * 0.6 + 0.4
		var v := 0.0
		if melody[si] != null:
			var f := 440.0 * pow(2.0, float(melody[si]) / 12.0)
			v += (1.0 if fmod(tm * f, 1.0) < 0.5 else -1.0) * 0.5 * env
		var bi := int(tm / (step * 2.0)) % bass.size()
		if bass[bi] != null:
			var fb := 220.0 * pow(2.0, float(bass[bi]) / 12.0)
			v += (1.0 if fmod(tm * fb, 1.0) < 0.5 else -1.0) * 0.3
		if si % 2 == 0 and local < 0.03:
			v += rng.randf_range(-1.0, 1.0) * 0.25 * (1.0 - local / 0.03)
		data.encode_s16(i * 2, int(clampf(v * volume, -1.0, 1.0) * 32767.0))
	var wav := AudioStreamWAV.new()
	wav.format = AudioStreamWAV.FORMAT_16_BITS
	wav.mix_rate = MIX_RATE
	wav.stereo = false
	wav.data = data
	wav.loop_mode = AudioStreamWAV.LOOP_FORWARD
	wav.loop_begin = 0
	wav.loop_end = n
	return wav


## Плеер с готовым потоком, добавить в дерево и звать `play()`. Шина звуков (#81).
static func player(stream: AudioStream, volume_db := 0.0) -> AudioStreamPlayer:
	var p := AudioStreamPlayer.new()
	p.stream = stream
	p.volume_db = volume_db
	p.bus = Options.SFX_BUS
	return p


## Плеер музыки демки: шина музыки (#81).
static func music(stream: AudioStream, volume_db := 0.0) -> AudioStreamPlayer:
	var p := player(stream, volume_db)
	p.bus = Options.MUSIC_BUS
	return p
