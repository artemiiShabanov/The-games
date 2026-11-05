class_name Demo
extends Control
## Базовый класс демки, спека `docs/specs/demos.md`. Хозяин делает `setup(record, source)`,
## добавляет в дерево и зовёт `start()`. Таймера нет (решение 2026-11-05): демка кончается по
## своей цели или по своему условию провала (жизни, счёт), затем короткий экран итога
## («добежал» / «не добежал») и сигнал `demo_finished`, хозяин возвращает туда, откуда
## запустили. B пауза, Esc выход. Баги читаются флагами из записи: `has_bug(&"through_floor")`.

signal demo_started(record: GameRecord, source: StringName)
signal demo_finished(record: GameRecord, reached_goal: bool)

const RESULT_SECONDS := 1.8

var record: GameRecord
var source: StringName = &"debug"
## Секунды с начала, для подписи итога.
var elapsed := 0.0
var running := false
var paused := false
var reached := false
var finished := false
var _result_left := 0.0
var _overlay: Control
var _overlay_title: Label
var _overlay_caption: Label


func setup(record_: GameRecord, source_: StringName) -> void:
	record = record_
	source = source_


func start() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_build_overlay()
	_on_start()
	running = true
	demo_started.emit(record, source)


func has_bug(id: StringName) -> bool:
	return record != null and record.has_bug(id)


## Итог: по цели (true) или по условию провала демки (false). Экран итога, потом сигнал.
func end_demo(goal: bool) -> void:
	if not running:
		return
	running = false
	reached = goal
	_on_end(goal)
	_show_overlay("добежал" if goal else "не добежал", _result_caption(), Style.SUCCESS if goal else Style.INK)
	_result_left = RESULT_SECONDS


## Esc: без экрана итога, сразу наружу.
func quit_demo() -> void:
	if finished:
		return
	running = false
	finished = true
	demo_finished.emit(record, false)


func _process(delta: float) -> void:
	if _result_left > 0.0:
		_result_left -= delta
		if _result_left <= 0.0 and not finished:
			finished = true
			demo_finished.emit(record, reached)
		return
	if not running or paused:
		return
	elapsed += delta
	if AutoTest.bot_active():
		_bot_step(delta)
	_on_tick(delta)


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.is_pressed() and not event.is_echo() and (event as InputEventKey).keycode == KEY_ESCAPE:
		quit_demo()
		get_viewport().set_input_as_handled()
	elif running and GameInput.is_b(event):
		paused = not paused
		if paused:
			_show_overlay("пауза", "B продолжить · Esc выход", Style.INK)
		else:
			_overlay.visible = false
		get_viewport().set_input_as_handled()


# --- Переопределяемое -----------------------------------------------------------------------

func _on_start() -> void:
	pass


func _on_tick(_delta: float) -> void:
	pass


func _on_end(_goal: bool) -> void:
	pass


func _bot_step(_delta: float) -> void:
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
	add_child(_overlay)
	var dim := ColorRect.new()
	dim.color = Color(Style.BG, 0.55)
	dim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_overlay.add_child(dim)
	var card := PanelContainer.new()
	card.add_theme_stylebox_override("panel", Style.card(true))
	card.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	card.grow_horizontal = Control.GROW_DIRECTION_BOTH
	card.grow_vertical = Control.GROW_DIRECTION_BOTH
	_overlay.add_child(card)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 12)
	card.add_child(column)
	_overlay_title = Label.new()
	_overlay_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_overlay_title.add_theme_font_size_override("font_size", Style.FONT_VERB)
	column.add_child(_overlay_title)
	_overlay_caption = Label.new()
	_overlay_caption.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_overlay_caption.add_theme_font_size_override("font_size", Style.FONT_H2)
	_overlay_caption.add_theme_color_override("font_color", Style.INK_2)
	column.add_child(_overlay_caption)


func _show_overlay(title: String, caption: String, color: Color) -> void:
	_overlay_title.text = title
	_overlay_title.add_theme_color_override("font_color", color)
	_overlay_caption.text = caption
	_overlay_caption.visible = caption != ""
	_overlay.visible = true
	_overlay.move_to_front()
