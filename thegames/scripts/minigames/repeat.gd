extends Minigame
## «Повтори» (repeat, управление), каталог `docs/specs/minigames_catalog.md`.
## Шесть клавиш-площадок: крестовина слева, A и B справа. Последовательность из 4-7 клавиш
## показывается вспышками, у каждой клавиши свой тон, затем игрок повторяет. Четыре раунда до
## конца таймера; провал, если не успел или набрал `MAX_ERRORS` ошибок (плейтест 2026-11-06).
## Неверная клавиша: ошибка в счётчик слева сверху, она дрожит красным, после короткой паузы
## та же последовательность показывается заново, во время показа ввод не принимается, затем
## ввод с первой клавиши (плейтесты 2026-11-05 и 2026-11-06).
## С `t` последовательность длиннее, показ быстрее, появляются ложные вспышки, которые надо
## пропустить мимо.
## Параметры от `t` в `resources/minigames/repeat.tres`: length, show, fake_share.
## Мармелад (STYLE «Мармелад»): клавиши мягкие `JellyShape`, вспыхнувшая клавиша вминается и
## встаёт на бортик темнее себя, верное нажатие расходится тихим кругом и парой неярких капель,
## собранная последовательность брызгает чуть больше, неверное нажатие трясёт клавишу вбок;
## точки прогресса, раундов и ошибок мягко вспухают при смене. В покое вид прежний.

enum Phase { SHOW, INPUT, PAUSE }

const KEYS: Array[StringName] = [GameInput.LEFT, GameInput.UP, GameInput.DOWN, GameInput.RIGHT, GameInput.A, GameInput.B]
const TONES: Array[float] = [392.0, 440.0, 494.0, 523.0, 587.0, 659.0]
const ROUNDS := 4
const MAX_ERRORS := 4
const PAD := 140.0
const PAD_GAP := 20.0
const GAP_SECONDS := 0.12
const FAKE_SECONDS := 0.14
const PRESS_SECONDS := 0.22
const ROUND_PAUSE := 0.5
const START_DELAY := 0.5
const SHAKE_SECONDS := 0.35
const BOT_STEP := 0.18

var seq_length := 4
var show_seconds := 0.35
var fake_share := 0.0

var phase := Phase.PAUSE
var round_index := 0
var rounds_done := 0
var errors := 0
## После ошибки: по концу паузы не новый раунд, а повторный показ той же последовательности.
var _replay := false
var _seq_snapshot: Array[int] = []
var sequence: Array[int] = []
var step := 0
var phase_time := 0.0
var pause_left := START_DELAY
var fake_key := -1
var fake_left := 0.0
var lit: Array[float] = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
var lit_color: Array[Color] = []
var shake: Array[float] = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
var _players: Array[AudioStreamPlayer] = []
var _miss_sound: AudioStreamPlayer
var _bot_timer := 0.0

# Мармелад: только рисование, на игру не влияет.
var _pads: Array[JellyShape] = []
var _lift: Array[JellySpring] = []
var _rings := RingFx.new()
var _splash := SplashFx.new()
var _fake_shown := false
## Вспухание точек: прогресс, раунды, ошибки; состояние, чтобы заметить смену.
var _dot_pop: Array[JellySpring] = []
var _dot_state: Array[int] = []
var _round_pop: Array[JellySpring] = []
var _round_state: Array[int] = []
var _err_pop: Array[JellySpring] = []
var _err_state: Array[int] = []


func _on_start() -> void:
	seq_length = int(round(def.param(&"length", t, 4.0)))
	show_seconds = def.param(&"show", t, 0.35)
	fake_share = def.param(&"fake_share", t, 0.0)
	for i in KEYS.size():
		lit_color.append(Style.accent(0))
		var p := Sfx.player(Sfx.blip(TONES[i], 0.18, 0.45, 14.0))
		add_child(p)
		_players.append(p)
	_miss_sound = Sfx.player(Sfx.thud())
	add_child(_miss_sound)
	for i in KEYS.size():
		_pads.append(JellyShape.rect(Vector2(PAD, PAD), Style.R_CTL))
		_lift.append(JellySpring.new())
	for j in ROUNDS:
		_round_pop.append(JellySpring.new())
		_round_state.append(0)
	for j in MAX_ERRORS:
		_err_pop.append(JellySpring.new())
		_err_state.append(0)
	queue_redraw()


func _unhandled_input(event: InputEvent) -> void:
	if not running or event.is_echo():
		return
	var action := GameInput.action_of(event)
	if action == &"" or not event.is_action_pressed(action):
		return
	_press(KEYS.find(action))
	get_viewport().set_input_as_handled()


