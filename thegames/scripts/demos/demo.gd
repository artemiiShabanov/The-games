class_name Demo
extends Control
## Базовый класс демки, спека `docs/specs/demos.md`. Хозяин делает `setup(record, source)`,
## добавляет в дерево и зовёт `start()`. Демка идёт в большой карточке `CardFrame` поверх
## студии, как спринты (решение 2026-11-06): карточка всплывает, экран демки в `screen`,
## после итога карточка уезжает вниз и приходит `demo_finished`. Таймера нет (решение
## 2026-11-05): демка кончается по своей цели или по своему условию провала (жизни, счёт),
## затем короткий экран итога («добежал» / «не добежал», слова жанра в `_result_title`).
## Esc открывает паузу с пунктами «Вернуться» и «Пропустить» (решение 2026-11-06); B
## остаётся демке, у платформера это дэш, у гонок тормоз.
## Подклассы переопределяют `_game_input`, а не `_unhandled_input`. Баги читаются флагами из
## записи: `has_bug(&"wild_physics")`. Общие баги (#44) живут здесь и работают в любой
## демке: фризы `frame_drops` (`bug_frame`), заикание звука `audio_stutter` (`bug_music`,
## `bug_play`, `bug_audio_tick`), ввод с опозданием и залипанием `sticky_input` (`bug_axis`,
## `bug_press`, `bug_input_tick`, `bug_stick`, `bug_take_stick`), розовые заглушки
## `pink_placeholders` по слотам спрайтов демки (`_placeholder_slots`, `is_pink`,
## `draw_pink`), чужая палитра `alien_palette` (`bug_palette` на слой мира) и мерцание 8-bit
## `sprite_flicker` (`flicker_reset`, `flicker_hidden`). Векторные демки (#88) рисуют на
## экране `vector_screen(draw_fn)`: слоты сеттинга контурами (`draw_slot`), розовая заглушка это
## розовый квадрат с крестом вместо контура, чужая палитра на всём экране; баг технологии
## вектора `beam_lag` «луч не успевает» (#89) включается там же и живёт в самом экране
## (`VectorScreen.set_beam_lag`), демке его звать не надо. Демки 16/32-bit (#95) рисуют на
## экране `bit16_screen(...)`: ленты кадров сеттинга (`draw_sprite16`), заглушка это розовый
## блок в шашку, чужая палитра на слое мира; баг технологии 16/32 `layer_tear` «слои
## вразнобой» (#97) включается там же (разрывы кадра в `Bit16Screen`) и в фоне `parallax16()`
## (слои едут в разные стороны), демке его звать не надо. Демки low poly (#108) строят 3D-сцену
## на экране `lowpoly_screen(draw_hud)`: модели слотов через `spawn_model`, заглушка это розовый
## ящик в шашку по габаритам модели, чужая палитра сдвигает оттенок материалов. Демка зовёт эти хуки в своих местах и
## не держит механику у себя; баги баланса и жанра (недостижимая цель, враги от чиха, дикая
## физика) остаются проявлениями самой демки. Встроенный режим (`embed(size)`, #26): без карточки и
## ввода, своего размера, бот играет сам, звук выключен; так демка крутится как запись стрима
## в ленте.

signal demo_started(record: GameRecord, source: StringName)
signal demo_finished(record: GameRecord, reached_goal: bool)

