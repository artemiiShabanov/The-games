class_name HintPill
extends PanelContainer
## Пилюля-подсказка ввода внизу экрана (STYLE: `surface-2`, высота 40, текст `ink-2`).
## Клавиши набираются глифами из `GameInput.LABELS`: «← →  A».


## Живая пилюля ввода: текст клавиш и мыши, между ними переключается по `GameInput.mouse`.
var _keys_text := ""
var _mouse_text := ""


static func make(text: String) -> HintPill:
	var pill := HintPill.new()
	var sb := Style.flat(Style.SURFACE_2, Style.R_PILL, Color.TRANSPARENT, 0)
	sb.content_margin_left = 20
	sb.content_margin_right = 20
	sb.content_margin_top = 6
	sb.content_margin_bottom = 6
	pill.add_theme_stylebox_override("panel", sb)
	pill.custom_minimum_size = Vector2(0, Style.PILL_HEIGHT)
	pill.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var label := Label.new()
	label.text = text
	label.add_theme_font_size_override("font_size", Style.FONT_CAPTION)
	label.add_theme_color_override("font_color", Style.INK_2)
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	pill.add_child(label)
	Jelly.attach_pill(pill)
	return pill


## Пилюля-подложка под шапку над карточкой (плейтест 2026-11-06: на пиксельной студии текст
## без подложки сольётся): `surface`, текст `ink-2` размером `body`.
static func header(text: String) -> PanelContainer:
	var pill := PanelContainer.new()
	var sb := Style.flat(Style.SURFACE, Style.R_PILL, Color.TRANSPARENT, 0)
	sb.content_margin_left = 20
	sb.content_margin_right = 20
	sb.content_margin_top = 6
	sb.content_margin_bottom = 6
	pill.add_theme_stylebox_override("panel", sb)
	pill.custom_minimum_size = Vector2(0, Style.PILL_HEIGHT)
	pill.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var label := Label.new()
	label.text = text
	label.add_theme_font_size_override("font_size", Style.FONT_BODY)
	label.add_theme_color_override("font_color", Style.INK_2)
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	pill.add_child(label)
	Jelly.attach_pill(pill)
	return pill


## Полоса внизу экрана с пилюлей по центру (STYLE: подсказки ввода внизу, отступ 40).
static func bottom_bar(pill: Control, margin := 40) -> Control:
	var bar := HBoxContainer.new()
	bar.alignment = BoxContainer.ALIGNMENT_CENTER
	bar.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	bar.offset_top = -(Style.PILL_HEIGHT + margin)
	bar.offset_bottom = -margin
	bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	bar.add_child(pill)
	return bar


## Пилюля с глифами действий мини-игры: «← → ↑ ↓» или «A  B». С `mouse_text` пилюля живая
## (#83): пока игрок на мыши (`GameInput.mouse`), показывает подсказку мыши, иначе клавиши.
static func for_inputs(inputs: Array[StringName], mouse_text := "") -> HintPill:
	var parts: PackedStringArray = []
	for action in inputs:
		parts.append(GameInput.key(action))
	var pill := make(" ".join(parts) if not parts.is_empty() else "любая клавиша")
	pill._keys_text = pill.label().text
	pill._mouse_text = mouse_text
	pill._sync_device()
	return pill


func _ready() -> void:
	set_process(_mouse_text != "")


## Подпись пилюли.
func label() -> Label:
	return get_child(0) as Label


func _process(_delta: float) -> void:
	_sync_device()


func _sync_device() -> void:
	if _mouse_text == "":
		return
	var want := _mouse_text if GameInput.mouse else _keys_text
	if label().text != want:
		label().text = want
		if is_inside_tree():
			Jelly.poke(self, 2.0)