func _on_tick(delta: float) -> void:
	for i in KEYS.size():
		lit[i] = maxf(lit[i] - delta, 0.0)
		shake[i] = maxf(shake[i] - delta, 0.0)
	fake_left = maxf(fake_left - delta, 0.0)
	phase_time += delta
	match phase:
		Phase.PAUSE:
			pause_left -= delta
			if pause_left <= 0.0:
				if _replay:
					_replay = false
					if AutoTest.enabled and sequence != _seq_snapshot:
						AutoTest.fail("repeat: последовательность изменилась после ошибки")
					_show_sequence()
				else:
					_start_round()
		Phase.SHOW:
			# Каждый шаг: вспышка `show_seconds`, пауза `GAP_SECONDS`; ложная вспышка между ними.
			var slot := show_seconds + GAP_SECONDS
			var idx := int(phase_time / slot)
			if idx >= sequence.size():
				phase = Phase.INPUT
				phase_time = 0.0
				step = 0
				_bot_timer = 0.0
			elif idx > step:
				step = idx
				_flash(sequence[step], Style.accent(0))
				_maybe_fake()
		Phase.INPUT:
			pass
	queue_redraw()


func _on_timeout() -> bool:
	return rounds_done >= ROUNDS


## Бот: WIN жмёт нужную клавишу каждые `BOT_STEP`, LOSE жмёт не ту.
func _bot_step(delta: float) -> bool:
	if phase != Phase.INPUT:
		return false
	_bot_timer += delta
	if _bot_timer < BOT_STEP:
		return false
	_bot_timer = 0.0
	var want := sequence[step]
	if AutoTest.bot_mode == AutoTest.BotMode.WIN:
		_press(want)
	else:
		_press((want + 1) % KEYS.size())
	return false


func _start_round() -> void:
	sequence.clear()
	var prev := -1
	for i in seq_length:
		var k := rng.randi_range(0, KEYS.size() - 1)
		if k == prev:
			k = (k + 1 + rng.randi_range(0, KEYS.size() - 2)) % KEYS.size()
		sequence.append(k)
		prev = k
	_show_sequence()


## Показ текущей последовательности с первой клавиши; ввод в фазе показа не принимается.
func _show_sequence() -> void:
	phase = Phase.SHOW
	phase_time = 0.0
	step = 0
	_flash(sequence[0], Style.accent(0))
	_maybe_fake()


func _flash(key: int, color: Color, seconds := -1.0) -> void:
	lit[key] = show_seconds if seconds < 0.0 else seconds
	lit_color[key] = color
	_players[key].play()
	# Клавиша вминается, как нажатая мармеладка, и встаёт на бортик (`_process`).
	if not _pads.is_empty():
		_pads[key].poke(-160.0)


## Ложная вспышка: другая клавиша коротко мигает серым, без тона, во второй половине шага.
func _maybe_fake() -> void:
	if rng.randf() >= fake_share:
		return
	var k := rng.randi_range(0, KEYS.size() - 1)
	if k == sequence[step]:
		k = (k + 1) % KEYS.size()
	fake_key = k
	fake_left = show_seconds + GAP_SECONDS * 0.5


func _press(key: int) -> void:
	if phase != Phase.INPUT or key < 0:
		return
	var want := sequence[step]
	if key == want:
		_flash(key, Style.SUCCESS, PRESS_SECONDS)
		_rings.add(_pad_center(key), PAD * 0.5, PAD * 0.78, Color(Style.SUCCESS, 0.35), 1, 0.45)
		step += 1
		_jelly_splash(key, step >= sequence.size())
		if step >= sequence.size():
			rounds_done += 1
			if rounds_done >= ROUNDS:
				finish(true)
				return
			phase = Phase.PAUSE
			pause_left = ROUND_PAUSE
	else:
		# Ошибка в счётчик, клавиша дрожит красным, после паузы показ заново.
		errors += 1
		shake[key] = SHAKE_SECONDS
		lit[key] = PRESS_SECONDS
		lit_color[key] = Style.DANGER
		_miss_sound.play()
		_pads[key].push(Vector2(-260.0, 0.0))
		_pads[key].poke(-120.0)
		if errors >= MAX_ERRORS:
			finish(false)
			return
		_replay = true
		_seq_snapshot = sequence.duplicate()
		phase = Phase.PAUSE
		pause_left = ROUND_PAUSE


# --- Мармелад -----------------------------------------------------------------------------

## Верное нажатие: пара капель цвета успеха с верхнего края клавиши; последняя клавиша
## последовательности брызгает чуть больше и выше.
func _jelly_splash(key: int, done: bool) -> void:
	if not Jelly.on():
		return
	var at := _pad_center(key) - Vector2(0.0, PAD * 0.45)
	if done:
		_splash.pop(at, Style.SUCCESS, 6, 650.0, 0.55)
	else:
		_splash.pop(at, Style.SUCCESS, 3, 450.0, 0.4)


