extends Minigame
## «Повтори» (repeat, управление), каталог `docs/specs/minigames_catalog.md`.
## Шесть клавиш-площадок: крестовина слева, A и B справа. Последовательность из 4-7 клавиш
## показывается вспышками, у каждой клавиши свой тон, затем игрок повторяет. Четыре раунда до
## конца таймера; провал, если не успел. Неверная клавиша не ошибка, а потеря времени: ввод
## блокируется на секунду, поле тускнеет вдвое, нужная клавиша подсвечивается, после паузы та
## же последовательность вводится заново с первой клавиши (плейтест 2026-11-05). С `t` последовательность длиннее, показ быстрее, появляются ложные вспышки,
## которые надо пропустить мимо.
## Параметры от `t` в `resources/minigames/repeat.tres`: length, show, fake_share.

enum Phase { SHOW, INPUT, PAUSE }

const KEYS: Array[StringName] = [GameInput.LEFT, GameInput.UP, GameInput.DOWN, GameInput.RIGHT, GameInput.A, GameInput.B]
const TONES: Array[float] = [392.0, 440.0, 494.0, 523.0, 587.0, 659.0]
const ROUNDS := 4
const LOCK_SECONDS := 1.0
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
var lock_left := 0.0
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
	if lock_left > 0.0:
		lock_left = maxf(lock_left - delta, 0.0)
		if lock_left <= 0.0:
			# Блокировка кончилась: та же последовательность с первой клавиши.
			step = 0
			if AutoTest.enabled and sequence != _seq_snapshot:
				AutoTest.fail("repeat: последовательность изменилась после ошибки")
	modulate.a = 0.5 if lock_left > 0.0 else 1.0
	phase_time += delta
	match phase:
		Phase.PAUSE:
			pause_left -= delta
			if pause_left <= 0.0:
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
	if phase != Phase.INPUT or lock_left > 0.0:
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
	phase = Phase.SHOW
	phase_time = 0.0
	step = 0
	_flash(sequence[0], Style.accent(0))
	_maybe_fake()


func _flash(key: int, color: Color, seconds := -1.0) -> void:
	lit[key] = show_seconds if seconds < 0.0 else seconds
	lit_color[key] = color
	_players[key].play()


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
	if phase != Phase.INPUT or key < 0 or lock_left > 0.0:
		return
	var want := sequence[step]
	if key == want:
		_flash(key, Style.SUCCESS, PRESS_SECONDS)
		step += 1
		if step >= sequence.size():
			rounds_done += 1
			if rounds_done >= ROUNDS:
				finish(true)
				return
			phase = Phase.PAUSE
			pause_left = ROUND_PAUSE
	else:
		# Не ошибка, а потеря времени: секунда блокировки, поле тускнеет, нужная клавиша видна.
		lock_left = LOCK_SECONDS
		_seq_snapshot = sequence.duplicate()
		shake[key] = SHAKE_SECONDS
		lit[key] = LOCK_SECONDS
		lit_color[key] = Style.DANGER
		lit[want] = LOCK_SECONDS
		lit_color[want] = Style.accent(0)
		_miss_sound.play()


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
	var font := ThemeDB.fallback_font
	for i in KEYS.size():
		var center := _pad_center(i)
		if shake[i] > 0.0:
			center.x += sin(shake[i] * 45.0) * 12.0 * shake[i] / SHAKE_SECONDS
		var scale_ := 1.0
		var fill := Color(Style.INK, 0.06)
		var ink := Style.INK
		var show_time := show_seconds if phase == Phase.SHOW else PRESS_SECONDS
		if lit[i] > 0.0:
			var k := clampf(lit[i] / show_time, 0.0, 1.0)
			fill = Color(lit_color[i], 0.35 + 0.65 * k)
			ink = Style.SURFACE_SOLID
			scale_ = 1.0 + 0.08 * k
		elif fake_key == i and fake_left > 0.0 and fake_left < FAKE_SECONDS:
			fill = Color(Style.INK_3, 0.5)
			ink = Style.SURFACE_SOLID
		var half := PAD * scale_ / 2.0
		var rect := Rect2(center - Vector2(half, half), Vector2(half * 2.0, half * 2.0))
		Style.flat(fill, Style.R_CTL, Color.TRANSPARENT, 0).draw(get_canvas_item(), rect)
		var glyph: String = GameInput.LABELS[KEYS[i]]
		var w := font.get_string_size(glyph, HORIZONTAL_ALIGNMENT_CENTER, -1, 56).x
		draw_string(font, Vector2(center.x - w / 2.0, center.y + 20.0), glyph, HORIZONTAL_ALIGNMENT_LEFT, -1, 56, ink)
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
			draw_circle(Vector2(x0 + j * gap, y), 8.0, c)
	# Раунды справа сверху.
	var r := 7.0
	var gap2 := 28.0
	var rx := size.x - 48.0 - (ROUNDS - 1) * gap2
	for j in ROUNDS:
		var c := Style.SURFACE_2
		if j < rounds_done:
			c = Style.SUCCESS
		elif j == rounds_done and phase != Phase.PAUSE:
			c = Style.INK
		draw_circle(Vector2(rx + j * gap2, 60.0), r, c)
