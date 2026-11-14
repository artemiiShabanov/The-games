class_name MiniSfx
extends RefCounted
## Общий набор звуков мини-игр (#131): четыре звука, которыми обходятся все двадцать игр.
## `TAP` тык: нейтральное действие (шаг, переворот карточки, прыжок, нажатие). `HIT` попал:
## засчитанное действие (блок встал, нота взята, пара сошлась), обычно лесенкой по высоте.
## `MISS` мимо: ошибка и промах. `WIN` готово: раунд или вся мини-игра сделаны.
## У каждого пять вариантов на выбор (сцена `debug/scenes/sounds_test`); выбранный номер
## потом станет единственным, остальные уйдут. `freq` это высота: один звук идёт в тон соседям.

enum Kind { TAP, HIT, MISS, WIN }

const RATE := Sfx.MIX_RATE
const KIND_NAMES: Array[String] = ["Тык", "Попал", "Мимо", "Готово"]
const KIND_USE: Array[String] = [
	"нейтральное действие: шаг, прыжок, переворот карточки, нажатие",
	"засчитано: блок встал, нота взята, пара сошлась; идёт лесенкой вверх",
	"ошибка: промах, удар о стену, неверная клавиша",
	"раунд или вся мини-игра сделаны"]
const KIND_FREQ: Array[float] = [520.0, 196.0, 220.0, 523.0]
const VARIANT_NAMES: Array[Array] = [
	["Капля", "Щелчок по желе", "Пузырёк", "Деревяшка", "Тук"],
	["Шлепок с отскоком", "Бульк", "Маримба", "Желейный колокольчик", "Чпок"],
	["Съезд вниз", "Глухой стук", "Бу-бу", "Шмяк", "Пружина вниз"],
	["Две ноты", "Три ноты", "Блеск", "Бульк-бульк-динь", "Мягкий аккорд"]]


## Звук вида `kind`, вариант 0..4, высота `freq` (0: своя высота вида).
static func make(kind: Kind, variant: int, freq := 0.0) -> AudioStreamWAV:
	var f := freq if freq > 0.0 else KIND_FREQ[kind]
	match kind:
		Kind.TAP:
			return _tap(variant, f)
		Kind.HIT:
			return _hit(variant, f)
		Kind.MISS:
			return _miss(variant, f)
	return _win(variant, f)


# --- Тык ---------------------------------------------------------------------------------------

static func _tap(variant: int, f: float) -> AudioStreamWAV:
	var out := _buf(0.12)
	match variant:
		0:  # Капля: тон быстро падает к своей высоте.
			_tone(out, 0.0, f * 1.7, f, 60.0, 0.5, 42.0)
		1:  # Щелчок по желе: мягкий шумовой щелчок и короткий тон под ним.
			_noise(out, 0.0, 0.03, 0.5, 120.0, 1500.0, 2400.0, 0.6, 31)
			_tone(out, 0.0, f * 1.15, f, 80.0, 0.3, 55.0)
		2:  # Пузырёк: тон всплывает вверх.
			_tone(out, 0.0, f * 0.7, f * 1.5, 22.0, 0.45, 38.0, 0.0, 0.006)
		3:  # Деревяшка: тон с негармоничным призвуком, как брусок маримбы.
			_tone(out, 0.0, f, f, 1.0, 0.42, 48.0)
			_tone(out, 0.0, f * 2.76, f * 2.76, 1.0, 0.16, 90.0)
		_:  # Тук: низкий короткий удар с щелчком.
			_tone(out, 0.0, f * 0.9, f * 0.45, 45.0, 0.6, 50.0)
			_noise(out, 0.0, 0.015, 0.25, 200.0, 2600.0, 2600.0, 0.8, 33)
	return _finish(out)


# --- Попал -------------------------------------------------------------------------------------