## Мармелад живёт и после финиша, пока сцена на экране; на паузе стоит.
func _process(delta: float) -> void:
	super(delta)
	if _pads.is_empty() or paused:
		return
	var tu := Jelly.tuning()
	var moving := Jelly.on()
	_rings.step(delta)
	_splash.step(delta, Callable())
	var fake_now := fake_left > 0.0 and fake_left < FAKE_SECONDS
	if fake_now and not _fake_shown and fake_key >= 0:
		_pads[fake_key].poke(90.0)
	_fake_shown = fake_now
	var k_lift := tu.spring_stiffness * 2.0
	# Тело оседает под своей тяжестью: ведём центр чуть выше, чтобы клавиша стояла на месте.
	var sag := Vector2(0.0, tu.blob_sit * PAD / 2.0 + tu.blob_gravity / tu.blob_stiffness)
	for i in KEYS.size():
		var k := _lit_k(i)
		var center := _pad_center(i) - sag
		if shake[i] > 0.0:
			center.x += sin(shake[i] * 45.0) * 12.0 * shake[i] / SHAKE_SECONDS
		var scale_ := 1.0 + 0.08 * k
		# Бортик растёт с перелётом и сходит вместе со вспышкой, без перелёта через ноль.
		var target := tu.lift_px * k
		var spring := _lift[i]
		if moving:
			var damping := tu.spring_damping * 1.6 if target > spring.value else 2.0 * sqrt(k_lift)
			spring.step(delta, k_lift, damping, target)
			_pads[i].follow(delta, center, 0.0, scale_)
		else:
			spring.value = target
			spring.velocity = 0.0
			_pads[i].blob.shape_scale = scale_
			_pads[i].snap(center)
		if target <= 0.0 and spring.value < 0.2:
			spring.value = 0.0
			spring.velocity = 0.0
	_pop_dots(delta, moving)
	queue_redraw()


## Яркость вспышки клавиши 0..1, как в рисовании.
func _lit_k(i: int) -> float:
	if lit[i] <= 0.0:
		return 0.0
	var show_time := show_seconds if phase == Phase.SHOW else PRESS_SECONDS
	return clampf(lit[i] / show_time, 0.0, 1.0)


## Точки вспухают при смене состояния: заполнилась, опустела, появилась.
func _pop_dots(delta: float, moving: bool) -> void:
	while _dot_pop.size() < sequence.size():
		var s := JellySpring.new()
		s.value = -1.0
		_dot_pop.append(s)
		_dot_state.append(0)
	for j in sequence.size():
		_kick_on_change(_dot_pop[j], _dot_state, j, _dot_color_id(j))
	for j in ROUNDS:
		_kick_on_change(_round_pop[j], _round_state, j, _round_color_id(j))
	for j in MAX_ERRORS:
		_kick_on_change(_err_pop[j], _err_state, j, 1 if j < errors else 0)
	var tu := Jelly.tuning()
	for group: Array[JellySpring] in [_dot_pop, _round_pop, _err_pop]:
		for s in group:
			if moving:
				s.step(delta, tu.spring_stiffness * 1.5, tu.spring_damping * 1.5)
			else:
				s.value = 0.0
				s.velocity = 0.0


func _kick_on_change(s: JellySpring, states: Array[int], j: int, now: int) -> void:
	if states[j] == now:
		return
	s.kick(4.0 if now > states[j] else -2.0)
	states[j] = now


## Состояние точки прогресса: 0 пустая, 1 набрана, 2 показана.
func _dot_color_id(j: int) -> int:
	if phase == Phase.INPUT and j < step:
		return 1
	if phase == Phase.SHOW and j <= step:
		return 2
	return 0


## Состояние точки раунда: 0 впереди, 1 текущий, 2 пройден.
func _round_color_id(j: int) -> int:
	if j < rounds_done:
		return 2
	if j == rounds_done and phase != Phase.PAUSE:
		return 1
	return 0


func _pop_scale(group: Array[JellySpring], j: int) -> float:
	return maxf(1.0 + group[j].value, 0.0) if j < group.size() else 1.0