const RESULT_SECONDS := 1.8
## Розовая заглушка вместо спрайта (`pink_placeholders`).
const PINK := Color("#FF2BD6")
## Заикание музыки: длина залипания и кусок, который повторяется.
const STUTTER_SECONDS := 0.35
const STUTTER_CHUNK := 0.07
## Сколько живут отрезки рассыпавшегося контура (`shatter_slot`).
const SHARD_LIFE := 0.6
## Чужая палитра: сдвиг оттенка всего слоя мира (`alien_palette`).
const HUE_SHADER := """
shader_type canvas_item;
uniform float hue_shift = 0.45;
vec3 rgb2hsv(vec3 c) {
	vec4 K = vec4(0.0, -1.0 / 3.0, 2.0 / 3.0, -1.0);
	vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
	vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));
	float d = q.x - min(q.w, q.y);
	float e = 1.0e-10;
	return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);
}
vec3 hsv2rgb(vec3 c) {
	vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
	vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
	return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}
void fragment() {
	vec4 c = texture(TEXTURE, UV) * COLOR;
	vec3 hsv = rgb2hsv(c.rgb);
	hsv.x = fract(hsv.x + hue_shift);
	COLOR = vec4(hsv2rgb(hsv), c.a);
}
"""
const MENU_ITEMS: Array[String] = ["Вернуться", "Пропустить"]
## Пиксельные цифры 3×5 для HUD демок 8-bit (`draw_pixel_text`), плюс «/» для места в гонке,
## «+», «-», «°» и буквы «ПАР» для гольфа (#52), «KO» и «ВРЕМЯ» для файтинга (#54).
const PIXEL_DIGITS := {
	"0": ["111", "101", "101", "101", "111"], "1": ["010", "110", "010", "010", "111"],
	"2": ["111", "001", "111", "100", "111"], "3": ["111", "001", "111", "001", "111"],
	"4": ["101", "101", "111", "001", "001"], "5": ["111", "100", "111", "001", "111"],
	"6": ["111", "100", "111", "101", "111"], "7": ["111", "001", "001", "001", "001"],
	"8": ["111", "101", "111", "101", "111"], "9": ["111", "101", "111", "001", "111"],
	"/": ["001", "001", "010", "100", "100"],
	"+": ["000", "010", "111", "010", "000"], "-": ["000", "000", "111", "000", "000"],
	"°": ["010", "101", "010", "000", "000"],
	"П": ["111", "101", "101", "101", "101"], "А": ["010", "101", "111", "101", "101"],
	"Р": ["111", "101", "111", "100", "100"],
	"K": ["101", "101", "110", "101", "101"], "O": ["111", "101", "101", "101", "111"],
	"В": ["110", "101", "110", "101", "110"], "Е": ["111", "100", "110", "100", "111"],
	"М": ["101", "111", "111", "101", "101"], "Я": ["011", "101", "011", "101", "101"],
}

var record: GameRecord
var source: StringName = &"debug"
## Секунды с начала, для подписи итога.
var elapsed := 0.0
var running := false
var paused := false
var reached := false
var finished := false
## Область под экран демки внутри карточки; размер `CardFrame.inner_size()`.
var screen: Control
var card: CardFrame
## Встроенный режим: размер экрана, бот вместо игрока, без звука и карточки.
var embedded := false
var embed_size := Vector2.ZERO
var bot_mode := AutoTest.BotMode.WIN
var _result_left := 0.0
var _closing := false
var _menu_index := 0
var _overlay: Control
var _overlay_title: Label
var _overlay_caption: Label
var _menu_row: HBoxContainer
var _menu_pills: Array[PanelContainer] = []
var _menu_labels: Array[Label] = []
var _menu_lifts: Array[JellyLift] = []
var _menu_hint: Control

# Общие баги (#44).
## Случайность багов из сида записи: проявления повторяются от запуска к запуску.
var bug_rng := RandomNumberGenerator.new()
## Музыка демки для заикания; демка ставит свою после создания плеера.
var bug_music: AudioStreamPlayer
var _freeze_timer := 0.0
var _freeze_left := 0.0
var _frozen := 0.0
var _stutter_timer := 0.0
var _stutter_left := 0.0
var _stutter_pos := 0.0
var _stutter_chunk := 0.0
var _axis_log: Array[Vector3] = []
var _press_queue: Array[Array] = []
var _sticky_extra := 0
var _sticky_first := true
var _pink: Dictionary[String, bool] = {}
var _palette: ShaderMaterial
var _flicker_limit := 0
var _line_counts: Dictionary[int, int] = {}
## Векторный экран демки и сеттинг записи (`vector_screen`).
var vector: VectorScreen
var vector_set: SettingDef
## Экран 16/32-bit демки и сеттинг записи (`bit16_screen`).
var bit16: Bit16Screen
var bit16_set: SettingDef
## Экран low poly демки и сеттинг записи (`lowpoly_screen`).
var lowpoly: LowpolyScreen
var lowpoly_set: SettingDef
## Отрезки рассыпавшихся контуров (`shatter_slot`): [a, b, скорость, возраст, чернила].
var _shards: Array[Array] = []
var _shard_rng := RandomNumberGenerator.new()


