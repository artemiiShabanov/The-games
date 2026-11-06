class_name HintPill
extends PanelContainer
## Пилюля-подсказка ввода внизу экрана (STYLE: `surface-2`, высота 40, текст `ink-2`).
## Клавиши набираются глифами из `GameInput.LABELS`: «← →  A».


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


## Пилюля с глифами действий мини-игры: «← → ↑ ↓» или «A  B».
static func for_inputs(inputs: Array[StringName]) -> HintPill:
	var parts: PackedStringArray = []
	for action in inputs:
		parts.append(str(GameInput.LABELS.get(action, String(action))))
	return make(" ".join(parts) if not parts.is_empty() else "любая клавиша")
