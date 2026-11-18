class_name LanguageScreen
extends Control
## Выбор языка на первом запуске (2026-11-18): до меню, пока в `user://settings.cfg` нет
## языка. Карточка с заголовком на двух языках и двумя кнопками, первым выбран язык системы
## (`Lang.system_default`). ← → или наведение выбирают, ␣ или клик подтверждают; выбор
## пишется в настройки, потом язык меняется в настройках. Под автотестом `--menu --first-launch`.

signal chosen(id: String)

const BUTTON := Vector2(320, 0)

var focus := 0
var _buttons: Array[PanelContainer] = []
var _lifts: Array[JellyLift] = []
var _done := false


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	# Подписи на своих языках: движок не переводит их по текущему языку.
	auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
	focus = maxi(Lang.IDS.find(Lang.system_default()), 0)
	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	center.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(center)
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", Style.card(true))
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	center.add_child(panel)
	Jelly.panel(panel)
	Jelly.cover(self)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 32)
	column.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.add_child(column)
	var title := _label("Язык · Language", Style.FONT_H1, Style.INK)  # i18n: skip
	title.add_theme_font_override("font", Jelly.fun_font(800))
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	column.add_child(title)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", Style.GAP_CARDS)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	column.add_child(row)
	for id in Lang.IDS:
		var b := PanelContainer.new()
		b.custom_minimum_size = Vector2(BUTTON.x, Style.BUTTON_HEIGHT)
		b.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var l := _label(Lang.name_of(id), Style.FONT_H2, Style.INK)
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		b.add_child(l)
		row.add_child(b)
		_buttons.append(b)
		_lifts.append(Jelly.button(b))
	var hints := HBoxContainer.new()
	hints.alignment = BoxContainer.ALIGNMENT_CENTER
	hints.add_theme_constant_override("separation", 16)
	hints.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	hints.offset_top = -(Style.PILL_HEIGHT + Style.HINTS_BOTTOM)
	hints.offset_bottom = -Style.HINTS_BOTTOM
	hints.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hints.add_child(HintPill.make("← →"))
	hints.add_child(HintPill.make(GameInput.key(GameInput.A) + " OK"))
	add_child(hints)
	MouseUi.pass_through(self)
	_refresh()


func _unhandled_input(event: InputEvent) -> void:
	if _done:
		return
	var viewport := get_viewport()
	if event is InputEventMouseMotion:
		var over := _item_at(event)
		if over >= 0 and over != focus:
			_set_focus(over)
		return
	if MouseUi.is_click(event):
		var at := _item_at(event)
		if at >= 0:
			focus = at
			choose()
		MouseUi.consume(viewport)
		return
	if event.is_echo():
		return
	if event.is_action_pressed(GameInput.LEFT):
		_set_focus(clampi(focus - 1, 0, _buttons.size() - 1))
	elif event.is_action_pressed(GameInput.RIGHT):
		_set_focus(clampi(focus + 1, 0, _buttons.size() - 1))
	elif GameInput.is_a(event):
		choose()
	else:
		return
	MouseUi.consume(viewport)


## Выбранный язык в настройки и сразу в дело.
func choose() -> void:
	if _done:
		return
	_done = true
	_lifts[focus].press()
	ShellSounds.play(&"done")
	Options.language = Lang.IDS[focus]
	Options.apply()
	Options.save()
	chosen.emit(Options.language)


func _set_focus(i: int) -> void:
	if i == focus:
		return
	focus = i
	ShellSounds.play(&"tick")
	_refresh()


func _item_at(event: InputEvent) -> int:
	for i in _buttons.size():
		if MouseUi.hit(_buttons[i], event):
			return i
	return -1


func _refresh() -> void:
	for i in _buttons.size():
		var on := i == focus
		_buttons[i].add_theme_stylebox_override("panel", Style.flat(Style.INK if on else Style.SURFACE_2, Style.R_CTL, Color.TRANSPARENT, 0))
		(_buttons[i].get_child(0) as Label).add_theme_color_override("font_color", Style.SURFACE_SOLID if on else Style.INK)
		_lifts[i].focused = on


func _label(text: String, font_size: int, color: Color) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", font_size)
	l.add_theme_color_override("font_color", color)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l