func setup(record_: GameRecord, source_: StringName) -> void:
	record = record_
	source = source_


## Встроить демку в чужой экран: размер в пикселях, бот играет, без звука.
func embed(size_: Vector2, mode := AutoTest.BotMode.WIN) -> void:
	embedded = true
	embed_size = size_
	bot_mode = mode


func start() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	if embedded:
		size = embed_size
		screen = self
		_setup_common_bugs()
		_on_start()
		running = true
		demo_started.emit(record, source)
		return
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	card = CardFrame.new()
	add_child(card)
	screen = Control.new()
	screen.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	screen.mouse_filter = Control.MOUSE_FILTER_IGNORE
	card.content.add_child(screen)
	_build_overlay()
	_setup_common_bugs()
	_on_start()
	await card.raise_card()
	running = true
	demo_started.emit(record, source)


## Бот ведёт демку: под автотестом или во встроенном режиме.
func bot_driven() -> bool:
	return embedded or AutoTest.bot_active()


## Режим бота: свой во встроенном режиме, иначе автотеста.
func active_bot_mode() -> AutoTest.BotMode:
	return bot_mode if embedded else AutoTest.bot_mode


func has_bug(id: StringName) -> bool:
	return record != null and record.has_bug(id)


# --- Общие баги (#44) ------------------------------------------------------------------------

## Слоты спрайтов, которые могут стать розовыми заглушками; герой и земля никогда. Демка
## переопределяет.
func _placeholder_slots() -> Array[String]:
	return []


func _setup_common_bugs() -> void:
	bug_rng.seed = hash(str(record.seed, ":bugs")) if record != null else 1
	if has_bug(&"frame_drops"):
		_freeze_timer = 1.0
	if has_bug(&"audio_stutter"):
		_stutter_timer = 1.5
	if has_bug(&"sprite_flicker"):
		_flicker_limit = int(bug_param(&"sprite_flicker", &"max_per_line", 3.0))
	if has_bug(&"alien_palette"):
		var shader := Shader.new()
		shader.code = HUE_SHADER
		_palette = ShaderMaterial.new()
		_palette.shader = shader
		_palette.set_shader_parameter("hue_shift", bug_param(&"alien_palette", &"hue_shift", 0.45))
	if has_bug(&"pink_placeholders"):
		var share := bug_param(&"pink_placeholders", &"share", 0.35)
		var slots := _placeholder_slots().duplicate()
		var count := mini(maxi(1, int(round(slots.size() * share))), slots.size())
		for i in count:
			var k := bug_rng.randi_range(0, slots.size() - 1)
			_pink[slots[k]] = true
			slots.remove_at(k)


## Параметр бага из каталога: `bug_param(&"frame_drops", &"period_s", 2.5)`.
func bug_param(bug_id: StringName, name: StringName, default: float) -> float:
	var catalog := BugCatalog.load_default()
	var bug := catalog.by_id(bug_id) if catalog != null else null
	return bug.param(name, default) if bug != null else default


## Кадр мира с фризами: `step(dt)` один раз; с `frame_drops` во время движения (`moving`) мир
## замирает на 200-400 мс, время копится и догоняется тремя шагами. true, если мир шагнул
## (демке пора перерисовать слой).
func bug_frame(delta: float, moving: bool, step: Callable) -> bool:
	if has_bug(&"frame_drops"):
		if _freeze_left > 0.0:
			_freeze_left -= delta
			_frozen += delta
			if _freeze_left > 0.0:
				return false
			for i in 3:
				step.call(_frozen / 3.0)
			_frozen = 0.0
			return true
		_freeze_timer -= delta
		if _freeze_timer <= 0.0 and moving:
			var lo := bug_param(&"frame_drops", &"freeze_ms_min", 200.0)
			var hi := bug_param(&"frame_drops", &"freeze_ms_max", 400.0)
			_freeze_left = bug_rng.randf_range(lo, hi) / 1000.0
			_freeze_timer = bug_param(&"frame_drops", &"period_s", 2.5) * bug_rng.randf_range(0.7, 1.3)
			return false
	step.call(delta)
	return true