static func _hit(variant: int, f: float) -> AudioStreamWAV:
	var out := _buf(0.42)
	match variant:
		0:  # Шлепок с отскоком: удар и два затухающих вздрога желе.
			_noise(out, 0.0, 0.06, 0.5, 48.0, 500.0, 900.0, 1.2, 21)
			_tone(out, 0.0, f * 2.5, f, 38.0, 0.6, 16.0, 0.22)
			_tone(out, 0.09, f * 2.6, f * 1.17, 38.0, 0.2, 26.0)
			_tone(out, 0.165, f * 2.4, f * 1.06, 38.0, 0.08, 34.0)
		1:  # Бульк: пузырь всплывает, под ним короткое тело.
			_tone(out, 0.0, f * 1.2, f * 3.2, 14.0, 0.5, 20.0, 0.0, 0.008)
			_tone(out, 0.0, f * 1.6, f, 50.0, 0.3, 24.0)
		2:  # Маримба: тёплый брусок на октаву выше высоты.
			_tone(out, 0.0, f * 2.0, f * 2.0, 1.0, 0.5, 13.0)
			_tone(out, 0.0, f * 8.0, f * 8.0, 1.0, 0.12, 60.0)
			_tone(out, 0.0, f, f, 1.0, 0.2, 18.0)
		3:  # Желейный колокольчик: мягкая атака, три призвука, лёгкое проседание высоты.
			_tone(out, 0.0, f * 2.06, f * 2.0, 9.0, 0.38, 9.0, 0.3, 0.012)
			_tone(out, 0.0, f * 6.05, f * 6.0, 9.0, 0.1, 22.0, 0.0, 0.012)
			_tone(out, 0.0, f * 1.3, f, 30.0, 0.22, 20.0)
		_:  # Чпок: присоска отлипла, тон вверх и хлопок.
			_tone(out, 0.0, f * 1.4, f * 4.0, 30.0, 0.45, 34.0, 0.0, 0.004)
			_noise(out, 0.035, 0.05, 0.45, 70.0, 900.0, 2200.0, 1.0, 25)
			_tone(out, 0.04, f * 2.2, f * 1.5, 40.0, 0.3, 22.0)
	return _finish(out)


# --- Мимо --------------------------------------------------------------------------------------

static func _miss(variant: int, f: float) -> AudioStreamWAV:
	var out := _buf(0.45)
	match variant:
		0:  # Съезд вниз: тон уныло сползает.
			_tone(out, 0.0, f * 1.4, f * 0.42, 5.5, 0.5, 6.0, 0.15, 0.01)
		1:  # Глухой стук: низкий шум и удар под ним.
			_noise(out, 0.0, 0.14, 0.9, 28.0, 260.0, 160.0, 1.4, 7)
			_tone(out, 0.0, f * 0.7, f * 0.4, 30.0, 0.5, 22.0)
		2:  # Бу-бу: две ноты вниз.
			_tone(out, 0.0, f * 1.0, f * 0.94, 8.0, 0.42, 16.0, 0.2, 0.006)
			_tone(out, 0.13, f * 0.75, f * 0.68, 8.0, 0.45, 11.0, 0.2, 0.006)
		3:  # Шмяк: мокрый шлепок, шум съезжает вниз.
			_noise(out, 0.0, 0.2, 0.9, 20.0, 1500.0, 260.0, 0.9, 27)
			_tone(out, 0.0, f * 1.1, f * 0.5, 24.0, 0.35, 18.0)
		_:  # Пружина вниз: тон сползает и дрожит неровно, как сдувшийся батут.
			_tone(out, 0.0, f * 1.6, f * 0.5, 7.0, 0.45, 7.0, 0.1, 0.006, 19.0, 0.09)
	return _finish(out)


# --- Готово ------------------------------------------------------------------------------------

