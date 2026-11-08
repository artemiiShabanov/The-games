class_name Demo
extends Control
## Базовый класс демки, спека `docs/specs/demos.md`. Хозяин делает `setup(record, source)`,
## добавляет в дерево и зовёт `start()`. Демка идёт в большой карточке `CardFrame` поверх
## студии, как спринты (решение 2026-11-06): карточка всплывает, экран демки в `screen`,
## после итога карточка уезжает вниз и приходит `demo_finished`. Таймера нет (решение
## 2026-11-05): демка кончается по своей цели или по своему условию провала (жизни, счёт),
## затем короткий экран итога («добежал» / «не добежал»). Esc открывает паузу с пунктами
## «Вернуться» и «Пропустить» (решение 2026-11-06); B остаётся демке, у платформера это дэш.
## Подклассы переопределяют `_game_input`, а не `_unhandled_input`. Баги читаются флагами из
## записи: `has_bug(&"wild_physics")`. Встроенный режим (`embed(size)`, #26): без карточки и
## ввода, своего размера, бот играет сам, звук выключен; так демка крутится как запись стрима
## в ленте.

signal demo_started(record: GameRecord, source: StringName)
signal demo_finished(record: GameRecord, reached_goal: bool)

const RESULT_SECONDS := 1.8
const MENU_ITEMS: Array[String] = ["Вернуться", "Пропустить"]

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
var _menu_hint: Control


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


## Итог: по цели (true) или по условию провала демки (false). Экран итога, потом сигнал.
func end_demo(goal: bool) -> void:
	if not running:
		return
	running = false
	paused = false
	reached = goal
	_on_end(goal)
	if not embedded:
		_show_overlay("добежал" if goal else "не добежал", _result_caption(), Style.SUCCESS if goal else Style.INK)
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
	_menu_hint = HBoxContainer.new()
	(_menu_hint as HBoxContainer).alignment = BoxContainer.ALIGNMENT_CENTER
	_menu_hint.add_child(HintPill.make("%s %s выбрать · %s подтвердить · %s вернуться" % [
			GameInput.key(GameInput.LEFT), GameInput.key(GameInput.RIGHT),
			GameInput.key(GameInput.A), GameInput.key(GameInput.B)]))
	_menu_hint.visible = false
	column.add_child(_menu_hint)
	MouseUi.pass_through(_overlay)


## Выбранный пункт: заливка `ink` и рамка фокуса; остальные `surface-2`.
func _refresh_menu() -> void:
	for i in _menu_pills.size():
		var on := i == _menu_index
		_menu_pills[i].add_theme_stylebox_override("panel",
				Style.flat(Style.INK if on else Style.SURFACE_2, Style.R_CTL, Style.FOCUS if on else Color.TRANSPARENT, 0))
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