## Звук демки: с `audio_stutter` с задержкой.
func bug_play(p: AudioStreamPlayer) -> void:
	if has_bug(&"audio_stutter"):
		get_tree().create_timer(bug_param(&"audio_stutter", &"delay_ms", 350.0) / 1000.0).timeout.connect(p.play)
	else:
		p.play()


## Заикание музыки `bug_music`: раз в несколько секунд кусок повторяется. Звать каждый кадр.
func bug_audio_tick(delta: float) -> void:
	if not has_bug(&"audio_stutter") or bug_music == null or not bug_music.playing:
		return
	if _stutter_left > 0.0:
		_stutter_left -= delta
		_stutter_chunk -= delta
		if _stutter_chunk <= 0.0:
			bug_music.seek(_stutter_pos)
			_stutter_chunk = STUTTER_CHUNK
		return
	_stutter_timer -= delta
	if _stutter_timer <= 0.0:
		_stutter_left = STUTTER_SECONDS
		_stutter_pos = bug_music.get_playback_position()
		_stutter_chunk = STUTTER_CHUNK
		_stutter_timer = bug_param(&"audio_stutter", &"stutter_period_s", 3.0) * bug_rng.randf_range(0.8, 1.2)


## Направление ввода: с `sticky_input` из прошлого на `delay_ms`. Звать раз за шаг мира.
func bug_axis(raw: Vector2) -> Vector2:
	if not has_bug(&"sticky_input"):
		return raw
	_axis_log.append(Vector3(elapsed, raw.x, raw.y))
	var delay := bug_param(&"sticky_input", &"delay_ms", 120.0) / 1000.0
	var value := raw
	for sample in _axis_log:
		if sample.x <= elapsed - delay:
			value = Vector2(sample.y, sample.z)
	while _axis_log.size() > 0 and _axis_log[0].x < elapsed - delay - 0.5:
		_axis_log.remove_at(0)
	return value


## Нажатие действия: сразу, а с `sticky_input` через `delay_ms` (`bug_input_tick` выполняет).
func bug_press(action: Callable) -> void:
	if has_bug(&"sticky_input"):
		_press_queue.append([elapsed + bug_param(&"sticky_input", &"delay_ms", 120.0) / 1000.0, action])
	else:
		action.call()


## Выполнить отложенные нажатия, чей срок пришёл. Звать в начале шага мира.
func bug_input_tick() -> void:
	while not _press_queue.is_empty() and float(_press_queue[0][0]) <= elapsed:
		var action: Callable = _press_queue.pop_front()[1]
		action.call()


## Действие удалось: с `sticky_input` кнопка может залипнуть и повториться ещё `extra_presses`
## раз (первое залипает всегда, чтобы баг был виден сразу, дальше по шансу).
func bug_stick() -> void:
	if not has_bug(&"sticky_input") or _sticky_extra > 0:
		return
	if _sticky_first or bug_rng.randf() < bug_param(&"sticky_input", &"stick_chance", 0.25):
		_sticky_extra = int(bug_param(&"sticky_input", &"extra_presses", 2.0))
	_sticky_first = false


## Демка в удобный для повтора момент (платформер: приземление) спрашивает, повторить ли
## залипшее нажатие.
func bug_take_stick() -> bool:
	if _sticky_extra <= 0:
		return false
	_sticky_extra -= 1
	return true


func bug_clear_stick() -> void:
	_sticky_extra = 0


func is_pink(slot: String) -> bool:
	return _pink.has(slot)


func draw_pink(canvas: CanvasItem, rect: Rect2) -> void:
	canvas.draw_rect(rect, PINK)


## Материал чужой палитры для слоя мира или null.
func bug_palette() -> ShaderMaterial:
	return _palette


## Мерцание 8-bit: сбросить счёт спрайтов на строках в начале кадра рисования.
func flicker_reset() -> void:
	_line_counts.clear()


