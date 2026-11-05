extends Minigame
## Заглушка мини-игры, пока настоящая не сделана: глагол по центру, A засчитывает спринт,
## B проваливает, по таймеру провал. Под ботом заканчивается сама.

var _label: Label


func _on_start() -> void:
	_label = Label.new()
	_label.text = "%s\n\nзаглушка мини-игры: A успех, B провал" % def.verb
	_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_label.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_label.add_theme_font_size_override("font_size", Style.FONT_H1)
	_label.add_theme_color_override("font_color", Style.INK_2)
	_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_label)
	move_child(_label, 0)


func _unhandled_input(event: InputEvent) -> void:
	if not running:
		return
	if GameInput.is_a(event):
		finish(true)
		get_viewport().set_input_as_handled()
	elif GameInput.is_b(event):
		finish(false)
		get_viewport().set_input_as_handled()
