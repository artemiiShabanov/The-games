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


## Трекер демок 16/32-bit (#95): восемь голосов из той же темы, что у чиптюна. Ведущий пульсом
## с вибрато, колокольчик октавой выше, треугольный бас, арпеджио аккорда от баса, тихий пэд
## квинтой, бочка, малый и хэт; на всё эхо. Частота 22050 Гц, как у сэмплов того времени.
## Ноты как полутоны от A4 (0), пауза null; бас меняется раз в два шага.
static func tracker_loop(melody: Array, bass: Array, bpm := 132.0, volume := 0.3) -> AudioStreamWAV:
	var rate := 22050
	var step := 60.0 / bpm / 2.0
	var steps := melody.size()
	var n := int(steps * step * rate)
	var mix := PackedFloat32Array()
	mix.resize(n)
	var rng := RandomNumberGenerator.new()
	rng.seed = 5
	var chord: Array[float] = [1.0, pow(2.0, 4.0 / 12.0), pow(2.0, 7.0 / 12.0), 2.0]
	for i in n:
		var tm := float(i) / rate
		var si := int(tm / step) % steps
		var local := tm - int(tm / step) * step
		var v := 0.0
		if melody[si] != null:
			var f := 440.0 * pow(2.0, float(melody[si]) / 12.0)
			var env := exp(-3.0 * local) * 0.5 + 0.5
			var ph := fmod(tm * f * (1.0 + 0.006 * sin(TAU * 5.5 * tm)), 1.0)
			v += (1.0 if ph < 0.25 else -0.333) * 0.22 * env
			v += sin(TAU * tm * f * 2.0) * 0.06 * env
		var bn: Variant = bass[int(tm / (step * 2.0)) % bass.size()]
		if bn != null:
			var fb := 110.0 * pow(2.0, float(bn) / 12.0)
			v += (4.0 * absf(fmod(tm * fb, 1.0) - 0.5) - 1.0) * 0.3
			var fa := fb * 4.0 * chord[int(tm / (step / 2.0)) % 4]
			v += (1.0 if fmod(tm * fa, 1.0) < 0.5 else -1.0) * 0.06
			v += (fmod(tm * fb * 3.0, 1.0) * 2.0 - 1.0) * 0.05
		var beat := si % 4
		if beat == 0 and local < 0.12:
			v += sin(TAU * (55.0 + 90.0 * exp(-local * 30.0)) * local) * 0.5 * (1.0 - local / 0.12)
		if beat == 2 and local < 0.1:
			v += rng.randf_range(-1.0, 1.0) * 0.3 * (1.0 - local / 0.1)
		if local < 0.02:
			v += rng.randf_range(-1.0, 1.0) * 0.12 * (1.0 - local / 0.02)
		mix[i] = v
	# Эхо на три четверти шага назад, по кругу, чтобы петля сходилась.
	var delay := int(step * 0.75 * rate)
	var data := PackedByteArray()
	data.resize(n * 2)
	for i in n:
		var v := mix[i] + 0.3 * mix[(i - delay + n) % n]
		data.encode_s16(i * 2, int(clampf(v * volume, -1.0, 1.0) * 32767.0))
	var wav := AudioStreamWAV.new()
	wav.format = AudioStreamWAV.FORMAT_16_BITS
	wav.mix_rate = rate
	wav.stereo = false
	wav.data = data
	wav.loop_mode = AudioStreamWAV.LOOP_FORWARD
	wav.loop_begin = 0
	wav.loop_end = n
	return wav


## Пищалка векторных демок (#88): один голос, чистый квадрат без огибающей, как динамик PC; частота
## скользит от `freq` к `to_freq` (0: без скольжения).
static func beep(freq: float, seconds: float, volume := 0.3, to_freq := 0.0) -> AudioStreamWAV:
	var n := int(seconds * MIX_RATE)
	var out := PackedFloat32Array()
	out.resize(n)
	var phase := 0.0
	for i in n:
		var t := float(i) / n
		var f := lerpf(freq, to_freq, t) if to_freq > 0.0 else freq
		phase = fmod(phase + f / MIX_RATE, 1.0)
		# Без огибающей, только щелчок срезан на краях в 2 мс.
		var edge := minf(1.0, minf(float(i), float(n - i)) / (0.002 * MIX_RATE))
		out[i] = (volume if phase < 0.5 else -volume) * edge
	return _wav(out)