## Спрайт на строке `line` сверх лимита виден только через кадр.
func flicker_hidden(line: int) -> bool:
	if _flicker_limit <= 0:
		return false
	var n: int = _line_counts.get(line, 0) + 1
	_line_counts[line] = n
	return n > _flicker_limit and (Engine.get_process_frames() + n) % 2 == 1


# --- Вектор (#88) -------------------------------------------------------------------------

## Векторный экран на всю область демки, цвета сеттинга записи, чужая палитра при баге.
## Координаты логические, по карточке демки; во встроенном режиме тот же экран уменьшен.
func vector_screen(draw_fn: Callable) -> VectorScreen:
	vector_set = SettingDef.of(record.setting if record != null else Game.Setting.PIRATES)
	var logical := CardFrame.inner_size()
	var area: Vector2 = embed_size if embedded else logical
	vector = VectorScreen.make(area, logical, vector_set.vector_colors)
	vector.draw_fn = draw_fn
	vector.glow = Debug.vector_glow
	vector.persistence = Debug.vector_persistence
	_shard_rng.seed = hash(str(record.seed if record != null else 1, ":shards"))
	if bug_palette() != null:
		vector.material = bug_palette()
	if has_bug(&"beam_lag"):
		vector.set_beam_lag(int(bug_param(&"beam_lag", &"budget", 140.0)), bug_param(&"beam_lag", &"min_keep", 0.5),
				bug_param(&"beam_lag", &"jitter_px", 2.5), bug_param(&"beam_lag", &"ghost_px", 5.0),
				bug_param(&"beam_lag", &"ghost_alpha", 0.4), bug_param(&"beam_lag", &"gap_px", 7.0),
				hash(str(record.seed, ":beam")))
	screen.add_child(vector)
	return vector


## Слот сеттинга контуром: `px` логических пикселей на пиксель спрайта; розовая заглушка
## квадратом с крестом. Звать из `draw_fn`.
func draw_slot(slot: StringName, center: Vector2, px: float, flip := false, angle := 0.0) -> void:
	if is_pink(String(slot)):
		vector.cross_box(center, 14.0 * px)
		return
	vector.shape(vector_set.vector_contours(slot), center, px, vector_set.vector_ink(slot), flip, angle)


# --- 16/32-bit (#95) ----------------------------------------------------------------------

## Экран 16/32 на всю область демки: палитра сеттинга записи, чужая палитра при баге ложится на
## слой мира. Демка рисует в трёх колбэках (фон, мир, HUD), каждый получает свой слой; `scale`
## увеличение экрана, ×3 для крупного плана.
func bit16_screen(draw_backdrop: Callable, draw_world: Callable, draw_hud: Callable, scale := Bit16Screen.SCALE) -> Bit16Screen:
	bit16_set = SettingDef.of(record.setting if record != null else Game.Setting.PIRATES)
	bit16 = Bit16Screen.make(embed_size if embedded else CardFrame.inner_size(), embedded, bit16_set.colors16(), scale)
	bit16.draw_backdrop = draw_backdrop
	bit16.draw_world = draw_world
	bit16.draw_hud = draw_hud
	if bug_palette() != null:
		bit16.world.material = bug_palette()
	if has_bug(&"layer_tear"):
		bit16.set_tear(bug_param(&"layer_tear", &"period_s", 2.4), bug_param(&"layer_tear", &"tear_s", 0.5),
				bug_param(&"layer_tear", &"shift_px", 18.0), hash(str(record.seed, ":tear")))
	screen.add_child(bit16)
	return bit16


## Фон вида сбоку для демки 16/32. С багом технологии `layer_tear` (#97) слои едут вразнобой:
## облака навстречу, берег быстрее и в свою сторону, вода назад; ленты слоёв рвёт пополам.
## Свои слои демки: имена лент, доли скорости и верх на экране (`Parallax16.of_layers`).
func parallax16(names: Array[String] = [], factors: Array[float] = [], tops: Array[float] = []) -> Parallax16:
	var p := Parallax16.of(bit16_set) if names.is_empty() else Parallax16.of_layers(bit16_set, names, factors, tops)
	if has_bug(&"layer_tear"):
		p.bug_dir = [bug_param(&"layer_tear", &"dir_sky", -3.0), bug_param(&"layer_tear", &"dir_far", 2.2),
				bug_param(&"layer_tear", &"dir_mid", -1.0)]
		p.bug_tear = bug_param(&"layer_tear", &"strip_tear_px", 14.0)
	return p