## Бортик под вспыхнувшей клавишей: сдвинутый вниз контур минус сама клавиша, поэтому
## полупрозрачная заливка не темнеет там, где они перекрылись бы.
func _draw_lip(pad: JellyShape, color: Color, lift: float) -> void:
	var body := pad.contour()
	var mid := Vector2.ZERO
	for p in body:
		mid += p
	mid /= body.size()
	# Бортик чуть уже клавиши (как у `JellyLift`): по бокам не остаётся обрезков.
	var squeeze := 1.0 - 2.0 * minf(3.0, lift * 0.3) / PAD
	var below := PackedVector2Array()
	var cut := PackedVector2Array()
	for p in body:
		below.append(Vector2(mid.x + (p.x - mid.x) * squeeze, p.y + lift))
		cut.append(p - Vector2(0.0, 1.0))
	var lip := Jelly.lip_color(color)
	var ci := get_canvas_item()
	for part in Geometry2D.clip_polygons(below, cut):
		if part.size() < 3 or Geometry2D.is_polygon_clockwise(part):
			continue
		# Не триангулируется (вырожденный обрезок): пропустить, а не рисовать заглушку.
		var tris := Geometry2D.triangulate_polygon(part)
		if tris.is_empty():
			continue
		var colors := PackedColorArray()
		colors.resize(part.size())
		colors.fill(lip)
		RenderingServer.canvas_item_add_triangle_array(ci, tris, part, colors)


# --- Рисование ----------------------------------------------------------------------------

func _pad_center(key: int) -> Vector2:
	var c := size / 2.0 + Vector2(0, 20)
	var s := PAD + PAD_GAP
	match key:
		0: return c + Vector2(-s * 2.2, 0)           # ←
		1: return c + Vector2(-s * 1.2, -s)          # ↑
		2: return c + Vector2(-s * 1.2, s)           # ↓
		3: return c + Vector2(-s * 0.2, 0)           # →
		4: return c + Vector2(s * 1.4, s * 0.5)      # A
		_: return c + Vector2(s * 2.4, -s * 0.5)     # B


func _draw() -> void:
	if def == null:
		return
	var font := get_theme_default_font()
	_rings.draw(self)
	for i in KEYS.size():
		var pad := _pads[i] if i < _pads.size() else null
		var fill := Color(Style.INK, 0.06)
		var ink := Style.INK
		if lit[i] > 0.0:
			fill = Color(lit_color[i], 0.35 + 0.65 * _lit_k(i))
			ink = Style.SURFACE_SOLID
		elif fake_key == i and fake_left > 0.0 and fake_left < FAKE_SECONDS:
			fill = Color(Style.INK_3, 0.5)
			ink = Style.SURFACE_SOLID
		var center := _pad_center(i)
		if pad == null or pad.blob.points.is_empty():
			var half := PAD / 2.0
			Style.flat(fill, Style.R_CTL, Color.TRANSPARENT, 0).draw(get_canvas_item(), Rect2(center - Vector2(half, half), Vector2(PAD, PAD)))
		else:
			if _lift[i].value > 0.2 and lit[i] > 0.0:
				_draw_lip(pad, fill, _lift[i].value)
			pad.draw(self, fill)
			# Знак едет вместе с телом клавиши.
			var mid := Vector2.ZERO
			for p in pad.blob.points:
				mid += p
			center = mid / pad.blob.points.size()
		var glyph: String = GameInput.key(KEYS[i])
		var w := font.get_string_size(glyph, HORIZONTAL_ALIGNMENT_CENTER, -1, 56).x
		draw_string(font, Vector2(center.x - w / 2.0, center.y + 20.0), glyph, HORIZONTAL_ALIGNMENT_LEFT, -1, 56, ink)
	_splash.draw_air(self, Vector2.ZERO)
	# Прогресс последовательности под площадками: заполняется при повторе.
	if not sequence.is_empty():
		var gap := 32.0
		var x0 := size.x / 2.0 - (sequence.size() - 1) * gap / 2.0
		var y := size.y - 200.0
		for j in sequence.size():
			var c := Style.SURFACE_2
			if phase == Phase.INPUT and j < step:
				c = Style.INK
			elif phase == Phase.SHOW and j <= step:
				c = Style.accent(0)
			draw_circle(Vector2(x0 + j * gap, y), 8.0 * _pop_scale(_dot_pop, j), c)
	# Раунды справа сверху, под ними ошибки крестиками: пустые серые, набранные `danger`.
	var r := 7.0
	var gap2 := 28.0
	var rx := size.x - 48.0 - (ROUNDS - 1) * gap2
	for j in ROUNDS:
		var c := Style.SURFACE_2
		if j < rounds_done:
			c = Style.SUCCESS
		elif j == rounds_done and phase != Phase.PAUSE:
			c = Style.INK
		draw_circle(Vector2(rx + j * gap2, 60.0), r * _pop_scale(_round_pop, j), c)
	var ex := size.x - 48.0 - (MAX_ERRORS - 1) * gap2
	for j in MAX_ERRORS:
		var c := Style.DANGER if j < errors else Style.SURFACE_2
		var cx := ex + j * gap2
		var cy := 60.0 + gap2
		var d := (r - 1.0) * _pop_scale(_err_pop, j)
		draw_line(Vector2(cx - d, cy - d), Vector2(cx + d, cy + d), c, 3.0, true)
		draw_line(Vector2(cx - d, cy + d), Vector2(cx + d, cy - d), c, 3.0, true)
