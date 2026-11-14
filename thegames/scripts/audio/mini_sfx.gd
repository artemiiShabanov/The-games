class_name MiniSfx
extends RefCounted
## Общий набор звуков мини-игр (#131): пять звуков, которыми обходятся все двадцать игр, выбраны
## на слух 2026-11-14 из пяти вариантов каждого (сцена `debug/scenes/sounds_test`).
## `tap` тык: нейтральное действие (шаг, переворот карточки, прыжок, нажатие), деревянный брусок.
## `hit` попал: засчитанное действие (блок встал, нота взята, пара сошлась), маримба, часто
## лесенкой по высоте. `miss` мимо: ошибка и промах, тон сползает вниз. `win` готово: раунд или
## вся мини-игра сделаны, две ноты квинтой. `squish` шлёп: мягкое тело коснулось мягкого (упало,
## ткнулось, сплющилось), упругий «батут»; он про физику, а не про результат, поэтому кладётся
## под «попал» или «мимо», а не вместо них, и его высота это вес: ниже тяжелее.
## Каждая функция отдаёт готовый плеер на шине звуков; `freq` высота (0: своя), `pitch` множитель
## высоты без нового синтеза: лесенка это один звук с разными `pitch`.

enum Kind { TAP, HIT, MISS, WIN, SQUISH }

const RATE := Sfx.MIX_RATE
const KIND_NAMES: Array[String] = ["Тык", "Попал", "Мимо", "Готово", "Шлёп"]
const KIND_USE: Array[String] = [
	"нейтральное действие: шаг, прыжок, переворот карточки, нажатие",
	"засчитано: блок встал, нота взята, пара сошлась; идёт лесенкой вверх",
	"ошибка: промах, неверная клавиша, фальстарт",
	"раунд или вся мини-игра сделаны",
	"мармелад коснулся мармелада: упал, ткнулся в стену, сплющился; ниже значит тяжелее"]
const KIND_FREQ: Array[float] = [520.0, 196.0, 220.0, 523.0, 90.0]

static var _cache: Dictionary[int, AudioStreamWAV] = {}


static func tap(freq := 0.0, volume_db := 0.0, pitch := 1.0) -> AudioStreamPlayer:
	return player(Kind.TAP, freq, volume_db, pitch)


static func hit(freq := 0.0, volume_db := 0.0, pitch := 1.0) -> AudioStreamPlayer:
	return player(Kind.HIT, freq, volume_db, pitch)


static func miss(freq := 0.0, volume_db := 0.0, pitch := 1.0) -> AudioStreamPlayer:
	return player(Kind.MISS, freq, volume_db, pitch)


static func win(freq := 0.0, volume_db := 0.0, pitch := 1.0) -> AudioStreamPlayer:
	return player(Kind.WIN, freq, volume_db, pitch)


static func squish(freq := 0.0, volume_db := 0.0, pitch := 1.0) -> AudioStreamPlayer:
	return player(Kind.SQUISH, freq, volume_db, pitch)


static func player(kind: Kind, freq := 0.0, volume_db := 0.0, pitch := 1.0) -> AudioStreamPlayer:
	var p := Sfx.player(make(kind, freq), volume_db)
	p.pitch_scale = pitch
	return p


## Звук вида `kind` высотой `freq` (0: своя высота вида). Синтез один раз на вид и высоту.
static func make(kind: Kind, freq := 0.0) -> AudioStreamWAV:
	var f := freq if freq > 0.0 else KIND_FREQ[kind]
	var key := int(kind) * 100000 + int(round(f * 10.0))
	if _cache.has(key):
		return _cache[key]
	var out: PackedFloat32Array
	match kind:
		Kind.TAP:  # Деревяшка: тон с негармоничным призвуком, как брусок маримбы.
			out = _buf(0.12)
			_tone(out, 0.0, f, f, 1.0, 0.42, 48.0)
			_tone(out, 0.0, f * 2.76, f * 2.76, 1.0, 0.16, 90.0)
		Kind.HIT:  # Маримба: тёплый брусок на октаву выше высоты.
			out = _buf(0.42)
			_tone(out, 0.0, f * 2.0, f * 2.0, 1.0, 0.5, 13.0)
			_tone(out, 0.0, f * 8.0, f * 8.0, 1.0, 0.12, 60.0)
			_tone(out, 0.0, f, f, 1.0, 0.2, 18.0)
		Kind.MISS:  # Съезд вниз: тон уныло сползает.
			out = _buf(0.45)
			_tone(out, 0.0, f * 1.4, f * 0.42, 5.5, 0.5, 6.0, 0.15, 0.01)
		Kind.WIN:  # Две ноты: квинта вверх, мягкие бруски.
			out = _buf(0.75)
			_bar(out, 0.0, f, 0.4)
			_bar(out, 0.11, f * 1.5, 0.45)
		_:  # Батут: сначала проседает под весом, потом выталкивает вверх.
			out = _buf(0.32)
			_tone(out, 0.0, f * 2.4, f * 1.2, 40.0, 0.5, 30.0, 0.0, 0.004)
			_tone(out, 0.06, f * 1.2, f * 3.2, 16.0, 0.45, 15.0, 0.0, 0.015)
	# Хвост без щелчка.
	var n := out.size()
	var tail := int(0.02 * RATE)
	for i in mini(tail, n):
		out[n - 1 - i] *= float(i) / tail
	var wav := Sfx._wav(out)
	_cache[key] = wav
	return wav


# --- Синтез ------------------------------------------------------------------------------------

static func _buf(seconds: float) -> PackedFloat32Array:
	var out := PackedFloat32Array()
	out.resize(int(seconds * RATE))
	return out


## Синус с `start` секунды: высота от `f0` к `f1` со скоростью `glide`, громкость `vol`,
## затухание `decay`, доля второй гармоники `harm`, атака `attack` секунд.
static func _tone(out: PackedFloat32Array, start: float, f0: float, f1: float, glide: float, vol: float,
		decay: float, harm := 0.0, attack := 0.002) -> void:
	var from := int(start * RATE)
	var phase := 0.0
	for i in out.size() - from:
		var tm := float(i) / RATE
		phase += TAU * (f1 + (f0 - f1) * exp(-tm * glide)) / RATE
		var env := minf(1.0, tm / attack) * exp(-tm * decay)
		out[from + i] += (sin(phase) + harm * sin(phase * 2.0)) * env * vol


## Мягкий брусок: нота с тихим верхним призвуком, для мелодии «готово».
static func _bar(out: PackedFloat32Array, start: float, f: float, vol: float) -> void:
	_tone(out, start, f, f, 1.0, vol, 8.0, 0.0, 0.003)
	_tone(out, start, f * 4.0, f * 4.0, 1.0, vol * 0.2, 40.0, 0.0, 0.003)