## Кадр ленты спрайта низом в точке `feet`; слот с розовой заглушкой рисуется блоком в шашку.
func draw_sprite16(canvas: CanvasItem, slot: String, tex: Texture2D, frame: int, feet: Vector2, flip := false,
		scale := 1.0) -> void:
	if is_pink(slot):
		bit16.pink(canvas, feet, scale, float(tex.get_height()) if tex != null else 32.0)
	else:
		bit16.sprite(canvas, tex, frame, feet, flip, scale)


# --- Low poly (#108) -----------------------------------------------------------------------

## Экран low poly на всю область демки: 3D-сцена в духе первой PlayStation с небом сеттинга
## записи, HUD рисуется в колбэке поверх неё. Чужая палитра при баге ложится на материалы мира.
func lowpoly_screen(draw_hud: Callable) -> LowpolyScreen:
	lowpoly_set = SettingDef.of(record.setting if record != null else Game.Setting.PIRATES)
	lowpoly = LowpolyScreen.make(embed_size if embedded else CardFrame.inner_size(), embedded,
			lowpoly_set.colors_lowpoly(), lowpoly_set.sky_lowpoly(), lowpoly_set.texture_lowpoly("sky"), Debug.lowpoly_scale)
	lowpoly.draw_hud = draw_hud
	if has_bug(&"alien_palette"):
		lowpoly.set_alien(bug_param(&"alien_palette", &"hue_shift", 0.45))
	screen.add_child(lowpoly)
	return lowpoly


## Модель слота сеттинга в мире демки; слот с розовой заглушкой приходит розовым ящиком.
func spawn_model(slot: String, name: String, parent: Node3D = null) -> LowpolyModel:
	var def := lowpoly_set.model(name)
	var m := lowpoly.pink_model(def) if is_pink(slot) else lowpoly.model(def)
	(parent if parent != null else lowpoly.world).add_child(m)
	return m


## Текстура уровня сеттинга записи для демки low poly: `sand`, `planks`, `water`, `rock`, `sail`.
func lowpoly_texture(name: String) -> Texture2D:
	return lowpoly_set.texture_lowpoly(name)


## Контур слота рассыпается на отрезки (враг от чиха, разбитое препятствие, потерянная жизнь):
## каждый отрезок летит от центра, падает и гаснет за `SHARD_LIFE`. `drift` общая скорость
## обломков (например, дорога уезжает назад). Демка зовёт `step_shards` в шаге мира и
## `draw_shards` в `draw_fn`.
func shatter_slot(slot: StringName, center: Vector2, px: float, ink_i: int, flip := false, angle := 0.0,
		drift := Vector2.ZERO) -> void:
	if vector_set == null:
		return
	var xf := Transform2D(angle, Vector2.ZERO).scaled_local(Vector2(-px if flip else px, px))
	for c in vector_set.vector_contours(slot):
		for i in c.size():
			var a := xf * c[i]
			var b := xf * c[(i + 1) % c.size()]
			var out := ((a + b) / 2.0).normalized()
			var vel := out * _shard_rng.randf_range(120.0, 340.0) + Vector2(0.0, -90.0) + drift
			_shards.append([center + a, center + b, vel, 0.0, ink_i])


## То же для своего замкнутого контура в координатах экрана (ракетка, фигура не из слотов).
func shatter_poly(points: PackedVector2Array, ink_i: int, drift := Vector2.ZERO) -> void:
	var center := Vector2.ZERO
	for q in points:
		center += q
	center /= maxf(points.size(), 1.0)
	for i in points.size():
		var a := points[i]
		var b := points[(i + 1) % points.size()]
		var out := ((a + b) / 2.0 - center).normalized()
		var vel := out * _shard_rng.randf_range(120.0, 340.0) + Vector2(0.0, -90.0) + drift
		_shards.append([a, b, vel, 0.0, ink_i])


