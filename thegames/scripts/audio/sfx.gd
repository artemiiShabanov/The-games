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


## Плеер с готовым потоком, добавить в дерево и звать `play()`.
static func player(stream: AudioStream, volume_db := 0.0) -> AudioStreamPlayer:
	var p := AudioStreamPlayer.new()
	p.stream = stream
	p.volume_db = volume_db
	return p