## Музыка пищалкой: одна мелодия без баса и шума, ноты полутонами от ля (null пауза), между
## нотами короткий разрыв, как у динамика PC.
static func beeper_loop(melody: Array, bpm := 150.0, volume := 0.22) -> AudioStreamWAV:
	var step := 60.0 / bpm / 2.0
	var n := int(melody.size() * step * MIX_RATE)
	var data := PackedByteArray()
	data.resize(n * 2)
	var phase := 0.0
	for i in n:
		var tm := float(i) / MIX_RATE
		var si := int(tm / step) % melody.size()
		var local := tm - si * step
		var v := 0.0
		if melody[si] != null and local < step * 0.85:
			var f := 440.0 * pow(2.0, float(melody[si]) / 12.0)
			phase = fmod(phase + f / MIX_RATE, 1.0)
			v = volume if phase < 0.5 else -volume
		data.encode_s16(i * 2, int(clampf(v, -1.0, 1.0) * 32767.0))
	var wav := AudioStreamWAV.new()
	wav.format = AudioStreamWAV.FORMAT_16_BITS
	wav.mix_rate = MIX_RATE
	wav.stereo = false
	wav.data = data
	wav.loop_mode = AudioStreamWAV.LOOP_FORWARD
	wav.loop_begin = 0
	wav.loop_end = n
	return wav


## «Бульк» кулера в студии (#80): два коротких всплеска синуса, частота скользит вверх, как
## пузырь в бутыли.
static func bulp(volume := 0.32) -> AudioStreamWAV:
	var parts := [[0.0, 210.0, 520.0, 0.09], [0.12, 300.0, 780.0, 0.075]]
	var n := int(0.21 * MIX_RATE)
	var out := PackedFloat32Array()
	out.resize(n)
	for part: Array in parts:
		var start := int(float(part[0]) * MIX_RATE)
		var count := int(float(part[3]) * MIX_RATE)
		var phase := 0.0
		for i in mini(count, n - start):
			var u := float(i) / count
			var freq := float(part[1]) * pow(float(part[2]) / float(part[1]), u)
			phase += TAU * freq / MIX_RATE
			out[start + i] += sin(phase) * sin(PI * u) * (1.0 - 0.5 * u) * volume
	return _wav(out)


## Шипение помех телевизора в студии (#80): белый шум без самых низов, редкий треск, мягкие
## начало и конец.
static func hiss(seconds := 0.6, volume := 0.16) -> AudioStreamWAV:
	var n := int(seconds * MIX_RATE)
	var out := PackedFloat32Array()
	out.resize(n)
	var rng := RandomNumberGenerator.new()
	rng.seed = 11
	var last := 0.0
	for i in n:
		var tm := float(i) / MIX_RATE
		var env := minf(1.0, tm * 80.0) * minf(1.0, (seconds - tm) * 10.0)
		var white := rng.randf_range(-1.0, 1.0)
		var v := white - last * 0.7
		last = white
		if rng.randf() < 0.0015:
			v += rng.randf_range(-2.0, 2.0)
		out[i] = v * env * volume
	return _wav(out)


## Стрёкот часов в студии (#80): щелчки, чаще к середине прокрутки и реже к концу.
static func whirr(seconds := 0.8, volume := 0.22) -> AudioStreamWAV:
	var n := int(seconds * MIX_RATE)
	var out := PackedFloat32Array()
	out.resize(n)
	var tm := 0.0
	while tm < seconds - 0.01:
		var start := int(tm * MIX_RATE)
		for i in mini(int(0.008 * MIX_RATE), n - start):
			var lt := float(i) / MIX_RATE
			out[start + i] += sin(TAU * 1700.0 * lt) * exp(-600.0 * lt) * volume
		tm += lerpf(0.075, 0.03, sin(PI * tm / seconds))
	return _wav(out)


## Мягкий «шух» сдвига: шум через резонанс, который плавно уезжает вверх, нарастает и гаснет
## без удара. Нейтральный: не похож ни на успех, ни на промах.
static func swish(volume := 0.2, seconds := 0.2) -> AudioStreamWAV:
	var n := int(seconds * MIX_RATE)
	var out := PackedFloat32Array()
	out.resize(n)
	var rng := RandomNumberGenerator.new()
	rng.seed = 29
	var low := 0.0
	var band := 0.0
	for i in n:
		var u := float(i) / n
		var k := 2.0 * sin(PI * lerpf(700.0, 2600.0, u) / MIX_RATE)
		var high := rng.randf_range(-1.0, 1.0) - low - 0.9 * band
		band += k * high
		low += k * band
		# Горб огибающей ближе к началу: звук приезжает и тает.
		out[i] = band * pow(sin(PI * pow(u, 0.7)), 2.0) * volume
	return _wav(out)


## Отсчёты -1..1 в моно 16 бит.
static func _wav(samples: PackedFloat32Array) -> AudioStreamWAV:
	var data := PackedByteArray()
	data.resize(samples.size() * 2)
	for i in samples.size():
		data.encode_s16(i * 2, int(clampf(samples[i], -1.0, 1.0) * 32767.0))
	var wav := AudioStreamWAV.new()
	wav.format = AudioStreamWAV.FORMAT_16_BITS
	wav.mix_rate = MIX_RATE
	wav.stereo = false
	wav.data = data
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
