class_name PauseMenu
extends Control
## Пауза вне мини-игр (#71), спека `docs/specs/run.md`: Esc на экранах оболочки, где Esc не
## занят самим экраном. Дерево на паузе (`get_tree().paused`), меню работает всегда:
## «Продолжить» и «В меню» (↑ ↓, ␣, клик; Esc продолжает). Настройки в M6. Забег сохранён на
## начало текущей фазы, поэтому «В меню» ничего не теряет, кроме хода внутри фазы.

signal resumed
signal to_menu

const ITEMS: Array[String] = ["Продолжить", "В меню"]

var index := 0
var _buttons: Array[PanelContainer] = []
var _lifts: Array[JellyLift] = []


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	var dim := ColorRect.new()
	dim.color = Color(Style.BG, 0.9)
	dim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	dim.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(dim)
	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	center.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(center)
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", Style.card(true))
	panel.custom_minimum_size = Vector2(560, 0)
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	center.add_child(panel)
	Jelly.panel(panel)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 16)
	column.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.add_child(column)
	var title := Label.new()
	title.text = "Пауза"
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.add_theme_font_size_override("font_size", Style.FONT_H1)
	title.add_theme_color_override("font_color", Style.INK)
	column.add_child(title)
	for text in ITEMS:
		var b := PanelContainer.new()
		b.custom_minimum_size = Vector2(0, Style.BUTTON_HEIGHT)
		b.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var l := Label.new()
		l.text = text
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		l.add_theme_font_size_override("font_size", Style.FONT_H2)
		b.add_child(l)
		column.add_child(b)
		_buttons.append(b)
		_lifts.append(Jelly.button(b))
	var hint := HBoxContainer.new()
	hint.alignment = BoxContainer.ALIGNMENT_CENTER
	hint.add_child(HintPill.make("↑ ↓ выбрать · %s выбрать · Esc продолжить" % GameInput.key(GameInput.A)))
	column.add_child(hint)
	_refresh()
	ShellSounds.play(&"tick")


func _input(event: InputEvent) -> void:
	# «В меню» синхронно уводит меню из дерева, поэтому вьюпорт берётся до выбора.
	var viewport := get_viewport()
	var key := event as InputEventKey
	var esc := key != null and key.pressed and not key.echo and key.keycode == KEY_ESCAPE
	var handled := true
	if MouseUi.is_motion(event):
		# Наведение (#82): кнопка под курсором берёт фокус.
		for i in _buttons.size():
			if i != index and MouseUi.hit(_buttons[i], event):
				index = i
				ShellSounds.play(&"tick")
				_refresh()
		return
	if esc:
		_choose(0)
	elif event.is_action_pressed(GameInput.UP) or event.is_action_pressed(GameInput.DOWN):
		index = 1 - index
		ShellSounds.play(&"tick")
		_refresh()
	elif GameInput.is_a(event) and not event.is_echo():
		_choose(index)
	elif MouseUi.is_click(event):
		handled = false
		for i in _buttons.size():
			if MouseUi.hit(_buttons[i], event):
				_choose(i)
				handled = true
	else:
		handled = event is InputEventKey or event is InputEventMouseButton
	if handled:
		MouseUi.consume(viewport)


func _choose(i: int) -> void:
	_lifts[i].press()
	ShellSounds.play(&"done")
	if i == 0:
		resumed.emit()
	else:
		to_menu.emit()


func _refresh() -> void:
	for i in _buttons.size():
		var on := i == index
		_buttons[i].add_theme_stylebox_override("panel", Style.flat(Style.INK if on else Style.SURFACE_2, Style.R_CTL, Color.TRANSPARENT, 0))
		(_buttons[i].get_child(0) as Label).add_theme_color_override("font_color", Style.SURFACE_SOLID if on else Style.INK)
		_lifts[i].focused = on
