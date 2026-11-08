class_name Minigame
extends Control
## Базовый класс сцены мини-игры. Раннер делает `setup()`, добавляет в дерево и зовёт
## `start()`; мини-игра заканчивается `finish(success)` сама или по таймеру.
## Общий обвес у всех двадцати (STYLE): полоса таймера сверху, значок владельца в углу,
## пилюля ввода внизу. Наследник переопределяет `_on_start`, `_on_tick`, `_on_timeout`,
## `_on_finish` и, когда появится настоящий бот, `_bot_step`. Пауза на Esc (плейтест
## 2026-11-08, #42): таймер и ввод стоят, поле закрыто подложкой с карточкой: глагол, правила
## (`def.hint`), пилюля ввода, кнопка «Продолжить» (␣, Esc или клик). Под ботом паузы нет.

signal finished(success: bool)

const TIMER_HEIGHT := 6.0
const DANGER_SECONDS := 3.0
const BOT_DELAY := 0.3

var def: MinigameDef
## Сложность 0..1.
var t := 0.0
var rng := RandomNumberGenerator.new()
var time_limit := 20.0
var time_left := 20.0
var running := false
var elapsed := 0.0

var paused := false

var _done := false
var _timer_bar: ColorRect
var _pause_overlay: Control
var _resume_button: PanelContainer


func setup(def_: MinigameDef, t_: float, seed_: int, time_multiplier := 1.0) -> void:
	def = def_
	t = clampf(t_, 0.0, 1.0)
	rng.seed = seed_
	time_limit = def.time_seconds * time_multiplier
	time_left = time_limit


func start() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_build_chrome()
	running = true
	_on_start()


func finish(success: bool) -> void:
	if _done:
		return
	_done = true
	running = false
	_on_finish(success)
	finished.emit(success)


## Пауза: таймер стоит, ввод мини-игры выключен, поле закрыто карточкой правил.
func pause() -> void:
	if paused or not running or _done:
		return
	paused = true
	running = false
	set_process_unhandled_input(false)
	if _pause_overlay == null:
		_build_pause()
	_pause_overlay.visible = true
	_pause_overlay.move_to_front()
	ShellSounds.play(&"tick")


func resume() -> void:
	if not paused:
		return
	paused = false
	running = true
	set_process_unhandled_input(true)
	_pause_overlay.visible = false
	ShellSounds.play(&"tick")


## Esc открывает и закрывает паузу; на паузе ␣, Esc или клик по кнопке продолжают, остальной
## ввод не доходит до мини-игры.
func _input(event: InputEvent) -> void:
	if _done or AutoTest.bot_active():
		return
	var key := event as InputEventKey
	var esc := key != null and key.pressed and not key.echo and key.keycode == KEY_ESCAPE
	if not paused:
		if esc and running:
			pause()
			get_viewport().set_input_as_handled()
		return
	var mouse := event as InputEventMouseButton
	var click := mouse != null and mouse.pressed and mouse.button_index == MOUSE_BUTTON_LEFT \
			and _resume_button != null and _resume_button.get_global_rect().has_point(mouse.position)
	if esc or GameInput.is_a(event) or click:
		resume()
	if key != null or mouse != null:
		get_viewport().set_input_as_handled()


func _process(delta: float) -> void:
	if not running:
		return
	elapsed += delta
	time_left = maxf(time_left - delta, 0.0)
	_update_timer_bar()
	if AutoTest.bot_active() and _bot_step(delta):
		return
	_on_tick(delta)
	if running and time_left <= 0.0:
		finish(_on_timeout())


# --- Переопределяемое -----------------------------------------------------------------------

## Поле построено, таймер пошёл.
func _on_start() -> void:
	pass


func _on_tick(_delta: float) -> void:
	pass


## Время вышло: засчитан ли спринт. По умолчанию провал.
func _on_timeout() -> bool:
	return false


func _on_finish(_success: bool) -> void:
	pass


## Бот вместо игрока. По умолчанию через `BOT_DELAY` заканчивает исходом по режиму и
## забирает кадр (возвращает true). Настоящий бот нажимает действия и возвращает false.
func _bot_step(_delta: float) -> bool:
	if elapsed >= BOT_DELAY:
		finish(AutoTest.bot_mode == AutoTest.BotMode.WIN)
	return true


# --- Обвес ------------------------------------------------------------------------------------

func _build_chrome() -> void:
	_timer_bar = ColorRect.new()
	_timer_bar.color = Style.accent(0)
	_timer_bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_timer_bar.position = Vector2.ZERO
	_timer_bar.size = Vector2(size.x, TIMER_HEIGHT)
	add_child(_timer_bar)

	var icon := AspectIcon.for_def(def)
	icon.position = Vector2(48, 40)
	add_child(icon)

	add_child(HintPill.bottom_bar(HintPill.for_inputs(def.inputs)))


## Карточка паузы поверх поля: глагол, правила, пилюля ввода, кнопка «Продолжить».
func _build_pause() -> void:
	_pause_overlay = Control.new()
	_pause_overlay.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_pause_overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_pause_overlay)
	var dim := ColorRect.new()
	dim.color = Color(Style.BG, 0.96)
	dim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	dim.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_pause_overlay.add_child(dim)
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", Style.card(true))
	panel.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	panel.grow_horizontal = Control.GROW_DIRECTION_BOTH
	panel.grow_vertical = Control.GROW_DIRECTION_BOTH
	panel.custom_minimum_size = Vector2(Style.FEED_WIDTH, 0)
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_pause_overlay.add_child(panel)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 16)
	column.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.add_child(column)
	column.add_child(_pause_label("пауза", Style.FONT_CAPTION, Style.INK_3))
	column.add_child(_pause_label(def.verb, Style.FONT_H1, Style.INK))
	column.add_child(_pause_label(def.hint, Style.FONT_BODY, Style.INK_2))
	var inputs := HBoxContainer.new()
	inputs.alignment = BoxContainer.ALIGNMENT_CENTER
	inputs.mouse_filter = Control.MOUSE_FILTER_IGNORE
	inputs.add_child(HintPill.for_inputs(def.inputs))
	column.add_child(inputs)
	_resume_button = PanelContainer.new()
	_resume_button.custom_minimum_size = Vector2(0, Style.BUTTON_HEIGHT)
	_resume_button.add_theme_stylebox_override("panel", Style.flat(Style.INK, Style.R_CTL, Color.TRANSPARENT, 0))
	_resume_button.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var bl := _pause_label("Продолжить", Style.FONT_H2, Style.SURFACE_SOLID)
	bl.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_resume_button.add_child(bl)
	column.add_child(_resume_button)
	var hint := HBoxContainer.new()
	hint.alignment = BoxContainer.ALIGNMENT_CENTER
	hint.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hint.add_child(HintPill.make("%s или Esc продолжить" % GameInput.key(GameInput.A)))
	column.add_child(hint)


func _pause_label(text: String, font_size: int, color: Color) -> Label:
	var l := Label.new()
	l.text = text
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.add_theme_font_size_override("font_size", font_size)
	l.add_theme_color_override("font_color", color)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l


func _update_timer_bar() -> void:
	if _timer_bar == null:
		return
	var frac := time_left / time_limit if time_limit > 0.0 else 0.0
	_timer_bar.size = Vector2(size.x * frac, TIMER_HEIGHT)
	_timer_bar.color = Style.DANGER if time_left <= DANGER_SECONDS else Style.accent(0)