func step_shards(dt: float) -> void:
	for i in range(_shards.size() - 1, -1, -1):
		var s := _shards[i]
		var vel: Vector2 = s[2]
		vel.y += 520.0 * dt
		s[0] = (s[0] as Vector2) + vel * dt
		s[1] = (s[1] as Vector2) + vel * dt
		s[2] = vel
		s[3] = float(s[3]) + dt
		if float(s[3]) >= SHARD_LIFE:
			_shards.remove_at(i)


func draw_shards() -> void:
	for s in _shards:
		vector.line(s[0], s[1], int(s[4]), 2.0, 1.0 - float(s[3]) / SHARD_LIFE)


## Строка пиксельными цифрами `PIXEL_DIGITS` клетками `cell` с тенью на клетку вправо-вниз.
func draw_pixel_text(canvas: CanvasItem, pos: Vector2, text: String, ink: Color, shadow: Color, cell := 2.0) -> void:
	for i in text.length():
		var rows: Array = PIXEL_DIGITS.get(text[i], [])
		for ry in rows.size():
			for rx in 3:
				if rows[ry][rx] == "1":
					var r := Rect2(pos + Vector2(i * 4 * cell + rx * cell, ry * cell), Vector2(cell, cell))
					canvas.draw_rect(Rect2(r.position + Vector2(cell, cell) / 2.0, r.size), shadow)
					canvas.draw_rect(r, ink)


## Итог: по цели (true) или по условию провала демки (false). Экран итога, потом сигнал.
func end_demo(goal: bool) -> void:
	if not running:
		return
	running = false
	paused = false
	reached = goal
	_on_end(goal)
	if not embedded:
		_show_overlay(_result_title(goal), _result_caption(), Style.SUCCESS if goal else Style.INK)
	_result_left = RESULT_SECONDS


## Пропустить: без экрана итога, сразу наружу.
func quit_demo() -> void:
	if finished or _closing:
		return
	running = false
	paused = false
	_close(false)


func _close(result: bool) -> void:
	_closing = true
	if card != null:
		await card.drop_card()
	finished = true
	demo_finished.emit(record, result)


func _process(delta: float) -> void:
	if _result_left > 0.0:
		_result_left -= delta
		if _result_left <= 0.0 and not finished and not _closing:
			_close(reached)
		return
	if not running or paused:
		return
	elapsed += delta
	if bot_driven():
		_bot_step(delta)
	_on_tick(delta)


func _unhandled_input(event: InputEvent) -> void:
	if embedded:
		return
	if _shell_input(event):
		get_viewport().set_input_as_handled()
	elif running and not paused:
		_game_input(event)


## Пауза и её меню. Возвращает true, если событие съедено оболочкой.
func _shell_input(event: InputEvent) -> bool:
	if not running or _closing:
		return false
	if not paused:
		if _is_escape(event):
			_open_pause()
			return true
		return false
	if MouseUi.is_click(event):
		for i in _menu_pills.size():
			if MouseUi.hit(_menu_pills[i], event):
				_menu_index = i
				_refresh_menu()
				if i == 0:
					_resume()
				else:
					quit_demo()
				return true
		return false
	if MouseUi.is_mouse(event):
		return false
	if GameInput.is_b(event):
		_resume()
	elif GameInput.is_a(event):
		if _menu_index == 0:
			_resume()
		else:
			quit_demo()
	elif event.is_action_pressed(GameInput.LEFT) or event.is_action_pressed(GameInput.UP) \
			or event.is_action_pressed(GameInput.RIGHT) or event.is_action_pressed(GameInput.DOWN):
		_menu_index = 1 - _menu_index
		_refresh_menu()
		ShellSounds.play(&"tick")
	else:
		return false
	return true


static func _is_escape(event: InputEvent) -> bool:
	var key := event as InputEventKey
	return key != null and key.pressed and not key.echo and key.keycode == KEY_ESCAPE


func _open_pause() -> void:
	paused = true
	_menu_index = 0
	_show_overlay("пауза", "", Style.INK)
	_menu_row.visible = true
	_menu_hint.visible = true
	_refresh_menu()