static func _win(variant: int, f: float) -> AudioStreamWAV:
	var out := _buf(0.75)
	match variant:
		0:  # Две ноты: квинта вверх, мягкие бруски.
			_bar(out, 0.0, f, 0.4)
			_bar(out, 0.11, f * 1.5, 0.45)
		1:  # Три ноты: мажорное трезвучие вверх.
			_bar(out, 0.0, f, 0.36)
			_bar(out, 0.09, f * 1.26, 0.36)
			_bar(out, 0.18, f * 1.5, 0.42)
		2:  # Блеск: нота с октавой и быстрым мерцанием.
			_tone(out, 0.0, f * 1.5, f * 1.5, 1.0, 0.36, 6.0, 0.0, 0.004, 24.0, 0.0, 0.5)
			_tone(out, 0.0, f * 3.0, f * 3.0, 1.0, 0.2, 9.0, 0.0, 0.004, 31.0, 0.0, 0.6)
		3:  # Бульк-бульк-динь: два пузыря и колокольчик.
			_tone(out, 0.0, f * 0.5, f * 1.3, 16.0, 0.4, 30.0, 0.0, 0.006)
			_tone(out, 0.1, f * 0.65, f * 1.7, 16.0, 0.4, 30.0, 0.0, 0.006)
			_bar(out, 0.21, f * 2.0, 0.4)
		_:  # Мягкий аккорд: трезвучие разом, медленная атака, лёгкое проседание.
			for mult: float in [1.0, 1.26, 1.5, 2.0]:
				_tone(out, 0.0, f * mult * 1.03, f * mult, 12.0, 0.17, 5.5, 0.15, 0.02)
	return _finish(out)


# --- Синтез ------------------------------------------------------------------------------------

static func _buf(seconds: float) -> PackedFloat32Array:
	var out := PackedFloat32Array()
	out.resize(int(seconds * RATE))
	return out


## Синус с `start` секунды: высота от `f0` к `f1` со скоростью `glide`, громкость `vol`,
## затухание `decay`, доля второй гармоники `harm`, атака `attack` секунд. `wob_hz` с
## `wob_pitch` качает высоту, с `wob_amp` громкость (мерцание).
static func _tone(out: PackedFloat32Array, start: float, f0: float, f1: float, glide: float, vol: float,
		decay: float, harm := 0.0, attack := 0.002, wob_hz := 0.0, wob_pitch := 0.0, wob_amp := 0.0) -> void:
	var from := int(start * RATE)
	var phase := 0.0
	for i in out.size() - from:
		var tm := float(i) / RATE
		var f := f1 + (f0 - f1) * exp(-tm * glide)
		var wob := sin(TAU * wob_hz * tm) if wob_hz > 0.0 else 0.0
		phase += TAU * f * (1.0 + wob_pitch * wob * exp(-tm * 3.0)) / RATE
		var env := minf(1.0, tm / attack) * exp(-tm * decay) * (1.0 + wob_amp * wob)
		out[from + i] += (sin(phase) + harm * sin(phase * 2.0)) * env * vol


## Шум через резонанс с `start` секунды: `seconds` длиной, полоса от `fc0` к `fc1`, `damp`
## ширина полосы (меньше: звонче).
static func _noise(out: PackedFloat32Array, start: float, seconds: float, vol: float, decay: float,
		fc0: float, fc1: float, damp: float, seed_: int) -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_
	var from := int(start * RATE)
	var n := mini(int(seconds * RATE), out.size() - from)
	var low := 0.0
	var band := 0.0
	for i in n:
		var u := float(i) / n
		var k := 2.0 * sin(PI * lerpf(fc0, fc1, u) / RATE)
		var high := rng.randf_range(-1.0, 1.0) - low - damp * band
		band += k * high
		low += k * band
		out[from + i] += band * minf(1.0, u * 40.0) * exp(-u * seconds * decay) * (1.0 - u) * vol


## Мягкий брусок: нота с тихим верхним призвуком, для мелодий «готово».
static func _bar(out: PackedFloat32Array, start: float, f: float, vol: float) -> void:
	_tone(out, start, f, f, 1.0, vol, 8.0, 0.0, 0.003)
	_tone(out, start, f * 4.0, f * 4.0, 1.0, vol * 0.2, 40.0, 0.0, 0.003)


## Хвост без щелчка и общая громкость.
static func _finish(out: PackedFloat32Array) -> AudioStreamWAV:
	var n := out.size()
	var tail := int(0.02 * RATE)
	for i in mini(tail, n):
		out[n - 1 - i] *= float(i) / tail
	return Sfx._wav(out)