func _resume() -> void:
	paused = false
	_overlay.visible = false


# --- Переопределяемое -----------------------------------------------------------------------

func _on_start() -> void:
	pass


func _on_tick(_delta: float) -> void:
	pass


func _on_end(_goal: bool) -> void:
	pass


func _bot_step(_delta: float) -> void:
	pass


## Ввод самой демки: приходит только на ходу, вне паузы.
func _game_input(_event: InputEvent) -> void:
	pass


## Подпись на экране итога: монеты, время и т.п.
func _result_caption() -> String:
	return ""


## Заголовок экрана итога словами жанра: у платформера «добежал», у гонок «добрался первым».
func _result_title(goal: bool) -> String:
	return "добежал" if goal else "не добежал"


# --- Оверлей итога и паузы в стиле оболочки ------------------------------------------------

func _build_overlay() -> void:
	_overlay = Control.new()
	_overlay.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_overlay.visible = false
	card.content.add_child(_overlay)
	var dim := ColorRect.new()
	dim.color = Color(Style.BG, 0.55)
	dim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	dim.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_overlay.add_child(dim)
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", Style.card(true))
	panel.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	panel.grow_horizontal = Control.GROW_DIRECTION_BOTH
	panel.grow_vertical = Control.GROW_DIRECTION_BOTH
	_overlay.add_child(panel)
	Jelly.panel(panel)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 12)
	panel.add_child(column)
	_overlay_title = Label.new()
	_overlay_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_overlay_title.add_theme_font_size_override("font_size", Style.FONT_VERB)
	column.add_child(_overlay_title)
	_overlay_caption = Label.new()
	_overlay_caption.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_overlay_caption.add_theme_font_size_override("font_size", Style.FONT_H2)
	_overlay_caption.add_theme_color_override("font_color", Style.INK_2)
	column.add_child(_overlay_caption)
	_menu_row = HBoxContainer.new()
	_menu_row.alignment = BoxContainer.ALIGNMENT_CENTER
	_menu_row.add_theme_constant_override("separation", Style.GAP_CARDS)
	_menu_row.visible = false
	column.add_child(_menu_row)
	for text in MENU_ITEMS:
		var pill := PanelContainer.new()
		pill.custom_minimum_size = Vector2(280, Style.BUTTON_HEIGHT)
		var l := Label.new()
		l.text = text
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		l.add_theme_font_size_override("font_size", Style.FONT_H2)
		pill.add_child(l)
		_menu_row.add_child(pill)
		_menu_pills.append(pill)
		_menu_labels.append(l)
		_menu_lifts.append(Jelly.button(pill))
	_menu_hint = HBoxContainer.new()
	(_menu_hint as HBoxContainer).alignment = BoxContainer.ALIGNMENT_CENTER
	_menu_hint.add_child(HintPill.make("%s %s выбрать · %s подтвердить · %s вернуться" % [
			GameInput.key(GameInput.LEFT), GameInput.key(GameInput.RIGHT),
			GameInput.key(GameInput.A), GameInput.key(GameInput.B)]))
	_menu_hint.visible = false
	column.add_child(_menu_hint)
	MouseUi.pass_through(_overlay)


## Выбранный пункт: заливка `ink` и толщина фокуса (мармелад); остальные `surface-2`.
func _refresh_menu() -> void:
	for i in _menu_pills.size():
		var on := i == _menu_index
		_menu_pills[i].add_theme_stylebox_override("panel",
				Style.flat(Style.INK if on else Style.SURFACE_2, Style.R_CTL, Color.TRANSPARENT, 0))
		_menu_lifts[i].focused = on
		_menu_labels[i].add_theme_color_override("font_color", Style.SURFACE_SOLID if on else Style.INK)


func _show_overlay(title: String, caption: String, color: Color) -> void:
	_overlay_title.text = title
	_overlay_title.add_theme_color_override("font_color", color)
	_overlay_caption.text = caption
	_overlay_caption.visible = caption != ""
	_menu_row.visible = false
	_menu_hint.visible = false
	_overlay.visible = true
	_overlay.move_to_front()
